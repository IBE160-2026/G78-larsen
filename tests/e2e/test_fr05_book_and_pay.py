"""Details, Review and Confirmation (FR-5, FR-6, FR-8, FR-22, FR-23, UX-DR5/9/10/12/14/23/24/26/27/33): a Guest books 2
Seats from Landing to Confirmation with the keyboard alone (through `a11y.tab_to` and `a11y.press`); the Window then
has 2 fewer Seats left. Also: the titles, axe on the three pages, Pay in the first view at 1366 x 768, no horizontal
scroll, the Details and Terms errors, the draft's redirects, and that after a payment Back and the addresses of
Details and Review show Confirmation, so nothing can be paid twice.

The stack runs on the real clock with the sample Bookings of the seed; the tests book on a date without them.
"""

from __future__ import annotations

import json
import re

import httpx
import pytest
from playwright.sync_api import Page

from . import a11y, trust
from .guest import book_in_browser, free_windows, open_session  # noqa: F401 (also used by other modules)

REFERENCE = re.compile(r"[0-9A-HJKMNP-TV-Z]{8}")
TERMS = ["A booking for a fixed date cannot be withdrawn.", "A booking cannot be changed or refunded.",
         "If Saunalöyly cancels your session, you choose a refund or a voucher."]
RECEPTION = "Keep your booking reference and give it at reception when you arrive."


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace(" ", " ")).strip()


def seats_left(base_url: str, window: dict) -> int:
    ws = httpx.get(base_url + "/api/windows", params=dict(date=window["date"]), timeout=30,
                   verify=trust.context()).json()["windows"]
    return next(w["seats_left"] for w in ws if w["id"] == window["id"])


def set_draft(page: Page, draft: dict) -> None:
    """Replace the tab's Booking draft (`draft:seats`); the page must be on the stack's origin."""
    page.evaluate("d => sessionStorage.setItem('draft:seats', JSON.stringify(d))", draft)


def draft(page: Page) -> dict:
    raw = page.evaluate("sessionStorage.getItem('draft:seats')")
    return json.loads(raw) if raw else {}


def review_draft(window: dict, seats: int = 2, name: str = "Ingrid Hansen") -> dict:
    return {"date": window["date"], "seats": seats, "window_id": window["id"], "name": name,
            "email": "ingrid@example.com"}


@pytest.fixture(scope="module")
def windows(base_url) -> list[dict]:
    return free_windows(base_url)


def test_keyboard_alone_from_landing_to_confirmation(page: Page, base_url, windows):
    window = windows[0]
    before = seats_left(base_url, window)
    page.set_viewport_size({"width": 1366, "height": 768})
    page.goto(base_url + "/")
    a11y.tab_to(page, page.get_by_role("link", name="Book seats", exact=True))
    a11y.press(page, "Enter")
    page.wait_for_url(base_url + "/book-seats")
    page.wait_for_selector(".cal-grid")
    # Book seats: type the date, choose 2 seats and the first session, continue
    a11y.tab_to(page, page.locator("#date"))
    y, m, d = window["date"].split("-")
    page.keyboard.type(f"{d}.{m}.{y}")
    a11y.press(page, "Enter")
    page.wait_for_selector(".session-rows")
    a11y.tab_to(page, page.locator("#seats-1"))
    a11y.press(page, "ArrowRight")
    assert page.locator("#seats-2").is_checked()
    page.wait_for_load_state("networkidle")  # the Sessions are read again for 2 Seats
    page.wait_for_selector(".session-rows")
    first = page.locator(f"#session-{window['id']}")
    a11y.tab_to(page, first)
    a11y.press(page, "Space")
    assert first.is_checked()
    a11y.tab_to(page, page.get_by_role("button", name="Continue booking"))
    a11y.press(page, "Enter")

    # Details
    page.wait_for_url(base_url + "/book-seats/details")
    page.wait_for_selector("#name")
    assert page.title() == "Your details – Saunalöyly"
    a11y.tab_to(page, page.locator("#name"))
    page.keyboard.type("Ingrid Hansen")
    a11y.tab_to(page, page.locator("#email"))
    page.keyboard.type("ingrid@example.com")
    a11y.tab_to(page, page.get_by_role("button", name="Continue booking"))
    a11y.press(page, "Enter")

    # Review
    page.wait_for_url(base_url + "/book-seats/review")
    pay = page.get_by_role("button", name="Pay NOK 500")
    pay.wait_for()
    assert page.title() == "Review – Saunalöyly"
    box = pay.bounding_box()
    assert box and box["y"] + box["height"] <= 768, box  # Pay in the first view at 1366 x 768
    assert not page.locator("#terms").is_checked()  # never pre-ticked
    a11y.tab_to(page, page.locator("#terms"))
    a11y.press(page, "Space")
    assert page.locator("#terms").is_checked()
    a11y.tab_to(page, pay)
    a11y.press(page, "Enter")

    # Confirmation
    page.wait_for_url(re.compile(re.escape(base_url) + r"/confirmation/[0-9A-HJKMNP-TV-Z]{8}$"))
    page.wait_for_selector(".reference")
    reference = page.url.rsplit("/", 1)[1]
    assert page.title() == "Booking confirmed – Saunalöyly"
    assert page.locator("h1").inner_text() == "Booking confirmed"
    assert page.locator(".reference").inner_text() == reference
    assert page.locator(".reference-box + .reception").inner_text() == RECEPTION
    summary = [_norm(t) for t in page.locator(".summary-row").all_inner_texts()]
    assert summary[2:5] == ["Seats 2 seats", "Total NOK 500 incl. VAT", "Email ingrid@example.com"], summary
    assert [_norm(t) for t in page.locator(".terms-section p").all_inner_texts()] == TERMS
    assert page.get_by_role("link", name="Before you come").get_attribute("href") == "/#before-you-come"
    assert page.locator(".email-as-sent h2").inner_text() == "Sent by email:"
    body = page.locator(".email-body").inner_text()
    assert body.startswith("Booking confirmed\n") and f"Booking reference: {reference}\n" in body
    assert body.rstrip().endswith("Simulated payment: no money moves")
    assert f"{base_url}/#before-you-come" in body
    assert draft(page) == {"reference": reference}
    assert seats_left(base_url, window) == before - 2


def test_details_review_and_confirmation_pass_axe_and_fit_every_width(page: Page, base_url, windows):
    window = windows[1]
    open_session(page, base_url)
    set_draft(page, {"date": window["date"], "seats": 2, "window_id": window["id"]})
    page.goto(base_url + "/book-seats/details")
    page.wait_for_selector("#name")
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)

    page.fill("#name", "Ingrid Hansen")
    page.fill("#email", "ingrid@example.com")
    page.get_by_role("button", name="Continue booking").click()
    page.get_by_role("button", name="Pay NOK 500").wait_for()
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)
    # two columns down to 1200 px: the summary beside the terms; stacked below
    page.set_viewport_size({"width": 1366, "height": 768})
    left_box = page.locator(".summary").bounding_box()
    right_box = page.locator(".terms-section").bounding_box()
    assert left_box["x"] < right_box["x"] and abs(left_box["y"] - right_box["y"]) < 40
    page.set_viewport_size({"width": 1199, "height": 768})
    assert page.locator(".summary").bounding_box()["y"] < page.locator(".terms-section").bounding_box()["y"]

    page.locator("label.terms-check").click()
    page.get_by_role("button", name="Pay NOK 500").click()
    page.wait_for_selector(".email-body")
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)


def test_details_errors_keep_the_input_and_name_the_fields(page: Page, base_url, windows):
    window = windows[2]
    open_session(page, base_url)
    set_draft(page, {"date": window["date"], "seats": 2, "window_id": window["id"]})
    page.goto(base_url + "/book-seats/details")
    page.wait_for_selector("#name")
    page.fill("#email", "ingrid@example")
    a11y.tab_to(page, page.get_by_role("button", name="Continue booking"))
    a11y.press(page, "Enter")
    summary = page.locator("[data-error-summary]")
    summary.wait_for()
    assert summary.evaluate("el => el === document.activeElement")
    assert [_norm(t) for t in summary.locator("a").all_inner_texts()] == ["Enter your name",
                                                                         "Enter a valid email address"]
    assert [_norm(t) for t in page.locator(".field-error").all_inner_texts()] == ["Enter your name",
                                                                                 "Enter a valid email address"]
    page.wait_for_function("() => document.title.startsWith('Error: ')")
    assert page.title() == "Error: Your details – Saunalöyly"
    assert page.locator("#email").input_value() == "ingrid@example"  # input kept
    assert page.locator("#email").get_attribute("aria-describedby") == "email-error"
    a11y.tab_to(page, summary.get_by_role("link", name="Enter a valid email address"))
    a11y.press(page, "Enter")
    assert page.evaluate("document.activeElement.id") == "email"
    a11y.check_axe(page)
    assert page.url == base_url + "/book-seats/details"


def test_pay_without_the_terms_shows_an_error_and_charges_nothing(page: Page, base_url, windows):
    window = windows[3]
    before = seats_left(base_url, window)
    open_session(page, base_url)
    set_draft(page, review_draft(window))
    page.goto(base_url + "/book-seats/review")
    pay = page.get_by_role("button", name="Pay NOK 500")
    pay.wait_for()
    a11y.tab_to(page, pay)
    a11y.press(page, "Enter")
    summary = page.locator("[data-error-summary]")
    summary.wait_for()
    assert [_norm(t) for t in summary.all_inner_texts()] == ["Accept the booking terms"]
    assert page.locator("#terms-error").inner_text() == "Accept the booking terms"
    page.wait_for_function("() => document.title.startsWith('Error: ')")
    assert page.url == base_url + "/book-seats/review"
    assert seats_left(base_url, window) == before
    key = draft(page)["key"]
    assert re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", key)
    page.reload()  # the key is kept in the draft for every retry
    page.get_by_role("button", name="Pay NOK 500").wait_for()
    assert draft(page)["key"] == key
    a11y.check_axe(page)


def test_back_and_the_privacy_notice_keep_everything_entered(page: Page, base_url, windows):
    window = windows[4]
    open_session(page, base_url)
    set_draft(page, {"date": window["date"], "seats": 3, "window_id": window["id"]})
    page.goto(base_url + "/book-seats/details")
    page.fill("#name", "Ingrid Hansen")
    page.fill("#email", "ingrid@example.com")
    page.get_by_role("link", name="Privacy notice").click()
    page.wait_for_url(base_url + "/privacy")
    page.go_back()
    page.wait_for_selector("#name")
    assert (page.locator("#name").input_value(), page.locator("#email").input_value()) == (
        "Ingrid Hansen", "ingrid@example.com")
    page.get_by_role("button", name="Continue booking").click()
    page.get_by_role("button", name="Pay NOK 750").wait_for()
    page.get_by_role("link", name="Back", exact=True).click()
    page.wait_for_url(base_url + "/book-seats/details")
    page.wait_for_selector("#name")
    assert page.locator("#name").input_value() == "Ingrid Hansen"
    page.get_by_role("link", name="Back", exact=True).click()
    page.wait_for_url(base_url + "/book-seats")
    page.wait_for_selector(".session-row input:checked")
    assert page.locator(f"#session-{window['id']}").is_checked()
    assert page.locator("#seats-3").is_checked()


def test_missing_choices_go_to_the_earliest_page_without_an_error(page: Page, base_url, windows):
    window = windows[5]
    open_session(page, base_url)
    page.goto(base_url + "/book-seats/details")  # no session chosen
    page.wait_for_url(base_url + "/book-seats")
    page.wait_for_selector(".cal-grid")
    page.wait_for_load_state("networkidle")  # Book seats has written its (empty) draft
    set_draft(page, {"date": window["date"], "seats": 2, "window_id": window["id"]})
    page.goto(base_url + "/book-seats/review")  # no name or email
    page.wait_for_url(base_url + "/book-seats/details")
    page.wait_for_selector("#name")
    assert page.locator("[data-error-summary], .field-error").count() == 0


def test_after_payment_back_and_the_old_addresses_show_confirmation(page: Page, base_url, windows):
    window = windows[6]
    open_session(page, base_url)
    set_draft(page, {"date": window["date"], "seats": 2, "window_id": window["id"]})
    page.goto(base_url + "/book-seats/details")
    page.fill("#name", "Ingrid Hansen")
    page.fill("#email", "ingrid@example.com")
    page.get_by_role("button", name="Continue booking").click()
    page.get_by_role("button", name="Pay NOK 500").wait_for()
    page.locator("label.terms-check").click()
    page.get_by_role("button", name="Pay NOK 500").click()
    page.wait_for_selector(".email-body")
    confirmation = page.url
    reference = confirmation.rsplit("/", 1)[1]
    left = seats_left(base_url, window)
    page.go_back()  # the Details entry replaces itself with Confirmation
    page.wait_for_url(confirmation)
    for path in ("/book-seats/details", "/book-seats/review"):
        page.goto(base_url + path)
        page.wait_for_url(confirmation)
        page.wait_for_selector(".email-body")
    assert page.locator(".reference").inner_text() == reference
    page.reload()  # a reload in the paying browser session shows it again
    page.wait_for_selector(".email-body")
    assert seats_left(base_url, window) == left  # nothing was paid twice
    # Book seats after a paid Booking starts a new draft (and Review a new key)
    page.goto(base_url + "/book-seats")
    page.wait_for_selector(".cal-grid")
    page.wait_for_load_state("networkidle")
    assert "reference" not in draft(page)
    assert page.locator("#date").input_value() == ""


def test_confirmation_in_another_browser_is_not_available(page: Page, browser, base_url, windows):
    window = windows[7]
    open_session(page, base_url)
    reference = book_in_browser(page, window, 1)["booking"]["reference"]
    page.goto(base_url + f"/confirmation/{reference}")
    page.wait_for_selector(".email-body")
    other = browser.new_context(ignore_https_errors=True)
    try:
        stranger = other.new_page()
        stranger.goto(base_url + f"/confirmation/{reference}")
        stranger.get_by_role("heading", name="This page is not available.").wait_for()
        assert stranger.locator(".reference, .email-body, .summary").count() == 0
    finally:
        other.close()
