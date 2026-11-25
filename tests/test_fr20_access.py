"""FR-20 / AD-10: Administrator access is decided at the router, and the API answers unknown paths with JSON.

Every Administrator endpoint is under `/api/admin/`: anonymous callers get `401 not_signed_in`, and so do Guest
sessions, which have no account (RB-1, Story 2.1); neither changes anything. (`403 not_allowed` is kept for an
account without the Administrator role, which the Core does not have.) Unknown paths, slash variants and 405s answer
the JSON `404 not_found` envelope; the backend never redirects, and `/docs` and `/openapi.json` are off.
"""

from __future__ import annotations

import datetime as dt

import pytest

from client import api_client
from conftest import win_start

NOT_FOUND = {"detail": {"error": "not_found"}}

_st = win_start(1)
ADMIN_CALLS = [
    ("POST", "/api/admin/blocks", dict(json=dict(sauna_id=4, start=_st.isoformat(),
                                                 end=(_st + dt.timedelta(minutes=90)).isoformat()))),
    ("DELETE", "/api/admin/blocks/1", {}),
    ("POST", "/api/admin/marks", dict(json=dict(window_id=1, sauna_id=4))),
    ("DELETE", "/api/admin/marks", dict(params=dict(window_id=2, sauna_id=3))),
    ("PUT", "/api/admin/settings", dict(json=dict(release_on=False, release_time="07:00", booking_deadline_minutes=5))),
]
IDS = [f"{m} {p}" for m, p, _ in ADMIN_CALLS]


def snapshot(pg) -> tuple:
    pg.rollback()
    row = pg.execute("SELECT (SELECT count(*) FROM whole_bookings), (SELECT count(*) FROM blocks), "
                     "(SELECT count(*) FROM marks), (SELECT release_on FROM settings), "
                     "(SELECT release_time FROM settings), (SELECT seats_left(1)), (SELECT seats_left(2))").fetchone()
    pg.rollback()
    return tuple(row)


@pytest.fixture
def furnished(admin, pg):
    """One Block and one mark exist, so the DELETE calls would have something to remove."""
    st = win_start(2)
    assert admin.post("/api/admin/blocks", json=dict(sauna_id=1, start=st.isoformat(),
                                                     end=(st + dt.timedelta(minutes=90)).isoformat())).status_code == 201
    assert admin.post("/api/admin/marks", json=dict(window_id=2, sauna_id=3)).status_code == 201
    return admin


@pytest.mark.parametrize("method,path,kw", ADMIN_CALLS, ids=IDS)
def test_an_anonymous_caller_gets_401_and_changes_nothing(furnished, world, pg, method, path, kw):
    before = snapshot(pg)
    with api_client(world, session=False) as anon:
        r = anon.request(method, path, **kw)
    assert r.status_code == 401 and r.json() == {"detail": {"error": "not_signed_in"}}, r.text
    assert snapshot(pg) == before


@pytest.mark.parametrize("method,path,kw", ADMIN_CALLS, ids=IDS)
def test_a_guest_session_gets_401_and_changes_nothing(furnished, api, pg, method, path, kw):
    """A Guest's booking session has no account, so it counts as anonymous (RB-1, Story 2.1)."""
    before = snapshot(pg)
    r = api.request(method, path, **kw)
    assert r.status_code == 401 and r.json() == {"detail": {"error": "not_signed_in"}}, r.text
    assert snapshot(pg) == before


def test_an_administrator_session_is_allowed(admin):
    assert admin.post("/api/admin/marks", json=dict(window_id=1, sauna_id=4)).status_code == 201
    assert admin.delete("/api/admin/marks", params=dict(window_id=1, sauna_id=4)).json() == {"removed": 1}


@pytest.mark.parametrize("method,path", [
    ("GET", "/api/nope"),
    ("GET", "/api"),
    ("GET", "/api/health/"),  # a slash variant is a 404, never a redirect
    ("GET", "/api/windows/"),
    ("DELETE", "/api/health"),  # 405 becomes 404
    ("POST", "/api/windows"),
    ("GET", "/api/admin/nope"),
    ("GET", "/api/admin/marks"),
    ("GET", "/docs"),
    ("GET", "/openapi.json"),
    ("GET", "/redoc"),
    ("GET", "/"),
])
def test_unknown_paths_and_wrong_methods_answer_the_json_404(api, method, path):
    r = api.request(method, path, **({"json": {}} if method == "POST" else {}))
    assert r.status_code == 404 and r.json() == NOT_FOUND, (path, r.status_code, r.text)
    assert "location" not in r.headers


def test_an_unknown_window_is_not_found(api):
    assert api.get("/api/windows/999").json() == NOT_FOUND
    r = api.post("/api/holds", json=dict(window_id=999, seats=1))
    assert r.status_code == 404 and r.json() == NOT_FOUND


def test_an_unknown_sauna_is_not_found(admin):
    st = win_start(1)
    # the slice's `/api/admin/whole-bookings` entry went with its endpoint (Story 5.1)
    for path, body in [("/api/admin/blocks", dict(sauna_id=99, start=st.isoformat(),
                                                   end=(st + dt.timedelta(minutes=90)).isoformat()))]:
        r = admin.post(path, json=body)
        assert r.status_code == 404 and r.json() == NOT_FOUND, (path, r.text)
