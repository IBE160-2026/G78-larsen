"""FR-22 and FR-23 on every Core page (Story 2.4): each page is visited in the states the flow reaches, and in each
axe-core reports no WCAG 2.2 level A or AA failure and nothing scrolls sideways at 1024, 1366 or 1920 px.

The pages and states: Landing and "Before you come"; Book seats empty, with its Error summary and with a sold-out
Session listed; Details with its Error summary; Review, and Review with a refusal Notice; Confirmation; Terms; the
Privacy notice; Sign-in, and Sign-in with its Error summary; the Booking list with a sold-out Session; the Outbox; and
the not-available page. The one known gap is WCAG 1.4.10 Reflow, until the narrow layout of FR-51.

The stack runs on the real clock with the seed's sample Bookings: the session at today + 3, 19:00 is full.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable

import httpx
import psycopg
import pytest
from playwright.sync_api import Page

from . import a11y, trust
from .admin import LOGIN, db_url, no_throttle, open_sign_in, type_login  # noqa: F401 (fixture)
from .guest import book_in_browser, free_windows, open_session
from .test_fr05_book_and_pay import review_draft, set_draft
from .test_fr11_refusals import RAW_FILL, pay, refusal_notice

FILL_NAME = "E2E fill"  # RAW_FILL's name; the fixture removes these rows


@pytest.fixture
def db(stack):
    with psycopg.connect(db_url(stack)) as c:
        yield c
        c.rollback()
        c.execute("DELETE FROM bookings WHERE name = %s", (FILL_NAME,))
        c.commit()


def today(base_url: str) -> dt.date:
    return dt.date.fromisoformat(httpx.get(base_url + "/api/windows", timeout=30,
                                           verify=trust.context()).json()["today"])


def dotted(d: dt.date) -> str:
    return d.strftime("%d.%m.%Y")


def audit(page: Page) -> None:
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)


def test_the_only_known_gap_is_reflow():
    assert a11y.KNOWN_GAPS == {"wcag1410": "1.4.10 Reflow (until FR-51)"}


# --- Guest pages ----------------------------------------------------------------------------------------------------

def _landing(page: Page, base_url: str, _db) -> None:
    page.goto(base_url + "/")
    page.locator("h1").first.wait_for()
    page.wait_for_load_state("networkidle")


def _before_you_come(page: Page, base_url: str, _db) -> None:
    page.goto(base_url + "/#before-you-come")
    page.wait_for_function("document.activeElement && document.activeElement.id === 'before-you-come'")


def _book_seats(page: Page, base_url: str, _db) -> None:
    open_session(page, base_url)


def _book_seats_error(page: Page, base_url: str, _db) -> None:
    open_session(page, base_url)
    a11y.tab_to(page, page.get_by_role("button", name="Continue booking"))
    a11y.press(page, "Enter")
    page.locator("[data-error-summary]").wait_for()


def _book_seats_sold_out(page: Page, base_url: str, _db) -> None:
    day = today(base_url) + dt.timedelta(days=3)  # the seed's full session, 19:00
    open_session(page, base_url)
    page.fill("#date", dotted(day))
    page.locator("#date").focus()
    a11y.press(page, "Enter")
    page.locator("label.cell:has(#seats-2)").click()
    page.locator(".session-row.unavailable", has_text="Sold out").first.wait_for()


def _details_error(page: Page, base_url: str, _db) -> None:
    window = free_windows(base_url)[0]
    open_session(page, base_url)
    set_draft(page, {"date": window["date"], "seats": 2, "window_id": window["id"]})
    page.goto(base_url + "/book-seats/details")
    page.wait_for_selector("#name")
    a11y.tab_to(page, page.get_by_role("button", name="Continue booking"))
    a11y.press(page, "Enter")
    page.locator("[data-error-summary]").wait_for()


def _open_review(page: Page, base_url: str, window: dict) -> None:
    open_session(page, base_url)
    set_draft(page, review_draft(window))
    page.goto(base_url + "/book-seats/review")
    page.get_by_role("button", name="Pay NOK 500").wait_for()


def _review(page: Page, base_url: str, _db) -> None:
    _open_review(page, base_url, free_windows(base_url)[0])


def _review_refused(page: Page, base_url: str, db) -> None:
    window = free_windows(base_url)[1]
    _open_review(page, base_url, window)
    db.execute(RAW_FILL, (window["id"], 44))
    db.commit()
    pay(page)
    refusal_notice(page)


def _confirmation(page: Page, base_url: str, _db) -> None:
    window = free_windows(base_url)[-1]
    open_session(page, base_url)
    reference = book_in_browser(page, window, 1)["booking"]["reference"]
    page.goto(f"{base_url}/confirmation/{reference}")
    page.wait_for_selector(".email-body")


def _terms(page: Page, base_url: str, _db) -> None:
    page.goto(base_url + "/terms")
    page.locator("h1").wait_for()


def _privacy(page: Page, base_url: str, _db) -> None:
    page.goto(base_url + "/privacy")
    page.locator("h1").wait_for()


def _not_available(page: Page, base_url: str, _db) -> None:
    page.goto(base_url + "/nope")
    page.get_by_role("link", name="Go to the Saunalöyly start page").wait_for()


# --- Administrator pages --------------------------------------------------------------------------------------------

def _sign_in(page: Page, base_url: str, _db) -> None:
    open_sign_in(page, base_url)


def _sign_in_error(page: Page, base_url: str, _db) -> None:
    open_sign_in(page, base_url)
    type_login(page, "not-the-password-at-all")
    page.locator("[data-error-summary]").wait_for()


def _signed_in(page: Page, base_url: str) -> None:
    open_sign_in(page, base_url)
    type_login(page, LOGIN["password"])
    page.wait_for_url(base_url + "/admin/bookings")
    page.locator("#date").wait_for()


def _booking_list_sold_out(page: Page, base_url: str, _db) -> None:
    _signed_in(page, base_url)
    day = today(base_url) + dt.timedelta(days=3)
    page.goto(f"{base_url}/admin/bookings?date={day.isoformat()}")
    page.locator(".session-group-full").first.wait_for()
    page.wait_for_load_state("networkidle")


def _outbox(page: Page, base_url: str, _db) -> None:
    _signed_in(page, base_url)
    page.goto(base_url + "/admin/outbox")
    page.locator(".outbox-entry").first.wait_for()
    page.wait_for_load_state("networkidle")


STATES: dict[str, Callable] = {
    "landing": _landing,
    "landing-before-you-come": _before_you_come,
    "book-seats": _book_seats,
    "book-seats-error-summary": _book_seats_error,
    "book-seats-sold-out-session": _book_seats_sold_out,
    "details-error-summary": _details_error,
    "review": _review,
    "review-refusal-notice": _review_refused,
    "confirmation": _confirmation,
    "terms": _terms,
    "privacy-notice": _privacy,
    "not-available": _not_available,
    "sign-in": _sign_in,
    "sign-in-error-summary": _sign_in_error,
    "booking-list-sold-out-session": _booking_list_sold_out,
    "outbox": _outbox,
}


@pytest.mark.parametrize("state", STATES)
def test_axe_and_no_horizontal_scroll(page: Page, base_url, db, state):
    STATES[state](page, base_url, db)
    audit(page)
