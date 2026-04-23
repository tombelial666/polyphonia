"""Window management helpers and JS API in phrygian_app (pywebview)."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import phrygian_app


def _reset_globals() -> None:
    phrygian_app._MAIN_WINDOW = None
    phrygian_app._ASSIST_WINDOW = None


def test_open_assist_window_offline_rejected() -> None:
    _reset_globals()
    api = phrygian_app.PolyphoniaApi(ui_mode="offline")
    out = json.loads(api.open_assist_window())
    assert out["ok"] is False
    assert out["error"] == "offline_mode"


def test_open_assist_window_creates_and_reuses(monkeypatch) -> None:
    _reset_globals()
    created = SimpleNamespace()
    created.bring_to_front = MagicMock()

    create_window = MagicMock(return_value=created)
    monkeypatch.setattr(phrygian_app.webview, "create_window", create_window)

    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    out1 = json.loads(api.open_assist_window())
    assert out1["ok"] is True
    assert out1.get("created") is True
    assert phrygian_app._ASSIST_WINDOW is created
    create_window.assert_called_once()

    out2 = json.loads(api.open_assist_window())
    assert out2["ok"] is True
    assert out2.get("reused") is True
    create_window.assert_called_once()
    created.bring_to_front.assert_called()


def test_tile_windows_not_supported_non_windows(monkeypatch) -> None:
    _reset_globals()
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    monkeypatch.setattr(phrygian_app, "_is_windows", lambda: False)
    out = json.loads(api.tile_windows())
    assert out["ok"] is False
    assert out["error"] == "not_supported"


def test_tile_windows_moves_and_resizes(monkeypatch) -> None:
    _reset_globals()
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")

    main = SimpleNamespace(move=MagicMock(), resize=MagicMock(), bring_to_front=MagicMock())
    assist = SimpleNamespace(move=MagicMock(), resize=MagicMock(), bring_to_front=MagicMock())
    phrygian_app._MAIN_WINDOW = main
    phrygian_app._ASSIST_WINDOW = assist

    monkeypatch.setattr(phrygian_app, "_is_windows", lambda: True)
    monkeypatch.setattr(phrygian_app, "_get_screen_size", lambda: (1920, 1080))

    out = json.loads(api.tile_windows(json.dumps({"mode": "vertical"})))
    assert out["ok"] is True
    main.move.assert_called()
    main.resize.assert_called()
    assist.move.assert_called()
    assist.resize.assert_called()

