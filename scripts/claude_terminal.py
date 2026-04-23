#!/usr/bin/env python3
"""
Лёгкая оболочка запуска **Claude Code** (`claude` в PATH): баннер в духе «навороченного»
Linux-терминала (рамки Unicode, ANSI-цвета), затем `exec` в настоящий `claude` без обёртки TTY.

Запуск из корня репозитория::

  python scripts/claude_terminal.py
  python scripts/claude_terminal.py chat
  python scripts/claude_terminal.py --banner-only   # только баннер, без exec

Отключить цвета: переменная окружения ``NO_COLOR`` (как у многих CLI).
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def _find_repo_root() -> Path:
    p = Path(__file__).resolve().parent.parent
    for candidate in (p, *p.parents):
        if (candidate / "MANIFEST.md").is_file() and (candidate / "build_index.py").is_file():
            return candidate
    return p


def _git_branch(root: Path) -> str:
    head = root / ".git" / "HEAD"
    if not head.is_file():
        return "—"
    try:
        line = head.read_text(encoding="utf-8").strip()
        if line.startswith("ref: "):
            return line[5:].replace("refs/heads/", "") or "—"
        return (line[:12] + "…") if len(line) > 12 else line
    except OSError:
        return "?"


def _enable_windows_vt100() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        STD_OUTPUT_HANDLE = -11
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        kernel32 = ctypes.windll.kernel32
        h = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(h, ctypes.byref(mode)):
            kernel32.SetConsoleMode(h, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
    except Exception:
        pass


def _use_color() -> bool:
    if os.environ.get("NO_COLOR", "").strip():
        return False
    if not sys.stderr.isatty():
        return False
    if sys.platform == "win32":
        _enable_windows_vt100()
    return True


def _term_width() -> int:
    try:
        import shutil

        # Avoid passing a fd when stderr is a pipe (pytest, CI): can raise on Windows.
        w = shutil.get_terminal_size((88, 24)).columns
        return max(44, min(104, w))
    except OSError:
        return 72


def _sgr(*parts: str) -> str:
    return "\033[" + ";".join(parts) + "m"


def _banner_lines(root: Path, width: int, color: bool) -> list[str]:
    r = _sgr("0", "1", "38;5;45") if color else ""
    m = _sgr("0", "38;5;141") if color else ""
    d = _sgr("0", "2", "38;5;245") if color else ""
    g = _sgr("0", "1", "38;5;120") if color else ""
    x = _sgr("0") if color else ""
    title = " PETS  ·  Claude Code "
    sub = " adapter: .cursor  →  mirror: .claude "
    inner = width - 2
    line_top = "╭" + "─" * (width - 2) + "╮"
    line_bot = "╰" + "─" * (width - 2) + "╯"
    sep = "├" + "─" * (width - 2) + "┤"

    def row(s: str, left: str, right: str = "│") -> str:
        pad = inner - len(s)
        if pad < 1:
            s = s[: max(1, inner - 1)] + "…"
            pad = inner - len(s)
        return left + s + (" " * pad) + right

    repo_s = f" repo   {root}"
    git_s = f" branch {_git_branch(root)}"
    if len(repo_s) > inner:
        repo_s = repo_s[: inner - 1] + "…"
    if len(git_s) > inner:
        git_s = git_s[: inner - 1] + "…"

    return [
        r + line_top + x,
        r + "│" + x + m + title.center(inner) + x + r + "│" + x,
        r + "│" + x + d + sub.center(inner) + x + r + "│" + x,
        r + sep + x,
        r + row(repo_s, "│", "│") + x,
        r + row(git_s, "│", "│") + x,
        r + line_bot + x,
        "",
        d + (" ▸ exec: " if color else "> exec: ") + g + "claude" + x
        + (d + " " + " ".join(sys.argv[1:]) + x if len(sys.argv) > 1 else ""),
        "",
    ]


def print_banner() -> None:
    root = _find_repo_root()
    color = _use_color()
    w = _term_width()
    for line in _banner_lines(root, w, color):
        sys.stderr.write(line + "\n")
    sys.stderr.flush()


def resolve_claude_executable() -> str | None:
    """Resolve Claude CLI path even when PATH is incomplete on Windows."""
    exe = shutil.which("claude")
    if exe:
        return exe
    candidates: list[Path] = []
    appdata = (os.environ.get("APPDATA") or "").strip()
    localapp = (os.environ.get("LOCALAPPDATA") or "").strip()
    userprof = (os.environ.get("USERPROFILE") or "").strip()
    npm_prefix = (os.environ.get("npm_config_prefix") or "").strip()
    if appdata:
        candidates.append(Path(appdata) / "npm" / "claude.cmd")
    if localapp:
        candidates.append(Path(localapp) / "Programs" / "Claude" / "claude.exe")
    if userprof:
        up = Path(userprof)
        candidates.append(up / "scoop" / "shims" / "claude.cmd")
        candidates.append(up / ".local" / "bin" / "claude")
    if npm_prefix:
        candidates.append(Path(npm_prefix) / "claude.cmd")
        candidates.append(Path(npm_prefix) / "claude")
    for p in candidates:
        try:
            if p.is_file():
                return str(p)
        except Exception:
            continue
    return None


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "--banner-only":
        print_banner()
        return 0

    print_banner()
    exe = resolve_claude_executable()
    if not exe:
        red, rst = ("\033[31m", "\033[0m") if _use_color() else ("", "")
        sys.stderr.write(f"{red}error:{rst} executable `claude` not found on PATH.\n")
        sys.stderr.write("Install Claude Code CLI and retry.\n")
        return 127
    try:
        os.execvp(exe, ["claude", *args])
    except OSError as e:
        sys.stderr.write(f"exec failed: {e}\n")
        return 126
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
