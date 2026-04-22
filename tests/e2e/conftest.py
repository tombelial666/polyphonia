"""Pytest fixtures for PETS browser-level (E2E) tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Playwright, sync_playwright

# tests/e2e/conftest.py -> parents[2] == repo root
PETS_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def pets_root() -> Path:
    return PETS_ROOT


@pytest.fixture(scope="session")
def index_html_uri(pets_root: Path) -> str:
    subprocess.run(
        ["python", "build_index.py"],
        cwd=pets_root,
        check=True,
    )
    return pets_root.joinpath("index.html").resolve().as_uri()


@pytest.fixture(scope="session")
def playwright_session() -> Playwright:
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_session: Playwright) -> Browser:
    b = playwright_session.chromium.launch(headless=True)
    yield b
    b.close()


@pytest.fixture
def page(browser: Browser, index_html_uri: str):
    context = browser.new_context()
    pg = context.new_page()
    pg.goto(index_html_uri)
    yield pg
    context.close()
