"""Shared Guest steps of the e2e layer: a date with no Booking at all, a browser session as Book seats opens it, and
a payment made from the page with its session cookie."""

from __future__ import annotations

import uuid

import httpx
from playwright.sync_api import Page

from . import trust


def free_windows(base_url: str) -> list[dict]:
    """The eight Windows of a date with no Booking at all (so none of the sample Bookings): the latest date first."""
    facts = httpx.get(base_url + "/api/windows", timeout=30, verify=trust.context()).json()
    for d in reversed(facts["dates"][:-3]):  # the last dates are Book seats' no-room fixtures
        ws = httpx.get(base_url + "/api/windows", params=dict(date=d), timeout=30,
                       verify=trust.context()).json()["windows"]
        if len(ws) == 8 and all(w["seats_left"] == 44 for w in ws):
            return [dict(w, date=d) for w in ws]
    raise AssertionError("no date without bookings")


def open_session(page: Page, base_url: str) -> None:
    """A browser session as Book seats opens it (the one place that sets the cookie)."""
    page.goto(base_url + "/book-seats")
    page.wait_for_selector(".cal-grid")
    page.wait_for_load_state("networkidle")


def book_in_browser(page: Page, window: dict, seats: int, name: str = "Ingrid Hansen") -> dict:
    """Pay through the API from the page, with its session cookie (as Review does). Returns the response body."""
    status, body = page.evaluate(
        """async ({body, key}) => {
             const r = await fetch('/api/bookings', {method: 'POST', credentials: 'same-origin',
               headers: {'Content-Type': 'application/json', 'Idempotency-Key': key}, body: JSON.stringify(body)});
             return [r.status, await r.json()];
           }""",
        {"body": {"window_id": window["id"], "seats": seats, "name": name, "email": "ingrid@example.com"},
         "key": str(uuid.uuid4())})
    assert status == 201, body
    return body
