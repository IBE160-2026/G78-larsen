"""The automated part of FR-23's manual passes (Story 2.4), built on `a11y`: every key goes through `a11y.press` or
`a11y.tab_to`, so focus is checked visible after each one.

- Book seats' tab order puts the date field, the calendar, the Seat picker and the Session list before the rail's
  "Continue booking" (WCAG 2.4.3, EXPERIENCE.md Open Item 14).
- The Session list's accessibility tree names every row with its Seats left text, and unavailable rows are disabled
  with theirs ("1 seat left, not enough for 2", "Sold out") (UX-DR19, UX-DR35). Nothing else in the list is exposed,
  so a screen reader in browse mode reads each row once.
- At 200 % zoom on 1366 x 768 and 1920 x 1080 screens, Book seats, Details and Review are completed with the keyboard
  alone, "Continue booking" and Pay are pressed, and Confirmation is reached. Review and Confirmation are one column
  (the rail above main) and the email in the Booking summary stays on one line. A full-page screenshot of Book
  seats, Details, Review and Confirmation is saved under `test-results/zoom/` (git-ignored) for Lisa's manual look
  (WCAG 1.4.4).

The keyboard flows from Landing to Confirmation and through Sign-in, Booking list, Outbox and Sign out are in
`test_fr05_book_and_pay.py`, `test_fr15_sign_in.py`, `test_fr16_booking_list.py` and `test_fr17_outbox.py`.
"""

from __future__ import annotations

import re
from pathlib import Path

import psycopg
import pytest
from playwright.sync_api import Browser, Page

from . import a11y
from .admin import db_url
from .guest import free_windows, open_session
from .test_fr11_refusals import RAW_FILL

ZOOM_DIR = Path(__file__).resolve().parents[2] / "test-results" / "zoom"
REFERENCE = re.compile(r"/confirmation/[0-9A-HJKMNP-TV-Z]{8}$")

_STOP = """() => {
  const el = document.activeElement;
  return {id: el.id || '', name: el.getAttribute('name') || '', calendar: !!el.closest('.cal-grid'),
          text: (el.textContent || '').replace(/\\s+/g, ' ').trim()};
}"""


@pytest.fixture
def db(stack):
    with psycopg.connect(db_url(stack)) as c:
        yield c
        c.rollback()
        c.execute("DELETE FROM bookings WHERE name = 'E2E fill'")
        c.commit()


def dotted(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}.{m}.{y}"


def choose(page: Page, iso: str) -> None:
    """Type the date, choose 2 Seats and the first open Session, all with the keyboard."""
    a11y.tab_to(page, page.locator("#date"))
    page.keyboard.type(dotted(iso))
    a11y.press(page, "Enter")
    page.wait_for_selector(".session-rows")
    a11y.tab_to(page, page.locator("#seats-1"))
    # the Sessions are read again for 2 Seats; Tab must not reach the rows before they are drawn again
    with page.expect_response(lambda r: "/api/windows" in r.url and "seats=2" in r.url):
        a11y.press(page, "ArrowRight")
    assert page.locator("#seats-2").is_checked()
    page.wait_for_selector(".session-rows")
    session = page.locator(".session-row input:not([disabled])").first
    a11y.tab_to(page, session)
    a11y.press(page, "Space")
    assert session.is_checked()


def test_book_seats_tab_order_puts_the_questions_before_continue(page: Page, base_url):
    window = free_windows(base_url)[0]
    open_session(page, base_url)
    choose(page, window["date"])
    page.reload()  # the draft is restored and nothing has focus: Tab starts at the top
    page.wait_for_selector(".session-row input:checked")
    page.wait_for_load_state("networkidle")
    continue_booking = page.get_by_role("button", name="Continue booking")
    stops = []
    for _ in range(80):
        a11y.press(page, "Tab")
        stops.append(page.evaluate(_STOP))
        if continue_booking.evaluate("el => el === document.activeElement"):
            break
    else:
        raise AssertionError(f"Continue booking was not reached: {stops}")

    def first(match) -> int | None:
        return next((i for i, s in enumerate(stops) if match(s)), None)

    order = [first(lambda s: s["id"] == "date"), first(lambda s: s["calendar"]),
             first(lambda s: s["id"].startswith("seats-")), first(lambda s: s["name"] == "session")]
    assert None not in order, stops  # each question was reached before Continue booking
    assert order == sorted(order), stops


def test_the_session_list_names_each_row_with_its_seats_left(page: Page, base_url, db):
    windows = free_windows(base_url)
    one_left, full = windows[0], windows[1]
    db.execute(RAW_FILL, (one_left["id"], 43))
    db.execute(RAW_FILL, (full["id"], 44))
    db.commit()
    open_session(page, base_url)
    page.fill("#date", dotted(one_left["date"]))
    page.locator("#date").focus()
    a11y.press(page, "Enter")
    page.locator("label.cell:has(#seats-2)").click()
    page.wait_for_load_state("networkidle")
    page.locator(".session-row.unavailable", has_text="Sold out").wait_for()
    snapshot = page.locator(".session-rows").aria_snapshot()
    radios = [line.strip() for line in snapshot.splitlines() if line.strip().startswith("- radio")]
    assert len(radios) == 8, snapshot
    # the visible row text is aria-hidden: browse mode reads each row once, by its radio (manual NVDA pass 2026-11-24)
    assert not [line for line in snapshot.splitlines() if not line.strip().startswith("- radio")], snapshot
    assert radios[0] == '- radio "10:00 to 11:30, 1 seat left, not enough for 2" [disabled]', snapshot
    assert radios[1] == '- radio "11:30 to 13:00, Sold out" [disabled]', snapshot
    for line in radios[2:]:
        assert re.fullmatch(r'- radio "\d\d:\d\d to \d\d:\d\d, 44 seats left"', line), snapshot


_EMAIL_LINES = """() => {
  const row = [...document.querySelectorAll('.summary-row')].find(r => r.querySelector('dt').textContent === 'Email');
  const range = document.createRange();
  range.selectNodeContents(row.querySelector('dd'));
  return new Set([...range.getClientRects()].map(r => Math.round(r.top))).size;
}"""


def email_lines(page: Page) -> int:
    """How many lines the Guest's email takes in the Booking summary."""
    return page.evaluate(_EMAIL_LINES)


def assert_stacked(page: Page) -> None:
    """Below 1024 px the shell is one column: the rail is drawn above main, both at the full width (manual zoom
    pass 2026-11-24, EXPERIENCE.md Zoom)."""
    rail, main = page.locator(".rail").bounding_box(), page.locator("#main").bounding_box()
    assert rail["y"] + rail["height"] <= main["y"] + 1, (rail, main)
    assert main["width"] >= page.viewport_size["width"] - 1, (main, page.viewport_size)


@pytest.mark.parametrize("screen", [(1366, 768), (1920, 1080)], ids=["1366x768", "1920x1080"])
def test_the_booking_flow_at_200_percent_zoom_with_the_keyboard_alone(browser: Browser, base_url, screen):
    ZOOM_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{screen[0]}x{screen[1]}"
    window = free_windows(base_url)[0]
    for which in ("book-seats", "details", "review", "confirmation"):
        (ZOOM_DIR / f"{which}-{name}.png").unlink(missing_ok=True)  # only this run's screenshots count
    with a11y.zoomed(browser, *screen) as page:
        open_session(page, base_url)
        choose(page, window["date"])
        page.screenshot(path=ZOOM_DIR / f"book-seats-{name}.png", full_page=True)
        a11y.tab_to(page, page.get_by_role("button", name="Continue booking"))
        a11y.press(page, "Enter")

        page.wait_for_url(base_url + "/book-seats/details")
        page.wait_for_selector("#name")
        a11y.tab_to(page, page.locator("#name"))
        page.keyboard.type("Zoom Guest")
        a11y.tab_to(page, page.locator("#email"))
        page.keyboard.type("zoom@example.com")
        page.screenshot(path=ZOOM_DIR / f"details-{name}.png", full_page=True)
        a11y.tab_to(page, page.get_by_role("button", name="Continue booking"))
        a11y.press(page, "Enter")

        page.wait_for_url(base_url + "/book-seats/review")
        pay = page.get_by_role("button", name="Pay NOK 500")
        pay.wait_for()
        a11y.tab_to(page, page.locator("#terms"))
        a11y.press(page, "Space")
        assert page.locator("#terms").is_checked()
        page.screenshot(path=ZOOM_DIR / f"review-{name}.png", full_page=True)
        assert_stacked(page)
        assert email_lines(page) == 1  # the email is not split mid-word
        a11y.tab_to(page, pay)
        a11y.press(page, "Enter")

        page.wait_for_url(REFERENCE)
        page.wait_for_selector(".reference")
        page.wait_for_selector(".summary")
        page.screenshot(path=ZOOM_DIR / f"confirmation-{name}.png", full_page=True)
        assert_stacked(page)
        assert email_lines(page) == 1
    for which in ("book-seats", "details", "review", "confirmation"):
        assert (ZOOM_DIR / f"{which}-{name}.png").stat().st_size > 0


# Records whether a Confirmation address was ever drawn without its h1 in main (the h1 must be there at once).
_WATCH_CONFIRMATION = """() => {
  window.__confirmationWithoutH1 = false;
  new MutationObserver(() => {
    const main = document.querySelector('#main');
    if (location.pathname.startsWith('/confirmation/') && main && !main.querySelector('h1'))
      window.__confirmationWithoutH1 = true;
  }).observe(document.documentElement, {childList: true, subtree: true});
}"""


def test_after_pay_confirmation_has_its_heading_at_once_and_focused(page: Page, base_url):
    """Straight after Pay, Confirmation is never drawn without "Booking confirmed": a page with only the rail's
    Wordmark was read by NVDA, which then missed the focus moving to the h1 (manual NVDA pass 2026-11-24)."""
    window = free_windows(base_url)[5]
    open_session(page, base_url)
    page.evaluate("d => sessionStorage.setItem('draft:seats', JSON.stringify(d))",
                  {"date": window["date"], "seats": 2, "window_id": window["id"], "name": "Focus Guest",
                   "email": "focus@example.com"})
    page.goto(base_url + "/book-seats/review")
    pay = page.get_by_role("button", name="Pay NOK 500")
    pay.wait_for()
    page.locator("label.terms-check").click()
    page.evaluate(_WATCH_CONFIRMATION)
    pay.click()
    page.wait_for_url(REFERENCE)
    page.wait_for_selector(".email-body")
    assert page.evaluate("window.__confirmationWithoutH1") is False
    assert page.evaluate("document.activeElement.tagName + ' ' + document.activeElement.textContent") == \
        "H1 Booking confirmed"
