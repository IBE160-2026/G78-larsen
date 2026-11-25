"""FR-28 / AD-30 / AD-19 (Story 4.4) in the compose stack, over HTTPS: a Guest gets a Voucher by giving up a Seat
through the Manage link, then pays part of a new Booking with it on Review with the keyboard alone (every key through
`a11y.press` / `a11y.tab_to`). Applying the code adds the "Voucher" and "To pay by card" rows and makes Pay "Pay NOK
250", still in the first view at 1366 x 768; Confirmation and the email show the total and both parts. An invalid code
is one Field error and Error summary entry with the input kept, a Voucher that covers the total makes Pay "Book with
voucher" with no payment note, and a code used up before Pay is refused at Pay with the same message. axe finds no A or
AA failure on Review with the Voucher field, nothing scrolls sideways at 1024, 1366 and 1920 px, and no Voucher code
reaches a container log.
"""

from __future__ import annotations

import re
import uuid

import pytest
from playwright.sync_api import Page

from . import a11y
from .guest import book_in_browser, free_windows, open_session
from .test_fr05_book_and_pay import draft, seats_left, set_draft
from .test_fr11_refusals import db, fill  # noqa: F401 (fixture)
from .test_fr27_voucher import CODE, _open_manage

INVALID = "This voucher code cannot be used. It may be mistyped, used up or expired. Check the code and try again."
NBSP = " "


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace(NBSP, " ")).strip()


@pytest.fixture(scope="module")
def windows(base_url) -> list[dict]:
    """The eight Windows of one date without Bookings, shared by this module's tests so they use up one date only."""
    return free_windows(base_url)


def _voucher(page: Page, base_url: str, window: dict, seats: int) -> str:
    """A Voucher worth `seats` x NOK 250: pay for `seats + 1` Seats, open the Manage link and give up `seats` from the
    page, as the Manage page does. Returns the code from the Change email."""
    reference, _ = _open_manage(page, base_url, window, seats + 1)
    status, body = page.evaluate(
        """async ({ref, seats, key}) => {
             const r = await fetch(`/api/manage/${ref}/seats/voucher`, {method: 'POST', credentials: 'same-origin',
               headers: {'Content-Type': 'application/json', 'Idempotency-Key': key},
               body: JSON.stringify({seats, version: 0})});
             return [r.status, await r.json()];
           }""",
        {"ref": reference, "seats": seats, "key": str(uuid.uuid4())})
    assert status == 200, body
    return CODE.search(body["emails"][0]["body"]).group(1)


def _review(page: Page, base_url: str, window: dict, seats: int) -> None:
    """Open Review for `seats` Seats in `window` with a fresh draft (a new key)."""
    set_draft(page, {"date": window["date"], "seats": seats, "window_id": window["id"], "name": "Ingrid Hansen",
                     "email": "ingrid@example.com"})
    page.goto(base_url + "/book-seats/review")
    page.get_by_role("heading", level=1, name="Review").wait_for()
    page.locator("#voucher-code").wait_for()
    page.wait_for_load_state("networkidle")


def _rows(page: Page) -> dict[str, str]:
    return dict(zip([_norm(t) for t in page.locator(".summary-row dt").all_inner_texts()],
                    [_norm(t) for t in page.locator(".summary-row dd").all_inner_texts()]))


def _type_code(page: Page, text: str) -> None:
    field = page.locator("#voucher-code")
    a11y.tab_to(page, field)
    page.keyboard.press("Control+A")
    page.keyboard.press("Delete")
    page.keyboard.type(text)


def test_a_guest_pays_partly_with_a_voucher_with_the_keyboard_alone(page: Page, base_url, stack, windows):
    page.set_viewport_size({"width": 1366, "height": 768})
    code = _voucher(page, base_url, windows[0], 1)  # NOK 250

    _review(page, base_url, windows[1], 2)
    assert page.get_by_role("button", name="Pay NOK 500").is_visible()
    label = page.locator("label[for=voucher-code]")
    assert _norm(label.inner_text()) == "Voucher code"
    # the field sits between the Booking summary and the booking terms, in the terms' column
    assert page.locator(".review-cols > div > .voucher-field + .terms-section").count() == 1
    a11y.check_axe(page)

    # typed as a Guest might: lower case, a space instead of a hyphen; applied with the Text link
    typed = code.lower().replace("-", " ", 1)
    _type_code(page, typed)
    a11y.tab_to(page, page.get_by_role("button", name="Apply voucher"))
    a11y.press(page, "Enter")
    pay = page.get_by_role("button", name="Pay NOK 250")
    pay.wait_for()
    rows = _rows(page)
    assert rows["Total"] == "NOK 500 incl. VAT"
    assert rows["Voucher"] == "−NOK 250" and rows["To pay by card"] == "NOK 250"
    assert list(rows)[3:6] == ["Total", "Voucher", "To pay by card"]
    assert _norm(page.locator(".pay-note").inner_text()) == "Simulated payment: no money moves"
    assert page.locator("#voucher-code").input_value() == typed
    assert draft(page)["voucher_code"] == typed
    box = pay.bounding_box()
    assert box and box["y"] + box["height"] <= 768, box  # Pay in the first view at 1366 x 768
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)

    a11y.tab_to(page, page.locator("#terms"))
    a11y.press(page, "Space")
    a11y.tab_to(page, pay)
    a11y.press(page, "Enter")

    # Confirmation: the total, then how it was paid; the email the same
    page.wait_for_url(re.compile(re.escape(base_url) + r"/confirmation/[0-9A-HJKMNP-TV-Z]{8}$"))
    page.wait_for_selector(".reference")
    reference = page.url.rsplit("/", 1)[1]
    summary = [_norm(t) for t in page.locator(".summary-row").all_inner_texts()]
    assert summary[2:6] == ["Seats 2 seats", "Total NOK 500 incl. VAT", "Paid with voucher NOK 250",
                            "Paid by card NOK 250"], summary
    body = page.locator(".email-body").inner_text()
    assert "Total: NOK 500 incl. VAT\nPaid with voucher: NOK 250\nPaid by card: NOK 250\n" in body
    assert body.rstrip().endswith("Simulated payment: no money moves")
    assert code not in body and code.replace("-", "") not in body
    a11y.check_axe(page)

    # no Voucher code in any container log
    logs = stack.compose("logs", "--no-color").stdout
    assert "POST /api/vouchers/quote" in logs and reference
    for c in (code, code.replace("-", ""), typed, typed.upper()):
        assert c not in logs, f"{c!r} is in the compose logs"


def test_invalid_codes_whole_vouchers_and_a_code_used_up_before_pay(page: Page, base_url, stack, windows):
    page.set_viewport_size({"width": 1366, "height": 768})
    whole = _voucher(page, base_url, windows[2], 2)  # NOK 500
    small = _voucher(page, base_url, windows[3], 1)  # NOK 250

    # an unknown code, applied with Enter in the field: one Field error and Error summary entry, the input kept
    _review(page, base_url, windows[4], 2)
    _type_code(page, "ABCD-EFGH-JKMN-PQRS")
    a11y.press(page, "Enter")
    page.locator("#voucher-code-error").wait_for()
    assert _norm(page.locator("#voucher-code-error").inner_text()) == INVALID
    assert [_norm(t) for t in page.locator(".error-summary li").all_inner_texts()] == [INVALID]
    assert page.locator("#voucher-code").input_value() == "ABCD-EFGH-JKMN-PQRS"
    assert page.locator("#voucher-code").get_attribute("aria-invalid") == "true"
    assert page.get_by_role("button", name="Pay NOK 500").is_visible()
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)
    # the summary entry leads to the field; editing removes the error
    a11y.tab_to(page, page.locator(".error-summary a"))
    a11y.press(page, "Enter")
    assert page.evaluate("() => document.activeElement.id") == "voucher-code"
    page.keyboard.press("End")
    page.keyboard.press("Backspace")
    assert page.locator("#voucher-code-error").count() == 0 and page.locator(".error-summary").count() == 0

    # a Voucher that covers the total: "Book with voucher", no card row, no payment note
    _review(page, base_url, windows[4], 1)
    _type_code(page, whole)
    a11y.press(page, "Enter")
    book = page.get_by_role("button", name="Book with voucher")
    book.wait_for()
    rows = _rows(page)
    assert rows["Voucher"] == "−NOK 250" and "To pay by card" not in rows
    assert page.locator(".pay-note").count() == 0
    a11y.check_axe(page)
    # editing the field removes the applied Voucher
    page.keyboard.press("Backspace")
    page.get_by_role("button", name="Pay NOK 250").wait_for()
    assert "Voucher" not in _rows(page)
    # applied again and booked: Confirmation shows the Voucher part only, with no payment note
    page.keyboard.type(whole[-1])
    a11y.press(page, "Enter")
    book.wait_for()
    a11y.tab_to(page, page.locator("#terms"))
    a11y.press(page, "Space")
    a11y.tab_to(page, book)
    a11y.press(page, "Enter")
    page.wait_for_url(re.compile(re.escape(base_url) + r"/confirmation/[0-9A-HJKMNP-TV-Z]{8}$"))
    page.wait_for_selector(".reference")
    summary = [_norm(t) for t in page.locator(".summary-row").all_inner_texts()]
    assert summary[3:5] == ["Total NOK 250 incl. VAT", "Paid with voucher NOK 250"], summary
    assert not any(row.startswith("Paid by card") for row in summary)
    body = page.locator(".email-body").inner_text()
    assert "Paid with voucher: NOK 250\n" in body and "Paid by card" not in body
    assert "Simulated payment: no money moves" not in body
    assert "Simulated payment" not in page.locator("main").inner_text()

    # a code applied, then used up elsewhere before Pay: Pay is refused with the same message, the input kept
    _review(page, base_url, windows[5], 2)
    _type_code(page, small)
    a11y.press(page, "Enter")
    page.get_by_role("button", name="Pay NOK 250").wait_for()
    status, body = page.evaluate(
        """async ({code, window, key}) => {
             const r = await fetch('/api/bookings', {method: 'POST', credentials: 'same-origin',
               headers: {'Content-Type': 'application/json', 'Idempotency-Key': key},
               body: JSON.stringify({window_id: window, seats: 1, name: 'Ingrid Hansen', email: 'ingrid@example.com',
                                     voucher_code: code, voucher_part_ore: 25000})});
             return [r.status, await r.json()];
           }""",
        {"code": small, "window": windows[6]["id"], "key": str(uuid.uuid4())})
    assert status == 201, body
    a11y.tab_to(page, page.locator("#terms"))
    a11y.press(page, "Space")
    a11y.tab_to(page, page.get_by_role("button", name="Pay NOK 250"))
    a11y.press(page, "Enter")
    page.locator("#voucher-code-error").wait_for()
    assert _norm(page.locator("#voucher-code-error").inner_text()) == INVALID
    assert [_norm(t) for t in page.locator(".error-summary li").all_inner_texts()] == [INVALID]
    assert page.locator("#voucher-code").input_value() == small
    assert page.get_by_role("button", name="Pay NOK 500").is_visible()  # nothing applied any more
    assert "Voucher" not in _rows(page)
    assert "reference" not in draft(page)  # nothing was booked
    a11y.check_axe(page)

    logs = stack.compose("logs", "--no-color").stdout
    for c in (whole, small):
        assert c not in logs and c.replace("-", "") not in logs, f"{c!r} is in the compose logs"


def test_the_quote_needs_a_session(page: Page, base_url, windows):
    open_session(page, base_url)
    window = windows[7]
    paid = book_in_browser(page, window, 1)
    assert paid["booking"]["paid"] == {"voucher_ore": 0, "card_ore": 25000}
    status, body = page.evaluate(
        """async () => {
             const r = await fetch('/api/vouchers/quote', {method: 'POST', credentials: 'omit',
               headers: {'Content-Type': 'application/json'},
               body: JSON.stringify({code: 'ABCD-EFGH-JKMN-PQRS', kind: 'seats', window_id: 1, seats: 1})});
             return [r.status, await r.json()];
           }""")
    assert status == 401 and body == {"detail": {"error": "no_session"}}, body


def test_a_stored_code_is_quoted_again_and_a_failed_check_keeps_the_input(page: Page, base_url, db, windows):
    page.set_viewport_size({"width": 1366, "height": 768})
    code = _voucher(page, base_url, windows[6], 1)  # NOK 250
    window = windows[7]

    # applied, then the page is reloaded: the code in the draft is quoted again
    _review(page, base_url, window, 2)
    _type_code(page, code)
    a11y.press(page, "Enter")
    page.get_by_role("button", name="Pay NOK 250").wait_for()
    page.reload()
    page.get_by_role("button", name="Pay NOK 250").wait_for()
    assert _rows(page)["Voucher"] == "−NOK 250"
    assert page.locator("#voucher-code").input_value() == code

    # a refusal at Pay (the Window filled around the API), then a nearest session: quoted again for it
    fill(db, window, seats_left(base_url, window) - 1)  # one Seat left, two requested
    a11y.tab_to(page, page.locator("#terms"))
    a11y.press(page, "Space")
    a11y.tab_to(page, page.get_by_role("button", name="Pay NOK 250"))
    a11y.press(page, "Enter")
    nearest = page.locator(".review > .notice .nearest a")
    nearest.first.wait_for()
    a11y.tab_to(page, nearest.first)
    a11y.press(page, "Enter")
    page.get_by_role("button", name="Pay NOK 250").wait_for()
    assert _rows(page)["Voucher"] == "−NOK 250" and _rows(page)["To pay by card"] == "NOK 250"
    assert draft(page)["window_id"] != window["id"] and draft(page)["voucher_code"] == code
    assert page.locator("#voucher-code").input_value() == code

    # the check fails (no session): a Field error only, the input kept, no Voucher applied
    page.context.clear_cookies()
    _type_code(page, code)
    a11y.tab_to(page, page.get_by_role("button", name="Apply voucher"))
    a11y.press(page, "Enter")
    page.locator("#voucher-code-error").wait_for()
    assert _norm(page.locator("#voucher-code-error").inner_text()) == \
        "The voucher could not be checked, please try again."
    assert page.locator("#voucher-code").input_value() == code
    assert page.locator(".error-summary").count() == 0
    assert "Voucher" not in _rows(page)
    assert page.get_by_role("button", name="Pay NOK 500").is_visible()
