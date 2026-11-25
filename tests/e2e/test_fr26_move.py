"""FR-26 / AD-29 (Story 4.2) in the compose stack, over HTTPS: a Guest moves 1 of 2 Seats through the Manage page with
the keyboard alone (every key through `a11y.press` / `a11y.tab_to`). The confirming step states what will happen and
shows the current session as a disabled row; the result page shows both emails under "Sent by email:", the new
reference and its Manage link; the Booking list shows both Bookings in their sessions, their status and the history
line. axe finds no A or AA failure on the step and the result, and nothing scrolls sideways at 1024, 1366 and 1920 px.
A refusal shows its Notice: `no_seat_free` keeps the choices and re-reads the Sessions, `booking_changed` reopens the
step fresh with a new key. A one-Seat Booking has no "How many" question and moves whole.
"""

from __future__ import annotations

import datetime as dt
import re

import psycopg
import pytest
from playwright.sync_api import Page

from . import a11y
from .admin import BOOKINGS, LOGIN, db_url, no_throttle, open_sign_in, type_login  # noqa: F401 (fixture)
from .guest import book_in_browser, free_windows, open_session

REFERENCE = r"[0-9A-HJKMNP-TV-Z]{8}"
LINK = re.compile(r"(?m)^(https://\S+/manage#t=[A-Za-z0-9_-]{43})$")
NBSP = "\u00a0"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace(NBSP, " ")).strip()


def _dotted(iso: str) -> str:
    return dt.date.fromisoformat(iso).strftime("%d.%m.%Y")


def _session(w: dict) -> str:
    return f"{_dotted(w['date'])} {w['start'][11:16]}–{w['end'][11:16]}"


def test_a_guest_moves_one_of_two_seats_with_the_keyboard_alone(page: Page, browser, base_url):
    windows = free_windows(base_url)
    current, target = windows[1], windows[2]
    page.set_viewport_size({"width": 1366, "height": 768})
    open_session(page, base_url)
    paid = book_in_browser(page, current, 2, "Kari Nordmann")
    reference = paid["booking"]["reference"]
    link = LINK.search(paid["emails"][0]["body"]).group(1)

    # the Manage page offers the move; the step opens with the keyboard alone
    page.goto(link)
    page.wait_for_url(f"{base_url}/manage/{reference}")
    page.get_by_role("heading", name="Manage booking").wait_for()
    a11y.tab_to(page, page.get_by_role("link", name="Move seats"))
    a11y.press(page, "Enter")
    page.wait_for_url(f"{base_url}/manage/{reference}/move")
    page.get_by_role("heading", level=1, name="Move seats").wait_for()
    page.wait_for_function("() => document.activeElement && document.activeElement.tagName === 'H1'")
    assert page.title() == "Move seats – Saunalöyly"
    key = page.evaluate(f"() => sessionStorage.getItem('draft:change:{reference}:move')")
    assert key and re.fullmatch(r"[0-9a-f-]{36}", key)

    # 1. how many: 1 or 2 (the Booking's Seats)
    assert _norm(page.locator("#seats legend").inner_text()) == "1. How many seats do you want to move?"
    assert page.locator("input[name=seats]").count() == 2
    a11y.tab_to(page, page.locator("#seats-1"))
    a11y.press(page, "Space")
    assert page.locator("#seats-1").is_checked()
    # 2. the date, typed
    assert _norm(page.locator("label[for=date]").inner_text()) == "2. Choose a date"
    a11y.tab_to(page, page.locator("#date"))
    page.keyboard.type(_dotted(target["date"]))
    a11y.press(page, "Enter")
    page.locator(f"#session-{target['id']}").wait_for()
    # 3. the session: the current one is a disabled row that says so
    mine = page.locator(f"#session-{current['id']}")
    assert mine.is_disabled()
    assert mine.get_attribute("aria-label").endswith("Your current session")
    first = page.locator("input[name=session]:not([disabled])").first
    a11y.tab_to(page, first)
    for _ in range(10):
        if page.locator(f"#session-{target['id']}").is_checked():
            break
        a11y.press(page, "ArrowDown")
    assert page.locator(f"#session-{target['id']}").is_checked()

    # what will happen; nothing has changed yet
    step = page.locator("section.confirming-step")
    step.get_by_role("heading", name="What will happen").wait_for()
    rows = dict(zip([_norm(t) for t in step.locator(".summary-row dt").all_inner_texts()],
                    [_norm(t) for t in step.locator(".summary-row dd").all_inner_texts()]))
    assert list(rows) == ["Seats moved", "From", "To", "Seats left in this booking"]
    assert rows["Seats moved"] == "1 seat" and rows["Seats left in this booking"] == "1 seat"
    assert rows["From"].endswith(f"{current['start'][11:16]}–{current['end'][11:16]}")
    assert rows["To"].endswith(f"{target['start'][11:16]}–{target['end'][11:16]}")
    assert _norm(step.locator(".move-note").inner_text()) == "Nothing changes until you confirm."
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)
    page.set_viewport_size({"width": 1366, "height": 768})

    a11y.tab_to(page, page.get_by_role("button", name="Move 1 seat"))
    page.keyboard.press("Enter")  # the button is gone once the result shows; its h1 takes focus
    page.get_by_role("heading", level=1, name="Seats moved").wait_for()
    page.wait_for_function("() => document.activeElement && document.activeElement.tagName === 'H1'")
    a11y.assert_focus_visible(page)
    assert page.title() == "Seats moved – Saunalöyly"
    text = _norm(page.locator("main").inner_text())
    assert "Your booking has been changed." in text
    m = re.search(rf"Your moved seats have a new booking reference: ({REFERENCE})\.", text)
    assert m, text
    new_reference = m.group(1)
    sent = page.locator("section.email-as-sent")
    assert sent.count() == 2
    assert [_norm(t) for t in sent.locator("h2").all_inner_texts()] == ["Sent by email:", "Sent by email:"]
    change, confirmation = sent.locator(".email-body").all_inner_texts()
    assert change.startswith("Booking changed") and f"New booking reference: {new_reference}" in change
    assert "Seats moved: 1" in change and "/manage#t=" not in change
    assert "The Manage link in your booking confirmation email still works." in change
    assert confirmation.startswith("Booking confirmed") and f"Booking reference: {new_reference}" in confirmation
    assert LINK.search(confirmation) and LINK.search(confirmation).group(1) != link
    assert page.evaluate(f"() => sessionStorage.getItem('draft:change:{reference}:move')") is None
    back = page.get_by_role("link", name="Back to your booking")  # Lisa, 2026-11-24
    assert back.get_attribute("href") == f"/manage/{reference}"
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)

    # the Booking list: both Bookings in their sessions, their status, and the history line
    admin = browser.new_context(ignore_https_errors=True).new_page()
    try:
        open_sign_in(admin, base_url)
        type_login(admin, LOGIN["password"])
        admin.wait_for_url(base_url + BOOKINGS)
        admin.goto(f"{base_url}{BOOKINGS}?date={target['date']}")
        admin.get_by_role("heading", level=1, name="Booking list").wait_for()

        def group(w):
            return admin.locator("section.session-group").filter(has=admin.get_by_role(
                "heading", level=2, name=f"Session {w['start'][11:16]} to {w['end'][11:16]}"))

        original = group(current).locator("tr.booking-row").filter(has_text=reference)
        original.wait_for()
        cells = [_norm(c) for c in original.locator("td").all_inner_texts()]
        assert cells[0] == reference and cells[3] == "1" and cells[4] == "NOK 250" and cells[6] == "Active"
        history = _norm(group(current).locator("tr.booking-history").inner_text())
        assert re.fullmatch(rf"Moved 1 seat on \d\d\.\d\d\.\d{{4}} \d\d:\d\d from {re.escape(_session(current))} "
                            rf"to {re.escape(_session(target))} · new booking {new_reference}", history), history
        moved = group(target).locator("tr.booking-row").filter(has_text=new_reference)
        cells = [_norm(c) for c in moved.locator("td").all_inner_texts()]
        assert cells[0] == new_reference and cells[3] == "1" and cells[6] == "Active"
        assert _norm(group(target).locator(".session-group-figures").inner_text()) == \
            "Seat capacity 44 · Seats booked 1 · Seats left 43"
        a11y.check_axe(admin)
        a11y.no_horizontal_scroll(admin)
    finally:
        admin.context.close()


# ------------------------------------------------------------------ refusals and one-Seat Bookings

# in rows of at most 10 (a Seat booking holds 1 to 10, Story 5.1)
RAW_FILL = ("INSERT INTO bookings (window_id, seats, reference, name, email, price_per_seat_ore, total_ore) "
            "SELECT v.w, LEAST(10, v.s - 10 * g.i), 'F' || g.i || 'F' || lpad(v.w::text, 5, '0'), 'E2E fill', "
            "'e2e@example.com', 25000, LEAST(10, v.s - 10 * g.i) * 25000 "
            "FROM (VALUES (%s, %s)) AS v(w, s) CROSS JOIN LATERAL generate_series(0, (v.s - 1) / 10) AS g(i)")


@pytest.fixture
def db(stack):
    """A raw connection to the stack's database; the fill rows are removed afterwards."""
    with psycopg.connect(db_url(stack)) as c:
        yield c
        c.rollback()
        c.execute("DELETE FROM bookings WHERE name = 'E2E fill'")
        c.commit()


def _open_step(page: Page, base_url: str, window: dict, seats: int) -> str:
    """Pay for `seats` in `window`, open its Manage link and the move step; returns the reference."""
    open_session(page, base_url)
    paid = book_in_browser(page, window, seats, "Kari Nordmann")
    reference = paid["booking"]["reference"]
    page.goto(LINK.search(paid["emails"][0]["body"]).group(1))
    page.wait_for_url(f"{base_url}/manage/{reference}")
    page.get_by_role("link", name="Move seats").wait_for()
    page.goto(f"{base_url}/manage/{reference}/move")
    page.get_by_role("heading", level=1, name="Move seats").wait_for()
    page.locator(".cal-grid").wait_for()
    return reference


def _choose(page: Page, target: dict, seats: int | None) -> None:
    """With the keyboard alone: the number (when asked), the date (typed) and the session."""
    if seats is not None:
        a11y.tab_to(page, page.locator("input[name=seats]").first)
        a11y.press(page, "Space")
        while not page.locator(f"#seats-{seats}").is_checked():
            a11y.press(page, "ArrowRight")
    a11y.tab_to(page, page.locator("#date"))
    a11y.press(page, "Control+A")
    page.keyboard.type(_dotted(target["date"]))
    a11y.press(page, "Enter")
    page.locator(f"#session-{target['id']}").wait_for()
    a11y.tab_to(page, page.locator("input[name=session]:not([disabled])").first)
    for _ in range(10):
        if page.locator(f"#session-{target['id']}").is_checked():
            break
        a11y.press(page, "ArrowDown")
    assert page.locator(f"#session-{target['id']}").is_checked()
    page.get_by_role("heading", name="What will happen").wait_for()


def _slot(page: Page, reference: str):
    return page.evaluate(f"() => sessionStorage.getItem('draft:change:{reference}:move')")


def test_refusals_show_a_notice_keep_or_renew_the_step(page: Page, base_url, db):
    windows = free_windows(base_url)
    current, target, other = windows[1], windows[2], windows[3]
    page.set_viewport_size({"width": 1366, "height": 768})
    reference = _open_step(page, base_url, current, 2)
    first_key = _slot(page, reference)
    assert first_key

    # no_seat_free: the target is filled to 1 Seat left in the store, after the step showed it with 44
    _choose(page, target, 2)
    db.execute(RAW_FILL, (target["id"], 43))
    db.commit()
    a11y.tab_to(page, page.get_by_role("button", name="Move 2 seats"))
    a11y.press(page, "Enter")
    notice = page.locator(".notice", has_text="Nothing has changed.")
    notice.wait_for()
    assert _norm(notice.inner_text()) == "Only 1 seat left in this session. Nothing has changed."
    page.wait_for_function("() => document.activeElement && document.activeElement.classList.contains('notice')")
    assert page.locator("#seats-2").is_checked()  # the choices stay
    assert page.locator("#date").input_value() == _dotted(target["date"])
    # the Sessions are read again: the target no longer fits 2 Seats and is no longer chosen
    page.wait_for_function(  # the rows are gone while the Sessions load
        f"() => {{ const el = document.querySelector('#session-{target['id']}'); return !!el && el.disabled; }}")
    assert not page.locator(f"#session-{target['id']}").is_checked()
    assert page.locator("section.confirming-step").count() == 0
    assert _slot(page, reference) is None  # the key slot is gone after a refusal
    a11y.check_axe(page)

    # booking_changed: the Booking's version moves on in the store
    _choose(page, other, None)
    db.execute("UPDATE bookings SET version = version + 1 WHERE reference = %s", (reference,))
    db.commit()
    a11y.tab_to(page, page.get_by_role("button", name="Move 2 seats"))
    a11y.press(page, "Enter")
    changed = page.locator(".notice", has_text="changed in the meantime")
    changed.wait_for()
    assert _norm(changed.inner_text()) == "This booking was changed in the meantime. Check it and choose again."
    # the step opens fresh with a new key
    page.wait_for_function(f"() => !!sessionStorage.getItem('draft:change:{reference}:move')")
    assert _slot(page, reference) != first_key
    assert not page.locator("#seats-1").is_checked() and not page.locator("#seats-2").is_checked()
    assert page.locator("#date").input_value() == ""
    assert page.locator("section.confirming-step").count() == 0
    rows = db.execute("SELECT seats, window_id FROM bookings WHERE reference = %s", (reference,)).fetchall()
    db.rollback()
    assert rows == [(2, current["id"])]  # nothing has changed


def test_a_one_seat_booking_moves_whole(page: Page, base_url, db):
    windows = free_windows(base_url)
    current, target = windows[4], windows[5]
    page.set_viewport_size({"width": 1366, "height": 768})
    reference = _open_step(page, base_url, current, 1)
    assert page.locator("#seats").count() == 0  # no "How many" question for one Seat
    _choose(page, target, None)
    step = page.locator("section.confirming-step")
    labels = [_norm(t) for t in step.locator(".summary-row dt").all_inner_texts()]
    assert labels == ["Seats moved", "From", "To"]  # a full move: no "Seats left in this booking"
    a11y.tab_to(page, page.get_by_role("button", name="Move 1 seat"))
    page.keyboard.press("Enter")
    page.get_by_role("heading", level=1, name="Seats moved").wait_for()
    text = _norm(page.locator("main").inner_text())
    assert "Your booking has been changed." in text and "new booking reference" not in text
    sent = page.locator("section.email-as-sent")
    assert sent.count() == 1
    body = sent.locator(".email-body").inner_text()
    assert body.startswith("Booking changed") and f"Booking reference: {reference}" in body
    assert "Seats moved:" not in body
    rows = db.execute("SELECT seats, window_id FROM bookings WHERE reference = %s", (reference,)).fetchall()
    db.rollback()
    assert rows == [(1, target["id"])]
