"""Language-model layer with switchable providers. One place for clients, model names and JSON parsing.

LLM_PROVIDER:
  claude  — Anthropic API (paid)                          needs ANTHROPIC_API_KEY
  gemini  — Google Gemini API free tier                   needs GEMINI_API_KEY
  ollama  — open model on your own machine (free, local)  needs Ollama running
  none    — no language model; rule-based fallbacks
  auto    — (default) first one with a key: claude, then gemini, else none

Gemini and Ollama are called through their OpenAI-compatible chat endpoints with plain
`requests`, so they add no dependencies.
"""
from __future__ import annotations

import json
import logging
import re

import requests

from .config import settings

log = logging.getLogger(__name__)

GEMINI_OPENAI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

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
    elif provider in ("gemini", "ollama"):
        text = _ask_openai_compatible(provider, system, content, max_tokens)
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


def _ask_openai_compatible(provider: str, system: str, content: list[dict], max_tokens: int) -> str:
    if provider == "gemini":
        url, model = GEMINI_OPENAI_URL, settings.gemini_model
        headers = {"Authorization": f"Bearer {settings.gemini_api_key}"}
        timeout = 90
    else:
        url, model = settings.ollama_url.rstrip("/") + "/v1/chat/completions", settings.ollama_model
        headers = {}
        timeout = 300  # local CPU models are slow
    resp = requests.post(url, json=build_openai_payload(model, system, content, max_tokens), headers=headers,
                         timeout=timeout)
    if resp.status_code == 429:
        raise RuntimeError(f"{provider} rate limit reached (free-tier quota); using fallback output")
    resp.raise_for_status()
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
