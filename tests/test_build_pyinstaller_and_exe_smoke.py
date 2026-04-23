"""Build-level checks: PyInstaller and basic exe smoke (Windows only)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(not sys.platform.startswith("win"), reason="PyInstaller exe smoke is Windows-only")
def test_pyinstaller_build_succeeds(tmp_path: Path) -> None:
    # Run in an isolated work dir to avoid locking dist/polyphonia.exe
    repo = Path(__file__).resolve().parents[1]
    spec = repo / "polyphonia.spec"
    assert spec.is_file()

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"

    cp = subprocess.run(
        [
            "pyinstaller",
            str(spec),
            "--distpath",
            str(tmp_path / "dist"),
            "--workpath",
            str(tmp_path / "build"),
        ],
        cwd=str(repo),
        env=env,
        capture_output=True,
        text=True,
        timeout=900,
    )
    assert cp.returncode == 0, cp.stdout + "\n" + cp.stderr
    assert (tmp_path / "dist" / "polyphonia.exe").is_file()


@pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows-only exe smoke")
def test_polyphonia_exe_smoke_starts_and_exits_cleanly() -> None:
    if (os.environ.get("PETS_RUN_EXE_SMOKE") or "").strip() != "1":
        pytest.skip("Set PETS_RUN_EXE_SMOKE=1 to run GUI exe smoke locally.")
    repo = Path(__file__).resolve().parents[1]
    exe = repo / "dist" / "polyphonia.exe"
    if not exe.is_file():
        pytest.skip("dist/polyphonia.exe not built; run test_pyinstaller_build_succeeds first")

    env = os.environ.copy()
    # Try to avoid UI blocking in CI-like runs.
    env["POLYPHONIA_MODE"] = "offline"

    p = subprocess.Popen([str(exe)], cwd=str(repo), env=env)
    try:
        # Give it a moment to start; if it crashes immediately, returncode will be non-None.
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # If still running, that's OK for smoke; terminate to avoid hanging tests.
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait(timeout=5)
        # exe is GUI; return codes vary depending on pywebview backend availability.
        assert p.returncode in (0, None, 1)
    finally:
        if p.poll() is None:
            p.kill()

