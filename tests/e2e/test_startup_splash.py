from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from playwright.sync_api import Page


@pytest.mark.e2e
def test_splash_default_online_next_calls_launch_main(pets_root: Path, browser, playwright_session) -> None:
    # Ensure assets exist (icon, splash)
    subprocess.run(["python", "build_index.py"], cwd=pets_root, check=True)
    splash = pets_root.joinpath("assets", "polyphonia_startup.html").resolve().as_uri()

    context = browser.new_context()
    page: Page = context.new_page()
    page.goto(splash)

    page.add_init_script(
        """
        window.__calls = [];
        window.pywebview = { api: {
          launch_main: (payload) => { window.__calls.push(payload); return Promise.resolve('{"ok": true}'); }
        }};
        """
    )
    # Reload so init script takes effect before page scripts.
    page.reload()

    page.locator("#btn_go").click()
    page.wait_for_timeout(200)

    calls = page.evaluate("window.__calls")
    assert len(calls) == 1
    assert '"mode":"assist"' in calls[0].replace(" ", "")
    context.close()


@pytest.mark.e2e
def test_splash_online_submits_keys(pets_root: Path, browser) -> None:
    subprocess.run(["python", "build_index.py"], cwd=pets_root, check=True)
    splash = pets_root.joinpath("assets", "polyphonia_startup.html").resolve().as_uri()

    context = browser.new_context()
    page: Page = context.new_page()
    page.goto(splash)

    page.add_init_script(
        """
        window.__calls = [];
        window.pywebview = { api: {
          launch_main: (payload) => { window.__calls.push(payload); return Promise.resolve('{"ok": true}'); }
        }};
        """
    )
    page.reload()

    page.locator("#btn_online").click()
    page.locator("#openai_key").fill("sk-openai-123")
    page.locator("#claude_key").fill("sk-ant-123")
    page.locator("#btn_go").click()
    page.wait_for_timeout(200)

    calls = page.evaluate("window.__calls")
    assert len(calls) == 1
    s = calls[0].replace(" ", "")
    assert '"mode":"assist"' in s
    assert '"openai_key":"sk-openai-123"' in s
    assert '"claude_key":"sk-ant-123"' in s
    context.close()


@pytest.mark.e2e
def test_splash_key_validation_buttons_call_api(pets_root: Path, browser) -> None:
    subprocess.run(["python", "build_index.py"], cwd=pets_root, check=True)
    splash = pets_root.joinpath("assets", "polyphonia_startup.html").resolve().as_uri()

    context = browser.new_context()
    page: Page = context.new_page()
    page.goto(splash)

    page.add_init_script(
        """
        window.__val_openai = [];
        window.__val_claude = [];
        window.pywebview = { api: {
          launch_main: (payload) => Promise.resolve('{"ok": true}'),
          validate_openai_key: (payload) => { window.__val_openai.push(payload); return Promise.resolve('{"ok": true, "http_status": 200}'); },
          validate_claude_key: (payload) => { window.__val_claude.push(payload); return Promise.resolve('{"ok": true, "message": "ok"}'); }
        }};
        """
    )
    page.reload()

    page.locator("#btn_online").click()
    page.locator("#openai_key").fill("sk-openai-123")
    page.locator("#claude_key").fill("sk-ant-123")
    page.locator("#btn_check_openai").click()
    page.locator("#btn_check_claude").click()
    page.wait_for_timeout(200)

    oa = page.evaluate("() => window.__val_openai")
    cl = page.evaluate("() => window.__val_claude")
    assert len(oa) == 1
    assert len(cl) == 1
    assert "sk-openai-123" in oa[0]
    assert "sk-ant-123" in cl[0]
    context.close()


@pytest.mark.e2e
def test_splash_offline_click_launches_immediately(pets_root: Path, browser) -> None:
    subprocess.run(["python", "build_index.py"], cwd=pets_root, check=True)
    splash = pets_root.joinpath("assets", "polyphonia_startup.html").resolve().as_uri()

    context = browser.new_context()
    page: Page = context.new_page()
    page.goto(splash)

    page.add_init_script(
        """
        window.__calls = [];
        window.pywebview = { api: {
          launch_main: (payload) => { window.__calls.push(payload); return Promise.resolve('{"ok": true}'); }
        }};
        """
    )
    page.reload()

    page.locator("#btn_online").click()
    page.locator("#btn_offline").click()
    page.wait_for_timeout(200)

    calls = page.evaluate("window.__calls")
    assert len(calls) == 1
    assert '"mode":"offline"' in calls[0].replace(" ", "")
    context.close()

