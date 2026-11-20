"""FR-18 / AD-8: every state-changing request must be same-origin. Its `Origin` equals the base URL's origin, or,
without `Origin`, it carries `Sec-Fetch-Site: same-origin`. Anything else is `403 cross_origin` and nothing changes.
There are no CSRF tokens, and `Host` is never compared."""

from __future__ import annotations

import httpx
import pytest

from client import COOKIE, _TLS, booking_body, new_key


def counts(pg) -> dict:
    pg.rollback()
    row = pg.execute("SELECT (SELECT count(*) FROM holds), (SELECT count(*) FROM bookings), "
                     "(SELECT count(*) FROM marks), (SELECT count(*) FROM sessions), "
                     "(SELECT release_time::text FROM settings)").fetchone()
    pg.rollback()
    return dict(holds=row[0], bookings=row[1], marks=row[2], sessions=row[3], release_time=row[4])


def raw(base: str, token: str | None, headers: dict[str, str]) -> httpx.Client:
    """A client that sends exactly the given headers (no Origin unless named), with a session cookie."""
    c = httpx.Client(base_url=base, timeout=30, headers=headers, verify=_TLS)
    if token:
        c.cookies.set(COOKIE, token, domain=httpx.URL(base).host)
    return c


CROSS = [
    {"Origin": "http://evil.example"},
    {"Origin": "null"},
    {"Origin": "http://127.0.0.1:1"},  # same host, another port: another origin
    {},  # neither Origin nor Sec-Fetch-Site
    {"Sec-Fetch-Site": "cross-site"},
    {"Sec-Fetch-Site": "same-site"},
]


@pytest.mark.parametrize("headers", CROSS, ids=["evil", "null", "other-port", "none", "cross-site", "same-site"])
def test_a_cross_origin_write_is_refused_and_writes_nothing(api, world, pg, headers):
    before = counts(pg)
    with raw(world, api.token, headers) as c:
        for r in [c.post("/api/holds", json=dict(window_id=1, seats=2)),
                  c.post("/api/bookings", json=booking_body(1, 2), headers=new_key()),
                  c.post("/api/session", json={})]:
            assert r.status_code == 403 and r.json() == {"detail": {"error": "cross_origin"}}, r.text
    assert counts(pg) == before


def test_cross_origin_is_checked_on_put_and_delete_as_well(api, admin, world, pg):
    assert api.post("/api/holds", json=dict(window_id=1, seats=2)).status_code == 200
    assert admin.post("/api/admin/marks", json=dict(window_id=2, sauna_id=4)).status_code == 201
    before = counts(pg)
    evil = {"Origin": "http://evil.example"}
    with raw(world, api.token, evil) as guest, raw(world, admin.token, evil) as adm:
        assert guest.delete("/api/holds", params=dict(window_id=1)).status_code == 403
        assert adm.delete("/api/admin/marks", params=dict(window_id=2, sauna_id=4)).status_code == 403
        r = adm.put("/api/admin/settings", json=dict(release_on=True, release_time="07:00", booking_deadline_minutes=5))
        assert r.status_code == 403 and r.json()["detail"]["error"] == "cross_origin"
    assert counts(pg) == before


def test_without_origin_a_same_origin_fetch_is_accepted(api, world, pg):
    with raw(world, api.token, {"Sec-Fetch-Site": "same-origin"}) as c:
        assert c.post("/api/holds", json=dict(window_id=1, seats=2)).status_code == 200
        assert c.delete("/api/holds", params=dict(window_id=1)).json() == {"released": 1}


def test_the_base_url_origin_is_accepted_and_reads_need_no_origin(api, world):
    assert api.post("/api/holds", json=dict(window_id=1, seats=1)).status_code == 200  # api_client sends Origin
    with raw(world, None, {"Origin": "http://evil.example"}) as c:
        assert c.get("/api/windows/1").status_code == 200  # a read changes nothing, so it is not checked
    with raw(world, None, {}) as c:
        assert c.get("/api/health").status_code == 200


def test_the_host_header_does_not_make_a_request_same_origin(api, world, pg):
    """Origin is compared with BP_BASE_URL only, never with Host (AD-27)."""
    before = counts(pg)
    with raw(world, api.token, {"Origin": "http://evil.example", "Host": "evil.example"}) as c:
        assert c.post("/api/holds", json=dict(window_id=1, seats=2)).status_code == 403
    assert counts(pg) == before
