"""Provider selection and the OpenAI-compatible request used for Gemini / Ollama (no network)."""
from qc_copilot import config, llm


def _settings(monkeypatch, **env):
    for key in ("LLM_PROVIDER", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.setenv(key, env.get(key, ""))
    return config.Settings()


def test_auto_prefers_claude_then_gemini_then_none(monkeypatch):
    assert _settings(monkeypatch, LLM_PROVIDER="auto", ANTHROPIC_API_KEY="a", GEMINI_API_KEY="g").llm_provider == "claude"
    assert _settings(monkeypatch, LLM_PROVIDER="auto", GEMINI_API_KEY="g").llm_provider == "gemini"
    assert _settings(monkeypatch, LLM_PROVIDER="auto").llm_provider == "none"


def test_provider_without_key_falls_back_to_none(monkeypatch):
    assert _settings(monkeypatch, LLM_PROVIDER="gemini").llm_provider == "none"
    assert _settings(monkeypatch, LLM_PROVIDER="ollama").llm_provider == "ollama"  # local, no key needed


def test_openai_payload_carries_images_as_data_urls():
    payload = llm.build_openai_payload("m", "sys", [llm.image_block("QUJD"), llm.text_block("hi")], 100)
    user = payload["messages"][1]["content"]
    assert payload["messages"][0] == {"role": "system", "content": "sys"}
    assert user[0]["image_url"]["url"] == "data:image/png;base64,QUJD"
    assert user[1] == {"type": "text", "text": "hi"}


def test_gemini_call_parses_json_reply(monkeypatch):
    class Resp:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": '```json\n{"verdict": "FAIL"}\n```'}}]}

    sent = {}

    def fake_post(url, json, headers, timeout):
        sent.update(url=url, headers=headers)
        return Resp()

    monkeypatch.setattr(llm, "settings", _settings(monkeypatch, LLM_PROVIDER="gemini", GEMINI_API_KEY="k"))
    monkeypatch.setattr(llm.requests, "post", fake_post)
    assert llm.ask_json("sys", [llm.text_block("x")]) == {"verdict": "FAIL"}
    assert sent["url"] == llm.GEMINI_OPENAI_URL and sent["headers"]["Authorization"] == "Bearer k"
