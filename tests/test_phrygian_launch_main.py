"""launch_main from startup splash (PolyphoniaApi)."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock

import phrygian_app


def test_launch_main_sets_keys_and_loads_url(monkeypatch) -> None:
    mock_win = MagicMock()
    monkeypatch.setattr(phrygian_app.webview, "windows", [mock_win])
    timer_calls: dict[str, object | None] = {"fn": None}

    class _ImmediateTimer:
        def __init__(self, _delay, fn):
            timer_calls["fn"] = fn

        def start(self):
            assert callable(timer_calls["fn"])
            timer_calls["fn"]()

    monkeypatch.setattr(phrygian_app.threading, "Timer", _ImmediateTimer)
    phrygian_app._SESSION_OPENAI_KEY = None
    phrygian_app._SESSION_CLAUDE_KEY = None
    try:
        api = phrygian_app.PolyphoniaApi(ui_mode="offline")
        out = json.loads(
            api.launch_main(
                json.dumps({"mode": "assist", "openai_key": "sk-openai", "claude_key": "sk-ant"})
            )
        )
        assert out["ok"] is True
        assert phrygian_app._SESSION_OPENAI_KEY == "sk-openai"
        assert phrygian_app._SESSION_CLAUDE_KEY == "sk-ant"
        assert os.environ.get("POLYPHONIA_MODE") == "assist"
        mock_win.load_url.assert_called_once()
    finally:
        phrygian_app._SESSION_OPENAI_KEY = None
        phrygian_app._SESSION_CLAUDE_KEY = None
        os.environ.pop("POLYPHONIA_MODE", None)


def test_launch_main_offline_clears_keys(monkeypatch) -> None:
    mock_win = MagicMock()
    monkeypatch.setattr(phrygian_app.webview, "windows", [mock_win])
    timer_calls: dict[str, object | None] = {"fn": None}

    class _ImmediateTimer:
        def __init__(self, _delay, fn):
            timer_calls["fn"] = fn

        def start(self):
            assert callable(timer_calls["fn"])
            timer_calls["fn"]()

    monkeypatch.setattr(phrygian_app.threading, "Timer", _ImmediateTimer)
    phrygian_app._SESSION_OPENAI_KEY = "x"
    phrygian_app._SESSION_CLAUDE_KEY = "y"
    try:
        api = phrygian_app.PolyphoniaApi(ui_mode="assist")
        out = json.loads(api.launch_main(json.dumps({"mode": "offline", "openai_key": "", "claude_key": ""})))
        assert out["ok"] is True
        assert phrygian_app._SESSION_OPENAI_KEY is None
        assert phrygian_app._SESSION_CLAUDE_KEY is None
    finally:
        os.environ.pop("POLYPHONIA_MODE", None)


def test_launch_main_invalid_json(monkeypatch) -> None:
    mock_win = MagicMock()
    monkeypatch.setattr(phrygian_app.webview, "windows", [mock_win])
    api = phrygian_app.PolyphoniaApi(ui_mode="offline")
    out = json.loads(api.launch_main("not json"))
    assert out["ok"] is False
    assert out["error"] == "invalid_json"


def test_launch_main_invalid_mode(monkeypatch) -> None:
    mock_win = MagicMock()
    monkeypatch.setattr(phrygian_app.webview, "windows", [mock_win])
    api = phrygian_app.PolyphoniaApi(ui_mode="offline")
    out = json.loads(api.launch_main(json.dumps({"mode": "nope"})))
    assert out["ok"] is False
    assert out["error"] == "invalid_mode"


def test_launch_main_index_not_found(monkeypatch, tmp_path) -> None:
    # Simulate a bad resource base (e.g., packaging regression)
    mock_win = MagicMock()
    monkeypatch.setattr(phrygian_app.webview, "windows", [mock_win])
    monkeypatch.setattr(phrygian_app, "get_resource_base", lambda: str(tmp_path))
    api = phrygian_app.PolyphoniaApi(ui_mode="offline")
    out = json.loads(api.launch_main(json.dumps({"mode": "offline"})))
    assert out["ok"] is False
    assert out["error"] == "index_not_found"
