from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def sessions_root(base_dir: str | Path) -> Path:
    root = Path(base_dir) / "polyphonia_sessions"
    root.mkdir(parents=True, exist_ok=True)
    return root


def dialogs_dir(base_dir: str | Path) -> Path:
    root = sessions_root(base_dir) / "dialogs"
    root.mkdir(parents=True, exist_ok=True)
    return root


def chats_dir(base_dir: str | Path) -> Path:
    root = sessions_root(base_dir) / "chats"
    root.mkdir(parents=True, exist_ok=True)
    return root


def auth_path(base_dir: str | Path) -> Path:
    """Optional "remember me" key storage under gitignored polyphonia_sessions/."""
    return sessions_root(base_dir) / "auth.json"


def load_persisted_auth(base_dir: str | Path) -> dict[str, Any]:
    path = auth_path(base_dir)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def save_persisted_auth(base_dir: str | Path, patch: dict[str, Any]) -> None:
    path = auth_path(base_dir)
    current = load_persisted_auth(base_dir)
    current.update(patch)
    for key in ("openai_key", "claude_key"):
        if key in current and (current.get(key) is None or str(current.get(key) or "").strip() == ""):
            current.pop(key, None)
    current["v"] = 1
    path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def forget_persisted_auth(base_dir: str | Path, *, openai: bool = False, claude: bool = False) -> None:
    current = load_persisted_auth(base_dir)
    if openai:
        current.pop("openai_key", None)
    if claude:
        current.pop("claude_key", None)
    path = auth_path(base_dir)
    if current:
        current["v"] = int(current.get("v") or 1)
        path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return
    try:
        path.unlink(missing_ok=True)
    except Exception:
        # Best-effort; don't crash app on permission issues.
        pass
