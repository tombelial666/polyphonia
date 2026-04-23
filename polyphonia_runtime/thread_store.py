from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sanitize_thread_id(raw: str | None) -> str:
    value = (raw or "").strip().lower()
    if not value:
        return "default"
    value = re.sub(r"[^a-z0-9._-]", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("._-")
    return value[:80] or "default"


def threads_root(chats_dir: str | Path, key_id: str) -> Path:
    root = Path(chats_dir) / (key_id or "unknown")
    root.mkdir(parents=True, exist_ok=True)
    return root


def thread_file(chats_dir: str | Path, key_id: str, thread_id: str) -> Path:
    return threads_root(chats_dir, key_id) / f"{sanitize_thread_id(thread_id)}.jsonl"


def append_thread_event(chats_dir: str | Path, key_id: str, thread_id: str, event: dict[str, Any]) -> None:
    path = thread_file(chats_dir, key_id, thread_id)
    row = dict(event)
    row["thread_id"] = sanitize_thread_id(thread_id)
    row.setdefault("ts", datetime.now(timezone.utc).isoformat())
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def ensure_thread_file(chats_dir: str | Path, key_id: str, thread_id: str, title: str = "") -> None:
    path = thread_file(chats_dir, key_id, thread_id)
    if path.exists():
        return
    append_thread_event(
        chats_dir,
        key_id,
        thread_id,
        {
            "kind": "thread_meta",
            "role": "meta",
            "title": (title or "").strip()[:140],
        },
    )


def load_thread_events(chats_dir: str | Path, key_id: str, thread_id: str, limit: int = 500) -> list[dict[str, Any]]:
    path = thread_file(chats_dir, key_id, thread_id)
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return rows
    tail = lines[-max(1, int(limit)) :] if lines else []
    for line in tail:
        raw = (line or "").strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def list_threads_for_key(chats_dir: str | Path, key_id: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    root = threads_root(chats_dir, key_id)
    for path in sorted(root.glob("*.jsonl"), key=lambda item: item.stat().st_mtime, reverse=True):
        thread_id = path.stem
        title = ""
        for row in load_thread_events(chats_dir, key_id, thread_id, limit=80):
            if str(row.get("kind") or "") == "thread_meta":
                title = str(row.get("title") or "").strip()[:140]
                if title:
                    break
            if str(row.get("role") or "") == "user":
                text = str(row.get("text") or "").strip()
                if text:
                    title = text.replace("\n", " ")[:80]
                    break
        stats = path.stat()
        out.append(
            {
                "thread_id": thread_id,
                "title": title,
                "updated_ts": datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc).isoformat(),
                "size_bytes": stats.st_size,
            }
        )
    return out


def thread_openai_messages(
    chats_dir: str | Path,
    key_id: str,
    thread_id: str,
    max_messages: int = 32,
    max_chars: int = 22000,
) -> list[dict[str, str]]:
    events = load_thread_events(chats_dir, key_id, thread_id, limit=max(100, max_messages * 4))
    filtered: list[dict[str, str]] = []
    for event in events:
        role = str(event.get("role") or "").strip().lower()
        if role not in ("user", "assistant"):
            continue
        text = str(event.get("text") or "")
        if not text.strip():
            continue
        filtered.append({"role": role, "content": text})
    tail = filtered[-max_messages:] if filtered else []
    kept: list[dict[str, str]] = []
    total = 0
    for message in reversed(tail):
        length = len(message["content"])
        if kept and total + length > max_chars:
            break
        kept.append(message)
        total += length
    kept.reverse()
    return kept
