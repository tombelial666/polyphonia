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
    assert any("mode:" in ln for ln in lines)


def test_resolve_api_key_prefers_polyphonia_env(monkeypatch) -> None:
    import scripts.claude_terminal as ct

    monkeypatch.setenv("POLYPHONIA_CLAUDE_API_KEY", "poly-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anth-key")
    assert ct.resolve_api_key() == "poly-key"


def test_extract_text_content_smoke() -> None:
    import scripts.claude_terminal as ct

    text = ct._extract_text_content(
        {
            "content": [
                {"type": "text", "text": "hello"},
                {"type": "tool_use", "name": "ignored"},
                {"type": "text", "text": "world"},
            ]
        }
    )
    assert text == "hello\n\nworld"


def test_api_repl_can_exit_immediately_with_key() -> None:
    env = {**os.environ, "NO_COLOR": "1", "POLYPHONIA_CLAUDE_API_KEY": "sk-ant-test"}
    cp = subprocess.run(
        [sys.executable, str(LAUNCHER)],
        cwd=str(ROOT),
        input="/exit\n",
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
        check=False,
    )
    assert cp.returncode == 0
    combined = (cp.stdout or "") + (cp.stderr or "")
    assert "Stable Claude terminal is ready." in combined


def test_main_uses_prompted_key_before_repl(monkeypatch) -> None:
    import scripts.claude_terminal as ct

    seen: dict[str, str] = {}

    monkeypatch.setattr(ct, "resolve_api_key", lambda: None)
    monkeypatch.setattr(ct, "_prompt_for_api_key", lambda: "sk-ant-prompt")

    def fake_run_api_repl(initial_prompt: str = "", *, api_key: str | None = None) -> int:
        seen["initial_prompt"] = initial_prompt
        seen["api_key"] = str(api_key or "")
        return 0

    monkeypatch.setattr(ct, "run_api_repl", fake_run_api_repl)

    assert ct.main(["hello", "world"]) == 0
    assert seen["initial_prompt"] == "hello world"
    assert seen["api_key"] == "sk-ant-prompt"


def test_main_exits_when_no_key_available(monkeypatch) -> None:
    import scripts.claude_terminal as ct

    monkeypatch.setattr(ct, "resolve_api_key", lambda: None)
    monkeypatch.setattr(ct, "_prompt_for_api_key", lambda: None)
    assert ct.main([]) == 2
