"""get_base() behavior in frozen/exe scenario."""

from __future__ import annotations

import os
from pathlib import Path

import phrygian_app


def test_get_base_prefers_exe_dir_when_index_present(monkeypatch, tmp_path: Path) -> None:
    # Simulate: packaged exe located in tmp_path, with index.html next to it.
    exe_dir = tmp_path / "app"
    exe_dir.mkdir(parents=True, exist_ok=True)
    (exe_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    (exe_dir / "assets").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(phrygian_app.sys, "frozen", True, raising=False)
    monkeypatch.setattr(phrygian_app.sys, "executable", str(exe_dir / "polyphonia.exe"), raising=False)
    monkeypatch.setattr(phrygian_app.sys, "_MEIPASS", str(tmp_path / "_meipass"), raising=False)

    base = phrygian_app.get_base()
    assert os.path.normpath(base) == os.path.normpath(str(exe_dir))


def test_get_resource_base_prefers_meipass_for_onefile(monkeypatch, tmp_path: Path) -> None:
    # Simulate: onefile extraction dir has index/assets, exe dir does not.
    exe_dir = tmp_path / "exe"
    exe_dir.mkdir(parents=True, exist_ok=True)
    meipass = tmp_path / "_meipass"
    meipass.mkdir(parents=True, exist_ok=True)
    (meipass / "index.html").write_text("<html></html>", encoding="utf-8")
    (meipass / "assets").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(phrygian_app.sys, "frozen", True, raising=False)
    monkeypatch.setattr(phrygian_app.sys, "executable", str(exe_dir / "polyphonia.exe"), raising=False)
    monkeypatch.setattr(phrygian_app.sys, "_MEIPASS", str(meipass), raising=False)

    base = phrygian_app.get_resource_base()
    assert os.path.normpath(base) == os.path.normpath(str(meipass))

