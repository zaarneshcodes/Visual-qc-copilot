"""Language-model layer with switchable providers. One place for clients, model names and JSON parsing.

LLM_PROVIDER:
  claude  — Anthropic API (paid)                          needs ANTHROPIC_API_KEY
  gemini  — Google Gemini API free tier                   needs GEMINI_API_KEY
  ollama  — open model on your own machine (free, local)  needs Ollama running
  none    — no language model; rule-based fallbacks
  auto    — (default) first one with a key: claude, then gemini, else none

Gemini is called through its native generateContent endpoint and Ollama through its
OpenAI-compatible endpoint, both with plain `requests`, so they add no dependencies.
"""
from __future__ import annotations

import json
import logging
import re

import requests

from .config import settings

log = logging.getLogger(__name__)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
# Gemini Flash models "think" before answering and that counts against the output limit,
# so give them headroom or the JSON answer gets cut off.
GEMINI_MIN_OUTPUT_TOKENS = 4096

_anthropic_client = None


def image_block(b64_png: str) -> dict:
    """Provider-neutral image part; converted per provider in ask_json."""
    return {"type": "image", "b64_png": b64_png}


def text_block(text: str) -> dict:
    return {"type": "text", "text": text}


def ask_json(system: str, content: list[dict], max_tokens: int = 1200) -> dict:
    """Send one user turn (text + images) and parse a JSON object out of the reply."""
    provider = settings.llm_provider
    if provider == "claude":
        text = _ask_claude(system, content, max_tokens)
    elif provider == "gemini":
        text = _ask_gemini(system, content, max_tokens)
    elif provider == "ollama":
        text = _ask_ollama(system, content, max_tokens)
    else:
        raise RuntimeError("No language model configured (LLM_PROVIDER=none)")
    return parse_json(text)


def _ask_claude(system: str, content: list[dict], max_tokens: int) -> str:
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic

        _anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    parts = [
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": c["b64_png"]}}
        if c["type"] == "image"
        else {"type": "text", "text": c["text"]}
        for c in content
    ]
    resp = _anthropic_client.messages.create(
        model=settings.claude_model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": parts}],
    )
    return "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")


def build_openai_payload(model: str, system: str, content: list[dict], max_tokens: int) -> dict:
    parts = [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{c['b64_png']}"}}
        if c["type"] == "image"
        else {"type": "text", "text": c["text"]}
        for c in content
    ]
    return {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": parts}],
    }


def build_gemini_payload(system: str, content: list[dict], max_tokens: int) -> dict:
    parts = [
        {"inline_data": {"mime_type": "image/png", "data": c["b64_png"]}}
        if c["type"] == "image"
        else {"text": c["text"]}
        for c in content
    ]
    return {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "maxOutputTokens": max(max_tokens, GEMINI_MIN_OUTPUT_TOKENS),
            "responseMimeType": "application/json",
        },
    }


def _ask_gemini(system: str, content: list[dict], max_tokens: int) -> str:
    resp = requests.post(
        GEMINI_URL.format(model=settings.gemini_model),
        json=build_gemini_payload(system, content, max_tokens),
        headers={"x-goog-api-key": settings.gemini_api_key},
        timeout=120,
    )
    if resp.status_code == 429:
        raise RuntimeError("gemini rate limit reached (free-tier quota); using fallback output")
    if not resp.ok:  # show Google's own explanation, not just the status code
        raise RuntimeError(f"gemini HTTP {resp.status_code}: {resp.text[:300]}")
    candidates = resp.json().get("candidates") or []
    if not candidates:
        raise RuntimeError(f"gemini returned no answer: {resp.text[:300]}")
    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts if not p.get("thought"))


def _ask_ollama(system: str, content: list[dict], max_tokens: int) -> str:
    url = settings.ollama_url.rstrip("/") + "/v1/chat/completions"
    payload = build_openai_payload(settings.ollama_model, system, content, max_tokens)
    resp = requests.post(url, json=payload, timeout=300)  # local CPU models are slow
    if not resp.ok:
        raise RuntimeError(f"ollama HTTP {resp.status_code}: {resp.text[:300]}")
    return resp.json()["choices"][0]["message"]["content"] or ""


def parse_json(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise
