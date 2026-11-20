"""FR-21 on every page this story builds: every request goes to the stack's own origin (no third party, fonts
included), no cookie is set, and each page loads exactly one stylesheet of ours and no <style> element."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page

PAGES = ["/", "/terms", "/privacy", "/nope"]


@pytest.mark.parametrize("path", PAGES)
def test_every_request_goes_to_the_stack_origin_and_no_cookie_is_set(page: Page, base_url, path):
    requests = []
    responses = []
    page.on("request", lambda r: requests.append(r.url))
    page.on("response", lambda r: responses.append(r))
    page.goto(base_url + path)
    page.wait_for_load_state("networkidle")
    page.evaluate("document.fonts.ready")
    # `Response.headers` omits cookie headers; `header_value` reads the raw ones
    set_cookies = [r.url for r in responses if r.header_value("set-cookie")]

    assert requests, "no request was recorded"
    others = [u for u in requests if not (u == base_url or u.startswith(base_url + "/"))]
    assert not others, f"requests to another origin: {others}"
    assert any(u.endswith(".woff2") for u in requests), "the self-hosted fonts were not loaded"
    assert not set_cookies, f"Set-Cookie on {set_cookies}"
    assert page.context.cookies() == []


@pytest.mark.parametrize("path", PAGES)
def test_exactly_one_stylesheet_and_no_style_element(page: Page, base_url, path):
    page.goto(base_url + path)
    page.wait_for_load_state("networkidle")
    sheets = page.evaluate("""() => Array.from(document.styleSheets).map(s => ({
        href: s.href, owner: s.ownerNode ? s.ownerNode.tagName.toLowerCase() : null}))""")
    assert len(sheets) == 1, sheets
    assert sheets[0]["owner"] == "link" and sheets[0]["href"].startswith(base_url + "/"), sheets
    assert page.locator("style").count() == 0
    # no style props in our markup (Next.js's own route announcer carries one, outside the shell)
    assert page.locator(".shell [style], .shell[style]").count() == 0
