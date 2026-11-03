"""FR-14 against the real stack: a temporary conflict in the data store is retried a bounded number of times;
if it still fails the Guest gets "try again" (503, not the definite "no seat free" 409) and nothing is written.

The conflict is forced inside PostgreSQL itself: a trigger on the written table raises SQLSTATE 40001
(serialization failure) or 40P01 (deadlock detected), exactly what the retry loop in db.run() is built for.
A sequence counts the attempts. Sequences are not rolled back, so the count survives the failed transactions
and shows how many times the request really tried. Nothing in the API, the pool or the retry is mocked.
"""

from __future__ import annotations

import pytest

from booking_platform import db

ALWAYS = 10**9

# (path, body, table the request writes to)
WRITES = [
    ("/bookings", dict(window_id=1, seats=3, session_id="s"), "bookings"),
    ("/holds", dict(window_id=1, seats=3, session_id="s"), "holds"),
    ("/whole-bookings", dict(window_id=1, sauna_id=4), "whole_bookings"),
]


@pytest.fixture
def force_conflict(pg):
    """install(table, sqlstate, failures): the first `failures` writes to `table` raise `sqlstate`."""
    installed: list[str] = []

    def install(table: str, sqlstate: str, failures: int) -> None:
        pg.execute("DROP SEQUENCE IF EXISTS force_conflict_attempts")
        pg.execute("CREATE SEQUENCE force_conflict_attempts")
        pg.execute(f"""
            CREATE OR REPLACE FUNCTION force_conflict() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN
              IF nextval('force_conflict_attempts') <= {failures} THEN
                RAISE EXCEPTION 'forced conflict' USING ERRCODE = '{sqlstate}';
              END IF;
              RETURN NEW;
            END $$""")
        # "z_" so it fires after the store's own locking triggers: the conflict hits late in the unit of work.
        pg.execute(f"CREATE TRIGGER z_force_conflict BEFORE INSERT ON {table} "
                   "FOR EACH ROW EXECUTE FUNCTION force_conflict()")
        pg.commit()
        installed.append(table)

    def attempts() -> int:
        pg.rollback()
        row = pg.execute("SELECT last_value, is_called FROM force_conflict_attempts").fetchone()
        pg.rollback()
        return row[0] if row[1] else 0

    install.attempts = attempts
    yield install
    pg.rollback()
    for t in installed:
        pg.execute(f"DROP TRIGGER IF EXISTS z_force_conflict ON {t}")
    pg.execute("DROP FUNCTION IF EXISTS force_conflict()")
    pg.execute("DROP SEQUENCE IF EXISTS force_conflict_attempts")
    pg.commit()


def rows(pg, table: str) -> int:
    pg.rollback()
    n = pg.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    pg.rollback()
    return n


@pytest.mark.parametrize("sqlstate", ["40001", "40P01"], ids=["serialization_failure", "deadlock_detected"])
@pytest.mark.parametrize("path,body,table", WRITES, ids=[w[2] for w in WRITES])
def test_when_every_attempt_conflicts_the_guest_is_told_to_try_again_and_nothing_is_written(
        api, pg, force_conflict, path, body, table, sqlstate):
    force_conflict(table, sqlstate, ALWAYS)

    r = api.post(path, json=body)

    assert r.status_code == 503 and r.json() == {"detail": {"error": "try_again"}}, r.text
    assert force_conflict.attempts() == db.RETRIES, "bounded: exactly RETRIES attempts, no more, no fewer"
    assert rows(pg, table) == 0


def test_a_failed_booking_leaves_the_guests_hold_untouched(api, pg, force_conflict):
    """/bookings deletes the session's Hold before it inserts the Booking. When the insert conflicts for good,
    that delete must be rolled back too: no partial data (FR-14)."""
    assert api.post("/holds", json=dict(window_id=1, seats=5, session_id="s")).status_code == 200
    before = pg.execute("SELECT id, seats, expires_at FROM holds").fetchall()
    pg.rollback()
    left_before = api.get("/windows/1").json()["seats_left"]

    force_conflict("bookings", "40001", ALWAYS)
    r = api.post("/bookings", json=dict(window_id=1, seats=5, session_id="s"))

    assert r.status_code == 503
    after = pg.execute("SELECT id, seats, expires_at FROM holds").fetchall()
    pg.rollback()
    assert after == before, "the Hold the Guest paid with is still there"
    assert rows(pg, "bookings") == 0
    assert api.get("/windows/1").json()["seats_left"] == left_before == 39


@pytest.mark.parametrize("failures", [1, 2, db.RETRIES - 1])
def test_a_conflict_that_clears_within_the_bound_is_retried_into_success(api, pg, force_conflict, failures):
    force_conflict("bookings", "40001", failures)

    r = api.post("/bookings", json=dict(window_id=1, seats=3, session_id="s"))

    assert r.status_code == 201, r.text
    assert force_conflict.attempts() == failures + 1
    assert rows(pg, "bookings") == 1, "exactly one Booking: the failed attempts left nothing behind"
    assert api.get("/windows/1").json()["seats_left"] == 41


def test_the_last_allowed_attempt_still_counts(api, pg, force_conflict):
    """Boundary: RETRIES-1 failures then success is a 201 (above); RETRIES failures is a 503."""
    force_conflict("bookings", "40001", db.RETRIES)

    r = api.post("/bookings", json=dict(window_id=1, seats=3, session_id="s"))

    assert r.status_code == 503
    assert force_conflict.attempts() == db.RETRIES
    assert rows(pg, "bookings") == 0


def test_try_again_and_no_seat_free_are_different_answers(api, pg, force_conflict):
    """FR-14: a definite loss (409 no_seat_free) is not the same message as retries used up (503 try_again)."""
    assert api.post("/bookings", json=dict(window_id=1, seats=44, session_id="a")).status_code == 201
    lost = api.post("/bookings", json=dict(window_id=1, seats=1, session_id="b"))
    assert lost.status_code == 409 and lost.json()["detail"]["error"] == "no_seat_free"

    force_conflict("bookings", "40001", ALWAYS)
    retry = api.post("/bookings", json=dict(window_id=2, seats=1, session_id="c"))
    assert retry.status_code == 503 and retry.json()["detail"]["error"] == "try_again"
    assert lost.json() != retry.json()


def test_a_non_temporary_error_is_not_retried(api, pg, force_conflict):
    """Only 40001/40P01 are temporary. Any other store error must fail at once instead of being retried."""
    force_conflict("bookings", "23514", ALWAYS)  # check_violation: the store's definite refusal

    r = api.post("/bookings", json=dict(window_id=1, seats=3, session_id="s"))

    assert r.status_code == 409, r.text
    assert force_conflict.attempts() == 1, "one attempt: a definite refusal is never retried"
    assert rows(pg, "bookings") == 0


def test_the_service_recovers_after_the_conflicts_stop(api, pg, force_conflict):
    force_conflict("bookings", "40001", ALWAYS)
    assert api.post("/bookings", json=dict(window_id=1, seats=3, session_id="s")).status_code == 503

    pg.execute("DROP TRIGGER z_force_conflict ON bookings")
    pg.commit()

    assert api.post("/bookings", json=dict(window_id=1, seats=3, session_id="s")).status_code == 201
    assert rows(pg, "bookings") == 1
