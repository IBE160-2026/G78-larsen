"""FR-21 on every Guest page: every request goes to the stack's own origin (no third party, fonts included), and each
page loads exactly one stylesheet of ours and no <style> element. No cookie is set, except on Book seats and on the
Administrator's Sign-in, which each set exactly one: the session cookie (AD-8). Other Administrator pages open no
session (Story 2.1). Details, Review and Confirmation (Story 1.5) keep that one cookie, and a name
with a script tag is shown as text on Review and Confirmation, never run (FR-18 IV-5).

Story 2.4 adds the Administrator pages: an anonymous visit to each Administrator address goes to Sign-in; Sign-in,
Booking list and Outbox keep every request on the origin, one cookie and one stylesheet of ours; and after a Booking,
a sign-in and a sign-out the compose logs hold neither the test password, nor a session token, nor the request body
(AD-19).

Story 4.1 adds the Manage page: opening a Manage link keeps every request on the origin with one cookie and one
stylesheet of ours, and the issued Manage token, opened in the browser, never reaches the compose logs (AD-19).

Story 5.1 adds the Private sauna page to the pages that set no cookie; with a date chosen, every request stays on the
origin too (tests/e2e/test_fr30_private_sauna.py).

Story 5.2 adds the Private sauna flow's Details and Review (`/private-sauna/details`, `/private-sauna/review`) and the
Confirmation of a Whole-sauna booking: each keeps every request on the origin, the one session cookie and one
stylesheet of ours, and a name with a script tag is text on its Review and Confirmation."""

from __future__ import annotations

import json
import re
import secrets
import uuid

import httpx
import pytest
from playwright.sync_api import Page

from .admin import LOGIN, SIGN_IN, no_throttle, open_sign_in, type_login  # noqa: F401 (fixture)
from .test_fr05_book_and_pay import book_in_browser, free_windows, open_session, review_draft, set_draft
from .test_fr25_manage import open_manage_link
from . import trust

MANAGE_TOKEN = re.compile(r"/manage#t=([A-Za-z0-9_-]{43})$", re.M)

SCRIPT_NAME = "<script>window.__pwned = 1</script><b>Bold</b>"

PAGES = ["/", "/#before-you-come", "/terms", "/privacy", "/nope", "/private-sauna"]  # Private sauna: Story 5.1
BOOK_SEATS = "/book-seats"


@pytest.mark.parametrize("path", PAGES)
def test_every_request_goes_to_the_stack_origin_and_no_cookie_is_set(page: Page, base_url, path):
    requests = []
    responses = []
    page.on("request", lambda r: requests.append(r.url))
    page.on("response", lambda r: responses.append(r))
    page.goto(base_url + path)
    page.wait_for_load_state("networkidle")
    page.evaluate("document.fonts.ready")
    # `Response.headers` omits cookie headers; `header_value` reads the raw ones
    set_cookies = [r.url for r in responses if r.header_value("set-cookie")]

    assert requests, "no request was recorded"
    others = [u for u in requests if not (u == base_url or u.startswith(base_url + "/"))]
    assert not others, f"requests to another origin: {others}"
    assert any(u.endswith(".woff2") for u in requests), "the self-hosted fonts were not loaded"
    assert not set_cookies, f"Set-Cookie on {set_cookies}"
    assert page.context.cookies() == []


def test_book_seats_sets_exactly_one_session_cookie_and_every_request_goes_to_the_stack_origin(page: Page, base_url):
    requests = []
    page.on("request", lambda r: requests.append(r.url))
    page.goto(base_url + BOOK_SEATS)
    page.wait_for_selector(".cal-grid")
    page.wait_for_load_state("networkidle")
    others = [u for u in requests if not (u == base_url or u.startswith(base_url + "/"))]
    assert not others, f"requests to another origin: {others}"
    assert sum(1 for u in requests if u == base_url + "/api/session") == 1
    cookies = page.context.cookies()
    assert [c["name"] for c in cookies] == ["bp_session"], cookies
    assert cookies[0]["httpOnly"] and cookies[0]["sameSite"] == "Strict" and cookies[0]["path"] == "/"
    page.reload()
    page.wait_for_selector(".cal-grid")
    page.wait_for_load_state("networkidle")
    assert [c["name"] for c in page.context.cookies()] == ["bp_session"]  # the existing session is kept


def test_an_administrator_page_opens_no_session(page: Page, base_url):
    """`/admin/bookings` with its guard's `GET /api/admin/me` held unanswered: no `POST /api/session`, no cookie."""
    posts = []
    page.on("request", lambda r: posts.append(r.url) if r.method == "POST" else None)
    page.route("**/api/admin/me", lambda route: None)  # never answered
    page.goto(base_url + "/admin/bookings")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1000)
    assert not [u for u in posts if u.endswith("/api/session")], posts
    assert page.context.cookies() == []


@pytest.mark.parametrize("path", PAGES + [BOOK_SEATS])
def test_exactly_one_stylesheet_and_no_style_element(page: Page, base_url, path):
    page.goto(base_url + path)
    page.wait_for_load_state("networkidle")
    sheets = page.evaluate("""() => Array.from(document.styleSheets).map(s => ({
        href: s.href, owner: s.ownerNode ? s.ownerNode.tagName.toLowerCase() : null}))""")
    assert len(sheets) == 1, sheets
    assert sheets[0]["owner"] == "link" and sheets[0]["href"].startswith(base_url + "/"), sheets
    assert page.locator("style").count() == 0
    # no style props in our markup (Next.js's own route announcer carries one, outside the shell)
    assert page.locator(".shell [style], .shell[style]").count() == 0


def _paid_pages(page: Page, base_url: str, name: str = "Ingrid Hansen") -> dict[str, str]:
    """Open a session, pay for one Seat as `name`, and return the addresses of Details, Review and Confirmation, with a
    draft in the tab that opens Details and Review (for a second Booking)."""
    window = free_windows(base_url)[-1]
    open_session(page, base_url)
    reference = book_in_browser(page, window, 1, name)["booking"]["reference"]
    set_draft(page, review_draft(window, 1, name))
    return {"details": "/book-seats/details", "review": "/book-seats/review", "confirmation": f"/confirmation/{reference}"}


@pytest.mark.parametrize("which", ["details", "review", "confirmation"])
def test_the_booking_pages_stay_on_the_origin_with_one_cookie_and_one_stylesheet(page: Page, base_url, which):
    path = _paid_pages(page, base_url)[which]
    requests = []
    page.on("request", lambda r: requests.append(r.url))
    page.goto(base_url + path)
    page.wait_for_selector("#name" if which == "details" else ".summary")
    page.wait_for_load_state("networkidle")
    others = [u for u in requests if not (u == base_url or u.startswith(base_url + "/"))]
    assert not others, f"requests to another origin: {others}"
    assert [c["name"] for c in page.context.cookies()] == ["bp_session"]
    sheets = page.evaluate("() => Array.from(document.styleSheets).map(s => s.href)")
    assert len(sheets) == 1 and sheets[0].startswith(base_url + "/"), sheets
    assert page.locator("style").count() == 0
    assert page.locator(".shell [style], .shell[style]").count() == 0


def _rauha_twice(base_url: str) -> tuple[str, dict]:
    """A later date on which Rauha can still be booked whole in at least two sessions, preferring a date that already
    has a Booking, so that the dates other modules need free (`free_windows`) are left alone. Returns (date, Rauha as
    the listing shows it)."""
    get = lambda path, **params: httpx.get(base_url + path, params=params, timeout=30,  # noqa: E731
                                           verify=trust.context()).json()
    facts = get("/api/windows")
    candidates = [d for d in reversed(facts["dates"][:-3]) if d > facts["today"]]
    fallback = None
    for d in candidates:
        rauha = next((s for s in get("/api/private-saunas", date=d)["saunas"] if s["id"] == 1), None)
        if rauha is None or len(rauha["windows"]) < 2:
            continue
        if any(w["seats_left"] != 44 for w in get("/api/windows", date=d)["windows"]):
            return d, rauha
        fallback = fallback or (d, rauha)
    assert fallback, "no date on which Rauha can be booked whole twice"
    return fallback


def _whole_paid_pages(page: Page, base_url: str, name: str = "Olav Berg") -> dict[str, str]:
    """Open a session, pay for Rauha whole in the last session of a free date as `name` (Story 5.2), and return the
    addresses of the Private sauna Details and Review and the Confirmation, with a `draft:whole` in the tab that opens
    Details and Review for another pair (Rauha, the first session of that date)."""
    date, rauha = _rauha_twice(base_url)
    open_session(page, base_url)
    status, body = page.evaluate(
        """async ({body, key}) => {
             const r = await fetch('/api/bookings', {method: 'POST', credentials: 'same-origin',
               headers: {'Content-Type': 'application/json', 'Idempotency-Key': key}, body: JSON.stringify(body)});
             return [r.status, await r.json()];
           }""",
        {"body": {"kind": "whole", "window_id": rauha["windows"][-1]["id"], "sauna_id": rauha["id"], "name": name,
                  "email": "olav@example.com"}, "key": str(uuid.uuid4())})
    assert status == 201, body
    page.evaluate("d => sessionStorage.setItem('draft:whole', JSON.stringify(d))",
                  {"date": date, "window_id": rauha["windows"][0]["id"], "sauna_id": rauha["id"],
                   "sauna_name": rauha["name"], "whole_price_ore": rauha["whole_price_ore"], "name": name,
                   "email": "olav@example.com"})
    return {"details": "/private-sauna/details", "review": "/private-sauna/review",
            "confirmation": f"/confirmation/{body['booking']['reference']}"}


@pytest.mark.parametrize("which", ["details", "review", "confirmation"])
def test_the_private_sauna_pages_stay_on_the_origin_with_one_cookie_and_one_stylesheet(page: Page, base_url, which):
    """Story 5.2: the Private sauna flow's Details and Review and a Whole-sauna booking's Confirmation."""
    path = _whole_paid_pages(page, base_url)[which]
    requests = []
    page.on("request", lambda r: requests.append(r.url))
    page.goto(base_url + path)
    page.wait_for_selector("#name" if which == "details" else ".summary")
    page.wait_for_load_state("networkidle")
    others = [u for u in requests if not (u == base_url or u.startswith(base_url + "/"))]
    assert not others, f"requests to another origin: {others}"
    assert [c["name"] for c in page.context.cookies()] == ["bp_session"]
    sheets = page.evaluate("() => Array.from(document.styleSheets).map(s => s.href)")
    assert len(sheets) == 1 and sheets[0].startswith(base_url + "/"), sheets
    assert page.locator("style").count() == 0
    assert page.locator(".shell [style], .shell[style]").count() == 0


def test_a_name_with_a_script_tag_is_text_on_the_private_sauna_review_and_confirmation(page: Page, base_url):
    pages = _whole_paid_pages(page, base_url, SCRIPT_NAME)
    page.goto(base_url + pages["review"])
    row = page.locator(".summary-row", has=page.locator("dt", has_text="Name"))
    row.wait_for()
    assert row.locator("dd").inner_text() == SCRIPT_NAME
    assert page.locator(".summary b, .summary script").count() == 0
    page.goto(base_url + pages["confirmation"])
    page.wait_for_selector(".email-body")
    assert page.locator("main script, main b").count() == 0
    assert page.evaluate("() => window.__pwned") is None


def test_a_name_with_a_script_tag_is_text_on_review_and_confirmation(page: Page, base_url):
    pages = _paid_pages(page, base_url, SCRIPT_NAME)
    page.goto(base_url + pages["review"])
    row = page.locator(".summary-row", has=page.locator("dt", has_text="Name"))
    row.wait_for()
    assert row.locator("dd").inner_text() == SCRIPT_NAME
    assert page.locator(".summary b, .summary script").count() == 0
    page.goto(base_url + pages["confirmation"])
    page.wait_for_selector(".email-body")
    # Confirmation's summary has no name row; the name reaches it only as the API's JSON, never as markup
    assert page.locator("main script, main b").count() == 0
    assert page.evaluate("() => window.__pwned") is None


def test_the_manage_page_stays_on_the_origin_with_one_cookie_and_one_stylesheet(page: Page, base_url):
    """Story 4.1: the Manage link of a new Booking, opened in the paying browser."""
    window = free_windows(base_url)[-1]
    open_session(page, base_url)
    paid = book_in_browser(page, window, 1)
    link = re.search(r"(?m)^(https://\S+/manage#t=[A-Za-z0-9_-]{43})$", paid["emails"][0]["body"]).group(1)
    requests = []
    page.on("request", lambda r: requests.append(r.url))
    open_manage_link(page, base_url, link)
    page.wait_for_load_state("networkidle")
    page.evaluate("document.fonts.ready")
    others = [u for u in requests if not (u == base_url or u.startswith(base_url + "/"))]
    assert not others, f"requests to another origin: {others}"
    assert [c["name"] for c in page.context.cookies()] == ["bp_session"]
    sheets = page.evaluate("() => Array.from(document.styleSheets).map(s => s.href)")
    assert len(sheets) == 1 and sheets[0].startswith(base_url + "/"), sheets
    assert page.locator("style").count() == 0
    assert page.locator(".shell [style], .shell[style]").count() == 0


# --- The Administrator pages (Story 2.4) ----------------------------------------------------------------------------

ADMIN_PAGES = ["/admin", "/admin/bookings", "/admin/outbox"]


def _other_origins(base_url: str, urls: list[str]) -> list[str]:
    return [u for u in urls if not (u == base_url or u.startswith(base_url + "/"))]


def _one_stylesheet_of_ours(page: Page, base_url: str) -> None:
    sheets = page.evaluate("() => Array.from(document.styleSheets).map(s => s.href)")
    assert len(sheets) == 1 and (sheets[0] or "").startswith(base_url + "/"), sheets
    assert page.locator("style").count() == 0


def _session_token(page: Page) -> str:
    return next(c["value"] for c in page.context.cookies() if c["name"] == "bp_session")


@pytest.mark.parametrize("path", ADMIN_PAGES)
def test_an_anonymous_visit_to_an_administrator_address_goes_to_sign_in(page: Page, base_url, path):
    page.goto(base_url + path)
    page.wait_for_url(base_url + SIGN_IN)
    page.wait_for_selector("#password")


def test_sign_in_booking_list_and_outbox_stay_on_the_origin_with_one_cookie_and_one_stylesheet(page: Page, base_url):
    requests = []
    page.on("request", lambda r: requests.append(r.url))
    open_sign_in(page, base_url)
    assert [c["name"] for c in page.context.cookies()] == ["bp_session"]  # Sign-in sets exactly one
    _one_stylesheet_of_ours(page, base_url)

    type_login(page, LOGIN["password"])
    page.wait_for_url(base_url + "/admin/bookings")
    page.locator("#date").wait_for()
    page.wait_for_load_state("networkidle")
    _one_stylesheet_of_ours(page, base_url)

    page.goto(base_url + "/admin/outbox")
    page.locator(".outbox-entry").first.wait_for()
    page.wait_for_load_state("networkidle")
    _one_stylesheet_of_ours(page, base_url)

    assert [c["name"] for c in page.context.cookies()] == ["bp_session"]
    assert requests, "no request was recorded"
    others = _other_origins(base_url, requests)
    assert not others, f"requests to another origin: {others}"


def test_the_password_tokens_and_request_bodies_never_reach_the_logs(page: Page, base_url, stack):
    """A Guest books from the browser and sends one refused booking body; then the Administrator is refused once with a
    wrong password, signs in and signs out in the same browser. The compose logs of the whole e2e stack hold none of
    the passwords, session tokens, idempotency keys or request bodies (AD-19, FR-21)."""
    marker = secrets.token_hex(8)
    name, email = f"Logcheck {marker}", f"logcheck-{marker}@example.com"
    wrong_password = f"wrong-password-{marker}"
    window = free_windows(base_url)[-1]
    tokens, keys = set(), [str(uuid.uuid4()), str(uuid.uuid4())]
    post = """async ({body, key}) => {
                const r = await fetch('/api/bookings', {method: 'POST', credentials: 'same-origin',
                  headers: {'Content-Type': 'application/json', 'Idempotency-Key': key}, body});
                return [r.status, await r.json()];
              }"""

    open_session(page, base_url)
    tokens.add(_session_token(page))
    body = json.dumps({"window_id": window["id"], "seats": 1, "name": name, "email": email})
    status, paid = page.evaluate(post, {"body": body, "key": keys[0]})
    assert status == 201, paid
    refused = json.dumps({"window_id": window["id"], "seats": 0, "name": f"Refused {marker}",
                          "email": f"refused-{marker}@example.com"})
    assert page.evaluate(post, {"body": refused, "key": keys[1]})[0] == 422
    # the issued Manage token, opened in this browser (Story 4.1)
    manage_token = MANAGE_TOKEN.search(paid["emails"][0]["body"]).group(1)
    open_manage_link(page, base_url, f"{base_url}/manage#t={manage_token}")

    open_sign_in(page, base_url)
    tokens.add(_session_token(page))
    type_login(page, wrong_password)
    page.locator("[data-error-summary]").wait_for()
    open_sign_in(page, base_url)
    type_login(page, LOGIN["password"])
    page.wait_for_url(base_url + "/admin/bookings")
    page.locator("#date").wait_for()
    tokens.add(_session_token(page))
    page.get_by_role("navigation", name="Administrator").get_by_role("button", name="Sign out").click()
    page.wait_for_url(base_url + SIGN_IN)
    page.wait_for_load_state("networkidle")
    tokens.update(c["value"] for c in page.context.cookies() if c["name"] == "bp_session")

    logs = stack.compose("logs", "--no-color").stdout
    assert "POST /api/bookings" in logs and "POST /api/admin/sign-in" in logs  # the access log is on
    assert "POST /api/manage/open" in logs and "GET /api/manage/" in logs
    for secret in (LOGIN["password"], wrong_password, *tokens, *keys, marker, body, refused, manage_token):
        assert secret not in logs, f"{secret!r} is in the compose logs"
