"""The Private sauna page (FR-29, FR-30, FR-21, FR-22, FR-23, UX-DR17, UX-DR33, UX-DR35, UX-DR41; Story 5.1).

Reached from Landing's "Private sauna" Text link with the keyboard, focus on the `h1` and the title "Private sauna –
Saunalöyly". A date is typed or picked in the Date calendar of Book seats; the page then lists the seed's Saunas that
can be booked whole (all four, Lisa 2026-11-25: Rauha 7 at NOK 1850, Löyly 10 at NOK 2600, Kajo 12 at NOK 3150, Lumo
15 at NOK 3950) with their free sessions, by sauna or by session, both regrouped from the one `GET /api/private-saunas` response. Every choice is a
radio group in a fieldset with a legend and one tab stop. An empty date says so plainly. axe finds no A or AA failure,
nothing scrolls sideways at 1024, 1366 and 1920 px, every request stays on the stack's origin and no cookie is set.
Booking and paying is Story 5.2.
"""

from __future__ import annotations

import datetime as dt
import re

import httpx
import psycopg
import pytest
from playwright.sync_api import Page

from . import a11y, trust
from .admin import db_url

PAGE = "/private-sauna"
LEAD = "Book a whole sauna for your group for one session. Nobody else can book it, or a seat in it."
OPTIONS = ["Rauha, Holds 7, NOK 1850, 8 free sessions", "Löyly, Holds 10, NOK 2600, 8 free sessions",
           "Kajo, Holds 12, NOK 3150, 8 free sessions", "Lumo, Holds 15, NOK 3950, 8 free sessions"]


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
    a11y.tab_to(page, page.get_by_role("link", name="Private sauna", exact=True))
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


def test_by_sauna_lists_each_sauna_with_size_price_and_free_sessions_and_then_its_sessions(page: Page, base_url,
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
    assert page.locator("#saunas legend").inner_text() == "2. Choose a sauna"
    assert labels(page, "#saunas") == OPTIONS
    rows = [_norm(t) for t in page.locator("#saunas .sauna-option").all_inner_texts()]
    assert rows == [o.replace(",", "") for o in OPTIONS]
    assert page.locator("#sessions").count() == 0  # the second question comes with the first answer

    # one tab stop per group, arrow keys inside: View, then the Saunas, then the sessions of the chosen Sauna
    a11y.tab_to(page, page.locator("#view-sauna"))
    a11y.press(page, "Tab")
    assert page.evaluate("document.activeElement.id") == "sauna-1"
    a11y.press(page, "ArrowDown")
    assert page.locator("#sauna-2").is_checked()
    page.wait_for_selector("#sessions")
    assert page.locator("#sessions legend").inner_text() == "3. Choose a session"
    sessions = labels(page, "#sessions")
    assert len(sessions) == 8 and sessions[0] == "10:00 to 11:30" and sessions[-1] == "20:30 to 22:00"
    a11y.press(page, "Tab")
    first = page.evaluate("document.activeElement.id")
    assert first.startswith("session-")
    a11y.press(page, "ArrowDown")
    assert page.locator("#sessions input:checked").get_attribute("aria-label") == "11:30 to 13:00"
    a11y.press(page, "Tab")  # out of the sessions: the rail's Wordmark is the next stop
    assert page.evaluate("document.activeElement.className") == "wordmark"
    rail = page.locator(".rail")
    assert rail.get_by_role("link", name="Terms", exact=True).get_attribute("href") == "/terms"
    assert rail.get_by_role("link", name="Privacy notice", exact=True).get_attribute("href") == "/privacy"
    assert rail.locator("button, .button-primary").count() == 0


def test_by_session_regroups_the_same_listing(page: Page, base_url, day):
    requests = []
    page.on("request", lambda r: requests.append(r.url) if "/api/private-saunas" in r.url else None)
    open_page(page, base_url)
    type_date(page, day)
    page.locator("label.cell:has(#view-session)").click()
    assert page.locator("#sessions legend").inner_text() == "2. Choose a session"
    assert len(labels(page, "#sessions")) == 8
    assert page.locator("#saunas").count() == 0
    page.locator("label.session-row:has(input[aria-label='13:00 to 14:30'])").click()
    assert page.locator("#saunas legend").inner_text() == "3. Choose a sauna"
    assert labels(page, "#saunas") == OPTIONS
    page.locator("label.session-row:has(#sauna-4)").click()
    # back to by sauna: the complete choice is kept
    page.locator("label.cell:has(#view-sauna)").click()
    assert page.locator("#sauna-4").is_checked()
    assert page.locator("#sessions input:checked").get_attribute("aria-label") == "13:00 to 14:30"
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
    page.locator("label.session-row:has(#sauna-1)").click()
    page.wait_for_selector("#sessions")
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
