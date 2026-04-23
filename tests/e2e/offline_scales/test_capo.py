"""Capo: display flag and capo marker parent fret row."""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import expect

from tests.e2e.support.scales_app import ScalesApp


@pytest.mark.e2e
def test_capo_moves_capo_marker_and_keeps_scale_highlight(scales_app: ScalesApp) -> None:
    page = scales_app.page
    scales_app.select_guitar_scale("a", "major")
    scales_app.select_capo_fret("2")
    disp = page.locator("#stringed_display")
    expect(disp).to_have_class(re.compile(r"\bhas_capo\b"))
    capo_parent = page.locator("#capo_con").locator("xpath=..")
    expect(capo_parent).to_have_attribute("id", "f_2")
