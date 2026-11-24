"""The Outbox in the browser (FR-17, FR-21, FR-22, FR-23, IV-5, UX-DR14, UX-DR32, UX-DR33), against the whole stack.

- The Administrator signs in and opens the Outbox from the Administrator bar with the keyboard alone (every key through
  `a11y.press` / `a11y.tab_to`), and finds the confirmation of a Booking made in the browser in the same test: its
  subject as the entry heading, "Sent dd.mm.yyyy HH:MM" (Venue time) and "To {recipient}" above the body, and a body
  equal to the one the Confirmation showed, with its reference.
- A raw row whose body holds `<script>alert(1)</script>` and `<b>x</b>` on two lines is shown as text with its line
  break kept; no dialog opens.
- A failed read shows the "please try again" Notice, an empty Outbox "No emails", a masked entry "To Anonymised" and
  "Removed after 12 months.", and a 401 goes to Sign-in (all through `page.route`).
- The title is "Outbox – Saunalöyly", axe reports no A or AA failure, and nothing scrolls sideways at 1024, 1366 or
  1920 px.

The stack runs on the real clock with the sample Bookings of the seed.
"""

from __future__ import annotations

import json
import re

import psycopg
from playwright.sync_api import Page

from . import a11y
from .admin import BOOKINGS, LOGIN, SIGN_IN, db_url, no_throttle, open_sign_in, type_login  # noqa: F401 (fixture)
from .guest import book_in_browser, free_windows, open_session

OUTBOX = "/admin/outbox"
NBSP = " "


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace(NBSP, " ")).strip()


def sign_in(page: Page, base_url: str) -> None:
    """Sign in with the keyboard alone; the Booking list then shows its date field."""
    open_sign_in(page, base_url)
    type_login(page, LOGIN["password"])
    page.wait_for_url(base_url + BOOKINGS)
    page.locator("#date").wait_for()


def open_outbox(page: Page, base_url: str) -> None:
    page.goto(base_url + OUTBOX)
    page.get_by_role("heading", level=1, name="Outbox").wait_for()
    page.wait_for_load_state("networkidle")


def entry(page: Page, subject: str):
    """The Outbox entry whose heading is the subject."""
    return page.locator("section.outbox-entry").filter(has=page.get_by_role("heading", level=2, name=subject))


def dotted_time(stamp: str) -> str:
    return f"{stamp[8:10]}.{stamp[5:7]}.{stamp[0:4]} {stamp[11:16]}"


def route_outbox(page: Page, status: int, body: dict) -> None:
    page.route("**/api/admin/outbox*", lambda route: route.fulfill(
        status=status, content_type="application/json", body=json.dumps(body)))


def test_the_confirmation_of_a_browser_booking_from_the_bar_with_the_keyboard_alone(page: Page, base_url, browser):
    window = free_windows(base_url)[2]
    guest = browser.new_context(base_url=base_url, ignore_https_errors=True).new_page()
    try:
        open_session(guest, base_url)
        booked = book_in_browser(guest, window, 2, "Marit Solberg")
    finally:
        guest.context.close()
    reference = booked["booking"]["reference"]
    sent = booked["emails"][0]

    sign_in(page, base_url)
    # focus is on the h1 after navigation; the bar is before it (Booking list, Outbox, Sign out)
    page.wait_for_function("() => document.activeElement && document.activeElement.tagName === 'H1'")
    outbox = page.get_by_role("navigation", name="Administrator").get_by_role("link", name="Outbox")
    for _ in range(3):
        a11y.press(page, "Shift+Tab")
        if outbox.evaluate("el => el === document.activeElement"):
            break
    assert outbox.evaluate("el => el === document.activeElement")
    a11y.press(page, "Enter")
    page.wait_for_url(base_url + OUTBOX)
    page.get_by_role("heading", level=1, name="Outbox").wait_for()
    assert page.title() == "Outbox – Saunalöyly"
    assert outbox.get_attribute("aria-current") == "page"

    e = entry(page, f"Booking confirmed: {reference}")
    e.wait_for()
    assert e.count() == 1
    emails = page.evaluate("""async () => {
        const r = await fetch('/api/admin/outbox', {credentials: 'same-origin'});
        return (await r.json()).emails;
    }""")
    stamp = next(m["created_at"] for m in emails if m["subject"] == sent["subject"])
    lines = [_norm(t) for t in e.locator("p.reference-label").all_inner_texts()]
    assert lines == [f"Sent {dotted_time(stamp)}", "To ingrid@example.com"]
    body = e.locator(".email-body")
    assert body.inner_text() == sent["body"]
    assert reference in body.inner_text()
    # the newest email is first: nothing was sent after this Booking
    assert page.locator("section.outbox-entry").first.locator("h2").inner_text() == sent["subject"]
    assert page.locator("section.outbox-entry").count() == len(emails)
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)


def test_a_hostile_body_is_shown_as_text(page: Page, base_url, stack):
    subject, body = "<img src=x onerror=alert(1)> Hostile raw row", "<script>alert(1)</script>\n<b>x</b>"
    with psycopg.connect(db_url(stack)) as c:
        c.execute("INSERT INTO outbox_emails (recipient, subject, body) VALUES (%s, %s, %s)",
                  ("<i>raw@example.com</i>", subject, body))
    dialogs = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))
    sign_in(page, base_url)
    open_outbox(page, base_url)
    e = entry(page, subject)
    assert e.count() == 1
    assert e.locator("h2").inner_text() == subject
    assert e.locator(".email-body").inner_text() == body
    assert _norm(e.locator("p.reference-label").nth(1).inner_text()) == "To <i>raw@example.com</i>"
    assert page.locator("main script, main b, main i, main img").count() == 0
    page.wait_for_timeout(300)
    assert dialogs == []


def test_a_failed_read_shows_the_notice(page: Page, base_url):
    sign_in(page, base_url)
    route_outbox(page, 500, {"detail": {"error": "internal_error"}})
    page.goto(base_url + OUTBOX)
    notice = page.locator(".notice")
    notice.wait_for()
    assert _norm(notice.inner_text()) == "The outbox could not be loaded, please try again."
    assert page.locator("section.outbox-entry").count() == 0


def test_an_empty_outbox_says_no_emails(page: Page, base_url):
    sign_in(page, base_url)
    route_outbox(page, 200, {"emails": []})
    open_outbox(page, base_url)
    assert page.get_by_text("No emails", exact=True).is_visible()
    assert page.locator("section.outbox-entry").count() == 0
    a11y.check_axe(page)


def test_a_masked_entry_says_so(page: Page, base_url):
    sign_in(page, base_url)
    route_outbox(page, 200, {"emails": [
        {"id": 7, "created_at": "2025-12-01T11:30:00+01:00", "recipient": "", "subject": "Booking confirmed: ABCD1234",
         "body": ""}]})
    open_outbox(page, base_url)
    e = entry(page, "Booking confirmed: ABCD1234")
    assert [_norm(t) for t in e.locator("p.reference-label").all_inner_texts()] == [
        "Sent 01.12.2025 11:30", "To Anonymised"]
    assert _norm(e.locator(".email-body").inner_text()) == "Removed after 12 months."
    a11y.check_axe(page)


def test_a_401_on_the_read_goes_to_sign_in(page: Page, base_url):
    sign_in(page, base_url)
    route_outbox(page, 401, {"detail": {"error": "not_signed_in"}})
    page.goto(base_url + OUTBOX)
    page.wait_for_url(base_url + SIGN_IN)
    page.wait_for_selector("#password")
    assert page.get_by_text("please try again").count() == 0
