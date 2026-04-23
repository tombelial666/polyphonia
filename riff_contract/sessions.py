from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .validate import validate_riff_fragment

_DEFAULT_DIRNAME = "polyphonia_sessions"


def sessions_root(repo_root: Path | None = None) -> Path:
    """Return (and create) the gitignored user session directory under the repo."""
    root = repo_root if repo_root is not None else Path(__file__).resolve().parent.parent
    p = root / _DEFAULT_DIRNAME
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_riff_fragment(
    filename: str,
    data: dict[str, Any],
    *,
    repo_root: Path | None = None,
) -> tuple[Path | None, list[str]]:
    """
    Validate ``data`` and write ``<sessions_root>/<safe-stem>.json``.
    Returns ``(path, [])`` on success, or ``(None, errors)`` when validation fails.
    """
    errs = validate_riff_fragment(data)
    if errs:
        return None, errs
    path = sessions_root(repo_root) / _safe_json_name(filename)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path, []


def _safe_json_name(filename: str) -> str:
    base = Path(filename.replace("\\", "/")).name
    stem = Path(base).stem or "session"
    out = []
    for ch in stem:
        out.append(ch if ch.isalnum() or ch in "-_" else "_")
    s = "".join(out).strip("_") or "session"
    return s + ".json"
