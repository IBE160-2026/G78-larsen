"""The compose stack behind Caddy (AD-10, AD-17, AD-27): `/api` routing, the JSON 404 for unknown API paths with
no redirect, the not-available page, the <noscript> line, `/privacy` with the backend stopped, and the headers
that only Caddy sets."""

from __future__ import annotations

import httpx
import pytest
from playwright.sync_api import Browser, Page

from . import trust

NOT_FOUND = {"detail": {"error": "not_found"}}
NOSCRIPT = "This booking page needs JavaScript."


def get(base_url: str, path: str) -> httpx.Response:
    return httpx.get(base_url + path, follow_redirects=False, timeout=10, verify=trust.context())


def test_api_health_answers_through_caddy(base_url):
    r = get(base_url, "/api/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}
    assert r.headers["cache-control"] == "no-store"
    assert r.headers["referrer-policy"] == "no-referrer"


@pytest.mark.parametrize("path", ["/api", "/api/x", "/api/x/"])
def test_unknown_api_path_is_the_json_404_never_a_page_or_redirect(base_url, path):
    r = get(base_url, path)
    assert r.status_code == 404
    assert "location" not in r.headers
    assert r.headers["content-type"].startswith("application/json")
    assert r.json() == NOT_FOUND
    assert r.headers["cache-control"] == "no-store"
    assert r.headers["referrer-policy"] == "no-referrer"


def test_unknown_page_shows_not_available_with_a_link_to_landing(page: Page, base_url):
    response = page.goto(base_url + "/nope")
    assert response.status == 404
    h1 = page.locator("h1")
    assert h1.inner_text() == "This page is not available."
    assert page.title() == "This page is not available – Saunalöyly"
    links = page.locator("main a[href='/']")
    assert links.count() == 1
    assert "404: This page could not be found" not in page.content()  # never Next.js's default page


def test_noscript_line_is_in_every_page(browser: Browser, base_url):
    for path in ("/", "/terms", "/privacy", "/nope"):
        assert NOSCRIPT in get(base_url, path).text
    context = browser.new_context(java_script_enabled=False, ignore_https_errors=True)
    try:
        page = context.new_page()
        page.goto(base_url + "/privacy")
        line = page.locator("body > noscript > p.noscript")
        assert line.inner_text() == NOSCRIPT
        assert line.is_visible()
    finally:
        context.close()


def test_noscript_line_is_hidden_with_javascript(page: Page, base_url):
    page.goto(base_url + "/privacy")
    assert not page.locator("p.noscript").is_visible()


def test_privacy_renders_while_the_backend_is_stopped(stack, base_url):
    stack.compose("stop", "backend")
    try:
        r = get(base_url, "/privacy")
        assert r.status_code == 200
        assert "Privacy notice" in r.text and "Datatilsynet" in r.text
        assert get(base_url, "/api/health").status_code == 502  # the API really is down
    finally:
        stack.compose("start", "backend")
        stack.wait()
    assert get(base_url, "/api/health").status_code == 200


def test_every_site_response_carries_caddys_headers(page: Page, base_url):
    responses = []
    page.on("response", lambda r: responses.append(r))
    for path in ("/", "/terms", "/privacy", "/nope"):
        page.goto(base_url + path)
        page.wait_for_load_state("networkidle")
    for path in ("/api/health", "/api/x"):
        responses.append(page.request.get(base_url + path))
    assert len(responses) > 8  # pages, the stylesheet, scripts, fonts and the API
    for r in responses:
        assert r.url.startswith(base_url)
        # a browser Response's `headers` leaves some out; `all_headers()` has every one
        headers = r.all_headers() if hasattr(r, "all_headers") else r.headers
        assert headers.get("referrer-policy") == "no-referrer", r.url
        path = r.url[len(base_url):]
        if path == "/api" or path.startswith("/api/"):
            assert headers.get("cache-control") == "no-store", r.url
        else:  # Caddy drops the frontend's own Cache-Control (AD-27)
            assert "cache-control" not in headers, r.url


def test_manage_paths_carry_noindex_and_other_pages_do_not(base_url):
    for path in ("/manage", "/api/manage/x"):
        assert get(base_url, path).headers.get("x-robots-tag") == "noindex", path
    assert "x-robots-tag" not in get(base_url, "/terms").headers
