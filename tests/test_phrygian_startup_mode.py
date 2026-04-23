"""Startup mode selection for phrygian_app (no webview)."""

from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    ("env_val", "expected"),
    [
        ("offline", "offline"),
        ("assist", "assist"),
        ("OFFLINE", "offline"),
    ],
)
def test_choose_startup_mode_from_env(
    monkeypatch: pytest.MonkeyPatch, env_val: str, expected: str
) -> None:
    monkeypatch.setenv("POLYPHONIA_MODE", env_val)
    import phrygian_app as pa

    assert pa.choose_startup_mode() == expected


def test_should_show_startup_splash_respects_env(monkeypatch: pytest.MonkeyPatch) -> None:
    import phrygian_app as pa

    monkeypatch.setenv("POLYPHONIA_MODE", "assist")
    assert pa.should_show_startup_splash() is False
    monkeypatch.delenv("POLYPHONIA_MODE", raising=False)
    monkeypatch.setenv("CI", "true")
    assert pa.should_show_startup_splash() is False
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("PETS_HEADLESS", "1")
    assert pa.should_show_startup_splash() is False
    monkeypatch.delenv("PETS_HEADLESS", raising=False)
    assert pa.should_show_startup_splash() is True
