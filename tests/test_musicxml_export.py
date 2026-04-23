from __future__ import annotations

from polyphonia_runtime import musicxml_export


def test_safe_musicxml_filename_strips_path_and_invalid_chars() -> None:
    out = musicxml_export.safe_musicxml_filename(r"..\bad/name:*?<>|demo.musicxml")
    assert out == "name______demo.musicxml"


def test_resolve_musicxml_export_dir_uses_env(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv(musicxml_export.EXPORT_DIR_ENV_VAR, str(tmp_path / "mx"))
    assert musicxml_export.resolve_musicxml_export_dir() == tmp_path / "mx"
