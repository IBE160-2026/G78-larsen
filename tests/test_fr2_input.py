"""FR-2 / FR-18 (Conventions: Input): request shapes are checked by Pydantic before anything runs. Seats are an
integer from 1 to 10, unknown fields are refused, and a shape error is `422 invalid_input` with `fields`."""

from __future__ import annotations

import datetime as dt

import pytest

from client import GUEST, new_key
from conftest import win_start


def post(c, path: str, body: dict):
    """Each path in its own request shape: a booking also carries the Guest's name and email and an
    `Idempotency-Key` (Story 1.5), so the shape error under test is the only one."""
    if path == "/api/bookings":
        return c.post(path, json={**GUEST, **body}, headers=new_key())
    return c.post(path, json=body)


def written(pg) -> tuple:
    pg.rollback()
    row = pg.execute("SELECT (SELECT count(*) FROM holds), (SELECT count(*) FROM bookings), "
                     "(SELECT count(*) FROM blocks), (SELECT count(*) FROM marks)").fetchone()
    pg.rollback()
    return tuple(row)


@pytest.mark.parametrize("path", ["/api/holds", "/api/bookings"])
@pytest.mark.parametrize("body,fields", [
    (dict(window_id=1, seats=0), ["seats"]),
    (dict(window_id=1, seats=11), ["seats"]),
    (dict(window_id=1, seats=-3), ["seats"]),
    (dict(window_id=1, seats=2.5), ["seats"]),
    (dict(window_id=1), ["seats"]),
    (dict(window_id=1, seats=2, session_id="mine"), ["session_id"]),  # the slice's client-chosen id is gone
    (dict(window_id=1, seats=2, extra=True), ["extra"]),
], ids=["zero", "eleven", "negative", "fraction", "missing", "session_id", "extra"])
def test_seats_outside_1_to_10_and_unknown_fields_are_422(api, pg, path, body, fields):
    r = post(api, path, body)
    assert r.status_code == 422, r.text
    assert r.json() == {"detail": {"error": "invalid_input", "fields": fields}}
    assert written(pg) == (0, 0, 0, 0)


@pytest.mark.parametrize("seats", [1, 10])
def test_the_edges_1_and_10_are_accepted(api, seats):
    assert api.book(1, seats).status_code == 201


def test_malformed_json_and_a_missing_body_are_422(api, pg):
    r = api.post("/api/holds", content=b"{not json", headers={"content-type": "application/json"})
    assert r.status_code == 422 and r.json()["detail"]["error"] == "invalid_input"
    r = api.post("/api/holds")
    assert r.status_code == 422 and r.json()["detail"]["error"] == "invalid_input"
    r = api.post("/api/session", json={"role": "admin"})  # the session endpoint takes an empty object only
    assert r.status_code == 422 and r.json()["detail"]["fields"] == ["role"]
    assert written(pg) == (0, 0, 0, 0)


def test_an_empty_block_period_is_422(admin, pg):
    st = win_start(0)
    for end in (st, st - dt.timedelta(minutes=1)):
        r = admin.post("/api/admin/blocks", json=dict(sauna_id=1, start=st.isoformat(), end=end.isoformat()))
        assert r.status_code == 422 and r.json() == {"detail": {"error": "invalid_input", "fields": ["end"]}}, r.text
    r = admin.post("/api/admin/marks", json=dict(window_id=1, sauna_id=4, note="x"))
    assert r.status_code == 422 and r.json()["detail"]["fields"] == ["note"]
    assert written(pg) == (0, 0, 0, 0)


def test_a_query_parameter_of_the_wrong_type_is_422(api):
    r = api.delete("/api/holds", params=dict(window_id="one"))
    assert r.status_code == 422 and r.json() == {"detail": {"error": "invalid_input", "fields": ["window_id"]}}


@pytest.mark.parametrize("path,body,fields", [
    ("/api/holds", dict(window_id=2**31, seats=1), ["window_id"]),
    ("/api/bookings", dict(window_id=0, seats=1), ["window_id"]),
    ("/api/admin/marks", dict(window_id=1, sauna_id=2**31), ["sauna_id"]),
    # the slice's `/api/admin/whole-bookings` entry, reshaped as the Whole-sauna booking (Story 5.2, AD-21)
    ("/api/bookings", dict(kind="whole", window_id=2**63, sauna_id=1), ["window_id"]),
    ("/api/bookings", dict(kind="whole", window_id=1, sauna_id=2**31), ["sauna_id"]),
])
def test_an_id_outside_int4_is_422(api, admin, pg, path, body, fields):
    c = admin if path.startswith("/api/admin/") else api
    r = post(c, path, body)
    assert r.status_code == 422 and r.json() == {"detail": {"error": "invalid_input", "fields": fields}}, r.text
    assert written(pg) == (0, 0, 0, 0)


def test_a_booking_deadline_outside_int4_is_422(admin):
    r = admin.put("/api/admin/settings", json=dict(release_on=True, release_time="06:00",
                                                   booking_deadline_minutes=-2**31))
    assert r.status_code == 422 and r.json()["detail"]["fields"] == ["booking_deadline_minutes"]


@pytest.mark.parametrize("start,end,fields", [
    ("2026-12-01T09:00:00", "2026-12-01T10:30:00+00:00", ["start"]),  # naive and aware mixed
    ("2026-12-01T09:00:00+00:00", "2026-12-01T10:30:00", ["end"]),
    ("2026-12-01T09:00:00", "2026-12-01T10:30:00", ["end", "start"]),  # both naive
])
def test_block_times_need_an_offset(admin, pg, start, end, fields):
    r = admin.post("/api/admin/blocks", json=dict(sauna_id=1, start=start, end=end))
    assert r.status_code == 422 and r.json() == {"detail": {"error": "invalid_input", "fields": fields}}, r.text
    assert written(pg) == (0, 0, 0, 0)


def test_an_undecodable_body_is_422(api, pg):
    body = b'{"window_id": 1, "seats": "' + bytes([0xFF, 0xFE]) + b'"}'  # not valid UTF-8
    r = api.post("/api/holds", content=body, headers={"content-type": "application/json"})
    assert r.status_code == 422 and r.json()["detail"]["error"] == "invalid_input", r.text
    assert written(pg) == (0, 0, 0, 0)
