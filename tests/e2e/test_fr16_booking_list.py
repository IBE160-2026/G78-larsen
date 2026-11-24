"""The Booking list in the browser (FR-16, FR-21, FR-22, FR-23, UX-DR31, UX-DR33, UX-DR37), against the whole stack.

- The Administrator signs in with the keyboard alone and finds a Booking made through the Guest flow in the right
  Session group, with its reference, name, "NOK" total and time of booking (dd.mm.yyyy HH:MM, Venue time).
- Without `?date` the list shows the API's today; "Next day" and "Previous day" move between days with the keyboard
  alone (every key through `a11y.press` / `a11y.tab_to`), and the address keeps the day.
- A raw row whose name is `<script>alert(1)</script>` and whose email holds SQL text is shown as text; no dialog opens.
- The seeded full session (today + 3, 19:00) has the sold-out header with "Seats left 0" and "Sold out" in weight 600;
  the seeded 42-of-44 session (today + 2, 17:30) says "Seats left 2".
- A failed read shows the "please try again" Notice; a malformed typed date shows the Field error.
- The title is "Booking list – Saunalöyly", axe reports no A or AA failure, and nothing scrolls sideways at 1024,
  1366 or 1920 px.

The stack runs on the real clock with the sample Bookings of the seed.
"""

from __future__ import annotations

import datetime as dt
import re
import secrets

import httpx
import psycopg
from playwright.sync_api import Page

from . import a11y, trust
from .admin import BOOKINGS, LOGIN, SIGN_IN, db_url, no_throttle, open_sign_in, type_login  # noqa: F401 (fixture)
from .guest import book_in_browser, free_windows, open_session

CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
NBSP = " "


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace(NBSP, " ")).strip()


def today(base_url: str) -> dt.date:
    return dt.date.fromisoformat(httpx.get(base_url + "/api/windows", timeout=30,
                                           verify=trust.context()).json()["today"])


def dotted(d: dt.date) -> str:
    return d.strftime("%d.%m.%Y")


def sign_in(page: Page, base_url: str) -> None:
    """Sign in with the keyboard alone; the Booking list then shows its date field."""
    open_sign_in(page, base_url)
    type_login(page, LOGIN["password"])
    page.wait_for_url(base_url + BOOKINGS)
    page.locator("#date").wait_for()


def open_day(page: Page, base_url: str, day: dt.date) -> None:
    page.goto(f"{base_url}{BOOKINGS}?date={day.isoformat()}")
    page.get_by_role("heading", level=1, name="Booking list").wait_for()
    page.wait_for_function("d => document.querySelector('#date') && document.querySelector('#date').value === d",
                           arg=dotted(day))
    page.wait_for_load_state("networkidle")


def group(page: Page, start: str, end: str):
    """The Session group whose heading names the session."""
    return page.locator("section.session-group").filter(
        has=page.get_by_role("heading", level=2, name=f"Session {start} to {end}"))


def test_a_guest_flow_booking_is_in_the_right_group(page: Page, base_url, browser):
    window = free_windows(base_url)[1]
    guest = browser.new_context(base_url=base_url, ignore_https_errors=True).new_page()
    try:
        open_session(guest, base_url)
        booked = book_in_browser(guest, window, 1, "Marit Solberg")["booking"]
    finally:
        guest.context.close()
    sign_in(page, base_url)
    assert page.title() == "Booking list – Saunalöyly"
    day = dt.date.fromisoformat(window["date"])
    open_day(page, base_url, day)
    start, end = window["start"][11:16], window["end"][11:16]
    g = group(page, start, end)
    assert g.count() == 1
    row = g.locator("tbody tr").filter(has_text=booked["reference"])
    cells = [_norm(c) for c in row.locator("td").all_inner_texts()]
    created = page.evaluate("""async (d) => {
        const r = await fetch('/api/admin/bookings?date=' + d, {credentials: 'same-origin'});
        return (await r.json()).windows.flatMap(w => w.bookings);
    }""", window["date"])
    stamp = next(b["created_at"] for b in created if b["reference"] == booked["reference"])
    expected_time = f"{stamp[8:10]}.{stamp[5:7]}.{stamp[0:4]} {stamp[11:16]}"
    assert cells == [booked["reference"], "Marit Solberg", "ingrid@example.com", "1", "NOK 250", expected_time,
                     "Active"]  # the Status column (Story 4.2)
    assert _norm(g.locator(".session-group-figures").inner_text()) == \
        "Seat capacity 44 · Seats booked 1 · Seats left 43"
    # every other session of the day is listed with "No bookings"
    assert page.locator("section.session-group").count() == 8
    assert page.get_by_text("No bookings", exact=True).count() == 7
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)


def test_previous_and_next_day_with_the_keyboard_alone(page: Page, base_url):
    now = today(base_url)
    sign_in(page, base_url)
    assert page.url == base_url + BOOKINGS
    page.wait_for_function("d => document.querySelector('#date').value === d", arg=dotted(now))

    a11y.tab_to(page, page.get_by_role("link", name="Next day"))
    a11y.press(page, "Enter")
    nxt = now + dt.timedelta(days=1)
    page.wait_for_url(f"{base_url}{BOOKINGS}?date={nxt.isoformat()}")
    page.wait_for_function("d => document.querySelector('#date').value === d", arg=dotted(nxt))
    # the seeded Booking of today + 1 (14:30, 2 Seats)
    g = group(page, "14:30", "16:00")
    g.get_by_text("Ingrid Berg", exact=True).wait_for()

    a11y.press(page, "Shift+Tab")
    assert page.get_by_role("link", name="Previous day").evaluate("el => el === document.activeElement")
    a11y.press(page, "Enter")
    page.wait_for_url(f"{base_url}{BOOKINGS}?date={now.isoformat()}")
    page.wait_for_function("d => document.querySelector('#date').value === d", arg=dotted(now))

    # typing a date commits on Enter and replaces the address; a malformed one shows the Field error
    field = page.locator("#date")
    a11y.press(page, "Shift+Tab")  # Previous day kept focus; the field is the stop before it
    assert field.evaluate("el => el === document.activeElement")
    a11y.press(page, "Control+A")
    page.keyboard.type(dotted(now + dt.timedelta(days=3)))
    a11y.press(page, "Enter")
    page.wait_for_url(f"{base_url}{BOOKINGS}?date={(now + dt.timedelta(days=3)).isoformat()}")
    a11y.press(page, "Control+A")
    page.keyboard.type("2026-1-1")
    a11y.press(page, "Enter")
    assert _norm(page.locator(".field-error").inner_text()) == "Enter the date as dd.mm.yyyy"
    assert field.get_attribute("aria-invalid") == "true"

    # reload keeps the day
    page.reload()
    page.wait_for_function("d => document.querySelector('#date') && document.querySelector('#date').value === d",
                           arg=dotted(now + dt.timedelta(days=3)))


def test_the_seeded_sessions_match_book_seats_and_the_full_one_is_sold_out(page: Page, base_url):
    now = today(base_url)
    sign_in(page, base_url)
    open_day(page, base_url, now + dt.timedelta(days=2))
    almost = group(page, "17:30", "19:00")
    assert _norm(almost.locator(".session-group-figures").inner_text()) == \
        "Seat capacity 44 · Seats booked 42 · Seats left 2"
    open_day(page, base_url, now + dt.timedelta(days=3))
    full = group(page, "19:00", "20:30")
    assert "session-group-full" in full.get_attribute("class")
    header = full.locator(".session-group-header")
    assert header.evaluate("el => getComputedStyle(el).backgroundColor") == "rgb(228, 235, 236)"  # unavailable
    strong = header.locator("strong")
    assert [_norm(t) for t in strong.all_inner_texts()] == ["Seats left 0", "Sold out"]
    assert strong.evaluate_all("els => els.map(e => getComputedStyle(e).fontWeight)") == ["600", "600"]
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)


def test_hostile_text_is_shown_as_text(page: Page, base_url, stack):
    day = today(base_url) + dt.timedelta(days=4)
    ws = httpx.get(base_url + "/api/windows", params={"date": day.isoformat()}, timeout=30,
                   verify=trust.context()).json()["windows"]
    window = ws[0]
    name, email = "<script>alert(1)</script>", "x'); DROP TABLE bookings; --"
    reference = "".join(secrets.choice(CROCKFORD) for _ in range(8))
    with psycopg.connect(db_url(stack)) as c:
        c.execute("INSERT INTO bookings (window_id, seats, reference, name, email, price_per_seat_ore, total_ore) "
                  "VALUES (%s, 1, %s, %s, %s, 25000, 25000)", (window["id"], reference, name, email))
    dialogs = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))
    sign_in(page, base_url)
    open_day(page, base_url, day)
    row = page.locator("tbody tr").filter(has_text=reference)
    cells = row.locator("td").all_inner_texts()
    assert cells[1] == name and cells[2] == email
    assert page.locator("table script").count() == 0
    page.wait_for_timeout(300)
    assert dialogs == []


def test_a_failed_read_shows_the_notice(page: Page, base_url):
    sign_in(page, base_url)
    page.route("**/api/admin/bookings*", lambda route: route.fulfill(
        status=500, content_type="application/json", body='{"detail": {"error": "internal_error"}}'))
    page.goto(f"{base_url}{BOOKINGS}?date={today(base_url).isoformat()}")
    notice = page.locator(".notice")
    notice.wait_for()
    assert _norm(notice.inner_text()) == "The booking list could not be loaded, please try again."
    assert page.locator("section.session-group").count() == 0



def test_a_401_on_the_read_goes_to_sign_in(page: Page, base_url):
    sign_in(page, base_url)
    page.route("**/api/admin/bookings*", lambda route: route.fulfill(
        status=401, content_type="application/json", body='{"detail": {"error": "not_signed_in"}}'))
    page.goto(f"{base_url}{BOOKINGS}?date={today(base_url).isoformat()}")
    page.wait_for_url(base_url + SIGN_IN)
    page.wait_for_selector("#password")
    assert page.get_by_text("please try again").count() == 0


def test_an_impossible_date_in_the_address_shows_today(page: Page, base_url):
    now = today(base_url)
    sign_in(page, base_url)
    page.goto(f"{base_url}{BOOKINGS}?date=2026-02-30")
    page.wait_for_function("d => document.querySelector('#date') && document.querySelector('#date').value === d",
                           arg=dotted(now))
    assert page.locator(".notice").count() == 0


def test_a_date_with_no_sessions(page: Page, base_url):
    sign_in(page, base_url)
    open_day(page, base_url, today(base_url) + dt.timedelta(days=400))
    assert page.get_by_text("No sessions on this day", exact=True).is_visible()
    assert page.locator("section.session-group").count() == 0
