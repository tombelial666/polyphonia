from __future__ import annotations

from pathlib import Path

import build_index


def test_build_index_html_smoke_contains_key_markers(tmp_path: Path) -> None:
    # Minimal inputs expected by build_index.build_index_html
    (tmp_path / "assets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "assets" / "_piano_html.txt").write_text("<div>Piano</div>", encoding="utf-8")
    (tmp_path / "guitar_template.html").write_text(
        """
        <html>
          <body>
            <select id="note"><option value="c">C</option></select>
            <select id="scale"><option value="major">Major</option></select>
          </body>
        </html>
        """.strip(),
        encoding="utf-8",
    )

    html = build_index.build_index_html(tmp_path)
    assert "<title>Polyphonia — scales & chords</title>" in html
    assert 'id="poly_settings_btn"' in html
    assert 'src="assets/polyphonia_ui.js"' in html
    assert 'id="assist_focus"' in html
    assert 'id="assist_status"' in html
    assert 'id="settings_claude_remember"' in html


def test_write_polyphonia_launchers_writes_expected_content(tmp_path: Path) -> None:
    build_index.write_polyphonia_launchers(tmp_path)
    bat = (tmp_path / "run_polyphonia.bat").read_text(encoding="utf-8")
    ps1 = (tmp_path / "run_polyphonia.ps1").read_text(encoding="utf-8")
    assert "python phrygian_app.py" in bat
    assert 'cd /d "%~dp0"' in bat
    assert "Set-Location -LiteralPath $PSScriptRoot" in ps1
    assert "python phrygian_app.py" in ps1


def test_try_write_polyphonia_ico_skips_when_png_missing(tmp_path: Path, capsys) -> None:
    (tmp_path / "assets").mkdir(parents=True, exist_ok=True)
    build_index.try_write_polyphonia_ico(tmp_path)
    out = capsys.readouterr().out
    assert "skip .ico" in out


def test_try_create_windows_desktop_shortcut_non_windows_is_noop(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(build_index.sys, "platform", "linux")
    # Should not raise even if launchers not present.
    build_index.try_create_windows_desktop_shortcut(tmp_path)

