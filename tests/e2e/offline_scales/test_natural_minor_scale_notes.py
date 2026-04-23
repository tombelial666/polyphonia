"""Natural minor: scale degree set differs from parallel major."""

from __future__ import annotations

import pytest

from tests.e2e.support.scales_app import ScalesApp


@pytest.mark.e2e
def test_natural_minor_changes_scale_notes(scales_app: ScalesApp) -> None:
    scales_app.select_guitar_scale("a", "natural-minor")
    notes = scales_app.page.locator("#info_scale_notes").inner_text()
    assert "C" in notes
    assert "F" in notes
