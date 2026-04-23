"""Smoke: assist panel, polyphonia bridge, layout class, string visibility."""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import expect

from tests.e2e.support.scales_app import ScalesApp


@pytest.mark.e2e
def test_polyphonia_settings_modal(scales_app: ScalesApp) -> None:
    page = scales_app.page
    page.locator("#poly_settings_btn").click()
    backdrop = page.locator("#settings_backdrop")
    expect(backdrop).to_be_visible()
    expect(page.locator("#settings_poly_mode")).to_contain_text("assist")
    expect(page.locator("#settings_gpt_line")).to_be_visible()
    expect(page.locator("#settings_dot_openai")).to_be_visible()
    expect(page.locator("#settings_claude_key")).to_be_visible()
    page.locator("#settings_close").click()
    expect(backdrop).to_be_hidden()


@pytest.mark.e2e
def test_settings_poly_mode_switch(scales_app: ScalesApp) -> None:
    page = scales_app.page
    page.locator("#poly_settings_btn").click()
    page.locator('input[name="settings_poly_mode_pick"][value="offline"]').check()
    page.locator("#settings_poly_mode_apply").click()
    expect(page.locator("html")).to_have_class(re.compile(r"\bpoly_mode_offline\b"))
    expect(page.locator("#settings_poly_mode")).to_contain_text("offline")
    page.locator('input[name="settings_poly_mode_pick"][value="assist"]').check()
    page.locator("#settings_poly_mode_apply").click()
    expect(page.locator("html")).to_have_class(re.compile(r"\bpoly_mode_assist\b"))
    page.locator("#settings_close").click()


@pytest.mark.e2e
def test_assist_openai_status_without_pywebview(scales_app: ScalesApp) -> None:
    page = scales_app.page
    page.locator("#poly_assist_btn").click()
    st = page.locator("#assist_openai_status")
    expect(st).to_contain_text("pywebview")
    page.locator("#assist_close").click()


@pytest.mark.e2e
def test_assist_send_default_draft_no_openai_call(scales_app: ScalesApp) -> None:
    page = scales_app.page
    page.add_init_script(
        """
        window.__openai_calls = 0;
        window.pywebview = { api: {
          openai_chat: () => { window.__openai_calls += 1; return Promise.resolve('{"ok":true,"content":"hi"}'); }
        }};
        """
    )
    page.reload()
    page.locator("#poly_assist_btn").click()
    page.locator("#assist_input").fill("hello")
    page.locator("#assist_send").click()
    # draft is default: no openai_chat call
    assert page.evaluate("() => window.__openai_calls") == 0


@pytest.mark.e2e
def test_assist_send_gpt_calls_openai_chat(scales_app: ScalesApp) -> None:
    page = scales_app.page
    page.add_init_script(
        """
        window.__openai_calls = [];
        window.pywebview = { api: {
          openai_chat: (payload) => { window.__openai_calls.push(payload); return Promise.resolve('{"ok":true,"content":"hi"}'); },
          get_openai_connection: () => Promise.resolve('{"ok":true,"ui_mode":"assist","source":"session","model_default":"gpt-4o-mini"}')
        }};
        """
    )
    page.reload()
    page.locator("#poly_assist_btn").click()
    page.locator("#assist_mode_gpt").click()
    page.locator("#assist_input").fill("hello gpt")
    page.locator("#assist_send").click()
    page.wait_for_timeout(200)
    calls = page.evaluate("() => window.__openai_calls")
    assert len(calls) == 1
    assert '"user_text"' in calls[0]

@pytest.mark.e2e
def test_polyphonia_assist_panel_and_bridge(scales_app: ScalesApp) -> None:
    page = scales_app.page
    scales_app.select_guitar_scale("c", "major")
    page.locator("#poly_assist_btn").click()
    panel = page.locator("#assist_panel")
    expect(panel).to_be_visible()
    assert page.evaluate("() => typeof window.polyphonia") == "object"
    ctx = page.evaluate("() => window.polyphonia.getInstrumentContext()")
    assert ctx.get("note") == "c"
    assert ctx.get("scale") == "major"
    page.locator("#assist_close").click()
    expect(panel).to_be_hidden()


@pytest.mark.e2e
def test_polyphonia_layout_wide_class(scales_app: ScalesApp) -> None:
    page = scales_app.page
    page.locator("#poly_layout_select").select_option("poly_layout_wide")
    expect(page.locator("#poly_grid")).to_have_class(re.compile(r"\bpoly_layout_wide\b"))


@pytest.mark.e2e
def test_polyphonia_fret_boxes_three_frets(scales_app: ScalesApp) -> None:
    page = scales_app.page
    scales_app.select_guitar_scale("d", "major")
    page.locator("#poly_fret_box_select").select_option("fret_box_3")
    disp = page.locator("#stringed_display")
    expect(disp).to_have_class(re.compile(r"\bpoly_fret_boxes\b"))
    expect(page.locator("#f_0")).to_have_class(re.compile(r"\bpoly_fb_start\b"))
    expect(page.locator("#f_3")).to_have_class(re.compile(r"\bpoly_fb_start\b"))


@pytest.mark.e2e
def test_polyphonia_string_visibility_css(scales_app: ScalesApp) -> None:
    page = scales_app.page
    scales_app.select_guitar_scale("e", "major")
    cb = page.locator('input.poly_str_vis[data-s="0"]')
    expect(cb).to_be_visible()
    cb.uncheck()
    expect(page.locator("#stringed_display")).to_have_class(re.compile(r"\bpoly_hide_s0\b"))
