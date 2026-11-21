"""Refusals on Review (FR-7, FR-11, FR-12, FR-14, FR-22, FR-23, UX-DR11/13/25/26, AD-9): the Guest reaches Review for 2
Seats, something changes under her, and she presses Pay.

- Seats taken through the database: the Notice under Back takes focus with the true Seats left and the nearest
  sessions; Pay, the payment note and the checkbox are gone; choosing a nearest session with the keyboard reloads
  Review for it with Pay back and focus on the heading.
- The last Seat lost: "No seat free. You have not been charged."
- The Booking deadline passed (the clock moved through `clock.off`): "This session can no longer be booked. ..."
- The payment switch `payment = "fail"` (switch file + backend restart, restored in `finally`): the Error summary,
  Pay kept, the same key; after the switch is off the same Pay books once.
- A key known from another browser session: the "may already be paid" Notice, Pay removed, Book seats starts a new
  draft.
- The browser session lost (its row deleted): "please try again", a new session, the same key; the next Pay books.

In each case no Booking or email exists for the refusal, name and email are still shown, and axe reports no A or AA
failure on Review.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import re
import uuid

import psycopg
import pytest
from playwright.sync_api import Page

from . import a11y
from .test_fr05_book_and_pay import _norm, draft, free_windows, open_session, review_draft, seats_left, set_draft

NAME, EMAIL = "Refused Guest", "refused@example.com"
REFERENCE = re.compile(r"/confirmation/[0-9A-HJKMNP-TV-Z]{8}$")

# Seats taken around the API (AD-21); "E2F" + the Window id is unique among these rows, removed by the fixture.
RAW_FILL = ("INSERT INTO bookings (window_id, seats, reference, name, email, price_per_seat_ore, total_ore) "
            "SELECT v.w, v.s, 'E2F' || lpad(v.w::text, 5, '0'), 'E2E fill', 'e2e@example.com', 25000, v.s * 25000 "
            "FROM (VALUES (%s, %s)) AS v(w, s)")


@pytest.fixture
def db(stack):
    """A raw connection to the stack's database; the fill rows are removed and the clock is reset afterwards."""
    url = f"postgresql://postgres:booking@127.0.0.1:{stack.db_port}/booking"
    with psycopg.connect(url) as c:
        yield c
        c.rollback()
        c.execute("DELETE FROM bookings WHERE name = 'E2E fill'")
        c.execute("UPDATE clock SET off = interval '0'")
        c.commit()


@pytest.fixture(scope="module")
def windows(base_url) -> list[dict]:
    return free_windows(base_url)


def mine(db, window: dict) -> tuple[int, int]:
    """(Bookings, Outbox emails) of this Guest in the Window."""
    db.rollback()
    row = db.execute("SELECT (SELECT count(*) FROM bookings WHERE window_id = %(w)s AND name = %(n)s), "
                     "(SELECT count(*) FROM outbox_emails o JOIN bookings b ON b.id = o.booking_id "
                     " WHERE b.window_id = %(w)s AND b.name = %(n)s)", {"w": window["id"], "n": NAME}).fetchone()
    db.rollback()
    return row


def fill(db, window: dict, seats: int) -> None:
    db.execute(RAW_FILL, (window["id"], seats))
    db.commit()


def to_review(page: Page, base_url: str, window: dict, **extra) -> None:
    open_session(page, base_url)
    set_draft(page, {**review_draft(window, name=NAME), "email": EMAIL, **extra})
    page.goto(base_url + "/book-seats/review")
    page.get_by_role("button", name=re.compile(r"^Pay NOK")).wait_for()


def pay(page: Page) -> None:
    """Tick the checkbox and press Pay, with the keyboard."""
    a11y.tab_to(page, page.locator("#terms"))
    a11y.press(page, "Space")
    a11y.tab_to(page, page.get_by_role("button", name=re.compile(r"^Pay NOK")))
    a11y.press(page, "Enter")


def refusal_notice(page: Page):
    notice = page.locator(".review > .notice")
    notice.wait_for()
    page.wait_for_function("() => document.activeElement && document.activeElement.matches('.review > .notice')")
    return notice


def kept(page: Page) -> None:
    """Name and email are still shown, and the summary and terms stay."""
    summary = [_norm(t) for t in page.locator(".summary-row").all_inner_texts()]
    assert f"Name {NAME}" in summary and f"Email {EMAIL}" in summary, summary
    assert page.locator(".terms-section").count() == 1


def pay_gone(page: Page) -> None:
    assert page.get_by_role("button", name=re.compile(r"^Pay NOK")).count() == 0
    assert page.locator("#terms, .pay-note").count() == 0


def test_seats_taken_shows_the_true_seats_left_and_the_nearest_sessions(page: Page, base_url, db, windows):
    window = windows[2]
    page.set_viewport_size({"width": 1366, "height": 768})
    to_review(page, base_url, window)
    key = draft(page)["key"]
    fill(db, window, 43)  # one Seat left, two requested
    pay(page)
    notice = refusal_notice(page)
    paragraphs = [_norm(t) for t in notice.locator("p").all_inner_texts()]
    assert paragraphs == ["Only 1 seat left in this session. You have not been charged.",
                          "The nearest sessions with room:"], paragraphs
    links = notice.locator(".nearest a")
    assert links.count() == 3
    assert all(re.search(r", \d{2}:\d{2}–\d{2}:\d{2}, 44 seats left$", _norm(t)) for t in links.all_inner_texts())
    # the three nearest in time to the refused one (a tie goes to the earlier), shown in time order
    at = dt.datetime.fromisoformat(window["start"])
    others = [w for w in windows if w["id"] != window["id"]]
    near = sorted(others, key=lambda w: abs(dt.datetime.fromisoformat(w["start"]) - at))[:3]
    expected = [f'{w["start"][11:16]}–{w["end"][11:16]}' for w in sorted(near, key=lambda w: w["start"])]
    shown = [re.search(r"(\d{2}:\d{2}–\d{2}:\d{2})", _norm(t)).group(1) for t in links.all_inner_texts()]
    assert shown == expected, (shown, expected)
    assert f'{window["start"][11:16]}–{window["end"][11:16]}' not in shown
    pay_gone(page)
    kept(page)
    assert mine(db, window) == (0, 0)
    assert draft(page)["key"] == key and draft(page)["window_id"] == window["id"]
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)

    # choose the first nearest session with the keyboard: Review for it, with Pay, the note and the checkbox back
    first = links.first
    chosen_text = _norm(first.inner_text())
    a11y.tab_to(page, first)
    a11y.press(page, "Enter")
    page.get_by_role("button", name="Pay NOK 500").wait_for()
    page.wait_for_function("() => document.activeElement && document.activeElement.tagName === 'H1'")
    a11y.assert_focus_visible(page)
    assert page.locator(".review > .notice").count() == 0
    assert not page.locator("#terms").is_checked()
    assert page.locator(".pay-note").count() == 1
    d = draft(page)
    assert d["window_id"] != window["id"] and d["key"] == key and d["name"] == NAME
    session = _norm(page.locator(".summary-row").nth(1).inner_text())
    assert session.split(" ", 1)[1] in chosen_text, (session, chosen_text)
    kept(page)


def test_the_last_seat_lost_says_no_seat_free(page: Page, base_url, db, windows):
    window = windows[3]
    to_review(page, base_url, window, seats=1)
    page.get_by_role("button", name="Pay NOK 250").wait_for()
    fill(db, window, 44)
    pay(page)
    notice = refusal_notice(page)
    assert _norm(notice.locator("p").first.inner_text()) == "No seat free. You have not been charged."
    assert notice.locator(".nearest a").count() >= 1
    pay_gone(page)
    kept(page)
    assert mine(db, window) == (0, 0)
    a11y.check_axe(page)
    a11y.tab_to(page, notice.locator(".nearest a").first)  # the links are reachable with the keyboard


def test_a_passed_deadline_says_the_session_can_no_longer_be_booked(page: Page, base_url, db, windows):
    window = windows[4]
    to_review(page, base_url, window)
    # the clock to 6 minutes after the start (the deadline is start + 5); the sessions keep their remaining life
    start = dt.datetime.fromisoformat(window["start"])
    shift = db.execute("SELECT %s::timestamptz + interval '6 minutes' - app_now()", (start,)).fetchone()[0]
    db.execute("UPDATE clock SET off = off + %s", (shift,))
    db.execute("UPDATE sessions SET expires_at = expires_at + %s WHERE expires_at <> 'infinity'", (shift,))
    db.commit()
    try:
        pay(page)
        notice = refusal_notice(page)
        assert _norm(notice.locator("p").first.inner_text()) == (
            "This session can no longer be booked. You have not been charged.")
        pay_gone(page)
        kept(page)
        assert mine(db, window) == (0, 0)
        a11y.check_axe(page)
        assert notice.locator(".nearest a").count() >= 1
        a11y.tab_to(page, notice.locator(".nearest a").first)  # the links are reachable with the keyboard
    finally:
        db.rollback()
        db.execute("UPDATE clock SET off = interval '0'")
        db.execute("UPDATE sessions SET expires_at = expires_at - %s WHERE expires_at <> 'infinity'", (shift,))
        db.commit()


def test_a_window_beyond_the_horizon_says_the_session_can_no_longer_be_booked(page: Page, base_url, db, windows):
    """The `outside_horizon` refusal on Review, stubbed: the booking and the date's listing both answer 409
    `outside_horizon` (the refused date has left the horizon), so there are no nearest sessions and the Notice offers
    Book seats instead."""
    window = windows[1]
    to_review(page, base_url, window)
    refused = {"status": 409, "content_type": "application/json",
               "body": '{"detail": {"error": "outside_horizon"}}'}
    page.route("**/api/bookings", lambda route: route.fulfill(**refused))
    page.route(re.compile(r".*/api/windows\?date=.*&seats=.*"), lambda route: route.fulfill(**refused))
    pay(page)
    notice = refusal_notice(page)
    assert [_norm(t) for t in notice.locator("p").all_inner_texts()] == [
        "This session can no longer be booked. You have not been charged.", "Book seats"]
    assert notice.locator(".nearest").count() == 0
    pay_gone(page)
    kept(page)
    assert mine(db, window) == (0, 0)
    a11y.check_axe(page)
    a11y.tab_to(page, notice.get_by_role("link", name="Book seats", exact=True))


def _switch(stack, text: str | None) -> None:
    f = stack.switches_dir / "test-switches.toml"
    if text is None:
        f.unlink(missing_ok=True)
    else:
        f.write_text(text, encoding="utf-8")
    stack.compose("restart", "backend")
    stack.wait()


def test_a_failed_payment_shows_the_error_summary_and_the_same_key_books_once(page: Page, base_url, db, stack,
                                                                              windows):
    window = windows[5]
    before = seats_left(base_url, window)
    to_review(page, base_url, window)
    key = draft(page)["key"]
    try:
        _switch(stack, 'payment = "fail"\n')
        pay(page)
        summary = page.locator("[data-error-summary]")
        summary.wait_for()
        page.wait_for_function("() => document.activeElement && document.activeElement.matches('[data-error-summary]')")
        assert _norm(summary.inner_text()) == "The payment failed. You have not been charged. You can pay again."
        page.wait_for_function("() => document.title.startsWith('Error: ')")
        assert page.get_by_role("button", name="Pay NOK 500").count() == 1  # Pay kept
        assert page.locator(".pay-note").count() == 1
        kept(page)
        assert mine(db, window) == (0, 0) and seats_left(base_url, window) == before
        assert draft(page)["key"] == key
        a11y.check_axe(page)
    finally:
        _switch(stack, None)
    a11y.tab_to(page, page.get_by_role("button", name="Pay NOK 500"))
    a11y.press(page, "Enter")
    page.wait_for_url(re.compile(re.escape(base_url) + REFERENCE.pattern))
    assert mine(db, window) == (1, 1) and seats_left(base_url, window) == before - 2


def test_a_key_known_from_another_session_removes_pay_and_offers_book_seats(page: Page, browser, base_url, db,
                                                                            windows):
    window = windows[6]
    key = str(uuid.uuid4())
    other = browser.new_context()
    try:  # another browser session pays first under the key
        o = other.new_page()
        open_session(o, base_url)
        status = o.evaluate(
            """async ({body, key}) => (await fetch('/api/bookings', {method: 'POST', credentials: 'same-origin',
                 headers: {'Content-Type': 'application/json', 'Idempotency-Key': key},
                 body: JSON.stringify(body)})).status""",
            {"body": {"window_id": window["id"], "seats": 2, "name": "First Payer", "email": "first@example.com"},
             "key": key})
        assert status == 201
    finally:
        other.close()
    to_review(page, base_url, window, key=key)
    pay(page)
    notice = refusal_notice(page)
    assert _norm(notice.locator("p").first.inner_text()) == (
        "This booking may already be paid. Check your email for a confirmation before you book again.")
    pay_gone(page)
    kept(page)
    assert mine(db, window) == (0, 0)
    a11y.check_axe(page)
    link = notice.get_by_role("link", name="Book seats", exact=True)
    a11y.tab_to(page, link)
    a11y.press(page, "Enter")
    page.wait_for_url(base_url + "/book-seats")
    page.wait_for_selector(".cal-grid")
    page.wait_for_load_state("networkidle")
    d = draft(page)
    assert "key" not in d and d.get("window_id") is None and d["name"] == NAME, d


@pytest.mark.parametrize("answer", ["payment_pending", "try_again", "network"])
def test_pending_retries_used_or_no_answer_say_try_again_with_pay_kept(page: Page, base_url, db, windows, answer):
    """`409 payment_pending`, `503 try_again` and no answer at all (stubbed with `page.route`): the "please try again"
    Notice takes focus; Pay, the payment note and the checkbox stay; the key is unchanged; nothing is written."""
    window = windows[1]
    to_review(page, base_url, window)
    key = draft(page)["key"]

    def stub(route):
        if answer == "network":
            route.abort()
        else:
            status = 409 if answer == "payment_pending" else 503
            route.fulfill(status=status, content_type="application/json", body=f'{{"detail": {{"error": "{answer}"}}}}')

    page.route(re.compile(r".*/api/bookings$"), stub)
    pay(page)
    notice = refusal_notice(page)
    assert _norm(notice.inner_text()) == "The booking could not be completed, please try again."
    assert page.get_by_role("button", name="Pay NOK 500").count() == 1
    assert page.locator(".pay-note").count() == 1 and page.locator("#terms").is_checked()
    kept(page)
    assert draft(page)["key"] == key
    assert mine(db, window) == (0, 0)
    a11y.check_axe(page)


def test_a_lost_browser_session_says_try_again_and_the_same_key_then_books(page: Page, base_url, db, windows):
    window = windows[7]
    to_review(page, base_url, window)
    key = draft(page)["key"]
    token = next(c["value"] for c in page.context.cookies() if c["name"] == "bp_session")
    db.execute("DELETE FROM sessions WHERE token_hash = %s", (hashlib.sha256(token.encode()).digest(),))
    db.commit()
    pay(page)
    notice = refusal_notice(page)
    text = _norm(notice.inner_text())
    assert "please try again" in text and "session" not in text.lower(), text
    assert page.get_by_role("button", name="Pay NOK 500").count() == 1  # Pay, the note and the checkbox kept
    assert page.locator("#terms").is_checked()
    kept(page)
    assert mine(db, window) == (0, 0)
    assert draft(page)["key"] == key
    a11y.check_axe(page)
    a11y.tab_to(page, page.get_by_role("button", name="Pay NOK 500"))
    a11y.press(page, "Enter")
    page.wait_for_url(re.compile(re.escape(base_url) + REFERENCE.pattern))
    assert mine(db, window) == (1, 1)
    db.rollback()
    assert db.execute("SELECT count(*) FROM idempotency_keys WHERE key = %s", (key,)).fetchone()[0] == 1
    db.rollback()
