"""FR-4 / AD-25: the Seat flow never shows a Sauna. Every response a Guest's browser reads while booking Seats (the
Window listing, one Window, the booking, its repeat and the confirmation read) and the confirmation email are walked:
no key names a Sauna and no text holds a Sauna's name. `GET /api/venue` is Landing's, not the Seat flow's: it lists
the Saunas as places to visit (FR-1.5)."""

from __future__ import annotations

import re
import uuid

from conftest import SAUNAS

NAMES = re.compile(r"\b(" + "|".join([n for _, n, _ in SAUNAS] + ["Löyly"]) + r")\b")


def walk(value, path="$"):
    """Yield (path, kind, text) for every key ("key") and every string ("text") in a JSON value."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield f"{path}.{k}", "key", k
            yield from walk(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk(v, f"{path}[{i}]")
    elif isinstance(value, str):
        yield path, "text", value


def assert_no_sauna(value) -> None:
    for path, kind, text in walk(value):
        if kind == "key":
            assert "sauna" not in text.lower(), path  # no `sauna_id`, `saunas`, `sauna`
        assert not NAMES.search(text), (path, text)


def test_no_seat_flow_response_or_email_names_a_sauna(api, pg):
    key = str(uuid.uuid4())
    listing = api.get("/api/windows", params=dict(date="2026-12-01", seats=2))
    one = api.get("/api/windows/1")
    paid = api.book(1, 2, key=key)
    again = api.book(1, 2, key=key)
    ref = paid.json()["booking"]["reference"]
    confirmation = api.get(f"/api/bookings/{ref}/confirmation")
    for r in (listing, one, paid, again, confirmation):
        assert r.status_code in (200, 201), r.text
        assert_no_sauna(r.json())
    body = pg.execute("SELECT subject || ' ' || body FROM outbox_emails").fetchone()[0]
    pg.rollback()
    assert not NAMES.search(body), body
    assert "sauna_id" not in body.lower()


def test_the_walk_would_see_a_sauna_name():
    """The check bites: a Sauna name or key anywhere in a response fails it."""
    for bad in ({"windows": [{"note": "in Rauha"}]}, {"booking": {"sauna_id": 1}}, ["Kajo"]):
        try:
            assert_no_sauna(bad)
        except AssertionError:
            continue
        raise AssertionError(f"not caught: {bad}")
