"""Append Assist dialog lines to local Markdown (pywebview API)."""

from __future__ import annotations

import json
from pathlib import Path

import phrygian_app


def test_append_assist_dialog_md_writes_file(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(phrygian_app, "get_base", lambda: str(tmp_path))
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    raw = api.append_assist_dialog_md(json.dumps({"role": "user", "text": "hello"}))
    out = json.loads(raw)
    assert out["ok"] is True
    assert "path" in out
    p = Path(out["path"])
    assert p.exists()
    text = p.read_text(encoding="utf-8")
    assert "hello" in text
    assert "user" in text.lower() or "User" in text


def test_append_assist_dialog_md_offline_rejected() -> None:
    api = phrygian_app.PolyphoniaApi(ui_mode="offline")
    raw = api.append_assist_dialog_md(json.dumps({"role": "user", "text": "x"}))
    out = json.loads(raw)
    assert out.get("ok") is False
    assert out.get("reason") == "offline_mode"


def test_append_assist_dialog_md_gpt_heading_distinct(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(phrygian_app, "get_base", lambda: str(tmp_path))
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    api.append_assist_dialog_md(json.dumps({"role": "gpt", "text": "model reply"}))
    api.append_assist_dialog_md(json.dumps({"role": "system", "text": "ui notice"}))
    p = tmp_path / "polyphonia_sessions" / "dialogs"
    files = list(p.glob("assist-dialog-*.md"))
    assert len(files) == 1
    body = files[0].read_text(encoding="utf-8")
    assert "GPT (OpenAI)" in body
    assert "System (UI)" in body
    assert "model reply" in body
    assert "ui notice" in body


def test_append_assist_dialog_md_gpt_error_heading(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(phrygian_app, "get_base", lambda: str(tmp_path))
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    raw = api.append_assist_dialog_md(json.dumps({"role": "gpt_error", "text": "missing_api_key"}))
    out = json.loads(raw)
    assert out["ok"] is True
    body = Path(out["path"]).read_text(encoding="utf-8")
    assert "GPT (ошибка)" in body
    assert "missing_api_key" in body
