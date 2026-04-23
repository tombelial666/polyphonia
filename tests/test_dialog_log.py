from __future__ import annotations

from datetime import datetime, timezone

from polyphonia_runtime import dialog_log


def test_dialog_heading_distinguishes_gpt_and_system() -> None:
    assert dialog_log.dialog_heading("gpt") == "GPT (OpenAI)"
    assert dialog_log.dialog_heading("gpt_error") == "GPT (ошибка)"
    assert dialog_log.dialog_heading("system") == "System (UI)"


def test_append_dialog_markdown_writes_daily_file(tmp_path) -> None:
    now = datetime(2026, 4, 23, 10, 11, 12, tzinfo=timezone.utc)
    path = dialog_log.append_dialog_markdown(tmp_path, role="user", text="hello", now=now)
    assert path.name == "assist-dialog-2026-04-23.md"
    body = path.read_text(encoding="utf-8")
    assert "hello" in body
    assert "User" in body
    assert "10:11:12 UTC" in body
