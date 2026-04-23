"""
PETS — запуск командной строки из корня репозитория по **операторскому токену** (общий смысл с другими привилегированными действиями).

Требования одновременно:
  - непустая переменная окружения ``PETS_OPERATOR_TOKEN`` (секрет; не коммитить);
  - текущий рабочий каталог (cwd) строго равен корню репозитория (``MANIFEST.md`` + ``build_index.py``).

Пример (PowerShell, из корня PETS)::

  $env:PETS_OPERATOR_TOKEN = "your-long-secret"
  python scripts/repo_admin_cli.py -- python -c "print(1)"

Библиотека::

  from scripts.repo_admin_cli import run_admin_shell
  run_admin_shell([\"git\", \"status\"])
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

_REPO_ROOT_CACHE: Path | None = None


def find_repo_root(start: Path | None = None) -> Path:
    """Найти корень PETS по маркерам ``MANIFEST.md`` и ``build_index.py``."""
    p = (start or Path(__file__).resolve().parent.parent).resolve()
    for candidate in [p, *p.parents]:
        if (candidate / "MANIFEST.md").is_file() and (candidate / "build_index.py").is_file():
            return candidate
    raise FileNotFoundError("PETS repository root not found (need MANIFEST.md and build_index.py).")


def repo_root() -> Path:
    global _REPO_ROOT_CACHE
    if _REPO_ROOT_CACHE is None:
        _REPO_ROOT_CACHE = find_repo_root()
    return _REPO_ROOT_CACHE


def require_operator_token() -> None:
    if not (os.environ.get("PETS_OPERATOR_TOKEN") or "").strip():
        raise PermissionError(
            "Operator CLI disabled: set a non-empty PETS_OPERATOR_TOKEN in the environment."
        )


def require_running_from_repo_root(root: Path | None = None) -> Path:
    """Текущий cwd должен совпадать с корнем репо (защита от случайного запуска из другого места)."""
    r = (root or repo_root()).resolve()
    cwd = Path.cwd().resolve()
    if cwd != r:
        raise RuntimeError(
            "Admin CLI requires cwd to equal repository root.\n"
            f"  expected: {r}\n"
            f"  actual:   {cwd}"
        )
    return r


def run_admin_shell(
    argv: Sequence[str],
    *,
    repo_root_arg: Path | None = None,
    timeout: float | None = 120,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    """
    Выполнить команду ``argv`` (список аргументов, без shell=True) с ``cwd`` = корень репо.

    Перед вызовом: непустой ``PETS_OPERATOR_TOKEN`` и ``Path.cwd()`` == корень репозитория.
    """
    require_operator_token()
    root = require_running_from_repo_root(repo_root_arg)
    if not argv:
        raise ValueError("argv must be non-empty")
    return subprocess.run(
        list(argv),
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=check,
    )


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "--":
        args = args[1:]
    if not args:
        sys.stderr.write(
            "Usage (from repo root, with non-empty PETS_OPERATOR_TOKEN):\n"
            "  python scripts/repo_admin_cli.py -- <command> [args...]\n"
            "Example:\n"
            "  set PETS_OPERATOR_TOKEN=your-secret\n"
            "  python scripts/repo_admin_cli.py -- python -c \"print(42)\"\n"
        )
        return 2
    try:
        cp = run_admin_shell(args)
    except (PermissionError, RuntimeError, FileNotFoundError) as e:
        sys.stderr.write(f"{e}\n")
        return 1
    except subprocess.TimeoutExpired:
        sys.stderr.write("Command timed out.\n")
        return 124
    sys.stdout.write(cp.stdout or "")
    sys.stderr.write(cp.stderr or "")
    return int(cp.returncode or 0)


if __name__ == "__main__":
    raise SystemExit(main())
