import json
import os
import sys
import subprocess
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import webview

_SESSION_OPENAI_KEY: str | None = None
_SESSION_CLAUDE_KEY: str | None = None

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
    "Rules: (1) Give reviewable suggestions, not final truth; label stylistic guesses as "
    "Assumption, not Confirmed. (2) Do not output or reconstruct specific copyrighted "
    "notation, tabs, or long verbatim excerpts of third-party works; prefer short original "
    "patterns, interval or scale-degree ideas, and high-level arrangement language. "
    "(3) Never contradict on-disk scale data from the host app; if unsure about the "
    "fretboard, say so. (4) Be concise unless the user asks for depth. (5) No medical or "
    "legal advice; do not instruct on licensing or infringement."
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
    d = Path(get_base()) / "polyphonia_sessions" / "dialogs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _assist_dialog_md_heading(role: str) -> str:
    """Человекочитаемая метка в Markdown (отличить ответ GPT от системных сообщений UI)."""
    r = (role or "note").strip().lower()
    if r == "gpt":
        return "GPT (OpenAI)"
    if r == "gpt_error":
        return "GPT (ошибка)"
    if r == "user":
        return "User"
    if r == "system":
        return "System (UI)"
    return (role or "note").strip().replace("\n", " ")[:48] or "note"


def _resolve_openai_key() -> str | None:
    env = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if env:
        return env
    if _SESSION_OPENAI_KEY:
        return _SESSION_OPENAI_KEY.strip()
    return None


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
            return json.dumps({"ok": True, "root": str(Path(get_base()).resolve())}, ensure_ascii=False)
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
            url = _with_query(_main_url("assist"), "poly_view=assist")
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
            repo_path = Path(get_base()).resolve()
            script = repo_path / "scripts" / "claude_terminal.py"
            if not script.is_file():
                return json.dumps(
                    {
                        "ok": False,
                        "error": "missing_launcher",
                        "message": "Не найден scripts/claude_terminal.py рядом с приложением. Запускайте из корня репозитория PETS.",
                        "base": str(repo_path),
                    },
                    ensure_ascii=False,
                )
            # Preflight: if Claude CLI not on PATH, keep console open with a clear message.
            import shutil

            has_claude = bool(shutil.which("claude"))
            creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0x00000010)
            if has_claude:
                # Use current Python interpreter so it works even if "python" isn't on PATH.
                cmd = ["cmd.exe", "/k", sys.executable, str(script)]
            else:
                msg = "echo Claude CLI не найден в PATH. Установите Claude Code и выполните: claude login"
                cmd = ["cmd.exe", "/k", msg]
            subprocess.Popen(cmd, cwd=str(repo_path), creationflags=creationflags)
            return json.dumps({"ok": True, "has_claude": has_claude}, ensure_ascii=False)
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
        return "ok" if _SESSION_CLAUDE_KEY else "cleared"

    @_api_log_wrap
    def get_claude_connection(self, _payload_json: str = "") -> str:
        """Сводка источника ключа Claude (env > session), без раскрытия секрета."""
        if self._ui_mode == "offline":
            return json.dumps(
                {
                    "ok": True,
                    "ui_mode": "offline",
                    "source": "none",
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
        return json.dumps({"ok": True, "ui_mode": "assist", "source": source}, ensure_ascii=False)

    @_api_log_wrap
    def set_openai_api_key(self, key: str) -> str:
        """Store API key in process RAM for this session only (empty string clears)."""
        if self._ui_mode == "offline":
            return "offline_mode"
        global _SESSION_OPENAI_KEY
        k = (key or "").strip()
        _SESSION_OPENAI_KEY = k or None
        return "ok" if _SESSION_OPENAI_KEY else "cleared"

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
                    "model_default": (os.environ.get("OPENAI_MODEL") or "gpt-4o-mini").strip(),
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
        model = (os.environ.get("OPENAI_MODEL") or "gpt-4o-mini").strip()
        return json.dumps(
            {
                "ok": True,
                "ui_mode": "assist",
                "source": source,
                "model_default": model,
            },
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
        req = urllib.request.Request(
            "https://api.openai.com/v1/models",
            headers={"Authorization": "Bearer " + key},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                status = int(getattr(resp, "status", 200) or 200)
                _ = resp.read(16384)
        except urllib.error.HTTPError as e:
            try:
                detail = e.read().decode("utf-8", errors="replace")[:1200]
            except Exception:
                detail = str(e)
            return json.dumps(
                {
                    "ok": False,
                    "error": "http_error",
                    "status": e.code,
                    "message": detail,
                },
                ensure_ascii=False,
            )
        except urllib.error.URLError as e:
            return json.dumps(
                {"ok": False, "error": "network", "message": str(e.reason or e)},
                ensure_ascii=False,
            )
        except Exception as e:
            return json.dumps(
                {"ok": False, "error": "request_failed", "message": str(e)},
                ensure_ascii=False,
            )
        _log("openai_ping", ok=True, http_status=status)
        return json.dumps({"ok": True, "http_status": status}, ensure_ascii=False)

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
        req = urllib.request.Request(
            "https://api.openai.com/v1/models",
            headers={"Authorization": "Bearer " + key},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                status = int(getattr(resp, "status", 200) or 200)
                _ = resp.read(2048)
            return json.dumps({"ok": True, "http_status": status}, ensure_ascii=False)
        except urllib.error.HTTPError as e:
            try:
                detail = e.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                detail = str(e)
            return json.dumps({"ok": False, "error": "http_error", "status": e.code, "message": detail}, ensure_ascii=False)
        except urllib.error.URLError as e:
            return json.dumps({"ok": False, "error": "network", "message": str(e.reason or e)}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"ok": False, "error": "request_failed", "message": str(e)}, ensure_ascii=False)

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
        if len(text) > 50000:
            text = text[:50000] + "\n\n…(truncated)\n"
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = assist_dialogs_dir() / f"assist-dialog-{day}.md"
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
        if not path.exists():
            path.write_text(
                f"# Polyphonia Assist — dialog log\n\n"
                f"- Date (UTC): **{day}**\n"
                f"- Path is under `polyphonia_sessions/dialogs/` (not committed to git).\n\n"
                f"---\n",
                encoding="utf-8",
            )
        heading = _assist_dialog_md_heading(role)
        block = f"\n### {heading} — {ts}\n\n{text}\n\n---\n"
        with path.open("a", encoding="utf-8") as f:
            f.write(block)
        return json.dumps({"ok": True, "path": str(path.resolve())}, ensure_ascii=False)

    @_api_log_wrap
    def openai_chat(self, payload_json: str) -> str:
        """
        Chat Completions from the page. ``payload_json``:
        ``{"user_text": str, "include_context": bool, "context_json": str|object,
        "model": str optional}``.
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

        model = (payload.get("model") or os.environ.get("OPENAI_MODEL") or "gpt-4o-mini").strip()
        include_ctx = bool(payload.get("include_context"))
        trace_id = str(payload.get("client_trace_id") or "").strip()[:96] or None
        _log(
            "openai_chat_request",
            model=model,
            include_context=include_ctx,
            user_len=len(user_text),
            trace_id=trace_id,
        )
        ctx = payload.get("context_json")
        if include_ctx and ctx is not None:
            if not isinstance(ctx, str):
                ctx = json.dumps(ctx, ensure_ascii=False)
            ctx_block = "Context from Polyphonia UI (may be incomplete):\n" + (ctx or "")[:8000]
        else:
            ctx_block = None

        messages: list[dict[str, str]] = [{"role": "system", "content": _OPENAI_SYSTEM}]
        if ctx_block:
            messages.append({"role": "user", "content": ctx_block})
        messages.append({"role": "user", "content": user_text})

        body = {
            "model": model,
            "messages": messages,
            "temperature": 0.6,
            "max_tokens": 1200,
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + key,
            },
            method="POST",
        )
        try:
            t0 = time.perf_counter()
            with urllib.request.urlopen(req, timeout=90) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                status = int(getattr(resp, "status", 200) or 200)
            if _trace_enabled():
                _log("openai_chat_http", trace_id=trace_id, http_status=status, elapsed_ms=int((time.perf_counter() - t0) * 1000))
        except urllib.error.HTTPError as e:
            try:
                detail = e.read().decode("utf-8", errors="replace")[:2000]
            except Exception:
                detail = str(e)
            if _trace_enabled():
                _log("openai_chat_http_error", trace_id=trace_id, status=e.code)
            return json.dumps(
                {
                    "ok": False,
                    "error": "http_error",
                    "status": e.code,
                    "message": detail,
                    "trace_id": trace_id,
                }
            )
        except urllib.error.URLError as e:
            if _trace_enabled():
                _log("openai_chat_network_error", trace_id=trace_id, message=str(e.reason or e))
            return json.dumps(
                {"ok": False, "error": "network", "message": str(e.reason or e), "trace_id": trace_id}
            )
        except Exception as e:
            if _trace_enabled():
                _log("openai_chat_request_failed", trace_id=trace_id, message=str(e))
            return json.dumps({"ok": False, "error": "request_failed", "message": str(e)})

        try:
            data = json.loads(raw)
            content = (
                (data.get("choices") or [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            if not isinstance(content, str):
                content = str(content)
            if _trace_enabled():
                _log("openai_chat_ok", trace_id=trace_id, content_len=len(content))
            return json.dumps({"ok": True, "content": content, "trace_id": trace_id}, ensure_ascii=False)
        except (json.JSONDecodeError, IndexError, KeyError, TypeError) as e:
            if _trace_enabled():
                _log("openai_chat_bad_response", trace_id=trace_id, message=str(e))
            return json.dumps(
                {
                    "ok": False,
                    "error": "bad_response",
                    "message": str(e),
                    "trace_id": trace_id,
                }
            )


if __name__ == "__main__":
    _install_excepthook()
    _log("app_start", frozen=bool(getattr(sys, "frozen", False)), exe=str(getattr(sys, "executable", "")))
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
