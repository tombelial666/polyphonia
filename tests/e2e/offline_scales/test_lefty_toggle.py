"""Left-handed layout toggle updates stringed display class."""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import expect

from tests.e2e.support.scales_app import ScalesApp


@pytest.mark.e2e
def test_lefty_toggles_display_class(scales_app: ScalesApp) -> None:
    page = scales_app.page
    scales_app.set_lefty(True)
    expect(page.locator("#stringed_display")).to_have_class(re.compile(r"\bis_lefty\b"))
    scales_app.set_lefty(False)
    expect(page.locator("#stringed_display")).not_to_have_class(re.compile(r"\bis_lefty\b"))
