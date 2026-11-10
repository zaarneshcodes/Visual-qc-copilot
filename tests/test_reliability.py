"""Retry on busy Gemini servers, and the verdict/disposition consistency rule."""
from qc_copilot import config, copilot, llm


class Resp:
    def __init__(self, status, text=""):
        self.status_code, self.ok, self.text = status, status == 200, text

    def json(self):
        return {"candidates": [{"content": {"parts": [{"text": '{"verdict": "PASS"}'}]}}]}


def test_gemini_retries_when_busy(monkeypatch):
    for key, val in (("LLM_PROVIDER", "gemini"), ("GEMINI_API_KEY", "k"), ("ANTHROPIC_API_KEY", "")):
        monkeypatch.setenv(key, val)
    monkeypatch.setattr(llm, "settings", config.Settings())
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    replies = iter([Resp(503), Resp(503), Resp(200)])
    monkeypatch.setattr(llm.requests, "post", lambda *a, **k: next(replies))
    assert llm.ask_json("sys", [llm.text_block("x")]) == {"verdict": "PASS"}


def test_contradiction_is_routed_to_review():
    out = copilot.enforce_consistency({"verdict": "FAIL", "disposition": "accept", "severity": "minor"})
    assert out["verdict"] == "REVIEW" and out["disposition"] == "escalate"
    assert "contradict" in out["consistency_note"]


def test_consistent_report_is_unchanged():
    out = copilot.enforce_consistency({"verdict": "fail", "disposition": "Scrap"})
    assert out == {"verdict": "FAIL", "disposition": "scrap"}
