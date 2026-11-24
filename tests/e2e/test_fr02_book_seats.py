"""Book seats (FR-2, FR-3, FR-4, FR-21, FR-22, FR-23, UX-DR9/12/13/17–21/26/33–36): the three choices with the
keyboard alone (through `a11y.tab_to` and `a11y.press`), the title, axe, the whole page and the total in the first
view at 1366 x 768 with all eight seed Sessions, no horizontal scroll, stacking below 1200 px, the Error summary
with the "Error: " title, the Session rows' accessible names, the Total block, the typed-date Field errors, the
Booking draft restored on reload, and exactly one session cookie. The no-room paths (Nearest sessions, no room in
the horizon, a chosen Session cleared after a larger number, a draft date that has left the horizon) are set up
through the stack's database with Blocks and Seat bookings, which each test removes again.

The stack runs on the real clock, so the tests take today and the bookable dates from the API.
"""

from __future__ import annotations

import datetime as dt
import json
import re

import httpx
import psycopg
import pytest
from playwright.sync_api import Page

from . import a11y, trust

SLOTS = ["10:00", "11:30", "13:00", "14:30", "16:00", "17:30", "19:00", "20:30"]
SEAT_STATEMENT = ("A booking gives you seats in the shared saunas open during your session. On site you can move "
                  "freely between them.")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace(" ", " ")).strip()


@pytest.fixture(scope="module")
def facts(base_url) -> dict:
    body = httpx.get(base_url + "/api/windows", timeout=30, verify=trust.context()).json()
    assert body["dates"], body
    return body


@pytest.fixture(scope="module")
def full_day(base_url, facts) -> str:
    """The first bookable date whose eight Sessions are all still listed (tomorrow at the latest)."""
    for d in facts["dates"]:
        ws = httpx.get(base_url + "/api/windows", params=dict(date=d), timeout=30,
                       verify=trust.context()).json()["windows"]
        if len(ws) == 8:
            return d
    raise AssertionError("no date with eight Sessions")


def dotted(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}.{m}.{y}"


def open_page(page: Page, base_url: str) -> None:
    page.goto(base_url + "/book-seats")
    page.wait_for_selector(".cal-grid")


def choose_by_typing(page: Page, iso: str, seats: int) -> None:
    """Type the date (the field and the grid stay in step), pick the number, wait for the Sessions."""
    page.fill("#date", dotted(iso))
    page.locator("#date").focus()
    a11y.press(page, "Enter")
    page.locator(f"label.cell:has(#seats-{seats})").click()
    page.wait_for_selector(".session-rows")


def test_title_heading_and_nothing_pre_selected(page: Page, base_url):
    open_page(page, base_url)
    assert page.title() == "Book seats – Saunalöyly"
    assert page.locator("h1").inner_text() == "Book seats"
    assert page.locator("label[for=date]").inner_text() == "1. Choose a date"
    assert page.locator("#seats legend").inner_text() == "2. How many seats?"
    assert page.locator("#sessions legend").inner_text() == "3. Choose a session"
    assert page.locator("#date").input_value() == ""
    assert page.locator("input[type=radio]:checked").count() == 0
    assert page.locator(".session-row").count() == 0
    assert page.locator("#seats input[type=radio]").count() == 10


def test_the_rail_draws_the_wordmark_first_and_holds_the_notes_and_links(page: Page, base_url):
    open_page(page, base_url)
    rail = page.locator(".rail")
    # DOM order: total, Continue, Wordmark, notes; the Wordmark is drawn first
    order = rail.evaluate("el => Array.from(el.querySelectorAll('.total-note, .button-primary, .wordmark, "
                          ".rail-note')).map(e => e.className)")
    assert order[:3] == ["total-note", "button-primary", "wordmark"]
    wordmark = rail.locator(".wordmark")
    assert wordmark.get_attribute("href") == "/"
    ys = [rail.locator(sel).first.bounding_box()["y"] for sel in (".wordmark", ".total-note", ".button-primary")]
    assert ys == sorted(ys)
    assert _norm(rail.locator(".total-note").inner_text()) == "NOK 250 per seat in every session"
    assert _norm(rail.locator(".total").inner_text()) == ""  # no total before a number is chosen
    notes = [_norm(t) for t in rail.locator(".rail-note").all_inner_texts()]
    assert notes[:2] == [SEAT_STATEMENT, "Changing time is part of your session."]
    assert rail.get_by_role("link", name="Terms", exact=True).get_attribute("href") == "/terms"
    assert rail.get_by_role("link", name="Privacy notice", exact=True).get_attribute("href") == "/privacy"
    assert rail.get_by_role("button", name="Continue booking").is_enabled()


def test_the_calendar_offers_only_bookable_dates_and_ends_at_the_horizon(page: Page, base_url, facts):
    open_page(page, base_url)
    group = page.locator(".cal-grid")
    month = page.locator(".cal-month").inner_text()
    assert group.get_attribute("role") == "radiogroup"
    assert group.get_attribute("aria-label") == f"Pick a day, {month}"
    labels = [r.get_attribute("aria-label") for r in group.locator("input[type=radio]").all()]
    assert labels and all(re.fullmatch(r"\d{1,2} [A-Z][a-z]+ \d{4}", lbl) for lbl in labels), labels
    # walk forward to the last month: it ends at horizon_end with the horizon line
    while page.get_by_role("button", name="Next month").count():
        page.get_by_role("button", name="Next month").click()
        assert page.get_by_role("button", name="Previous month").count() == 1
    end_day = int(facts["horizon_end"][8:])
    last_cell = page.locator(".cal-grid > :last-child").inner_text()
    assert int(last_cell) == end_day
    assert page.locator(".cal-end").inner_text() == "Booking opens 4 weeks ahead."


def test_sessions_rows_name_their_seats_left_and_the_total_shows(page: Page, base_url, full_day):
    open_page(page, base_url)
    choose_by_typing(page, full_day, 2)
    rows = page.locator(".session-row")
    assert rows.count() == 8
    names = [r.get_attribute("aria-label") for r in page.locator(".session-row input").all()]
    for name, start, end in zip(names, SLOTS, SLOTS[1:] + ["22:00"]):
        assert re.fullmatch(rf"{start} to {end}, \d+ seats? left", name), name
    text = _norm(page.locator(".session-rows").inner_text())
    for banned in ("NOK", "Rauha", "Löyly", "Kajo", "Lumo", "hurry", "Only"):
        assert banned not in text, banned
    total = page.locator(".total")
    assert total.get_attribute("aria-live") == "polite"
    assert _norm(total.inner_text()) == "Total NOK 500 incl. VAT"
    assert page.locator("#date").input_value() == dotted(full_day)
    assert page.locator(f".cal-grid input[value='{full_day}']").is_checked()


def test_keyboard_alone_completes_the_three_choices_and_continues(page: Page, base_url):
    open_page(page, base_url)
    first_day = page.locator(".cal-grid input[type=radio]").first
    a11y.tab_to(page, first_day)
    a11y.press(page, "Space")
    assert first_day.is_checked()
    page.wait_for_selector(".session-rows")
    a11y.tab_to(page, page.locator("#seats-1"))
    a11y.press(page, "ArrowRight")
    assert page.locator("#seats-2").is_checked()
    page.wait_for_load_state("networkidle")  # the Sessions are read again for 2 Seats before Tab reaches them
    page.wait_for_selector(".session-rows")
    session = page.locator(".session-row input:not([disabled])").first
    a11y.tab_to(page, session)
    a11y.press(page, "Space")
    assert session.is_checked()
    a11y.tab_to(page, page.get_by_role("button", name="Continue booking"))
    a11y.press(page, "Enter")
    page.wait_for_url(base_url + "/book-seats/details")
    draft = json.loads(page.evaluate("sessionStorage.getItem('draft:seats')"))
    assert draft["seats"] == 2 and isinstance(draft["window_id"], int) and re.fullmatch(r"\d{4}-\d{2}-\d{2}",
                                                                                        draft["date"])


def test_continue_with_choices_missing_shows_the_error_summary(page: Page, base_url):
    open_page(page, base_url)
    a11y.tab_to(page, page.get_by_role("button", name="Continue booking"))
    a11y.press(page, "Enter")
    summary = page.locator("[data-error-summary]")
    summary.wait_for()
    assert summary.evaluate("el => el === document.activeElement")
    assert [_norm(t) for t in summary.locator("a").all_inner_texts()] == [
        "Choose a date", "Choose the number of seats", "Choose a session"]
    page.wait_for_function("() => document.title.startsWith('Error: ')")
    assert page.title() == "Error: Book seats – Saunalöyly"
    assert [_norm(t) for t in page.locator(".field-error").all_inner_texts()] == [
        "Choose a date", "Choose the number of seats", "Choose a session"]
    # each entry links to its question
    a11y.tab_to(page, summary.get_by_role("link", name="Choose the number of seats"))
    a11y.press(page, "Enter")
    assert page.evaluate("document.activeElement.id") == "seats-1"
    a11y.check_axe(page)


def test_a_typed_date_is_checked_on_enter(page: Page, base_url, facts):
    open_page(page, base_url)
    page.fill("#date", "32.13.2026")
    page.locator("#date").focus()
    a11y.press(page, "Enter")
    assert page.locator("#date-error").inner_text() == "Enter the date as dd.mm.yyyy"
    assert page.evaluate("document.activeElement.id") == "date"
    y, m, d = facts["today"].split("-")
    page.fill("#date", f"{min(int(d), 28):02d}.{m}.{int(y) + 1}")  # a real date a year ahead, even from 29.02
    a11y.press(page, "Enter")
    assert page.locator("#date-error").inner_text() == "This date cannot be booked. Pick a day below."
    assert page.locator(".cal-grid input:checked").count() == 0


def test_a_reload_restores_the_draft_and_reads_the_sessions_again(page: Page, base_url, full_day):
    open_page(page, base_url)
    choose_by_typing(page, full_day, 3)
    page.locator(".session-row:not(.unavailable)").nth(1).click()
    chosen = page.locator(".session-row input:checked").get_attribute("id")
    page.reload()
    page.wait_for_selector(".session-rows")
    page.wait_for_selector(".session-row input:checked")
    assert page.locator("#date").input_value() == dotted(full_day)
    assert page.locator("#seats-3").is_checked()
    assert page.locator(".session-row input:checked").get_attribute("id") == chosen
    assert _norm(page.locator(".total").inner_text()) == "Total NOK 750 incl. VAT"


def test_the_page_and_the_total_fit_the_first_view_at_1366x768(page: Page, base_url, full_day):
    page.set_viewport_size({"width": 1366, "height": 768})
    open_page(page, base_url)
    choose_by_typing(page, full_day, 2)
    assert page.locator(".session-row").count() == 8
    for locator in (page.locator("h1"), page.locator(".cal-grid"), page.locator(".session-row").last,
                    page.locator(".total"), page.get_by_role("button", name="Continue booking")):
        box = locator.bounding_box()
        assert box and box["y"] >= 0 and box["y"] + box["height"] <= 768, box
    assert page.evaluate("document.documentElement.scrollHeight") <= 768


def test_axe_no_horizontal_scroll_and_stacking_below_1200(page: Page, base_url, full_day):
    open_page(page, base_url)
    choose_by_typing(page, full_day, 2)
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)
    page.set_viewport_size({"width": 1366, "height": 768})
    date_box = page.locator(".question-date").bounding_box()
    seats_box = page.locator("#seats").bounding_box()
    assert date_box["x"] < seats_box["x"] and abs(date_box["y"] - seats_box["y"]) < 2
    page.set_viewport_size({"width": 1199, "height": 768})
    date_box = page.locator(".question-date").bounding_box()
    seats_box = page.locator("#seats").bounding_box()
    sessions_box = page.locator("#sessions").bounding_box()
    assert date_box["y"] + date_box["height"] <= seats_box["y"] < sessions_box["y"]
    assert abs(date_box["x"] - seats_box["x"]) < 2


def test_landing_book_seats_with_the_keyboard_reaches_the_page_with_one_cookie(page: Page, base_url):
    page.goto(base_url + "/")
    a11y.tab_to(page, page.get_by_role("link", name="Book seats", exact=True))
    assert page.context.cookies() == []  # no Landing load creates a session
    a11y.press(page, "Enter")
    page.wait_for_url(base_url + "/book-seats")
    page.wait_for_function("() => document.activeElement && document.activeElement.tagName === 'H1'")
    assert page.locator("h1").inner_text() == "Book seats"
    page.wait_for_load_state("networkidle")
    cookies = page.context.cookies()
    assert [c["name"] for c in cookies] == ["bp_session"]
    assert cookies[0]["httpOnly"] and cookies[0]["sameSite"] == "Strict"
    assert cookies[0]["secure"]  # HTTPS only since FR-24 (HT-3)


# ------------------------------------------------------------------ the no-room paths, set up in the stack's database


# A Seat booking written straight to the stack's database (with every NOT NULL column of Story 1.5), filling `seats`
# of Window `wid`; its reference "E2E" + the Window id is unique among these rows. The fixture below removes them.
RAW_FILL = ("INSERT INTO bookings (window_id, seats, reference, name, email, price_per_seat_ore, total_ore) "
            "SELECT v.w, v.s, 'E2E' || lpad(v.w::text, 5, '0'), 'E2E fill', 'e2e@example.com', 25000, v.s * 25000 "
            "FROM (VALUES (%s, %s)) AS v(w, s)")


@pytest.fixture
def db(stack):
    """A raw connection to the stack's database. Blocks and the Seat bookings written through it are removed
    afterwards (row deletes, so the triggers recompute), and the other tests see eight open Sessions again. The seed's
    sample Bookings, which have payments, emails and keys, stay."""
    url = f"postgresql://postgres:booking@127.0.0.1:{stack.db_port}/booking"
    with psycopg.connect(url) as c:
        yield c
        c.rollback()
        c.execute("DELETE FROM blocks")
        c.execute("DELETE FROM bookings WHERE name = 'E2E fill'")
        c.commit()


def block(db, first: str, days: int) -> None:
    """Block every Sauna for `days` whole Venue dates from `first`."""
    db.execute("INSERT INTO blocks (sauna_id, during) SELECT id, tstzrange("
               "%(d)s::date::timestamp AT TIME ZONE 'Europe/Oslo', "
               "(%(d)s::date + %(n)s)::timestamp AT TIME ZONE 'Europe/Oslo', '[)') FROM saunas",
               {"d": first, "n": days})
    db.commit()


@pytest.fixture(scope="module")
def late_day(base_url, facts) -> tuple[str, str]:
    """Two following bookable dates near the end of the horizon, both with eight Sessions."""
    first, second = facts["dates"][-3], facts["dates"][-2]
    for d in (first, second):
        assert len(httpx.get(base_url + "/api/windows", params=dict(date=d), timeout=30,
                             verify=trust.context()).json()["windows"]) == 8
    return first, second


def test_no_room_on_the_date_offers_the_nearest_sessions_and_choosing_one_selects_it(page: Page, base_url, db,
                                                                                    late_day):
    full, after = late_day
    block(db, full, 1)
    nearest = httpx.get(base_url + "/api/windows", params=dict(date=full, seats=2), timeout=30,
                        verify=trust.context()).json()["nearest"]
    assert [n["date"] for n in nearest] == [after] * 3
    open_page(page, base_url)
    choose_by_typing(page, full, 2)
    weekday = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][
        dt.date.fromisoformat(full).weekday()]
    notice = page.locator(".question-sessions .notice", has=page.locator(".nearest"))
    assert _norm(notice.locator("p").first.inner_text()) == (
        f"No room for 2 seats on {weekday}. The nearest sessions with room:")
    links = notice.locator(".nearest a")
    assert links.count() == 3
    assert all(re.search(r", \d{2}:\d{2}–\d{2}:\d{2}, 44 seats left$", _norm(t)) for t in links.all_inner_texts())
    assert page.locator(".session-row.unavailable").count() == 8
    a11y.tab_to(page, links.first)
    a11y.press(page, "Enter")
    sid = f"session-{nearest[0]['id']}"
    target = page.locator(f"#{sid}")
    page.wait_for_function(f"() => document.activeElement && document.activeElement.id === '{sid}'")
    assert target.is_checked()
    assert page.locator("#date").input_value() == dotted(after)
    assert page.locator(f".cal-grid input[value='{after}']").is_checked()
    assert page.locator("#seats-2").is_checked()
    a11y.assert_focus_visible(page)


def test_no_room_anywhere_in_the_horizon_says_so_without_alternatives(page: Page, base_url, db, facts, late_day):
    # every Seat left is booked: a Block cannot be laid over the sample Bookings of the seed, so fill instead
    db.execute("INSERT INTO bookings (window_id, seats, reference, name, email, price_per_seat_ore, total_ore) "
               "SELECT w.id, seats_left(w.id), 'E2E' || lpad(w.id::text, 5, '0'), 'E2E fill', 'e2e@example.com', "
               "25000, seats_left(w.id) * 25000 FROM windows w WHERE seats_left(w.id) > 0")
    db.commit()
    open_page(page, base_url)
    choose_by_typing(page, late_day[0], 2)
    notice = page.locator(".question-sessions .notice")
    notice.first.wait_for()
    assert [_norm(t) for t in notice.all_inner_texts()] == ["There is no room for 2 seats in the next 4 weeks."]
    assert page.locator(".nearest").count() == 0


def test_a_larger_number_clears_a_chosen_session_without_room(page: Page, base_url, db, late_day):
    day = late_day[0]
    windows = httpx.get(base_url + "/api/windows", params=dict(date=day), timeout=30,
                        verify=trust.context()).json()["windows"]
    wid = next(w["id"] for w in windows if w["start"][11:16] == "10:00")
    db.execute(RAW_FILL, (wid, 41))  # 3 Seats left
    db.commit()
    open_page(page, base_url)
    choose_by_typing(page, day, 2)
    row = page.locator(f"#session-{wid}")
    assert row.get_attribute("aria-label") == "10:00 to 11:30, 3 seats left"
    page.locator(f"label.session-row:has(#session-{wid})").click()
    assert row.is_checked()
    page.locator("label.cell:has(#seats-5)").click()
    cleared = page.locator(".question-sessions .notice", has_text="no longer has room")
    cleared.wait_for()
    assert _norm(cleared.inner_text()) == ("The session you chose no longer has room for 5 seats. "
                                           "Choose another session.")
    assert not row.is_checked() and row.is_disabled()
    assert row.get_attribute("aria-label") == "10:00 to 11:30, 3 seats left, not enough for 5"
    assert page.locator(f"label.session-row:has(#session-{wid})").get_attribute("class").split() == [
        "session-row", "unavailable"]


def test_a_draft_date_that_has_left_the_horizon_is_dropped_without_an_error(page: Page, base_url, facts):
    yesterday = (dt.date.fromisoformat(facts["today"]) - dt.timedelta(days=1)).isoformat()
    draft = json.dumps({"date": yesterday, "seats": 2, "window_id": 1})
    page.add_init_script(f"window.sessionStorage.setItem('draft:seats', {json.dumps(draft)})")
    page.goto(base_url + "/book-seats")
    page.wait_for_selector(".cal-grid")
    page.wait_for_load_state("networkidle")
    assert page.locator("#date").input_value() == ""
    assert page.locator(".cal-grid input:checked").count() == 0
    assert page.locator(".question-date .notice, .field-error, [data-error-summary]").count() == 0
    assert page.locator(".session-row").count() == 0


# ------------------------------------------------------------------ the month buttons, a failed read, an emptied field


def _active_text(page: Page) -> str:
    return page.evaluate("() => document.activeElement ? document.activeElement.textContent : ''")


def test_a_month_button_that_disappears_hands_focus_to_the_other(page: Page, base_url, db):
    """A 31-day horizon always spans two or three months, whatever the date of the run."""
    db.execute("UPDATE settings SET booking_horizon_days = 31")
    db.commit()
    try:
        open_page(page, base_url)
        next_month = page.get_by_role("button", name="Next month", exact=True)
        previous_month = page.get_by_role("button", name="Previous month", exact=True)
        first = page.locator(".cal-month").inner_text()
        assert previous_month.count() == 0 and next_month.count() == 1
        # forward to the last month: "Next month" goes, and focus moves to "Previous month"
        a11y.tab_to(page, next_month)
        while True:
            shown = page.locator(".cal-month").inner_text()
            a11y.press(page, "Enter")
            page.wait_for_function("(m) => document.querySelector('.cal-month').textContent !== m", arg=shown)
            if next_month.count() == 0:
                break
            assert _active_text(page) == "Next month"
        page.wait_for_function("() => document.activeElement && document.activeElement.textContent === "
                               "'Previous month'")
        a11y.assert_focus_visible(page)
        assert page.locator(".cal-end").count() == 1
        # back to the first month: "Previous month" goes, and focus moves to "Next month"
        while previous_month.count():
            shown = page.locator(".cal-month").inner_text()
            a11y.press(page, "Enter")
            page.wait_for_function("(m) => document.querySelector('.cal-month').textContent !== m", arg=shown)
        page.wait_for_function("() => document.activeElement && document.activeElement.textContent === 'Next month'")
        a11y.assert_focus_visible(page)
        assert page.locator(".cal-month").inner_text() == first
    finally:
        db.rollback()
        db.execute("UPDATE settings SET booking_horizon_days = 28")
        db.commit()


def test_a_failed_first_read_shows_the_notice_in_the_date_question(page: Page, base_url):
    page.route(re.compile(r".*/api/windows(\?.*)?$"),
               lambda route: route.fulfill(status=500, content_type="application/json",
                                           body='{"detail": {"error": "internal_error"}}'))
    page.goto(base_url + "/book-seats")
    notice = page.locator(".question-date .notice")
    notice.wait_for()
    assert _norm(notice.inner_text()) == "The sessions could not be loaded, please try again."
    assert page.locator(".cal-grid").count() == 0
    assert page.locator("#date").is_editable()
    assert page.get_by_role("button", name="Continue booking").is_enabled()
    a11y.check_axe(page)


def test_emptying_the_date_field_clears_the_date_and_the_chosen_session(page: Page, base_url, full_day):
    open_page(page, base_url)
    choose_by_typing(page, full_day, 2)
    page.locator(".session-row:not(.unavailable)").first.click()
    assert page.locator(".session-row input:checked").count() == 1
    page.fill("#date", "")
    a11y.press(page, "Tab")  # leaving the field commits it
    page.wait_for_function("() => document.querySelectorAll('.session-row').length === 0")
    assert page.locator(".cal-grid input:checked").count() == 0
    assert page.locator("#seats-2").is_checked()  # the number is not a date choice, so it stays
    assert page.locator(".field-error").count() == 0
    draft = json.loads(page.evaluate("sessionStorage.getItem('draft:seats')"))
    assert (draft["date"], draft["seats"], draft["window_id"]) == (None, 2, None)
    a11y.tab_to(page, page.get_by_role("button", name="Continue booking"))
    a11y.press(page, "Enter")
    summary = page.locator("[data-error-summary]")
    summary.wait_for()
    assert [_norm(t) for t in summary.locator("a").all_inner_texts()] == ["Choose a date", "Choose a session"]
