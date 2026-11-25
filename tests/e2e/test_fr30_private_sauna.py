"""The Private sauna page (FR-29, FR-30, FR-21, FR-22, FR-23, UX-DR17, UX-DR33, UX-DR35, UX-DR41; Story 5.1).

Reached from Landing's "Book private sauna" Booking choice with the keyboard, focus on the `h1` and the title "Private sauna –
Saunalöyly". A date is typed or picked in the Date calendar of Book seats; the page then lists the seed's Saunas that
can be booked whole (all four, Lisa 2026-11-25: Rauha 7 at NOK 1850, Löyly 10 at NOK 2600, Kajo 12 at NOK 3150, Lumo
15 at NOK 3950) with their free sessions, by sauna (proposal H: a card per Sauna with photo, description and its
sessions as buttons, one click for both) or by session (proposal K: session buttons, then the free Saunas as cards),
both regrouped from the one `GET /api/private-saunas` response (Lisa 2026-11-25). Every choice is a radio group in a
fieldset with a legend and one tab stop. An empty date says so plainly. axe finds no A or AA failure,
nothing scrolls sideways at 1024, 1366 and 1920 px, every request stays on the stack's origin and no cookie is set.

Story 5.2: the rail's "Continue booking" goes to the shared Details, Review and Confirmation with the draft
`draft:whole`. A Guest books Kajo from Landing to Confirmation with the keyboard alone; Review shows the Sauna, never
its Capacity, the Whole-sauna terms with "The sauna is not held while you pay." and "Pay NOK 3150", and axe passes on
Review and Confirmation. A Sauna taken while the Guest is on Review is refused with nothing charged, and the Notice
links back to the Private sauna page for the same date. Continue with nothing chosen gives an Error summary.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import uuid

import httpx
import psycopg
import pytest
from playwright.sync_api import Page

from . import a11y, trust
from .admin import db_url
from .guest import open_session

PAGE = "/private-sauna"
LEAD = "Book a whole sauna for your group for one session. Nobody else can book it, or a seat in it."
# Proposal K's Sauna cards (by session): name, size and price; the description is the radio's description
OPTIONS = ["Rauha, Holds 7, NOK 1850", "Löyly, Holds 10, NOK 2600", "Kajo, Holds 12, NOK 3150",
           "Lumo, Holds 15, NOK 3950"]
NAMES = ["Rauha", "Löyly", "Kajo", "Lumo"]
DESCRIPTIONS = ["Our smallest sauna. Rauha means peace: a quiet room for a small group.",
                "Löyly is the steam that rises when water meets the hot stones. A sauna for a mid-sized group.",
                "Kajo means a soft glow. A view of the open sea, and a bucket and ladle for throwing water on the stones, as in all our saunas.",
                "Our largest sauna, with long benches and a view of the open sea. Room for a big group."]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace(" ", " ")).strip()


def dotted(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}.{m}.{y}"


def long_date(iso: str) -> str:
    d = dt.date.fromisoformat(iso)
    return f"{d.strftime('%A')} {d.day} {d.strftime('%B')} {d.year}"


@pytest.fixture(scope="module")
def day(base_url) -> str:
    """A later date (never today, whose past sessions drop out) with no Booking at all, so all eight Sessions are
    free in every Sauna: the latest such date before Book seats' no-room fixtures (the last three dates)."""
    get = lambda path, **params: httpx.get(base_url + path, params=params, timeout=30,  # noqa: E731
                                           verify=trust.context()).json()
    facts = get("/api/windows")
    for d in reversed(facts["dates"][:-3]):
        if d <= facts["today"]:
            continue
        ws = get("/api/windows", date=d)["windows"]
        if len(ws) != 8 or any(w["seats_left"] != 44 for w in ws):
            continue
        if [len(s["windows"]) for s in get("/api/private-saunas", date=d)["saunas"]] == [8, 8, 8, 8]:
            return d
    raise AssertionError("no later date without bookings")


@pytest.fixture
def db(stack):
    """A raw connection to the stack's database; the Whole-sauna prices are put back afterwards."""
    with psycopg.connect(db_url(stack)) as c:
        prices = c.execute("SELECT id, whole_price_ore FROM saunas").fetchall()
        c.rollback()
        yield c
        c.rollback()
        for sid, price in prices:
            c.execute("UPDATE saunas SET whole_price_ore = %s WHERE id = %s", (price, sid))
        c.commit()


def open_page(page: Page, base_url: str) -> None:
    page.goto(base_url + PAGE)
    page.wait_for_selector(".cal-grid")


def type_date(page: Page, iso: str) -> None:
    """Type the date with the keyboard and wait for the listing."""
    a11y.tab_to(page, page.locator("#date"))
    page.keyboard.type(dotted(iso))
    a11y.press(page, "Enter")
    page.wait_for_selector("#saunas, .private-empty")


def labels(page: Page, group: str) -> list[str]:
    return [_norm(r.get_attribute("aria-label")) for r in page.locator(f"{group} input[type=radio]").all()]


def test_landing_link_with_the_keyboard_reaches_the_page_with_focus_on_its_heading(page: Page, base_url):
    page.goto(base_url + "/")
    a11y.tab_to(page, page.get_by_role("link", name="Book private sauna", exact=True))
    a11y.press(page, "Enter")
    page.wait_for_url(base_url + PAGE)
    page.wait_for_function("() => document.activeElement && document.activeElement.tagName === 'H1'")
    assert page.title() == "Private sauna – Saunalöyly"
    assert page.locator("h1").inner_text() == "Private sauna"
    assert _norm(page.locator(".private-lead").inner_text()) == LEAD
    assert page.locator("label[for=date]").inner_text() == "1. Choose a date"
    page.wait_for_selector(".cal-grid")
    assert page.locator("input[type=radio]:checked").count() == 0
    page.wait_for_load_state("networkidle")
    assert page.context.cookies() == []  # the page opens no session (AD-8)


def test_by_sauna_shows_a_card_per_sauna_and_one_click_chooses_the_sauna_and_the_session(page: Page, base_url,
                                                                                       day):
    # the page shows what the API lists: only the Saunas offered whole (in the browser-parametrized group of this
    # module, so `day` is not computed a second time after other modules have run)
    body = httpx.get(base_url + "/api/private-saunas", params=dict(date=day), timeout=30,
                     verify=trust.context()).json()
    assert set(body) == {"saunas", "horizon_end", "horizon_days"}
    assert [(s["name"], s["capacity"], s["whole_price_ore"], len(s["windows"])) for s in body["saunas"]] == [
        ("Rauha", 7, 185000, 8), ("Löyly", 10, 260000, 8), ("Kajo", 12, 315000, 8), ("Lumo", 15, 395000, 8)]
    open_page(page, base_url)
    type_date(page, day)
    assert page.locator("#view legend").inner_text() == "View"
    assert [_norm(t) for t in page.locator("#view label").all_inner_texts()] == ["Show by sauna", "Show by session"]
    assert page.locator("#view-sauna").is_checked()
    assert page.locator("#saunas > legend").inner_text() == "2. Choose a sauna and a session"

    # proposal H: one card per Sauna, each a group named by its Sauna and described by its text
    cards = page.locator("#saunas .private-card")
    assert cards.count() == 4
    for i, card in enumerate(cards.all()):
        assert card.get_attribute("role") == "group"
        name_id, text_id = card.get_attribute("aria-labelledby"), card.get_attribute("aria-describedby")
        assert _norm(page.locator(f"#{name_id}").inner_text()).startswith(NAMES[i] + " · Holds")
        assert _norm(page.locator(f"#{text_id}").inner_text()) == DESCRIPTIONS[i]
        assert _norm(card.locator(".private-card-price").inner_text()) == OPTIONS[i].rsplit(", ", 1)[1]
        assert card.locator("img").get_attribute("alt") == ""  # decorative here; the alt texts are on Landing
        assert card.locator("input[type=radio]").count() == 8
    pairs = labels(page, "#saunas")
    assert len(pairs) == 32 and pairs[0] == "Rauha, 10:00 to 11:30" and pairs[-1] == "Lumo, 20:30 to 22:00"
    assert page.locator("#saunas input[name=pair]").count() == 32  # one radio group for the whole listing
    assert page.locator("#sessions").count() == 0  # no third question

    # one tab stop for the whole listing, arrow keys inside
    a11y.tab_to(page, page.locator("#view-sauna"))
    a11y.press(page, "Tab")
    assert page.evaluate("document.activeElement.getAttribute('aria-label')") == "Rauha, 10:00 to 11:30"
    a11y.press(page, "ArrowDown")
    assert page.locator("#saunas input:checked").get_attribute("aria-label") == "Rauha, 11:30 to 13:00"
    a11y.press(page, "Tab")  # out of the listing: the rail's Continue (Story 5.2) is the next stop
    assert page.evaluate("document.activeElement.textContent") == "Continue booking"
    a11y.press(page, "Tab")
    assert page.evaluate("document.activeElement.className") == "wordmark"

    # one click on a session button chooses the Sauna and the session
    page.locator("#saunas label.slot:has(input[aria-label='Kajo, 13:00 to 14:30'])").click()
    checked = page.locator("#saunas input:checked")
    assert checked.count() == 1 and checked.get_attribute("aria-label") == "Kajo, 13:00 to 14:30"
    rail = page.locator(".rail")
    assert rail.get_by_role("link", name="Terms", exact=True).get_attribute("href") == "/terms"
    assert rail.get_by_role("link", name="Privacy notice", exact=True).get_attribute("href") == "/privacy"
    assert [_norm(t) for t in rail.locator("button, .button-primary").all_inner_texts()] == ["Continue booking"]


def test_by_session_shows_the_sessions_then_the_free_saunas_as_cards(page: Page, base_url, day):
    requests = []
    page.on("request", lambda r: requests.append(r.url) if "/api/private-saunas" in r.url else None)
    open_page(page, base_url)
    type_date(page, day)
    page.locator("label.cell:has(#view-session)").click()
    assert page.locator("#by-session > legend").inner_text() == "2. Choose a session and a sauna"
    assert page.locator("#sessions legend").inner_text() == "Session"
    sessions = labels(page, "#sessions")
    assert len(sessions) == 8
    assert sessions[0] == "10:00 to 11:30, 4 saunas free" and sessions[-1] == "20:30 to 22:00, 4 saunas free"
    assert _norm(page.locator("#sessions label.slot").first.inner_text()) == "10:00–11:30 4 saunas free"
    assert page.locator("#saunas").count() == 0
    page.locator("#sessions label.slot:has(input[aria-label^='13:00 to 14:30'])").click()
    assert page.locator("#saunas legend").inner_text() == "Sauna"
    assert labels(page, "#saunas") == OPTIONS
    for i, radio in enumerate(page.locator("#saunas input[type=radio]").all()):
        assert _norm(page.locator("#" + radio.get_attribute("aria-describedby")).inner_text()) == DESCRIPTIONS[i]
    assert page.locator("#saunas .private-pick img").count() == 4
    page.locator("label.private-pick:has(#sauna-4)").click()
    assert page.locator("#sauna-4").is_checked()
    # back to by sauna: the complete choice is kept
    page.locator("label.cell:has(#view-sauna)").click()
    assert page.locator("#saunas input:checked").get_attribute("aria-label") == "Lumo, 13:00 to 14:30"
    assert len(requests) == 1  # one listing, regrouped in the browser


def test_an_empty_date_says_so_plainly(page: Page, base_url, db, day):
    db.execute("UPDATE saunas SET whole_price_ore = NULL")
    db.commit()
    open_page(page, base_url)
    type_date(page, day)
    assert _norm(page.locator(".private-empty").inner_text()) == f"No sauna can be booked whole on {long_date(day)}."
    assert page.locator("#view, #saunas, #sessions").count() == 0
    # announced politely, as the Notices of Book seats; no urgency cue
    assert page.locator(".private-empty").evaluate("el => el.closest('[role=status]') !== null")
    # inside main: Next.js's own route announcer (`next-route-announcer`, role=alert in its shadow root) is always on
    # the page and is not ours
    assert page.locator("main [role=alert], main .notice").count() == 0
    a11y.check_axe(page)


def test_axe_no_horizontal_scroll_and_every_request_on_the_origin_without_a_cookie(page: Page, base_url, day):
    requests = []
    page.on("request", lambda r: requests.append(r.url))
    open_page(page, base_url)
    a11y.check_axe(page)
    page.locator(".cal-grid input[type=radio]").first.wait_for()
    page.fill("#date", dotted(day))
    page.locator("#date").press("Enter")
    page.wait_for_selector("#saunas")
    page.locator("#saunas label.slot").first.click()
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)
    page.locator("label.cell:has(#view-session)").click()
    page.locator("#sessions input[type=radio]").first.check()
    page.wait_for_selector("#saunas")
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)
    page.wait_for_load_state("networkidle")
    others = [u for u in requests if not (u == base_url or u.startswith(base_url + "/"))]
    assert not others, f"requests to another origin: {others}"
    assert not [u for u in requests if u.endswith("/api/session")]
    assert page.context.cookies() == []


# ------------------------------------------------------------------ Story 5.2: book and pay for a Private sauna

TERMS_WHOLE = ["A booking for a fixed date cannot be withdrawn.",
               "Up to 72 hours before the session starts, you can cancel for a refund or a voucher, or move the booking "
               "to another session.",
               "If Saunalöyly cancels your session, you choose a refund or a voucher.",
               "The sauna is not held while you pay."]
UNAVAILABLE = "This sauna can no longer be booked for this session. You have not been charged."


@pytest.fixture(scope="module")
def booking_day(base_url, day) -> str:
    """Another later date with no Booking at all, so booking on it leaves `day` free for the listing tests."""
    get = lambda path, **params: httpx.get(base_url + path, params=params, timeout=30,  # noqa: E731
                                           verify=trust.context()).json()
    facts = get("/api/windows")
    for d in reversed(facts["dates"][:-3]):
        if d <= facts["today"] or d == day:
            continue
        ws = get("/api/windows", date=d)["windows"]
        if len(ws) == 8 and all(w["seats_left"] == 44 for w in ws):
            return d
    raise AssertionError("no second later date without bookings")


def listing_of(base_url: str, date: str) -> dict:
    return httpx.get(base_url + "/api/private-saunas", params=dict(date=date), timeout=30,
                     verify=trust.context()).json()


def seats_left(base_url: str, date: str, window_id: int) -> int:
    ws = httpx.get(base_url + "/api/windows", params=dict(date=date), timeout=30,
                   verify=trust.context()).json()["windows"]
    return next(w["seats_left"] for w in ws if w["id"] == window_id)


def whole_draft(page: Page) -> dict:
    raw = page.evaluate("sessionStorage.getItem('draft:whole')")
    return json.loads(raw) if raw else {}


def summary(page: Page) -> list[str]:
    return [_norm(t) for t in page.locator(".summary-row").all_inner_texts()]


def test_keyboard_alone_books_kajo_from_landing_to_confirmation(page: Page, base_url, booking_day):
    kajo = next(s for s in listing_of(base_url, booking_day)["saunas"] if s["name"] == "Kajo")
    window = kajo["windows"][0]  # 10:00-11:30
    before = seats_left(base_url, booking_day, window["id"])
    page.set_viewport_size({"width": 1366, "height": 768})
    page.goto(base_url + "/")
    a11y.tab_to(page, page.get_by_role("link", name="Book private sauna", exact=True))
    a11y.press(page, "Enter")
    page.wait_for_url(base_url + PAGE)
    page.wait_for_selector(".cal-grid")
    type_date(page, booking_day)
    # one tab stop into the listing (Rauha 10:00), then the arrow keys to Kajo 10:00 (after Rauha's and Löyly's 8 each)
    a11y.tab_to(page, page.locator("#view-sauna"))
    a11y.press(page, "Tab")
    for _ in range(16):
        a11y.press(page, "ArrowDown")
    assert page.locator("#saunas input:checked").get_attribute("aria-label") == "Kajo, 10:00 to 11:30"
    a11y.tab_to(page, page.get_by_role("button", name="Continue booking"))
    a11y.press(page, "Enter")

    # Details: the shared page, with the Private sauna draft
    page.wait_for_url(base_url + "/private-sauna/details")
    page.wait_for_selector("#name")
    assert page.title() == "Your details – Saunalöyly"
    assert [c["name"] for c in page.context.cookies()] == ["bp_session"]  # Continue opened the session (AD-8)
    assert page.get_by_role("link", name="Back").get_attribute("href") == f"{PAGE}?date={booking_day}"
    a11y.tab_to(page, page.locator("#name"))
    page.keyboard.type("Olav Berg")
    a11y.tab_to(page, page.locator("#email"))
    page.keyboard.type("olav@example.com")
    a11y.tab_to(page, page.get_by_role("button", name="Continue booking"))
    a11y.press(page, "Enter")

    # Review
    page.wait_for_url(base_url + "/private-sauna/review")
    pay = page.get_by_role("button", name="Pay NOK 3150")
    pay.wait_for()
    assert page.title() == "Review – Saunalöyly"
    rows = summary(page)
    assert rows[:6] == ["Sauna Kajo", f"Date {long_date(booking_day)}", "Session 10:00–11:30",
                        "Total NOK 3150 incl. VAT", "Name Olav Berg", "Email olav@example.com"], rows
    assert [r.split(" ")[0] for r in rows[6:]] == ["Venue", "Contact"]
    assert not any("Holds" in r or "Seats" in r for r in rows)  # never the Sauna's Capacity
    assert [_norm(t) for t in page.locator(".terms-section p:not(.terms-links)").all_inner_texts()] == TERMS_WHOLE
    assert _norm(page.locator(".pay-note").inner_text()) == "Simulated payment: no money moves"
    assert not page.locator("#terms").is_checked()  # never pre-ticked
    box = pay.bounding_box()
    assert box and box["y"] + box["height"] <= 768, box
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)
    key = whole_draft(page)["key"]
    assert uuid.UUID(key).version == 4  # the one key, made on reaching Review (AD-9)
    a11y.tab_to(page, page.locator("#terms"))
    a11y.press(page, "Space")
    a11y.tab_to(page, pay)
    a11y.press(page, "Enter")

    # Confirmation: the shared page, rendered by kind
    page.wait_for_url(re.compile(re.escape(base_url) + r"/confirmation/[0-9A-HJKMNP-TV-Z]{8}$"))
    page.wait_for_selector(".reference")
    reference = page.url.rsplit("/", 1)[1]
    assert page.locator("h1").inner_text() == "Booking confirmed"
    rows = summary(page)
    assert rows[:5] == ["Sauna Kajo", f"Date {long_date(booking_day)}", "Session 10:00–11:30",
                        "Total NOK 3150 incl. VAT", "Email olav@example.com"], rows
    assert [_norm(t) for t in page.locator(".terms-section p").all_inner_texts()] == TERMS_WHOLE[:3]
    body = page.locator(".email-body").inner_text()
    assert "\nSauna: Kajo\n" in body and "\nSeats:" not in body and "Holds" not in body
    assert all(t in body for t in TERMS_WHOLE[:3])
    assert re.search(r"(?m)^Manage your booking\n" + re.escape(base_url) + r"/manage#t=[A-Za-z0-9_-]{43}\n\n"
                     r"Before you come$", body), body
    assert f"{base_url}/#before-you-come" in body and base_url.startswith("https://")
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)
    assert whole_draft(page) == {"reference": reference}
    assert seats_left(base_url, booking_day, window["id"]) == before - 12  # Kajo's 12 Seats at once (AD-5)
    # Back and the addresses of Details and Review show Confirmation: nothing can be paid twice
    for path in ("/private-sauna/review", "/private-sauna/details"):
        page.goto(base_url + path)
        page.wait_for_url(base_url + f"/confirmation/{reference}")


def test_a_sauna_taken_while_on_review_is_refused_and_links_back_to_the_date(page: Page, base_url, booking_day):
    lumo = next(s for s in listing_of(base_url, booking_day)["saunas"] if s["name"] == "Lumo")
    window = lumo["windows"][-1]
    open_session(page, base_url)
    page.evaluate("d => sessionStorage.setItem('draft:whole', JSON.stringify(d))",
                  {"date": booking_day, "window_id": window["id"], "sauna_id": lumo["id"], "sauna_name": "Lumo",
                   "whole_price_ore": lumo["whole_price_ore"], "name": "Olav Berg", "email": "olav@example.com"})
    page.goto(base_url + "/private-sauna/review")
    pay = page.get_by_role("button", name="Pay NOK 3950")
    pay.wait_for()
    # another Guest takes Lumo in that session meanwhile
    with httpx.Client(base_url=base_url, verify=trust.context(), headers={"Origin": base_url}, timeout=30) as other:
        assert other.post("/api/session", json={}).status_code == 200
        r = other.post("/api/bookings", json={"kind": "whole", "window_id": window["id"], "sauna_id": lumo["id"],
                                               "name": "Someone Else", "email": "else@example.com"},
                       headers={"Idempotency-Key": str(uuid.uuid4())})
        assert r.status_code == 201, r.text
    left = seats_left(base_url, booking_day, window["id"])
    page.locator("label.terms-check").click()
    pay.click()
    notice = page.locator(".notice", has_text=UNAVAILABLE)
    notice.wait_for()
    assert _norm(notice.locator("p").first.inner_text()) == UNAVAILABLE
    page.wait_for_function("() => document.activeElement && document.activeElement.classList.contains('notice')")
    link = notice.get_by_role("link", name="Choose another sauna or session")
    assert link.get_attribute("href") == f"{PAGE}?date={booking_day}"
    assert page.locator("#terms, .pay-note").count() == 0
    assert page.get_by_role("button", name=re.compile("^Pay")).count() == 0
    assert notice.locator(".nearest, input[type=radio]").count() == 0  # no Nearest sessions in this flow
    assert seats_left(base_url, booking_day, window["id"]) == left  # nothing written
    a11y.check_axe(page)
    link.click()
    page.wait_for_url(base_url + f"{PAGE}?date={booking_day}")
    page.wait_for_selector("#saunas")
    assert page.locator("#date").input_value() == dotted(booking_day)
    assert page.locator("#saunas input:checked").count() == 0  # the taken pair is not chosen again


def test_continue_with_nothing_chosen_gives_an_error_summary(page: Page, base_url, day):
    open_page(page, base_url)
    page.get_by_role("button", name="Continue booking").click()
    summary_box = page.locator(".error-summary")
    summary_box.wait_for()
    assert [_norm(t) for t in summary_box.locator("li").all_inner_texts()] == ["Choose a date"]
    type_date(page, day)
    page.get_by_role("button", name="Continue booking").click()
    page.wait_for_function("() => document.activeElement && document.activeElement.classList.contains('error-summary')")
    assert [_norm(t) for t in summary_box.locator("li").all_inner_texts()] == ["Choose a sauna and a session"]
    assert page.url == base_url + PAGE
    a11y.check_axe(page)


def book_whole_in_browser(page: Page, window_id: int, sauna_id: int, name: str = "Olav Berg") -> dict:
    """Pay for a Private sauna through the API from the page, with its session cookie (as Review does)."""
    status, body = page.evaluate(
        """async ({body, key}) => {
             const r = await fetch('/api/bookings', {method: 'POST', credentials: 'same-origin',
               headers: {'Content-Type': 'application/json', 'Idempotency-Key': key}, body: JSON.stringify(body)});
             return [r.status, await r.json()];
           }""",
        {"body": {"kind": "whole", "window_id": window_id, "sauna_id": sauna_id, "name": name,
                  "email": "olav@example.com"}, "key": str(uuid.uuid4())})
    assert status == 201, body
    return body


def sauna_window(base_url: str, date: str, name: str, start: str) -> tuple[dict, dict]:
    """(the Sauna as the listing shows it, its free Window that starts at `start` "HH:MM")."""
    sauna = next(s for s in listing_of(base_url, date)["saunas"] if s["name"] == name)
    return sauna, next(w for w in sauna["windows"] if w["start"][11:16] == start)


def test_a_whole_booking_on_the_manage_page_and_in_the_booking_list(page: Page, base_url, browser, booking_day):
    """Before Story 5.3 the Manage link shows the Whole-sauna booking with no Changes, and the Seat Change pages are
    not available for it; the Administrator's Booking list names its Sauna in the Seats column."""
    from .test_fr16_booking_list import group, open_day, sign_in

    loyly, window = sauna_window(base_url, booking_day, "Löyly", "16:00")
    open_session(page, base_url)
    paid = book_whole_in_browser(page, window["id"], loyly["id"])
    reference = paid["booking"]["reference"]
    link = re.search(r"(?m)^(https://\S+/manage#t=[A-Za-z0-9_-]{43})$", paid["emails"][0]["body"]).group(1)
    page.goto(link)
    page.wait_for_url(f"{base_url}/manage/{reference}")
    page.get_by_role("heading", name="Manage booking").wait_for()
    page.locator(".summary").wait_for()
    assert [_norm(t) for t in page.locator(".summary-row dt").all_inner_texts()] == ["Sauna", "Date", "Session",
                                                                                      "Total"]
    assert summary(page) == ["Sauna Löyly", f"Date {long_date(booking_day)}", "Session 16:00–17:30",
                             "Total NOK 2600 incl. VAT"]
    assert page.get_by_role("link", name="Move seats").count() == 0
    assert page.get_by_role("link", name="Give up seats for a voucher").count() == 0
    main = page.locator("main").inner_text()
    assert "Seats" not in main and "Holds" not in main
    a11y.check_axe(page)
    for step in ("move", "voucher"):
        page.goto(f"{base_url}/manage/{reference}/{step}")
        page.get_by_role("heading", level=1, name="This page is not available.").wait_for()

    admin = browser.new_context(base_url=base_url, ignore_https_errors=True).new_page()
    try:
        sign_in(admin, base_url)
        open_day(admin, base_url, dt.date.fromisoformat(booking_day))
        row = group(admin, "16:00", "17:30").locator("tbody tr").filter(has_text=reference)
        cells = row.locator("td")
        assert _norm(cells.nth(3).inner_text()) == "Löyly"  # the Seats column names the Sauna
        assert "num" not in (cells.nth(3).get_attribute("class") or "")
        assert _norm(cells.nth(4).inner_text()) == "NOK 2600"
    finally:
        admin.context.close()


def test_a_voucher_pays_part_of_a_private_sauna_on_review(page: Page, base_url, booking_day):
    from .test_fr28_voucher import _rows, _voucher

    ws = httpx.get(base_url + "/api/windows", params=dict(date=booking_day), timeout=30,
                   verify=trust.context()).json()["windows"]
    code = _voucher(page, base_url, dict(ws[6], date=booking_day), 1)  # NOK 250
    rauha, window = sauna_window(base_url, booking_day, "Rauha", "14:30")
    page.evaluate("d => sessionStorage.setItem('draft:whole', JSON.stringify(d))",
                  {"date": booking_day, "window_id": window["id"], "sauna_id": rauha["id"], "sauna_name": "Rauha",
                   "whole_price_ore": rauha["whole_price_ore"], "name": "Olav Berg", "email": "olav@example.com"})
    page.goto(base_url + "/private-sauna/review")
    page.get_by_role("button", name="Pay NOK 1850").wait_for()
    page.locator("#voucher-code").fill(code)
    page.get_by_role("button", name="Apply voucher").click()
    pay = page.get_by_role("button", name="Pay NOK 1600")
    pay.wait_for()
    rows = _rows(page)
    assert (rows["Total"], rows["Voucher"], rows["To pay by card"]) == ("NOK 1850 incl. VAT", "−NOK 250", "NOK 1600")
    assert list(rows)[:6] == ["Sauna", "Date", "Session", "Total", "Voucher", "To pay by card"]
    a11y.check_axe(page)
    page.locator("label.terms-check").click()
    pay.click()
    page.wait_for_url(re.compile(re.escape(base_url) + r"/confirmation/[0-9A-HJKMNP-TV-Z]{8}$"))
    page.wait_for_selector(".reference")
    rows = summary(page)
    assert rows[:6] == ["Sauna Rauha", f"Date {long_date(booking_day)}", "Session 14:30–16:00",
                        "Total NOK 1850 incl. VAT", "Paid with voucher NOK 250", "Paid by card NOK 1600"], rows
    body = page.locator(".email-body").inner_text()
    assert "Total: NOK 1850 incl. VAT\nPaid with voucher: NOK 250\nPaid by card: NOK 1600\n" in body
