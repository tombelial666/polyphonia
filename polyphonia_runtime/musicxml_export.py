from __future__ import annotations

import os
from pathlib import Path

DEFAULT_MUSICXML_EXPORT_DIR = Path(r"D:\projects\MIDI-MusXML")
EXPORT_DIR_ENV_VAR = "PETS_MUSICXML_EXPORT_DIR"


def resolve_musicxml_export_dir() -> Path:
    raw = (os.environ.get(EXPORT_DIR_ENV_VAR) or "").strip()
    if raw:
        return Path(raw).expanduser()
    return DEFAULT_MUSICXML_EXPORT_DIR


def safe_musicxml_filename(name: str) -> str:
    base = Path(str(name or "").replace("\\", "/")).name.strip() or "polyphonia-export.musicxml"
    stem = Path(base).stem or "polyphonia-export"
    out = []
    for ch in stem:
        out.append(ch if ch.isalnum() or ch in "-_." else "_")
    safe_stem = "".join(out).strip("._") or "polyphonia-export"
    return safe_stem[:120] + ".musicxml"


def save_musicxml_copy(filename: str, musicxml: str, export_dir: Path | None = None) -> Path:
    target_dir = Path(export_dir) if export_dir is not None else resolve_musicxml_export_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / safe_musicxml_filename(filename)
    target.write_text(musicxml, encoding="utf-8")
    return target
