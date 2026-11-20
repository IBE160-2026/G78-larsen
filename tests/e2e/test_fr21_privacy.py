"""FR-21 on every Guest page: every request goes to the stack's own origin (no third party, fonts included), and each
page loads exactly one stylesheet of ours and no <style> element. No cookie is set, except on Book seats, which sets
exactly one: the session cookie (AD-8). Details, Review and Confirmation (Story 1.5) keep that one cookie, and a name
with a script tag is shown as text on Review and Confirmation, never run (FR-18 IV-5)."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page

from .test_fr05_book_and_pay import book_in_browser, free_windows, open_session, review_draft, set_draft

SCRIPT_NAME = "<script>window.__pwned = 1</script><b>Bold</b>"

PAGES = ["/", "/#before-you-come", "/terms", "/privacy", "/nope"]
BOOK_SEATS = "/book-seats"


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


def test_book_seats_sets_exactly_one_session_cookie_and_every_request_goes_to_the_stack_origin(page: Page, base_url):
    requests = []
    page.on("request", lambda r: requests.append(r.url))
    page.goto(base_url + BOOK_SEATS)
    page.wait_for_selector(".cal-grid")
    page.wait_for_load_state("networkidle")
    others = [u for u in requests if not (u == base_url or u.startswith(base_url + "/"))]
    assert not others, f"requests to another origin: {others}"
    assert sum(1 for u in requests if u == base_url + "/api/session") == 1
    cookies = page.context.cookies()
    assert [c["name"] for c in cookies] == ["bp_session"], cookies
    assert cookies[0]["httpOnly"] and cookies[0]["sameSite"] == "Strict" and cookies[0]["path"] == "/"
    page.reload()
    page.wait_for_selector(".cal-grid")
    page.wait_for_load_state("networkidle")
    assert [c["name"] for c in page.context.cookies()] == ["bp_session"]  # the existing session is kept


@pytest.mark.parametrize("path", PAGES + [BOOK_SEATS])
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


def _paid_pages(page: Page, base_url: str, name: str = "Ingrid Hansen") -> dict[str, str]:
    """Open a session, pay for one Seat as `name`, and return the addresses of Details, Review and Confirmation, with a
    draft in the tab that opens Details and Review (for a second Booking)."""
    window = free_windows(base_url)[-1]
    open_session(page, base_url)
    reference = book_in_browser(page, window, 1, name)["booking"]["reference"]
    set_draft(page, review_draft(window, 1, name))
    return {"details": "/book-seats/details", "review": "/book-seats/review", "confirmation": f"/confirmation/{reference}"}


@pytest.mark.parametrize("which", ["details", "review", "confirmation"])
def test_the_booking_pages_stay_on_the_origin_with_one_cookie_and_one_stylesheet(page: Page, base_url, which):
    path = _paid_pages(page, base_url)[which]
    requests = []
    page.on("request", lambda r: requests.append(r.url))
    page.goto(base_url + path)
    page.wait_for_selector("#name" if which == "details" else ".summary")
    page.wait_for_load_state("networkidle")
    others = [u for u in requests if not (u == base_url or u.startswith(base_url + "/"))]
    assert not others, f"requests to another origin: {others}"
    assert [c["name"] for c in page.context.cookies()] == ["bp_session"]
    sheets = page.evaluate("() => Array.from(document.styleSheets).map(s => s.href)")
    assert len(sheets) == 1 and sheets[0].startswith(base_url + "/"), sheets
    assert page.locator("style").count() == 0
    assert page.locator(".shell [style], .shell[style]").count() == 0


def test_a_name_with_a_script_tag_is_text_on_review_and_confirmation(page: Page, base_url):
    pages = _paid_pages(page, base_url, SCRIPT_NAME)
    page.goto(base_url + pages["review"])
    row = page.locator(".summary-row", has=page.locator("dt", has_text="Name"))
    row.wait_for()
    assert row.locator("dd").inner_text() == SCRIPT_NAME
    assert page.locator(".summary b, .summary script").count() == 0
    page.goto(base_url + pages["confirmation"])
    page.wait_for_selector(".email-body")
    # Confirmation's summary has no name row; the name reaches it only as the API's JSON, never as markup
    assert page.locator("main script, main b").count() == 0
    assert page.evaluate("() => window.__pwned") is None
