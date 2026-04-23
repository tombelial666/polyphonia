"""Runtime poly mode switch (PolyphoniaApi.set_poly_mode)."""

from __future__ import annotations

import json

import phrygian_app


def test_set_poly_mode_toggles_openai_gate() -> None:
    api = phrygian_app.PolyphoniaApi(ui_mode="offline")
    assert api.set_openai_api_key("sk-test") == "offline_mode"
    out = json.loads(api.set_poly_mode(json.dumps({"mode": "assist"})))
    assert out["ok"] is True
    assert out["mode"] == "assist"
    assert api.set_openai_api_key("sk-test") == "ok"
    out2 = json.loads(api.set_poly_mode(json.dumps({"mode": "offline"})))
    assert out2["ok"] is True
    assert api.set_openai_api_key("sk-x") == "offline_mode"
    phrygian_app._SESSION_OPENAI_KEY = None


def test_set_poly_mode_invalid() -> None:
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    out = json.loads(api.set_poly_mode(json.dumps({"mode": "nope"})))
    assert out["ok"] is False
    assert out["error"] == "invalid_mode"
