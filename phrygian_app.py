import json
import os
import sys
import subprocess
import shutil
import hashlib
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import webview
from polyphonia_runtime import dialog_log
from polyphonia_runtime import musicxml_export
from polyphonia_runtime import openai_client
from polyphonia_runtime import session_store
from polyphonia_runtime import thread_store

_SESSION_OPENAI_KEY: str | None = None
_SESSION_CLAUDE_KEY: str | None = None
_SESSION_OPENAI_KEY_ORIGIN: str | None = None  # "ui" | "persisted"
_SESSION_CLAUDE_KEY_ORIGIN: str | None = None  # "ui" | "persisted"

_MAIN_WINDOW: Any | None = None
_ASSIST_WINDOW: Any | None = None


def _log(event: str, **fields: Any) -> None:
    """
    Console log for app activity. Always safe: never prints secrets.
    """
    try:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        ts = "time?"
    safe: dict[str, Any] = {}
    for k, v in fields.items():
        if k.lower() in ("key", "openai_key", "claude_key", "api_key", "authorization"):
            safe[k] = "<redacted>"
        else:
            safe[k] = v
    try:
        msg = json.dumps(safe, ensure_ascii=False)
    except Exception:
        msg = str(safe)
    try:
        print(f"[{ts}Z] {event} {msg}", flush=True)
    except Exception:
        pass


def _install_excepthook() -> None:
    prev = getattr(sys, "excepthook", None)

    def _hook(tp, val, tb):
        try:
            _log("unhandled_exception", type=str(getattr(tp, "__name__", tp)), message=str(val))
        except Exception:
            pass
        if callable(prev):
            prev(tp, val, tb)

    sys.excepthook = _hook


def _trace_enabled() -> bool:
    return (os.environ.get("POLYPHONIA_TRACE") or "").strip().lower() in ("1", "true", "yes", "on")


def _json_safe_load(s: str) -> Any | None:
    try:
        return json.loads(s)
    except Exception:
        return None


def _api_log_wrap(fn):
    """
    Decorator for PolyphoniaApi methods: logs call/return with duration.
    Never logs secrets; keys should be passed via *_key and redacted by _log.
    """

    def _wrapped(self, *args, **kwargs):
        t0 = time.perf_counter()
        name = getattr(fn, "__name__", "api_call")
        _log("api_call", method=name, argc=len(args), kwc=len(kwargs))
        try:
            out = fn(self, *args, **kwargs)
        except Exception as e:
            _log("api_exc", method=name, elapsed_ms=int((time.perf_counter() - t0) * 1000), message=str(e))
            raise
        elapsed = int((time.perf_counter() - t0) * 1000)
        # Try to interpret common JSON return shape
        ok = None
        err = None
        if isinstance(out, str):
            o = _json_safe_load(out)
            if isinstance(o, dict):
                ok = o.get("ok")
                err = o.get("error") or o.get("reason")
        _log("api_return", method=name, elapsed_ms=elapsed, ok=ok, error=err)
        return out

    return _wrapped


def choose_startup_mode() -> str:
    """
    Режим UI: ``offline`` (без Assist/GPT) или ``assist``.
    Неинтерактивно: ``POLYPHONIA_MODE=offline|assist``; без TTY по умолчанию ``offline``.
    """
    preset = os.environ.get("POLYPHONIA_MODE", "").strip().lower()
    if preset in ("offline", "assist"):
        return preset
    if not sys.stdin.isatty():
        return "offline"
    print("Polyphonia — выберите режим работы:", flush=True)
    print("  1 — Офлайн: только гриф и справка (без Assist и GPT)", flush=True)
    print("  2 — С ассистентами: панель Assist, GPT при настроенном ключе", flush=True)
    while True:
        raw = input("Введите 1 или 2 (по умолчанию 2): ").strip().lower()
        if raw in ("", "2", "assist"):
            return "assist"
        if raw in ("1", "offline"):
            return "offline"
        print("Неверный ввод. Укажите 1 или 2.", flush=True)

_OPENAI_SYSTEM = (
    "You are Polyphonia Assist: a guitar/scale and creative-riff ideation helper inside a "
    "deterministic offline-first app.\n"
    "Users may ask about: riff feel in the style of a band or guitarist, genre context, "
    "tone/arrangement hints, or the purpose / narrative role of a musical idea. Answer in "
    "that spirit when asked.\n"
    "Workflow: first infer the user's primary goal (composition, theory learning, arrangement/"
    "production, ear-training, or analysis/debug of an existing idea). If the goal is unclear, "
    "ask one concise clarifying question before giving a long answer.\n"
    "When answering, adapt to the inferred mode and mention assumptions briefly when needed.\n"
    "Rules: (1) Give reviewable suggestions, not final truth; label stylistic guesses as "
    "Assumption, not Confirmed. (2) Reuse deterministic context from Polyphonia whenever present "
    "(scale notes, selected chord, tuning, capo) and do not contradict it; if context is missing, "
    "say what is missing. (3) Be concise unless the user asks for depth. (4) No medical or legal "
    "advice. (5) When user asks for notation, tabs, or MusicXML, you MAY provide compact, "
    "import-ready snippets and examples in fenced code blocks when useful."
)


def get_base():
    """
    База ресурсов (index.html + assets/).

    В dev: каталог репозитория (рядом с phrygian_app.py).
    В frozen: предпочитаем каталог рядом с executable, если там лежит index.html (и/или assets),
    иначе fallback на _MEIPASS (типичный onefile bundle).
    """
    if getattr(sys, "frozen", False):
        try:
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            if os.path.exists(os.path.join(exe_dir, "index.html")):
                return exe_dir
            if os.path.exists(os.path.join(exe_dir, "assets")):
                return exe_dir
        except Exception:
            pass
        return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
    return os.path.dirname(os.path.abspath(__file__))


def get_resource_base() -> str:
    """
    База для чтения ресурсов (index.html + assets/), устойчиво к onedir/onefile и ярлыкам.

    Приоритет: каталог рядом с exe (если там есть index.html) → _MEIPASS (onefile) →
    каталог рядом с exe (если там есть assets) → каталог скрипта.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    exe_dir = os.path.dirname(os.path.abspath(getattr(sys, "executable", script_dir)))
    meipass = getattr(sys, "_MEIPASS", "")

    candidates: list[str] = []
    # onedir layout: index.html lives next to exe
    if exe_dir:
        candidates.append(exe_dir)
    # onefile layout: extracted temp dir
    if meipass:
        candidates.append(meipass)
    # fallback: script dir (dev)
    candidates.append(script_dir)

    for b in candidates:
        try:
            if os.path.exists(os.path.join(b, "index.html")) and os.path.exists(os.path.join(b, "assets")):
                return b
        except Exception:
            continue
    for b in candidates:
        try:
            if os.path.exists(os.path.join(b, "index.html")):
                return b
        except Exception:
            continue
    return get_base()


def _candidate_repo_roots() -> list[Path]:
    """Candidate roots for repo-local helper scripts in dev and frozen runs."""
    script_dir = Path(__file__).resolve().parent
    exe_dir = Path(os.path.abspath(getattr(sys, "executable", str(script_dir / "phrygian_app.py")))).parent
    paths: list[Path] = []
    raw_candidates = [
        Path(get_base()),
        Path(get_resource_base()),
        exe_dir,
        exe_dir.parent,
        script_dir,
        script_dir.parent,
        Path.cwd(),
    ]
    for p in raw_candidates:
        try:
            rp = p.resolve()
        except Exception:
            continue
        if rp not in paths:
            paths.append(rp)
    return paths


def _resolve_repo_root() -> Path:
    """Best-effort PETS repository root for UI hints and launcher helpers."""
    candidates = _candidate_repo_roots()
    for root in candidates:
        if (root / ".git").exists() and (root / "index.html").is_file() and (root / "phrygian_app.py").is_file():
            return root
    for root in candidates:
        if (root / "index.html").is_file() and (root / "scripts").is_dir():
            return root
    return candidates[0] if candidates else Path(get_base()).resolve()


def _resolve_claude_launcher() -> tuple[Path | None, Path | None]:
    """Locate scripts/claude_terminal.py from likely PETS roots."""
    for root in _candidate_repo_roots():
        script = root / "scripts" / "claude_terminal.py"
        if script.is_file():
            return root, script
    return None, None


def _resolve_claude_cli_executable() -> str | None:
    """Best-effort Claude CLI executable path on Windows and dev shells."""
    direct = shutil.which("claude")
    if direct:
        return direct
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


def _is_python_runtime_executable(path: str | os.PathLike[str] | None) -> bool:
    """True when the path looks like a real Python launcher, not the frozen app exe."""
    if not path:
        return False
    try:
        name = Path(path).name.lower()
    except Exception:
        return False
    return name in ("python", "python.exe", "pythonw", "pythonw.exe", "py", "py.exe")


def _resolve_python_launcher_command() -> list[str] | None:
    """
    Best-effort command prefix for running repo Python helpers from both dev and
    frozen Polyphonia builds on Windows.
    """
    seen: set[tuple[str, ...]] = set()

    def _remember(parts: list[str]) -> list[str] | None:
        key = tuple(parts)
        if key in seen:
            return None
        seen.add(key)
        return parts

    current = str(getattr(sys, "executable", "") or "").strip()
    if _is_python_runtime_executable(current):
        try:
            resolved = str(Path(current).resolve())
        except Exception:
            resolved = current
        remembered = _remember([resolved])
        if remembered:
            return remembered

    for tool in ("python", "py"):
        resolved = shutil.which(tool)
        if not resolved:
            continue
        parts = [resolved]
        if Path(resolved).name.lower() in ("py", "py.exe"):
            parts.append("-3")
        remembered = _remember(parts)
        if remembered:
            return remembered

    prefixes: list[Path] = []
    for raw in (getattr(sys, "prefix", ""), getattr(sys, "base_prefix", ""), getattr(sys, "exec_prefix", "")):
        if not raw:
            continue
        try:
            rp = Path(raw).resolve()
        except Exception:
            rp = Path(raw)
        if rp not in prefixes:
            prefixes.append(rp)

    localapp = (os.environ.get("LOCALAPPDATA") or "").strip()
    if localapp:
        py_home = Path(localapp) / "Programs" / "Python"
        try:
            for candidate_dir in sorted(py_home.glob("Python*"), reverse=True):
                if candidate_dir not in prefixes:
                    prefixes.append(candidate_dir)
        except Exception:
            pass

    for prefix in prefixes:
        for candidate in (prefix / "python.exe", prefix / "Scripts" / "python.exe", prefix / "py.exe"):
            try:
                if not candidate.is_file():
                    continue
            except Exception:
                continue
            parts = [str(candidate)]
            if candidate.name.lower() == "py.exe":
                parts.append("-3")
            remembered = _remember(parts)
            if remembered:
                return remembered
    return None


def _main_url(mode: str) -> str:
    base = get_resource_base()
    html_path = Path(base) / "index.html"
    try:
        url = html_path.resolve().as_uri()
    except Exception:
        url = "file:///" + str(html_path).replace("\\", "/")
    # IMPORTANT: avoid query params on file:// for WebView2 stability (ERR_FILE_NOT_FOUND observed).
    return url + "#poly_mode=" + (mode or "offline").strip().lower()


def _with_query(url: str, extra_query: str) -> str:
    if not extra_query:
        return url
    # If there is a fragment (#...), query must be inserted before it.
    base, frag = (url.split("#", 1) + [""])[:2]
    sep = "&" if "?" in base else "?"
    out = base + sep + extra_query.lstrip("?&")
    return out + ("#" + frag if frag else "")


def _is_windows() -> bool:
    return sys.platform.startswith("win")


def _get_screen_size() -> tuple[int, int] | None:
    if not _is_windows():
        return None
    try:
        import ctypes

        user32 = ctypes.windll.user32
        w = int(user32.GetSystemMetrics(0))
        h = int(user32.GetSystemMetrics(1))
        if w > 0 and h > 0:
            return (w, h)
    except Exception:
        return None
    return None


def _safe_move_resize(win: Any, x: int, y: int, w: int, h: int) -> None:
    try:
        mv = getattr(win, "move", None)
        if callable(mv):
            mv(int(x), int(y))
    except Exception:
        pass
    try:
        rs = getattr(win, "resize", None)
        if callable(rs):
            rs(int(w), int(h))
    except Exception:
        pass


def _safe_bring_to_front(win: Any) -> None:
    for name in ("bring_to_front", "focus"):
        try:
            fn = getattr(win, name, None)
            if callable(fn):
                fn()
                return
        except Exception:
            continue


def assist_dialogs_dir() -> Path:
    return session_store.dialogs_dir(get_base())


def assist_chats_dir() -> Path:
    return session_store.chats_dir(get_base())


def _resolve_openai_key() -> str | None:
    env = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if env:
        return env
    if _SESSION_OPENAI_KEY:
        return _SESSION_OPENAI_KEY.strip()
    return None


def _resolve_claude_key() -> str | None:
    env = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    if env:
        return env
    if _SESSION_CLAUDE_KEY:
        return _SESSION_CLAUDE_KEY.strip()
    return None


def _persisted_auth_path() -> Path:
    return session_store.auth_path(get_base())


def _load_persisted_auth() -> dict[str, Any]:
    return session_store.load_persisted_auth(get_base())


def _save_persisted_auth(patch: dict[str, Any]) -> None:
    session_store.save_persisted_auth(get_base(), patch)


def _forget_persisted_auth(*, openai: bool = False, claude: bool = False) -> None:
    session_store.forget_persisted_auth(get_base(), openai=openai, claude=claude)


def _bootstrap_session_keys_from_persisted_auth() -> None:
    """
    If user opted into "remember me", prefill session keys from disk.
    Env vars still win at runtime.
    """
    global _SESSION_OPENAI_KEY, _SESSION_CLAUDE_KEY, _SESSION_OPENAI_KEY_ORIGIN, _SESSION_CLAUDE_KEY_ORIGIN
    a = _load_persisted_auth()
    ok = str(a.get("openai_key") or "").strip()
    ck = str(a.get("claude_key") or "").strip()
    if ok and not _SESSION_OPENAI_KEY:
        _SESSION_OPENAI_KEY = ok
        _SESSION_OPENAI_KEY_ORIGIN = "persisted"
    if ck and not _SESSION_CLAUDE_KEY:
        _SESSION_CLAUDE_KEY = ck
        _SESSION_CLAUDE_KEY_ORIGIN = "persisted"


def _openai_key_id(key: str) -> str:
    return hashlib.sha256((key or "").encode("utf-8")).hexdigest()


def _resolve_openai_key_id() -> str | None:
    key = _resolve_openai_key()
    if not key:
        return None
    return _openai_key_id(key)


def _sanitize_thread_id(raw: str | None) -> str:
    return thread_store.sanitize_thread_id(raw)


def _threads_root_for_key(key_id: str) -> Path:
    return thread_store.threads_root(assist_chats_dir(), key_id)


def _thread_file_for_key(key_id: str, thread_id: str) -> Path:
    return thread_store.thread_file(assist_chats_dir(), key_id, thread_id)


def _append_thread_event(key_id: str, thread_id: str, event: dict[str, Any]) -> None:
    thread_store.append_thread_event(assist_chats_dir(), key_id, thread_id, event)


def _ensure_thread_file(key_id: str, thread_id: str, title: str = "") -> None:
    thread_store.ensure_thread_file(assist_chats_dir(), key_id, thread_id, title=title)


def _load_thread_events(key_id: str, thread_id: str, limit: int = 500) -> list[dict[str, Any]]:
    return thread_store.load_thread_events(assist_chats_dir(), key_id, thread_id, limit=limit)


def _list_threads_for_key(key_id: str) -> list[dict[str, Any]]:
    return thread_store.list_threads_for_key(assist_chats_dir(), key_id)


def _thread_openai_messages(key_id: str, thread_id: str, max_messages: int = 32, max_chars: int = 22000) -> list[dict[str, str]]:
    return thread_store.thread_openai_messages(
        assist_chats_dir(),
        key_id,
        thread_id,
        max_messages=max_messages,
        max_chars=max_chars,
    )


def _format_context_block(ctx: Any) -> str | None:
    if ctx is None:
        return None
    if isinstance(ctx, str):
        s = ctx.strip()
        if not s:
            return None
        return "Polyphonia context:\n" + s[:10000]
    if not isinstance(ctx, dict):
        try:
            s = json.dumps(ctx, ensure_ascii=False)
        except Exception:
            return None
        return "Polyphonia context:\n" + s[:10000]
    scale = ctx.get("scaleContext") if isinstance(ctx.get("scaleContext"), dict) else {}
    chord = ctx.get("selectedChord") if isinstance(ctx.get("selectedChord"), dict) else {}
    lines: list[str] = []
    lines.append("Polyphonia deterministic context:")
    lines.append(f"- instrument: {ctx.get('instrument') or ''}")
    lines.append(f"- tuning: {ctx.get('tuning') or ''}")
    lines.append(f"- capo: {ctx.get('capo')}")
    lines.append(f"- lefty: {ctx.get('lefty')}")
    if scale:
        lines.append(f"- scale root: {scale.get('rootName') or scale.get('rootCode') or ''}")
        lines.append(f"- scale code: {scale.get('scaleCode') or ''}")
        lines.append(f"- scale name: {scale.get('scaleName') or ''}")
        lines.append(f"- scale notes: {', '.join(scale.get('scaleNoteNames') or [])}")
    if chord:
        lines.append(f"- selected chord: {chord.get('chordName') or ''}")
        lines.append(f"- chord notes: {', '.join(chord.get('chordNoteNames') or [])}")
        lines.append(f"- chord degrees: {chord.get('chordDegrees') or ''}")
    riff = ctx.get("riffDraft")
    if riff:
        lines.append("- riff draft: present")
    return "\n".join(lines)[:10000]


def _goal_mode_system_hint(mode: str) -> str | None:
    m = (mode or "").strip().lower()
    if not m or m == "auto":
        return None
    mapping = {
        "compose": "Goal mode: Composer. Prioritize creating musical ideas, motifs, sections, and playable riffs.",
        "theory": "Goal mode: Theory. Prioritize clear interval/degree explanations and concise, checkable examples.",
        "production": "Goal mode: Production. Prioritize arrangement, tone, dynamics, and mix/recording guidance.",
        "practice": "Goal mode: Practice. Prioritize drills, progressive exercises, and concrete practice loops.",
        "analysis": "Goal mode: Analyze. Prioritize diagnosing issues in harmony/rhythm/voice-leading and proposing fixes.",
    }
    return mapping.get(m)


def should_show_startup_splash() -> bool:
    """Графическое окно выбора режима, если режим не задан заранее (CI/headless — без окна)."""
    preset = os.environ.get("POLYPHONIA_MODE", "").strip().lower()
    if preset in ("offline", "assist"):
        return False
    if os.environ.get("CI", "").strip().lower() in ("1", "true", "yes"):
        return False
    if os.environ.get("PETS_HEADLESS", "").strip() == "1":
        return False
    return True


def resolve_mode_without_splash() -> str:
    """Режим без стартового окна: env, CI, неинтерактивный stdin или консольный выбор."""
    preset = os.environ.get("POLYPHONIA_MODE", "").strip().lower()
    if preset in ("offline", "assist"):
        return preset
    if os.environ.get("CI", "").strip().lower() in ("1", "true", "yes"):
        return "offline"
    if os.environ.get("PETS_HEADLESS", "").strip() == "1":
        return "offline"
    if not sys.stdin.isatty():
        return "offline"
    return choose_startup_mode()


class PolyphoniaApi:
    """JS API: fullscreen + optional OpenAI chat (server-side key only)."""

    def __init__(self, ui_mode: str = "offline") -> None:
        self._ui_mode = (ui_mode or "offline").strip().lower()

    def fullscreen_toggle(self) -> None:
        wins = getattr(webview, "windows", None) or []
        if not wins:
            return
        win = wins[0]
        for name in ("toggle_fullscreen", "toggle_full_screen"):
            fn = getattr(win, name, None)
            if callable(fn):
                fn()
                return
        fs = getattr(win, "fullscreen", None)
        if isinstance(fs, bool):
            win.fullscreen = not fs

    @_api_log_wrap
    def save_musicxml(self, payload_json: str = "") -> str:
        """
        Save MusicXML text to local export directory.
        payload_json: {"filename":"...", "musicxml":"..."}
        """
        try:
            payload: dict[str, Any] = json.loads(payload_json) if payload_json else {}
        except json.JSONDecodeError as e:
            return json.dumps({"ok": False, "error": "invalid_json", "message": str(e)}, ensure_ascii=False)
        raw_xml = payload.get("musicxml")
        if not isinstance(raw_xml, str) or not raw_xml.strip():
            return json.dumps({"ok": False, "error": "empty_musicxml"}, ensure_ascii=False)
        try:
            p = musicxml_export.save_musicxml_copy(
                filename=str(payload.get("filename") or "polyphonia-export.musicxml"),
                musicxml=raw_xml,
            )
            return json.dumps({"ok": True, "path": str(p)}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": "write_failed", "message": str(e)}, ensure_ascii=False)

    @_api_log_wrap
    def log_client_event(self, payload_json: str = "") -> str:
        """
        Client-side (JS) logging bridge. payload_json:
        {event, message?, stack?, href?, data?}
        """
        try:
            payload: dict[str, Any] = json.loads(payload_json) if payload_json else {}
        except json.JSONDecodeError:
            payload = {"event": "bad_json", "raw": payload_json[:4000]}
        ev = str(payload.get("event") or "client_event")
        msg = str(payload.get("message") or "")[:2000]
        href = str(payload.get("href") or "")[:400]
        # Avoid naming collision with _log(event=...) positional argument.
        _log("client", client_event=ev, message=msg, href=href)
        return json.dumps({"ok": True}, ensure_ascii=False)

    @_api_log_wrap
    def get_repo_root(self, _payload_json: str = "") -> str:
        """Абсолютный путь к корню репозитория (для подсказок в UI)."""
        try:
            return json.dumps({"ok": True, "root": str(_resolve_repo_root())}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": "resolve_failed", "message": str(e)}, ensure_ascii=False)

    @_api_log_wrap
    def open_assist_window(self, _payload_json: str = "") -> str:
        """
        Открепить Assist/GPT в отдельное окно (внутри pywebview).
        Возвращает JSON: ``{ok:true}`` или ``{ok:false,error,...}``.
        """
        if self._ui_mode != "assist":
            return json.dumps({"ok": False, "error": "offline_mode"}, ensure_ascii=False)
        global _ASSIST_WINDOW
        try:
            if _ASSIST_WINDOW is not None:
                if bool(getattr(_ASSIST_WINDOW, "closed", False)):
                    _ASSIST_WINDOW = None
                else:
                    _safe_bring_to_front(_ASSIST_WINDOW)
                    return json.dumps({"ok": True, "reused": True}, ensure_ascii=False)
        except Exception:
            _ASSIST_WINDOW = None

        try:
            # Keep navigation in hash only: query params on file:// can break on WebView2.
            url = _main_url("assist") + "&poly_view=assist"
            _ASSIST_WINDOW = webview.create_window(
                "Polyphonia — Assist",
                url,
                width=560,
                height=900,
                resizable=True,
                js_api=self,
            )
            try:
                threading.Timer(0.05, lambda: _safe_bring_to_front(_ASSIST_WINDOW)).start()
            except Exception:
                pass
            return json.dumps({"ok": True, "created": True}, ensure_ascii=False)
        except Exception as e:
            _ASSIST_WINDOW = None
            return json.dumps({"ok": False, "error": "create_failed", "message": str(e)}, ensure_ascii=False)

    @_api_log_wrap
    def tile_windows(self, payload_json: str = "") -> str:
        """
        Разделение экрана 50/50 (main + assist) под Windows.
        ``payload_json`` (опционально): ``{"mode":"vertical"}`` (пока только vertical).
        """
        global _MAIN_WINDOW, _ASSIST_WINDOW
        if not _is_windows():
            return json.dumps({"ok": False, "error": "not_supported"}, ensure_ascii=False)
        if _MAIN_WINDOW is None:
            wins = getattr(webview, "windows", None) or []
            if wins:
                _MAIN_WINDOW = wins[0]
        if _MAIN_WINDOW is None or _ASSIST_WINDOW is None:
            return json.dumps({"ok": False, "error": "missing_windows"}, ensure_ascii=False)
        sz = _get_screen_size()
        if not sz:
            return json.dumps({"ok": False, "error": "screen_unknown"}, ensure_ascii=False)
        sw, sh = sz
        half = max(320, int(sw // 2))
        _safe_move_resize(_MAIN_WINDOW, 0, 0, half, sh)
        _safe_move_resize(_ASSIST_WINDOW, half, 0, sw - half, sh)
        try:
            _safe_bring_to_front(_ASSIST_WINDOW)
        except Exception:
            pass
        return json.dumps({"ok": True, "screen": {"w": sw, "h": sh}}, ensure_ascii=False)

    @_api_log_wrap
    def launch_claude_terminal_window(self, _payload_json: str = "") -> str:
        """Открыть Claude Code launcher в отдельном консольном окне (Windows)."""
        if not _is_windows():
            return json.dumps({"ok": False, "error": "not_supported"}, ensure_ascii=False)
        try:
            repo_path, script = _resolve_claude_launcher()
            if repo_path is None or script is None:
                return json.dumps(
                    {
                        "ok": False,
                        "error": "missing_launcher",
                        "message": "Не найден scripts/claude_terminal.py рядом с приложением. Запускайте из корня репозитория PETS.",
                        "base": str(_resolve_repo_root()),
                    },
                    ensure_ascii=False,
                )
            cli_exe = _resolve_claude_cli_executable()
            has_claude = bool(cli_exe)
            claude_key = _resolve_claude_key()
            creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0x00000010)
            env = os.environ.copy()
            py_cmd = _resolve_python_launcher_command()
            if has_claude or py_cmd:
                if has_claude:
                    exe_dir = str(Path(cli_exe or "").resolve().parent)
                    if exe_dir:
                        path_parts = (env.get("PATH") or "").split(os.pathsep)
                        if exe_dir not in path_parts:
                            env["PATH"] = exe_dir + os.pathsep + (env.get("PATH") or "")
                # Native Claude on Windows has had TUI input freezes in some
                # terminals; prefer a conservative env instead of forcing TERM.
                env["CLAUDE_CODE_DISABLE_TERMINAL_TITLE"] = "1"
                env.pop("TERM", None)
                if claude_key:
                    env["POLYPHONIA_CLAUDE_API_KEY"] = claude_key
                    env.setdefault("ANTHROPIC_API_KEY", claude_key)
                    env.setdefault("POLYPHONIA_CLAUDE_MODEL", "claude-sonnet-4-20250514")
                sc = str(Path(script).resolve())
                launcher_mode = "direct_cli"
                if py_cmd:
                    launcher_mode = "python_wrapper"
                    launch_cmd = py_cmd + [sc]
                else:
                    launch_cmd = [str(Path(cli_exe or "claude").resolve())]
                # Use a real Python launcher when available so frozen Polyphonia
                # doesn't try to execute scripts via polyphonia.exe.
                # Switch console to UTF-8, but do not force TERM on Windows:
                # Claude's native TUI is more stable when it probes the console itself.
                cmdline = 'chcp 65001>nul & title PETS Claude Code & ' + subprocess.list2cmdline(launch_cmd)
                cmd = ["cmd.exe", "/k", cmdline]
                subprocess.Popen(cmd, cwd=str(repo_path), creationflags=creationflags, env=env)
            else:
                launcher_mode = "missing_cli"
                msg = "chcp 65001>nul & echo Claude CLI не найден в PATH. Установите Claude Code и выполните: claude login"
                cmd = ["cmd.exe", "/k", msg]
                subprocess.Popen(cmd, cwd=str(repo_path), creationflags=creationflags)
            return json.dumps(
                {
                    "ok": True,
                    "has_claude": has_claude,
                    "claude_exe": cli_exe or "",
                    "launcher_mode": launcher_mode,
                    "key_source": "available" if claude_key else "missing",
                },
                ensure_ascii=False,
            )
        except Exception as e:
            return json.dumps({"ok": False, "error": "spawn_failed", "message": str(e)}, ensure_ascii=False)

    @_api_log_wrap
    def set_poly_mode(self, payload_json: str) -> str:
        """
        Смена режима UI/API в рамках текущей сессии pywebview.
        ``payload_json``: ``{"mode": "offline"|"assist"}``. Следующий холодный старт
        приложения по-прежнему определяется ``POLYPHONIA_MODE`` / интерактивным выбором.
        """
        try:
            payload: dict[str, Any] = json.loads(payload_json)
        except json.JSONDecodeError as e:
            return json.dumps({"ok": False, "error": "invalid_json", "message": str(e)})
        m = str(payload.get("mode") or "").strip().lower()
        if m not in ("offline", "assist"):
            return json.dumps(
                {
                    "ok": False,
                    "error": "invalid_mode",
                    "message": "mode must be offline or assist",
                },
                ensure_ascii=False,
            )
        self._ui_mode = m
        return json.dumps({"ok": True, "mode": m}, ensure_ascii=False)

    @_api_log_wrap
    def launch_main(self, payload_json: str) -> str:
        """
        Стартовое окно: применить режим и сессионные ключи, открыть основной ``index.html``.
        ``payload_json``: ``{"mode":"offline"|"assist","openai_key":"...","claude_key":"..."}``.
        """
        try:
            payload: dict[str, Any] = json.loads(payload_json)
        except json.JSONDecodeError as e:
            _log("launch_main_invalid_json", message=str(e))
            return json.dumps({"ok": False, "error": "invalid_json", "message": str(e)})
        mode = str(payload.get("mode") or "").strip().lower()
        if mode not in ("offline", "assist"):
            _log("launch_main_invalid_mode", mode=mode)
            return json.dumps(
                {"ok": False, "error": "invalid_mode", "message": "mode must be offline or assist"},
                ensure_ascii=False,
            )
        global _SESSION_OPENAI_KEY, _SESSION_CLAUDE_KEY
        openai_in = str(payload.get("openai_key") or "").strip()
        claude_in = str(payload.get("claude_key") or "").strip()
        if mode == "assist":
            if openai_in:
                _SESSION_OPENAI_KEY = openai_in
            if claude_in:
                _SESSION_CLAUDE_KEY = claude_in
        else:
            _SESSION_OPENAI_KEY = None
            _SESSION_CLAUDE_KEY = None
        self._ui_mode = mode
        os.environ["POLYPHONIA_MODE"] = mode
        _log("launch_main", mode=mode, openai_key_set=bool(openai_in), claude_key_set=bool(claude_in))
        wins = getattr(webview, "windows", None) or []
        if not wins:
            return json.dumps({"ok": False, "error": "no_window", "message": "No webview window."})
        win = wins[0]
        base = get_resource_base()
        html_path = Path(base) / "index.html"
        if not html_path.exists():
            # Return a clear error to the splash instead of navigating into a blank/error page.
            return json.dumps(
                {
                    "ok": False,
                    "error": "index_not_found",
                    "message": f"index.html not found at: {html_path}",
                    "base": base,
                    "exe_dir": os.path.dirname(os.path.abspath(getattr(sys, 'executable', ''))),
                    "meipass": getattr(sys, "_MEIPASS", ""),
                },
                ensure_ascii=False,
            )
        main_url = _main_url(mode)
        # IMPORTANT: do not navigate synchronously inside a JS->Python call.
        # On some pywebview backends, immediate navigation can tear down the JS context
        # before the return-value callback executes, causing a JS TypeError.
        def _nav() -> None:
            try:
                win.load_url(main_url)
            except Exception:
                return
            try:
                r = getattr(win, "resize", None)
                if callable(r):
                    r(1400, 900)
            except Exception:
                pass
            try:
                st = getattr(win, "set_title", None)
                if callable(st):
                    st("Polyphonia")
            except Exception:
                pass

        threading.Timer(0.05, _nav).start()
        return json.dumps({"ok": True, "mode": mode}, ensure_ascii=False)

    @_api_log_wrap
    def set_claude_api_key(self, key: str) -> str:
        """Сессионный ключ Anthropic (Claude) в RAM; пустая строка сбрасывает."""
        if self._ui_mode == "offline":
            return "offline_mode"
        global _SESSION_CLAUDE_KEY
        k = (key or "").strip()
        _SESSION_CLAUDE_KEY = k or None
        global _SESSION_CLAUDE_KEY_ORIGIN
        _SESSION_CLAUDE_KEY_ORIGIN = "ui" if _SESSION_CLAUDE_KEY else None
        return "ok" if _SESSION_CLAUDE_KEY else "cleared"

    @_api_log_wrap
    def set_claude_api_key_persist(self, payload_json: str = "") -> str:
        """
        Set Claude key for this session; optionally persist to disk.
        payload_json: {"key":"sk-ant-...", "remember": true|false}
        """
        if self._ui_mode == "offline":
            return json.dumps({"ok": False, "error": "offline_mode"}, ensure_ascii=False)
        try:
            payload: dict[str, Any] = json.loads(payload_json) if payload_json else {}
        except json.JSONDecodeError as e:
            return json.dumps({"ok": False, "error": "invalid_json", "message": str(e)}, ensure_ascii=False)
        k = str(payload.get("key") or "").strip()
        remember = bool(payload.get("remember"))
        global _SESSION_CLAUDE_KEY, _SESSION_CLAUDE_KEY_ORIGIN
        _SESSION_CLAUDE_KEY = k or None
        _SESSION_CLAUDE_KEY_ORIGIN = "ui" if _SESSION_CLAUDE_KEY else None
        if remember and _SESSION_CLAUDE_KEY:
            _save_persisted_auth({"claude_key": _SESSION_CLAUDE_KEY})
            return json.dumps({"ok": True, "status": "ok", "remembered": True}, ensure_ascii=False)
        return json.dumps({"ok": True, "status": "ok" if _SESSION_CLAUDE_KEY else "cleared", "remembered": False}, ensure_ascii=False)

    @_api_log_wrap
    def forget_claude_api_key_persisted(self, _payload_json: str = "") -> str:
        """Remove persisted Claude key from disk (does not touch env)."""
        _forget_persisted_auth(claude=True)
        return json.dumps({"ok": True}, ensure_ascii=False)

    @_api_log_wrap
    def get_claude_connection(self, _payload_json: str = "") -> str:
        """Сводка источника ключа Claude (env > session), без раскрытия секрета."""
        if self._ui_mode == "offline":
            return json.dumps(
                {
                    "ok": True,
                    "ui_mode": "offline",
                    "source": "none",
                    "session_origin": None,
                    "persisted": bool(str(_load_persisted_auth().get("claude_key") or "").strip()),
                },
                ensure_ascii=False,
            )
        env_set = bool((os.environ.get("ANTHROPIC_API_KEY") or "").strip())
        session_set = bool(_SESSION_CLAUDE_KEY and str(_SESSION_CLAUDE_KEY).strip())
        if env_set:
            source = "env"
        elif session_set:
            source = "session"
        else:
            source = "none"
        return json.dumps(
            {
                "ok": True,
                "ui_mode": "assist",
                "source": source,
                "session_origin": _SESSION_CLAUDE_KEY_ORIGIN if source == "session" else None,
                "persisted": bool(str(_load_persisted_auth().get("claude_key") or "").strip()),
            },
            ensure_ascii=False,
        )

    @_api_log_wrap
    def set_openai_api_key(self, key: str) -> str:
        """Store API key in process RAM for this session only (empty string clears)."""
        if self._ui_mode == "offline":
            return "offline_mode"
        global _SESSION_OPENAI_KEY
        k = (key or "").strip()
        _SESSION_OPENAI_KEY = k or None
        global _SESSION_OPENAI_KEY_ORIGIN
        _SESSION_OPENAI_KEY_ORIGIN = "ui" if _SESSION_OPENAI_KEY else None
        return "ok" if _SESSION_OPENAI_KEY else "cleared"

    @_api_log_wrap
    def set_openai_api_key_persist(self, payload_json: str = "") -> str:
        """
        Set OpenAI key for this session; optionally persist to disk.
        payload_json: {"key":"sk-...", "remember": true|false}
        """
        if self._ui_mode == "offline":
            return json.dumps({"ok": False, "error": "offline_mode"}, ensure_ascii=False)
        try:
            payload: dict[str, Any] = json.loads(payload_json) if payload_json else {}
        except json.JSONDecodeError as e:
            return json.dumps({"ok": False, "error": "invalid_json", "message": str(e)}, ensure_ascii=False)
        k = str(payload.get("key") or "").strip()
        remember = bool(payload.get("remember"))
        global _SESSION_OPENAI_KEY, _SESSION_OPENAI_KEY_ORIGIN
        _SESSION_OPENAI_KEY = k or None
        _SESSION_OPENAI_KEY_ORIGIN = "ui" if _SESSION_OPENAI_KEY else None
        if remember and _SESSION_OPENAI_KEY:
            _save_persisted_auth({"openai_key": _SESSION_OPENAI_KEY})
            return json.dumps({"ok": True, "status": "ok", "remembered": True}, ensure_ascii=False)
        return json.dumps({"ok": True, "status": "ok" if _SESSION_OPENAI_KEY else "cleared", "remembered": False}, ensure_ascii=False)

    @_api_log_wrap
    def forget_openai_api_key_persisted(self, _payload_json: str = "") -> str:
        """Remove persisted OpenAI key from disk (does not touch env)."""
        _forget_persisted_auth(openai=True)
        return json.dumps({"ok": True}, ensure_ascii=False)

    @_api_log_wrap
    def get_openai_connection(self, _payload_json: str = "") -> str:
        """
        Сводка для UI: откуда берётся ключ (env > session), без раскрытия секрета.
        """
        if self._ui_mode == "offline":
            return json.dumps(
                {
                    "ok": True,
                    "ui_mode": "offline",
                    "source": "none",
                    "model_default": openai_client.default_openai_model(os.environ),
                    "session_origin": None,
                    "persisted": bool(str(_load_persisted_auth().get("openai_key") or "").strip()),
                },
                ensure_ascii=False,
            )
        env_set = bool((os.environ.get("OPENAI_API_KEY") or "").strip())
        session_set = bool(_SESSION_OPENAI_KEY and str(_SESSION_OPENAI_KEY).strip())
        if env_set:
            source = "env"
        elif session_set:
            source = "session"
        else:
            source = "none"
        model = openai_client.default_openai_model(os.environ)
        return json.dumps(
            {
                "ok": True,
                "ui_mode": "assist",
                "source": source,
                "model_default": model,
                "session_origin": _SESSION_OPENAI_KEY_ORIGIN if source == "session" else None,
                "persisted": bool(str(_load_persisted_auth().get("openai_key") or "").strip()),
            },
            ensure_ascii=False,
        )

    @_api_log_wrap
    def get_openai_identity(self, _payload_json: str = "") -> str:
        """Stable key fingerprint for chat storage (never exposes the key)."""
        conn = json.loads(self.get_openai_connection())
        key_id = _resolve_openai_key_id()
        return json.dumps(
            {
                "ok": True,
                "ui_mode": conn.get("ui_mode"),
                "source": conn.get("source"),
                "model_default": conn.get("model_default"),
                "key_id": key_id or "",
            },
            ensure_ascii=False,
        )

    @_api_log_wrap
    def list_openai_threads(self, payload_json: str = "") -> str:
        if self._ui_mode == "offline":
            return json.dumps({"ok": False, "error": "offline_mode"}, ensure_ascii=False)
        try:
            payload: dict[str, Any] = json.loads(payload_json) if payload_json else {}
        except json.JSONDecodeError as e:
            return json.dumps({"ok": False, "error": "invalid_json", "message": str(e)}, ensure_ascii=False)
        key_id = str(payload.get("key_id") or "").strip() or (_resolve_openai_key_id() or "")
        if not key_id:
            return json.dumps({"ok": False, "error": "missing_key_id"}, ensure_ascii=False)
        threads = _list_threads_for_key(key_id)
        return json.dumps({"ok": True, "key_id": key_id, "threads": threads}, ensure_ascii=False)

    @_api_log_wrap
    def new_openai_thread(self, payload_json: str = "") -> str:
        if self._ui_mode == "offline":
            return json.dumps({"ok": False, "error": "offline_mode"}, ensure_ascii=False)
        try:
            payload: dict[str, Any] = json.loads(payload_json) if payload_json else {}
        except json.JSONDecodeError as e:
            return json.dumps({"ok": False, "error": "invalid_json", "message": str(e)}, ensure_ascii=False)
        key_id = str(payload.get("key_id") or "").strip() or (_resolve_openai_key_id() or "")
        if not key_id:
            return json.dumps({"ok": False, "error": "missing_key_id"}, ensure_ascii=False)
        title = str(payload.get("title") or "").strip()[:140]
        thread_id = _sanitize_thread_id(payload.get("thread_id") or ("t-" + uuid.uuid4().hex[:12]))
        _ensure_thread_file(key_id, thread_id, title=title)
        return json.dumps({"ok": True, "key_id": key_id, "thread_id": thread_id}, ensure_ascii=False)

    @_api_log_wrap
    def load_openai_thread(self, payload_json: str = "") -> str:
        if self._ui_mode == "offline":
            return json.dumps({"ok": False, "error": "offline_mode"}, ensure_ascii=False)
        try:
            payload: dict[str, Any] = json.loads(payload_json) if payload_json else {}
        except json.JSONDecodeError as e:
            return json.dumps({"ok": False, "error": "invalid_json", "message": str(e)}, ensure_ascii=False)
        key_id = str(payload.get("key_id") or "").strip() or (_resolve_openai_key_id() or "")
        if not key_id:
            return json.dumps({"ok": False, "error": "missing_key_id"}, ensure_ascii=False)
        thread_id = _sanitize_thread_id(payload.get("thread_id") or "default")
        limit = int(payload.get("limit") or 200)
        limit = max(1, min(1000, limit))
        events = _load_thread_events(key_id, thread_id, limit=limit)
        rows: list[dict[str, Any]] = []
        for e in events:
            role = str(e.get("role") or "")
            if role not in ("user", "assistant", "gpt", "system", "gpt_error"):
                continue
            text = str(e.get("text") or "")
            if not text:
                continue
            # Keep backward-compatible names for UI rendering.
            ui_role = "gpt" if role == "assistant" else role
            rows.append({"ts": e.get("ts"), "role": ui_role, "text": text})
        return json.dumps(
            {"ok": True, "key_id": key_id, "thread_id": thread_id, "messages": rows},
            ensure_ascii=False,
        )

    @_api_log_wrap
    def openai_ping(self, _payload: str = "") -> str:
        """Лёгкий GET /v1/models для проверки ключа (чтение ответа ограничено)."""
        if self._ui_mode == "offline":
            return json.dumps(
                {
                    "ok": False,
                    "error": "offline_mode",
                    "message": "Режим офлайн.",
                },
                ensure_ascii=False,
            )
        key = _resolve_openai_key()
        if not key:
            return json.dumps(
                {
                    "ok": False,
                    "error": "missing_api_key",
                    "message": "Нет ключа: OPENAI_API_KEY или сессионный ключ.",
                },
                ensure_ascii=False,
            )
        result = openai_client.ping_models(
            key,
            timeout=25,
            read_limit=16384,
            urlopen=urllib.request.urlopen,
            request_ctor=urllib.request.Request,
        )
        if result.get("ok"):
            _log("openai_ping", ok=True, http_status=result.get("http_status"))
        return json.dumps(result, ensure_ascii=False)

    @_api_log_wrap
    def validate_openai_key(self, payload_json: str = "") -> str:
        """
        Проверка ключа OpenAI, не сохраняя его в сессию.
        payload_json: {"key":"sk-..."} (опционально). Если key пустой, используется текущий resolved key.
        """
        # Allow validation even in offline mode (startup splash can start in offline ui_mode).
        key_override = ""
        if payload_json:
            try:
                payload: dict[str, Any] = json.loads(payload_json)
                key_override = str(payload.get("key") or "").strip()
            except json.JSONDecodeError:
                key_override = ""
        key = key_override or (_resolve_openai_key() or "")
        if not key:
            return json.dumps({"ok": False, "error": "missing_api_key", "message": "Нет ключа OpenAI."}, ensure_ascii=False)
        model = openai_client.default_openai_model(os.environ)
        result = openai_client.validate_key_with_chat_probe(
            key,
            model=model,
            urlopen=urllib.request.urlopen,
            request_ctor=urllib.request.Request,
        )
        return json.dumps(result, ensure_ascii=False)

    @_api_log_wrap
    def validate_claude_key(self, payload_json: str = "") -> str:
        """
        Лёгкая проверка формата ключа Anthropic (без сетевого вызова, т.к. Claude CLI отдельно).
        payload_json: {"key":"sk-ant-..."}.
        """
        # Allow validation even in offline mode (startup splash starts in offline ui_mode).
        try:
            payload: dict[str, Any] = json.loads(payload_json) if payload_json else {}
        except json.JSONDecodeError:
            payload = {}
        k = str(payload.get("key") or "").strip()
        if not k:
            return json.dumps({"ok": False, "error": "missing_key", "message": "Ключ Claude пустой."}, ensure_ascii=False)
        # Format-only heuristic
        if not k.startswith("sk-ant-"):
            return json.dumps({"ok": False, "error": "bad_format", "message": "Ожидается формат sk-ant-…"}, ensure_ascii=False)
        if len(k) < 18:
            return json.dumps({"ok": False, "error": "too_short", "message": "Ключ слишком короткий."}, ensure_ascii=False)
        return json.dumps({"ok": True, "message": "Формат ключа выглядит корректно."}, ensure_ascii=False)

    @_api_log_wrap
    def append_assist_dialog_md(self, payload_json: str) -> str:
        """
        Append one Assist message to a daily Markdown file under
        ``polyphonia_sessions/dialogs/`` (gitignored). ``payload_json``:
        ``{"role": "user"|"system"|"gpt"|"gpt_error"|..., "text": "..."}``.
        Рекомендуемые роли: ``user``, ``system`` (интерфейс), ``gpt`` (ответ OpenAI), ``gpt_error`` (ошибка запроса/ответа API).
        """
        if self._ui_mode != "assist":
            return json.dumps({"ok": False, "reason": "offline_mode"})
        try:
            payload: dict[str, Any] = json.loads(payload_json)
        except json.JSONDecodeError as e:
            return json.dumps({"ok": False, "error": "invalid_json", "message": str(e)})
        role = str(payload.get("role") or "note").strip().replace("\n", " ")[:48]
        text = str(payload.get("text") or "")
        path = dialog_log.append_dialog_markdown(get_base(), role=role, text=text)
        return json.dumps({"ok": True, "path": str(path.resolve())}, ensure_ascii=False)

    @_api_log_wrap
    def openai_chat(self, payload_json: str) -> str:
        """
        Chat Completions from the page. ``payload_json``:
        ``{"user_text": str, "include_context": bool, "context_json": str|object,
        "model": str optional, "thread_id": str optional, "goal_mode": str optional}``.
        Returns JSON string ``{"ok": true, "content": "..."}`` or ``{"ok": false, ...}``.
        """
        if self._ui_mode == "offline":
            _log("openai_chat_blocked_offline")
            return json.dumps(
                {
                    "ok": False,
                    "error": "offline_mode",
                    "message": "Сессия в режиме «офлайн»: Assist / GPT отключены.",
                }
            )
        key = _resolve_openai_key()
        if not key:
            _log("openai_chat_missing_key")
            return json.dumps(
                {
                    "ok": False,
                    "error": "missing_api_key",
                    "message": "Set OPENAI_API_KEY or use «session key» in the Assist panel.",
                }
            )

        try:
            payload: dict[str, Any] = json.loads(payload_json)
        except json.JSONDecodeError as e:
            _log("openai_chat_invalid_json", message=str(e))
            return json.dumps({"ok": False, "error": "invalid_json", "message": str(e)})

        user_text = (payload.get("user_text") or "").strip()
        if not user_text:
            return json.dumps({"ok": False, "error": "empty_user", "message": "Empty message."})
        if len(user_text) > 12000:
            user_text = user_text[:12000] + "\n…(truncated)"

        model = (payload.get("model") or openai_client.default_openai_model(os.environ)).strip()
        include_ctx = bool(payload.get("include_context"))
        goal_mode = str(payload.get("goal_mode") or "auto").strip().lower()
        key_id = _openai_key_id(key)
        thread_id = _sanitize_thread_id(payload.get("thread_id") or "default")
        _ensure_thread_file(key_id, thread_id, title=str(user_text).strip()[:80])
        trace_id = str(payload.get("client_trace_id") or "").strip()[:96] or None
        _log(
            "openai_chat_request",
            model=model,
            include_context=include_ctx,
            goal_mode=goal_mode,
            user_len=len(user_text),
            trace_id=trace_id,
            thread_id=thread_id,
        )
        ctx = payload.get("context_json")
        ctx_block = _format_context_block(ctx) if include_ctx else None

        goal_hint = _goal_mode_system_hint(goal_mode)
        body = openai_client.build_chat_body(
            system_prompt=_OPENAI_SYSTEM,
            goal_hint=goal_hint,
            context_block=ctx_block,
            history_messages=_thread_openai_messages(key_id, thread_id),
            user_text=user_text,
            model=model,
            temperature=0.6,
            max_tokens=1200,
        )
        transport = None
        try:
            t0 = time.perf_counter()
            transport = openai_client.post_chat_completion(
                key,
                body,
                timeout=90,
                urlopen=urllib.request.urlopen,
                request_ctor=urllib.request.Request,
            )
            if _trace_enabled():
                if transport.get("ok"):
                    _log("openai_chat_http", trace_id=trace_id, http_status=transport.get("http_status"), elapsed_ms=int((time.perf_counter() - t0) * 1000))
                elif transport.get("error") == "http_error":
                    _log("openai_chat_http_error", trace_id=trace_id, status=transport.get("status"))
                elif transport.get("error") == "network":
                    _log("openai_chat_network_error", trace_id=trace_id, message=str(transport.get("message") or ""))
                else:
                    _log("openai_chat_request_failed", trace_id=trace_id, message=str(transport.get("message") or ""))
        except Exception:
            transport = {"ok": False, "error": "request_failed", "message": "transport_wrapper_failed"}

        if not transport.get("ok"):
            _append_thread_event(key_id, thread_id, {"role": "user", "text": user_text, "trace_id": trace_id, "model": model})
            gpt_error_event = {
                "role": "gpt_error",
                "text": str(transport.get("message") or ""),
                "trace_id": trace_id,
            }
            if transport.get("error") == "http_error" and transport.get("status") is not None:
                gpt_error_event["status"] = transport.get("status")
            else:
                gpt_error_event["error"] = transport.get("error")
            _append_thread_event(
                key_id,
                thread_id,
                gpt_error_event,
            )
            out = {
                "ok": False,
                "error": transport.get("error"),
                "message": str(transport.get("message") or ""),
                "trace_id": trace_id,
                "thread_id": thread_id,
                "key_id": key_id,
            }
            if transport.get("status") is not None:
                out["status"] = transport.get("status")
            return json.dumps(out)

        parsed = openai_client.parse_chat_completion_content(str(transport.get("raw") or ""))
        if parsed.get("ok"):
            content = str(parsed.get("content") or "")
            if _trace_enabled():
                _log("openai_chat_ok", trace_id=trace_id, content_len=len(content))
            _append_thread_event(
                key_id,
                thread_id,
                {
                    "role": "user",
                    "text": user_text,
                    "trace_id": trace_id,
                    "model": model,
                    "include_context": include_ctx,
                },
            )
            _append_thread_event(
                key_id,
                thread_id,
                {
                    "role": "assistant",
                    "text": content,
                    "trace_id": trace_id,
                    "model": model,
                },
            )
            return json.dumps(
                {"ok": True, "content": content, "trace_id": trace_id, "thread_id": thread_id, "key_id": key_id},
                ensure_ascii=False,
            )
        if _trace_enabled():
            _log("openai_chat_bad_response", trace_id=trace_id, message=str(parsed.get("message") or ""))
        _append_thread_event(key_id, thread_id, {"role": "user", "text": user_text, "trace_id": trace_id, "model": model})
        _append_thread_event(
            key_id,
            thread_id,
            {"role": "gpt_error", "text": str(parsed.get("message") or ""), "trace_id": trace_id, "error": "bad_response"},
        )
        return json.dumps(
            {
                "ok": False,
                "error": "bad_response",
                "message": str(parsed.get("message") or ""),
                "trace_id": trace_id,
                "thread_id": thread_id,
                "key_id": key_id,
            }
        )


if __name__ == "__main__":
    _install_excepthook()
    _log("app_start", frozen=bool(getattr(sys, "frozen", False)), exe=str(getattr(sys, "executable", "")))
    try:
        _bootstrap_session_keys_from_persisted_auth()
    except Exception:
        pass
    if should_show_startup_splash():
        splash_path = Path(get_resource_base()) / "assets" / "polyphonia_startup.html"
        try:
            splash_url = splash_path.resolve().as_uri()
        except Exception:
            splash_url = "file:///" + str(splash_path).replace("\\", "/")
        _MAIN_WINDOW = webview.create_window(
            "Polyphonia — режим",
            splash_url,
            width=520,
            height=780,
            resizable=False,
            js_api=PolyphoniaApi(ui_mode="offline"),
        )
        webview.start()
    else:
        mode = resolve_mode_without_splash()
        os.environ["POLYPHONIA_MODE"] = mode
        _MAIN_WINDOW = webview.create_window(
            "Polyphonia",
            _main_url(mode),
            width=1400,
            height=900,
            resizable=True,
            js_api=PolyphoniaApi(ui_mode=mode),
        )
        webview.start()
