"""FR-4 / AD-25: the Seat flow never shows a Sauna. Every response a Guest's browser reads while booking Seats (the
Window listing, one Window, the booking, its repeat and the confirmation read) and the confirmation email are walked:
no key names a Sauna (apart from the one serializer's `sauna`, which is null for a Seat booking, AD-23) and no text
holds a Sauna's name. `GET /api/venue` is Landing's, not the Seat flow's: it lists the Saunas as places to visit
(FR-1.5). Story 5.2: the walk is repeated with a Whole-sauna booking in the same Window, and the Manage read of the
Seat booking is walked too; only the Whole-sauna booking's own responses name its Sauna. Story 5.4 (AD-25): no walked
response carries a `placement` key; Placement is read only under `/api/admin/`."""

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


def _null_sauna_keys(value, path="$"):
    """The paths of every `sauna` key whose value is null: the one serializer's field of a Seat booking (AD-23)."""
    if isinstance(value, dict):
        for k, v in value.items():
            if k == "sauna" and v is None:
                yield f"{path}.{k}"
            yield from _null_sauna_keys(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _null_sauna_keys(v, f"{path}[{i}]")


def assert_no_sauna(value) -> None:
    allowed = set(_null_sauna_keys(value))
    for path, kind, text in walk(value):
        if kind == "key" and path not in allowed:
            assert "sauna" not in text.lower(), path  # no `sauna_id`, `saunas`, or a `sauna` that is set
        if kind == "key":
            assert "placement" not in text.lower(), path  # Placement only under /api/admin/ (AD-25)
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


def test_with_a_whole_sauna_booking_present_the_seat_flow_still_names_no_sauna(api, world, pg):
    """AD-25, Story 5.2: Kajo is booked whole through the API in Window 1, then a Seat booking is made in the same
    Window. Every Seat-flow response, the Seat booking's Manage read and its email name no Sauna; the Whole-sauna
    booking's own response does (`kind = 'whole'`)."""
    from client import api_client
    from test_fr25_manage_link import TOKEN, open_link

    with api_client(world) as group:
        r = group.post("/api/bookings", json={"kind": "whole", "window_id": 1, "sauna_id": 3, "name": "Olav Group",
                                              "email": "olav@example.com"}, headers={"Idempotency-Key": str(uuid.uuid4())})
        assert r.status_code == 201, r.text
        assert r.json()["booking"]["sauna"] == {"id": 3, "name": "Kajo"}
        listing_whole = group.get("/api/private-saunas", params=dict(date="2026-12-01"))
        for named in (r, listing_whole):  # they name Saunas (kind = 'whole'), but carry no Placement (AD-25)
            assert named.status_code in (200, 201) and "placement" not in named.text, named.text
    key = str(uuid.uuid4())
    listing = api.get("/api/windows", params=dict(date="2026-12-01", seats=2))
    one = api.get("/api/windows/1")
    paid = api.book(1, 2, key=key)
    again = api.book(1, 2, key=key)
    ref = paid.json()["booking"]["reference"]
    confirmation = api.get(f"/api/bookings/{ref}/confirmation")
    assert open_link(api, TOKEN.search(paid.json()["emails"][0]["body"]).group(1)).status_code == 200
    manage = api.get(f"/api/manage/{ref}")
    for r in (listing, one, paid, again, confirmation, manage):
        assert r.status_code in (200, 201), r.text
        assert_no_sauna(r.json())
    body = pg.execute("SELECT subject || ' ' || body FROM outbox_emails o JOIN bookings b ON b.id = o.booking_id "
                      "WHERE b.reference = %s", (ref,)).fetchone()[0]
    pg.rollback()
    assert not NAMES.search(body), body


def test_the_walk_would_see_a_sauna_name():
    """The check bites: a Sauna name or key anywhere in a response fails it."""
    for bad in ({"windows": [{"note": "in Rauha"}]}, {"booking": {"sauna_id": 1}}, ["Kajo"],
                {"booking": {"sauna": {"id": 1, "name": "x"}}}, {"windows": [{"placement": []}]}):
        try:
            assert_no_sauna(bad)
        except AssertionError:
            continue
        raise AssertionError(f"not caught: {bad}")
