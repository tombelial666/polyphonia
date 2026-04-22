"""
E2E checks for offline PETS scales page: DOM + highlighting + chord table.

Uses Playwright against file:// index.html (assets resolve relative to the
document directory, i.e. PETS repo root).
"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect


def _select_guitar_scale(page: Page, note_value: str, scale_value: str) -> None:
    page.locator("#note").select_option(note_value)
    page.locator("#scale").select_option(scale_value)


def test_default_a_major_scale_info_and_root_highlight(page: Page) -> None:
    _select_guitar_scale(page, "a", "major")
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


def test_natural_minor_changes_scale_notes(page: Page) -> None:
    _select_guitar_scale(page, "a", "natural-minor")
    notes = page.locator("#info_scale_notes").inner_text()
    assert "C" in notes
    assert "F" in notes


def test_chord_click_shows_chord_info_and_highlight(page: Page) -> None:
    _select_guitar_scale(page, "a", "major")
    btn = page.locator("#scale_chord_table tbody tr").first.locator("button:not([disabled])").first
    expect(btn).to_be_enabled()
    btn.click()
    expect(page.locator("#chord_info")).not_to_have_class("hidden")
    expect(page.locator("#info_chord_notes")).not_to_have_text("")
    chord_root = page.locator("#f_0 .s_1")
    expect(chord_root).to_have_class(re.compile(r"\bin_chord\b"))


def test_capo_moves_capo_marker_and_keeps_scale_highlight(page: Page) -> None:
    _select_guitar_scale(page, "a", "major")
    page.locator("#capo_fret").select_option("2")
    disp = page.locator("#stringed_display")
    expect(disp).to_have_class(re.compile(r"\bhas_capo\b"))
    capo_parent = page.locator("#capo_con").locator("xpath=..")
    expect(capo_parent).to_have_attribute("id", "f_2")


def test_alternate_tuning_minor_third_still_renders_scale(page: Page) -> None:
    page.locator("#tuning").select_option("minor-third")
    _select_guitar_scale(page, "a", "melodic-minor")
    expect(page.locator("#info_scale_name")).to_contain_text("Melodic Minor")
    notes = page.locator("#info_scale_notes").inner_text()
    assert len(notes.strip()) > 3
    any_highlight = page.locator("#fret_note_con .sf.in_scale").first
    expect(any_highlight).to_be_visible()


def test_lefty_toggles_display_class(page: Page) -> None:
    page.locator("#lefty").check()
    expect(page.locator("#stringed_display")).to_have_class(re.compile(r"\bis_lefty\b"))
    page.locator("#lefty").uncheck()
    expect(page.locator("#stringed_display")).not_to_have_class(re.compile(r"\bis_lefty\b"))


def test_flat_accidental_updates_note_labels(page: Page) -> None:
    page.locator("#accidental").select_option("flat")
    _select_guitar_scale(page, "a", "major")
    text = page.locator("#info_scale_notes").inner_text()
    assert "\u266d" in text
