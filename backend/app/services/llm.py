from __future__ import annotations

import json
import os
from typing import Any
from uuid import uuid4

import requests


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4").strip() or "gpt-5.4"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro").strip() or "gemini-2.5-pro"
_usage_tracker = None


class _NoOpUsageTracker:
    def track_openai_response(self, **kwargs: Any) -> None:
        return None

    def track_gemini_response(self, **kwargs: Any) -> None:
        return None


def _get_usage_tracker():
    global _usage_tracker
    if _usage_tracker is not None:
        return _usage_tracker

    try:
        from kbf_llm_usage import KbfLlmUsageClient
    except ImportError:
        _usage_tracker = _NoOpUsageTracker()
    else:
        _usage_tracker = KbfLlmUsageClient.from_env(
            service_id="paper",
            service_name="Paper",
        )
    return _usage_tracker


def _build_request_id(prefix: str) -> str:
    return f"{prefix}-{uuid4()}"


def _safe_track_openai_response(*, payload: dict[str, Any], request_id: str, route: str, meta: dict[str, Any]) -> None:
    try:
        _get_usage_tracker().track_openai_response(
            response=payload,
            operation="chat",
            request_id=request_id,
            model=OPENAI_MODEL,
            route=route,
            meta=meta,
        )
    except Exception:
        return None


def _safe_track_gemini_response(*, payload: dict[str, Any], request_id: str, route: str, meta: dict[str, Any]) -> None:
    try:
        _get_usage_tracker().track_gemini_response(
            raw_response=payload,
            operation="chat",
            request_id=request_id,
            model=GEMINI_MODEL,
            route=route,
            meta=meta,
        )
    except Exception:
        return None


def openai_available() -> bool:
    return bool(OPENAI_API_KEY)


def gemini_available() -> bool:
    return bool(GEMINI_API_KEY)


def openai_chat_json(system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
    if not openai_available():
        return None
    request_id = _build_request_id("paper-openai-json")
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENAI_MODEL,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    _safe_track_openai_response(
        payload=payload,
        request_id=request_id,
        route="paper.app.services.llm.openai_chat_json",
        meta={"response_format": "json_object"},
    )
    content = payload["choices"][0]["message"]["content"]
    if not isinstance(content, str):
        return None
    return json.loads(content)


def openai_chat_text(system_prompt: str, user_prompt: str) -> str | None:
    if not openai_available():
        return None
    request_id = _build_request_id("paper-openai-text")
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENAI_MODEL,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    _safe_track_openai_response(
        payload=payload,
        request_id=request_id,
        route="paper.app.services.llm.openai_chat_text",
        meta={"response_format": "text"},
    )
    content = payload["choices"][0]["message"]["content"]
    return content if isinstance(content, str) else None


def gemini_text(system_prompt: str, user_prompt: str) -> str | None:
    if not gemini_available():
        return None
    request_id = _build_request_id("paper-gemini-text")
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
        params={"key": GEMINI_API_KEY},
        headers={"Content-Type": "application/json"},
        json={
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": 0.2},
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    _safe_track_gemini_response(
        payload=payload,
        request_id=request_id,
        route="paper.app.services.llm.gemini_text",
        meta={"response_format": "text"},
    )
    candidates = payload.get("candidates") or []
    if not candidates:
        return None
    parts = candidates[0].get("content", {}).get("parts") or []
    text = "".join(str(part.get("text") or "") for part in parts if isinstance(part, dict)).strip()
    return text or None
