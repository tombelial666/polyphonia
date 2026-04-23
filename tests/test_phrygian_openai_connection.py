"""get_openai_connection / openai_ping (PolyphoniaApi)."""

from __future__ import annotations

import json

import phrygian_app


def test_get_openai_connection_offline() -> None:
    api = phrygian_app.PolyphoniaApi(ui_mode="offline")
    o = json.loads(api.get_openai_connection())
    assert o["ok"] is True
    assert o["source"] == "none"
    assert o["ui_mode"] == "offline"


def test_get_openai_connection_env_wins(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    phrygian_app._SESSION_OPENAI_KEY = "sk-session-test"
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    o = json.loads(api.get_openai_connection())
    assert o["source"] == "env"
    assert o["model_default"] == "gpt-4o-mini"
    phrygian_app._SESSION_OPENAI_KEY = None


def test_get_openai_connection_session_only(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    phrygian_app._SESSION_OPENAI_KEY = "sk-only-session"
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    o = json.loads(api.get_openai_connection())
    assert o["source"] == "session"
    phrygian_app._SESSION_OPENAI_KEY = None


def test_get_openai_connection_none(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    phrygian_app._SESSION_OPENAI_KEY = None
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    o = json.loads(api.get_openai_connection())
    assert o["source"] == "none"
    phrygian_app._SESSION_OPENAI_KEY = None


def test_openai_ping_ok(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    phrygian_app._SESSION_OPENAI_KEY = "sk-fake"

    class Resp:
        status = 200

        def read(self, n: int = -1) -> bytes:
            return b'{"data":[]}'

    class Ctx:
        def __enter__(self):
            return Resp()

        def __exit__(self, *args):
            return None

    monkeypatch.setattr(phrygian_app.urllib.request, "urlopen", lambda *a, **k: Ctx())
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    o = json.loads(api.openai_ping())
    assert o["ok"] is True
    assert o.get("http_status") == 200
    phrygian_app._SESSION_OPENAI_KEY = None


def test_openai_ping_missing_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    phrygian_app._SESSION_OPENAI_KEY = None
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    o = json.loads(api.openai_ping())
    assert o["ok"] is False
    assert o["error"] == "missing_api_key"
