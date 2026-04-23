"""A major: scale info text, accidentals, root and string highlights."""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import expect

from tests.e2e.support.scales_app import ScalesApp


@pytest.mark.e2e
def test_a_major_scale_info_and_root_highlight(scales_app: ScalesApp) -> None:
    page = scales_app.page
    scales_app.select_guitar_scale("a", "major")
    name = page.locator("#info_scale_name")
    notes = page.locator("#info_scale_notes")
    expect(name).to_contain_text("A")
    expect(name).to_contain_text("Major")
    text = notes.inner_text()
    assert "A" in text
    assert "B" in text
    assert "D" in text
    assert "E" in text
    assert "\u266f" in text

    root = page.locator("#f_0 .s_1")
    expect(root).to_have_class(re.compile(r"\bin_scale\b"))
    expect(root).to_have_class(re.compile(r"\bscale_root\b"))

    low_e = page.locator("#f_0 .s_5")
    expect(low_e).to_have_class(re.compile(r"\bin_scale\b"))
