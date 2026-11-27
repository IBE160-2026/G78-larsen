"""FR-33 / AD-29 / AD-31 (Story 5.3, part 1) in the compose stack, over HTTPS: a Guest cancels a Private sauna through
the Manage page with the keyboard alone (every key through `a11y.press` / `a11y.tab_to`).

The Manage page of a Whole-sauna booking shows until when it can be changed and the link "Cancel booking". The
step asks "What do you want back?" (a radio group in a fieldset with a legend: "A refund" or "A voucher", each with
its hint); once a remedy is chosen, "What will happen" states the Sauna, the session and the refund (card part, and a
new Voucher for a Voucher part) or the Voucher (value, last valid date, no money back), and nothing changes until
"Cancel booking". The result page shows "Booking cancelled" and the email as stored under "Sent by email:"; the
cancelled Manage page says when it was cancelled and the remedy chosen; the Booking list shows it cancelled by the
Guest with its remedy and the history line, outside Seats booked. A stale version reopens the step fresh with a new
key. axe finds no A or AA failure on the step, the result and the cancelled page, nothing scrolls sideways, the pages
carry `X-Robots-Tag: noindex` and `Referrer-Policy: no-referrer`, and no Voucher code reaches a container log.
Wording: Lisa, 2026-11-26 (EXPERIENCE.md "Cancel private sauna wording"). Every Booking made here ends cancelled,
so the dates stay free (`free_windows`) for the other e2e tests.
"""

from __future__ import annotations

import datetime as dt
import re
import uuid

import httpx
import psycopg
from playwright.sync_api import Page

from . import a11y, trust
from .admin import db_url, no_throttle  # noqa: F401 (fixture)
from .guest import free_windows, open_session
from .test_fr26_move import db  # noqa: F401 (fixture)
from .test_fr27_voucher import CODE, _booking_list, _group, _long, _norm, _open_manage as _open_seat_manage, _summary
from .test_fr30_private_sauna import listing_of

LINK = re.compile(r"(?m)^(https://\S+/manage#t=[A-Za-z0-9_-]{43})$")
NOTHING_YET = "Nothing changes until you confirm."
NO_MONEY = "No money is paid back. The voucher can pay for a new booking until it expires."
SIMULATED = "Simulated payment: no money moves"
STILL_WORKS = "The Manage link in your booking confirmation email still works."
VOUCHER_ROWS = ("() => [...document.querySelectorAll('section.confirming-step dt')]"
                ".some(d => d.textContent.trim() === 'Voucher value')")


def _pair(base_url: str, window: dict, name: str) -> dict:
    """The Sauna `name` as the Private sauna listing offers it for `window`."""
    sauna = next(s for s in listing_of(base_url, window["date"])["saunas"] if s["name"] == name)
    assert any(w["id"] == window["id"] for w in sauna["windows"]), (name, window)
    return sauna


def _book_whole(page: Page, window: dict, sauna: dict, **fields) -> dict:
    """Pay for a Private sauna through the API from the page, with its session cookie (as Review does)."""
    status, body = page.evaluate(
        """async ({body, key}) => {
             const r = await fetch('/api/bookings', {method: 'POST', credentials: 'same-origin',
               headers: {'Content-Type': 'application/json', 'Idempotency-Key': key}, body: JSON.stringify(body)});
             return [r.status, await r.json()];
           }""",
        {"body": {"kind": "whole", "window_id": window["id"], "sauna_id": sauna["id"], "name": "Olav Berg",
                  "email": "olav@example.com", **fields}, "key": str(uuid.uuid4())})
    assert status == 201, body
    return body


def _voucher(page: Page, base_url: str, window: dict) -> str:
    """A Voucher worth NOK 250: pay for 1 Seat, open its Manage link and give it up from the page, so the Seat booking
    is cancelled and the date stays free for the other e2e tests. Returns the code from the Change email."""
    reference, _ = _open_seat_manage(page, base_url, window, 1)
    status, body = page.evaluate(
        """async ({ref, key}) => {
             const r = await fetch(`/api/manage/${ref}/seats/voucher`, {method: 'POST', credentials: 'same-origin',
               headers: {'Content-Type': 'application/json', 'Idempotency-Key': key},
               body: JSON.stringify({seats: 1, version: 0})});
             return [r.status, await r.json()];
           }""",
        {"ref": reference, "key": str(uuid.uuid4())})
    assert status == 200, body
    return CODE.search(body["emails"][0]["body"]).group(1)


def _open_manage(page: Page, base_url: str, paid: dict) -> tuple[str, str]:
    reference = paid["booking"]["reference"]
    link = LINK.search(paid["emails"][0]["body"]).group(1)
    page.goto(link)
    page.wait_for_url(f"{base_url}/manage/{reference}")
    page.get_by_role("heading", name="Manage booking").wait_for()
    return reference, link


def _open_step_by_keyboard(page: Page, base_url: str, reference: str) -> None:
    link = page.get_by_role("link", name="Cancel booking")
    link.wait_for()  # the Manage page has read the Booking
    page.wait_for_function("() => document.activeElement && document.activeElement.tagName === 'H1'")
    a11y.tab_to(page, link)
    a11y.press(page, "Enter")
    page.wait_for_url(f"{base_url}/manage/{reference}/cancel")
    page.get_by_role("heading", level=1, name="Cancel booking").wait_for()
    page.wait_for_function("() => document.activeElement && document.activeElement.tagName === 'H1'")


def _slot(page: Page, reference: str):
    return page.evaluate(f"() => sessionStorage.getItem('draft:change:{reference}:cancel')")


def _notes(page: Page) -> list[str]:
    return [_norm(t) for t in page.locator("section.confirming-step .move-note").all_inner_texts()]


def _state(db, reference: str) -> tuple:
    row = db.execute("SELECT b.status, b.version, (SELECT count(*) FROM whole_bookings wb WHERE wb.booking_id = b.id), "
                     "(SELECT count(*) FROM payments p WHERE p.booking_id = b.id AND p.direction = 'refund'), "
                     "(SELECT count(*) FROM vouchers v WHERE v.booking_id = b.id) "
                     "FROM bookings b WHERE b.reference = %s", (reference,)).fetchone()
    db.rollback()
    return row


def _session(window: dict) -> str:
    return f"{_long(dt.date.fromisoformat(window['date']))}, {window['start'][11:16]}–{window['end'][11:16]}"


def test_a_guest_cancels_a_private_sauna_for_a_refund_with_the_keyboard_alone(page: Page, browser, base_url, db,
                                                                              stack):
    window = free_windows(base_url)[2]
    kajo = _pair(base_url, window, "Kajo")
    page.set_viewport_size({"width": 1366, "height": 768})
    open_session(page, base_url)
    reference, link = _open_manage(page, base_url, _book_whole(page, window, kajo))
    today = dt.date.fromisoformat(page.evaluate("() => fetch('/api/windows').then(r => r.json()).then(b => b.today)"))
    last = dt.date(today.year + 1, today.month, 28 if (today.month, today.day) == (2, 29) else today.day)

    # the Manage page: until when, and the one Change of this spec
    until = page.locator(".manage-until")
    until.wait_for()
    assert re.fullmatch(r"You can change this booking until \w+ \d{1,2} \w+ \d{4} at \d\d:\d\d\.",
                        _norm(until.inner_text()))
    assert page.get_by_role("link", name="Move seats").count() == 0
    assert page.get_by_role("link", name="Give up seats for a voucher").count() == 0
    a11y.check_axe(page)

    _open_step_by_keyboard(page, base_url, reference)
    assert page.title() == "Cancel booking – Saunalöyly"
    key = _slot(page, reference)
    assert key and re.fullmatch(r"[0-9a-f-]{36}", key)
    assert _norm(page.locator("#remedy legend").inner_text()) == "What do you want back?"
    options = [_norm(t) for t in page.locator("#remedy label").all_inner_texts()]
    assert options == ["A refund Paid back the way you paid.",
                       "A voucher A voucher for the full NOK 3150, valid for one year."]
    assert page.locator("input[name=remedy]:checked").count() == 0
    assert page.locator("section.confirming-step").count() == 0
    a11y.tab_to(page, page.locator("#remedy-refund"))
    a11y.press(page, "Space")
    assert page.locator("#remedy-refund").is_checked()

    # what will happen, for a refund; nothing has changed yet
    step = page.locator("section.confirming-step")
    step.get_by_role("heading", name="What will happen").wait_for()
    rows = _summary(page)
    assert rows == {"Sauna": "Kajo", "Session": _session(window), "Refund to card": "NOK 3150"}
    assert list(rows) == ["Sauna", "Session", "Refund to card"]
    assert _notes(page) == [NOTHING_YET]
    # the voucher, by arrow key in the one radio group
    a11y.press(page, "ArrowDown")
    assert page.locator("#remedy-voucher").is_checked()
    page.wait_for_function(VOUCHER_ROWS)
    rows = _summary(page)
    assert rows == {"Sauna": "Kajo", "Session": _session(window), "Voucher value": "NOK 3150",
                    "Valid until": _long(last)}
    assert _notes(page) == [NO_MONEY, NOTHING_YET]
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)
    page.set_viewport_size({"width": 1366, "height": 768})
    a11y.press(page, "ArrowUp")
    assert page.locator("#remedy-refund").is_checked()
    assert list(_summary(page)) == ["Sauna", "Session", "Refund to card"]
    assert _state(db, reference) == ("active", 0, 1, 0, 0)  # nothing changes until the Guest confirms

    a11y.tab_to(page, page.get_by_role("button", name="Cancel booking"))
    page.keyboard.press("Enter")  # the button is gone once the result shows; its h1 takes focus
    page.get_by_role("heading", level=1, name="Booking cancelled").wait_for()
    page.wait_for_function("() => document.activeElement && document.activeElement.tagName === 'H1'")
    a11y.assert_focus_visible(page)
    assert page.title() == "Booking cancelled – Saunalöyly"
    text = _norm(page.locator("main").inner_text())
    assert "Your booking has been cancelled." in text and "Your refund is in the email below." in text
    sent = page.locator("section.email-as-sent")
    assert sent.count() == 1
    assert _norm(sent.locator("h2").inner_text()) == "Sent by email:"
    body = sent.locator(".email-body").inner_text()
    assert body.startswith("Booking cancelled") and f"Booking reference: {reference}" in body
    assert "Sauna: Kajo" in body and "Refunded to card: NOK 3150" in body and SIMULATED in body
    assert STILL_WORKS in body and "/manage#t=" not in body and "Code:" not in body
    assert _slot(page, reference) is None
    assert _state(db, reference) == ("cancelled", 1, 0, 1, 0)
    back = page.get_by_role("link", name="Back to your booking")
    assert back.get_attribute("href") == f"/manage/{reference}"
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)
    page.set_viewport_size({"width": 1366, "height": 768})

    # the cancelled Manage page: when, and the remedy; no Change
    a11y.tab_to(page, back)
    a11y.press(page, "Enter")
    page.wait_for_url(f"{base_url}/manage/{reference}")
    page.locator(".manage-cancelled").wait_for()
    line = _norm(page.locator(".manage-cancelled").inner_text())
    assert re.fullmatch(r"This booking was cancelled on \w+ \d{1,2} \w+ \d{4} at \d\d:\d\d\. You chose a refund, "
                        r"which was sent by email\.", line), line
    assert page.get_by_role("link", name="Cancel booking").count() == 0
    assert page.locator(".manage-until").count() == 0
    a11y.check_axe(page)
    # a reload of the step shows why there is no step
    page.goto(f"{base_url}/manage/{reference}/cancel")
    page.locator(".notice", has_text="This booking was cancelled on").wait_for()
    assert page.locator("section.confirming-step").count() == 0 and page.locator("#remedy").count() == 0

    # the Booking list: cancelled by the Guest for a refund, outside Seats booked
    admin = _booking_list(browser, base_url, window["date"])
    try:
        row = _group(admin, window).locator("tr.booking-row").filter(has_text=reference)
        row.wait_for()
        cells = [_norm(c) for c in row.locator("td").all_inner_texts()]
        assert cells[3] == "Kajo"
        assert re.fullmatch(r"Cancelled \d\d\.\d\d\.\d{4} \d\d:\d\d · Guest · Refund", cells[6]), cells[6]
        history = _norm(_group(admin, window).locator("tr.booking-history").inner_text())
        assert re.fullmatch(r"Cancelled on \d\d\.\d\d\.\d{4} \d\d:\d\d for a refund", history), history
        assert _norm(_group(admin, window).locator(".session-group-figures").inner_text()) == \
            "Seat capacity 44 · Seats booked 0 · Seats left 44"
        a11y.check_axe(admin)
    finally:
        admin.context.close()

    # Caddy marks the step noindex and no referrer
    with httpx.Client(base_url=base_url, verify=trust.context(), timeout=30) as c:
        r = c.get(f"/manage/{reference}/cancel")
    assert r.status_code == 200
    assert r.headers.get("x-robots-tag") == "noindex" and r.headers.get("referrer-policy") == "no-referrer"
    assert link not in stack.compose("logs", "--no-color").stdout


def test_a_partly_voucher_paid_private_sauna_is_cancelled_for_a_voucher(page: Page, browser, base_url, db, stack):
    windows = free_windows(base_url)
    page.set_viewport_size({"width": 1366, "height": 768})
    code = _voucher(page, base_url, windows[4])  # NOK 250, from a give-up (opens a session)
    rauha = _pair(base_url, windows[5], "Rauha")
    paid = _book_whole(page, windows[5], rauha, voucher_code=code, voucher_part_ore=25000)
    reference, _link = _open_manage(page, base_url, paid)
    today = dt.date.fromisoformat(page.evaluate("() => fetch('/api/windows').then(r => r.json()).then(b => b.today)"))
    last = dt.date(today.year + 1, today.month, 28 if (today.month, today.day) == (2, 29) else today.day)
    _open_step_by_keyboard(page, base_url, reference)

    # a refund would split: the card part, and a new Voucher for the Voucher part with the spent one's date
    a11y.tab_to(page, page.locator("#remedy-refund"))
    a11y.press(page, "Space")
    page.locator("section.confirming-step").get_by_role("heading", name="What will happen").wait_for()
    rows = _summary(page)
    assert list(rows) == ["Sauna", "Session", "Refund to card", "New voucher", "Valid until"]
    assert (rows["Sauna"], rows["Refund to card"], rows["New voucher"], rows["Valid until"]) == (
        "Rauha", "NOK 1600", "NOK 250", _long(last))
    a11y.check_axe(page)

    # the voucher: the full total, one year
    a11y.press(page, "ArrowDown")
    assert page.locator("#remedy-voucher").is_checked()
    page.wait_for_function(VOUCHER_ROWS)
    rows = _summary(page)
    assert rows == {"Sauna": "Rauha", "Session": _session(windows[5]), "Voucher value": "NOK 1850",
                    "Valid until": _long(last)}
    assert _state(db, reference) == ("active", 0, 1, 0, 0)
    a11y.tab_to(page, page.get_by_role("button", name="Cancel booking"))
    page.keyboard.press("Enter")
    page.get_by_role("heading", level=1, name="Booking cancelled").wait_for()
    text = _norm(page.locator("main").inner_text())
    assert "Your booking has been cancelled." in text and "Your voucher code is in the email below." in text
    body = page.locator("section.email-as-sent .email-body").inner_text()
    new_code = CODE.search(body).group(1)
    assert new_code != code and "Value: NOK 1850" in body and f"Valid until: {_long(last)}" in body
    assert "Refunded to card" not in body and SIMULATED not in body
    assert _state(db, reference) == ("cancelled", 1, 0, 1, 1)
    a11y.check_axe(page)

    page.goto(f"{base_url}/manage/{reference}")
    page.locator(".manage-cancelled").wait_for()
    assert _norm(page.locator(".manage-cancelled").inner_text()).endswith(
        "You chose a voucher, which was sent by email.")

    admin = _booking_list(browser, base_url, windows[5]["date"])
    try:
        row = _group(admin, windows[5]).locator("tr.booking-row").filter(has_text=reference)
        row.wait_for()
        cells = [_norm(c) for c in row.locator("td").all_inner_texts()]
        assert re.fullmatch(r"Cancelled \d\d\.\d\d\.\d{4} \d\d:\d\d · Guest · Voucher", cells[6]), cells[6]
        history = _norm(_group(admin, windows[5]).locator("tr.booking-history").inner_text())
        assert re.fullmatch(r"Cancelled on \d\d\.\d\d\.\d{4} \d\d:\d\d for a voucher of NOK 1850", history), history
        assert new_code not in admin.locator("main").inner_text()
    finally:
        admin.context.close()

    logs = stack.compose("logs", "--no-color").stdout
    assert "POST /api/manage/" in logs
    assert new_code not in logs and new_code.replace("-", "") not in logs


def test_a_stale_version_renews_the_step_with_a_new_key(page: Page, base_url, db):
    window = free_windows(base_url)[6]
    loyly = _pair(base_url, window, "Löyly")
    page.set_viewport_size({"width": 1366, "height": 768})
    open_session(page, base_url)
    reference, _link = _open_manage(page, base_url, _book_whole(page, window, loyly))
    _open_step_by_keyboard(page, base_url, reference)
    first_key = _slot(page, reference)
    assert first_key
    a11y.tab_to(page, page.locator("#remedy-refund"))
    a11y.press(page, "Space")
    page.get_by_role("heading", name="What will happen").wait_for()
    db.execute("UPDATE bookings SET version = version + 1 WHERE reference = %s", (reference,))
    db.commit()
    a11y.tab_to(page, page.get_by_role("button", name="Cancel booking"))
    a11y.press(page, "Enter")
    changed = page.locator(".notice", has_text="changed in the meantime")
    changed.wait_for()
    assert _norm(changed.inner_text()) == "This booking was changed in the meantime. Check it and choose again."
    page.wait_for_function(
        f"(old) => {{ const k = sessionStorage.getItem('draft:change:{reference}:cancel'); return !!k && k !== old; }}",
        arg=first_key)
    assert page.locator("input[name=remedy]:checked").count() == 0
    assert page.locator("section.confirming-step").count() == 0
    assert _state(db, reference) == ("active", 1, 1, 0, 0)  # nothing has changed
    a11y.check_axe(page)
    # the fresh step cancels with the new version
    a11y.tab_to(page, page.locator("#remedy-refund"))
    a11y.press(page, "Space")
    a11y.tab_to(page, page.get_by_role("button", name="Cancel booking"))
    page.keyboard.press("Enter")
    page.get_by_role("heading", level=1, name="Booking cancelled").wait_for()
    assert _state(db, reference) == ("cancelled", 2, 0, 1, 0)


CUTOFF_72 = re.compile(r"This booking can no longer be changed\. Changes are possible until 72 hours before the "
                       r"session starts, and that was \w+day \d{1,2} \w+ \d{4} at \d\d:\d\d\.")


def test_after_the_72_hour_cutoff_the_pages_give_the_reason(page: Page, base_url, stack):
    """The clock moves (`clock.off`) to one minute past the Private sauna's Cutoff (`start - 72 h`): the Manage page and
    the cancel step give the 72-hour reason and offer no cancel. The clock is put back and the Booking cancelled, so
    the date stays free."""
    window = free_windows(base_url)[1]
    lumo = _pair(base_url, window, "Lumo")
    page.set_viewport_size({"width": 1366, "height": 768})
    open_session(page, base_url)
    paid = _book_whole(page, window, lumo)
    reference = paid["booking"]["reference"]
    link = LINK.search(paid["emails"][0]["body"]).group(1)
    with psycopg.connect(db_url(stack)) as c:
        start = c.execute("SELECT lower(w.during) FROM bookings b JOIN windows w ON w.id = b.window_id "
                          "WHERE b.reference = %s", (reference,)).fetchone()[0]
        shift = c.execute("SELECT %s::timestamptz - interval '72 hours' + interval '1 minute' - app_now()",
                          (start,)).fetchone()[0]
        c.execute("UPDATE clock SET off = off + %s", (shift,))
        c.execute("UPDATE sessions SET expires_at = expires_at + %s WHERE expires_at <> 'infinity'", (shift,))
        c.commit()
        try:
            _open_manage(page, base_url, paid)  # the link again: the grant was idle across the shift
            notice = page.locator(".notice")
            notice.wait_for()
            assert CUTOFF_72.fullmatch(_norm(notice.inner_text())), notice.inner_text()
            assert page.locator(".manage-until").count() == 0
            assert page.get_by_role("link", name="Cancel booking").count() == 0
            a11y.check_axe(page)
            page.goto(f"{base_url}/manage/{reference}/cancel")
            page.get_by_role("heading", level=1, name="Cancel booking").wait_for()
            notice = page.locator(".notice", has_text="can no longer be changed")
            notice.wait_for()
            assert CUTOFF_72.fullmatch(_norm(notice.inner_text())), notice.inner_text()
            assert page.locator("#remedy").count() == 0 and page.locator("section.confirming-step").count() == 0
            a11y.check_axe(page)
        finally:
            c.rollback()
            c.execute("UPDATE clock SET off = off - %s", (shift,))
            c.execute("UPDATE sessions SET expires_at = expires_at - %s WHERE expires_at <> 'infinity'", (shift,))
            c.commit()
            # cancelled, so the date stays free for the other e2e tests
            page.goto(link)
            page.wait_for_url(f"{base_url}/manage/{reference}")
            status, body = page.evaluate(
                """async ({ref, key}) => {
                     const r = await fetch(`/api/manage/${ref}/whole/cancel`, {method: 'POST',
                       credentials: 'same-origin',
                       headers: {'Content-Type': 'application/json', 'Idempotency-Key': key},
                       body: JSON.stringify({remedy: 'refund', version: 0})});
                     return [r.status, await r.json()];
                   }""",
                {"ref": reference, "key": str(uuid.uuid4())})
            assert status == 200, body
