"""Smoke tests for scripts/claude_terminal.py (banner, no exec)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "claude_terminal.py"


def test_banner_only_contains_pets() -> None:
    env = {**os.environ, "NO_COLOR": "1"}
    cp = subprocess.run(
        [sys.executable, str(LAUNCHER), "--banner-only"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
        check=False,
    )
    assert cp.returncode == 0
    out = (cp.stdout or "") + (cp.stderr or "")
    assert "PETS" in out
    assert "claude" in out.lower()


def test_banner_only_no_color_tty_safe() -> None:
    """With NO_COLOR, banner should not require escape sequences (optional)."""
    env = {**os.environ, "NO_COLOR": "1"}
    cp = subprocess.run(
        [sys.executable, str(LAUNCHER), "--banner-only"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
        check=False,
    )
    assert cp.returncode == 0
    combined = (cp.stdout or "") + (cp.stderr or "")
    assert "\033[" not in combined


def test_banner_lines_api_smoke() -> None:
    import scripts.claude_terminal as ct

    root = ct._find_repo_root()
    lines = ct._banner_lines(root, width=72, color=False)
    assert any("PETS" in ln for ln in lines)
    assert any("exec:" in ln for ln in lines)
