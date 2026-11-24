"""FR-27 / AD-29 / AD-30 (Story 4.3) in the compose stack, over HTTPS: a Guest gives up 1 of 2 Seats for a Voucher
through the Manage page with the keyboard alone (every key through `a11y.press` / `a11y.tab_to`). The confirming step
states what will happen (Seats given up, Seats left, the Voucher value and its last valid date, no money back); the
result page shows the email with the Voucher code under "Sent by email:"; the Booking list shows 1 Seat and the
history line. A stale version reopens the step fresh with a new key; a cancelled Booking's step shows why, with no
step. Giving up the last Seat cancels the Booking: the Manage page then shows it as cancelled with no
Changes, and the Booking list lists it as cancelled by the Guest with a Voucher, outside Seats booked. axe finds no A
or AA failure on the step, the result and the cancelled page, nothing scrolls sideways at 1024, 1366 and 1920 px, and
no Voucher code reaches a container log.
"""

from __future__ import annotations

import datetime as dt
import re

from playwright.sync_api import Page

from . import a11y
from .admin import BOOKINGS, LOGIN, no_throttle, open_sign_in, type_login  # noqa: F401 (fixture)
from .guest import book_in_browser, free_windows, open_session
from .test_fr26_move import db  # noqa: F401 (fixture)

LINK = re.compile(r"(?m)^(https://\S+/manage#t=[A-Za-z0-9_-]{43})$")
CODE = re.compile(r"(?m)^Code: ([0-9A-HJKMNP-TV-Z]{4}(?:-[0-9A-HJKMNP-TV-Z]{4}){3})$")
NBSP = "\u00a0"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace(NBSP, " ")).strip()


def _long(d: dt.date) -> str:
    return f"{WEEKDAYS[d.weekday()]} {d.day} {MONTHS[d.month - 1]} {d.year}"


def _summary(page: Page) -> dict[str, str]:
    step = page.locator("section.confirming-step")
    return dict(zip([_norm(t) for t in step.locator(".summary-row dt").all_inner_texts()],
                    [_norm(t) for t in step.locator(".summary-row dd").all_inner_texts()]))


def _open_manage(page: Page, base_url: str, window: dict, seats: int) -> tuple[str, str]:
    """Pay for `seats` in `window` and open its Manage link; returns (reference, link)."""
    open_session(page, base_url)
    paid = book_in_browser(page, window, seats, "Kari Nordmann")
    reference = paid["booking"]["reference"]
    link = LINK.search(paid["emails"][0]["body"]).group(1)
    page.goto(link)
    page.wait_for_url(f"{base_url}/manage/{reference}")
    page.get_by_role("heading", name="Manage booking").wait_for()
    return reference, link


def _open_step_by_keyboard(page: Page, base_url: str, reference: str) -> None:
    link = page.get_by_role("link", name="Give up seats for a voucher")
    link.wait_for()  # the Manage page has read the Booking
    page.wait_for_function("() => document.activeElement && document.activeElement.tagName === 'H1'")
    a11y.tab_to(page, link)
    a11y.press(page, "Enter")
    page.wait_for_url(f"{base_url}/manage/{reference}/voucher")
    page.get_by_role("heading", level=1, name="Give up seats").wait_for()
    page.wait_for_function("() => document.activeElement && document.activeElement.tagName === 'H1'")


def _booking_list(browser, base_url: str, date: str):
    admin = browser.new_context(ignore_https_errors=True).new_page()
    open_sign_in(admin, base_url)
    type_login(admin, LOGIN["password"])
    admin.wait_for_url(base_url + BOOKINGS)
    admin.goto(f"{base_url}{BOOKINGS}?date={date}")
    admin.get_by_role("heading", level=1, name="Booking list").wait_for()
    return admin


def _group(admin: Page, w: dict):
    return admin.locator("section.session-group").filter(has=admin.get_by_role(
        "heading", level=2, name=f"Session {w['start'][11:16]} to {w['end'][11:16]}"))


def test_a_guest_gives_up_seats_for_a_voucher_with_the_keyboard_alone(page: Page, browser, base_url, stack):
    window = free_windows(base_url)[6]
    page.set_viewport_size({"width": 1366, "height": 768})
    reference, link = _open_manage(page, base_url, window, 2)
    today = dt.date.fromisoformat(page.evaluate("() => fetch('/api/windows').then(r => r.json()).then(b => b.today)"))
    last = dt.date(today.year + 1, today.month, 28 if (today.month, today.day) == (2, 29) else today.day)

    # the step opens with the keyboard alone, with its key slot
    _open_step_by_keyboard(page, base_url, reference)
    assert page.title() == "Give up seats – Saunalöyly"
    key = page.evaluate(f"() => sessionStorage.getItem('draft:change:{reference}:voucher')")
    assert key and re.fullmatch(r"[0-9a-f-]{36}", key)
    assert _norm(page.locator("#seats legend").inner_text()) == "How many seats do you want to give up?"
    assert page.locator("input[name=seats]").count() == 2
    assert page.locator("section.confirming-step").count() == 0
    a11y.tab_to(page, page.locator("#seats-1"))
    a11y.press(page, "Space")
    assert page.locator("#seats-1").is_checked()

    # what will happen; nothing has changed yet
    step = page.locator("section.confirming-step")
    step.get_by_role("heading", name="What will happen").wait_for()
    rows = _summary(page)
    assert rows == {"Seats given up": "1 seat", "Seats left in this booking": "1 seat", "Voucher value": "NOK 250",
                    "Valid until": _long(last)}
    assert list(rows) == ["Seats given up", "Seats left in this booking", "Voucher value", "Valid until"]
    assert [_norm(t) for t in step.locator(".move-note").all_inner_texts()] == [
        "No money is paid back. The voucher can pay for a new booking until it expires.",
        "Nothing changes until you confirm."]
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)
    page.set_viewport_size({"width": 1366, "height": 768})

    a11y.tab_to(page, page.get_by_role("button", name="Give up 1 seat"))
    page.keyboard.press("Enter")  # the button is gone once the result shows; its h1 takes focus
    page.get_by_role("heading", level=1, name="Seats given up").wait_for()
    page.wait_for_function("() => document.activeElement && document.activeElement.tagName === 'H1'")
    a11y.assert_focus_visible(page)
    assert page.title() == "Seats given up – Saunalöyly"
    text = _norm(page.locator("main").inner_text())
    assert "Your booking has been changed." in text and "Your voucher code is in the email below." in text
    sent = page.locator("section.email-as-sent")
    assert sent.count() == 1
    assert _norm(sent.locator("h2").inner_text()) == "Sent by email:"
    body = sent.locator(".email-body").inner_text()
    assert body.startswith("Booking changed") and f"Booking reference: {reference}" in body and "Seats: 1" in body
    code = CODE.search(body).group(1)
    assert "Value: NOK 250" in body and f"Valid until: {_long(last)}" in body
    assert "A voucher is never paid out in money." in body
    assert "The Manage link in your booking confirmation email still works." in body and "/manage#t=" not in body
    assert page.evaluate(f"() => sessionStorage.getItem('draft:change:{reference}:voucher')") is None
    back = page.get_by_role("link", name="Back to your booking")
    assert back.get_attribute("href") == f"/manage/{reference}"
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)

    # the Booking list: 1 Seat, Active, and the history line with the value, never the code
    admin = _booking_list(browser, base_url, window["date"])
    try:
        row = _group(admin, window).locator("tr.booking-row").filter(has_text=reference)
        row.wait_for()
        cells = [_norm(c) for c in row.locator("td").all_inner_texts()]
        assert cells[0] == reference and cells[3] == "1" and cells[4] == "NOK 250" and cells[6] == "Active"
        history = _norm(_group(admin, window).locator("tr.booking-history").inner_text())
        assert re.fullmatch(r"Gave up 1 seat on \d\d\.\d\d\.\d{4} \d\d:\d\d for a voucher of NOK 250", history), history
        assert code not in admin.locator("main").inner_text()
        a11y.check_axe(admin)
    finally:
        admin.context.close()

    # the last Seat: a one-Seat Booking has no question; giving it up cancels the Booking
    a11y.tab_to(page, back)
    a11y.press(page, "Enter")
    page.wait_for_url(f"{base_url}/manage/{reference}")
    _open_step_by_keyboard(page, base_url, reference)
    page.get_by_role("heading", name="What will happen").wait_for()
    assert page.locator("#seats").count() == 0
    assert list(_summary(page)) == ["Seats given up", "Voucher value", "Valid until"]
    a11y.tab_to(page, page.get_by_role("button", name="Give up 1 seat"))
    page.keyboard.press("Enter")
    page.get_by_role("heading", level=1, name="Seats given up").wait_for()
    text = _norm(page.locator("main").inner_text())
    assert "Your booking has been cancelled." in text
    body = page.locator("section.email-as-sent .email-body").inner_text()
    assert body.startswith("Booking cancelled") and "Seats given up: 1" in body
    second_code = CODE.search(body).group(1)
    assert second_code != code

    # the cancelled Manage page: the link still opens it; no Changes
    page.goto(link)
    page.wait_for_url(f"{base_url}/manage/{reference}")
    page.get_by_role("heading", name="Manage booking").wait_for()
    page.locator(".manage-cancelled").wait_for()
    line = _norm(page.locator(".manage-cancelled").inner_text())
    assert re.fullmatch(r"This booking was cancelled on \w+ \d{1,2} \w+ \d{4} at \d\d:\d\d\. You gave up all seats "
                        r"for a voucher, which was sent by email\.", line), line
    summary = dict(zip([_norm(t) for t in page.locator(".summary-row dt").all_inner_texts()],
                       [_norm(t) for t in page.locator(".summary-row dd").all_inner_texts()]))
    assert list(summary) == ["Date", "Session", "Seats given up"] and summary["Seats given up"] == "1 seat"
    assert page.get_by_role("link", name="Move seats").count() == 0
    assert page.get_by_role("link", name="Give up seats for a voucher").count() == 0
    assert page.locator(".manage-until").count() == 0
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)

    # the Booking list: cancelled by the Guest with a Voucher, outside Seats booked
    admin = _booking_list(browser, base_url, window["date"])
    try:
        row = _group(admin, window).locator("tr.booking-row").filter(has_text=reference)
        row.wait_for()
        cells = [_norm(c) for c in row.locator("td").all_inner_texts()]
        assert re.fullmatch(r"Cancelled \d\d\.\d\d\.\d{4} \d\d:\d\d · Guest · Voucher", cells[6]), cells[6]
        lines = [_norm(t) for t in _group(admin, window).locator("tr.booking-history").all_inner_texts()]
        assert len(lines) == 2 and all(x.startswith("Gave up 1 seat on ") for x in lines)
        assert _norm(_group(admin, window).locator(".session-group-figures").inner_text()) == \
            "Seat capacity 44 · Seats booked 0 · Seats left 44"
        a11y.check_axe(admin)
        a11y.no_horizontal_scroll(admin)
    finally:
        admin.context.close()

    # no Voucher code in any container log
    logs = stack.compose("logs", "--no-color").stdout
    assert "POST /api/manage/" in logs
    for c in (code, second_code):
        assert c not in logs and c.replace("-", "") not in logs, f"{c!r} is in the compose logs"


def _slot(page: Page, reference: str):
    return page.evaluate(f"() => sessionStorage.getItem('draft:change:{reference}:voucher')")


def test_refusals_renew_the_step_and_a_cancelled_booking_shows_why(page: Page, base_url, db):
    window = free_windows(base_url)[7]
    page.set_viewport_size({"width": 1366, "height": 768})
    reference, _link = _open_manage(page, base_url, window, 2)
    _open_step_by_keyboard(page, base_url, reference)
    first_key = _slot(page, reference)
    assert first_key

    # booking_changed: the Booking's version moves on in the store after the step read it
    a11y.tab_to(page, page.locator("#seats-1"))
    a11y.press(page, "Space")
    page.get_by_role("heading", name="What will happen").wait_for()
    db.execute("UPDATE bookings SET version = version + 1 WHERE reference = %s", (reference,))
    db.commit()
    a11y.tab_to(page, page.get_by_role("button", name="Give up 1 seat"))
    a11y.press(page, "Enter")
    changed = page.locator(".notice", has_text="changed in the meantime")
    changed.wait_for()
    assert _norm(changed.inner_text()) == "This booking was changed in the meantime. Check it and choose again."
    # the step opens fresh with a new key and no Seat chosen
    page.wait_for_function(
        f"(old) => {{ const k = sessionStorage.getItem('draft:change:{reference}:voucher'); return !!k && k !== old; }}",
        arg=first_key)
    assert not page.locator("#seats-1").is_checked() and not page.locator("#seats-2").is_checked()
    assert page.locator("section.confirming-step").count() == 0
    got = db.execute("SELECT seats, total_ore, status, version FROM bookings WHERE reference = %s",
                     (reference,)).fetchall()
    vouchers = db.execute("SELECT count(*) FROM vouchers v JOIN bookings b ON b.id = v.booking_id "
                          "WHERE b.reference = %s", (reference,)).fetchone()[0]
    db.rollback()
    assert got == [(2, 50000, "active", 1)] and vouchers == 0  # nothing has changed

    # cancelled in the store (all Seats given up elsewhere): a reload shows why, and no step
    db.execute("UPDATE bookings SET status = 'cancelled', cancelled_at = app_now(), cancel_cause = 'guest', "
               "cancel_remedy = 'voucher', version = version + 1 WHERE reference = %s", (reference,))
    db.commit()
    page.goto(f"{base_url}/manage/{reference}/voucher")
    page.get_by_role("heading", level=1, name="Give up seats").wait_for()
    notice = page.locator(".notice", has_text="This booking was cancelled on")
    notice.wait_for()
    assert re.fullmatch(r"This booking was cancelled on \w+ \d{1,2} \w+ \d{4} at \d\d:\d\d\. You gave up all seats "
                        r"for a voucher, which was sent by email\.", _norm(notice.inner_text()))
    assert page.locator("section.confirming-step").count() == 0
    assert page.locator("#seats").count() == 0
    a11y.check_axe(page)
