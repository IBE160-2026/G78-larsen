"""Sign-in and sign-out in the browser (FR-15, FR-21, FR-22, FR-23, UX-DR3, UX-DR30, UX-DR33), against the whole stack.

- The Administrator signs in and out with the keyboard alone (every key through `a11y.press` / `a11y.tab_to`): Sign-in
  shows the bar with the name only, then the heading, Email, Password and "Sign in"; the Booking list shows the bar
  with Booking list, Outbox and Sign out and has focus on its heading; Sign out leads back to Sign-in, and so does the
  browser's Back.
- A wrong password shows the Error summary "Wrong email or password" with no Field error, and the title starts with
  "Error: ".
- An anonymous visit to `/admin/bookings` (or `/admin`) renders nothing of the page and lands on Sign-in.
- axe reports no A or AA failure on Sign-in (also with the Error summary) and the Booking list, and neither scrolls
  sideways at 1024, 1366 or 1920 px.
- Neither the test password nor the session token appears in `docker compose -p booking_e2e logs`.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import psycopg
import pytest
from playwright.sync_api import Page

from . import a11y

LOGIN = json.loads((Path(__file__).resolve().parents[2] / "seeds" / "admin.json").read_text(encoding="utf-8"))
SIGN_IN, BOOKINGS = "/admin/sign-in", "/admin/bookings"


@pytest.fixture(autouse=True)
def no_throttle(stack):
    """Each test starts and ends with no sign-in failures counted, so the seeded login is never locked."""
    url = f"postgresql://postgres:booking@127.0.0.1:{stack.db_port}/booking"

    def clear():
        with psycopg.connect(url) as c:
            c.execute("DELETE FROM sign_in_throttle")

    clear()
    yield
    clear()


def open_sign_in(page: Page, base_url: str) -> None:
    page.goto(base_url + SIGN_IN)
    page.wait_for_selector("#password")
    page.wait_for_load_state("networkidle")  # the page's `POST /api/session` has answered


def type_login(page: Page, password: str) -> None:
    a11y.tab_to(page, page.locator("#email"))
    page.keyboard.type(LOGIN["email"])
    a11y.tab_to(page, page.locator("#password"))
    page.keyboard.type(password)
    a11y.tab_to(page, page.get_by_role("button", name="Sign in"))
    a11y.press(page, "Enter")


def test_sign_in_and_out_with_the_keyboard_alone(page: Page, base_url):
    open_sign_in(page, base_url)
    assert page.title() == "Sign in – Saunalöyly"
    bar = page.locator("header.admin-bar")
    assert bar.inner_text().strip() == "Saunalöyly"  # the name only
    order = page.evaluate("""() => Array.from(document.querySelectorAll(
        'header.admin-bar, h1, label[for=email], label[for=password], button[type=submit]'))
        .map(e => e.tagName.toLowerCase() + ':' + e.textContent.trim())""")
    assert order == ["header:Saunalöyly", "h1:Sign in", "label:Email", "label:Password", "button:Sign in"]
    assert [c["name"] for c in page.context.cookies()] == ["bp_session"]
    guest_token = page.context.cookies()[0]["value"]

    type_login(page, LOGIN["password"])
    page.wait_for_url(base_url + BOOKINGS)
    heading = page.get_by_role("heading", level=1, name="Booking list")
    heading.wait_for()
    page.wait_for_function("document.activeElement && document.activeElement.tagName === 'H1'")
    assert page.title() == "Booking list – Saunalöyly"
    nav = page.get_by_role("navigation", name="Administrator")
    assert [x.strip() for x in nav.locator("a, button").all_inner_texts()] == ["Booking list", "Outbox", "Sign out"]
    assert nav.get_by_role("link", name="Booking list").get_attribute("aria-current") == "page"
    admin_token = page.context.cookies()[0]["value"]
    assert admin_token != guest_token  # rotated at sign-in

    # focus is on the heading, the last stop of the page for now; Sign out is the stop before it
    a11y.press(page, "Shift+Tab")
    assert nav.get_by_role("button", name="Sign out").evaluate("el => el === document.activeElement")
    a11y.press(page, "Enter")
    page.wait_for_url(base_url + SIGN_IN)
    page.wait_for_selector("#password")
    assert page.context.cookies() == [] or page.context.cookies()[0]["value"] != admin_token

    # the old token grants nothing
    r = httpx.get(base_url + "/api/admin/me", cookies={"bp_session": admin_token})
    assert r.status_code == 401 and r.json() == {"detail": {"error": "not_signed_in"}}

    # Back leads to Sign-in, too
    page.go_back()
    page.wait_for_url(base_url + SIGN_IN)
    page.wait_for_selector("#password")
    assert page.get_by_role("heading", level=1).inner_text() == "Sign in"
    page.goto(base_url + BOOKINGS)
    page.wait_for_url(base_url + SIGN_IN)


def test_a_wrong_password_shows_the_error_summary_and_the_error_title(page: Page, base_url):
    open_sign_in(page, base_url)
    type_login(page, "not the right password")
    summary = page.locator("[data-error-summary]")
    summary.wait_for()
    assert summary.inner_text().strip() == "Wrong email or password"
    page.wait_for_function("document.title === 'Error: Sign in – Saunalöyly'")
    assert page.locator(".field-error").count() == 0
    assert page.locator("[aria-invalid]").count() == 0
    assert page.evaluate("document.activeElement.hasAttribute('data-error-summary')")
    a11y.check_axe(page)
    assert page.url == base_url + SIGN_IN


def test_a_lost_session_is_reopened_and_the_sign_in_retried_once(page: Page, base_url, stack):
    """Matrix row "No session": the page's session is gone when Sign in is pressed, so the first attempt answers
    `401 no_session`; the page opens a new session, tries once more and lands on the Booking list."""
    open_sign_in(page, base_url)
    with psycopg.connect(f"postgresql://postgres:booking@127.0.0.1:{stack.db_port}/booking") as c:
        c.execute("DELETE FROM sessions")
    calls = []
    page.on("request", lambda req: calls.append(req.url.removeprefix(base_url))
            if req.method == "POST" and "/api/" in req.url else None)
    type_login(page, LOGIN["password"])
    page.wait_for_url(base_url + BOOKINGS)
    page.get_by_role("heading", level=1, name="Booking list").wait_for()
    assert calls == ["/api/admin/sign-in", "/api/session", "/api/admin/sign-in"]


@pytest.mark.parametrize("path", [BOOKINGS, "/admin"])
def test_an_anonymous_visitor_is_sent_to_sign_in_and_shown_nothing_else(page: Page, base_url, path):
    page.goto(base_url + path)
    page.wait_for_url(base_url + SIGN_IN)
    page.wait_for_selector("#password")
    assert page.get_by_role("navigation", name="Administrator").count() == 0
    assert page.get_by_text("Booking list").count() == 0


def test_the_booking_list_renders_nothing_before_the_guard_answers(page: Page, base_url):
    page.route("**/api/admin/me", lambda route: None)  # never answered
    page.goto(base_url + BOOKINGS)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(500)
    assert page.locator("h1").count() == 0 and page.locator("header.admin-bar").count() == 0


def test_sign_in_and_the_booking_list_pass_axe_and_fit_every_width(page: Page, base_url):
    open_sign_in(page, base_url)
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)
    page.fill("#email", LOGIN["email"])
    page.fill("#password", LOGIN["password"])
    page.get_by_role("button", name="Sign in").click()
    page.get_by_role("heading", level=1, name="Booking list").wait_for()
    a11y.check_axe(page)
    a11y.no_horizontal_scroll(page)


def test_the_password_and_the_token_never_reach_the_logs(page: Page, base_url, stack):
    open_sign_in(page, base_url)
    page.fill("#email", LOGIN["email"])
    page.fill("#password", LOGIN["password"])
    page.get_by_role("button", name="Sign in").click()
    page.get_by_role("heading", level=1, name="Booking list").wait_for()
    token = page.context.cookies()[0]["value"]
    logs = stack.compose("logs", "--no-color").stdout
    assert "POST /api/admin/sign-in" in logs  # the right logs: the access log is on
    assert LOGIN["password"] not in logs
    assert token not in logs


def sign_in_with_mouse(page: Page, base_url: str) -> None:
    open_sign_in(page, base_url)
    page.fill("#email", LOGIN["email"])
    page.fill("#password", LOGIN["password"])
    page.get_by_role("button", name="Sign in").click()
    page.get_by_role("heading", level=1, name="Booking list").wait_for()


def test_sign_in_when_already_signed_in_goes_to_the_booking_list(page: Page, base_url):
    sign_in_with_mouse(page, base_url)
    page.goto(base_url + SIGN_IN)
    page.wait_for_url(base_url + BOOKINGS)
    page.get_by_role("heading", level=1, name="Booking list").wait_for()


def test_an_outage_at_sign_in_shows_the_notice_and_no_error_summary(page: Page, base_url):
    page.route("**/api/admin/sign-in", lambda route: route.fulfill(
        status=503, content_type="application/json", body='{"detail": {"error": "try_again"}}'))
    open_sign_in(page, base_url)
    page.fill("#email", LOGIN["email"])
    page.fill("#password", LOGIN["password"])
    page.get_by_role("button", name="Sign in").click()
    notice = page.locator(".notice")
    notice.wait_for()
    assert notice.inner_text().strip() == "Sign-in could not be completed, please try again."
    assert page.locator("[data-error-summary]").count() == 0
    assert page.title() == "Sign in – Saunalöyly"
    assert page.url == base_url + SIGN_IN


def test_a_failed_sign_out_keeps_the_booking_list_and_shows_a_notice(page: Page, base_url):
    sign_in_with_mouse(page, base_url)
    page.route("**/api/admin/sign-out", lambda route: route.fulfill(
        status=500, content_type="application/json", body='{"detail": {"error": "internal_error"}}'))
    page.get_by_role("button", name="Sign out").click()
    notice = page.locator(".notice")
    notice.wait_for()
    assert notice.inner_text().strip() == "Sign-out could not be completed, please try again."
    assert page.url == base_url + BOOKINGS
    assert page.get_by_role("heading", level=1, name="Booking list").is_visible()
