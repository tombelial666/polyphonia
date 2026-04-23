"""Thin page helper for the offline scales / stringed UI."""

from __future__ import annotations

from playwright.sync_api import Page


class ScalesApp:
    def __init__(self, page: Page) -> None:
        self.page = page

    def select_guitar_scale(self, note_value: str, scale_value: str) -> None:
        self.page.locator("#note").select_option(note_value)
        self.page.locator("#scale").select_option(scale_value)

    def select_capo_fret(self, fret: str) -> None:
        self.page.locator("#capo_fret").select_option(fret)

    def select_tuning(self, value: str) -> None:
        self.page.locator("#tuning").select_option(value)

    def set_lefty(self, enabled: bool) -> None:
        loc = self.page.locator("#lefty")
        if enabled:
            loc.check()
        else:
            loc.uncheck()

    def select_accidental(self, mode: str) -> None:
        self.page.locator("#accidental").select_option(mode)
