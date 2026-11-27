"""FR-33 / AD-24 / AD-29 (Story 5.3, part 2) in the compose stack, over HTTPS: a Guest moves a Private sauna through the
Manage page with the keyboard alone (every key through `a11y.press` / `a11y.tab_to`).

The Manage page of a Whole-sauna booking offers "Move private sauna" beside "Cancel private sauna". The step asks
"1. Choose a date" and "2. Choose a sauna and a session": the Booking's own Sauna comes first as "Your sauna", its own
pair a disabled button "Your current session"; a Sauna at another price (all four seeded prices differ) shows its
price and why it cannot be chosen, with no session buttons. Once a pair is chosen, "What will happen" states From, To
and the unchanged price, and nothing changes until "Move booking". The result page shows "Booking moved" and the email
as stored under "Sent by email:"; the Booking list shows the history line with both Saunas. A refusal
`price_differs` gives the same reason on the page. axe finds no A or AA failure, nothing scrolls sideways, and the
pages carry `X-Robots-Tag: noindex` and `Referrer-Policy: no-referrer`. Wording: Lisa, 2026-11-26 (EXPERIENCE.md
"Move private sauna wording"). Every Booking made here is deleted with its rows afterwards (`made`), so the dates stay
free (`free_windows`) and no other e2e test meets a leftover history line in the Booking list.
"""

from __future__ import annotations

import datetime as dt
import re

import httpx
import psycopg
import pytest
from playwright.sync_api import Page

from . import a11y, trust
from .admin import db_url, no_throttle  # noqa: F401 (fixture)
from .guest import free_windows, open_session
from .test_fr26_move import _dotted, db  # noqa: F401 (fixture)
from .test_fr27_voucher import _booking_list, _group, _long, _norm, _summary
from .test_fr33_whole_cancel import CUTOFF_72, NOTHING_YET, STILL_WORKS, _book_whole, _open_manage, _pair

OTHER_PRICE = "This sauna has another price than you paid. To book it, cancel this booking and book again."
SESSION = r"\d\d\.\d\d\.\d{4} \d\d:\d\d–\d\d:\d\d"


_REMOVE = (
    "DELETE FROM idempotency_keys WHERE booking_id = ANY(%(b)s) "
    "OR change_id IN (SELECT id FROM booking_changes WHERE booking_id = ANY(%(b)s))",
    "DELETE FROM outbox_emails WHERE booking_id = ANY(%(b)s) "
    "OR change_id IN (SELECT id FROM booking_changes WHERE booking_id = ANY(%(b)s))",
    "DELETE FROM payments WHERE booking_id = ANY(%(b)s)",
    "DELETE FROM booking_changes WHERE booking_id = ANY(%(b)s)",
    "DELETE FROM vouchers WHERE booking_id = ANY(%(b)s)",
    "DELETE FROM access_tokens WHERE booking_id = ANY(%(b)s)",  # its grants cascade
    "DELETE FROM whole_bookings WHERE booking_id = ANY(%(b)s)",
    "DELETE FROM bookings WHERE id = ANY(%(b)s)",
)


@pytest.fixture
def made(db):
    """References of the Bookings a test made; afterwards they are deleted with every row that names them (a
    cancelled Booking would keep its history line in the Booking list, an active one would take the date)."""
    refs: list[str] = []
    yield refs
    db.rollback()
    ids = [r[0] for r in db.execute("SELECT id FROM bookings WHERE reference = ANY(%s)", (refs,)).fetchall()]
    for sql in _REMOVE:
        db.execute(sql, {"b": ids})
    db.commit()


def _slot(page: Page, reference: str):
    return page.evaluate(f"() => sessionStorage.getItem('draft:change:{reference}:move')")


def _state(db, reference: str) -> tuple:
    row = db.execute("SELECT b.status, b.version, b.window_id, b.sauna_id, "
                     "(SELECT (wb.window_id, wb.sauna_id)::text FROM whole_bookings wb WHERE wb.booking_id = b.id) "
                     "FROM bookings b WHERE b.reference = %s", (reference,)).fetchone()
    db.rollback()
    return row


def _when(sauna: str, w: dict) -> str:
    return f"{sauna}, {_long(dt.date.fromisoformat(w['date']))}, {w['start'][11:16]}–{w['end'][11:16]}"


def _open_step_by_keyboard(page: Page, base_url: str, reference: str) -> None:
    link = page.get_by_role("link", name="Move private sauna")
    link.wait_for()  # the Manage page has read the Booking
    page.wait_for_function("() => document.activeElement && document.activeElement.tagName === 'H1'")
    a11y.tab_to(page, link)
    a11y.press(page, "Enter")
    page.wait_for_url(f"{base_url}/manage/{reference}/move-sauna")
    page.get_by_role("heading", level=1, name="Move private sauna").wait_for()
    page.wait_for_function("() => document.activeElement && document.activeElement.tagName === 'H1'")


def _choose(page: Page, date: str, sauna_id: int, window_id: int) -> None:
    """With the keyboard alone: the date (typed), then the pair in the one radio group."""
    a11y.tab_to(page, page.locator("#date"))
    a11y.press(page, "Control+A")
    page.keyboard.type(_dotted(date))
    a11y.press(page, "Enter")
    target = page.locator(f"#pair-{sauna_id}-{window_id}")
    target.wait_for()
    a11y.tab_to(page, page.locator("input[name=pair]:not([disabled])").first)
    for _ in range(40):
        if target.is_checked():
            break
        a11y.press(page, "ArrowRight")
    assert target.is_checked()
    page.get_by_role("heading", name="What will happen").wait_for()


def test_a_guest_moves_a_private_sauna_with_the_keyboard_alone(page: Page, browser, base_url, db, stack, made):
    windows = free_windows(base_url)
    current, target = windows[3], windows[7]
    kajo = _pair(base_url, current, "Kajo")
    page.set_viewport_size({"width": 1366, "height": 768})
    open_session(page, base_url)
    reference, link = _open_manage(page, base_url, _book_whole(page, current, kajo))
    made.append(reference)
    before = _state(db, reference)
    assert before[:4] == ("active", 0, current["id"], kajo["id"])
    # the Manage page offers both Changes
    assert page.get_by_role("link", name="Cancel private sauna").count() == 1
    assert page.get_by_role("link", name="Move private sauna").count() == 1
    a11y.check_axe(page)

    _open_step_by_keyboard(page, base_url, reference)
    assert page.title() == "Move private sauna – Saunalöyly"
    key = _slot(page, reference)
    assert key and re.fullmatch(r"[0-9a-f-]{36}", key)
    assert "1. Choose a date" in _norm(page.locator("main").inner_text())
    _choose(page, current["date"], kajo["id"], target["id"])

    # the cards: the Booking's own Sauna first, its pair disabled; the others at another price, no buttons
    assert _norm(page.locator("#saunas > legend").inner_text()) == "2. Choose a sauna and a session"
    cards = page.locator("#saunas .private-card")
    first = cards.first
    assert _norm(first.locator(".private-card-label").inner_text()) == "Your sauna"
    assert _norm(first.locator(".private-card-name").inner_text()).startswith("Kajo")
    own = page.locator(f"#pair-{kajo['id']}-{current['id']}")
    assert own.is_disabled()
    assert "Your current session" in _norm(first.locator("label.current").inner_text())
    for i in range(1, cards.count()):
        card = cards.nth(i)
        assert _norm(card.locator(".private-card-other").inner_text()) == OTHER_PRICE
        assert card.locator("input[name=pair]").count() == 0
        assert re.fullmatch(r"NOK \d+", _norm(card.locator(".private-card-price").inner_text()))
    assert cards.count() == 4

    # what will happen; nothing has changed yet
    rows = _summary(page)
    assert rows == {"From": _when("Kajo", current), "To": _when("Kajo", target), "Price": "NOK 3150 (unchanged)"}
    assert list(rows) == ["From", "To", "Price"]
    notes = [_norm(t) for t in page.locator("section.confirming-step .move-note").all_inner_texts()]
    assert notes == [NOTHING_YET]
    assert _state(db, reference) == before
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)
    page.set_viewport_size({"width": 1366, "height": 768})

    a11y.tab_to(page, page.get_by_role("button", name="Move booking"))
    page.keyboard.press("Enter")  # the button is gone once the result shows; its h1 takes focus
    page.get_by_role("heading", level=1, name="Booking moved").wait_for()
    page.wait_for_function("() => document.activeElement && document.activeElement.tagName === 'H1'")
    a11y.assert_focus_visible(page)
    assert page.title() == "Booking moved – Saunalöyly"
    assert "Your booking has been changed." in _norm(page.locator("main").inner_text())
    sent = page.locator("section.email-as-sent")
    assert sent.count() == 1
    assert _norm(sent.locator("h2").inner_text()) == "Sent by email:"
    body = sent.locator(".email-body").inner_text()
    assert body.startswith("Booking changed") and f"Booking reference: {reference}" in body
    assert f"Session: {target['start'][11:16]}–{target['end'][11:16]}" in body
    assert "Sauna: Kajo" in body and "Total: NOK 3150" in body and STILL_WORKS in body
    assert "/manage#t=" not in body
    assert _slot(page, reference) is None
    assert _state(db, reference) == ("active", 1, target["id"], kajo["id"], f"({target['id']},{kajo['id']})")
    back = page.get_by_role("link", name="Back to your booking")
    assert back.get_attribute("href") == f"/manage/{reference}"
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)
    page.set_viewport_size({"width": 1366, "height": 768})

    # the Booking list: the Booking in its new session, the history line with both Saunas
    admin = _booking_list(browser, base_url, target["date"])
    try:
        group = _group(admin, target)
        group.locator("tr.booking-row").filter(has_text=reference).wait_for()
        history = _norm(group.locator("tr.booking-history").inner_text())
        assert re.fullmatch(rf"Moved on \d\d\.\d\d\.\d{{4}} \d\d:\d\d from Kajo {SESSION} to Kajo {SESSION}",
                            history), history
        assert f"{target['start'][11:16]}–{target['end'][11:16]}" in history.split(" to Kajo ")[1]
        assert _group(admin, current).locator("tr.booking-row").filter(has_text=reference).count() == 0
        a11y.check_axe(admin)
    finally:
        admin.context.close()

    # Caddy marks the step and the move list noindex and no referrer
    with httpx.Client(base_url=base_url, verify=trust.context(), timeout=30) as c:
        for path in (f"/manage/{reference}/move-sauna",
                     f"/api/manage/{reference}/whole/move-list?date={current['date']}"):
            r = c.get(path)
            assert r.headers.get("x-robots-tag") == "noindex", path
            assert r.headers.get("referrer-policy") == "no-referrer", path
    assert link not in stack.compose("logs", "--no-color").stdout



def test_a_refusal_price_differs_gives_the_reason_and_changes_nothing(page: Page, base_url, db, made):
    """Löyly is set to Kajo's price so the step offers it; its price changes back before the Guest confirms, so the
    API refuses `price_differs` and the step says why. The seeded price is restored."""
    windows = free_windows(base_url)
    current, target = windows[2], windows[5]
    kajo = _pair(base_url, current, "Kajo")
    loyly = _pair(base_url, target, "Löyly")
    page.set_viewport_size({"width": 1366, "height": 768})
    open_session(page, base_url)
    reference, _link = _open_manage(page, base_url, _book_whole(page, current, kajo))
    made.append(reference)
    price = loyly["whole_price_ore"]
    try:
        db.execute("UPDATE saunas SET whole_price_ore = %s WHERE id = %s", (kajo["whole_price_ore"], loyly["id"]))
        db.commit()
        _open_step_by_keyboard(page, base_url, reference)
        _choose(page, current["date"], loyly["id"], target["id"])
        assert _summary(page)["To"] == _when("Löyly", target)
        db.execute("UPDATE saunas SET whole_price_ore = %s WHERE id = %s", (price, loyly["id"]))
        db.commit()
        before = _state(db, reference)
        a11y.tab_to(page, page.get_by_role("button", name="Move booking"))
        a11y.press(page, "Enter")
        notice = page.locator(".move-notice .notice", has_text="another price")
        notice.wait_for()
        assert _norm(notice.inner_text()) == OTHER_PRICE
        assert _state(db, reference) == before  # nothing has changed
        # the list is read again: Löyly now shows its price and no session buttons
        page.locator(f"#saunas .private-card:has(#sauna-name-{loyly['id']}) .private-card-other").wait_for()
        assert page.locator(f"#pair-{loyly['id']}-{target['id']}").count() == 0
        assert page.locator("section.confirming-step").count() == 0
        a11y.check_axe(page)
    finally:
        db.rollback()
        db.execute("UPDATE saunas SET whole_price_ore = %s WHERE id = %s", (price, loyly["id"]))
        db.commit()


def test_a_refusal_sauna_unavailable_gives_the_reason_and_drops_the_pair(page: Page, base_url, db, made):
    """The chosen pair is Blocked in the store before the Guest confirms: the API refuses `sauna_unavailable`, the step
    says why, reads the date's list again (the pair is gone) and nothing changes. The Block is removed afterwards."""
    windows = free_windows(base_url)
    current, target = windows[4], windows[6]
    kajo = _pair(base_url, current, "Kajo")
    page.set_viewport_size({"width": 1366, "height": 768})
    open_session(page, base_url)
    reference, _link = _open_manage(page, base_url, _book_whole(page, current, kajo))
    made.append(reference)
    try:
        _open_step_by_keyboard(page, base_url, reference)
        _choose(page, current["date"], kajo["id"], target["id"])
        db.execute("INSERT INTO blocks (sauna_id, during) SELECT %s, during FROM windows WHERE id = %s",
                   (kajo["id"], target["id"]))
        db.commit()
        before = _state(db, reference)
        a11y.tab_to(page, page.get_by_role("button", name="Move booking"))
        a11y.press(page, "Enter")
        notice = page.locator(".move-notice .notice", has_text="can no longer be booked")
        notice.wait_for()
        assert _norm(notice.inner_text()) ==             "This sauna can no longer be booked for this session. Nothing has changed."
        # the date's list is read again: the pair is gone, nothing is chosen, no confirming step
        page.locator("section.confirming-step").wait_for(state="detached")
        page.locator(f"#pair-{kajo['id']}-{current['id']}").wait_for()  # the list is shown again
        assert page.locator(f"#pair-{kajo['id']}-{target['id']}").count() == 0
        assert page.locator("input[name=pair]:checked").count() == 0
        assert _state(db, reference) == before  # nothing has changed
        a11y.check_axe(page)
    finally:
        db.rollback()
        db.execute("DELETE FROM blocks WHERE sauna_id = %s AND during = (SELECT during FROM windows WHERE id = %s)",
                   (kajo["id"], target["id"]))
        db.commit()


def test_a_stale_version_renews_the_move_step_with_a_new_key(page: Page, base_url, db, made):
    windows = free_windows(base_url)
    current, target = windows[1], windows[5]
    kajo = _pair(base_url, current, "Kajo")
    page.set_viewport_size({"width": 1366, "height": 768})
    open_session(page, base_url)
    reference, _link = _open_manage(page, base_url, _book_whole(page, current, kajo))
    made.append(reference)
    _open_step_by_keyboard(page, base_url, reference)
    first_key = _slot(page, reference)
    assert first_key
    _choose(page, current["date"], kajo["id"], target["id"])
    db.execute("UPDATE bookings SET version = version + 1 WHERE reference = %s", (reference,))
    db.commit()
    a11y.tab_to(page, page.get_by_role("button", name="Move booking"))
    a11y.press(page, "Enter")
    changed = page.locator(".notice", has_text="changed in the meantime")
    changed.wait_for()
    assert _norm(changed.inner_text()) == "This booking was changed in the meantime. Check it and choose again."
    page.wait_for_function(
        f"(old) => {{ const k = sessionStorage.getItem('draft:change:{reference}:move'); return !!k && k !== old; }}",
        arg=first_key)
    assert page.locator("input[name=pair]:checked").count() == 0
    assert page.locator("#saunas").count() == 0  # the date is asked again
    assert page.locator("section.confirming-step").count() == 0
    assert _state(db, reference)[:4] == ("active", 1, current["id"], kajo["id"])  # nothing has changed
    a11y.check_axe(page)
    # the fresh step moves with the new version
    _choose(page, current["date"], kajo["id"], target["id"])
    a11y.tab_to(page, page.get_by_role("button", name="Move booking"))
    page.keyboard.press("Enter")
    page.get_by_role("heading", level=1, name="Booking moved").wait_for()
    assert _state(db, reference)[:4] == ("active", 2, target["id"], kajo["id"])


def test_after_the_72_hour_cutoff_the_move_step_gives_the_reason(page: Page, base_url, stack, made):
    """The clock moves (`clock.off`) to one minute past the Private sauna's Cutoff (`start - 72 h`): the Manage page
    offers no move, and the move step gives the 72-hour reason with no date or Sauna question. The clock is put
    back."""
    window = free_windows(base_url)[0]
    kajo = _pair(base_url, window, "Kajo")
    page.set_viewport_size({"width": 1366, "height": 768})
    open_session(page, base_url)
    paid = _book_whole(page, window, kajo)
    reference = paid["booking"]["reference"]
    made.append(reference)
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
            page.locator(".notice").wait_for()
            assert page.get_by_role("link", name="Move private sauna").count() == 0
            page.goto(f"{base_url}/manage/{reference}/move-sauna")
            page.get_by_role("heading", level=1, name="Move private sauna").wait_for()
            notice = page.locator(".notice", has_text="can no longer be changed")
            notice.wait_for()
            assert CUTOFF_72.fullmatch(_norm(notice.inner_text())), notice.inner_text()
            assert page.locator("#date").count() == 0 and page.locator("#saunas").count() == 0
            assert page.locator("section.confirming-step").count() == 0
            a11y.check_axe(page)
        finally:
            c.rollback()
            c.execute("UPDATE clock SET off = off - %s", (shift,))
            c.execute("UPDATE sessions SET expires_at = expires_at - %s WHERE expires_at <> 'infinity'", (shift,))
            c.commit()
