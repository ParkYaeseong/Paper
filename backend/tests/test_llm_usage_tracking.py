from __future__ import annotations

from types import SimpleNamespace

from app.services import llm


class FakeTracker:
    def __init__(self, emitted, raise_on_send: bool = False):
        self.emitted = emitted
        self.raise_on_send = raise_on_send

    def track_openai_response(self, **kwargs):
        self.emitted.append(
            {
                "provider": "openai",
                "operation": kwargs["operation"],
                "request_id": kwargs["request_id"],
                "model": kwargs.get("model"),
                "route": kwargs.get("route"),
                "total_tokens": kwargs["response"].get("usage", {}).get("total_tokens", 0),
            }
        )
        if self.raise_on_send:
            raise RuntimeError("collector down")

    def track_gemini_response(self, **kwargs):
        usage = kwargs["raw_response"].get("usageMetadata") or {}
        self.emitted.append(
            {
                "provider": "google",
                "operation": kwargs["operation"],
                "request_id": kwargs["request_id"],
                "model": kwargs.get("model"),
                "route": kwargs.get("route"),
                "total_tokens": usage.get("totalTokenCount", 0),
            }
        )
        if self.raise_on_send:
            raise RuntimeError("collector down")


def _response(payload):
    return SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: payload,
    )


def test_openai_chat_json_emits_usage_event(monkeypatch):
    emitted = []
    payload = {
        "choices": [{"message": {"content": "{\"title\": \"Tracked\"}"}}],
        "usage": {
            "prompt_tokens": 120,
            "completion_tokens": 30,
            "total_tokens": 150,
        },
    }

    monkeypatch.setattr(llm, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(llm, "_usage_tracker", FakeTracker(emitted), raising=False)
    monkeypatch.setattr(llm.requests, "post", lambda *args, **kwargs: _response(payload))

    result = llm.openai_chat_json("system", "user")

    assert result == {"title": "Tracked"}
    assert len(emitted) == 1
    assert emitted[0]["provider"] == "openai"
    assert emitted[0]["operation"] == "chat"
    assert emitted[0]["total_tokens"] == 150


def test_openai_chat_text_swallows_tracker_errors(monkeypatch):
    emitted = []
    payload = {
        "choices": [{"message": {"content": "Tracked text"}}],
        "usage": {
            "prompt_tokens": 90,
            "completion_tokens": 10,
            "total_tokens": 100,
        },
    }

    monkeypatch.setattr(llm, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(llm, "_usage_tracker", FakeTracker(emitted, raise_on_send=True), raising=False)
    monkeypatch.setattr(llm.requests, "post", lambda *args, **kwargs: _response(payload))

    result = llm.openai_chat_text("system", "user")

    assert result == "Tracked text"
    assert len(emitted) == 1
    assert emitted[0]["provider"] == "openai"
    assert emitted[0]["total_tokens"] == 100


def test_gemini_text_emits_usage_event(monkeypatch):
    emitted = []
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "Gemini tracked"},
                    ]
                }
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 70,
            "candidatesTokenCount": 15,
            "totalTokenCount": 85,
        },
    }

    monkeypatch.setattr(llm, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(llm, "_usage_tracker", FakeTracker(emitted), raising=False)
    monkeypatch.setattr(llm.requests, "post", lambda *args, **kwargs: _response(payload))

    result = llm.gemini_text("system", "user")

    assert result == "Gemini tracked"
    assert len(emitted) == 1
    assert emitted[0]["provider"] == "google"
    assert emitted[0]["operation"] == "chat"
    assert emitted[0]["total_tokens"] == 85
