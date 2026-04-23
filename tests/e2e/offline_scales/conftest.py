"""Fixtures scoped to offline scales E2E package."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page

from tests.e2e.support.scales_app import ScalesApp


@pytest.fixture
def scales_app(page: Page) -> ScalesApp:
    return ScalesApp(page)
