"""AD-14 / AD-22: the test switch file and the configuration read at startup.

A missing switch file, or a path that is not a regular file, means every switch is off. A file that exists but
cannot be parsed stops startup with one line naming it. `force_conflict` raises a real 40001 before COMMIT in runs
made for an HTTP request that have written, so the request ends in `503 try_again` with nothing written.
"""

from __future__ import annotations

import time

import pytest

from booking_platform import config
from client import COOKIE, ApiClient, _TLS
from conftest import start_backend


def test_a_missing_file_or_a_directory_means_every_switch_is_off(tmp_path):
    assert config.load_switches(tmp_path / "nope.toml") == config.Switches(payment="ok", force_conflict=False)
    assert config.load_switches(tmp_path) == config.Switches()


def test_the_committed_example_has_every_switch_off():
    assert config.load_switches(config.paths.CONFIG / "test-switches.example.toml") == config.Switches()


def test_a_valid_file_is_read(tmp_path):
    f = tmp_path / "s.toml"
    f.write_text('payment = "hold"\nforce_conflict = true\n', encoding="utf-8")
    assert config.load_switches(f) == config.Switches(payment="hold", force_conflict=True)


@pytest.mark.parametrize("text", ["payment = [", 'payment = "maybe"', "force_conflict = 1", "lock = true"])
def test_a_broken_file_is_one_line_naming_it(tmp_path, text):
    f = tmp_path / "s.toml"
    f.write_text(text, encoding="utf-8")
    with pytest.raises(config.ConfigError) as e:
        config.load_switches(f)
    assert str(f) in str(e.value) and "\n" not in str(e.value)


def test_https_needs_an_https_base_url():
    with pytest.raises(config.ConfigError, match="https://"):
        config.load_settings({"BP_HTTPS": "on", "BP_BASE_URL": "http://localhost:8000"})
    s = config.load_settings({"BP_HTTPS": "on", "BP_BASE_URL": "https://localhost:8443"})
    assert s.https and s.base_origin == "https://localhost:8443"


def test_the_defaults_work_without_any_variable():
    s = config.load_settings({})
    assert (s.host, s.port, s.https) == ("127.0.0.1", 8001, False)
    assert s.base_url == "http://127.0.0.1:3000"
    assert s.database_url == "postgresql://postgres:booking@127.0.0.1:55432/booking_dev"
    assert s.test_switches == config.paths.ROOT / "config" / "test-switches.toml"


def test_startup_stops_on_a_broken_switch_file_with_one_line_naming_it(database, tmp_path):
    b = start_backend(database, tmp_path, name="broken", switches="payment = [", wait=False)
    try:
        b.proc.wait(timeout=90)
    finally:
        b.stop()
    out = b.output()
    assert b.proc.returncode not in (None, 0)
    named = [line for line in out.splitlines() if str(tmp_path / "broken-switches.toml") in line]
    assert len(named) == 1, out
    assert "Traceback" not in out


def test_force_conflict_makes_every_writing_request_try_again_and_writes_nothing(api, world, pg, database,
                                                                                 tmp_path):
    b = start_backend(database, tmp_path, name="conflict", switches="force_conflict = true\n")
    try:
        # the switched backend started: migrations and the startup purge are not affected
        with ApiClient(base_url=b.base, timeout=60, headers={"Origin": b.base}, verify=_TLS) as c:
            c.cookies.set(COOKIE, api.token, domain="127.0.0.1")  # a session made through the normal backend
            t = time.monotonic()
            r = c.post("/api/bookings", json=dict(window_id=1, seats=2))
            assert r.status_code == 503 and r.json() == {"detail": {"error": "try_again"}}, r.text
            assert time.monotonic() - t < 30
            r = c.post("/api/holds", json=dict(window_id=1, seats=2))
            assert r.status_code == 503
            assert c.post("/api/session", json={}).status_code == 200  # a still-valid session: nothing written
            # reads, and actions that write nothing, are not affected
            assert c.get("/api/windows/1").json()["seats_left"] == 44
            assert c.delete("/api/holds", params=dict(window_id=1)).json() == {"released": 0}
    finally:
        b.stop()
    pg.rollback()
    assert pg.execute("SELECT (SELECT count(*) FROM bookings), (SELECT count(*) FROM holds)").fetchone() == (0, 0)
    pg.rollback()
    # the normal backend, with every switch off, still writes
    assert api.post("/api/bookings", json=dict(window_id=1, seats=2)).status_code == 201
