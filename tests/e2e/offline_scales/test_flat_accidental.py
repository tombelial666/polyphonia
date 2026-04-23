"""Flat accidental mode: scale notes show flat symbols where applicable."""

from __future__ import annotations

import pytest

from tests.e2e.support.scales_app import ScalesApp


@pytest.mark.e2e
def test_flat_accidental_updates_note_labels(scales_app: ScalesApp) -> None:
    scales_app.select_accidental("flat")
    scales_app.select_guitar_scale("a", "major")
    text = scales_app.page.locator("#info_scale_notes").inner_text()
    assert "\u266d" in text
