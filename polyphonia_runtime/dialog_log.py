from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from polyphonia_runtime import session_store


def dialog_heading(role: str) -> str:
    """Human-readable Markdown heading that distinguishes GPT from UI/system messages."""
    normalized = (role or "note").strip().lower()
    if normalized == "gpt":
        return "GPT (OpenAI)"
    if normalized == "gpt_error":
        return "GPT (ошибка)"
    if normalized == "user":
        return "User"
    if normalized == "system":
        return "System (UI)"
    return (role or "note").strip().replace("\n", " ")[:48] or "note"


def append_dialog_markdown(
    base_dir: str | Path,
    *,
    role: str,
    text: str,
    now: datetime | None = None,
) -> Path:
    current = now or datetime.now(timezone.utc)
    day = current.strftime("%Y-%m-%d")
    path = session_store.dialogs_dir(base_dir) / f"assist-dialog-{day}.md"
    body = text
    if len(body) > 50000:
        body = body[:50000] + "\n\n…(truncated)\n"
    if not path.exists():
        path.write_text(
            f"# Polyphonia Assist — dialog log\n\n"
            f"- Date (UTC): **{day}**\n"
            f"- Path is under `polyphonia_sessions/dialogs/` (not committed to git).\n\n"
            f"---\n",
            encoding="utf-8",
        )
    ts = current.strftime("%H:%M:%S UTC")
    block = f"\n### {dialog_heading(role)} — {ts}\n\n{body}\n\n---\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(block)
    return path.resolve()
