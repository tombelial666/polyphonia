from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_require_operator_token_raises_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PETS_OPERATOR_TOKEN", raising=False)
    import scripts.repo_admin_cli as rac

    monkeypatch.chdir(ROOT)
    with pytest.raises(PermissionError, match="PETS_OPERATOR_TOKEN"):
        rac.run_admin_shell([sys.executable, "-c", "print(1)"])


def test_require_repo_root_cwd(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PETS_OPERATOR_TOKEN", "x")
    monkeypatch.chdir(tmp_path)
    import scripts.repo_admin_cli as rac

    with pytest.raises(RuntimeError, match="cwd"):
        rac.run_admin_shell([sys.executable, "-c", "print(1)"], repo_root_arg=ROOT)


def test_run_admin_shell_echo_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PETS_OPERATOR_TOKEN", "dev-token")
    monkeypatch.chdir(ROOT)
    import scripts.repo_admin_cli as rac

    cp = rac.run_admin_shell([sys.executable, "-c", "print(99)"])
    assert cp.returncode == 0
    assert "99" in (cp.stdout or "")
