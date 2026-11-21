"""Shared Administrator steps of the e2e layer (Stories 2.1 and 2.2): the seeded login, a fixture that keeps it from
being throttled, opening Sign-in and typing the login with the keyboard alone (through `a11y`)."""

from __future__ import annotations

import json
from pathlib import Path

import psycopg
import pytest
from playwright.sync_api import Page

from . import a11y

LOGIN = json.loads((Path(__file__).resolve().parents[2] / "seeds" / "admin.json").read_text(encoding="utf-8"))
SIGN_IN, BOOKINGS = "/admin/sign-in", "/admin/bookings"


def db_url(stack) -> str:
    """The stack's own database (compose project `booking_e2e`)."""
    return f"postgresql://postgres:booking@127.0.0.1:{stack.db_port}/booking"


@pytest.fixture(autouse=True)
def no_throttle(stack):
    """Each test starts and ends with no sign-in failures counted, so the seeded login is never locked. A test module
    that imports it gets it for every test."""
    url = db_url(stack)

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
