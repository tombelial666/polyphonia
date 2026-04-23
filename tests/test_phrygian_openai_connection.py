"""get_openai_connection / openai_ping (PolyphoniaApi)."""

from __future__ import annotations

import io
import json
import urllib.error

import phrygian_app


def test_openai_key_persist_and_bootstrap(monkeypatch, tmp_path) -> None:
    # Isolate persisted auth to a temp base dir.
    monkeypatch.setattr(phrygian_app, "get_base", lambda: str(tmp_path))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    r = json.loads(api.set_openai_api_key_persist(json.dumps({"key": "sk-remembered", "remember": True})))
    assert r["ok"] is True
    assert r["remembered"] is True

    # Clear RAM and bootstrap from disk.
    phrygian_app._SESSION_OPENAI_KEY = None
    phrygian_app._SESSION_OPENAI_KEY_ORIGIN = None
    phrygian_app._bootstrap_session_keys_from_persisted_auth()
    assert phrygian_app._SESSION_OPENAI_KEY == "sk-remembered"

    api2 = phrygian_app.PolyphoniaApi(ui_mode="assist")
    conn = json.loads(api2.get_openai_connection())
    assert conn["source"] == "session"
    assert conn["persisted"] is True


def test_forget_persisted_openai_key(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(phrygian_app, "get_base", lambda: str(tmp_path))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    _ = json.loads(api.set_openai_api_key_persist(json.dumps({"key": "sk-remembered", "remember": True})))
    conn1 = json.loads(api.get_openai_connection())
    assert conn1["persisted"] is True
    o = json.loads(api.forget_openai_api_key_persisted())
    assert o["ok"] is True
    conn2 = json.loads(api.get_openai_connection())
    assert conn2["persisted"] is False


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


def test_validate_openai_key_chat_probe_quota_error(monkeypatch) -> None:
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

    body = b'{"error":{"message":"quota","code":"insufficient_quota"}}'
    err = urllib.error.HTTPError(
        url="https://api.openai.com/v1/chat/completions",
        code=429,
        msg="Too Many Requests",
        hdrs=None,
        fp=io.BytesIO(body),
    )

    def _urlopen(req, timeout=0):
        if req.full_url.endswith("/v1/models"):
            return Ctx()
        raise err

    monkeypatch.setattr(phrygian_app.urllib.request, "urlopen", _urlopen)
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    o = json.loads(api.validate_openai_key())
    assert o["ok"] is False
    assert o["error"] == "chat_probe_http_error"
    assert o["status"] == 429
    assert "insufficient_quota" in o["message"]
    phrygian_app._SESSION_OPENAI_KEY = None
