"""FR-25 / AD-28 / CAP-10 (Story 4.1) in the compose stack, over HTTPS: a sample Manage link from the Outbox opens its
Booking, the token is gone from the address bar and the h1 has focus; a guessed reference and a bad link show "This
page is not available."; Caddy adds `X-Robots-Tag: noindex` and `Referrer-Policy: no-referrer` to the Manage pages and
the Manage API; axe finds no A or AA failure, the keyboard alone works and nothing scrolls sideways at 1024, 1366 and
1920 px.

The sample link is read from the Outbox as the examiner reads it (the stack's own `outbox_emails`), so it is the link
the seed issued at startup.
"""

from __future__ import annotations

import re

import httpx
import psycopg
from playwright.sync_api import Page

from . import a11y, trust
from .admin import db_url

REFERENCE = r"[0-9A-HJKMNP-TV-Z]{8}"
LINK = re.compile(r"(?m)^(https://\S+/manage#t=([A-Za-z0-9_-]{43}))$")
NOT_AVAILABLE = "This page is not available."
SAMPLE = "ingrid.berg@example.com"  # the sample Booking of tomorrow at 14:30 (seeds/bookings.json)


def sample_link(stack) -> tuple[str, str, str]:
    """(link, token, reference) of a sample Booking's Manage link, from its confirmation email in the Outbox."""
    with psycopg.connect(db_url(stack)) as c:
        body, reference = c.execute(
            "SELECT o.body, b.reference FROM outbox_emails o JOIN bookings b ON b.id = o.booking_id "
            "WHERE o.recipient = %s AND o.subject LIKE 'Booking confirmed:%%' ORDER BY o.id LIMIT 1",
            (SAMPLE,)).fetchone()
    m = LINK.search(body)
    assert m, body
    return m.group(1), m.group(2), reference


def open_manage_link(page: Page, base_url: str, link: str) -> str:
    """Open a Manage link and wait for the Booking; returns its reference."""
    page.goto(link)
    page.wait_for_url(re.compile(re.escape(base_url) + r"/manage/" + REFERENCE + "$"))
    page.get_by_role("heading", name="Manage booking").wait_for()
    page.locator(".summary").wait_for()
    return page.url.rsplit("/", 1)[1]


def test_the_sample_link_from_the_outbox_opens_the_booking(page: Page, base_url, stack):
    link, token, reference = sample_link(stack)
    assert link.startswith(base_url + "/manage#t=")
    page.set_viewport_size({"width": 1366, "height": 768})
    requests = []
    page.on("request", lambda r: requests.append(r.url))
    assert open_manage_link(page, base_url, link) == reference
    page.wait_for_function("() => document.activeElement && document.activeElement.tagName === 'H1'")
    assert page.url == f"{base_url}/manage/{reference}"
    assert token not in page.url and page.evaluate("location.hash") == ""
    assert page.title() == "Manage booking – Saunalöyly"
    assert page.locator(".reference").inner_text() == reference
    labels = page.locator(".summary-row dt").all_inner_texts()
    assert labels == ["Date", "Session", "Seats", "Total"]
    assert page.locator(".summary").inner_text().count("@") == 0  # no name or email on the page
    assert re.fullmatch(r"You can change this booking until \w+day \d{1,2} \w+ \d{4} at \d\d:\d\d\.",
                        page.locator(".manage-until").inner_text())
    assert page.locator("button").count() == 0  # the page itself changes nothing: Changes are links to their steps
    assert page.get_by_role("link", name="Move seats").get_attribute("href") == f"/manage/{reference}/move"
    others = [u for u in requests if not (u == base_url or u.startswith(base_url + "/"))]
    assert not others, f"requests to another origin: {others}"
    assert not [u for u in requests if token in u.split("#", 1)[0]]  # the token is never in a path or query
    assert [c["name"] for c in page.context.cookies()] == ["bp_session"]
    page.reload()  # the grant stays with this browser's session
    page.get_by_role("heading", name="Manage booking").wait_for()
    assert page.locator(".reference").inner_text() == reference


def test_after_the_cutoff_the_page_gives_the_approved_reason(page: Page, base_url, stack):
    """The clock moves (`clock.off`) to one hour before the sample's session: past its 12-hour Cutoff, before its end."""
    link, _token, reference = sample_link(stack)
    with psycopg.connect(db_url(stack)) as c:
        start = c.execute("SELECT lower(w.during) FROM bookings b JOIN windows w ON w.id = b.window_id "
                          "WHERE b.reference = %s", (reference,)).fetchone()[0]
        shift = c.execute("SELECT %s::timestamptz - interval '1 hour' - app_now()", (start,)).fetchone()[0]
        c.execute("UPDATE clock SET off = off + %s", (shift,))
        c.execute("UPDATE sessions SET expires_at = expires_at + %s WHERE expires_at <> 'infinity'", (shift,))
        c.commit()
        try:
            open_manage_link(page, base_url, link)
            notice = page.locator(".notice")
            assert notice.inner_text().strip() == (
                "This booking can no longer be changed. Changes are only possible until 12 hours before the session "
                "starts."), notice.inner_text()
            assert page.locator(".manage-until").count() == 0
            assert page.get_by_role("link", name="Move seats").count() == 0  # no Change offered (Story 4.2)
            a11y.check_axe(page)
        finally:
            c.rollback()
            c.execute("UPDATE clock SET off = off - %s", (shift,))
            c.execute("UPDATE sessions SET expires_at = expires_at - %s WHERE expires_at <> 'infinity'", (shift,))
            c.commit()


def test_the_manage_page_passes_axe_fits_every_width_and_works_by_keyboard(page: Page, base_url, stack):
    link, _token, _reference = sample_link(stack)
    open_manage_link(page, base_url, link)
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)
    page.set_viewport_size({"width": 1366, "height": 768})
    a11y.tab_to(page, page.get_by_role("link", name="Saunalöyly"))
    a11y.press(page, "Enter")
    page.wait_for_url(base_url + "/")


def test_a_guessed_reference_and_bad_links_are_not_available(page: Page, browser, base_url, stack):
    _link, _token, reference = sample_link(stack)
    context = browser.new_context(ignore_https_errors=True)  # a browser that never opened the link
    try:
        stranger = context.new_page()
        for path in (f"/manage/{reference}", "/manage/ZZZZZZZZ", "/manage#t=not-a-real-token", "/manage"):
            stranger.goto(base_url + path)
            stranger.get_by_role("heading", name=NOT_AVAILABLE).wait_for()
            assert stranger.locator(".reference, .summary").count() == 0, path
            assert "#" not in stranger.url, path
        # a refused link creates no session
        assert context.cookies() == []
        a11y.check_axe(stranger)
        a11y.no_horizontal_scroll(stranger)
        stranger.set_viewport_size({"width": 1366, "height": 768})
        a11y.tab_to(stranger, stranger.get_by_role("link", name="Go to the Saunalöyly start page"))
        a11y.press(stranger, "Enter")
        stranger.wait_for_url(base_url + "/")
    finally:
        context.close()


LOAD_FAILED = "The booking could not be loaded, please try again."
UNAVAILABLE = dict(status=503, content_type="application/json", body='{"detail": {"error": "try_again"}}')


def test_a_failed_read_shows_the_heading_and_a_notice_not_not_available(page: Page, base_url, stack):
    link, _token, reference = sample_link(stack)
    page.route(f"**/api/manage/{reference}", lambda route: route.fulfill(**UNAVAILABLE))
    page.goto(link)
    page.wait_for_url(f"{base_url}/manage/{reference}")
    page.get_by_role("heading", name="Manage booking").wait_for()
    notice = page.locator(".notice")
    notice.wait_for()
    assert notice.inner_text() == LOAD_FAILED
    assert page.get_by_role("heading", name=NOT_AVAILABLE).count() == 0
    assert page.locator(".summary").count() == 0


def test_a_failed_open_shows_the_heading_and_a_notice_not_not_available(page: Page, base_url, stack):
    link, token, _reference = sample_link(stack)
    page.route("**/api/manage/open", lambda route: route.fulfill(**UNAVAILABLE))
    page.goto(link)
    page.get_by_role("heading", name="Manage booking").wait_for()
    notice = page.locator(".notice")
    notice.wait_for()
    assert notice.inner_text() == LOAD_FAILED
    assert page.get_by_role("heading", name=NOT_AVAILABLE).count() == 0
    assert page.url == f"{base_url}/manage" and token not in page.url


def test_caddy_marks_the_manage_pages_and_api_noindex_and_no_referrer(base_url, stack):
    _link, _token, reference = sample_link(stack)
    with httpx.Client(base_url=base_url, verify=trust.context(), timeout=30, headers={"Origin": base_url}) as c:
        answers = [c.get("/manage"), c.get(f"/manage/{reference}"), c.get(f"/api/manage/{reference}"),
                   c.post("/api/manage/open", json={"token": "not-a-real-token"})]
    assert [r.status_code for r in answers] == [200, 200, 404, 404]
    for r in answers:
        assert r.headers.get("x-robots-tag") == "noindex", r.url
        assert r.headers.get("referrer-policy") == "no-referrer", r.url
    assert answers[3].json() == {"detail": {"error": "not_found"}}
