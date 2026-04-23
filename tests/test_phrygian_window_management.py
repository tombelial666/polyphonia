"""Window management helpers and JS API in phrygian_app (pywebview)."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import phrygian_app


def _reset_globals() -> None:
    phrygian_app._MAIN_WINDOW = None
    phrygian_app._ASSIST_WINDOW = None


def test_open_assist_window_offline_rejected() -> None:
    _reset_globals()
    api = phrygian_app.PolyphoniaApi(ui_mode="offline")
    out = json.loads(api.open_assist_window())
    assert out["ok"] is False
    assert out["error"] == "offline_mode"


def test_open_assist_window_creates_and_reuses(monkeypatch) -> None:
    _reset_globals()
    created = SimpleNamespace()
    created.bring_to_front = MagicMock()

    create_window = MagicMock(return_value=created)
    monkeypatch.setattr(phrygian_app.webview, "create_window", create_window)

    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    out1 = json.loads(api.open_assist_window())
    assert out1["ok"] is True
    assert out1.get("created") is True
    assert phrygian_app._ASSIST_WINDOW is created
    create_window.assert_called_once()
    called_url = create_window.call_args.args[1]
    assert "#poly_mode=assist&poly_view=assist" in called_url
    assert "?poly_view=assist" not in called_url

    out2 = json.loads(api.open_assist_window())
    assert out2["ok"] is True
    assert out2.get("reused") is True
    create_window.assert_called_once()
    created.bring_to_front.assert_called()


def test_launch_claude_terminal_window_uses_resolved_launcher(monkeypatch, tmp_path) -> None:
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    scripts.mkdir(parents=True)
    launcher = scripts / "claude_terminal.py"
    launcher.write_text("print('ok')", encoding="utf-8")

    monkeypatch.setattr(phrygian_app, "_is_windows", lambda: True)
    monkeypatch.setattr(phrygian_app, "_resolve_claude_launcher", lambda: (repo, launcher))
    monkeypatch.setattr(phrygian_app, "_resolve_claude_cli_executable", lambda: "C:/bin/claude.cmd")
    monkeypatch.setattr(phrygian_app, "_resolve_python_launcher_command", lambda: ["C:/Python312/python.exe"])

    popen = MagicMock()
    monkeypatch.setattr(phrygian_app.subprocess, "Popen", popen)

    out = json.loads(api.launch_claude_terminal_window())
    assert out["ok"] is True
    assert out["has_claude"] is True
    assert out["claude_exe"] == "C:/bin/claude.cmd"
    assert out["launcher_mode"] == "python_wrapper"
    assert out["key_source"] == "missing"
    popen.assert_called_once()
    args = popen.call_args.args[0]
    kwargs = popen.call_args.kwargs
    assert args[:2] == ["cmd.exe", "/k"]
    assert "C:/Python312/python.exe" in args[2]
    assert str(launcher) in args[2]
    assert "TERM=xterm-256color" not in args[2]
    assert kwargs["cwd"] == str(repo)
    assert "env" in kwargs
    assert "C:\\bin" in kwargs["env"]["PATH"] or "C:/bin" in kwargs["env"]["PATH"]
    assert kwargs["env"]["CLAUDE_CODE_DISABLE_TERMINAL_TITLE"] == "1"
    assert "TERM" not in kwargs["env"]


def test_launch_claude_terminal_window_missing_launcher(monkeypatch) -> None:
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    monkeypatch.setattr(phrygian_app, "_is_windows", lambda: True)
    monkeypatch.setattr(phrygian_app, "_resolve_claude_launcher", lambda: (None, None))
    out = json.loads(api.launch_claude_terminal_window())
    assert out["ok"] is False
    assert out["error"] == "missing_launcher"


def test_launch_claude_terminal_window_no_cli_shows_hint(monkeypatch, tmp_path) -> None:
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    scripts.mkdir(parents=True)
    launcher = scripts / "claude_terminal.py"
    launcher.write_text("print('ok')", encoding="utf-8")

    monkeypatch.setattr(phrygian_app, "_is_windows", lambda: True)
    monkeypatch.setattr(phrygian_app, "_resolve_claude_launcher", lambda: (repo, launcher))
    monkeypatch.setattr(phrygian_app, "_resolve_claude_cli_executable", lambda: None)
    monkeypatch.setattr(phrygian_app, "_resolve_python_launcher_command", lambda: ["C:/Python312/python.exe"])

    popen = MagicMock()
    monkeypatch.setattr(phrygian_app.subprocess, "Popen", popen)
    out = json.loads(api.launch_claude_terminal_window())
    assert out["ok"] is True
    assert out["has_claude"] is False
    assert out["claude_exe"] == ""
    assert out["launcher_mode"] == "python_wrapper"
    popen.assert_called_once()
    args = popen.call_args.args[0]
    kwargs = popen.call_args.kwargs
    assert args[:2] == ["cmd.exe", "/k"]
    assert "C:/Python312/python.exe" in args[2]
    assert str(launcher) in args[2]
    assert kwargs["cwd"] == str(repo)
    assert kwargs["env"]["CLAUDE_CODE_DISABLE_TERMINAL_TITLE"] == "1"


def test_launch_claude_terminal_window_falls_back_to_direct_cli_when_python_runtime_missing(monkeypatch, tmp_path) -> None:
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    scripts.mkdir(parents=True)
    launcher = scripts / "claude_terminal.py"
    launcher.write_text("print('ok')", encoding="utf-8")

    monkeypatch.setattr(phrygian_app, "_is_windows", lambda: True)
    monkeypatch.setattr(phrygian_app, "_resolve_claude_launcher", lambda: (repo, launcher))
    monkeypatch.setattr(phrygian_app, "_resolve_claude_cli_executable", lambda: "C:/bin/claude.cmd")
    monkeypatch.setattr(phrygian_app, "_resolve_python_launcher_command", lambda: None)

    popen = MagicMock()
    monkeypatch.setattr(phrygian_app.subprocess, "Popen", popen)

    out = json.loads(api.launch_claude_terminal_window())
    assert out["ok"] is True
    assert out["has_claude"] is True
    assert out["launcher_mode"] == "direct_cli"
    assert out["key_source"] == "missing"
    args = popen.call_args.args[0]
    kwargs = popen.call_args.kwargs
    assert "claude.cmd" in args[2].lower()
    assert str(launcher) not in args[2]
    assert "TERM=xterm-256color" not in args[2]
    assert kwargs["env"]["CLAUDE_CODE_DISABLE_TERMINAL_TITLE"] == "1"


def test_launch_claude_terminal_window_passes_session_key_into_env(monkeypatch, tmp_path) -> None:
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    scripts.mkdir(parents=True)
    launcher = scripts / "claude_terminal.py"
    launcher.write_text("print('ok')", encoding="utf-8")

    monkeypatch.setattr(phrygian_app, "_is_windows", lambda: True)
    monkeypatch.setattr(phrygian_app, "_resolve_claude_launcher", lambda: (repo, launcher))
    monkeypatch.setattr(phrygian_app, "_resolve_claude_cli_executable", lambda: "C:/bin/claude.cmd")
    monkeypatch.setattr(phrygian_app, "_resolve_python_launcher_command", lambda: ["C:/Python312/python.exe"])

    phrygian_app._SESSION_CLAUDE_KEY = "sk-ant-test"
    phrygian_app._SESSION_CLAUDE_KEY_ORIGIN = "ui"

    popen = MagicMock()
    monkeypatch.setattr(phrygian_app.subprocess, "Popen", popen)

    out = json.loads(api.launch_claude_terminal_window())
    kwargs = popen.call_args.kwargs
    assert out["ok"] is True
    assert out["key_source"] == "available"
    assert kwargs["env"]["POLYPHONIA_CLAUDE_API_KEY"] == "sk-ant-test"
    assert kwargs["env"]["ANTHROPIC_API_KEY"] == "sk-ant-test"
    phrygian_app._SESSION_CLAUDE_KEY = None
    phrygian_app._SESSION_CLAUDE_KEY_ORIGIN = None


def test_resolve_python_launcher_command_skips_frozen_polyphonia(monkeypatch) -> None:
    monkeypatch.setattr(phrygian_app.sys, "executable", r"D:\Reps\PETS\dist\polyphonia.exe")

    def fake_which(name: str) -> str | None:
        if name == "python":
            return r"C:\Python312\python.exe"
        return None

    monkeypatch.setattr(phrygian_app.shutil, "which", fake_which)

    cmd = phrygian_app._resolve_python_launcher_command()
    assert cmd == [r"C:\Python312\python.exe"]


def test_resolve_python_launcher_command_uses_py_launcher_with_python3_flag(monkeypatch) -> None:
    monkeypatch.setattr(phrygian_app.sys, "executable", r"D:\Reps\PETS\dist\polyphonia.exe")

    def fake_which(name: str) -> str | None:
        if name == "py":
            return r"C:\Windows\py.exe"
        return None

    monkeypatch.setattr(phrygian_app.shutil, "which", fake_which)

    cmd = phrygian_app._resolve_python_launcher_command()
    assert cmd == [r"C:\Windows\py.exe", "-3"]


def test_tile_windows_not_supported_non_windows(monkeypatch) -> None:
    _reset_globals()
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")
    monkeypatch.setattr(phrygian_app, "_is_windows", lambda: False)
    out = json.loads(api.tile_windows())
    assert out["ok"] is False
    assert out["error"] == "not_supported"


def test_tile_windows_moves_and_resizes(monkeypatch) -> None:
    _reset_globals()
    api = phrygian_app.PolyphoniaApi(ui_mode="assist")

    main = SimpleNamespace(move=MagicMock(), resize=MagicMock(), bring_to_front=MagicMock())
    assist = SimpleNamespace(move=MagicMock(), resize=MagicMock(), bring_to_front=MagicMock())
    phrygian_app._MAIN_WINDOW = main
    phrygian_app._ASSIST_WINDOW = assist

    monkeypatch.setattr(phrygian_app, "_is_windows", lambda: True)
    monkeypatch.setattr(phrygian_app, "_get_screen_size", lambda: (1920, 1080))

    out = json.loads(api.tile_windows(json.dumps({"mode": "vertical"})))
    assert out["ok"] is True
    main.move.assert_called()
    main.resize.assert_called()
    assist.move.assert_called()
    assist.resize.assert_called()

