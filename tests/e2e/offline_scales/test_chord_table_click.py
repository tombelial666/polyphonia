"""Chord table: enabled chord button reveals info and fretboard chord class."""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import expect

from tests.e2e.support.scales_app import ScalesApp


@pytest.mark.e2e
def test_chord_click_shows_chord_info_and_highlight(scales_app: ScalesApp) -> None:
    page = scales_app.page
    scales_app.select_guitar_scale("a", "major")
    btn = (
        page.locator("#scale_chord_table tbody tr")
        .first.locator("button:not([disabled])")
        .first
    )
    expect(btn).to_be_enabled()
    btn.click()
    expect(page.locator("#chord_info")).not_to_have_class("hidden")
    expect(page.locator("#info_chord_notes")).not_to_have_text("")
    chord_root = page.locator("#f_0 .s_1")
    expect(chord_root).to_have_class(re.compile(r"\bin_chord\b"))
