#!/usr/bin/env python3
"""
Stable PETS Claude terminal launcher.

Default behavior:
- if a Claude API key is available in the environment, run a simple repo-local
  REPL over the Anthropic Messages API
- otherwise, ask for a one-time Claude API key and stay in the stable REPL

Use `--native` to force the native Claude Code CLI.
Use `--banner-only` for smoke tests.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import textwrap
import urllib.error
import urllib.request
from datetime import datetime, timezone
from getpass import getpass
from pathlib import Path

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-4-20250514"


def _find_repo_root() -> Path:
    p = Path(__file__).resolve().parent.parent
    for candidate in (p, *p.parents):
        if (candidate / "MANIFEST.md").is_file() and (candidate / "build_index.py").is_file():
            return candidate
    return p


def _git_branch(root: Path) -> str:
    head = root / ".git" / "HEAD"
    if not head.is_file():
        return "-"
    try:
        line = head.read_text(encoding="utf-8").strip()
        if line.startswith("ref: "):
            return line[5:].replace("refs/heads/", "") or "-"
        return (line[:12] + "...") if len(line) > 12 else line
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
    title = " PETS  .  Claude Terminal "
    sub = " stable API REPL for Windows-friendly input "
    inner = width - 2
    line_top = "╭" + "─" * (width - 2) + "╮"
    line_bot = "╰" + "─" * (width - 2) + "╯"
    sep = "├" + "─" * (width - 2) + "┤"

    def row(s: str, left: str, right: str = "│") -> str:
        pad = inner - len(s)
        if pad < 1:
            s = s[: max(1, inner - 3)] + "..."
            pad = inner - len(s)
        return left + s + (" " * pad) + right

    repo_s = f" repo   {root}"
    git_s = f" branch {_git_branch(root)}"
    if len(repo_s) > inner:
        repo_s = repo_s[: inner - 3] + "..."
    if len(git_s) > inner:
        git_s = git_s[: inner - 3] + "..."

    mode = "api-repl" if resolve_api_key() else "setup-needed"
    return [
        r + line_top + x,
        r + "│" + x + m + title.center(inner) + x + r + "│" + x,
        r + "│" + x + d + sub.center(inner) + x + r + "│" + x,
        r + sep + x,
        r + row(repo_s, "│", "│") + x,
        r + row(git_s, "│", "│") + x,
        r + line_bot + x,
        "",
        d + (" ▸ mode: " if color else "> mode: ") + g + mode + x,
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


def resolve_api_key() -> str | None:
    for env_name in ("POLYPHONIA_CLAUDE_API_KEY", "ANTHROPIC_API_KEY"):
        raw = (os.environ.get(env_name) or "").strip()
        if raw:
            return raw
    return None


def resolve_model() -> str:
    for env_name in ("POLYPHONIA_CLAUDE_MODEL", "ANTHROPIC_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL"):
        raw = (os.environ.get(env_name) or "").strip()
        if raw:
            return raw
    return DEFAULT_MODEL


def _prompt_for_api_key() -> str | None:
    print_banner()
    print("Claude API key is not configured for this terminal.")
    print("Paste an Anthropic API key to start the stable terminal.")
    print("The key stays only in this console session.")
    print("Press Enter to exit, or type /native to force the native Claude CLI.")
    print("")
    try:
        raw = getpass("anthropic key> ")
    except (EOFError, KeyboardInterrupt):
        print("")
        return None
    except Exception:
        try:
            raw = input("anthropic key> ")
        except (EOFError, KeyboardInterrupt):
            print("")
            return None
    raw = str(raw or "").strip()
    return raw or None


def _session_log_path(root: Path) -> Path:
    out_dir = root / "polyphonia_sessions" / "claude_terminal"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return out_dir / f"session-{stamp}.jsonl"


def _append_session_log(path: Path, role: str, text: str) -> None:
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "role": role,
        "text": text,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _system_prompt(root: Path) -> str:
    return (
        "You are Claude assisting inside the PETS repository. "
        "Be concise, practical, and code-aware. "
        f"Current repo root: {root}"
    )


def _extract_text_content(payload: dict) -> str:
    blocks = payload.get("content")
    if not isinstance(blocks, list):
        return ""
    parts: list[str] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            parts.append(str(block.get("text") or ""))
    return "\n\n".join(p.strip() for p in parts if str(p or "").strip()).strip()


def _wrap_for_terminal(text: str) -> str:
    width = max(50, _term_width() - 2)
    chunks: list[str] = []
    for para in str(text or "").splitlines():
        if not para.strip():
            chunks.append("")
            continue
        chunks.append(textwrap.fill(para, width=width, replace_whitespace=False))
    return "\n".join(chunks).rstrip()


def _request_messages_api(
    *,
    api_key: str,
    messages: list[dict[str, str]],
    model: str,
    system_prompt: str,
    timeout: float = 180.0,
    urlopen=urllib.request.urlopen,
    request_ctor=urllib.request.Request,
) -> str:
    body = {
        "model": model,
        "max_tokens": 1400,
        "system": system_prompt,
        "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
    }
    req = request_ctor(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "anthropic-version": API_VERSION,
            "x-api-key": api_key,
        },
        method="POST",
    )
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
    parsed = json.loads(raw)
    text = _extract_text_content(parsed)
    if text:
        return text
    stop_reason = str(parsed.get("stop_reason") or "").strip()
    return f"(empty response{': ' + stop_reason if stop_reason else ''})"


def _read_user_message() -> str:
    lines: list[str] = []
    prompt = "you> "
    while True:
        line = input(prompt)
        if not lines and line.strip().startswith("/"):
            return line.strip()
        if line.endswith("\\"):
            lines.append(line[:-1].rstrip())
            prompt = "...> "
            continue
        lines.append(line)
        return "\n".join(lines).strip()


def _print_help() -> None:
    print("Commands:")
    print("  /help   show help")
    print("  /clear  clear local conversation context")
    print("  /status show model and cwd")
    print("  /exit   quit")
    print("")
    print("Tips:")
    print("  - Press Enter to send")
    print(r"  - End a line with \ to continue on the next line")
    print("")


def run_api_repl(initial_prompt: str = "", *, api_key: str | None = None) -> int:
    root = _find_repo_root()
    api_key = api_key or resolve_api_key()
    if not api_key:
        print_banner()
        sys.stderr.write("error: Claude API key is missing.\n")
        sys.stderr.write("Set it in Polyphonia Settings -> Claude or paste it when prompted.\n")
        return 2

    model = resolve_model()
    log_path = _session_log_path(root)
    system_prompt = _system_prompt(root)
    messages: list[dict[str, str]] = []

    print_banner()
    print("Stable Claude terminal is ready.")
    print(f"Repo:   {root}")
    print(f"Model:  {model}")
    print(f"Log:    {log_path}")
    print("")
    _print_help()

    pending = initial_prompt.strip()
    while True:
        try:
            raw = pending or _read_user_message()
            pending = ""
        except EOFError:
            print("")
            return 0
        except KeyboardInterrupt:
            print("\n(use /exit to quit)\n")
            continue

        if not raw:
            continue
        if raw == "/exit":
            return 0
        if raw == "/help":
            _print_help()
            continue
        if raw == "/clear":
            messages = []
            print("Local conversation context cleared.\n")
            continue
        if raw == "/status":
            print(f"cwd: {root}")
            print(f"model: {model}")
            print(f"history turns: {len(messages)}")
            print("")
            continue

        messages.append({"role": "user", "content": raw})
        _append_session_log(log_path, "user", raw)
        print("\nclaude> thinking...\n")
        try:
            reply = _request_messages_api(
                api_key=api_key,
                messages=messages,
                model=model,
                system_prompt=system_prompt,
            )
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", errors="replace")
            except Exception:
                detail = str(exc)
            print(_wrap_for_terminal(f"error: HTTP {getattr(exc, 'code', '?')} {detail}"))
            print("")
            continue
        except Exception as exc:
            print(_wrap_for_terminal(f"error: {exc}"))
            print("")
            continue

        messages.append({"role": "assistant", "content": reply})
        _append_session_log(log_path, "assistant", reply)
        print(_wrap_for_terminal(reply))
        print("")


def run_native_claude(args: list[str]) -> int:
    print_banner()
    exe = resolve_claude_executable()
    if not exe:
        red, rst = ("\033[31m", "\033[0m") if _use_color() else ("", "")
        sys.stderr.write(f"{red}error:{rst} executable `claude` not found on PATH.\n")
        sys.stderr.write("Install Claude Code CLI and retry.\n")
        return 127
    try:
        os.execvp(exe, ["claude", *args])
    except OSError as exc:
        sys.stderr.write(f"exec failed: {exc}\n")
        return 126
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "--banner-only":
        print_banner()
        return 0
    if args and args[0] == "--native":
        return run_native_claude(args[1:])
    if os.environ.get("POLYPHONIA_CLAUDE_FORCE_NATIVE", "").strip() == "1":
        return run_native_claude(args)

    api_key = resolve_api_key()
    if not api_key:
        entered = _prompt_for_api_key()
        if entered == "/native":
            return run_native_claude(args)
        if not entered:
            return 2
        api_key = entered
        os.environ["POLYPHONIA_CLAUDE_API_KEY"] = api_key

    return run_api_repl(initial_prompt=" ".join(args).strip(), api_key=api_key)


if __name__ == "__main__":
    raise SystemExit(main())
