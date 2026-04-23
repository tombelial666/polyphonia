"""openai_chat error handling (network + HTTP) without real network."""

from __future__ import annotations

import io
import json
import urllib.error
from unittest.mock import MagicMock

import phrygian_app


def test_openai_chat_missing_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    phrygian_app._SESSION_OPENAI_KEY = None
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    out = json.loads(api.openai_chat(json.dumps({"user_text": "hi", "include_context": False})))
    assert out["ok"] is False
    assert out["error"] == "missing_api_key"


def test_openai_chat_http_error_includes_body(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    body = json.dumps(
        {
            "error": {
                "message": "You exceeded your current quota, please check your plan and billing details.",
                "type": "insufficient_quota",
                "code": "insufficient_quota",
            }
        }
    ).encode("utf-8")

    fp = io.BytesIO(body)
    err = urllib.error.HTTPError(
        url="https://api.openai.com/v1/chat/completions",
        code=429,
        msg="Too Many Requests",
        hdrs=None,
        fp=fp,
    )

    def _raise(*_a, **_kw):
        raise err

    monkeypatch.setattr(phrygian_app.urllib.request, "urlopen", _raise)
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    out = json.loads(api.openai_chat(json.dumps({"user_text": "hi", "include_context": False})))
    assert out["ok"] is False
    assert out["error"] == "http_error"
    assert out["status"] == 429
    assert "insufficient_quota" in out["message"]


def test_openai_chat_network_error(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    def _raise(*_a, **_kw):
        raise urllib.error.URLError("nope")

    monkeypatch.setattr(phrygian_app.urllib.request, "urlopen", _raise)
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    out = json.loads(api.openai_chat(json.dumps({"user_text": "hi", "include_context": False})))
    assert out["ok"] is False
    assert out["error"] == "network"

