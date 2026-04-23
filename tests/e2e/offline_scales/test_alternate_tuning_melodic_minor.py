"""Alternate tuning + melodic minor: info and at least one in-scale highlight."""

from __future__ import annotations

import pytest
from playwright.sync_api import expect

from tests.e2e.support.scales_app import ScalesApp


@pytest.mark.e2e
def test_alternate_tuning_minor_third_still_renders_scale(scales_app: ScalesApp) -> None:
    scales_app.select_tuning("minor-third")
    scales_app.select_guitar_scale("a", "melodic-minor")
    page = scales_app.page
    expect(page.locator("#info_scale_name")).to_contain_text("Melodic Minor")
    notes = page.locator("#info_scale_notes").inner_text()
    assert len(notes.strip()) > 3
    any_highlight = page.locator("#fret_note_con .sf.in_scale").first
    expect(any_highlight).to_be_visible()
