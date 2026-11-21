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
from client import booking_body, new_key
from test_fr10_through_the_api import fill

ALWAYS = 10**9

# (path, body, table the request writes to); /api/admin/ paths are sent with the Administrator session
WRITES = [
    ("/api/bookings", booking_body(1, 3), "bookings"),
    ("/api/holds", dict(window_id=1, seats=3), "holds"),
    ("/api/admin/whole-bookings", dict(window_id=1, sauna_id=4), "whole_bookings"),
]


@pytest.fixture
def force_conflict(pg):
    """install(table, sqlstate, failures): the first `failures` writes to `table` raise `sqlstate`."""
    installed: list[str] = []

    def install(table: str, sqlstate: str, failures: int, constraint: str | None = None) -> None:
        named = f", CONSTRAINT = '{constraint}'" if constraint else ""
        pg.execute("DROP SEQUENCE IF EXISTS force_conflict_attempts")
        pg.execute("CREATE SEQUENCE force_conflict_attempts")
        pg.execute(f"""
            CREATE OR REPLACE FUNCTION force_conflict() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN
              IF nextval('force_conflict_attempts') <= {failures} THEN
                RAISE EXCEPTION 'forced conflict' USING ERRCODE = '{sqlstate}'{named};
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
        api, admin, pg, force_conflict, path, body, table, sqlstate):
    force_conflict(table, sqlstate, ALWAYS)

    r = (admin if path.startswith("/api/admin/") else api).post(path, json=body, headers=new_key())

    assert r.status_code == 503 and r.json() == {"detail": {"error": "try_again"}}, r.text
    assert force_conflict.attempts() == db.RETRIES, "bounded: exactly RETRIES attempts, no more, no fewer"
    assert rows(pg, table) == 0
    if table == "bookings":  # a Booking that never came has no charge, no email and no key (FR-12, FR-14)
        assert [rows(pg, t) for t in ("payments", "outbox_emails", "idempotency_keys")] == [0, 0, 0]


def test_a_failed_booking_leaves_the_guests_hold_untouched(api, pg, force_conflict):
    """/bookings deletes the session's Hold before it inserts the Booking. When the insert conflicts for good,
    that delete must be rolled back too: no partial data (FR-14)."""
    assert api.post("/api/holds", json=dict(window_id=1, seats=5)).status_code == 200
    before = pg.execute("SELECT id, seats, expires_at FROM holds").fetchall()
    pg.rollback()
    left_before = api.get("/api/windows/1").json()["seats_left"]

    force_conflict("bookings", "40001", ALWAYS)
    r = api.book(1, 5)

    assert r.status_code == 503
    after = pg.execute("SELECT id, seats, expires_at FROM holds").fetchall()
    pg.rollback()
    assert after == before, "the Hold the Guest paid with is still there"
    assert rows(pg, "bookings") == 0
    assert api.get("/api/windows/1").json()["seats_left"] == left_before == 39


@pytest.mark.parametrize("failures", [1, 2, db.RETRIES - 1])
def test_a_conflict_that_clears_within_the_bound_is_retried_into_success(api, pg, force_conflict, failures):
    force_conflict("bookings", "40001", failures)

    r = api.book(1, 3)

    assert r.status_code == 201, r.text
    assert force_conflict.attempts() == failures + 1
    assert rows(pg, "bookings") == 1, "exactly one Booking: the failed attempts left nothing behind"
    assert api.get("/api/windows/1").json()["seats_left"] == 41


def test_the_last_allowed_attempt_still_counts(api, pg, force_conflict):
    """Boundary: RETRIES-1 failures then success is a 201 (above); RETRIES failures is a 503."""
    force_conflict("bookings", "40001", db.RETRIES)

    r = api.book(1, 3)

    assert r.status_code == 503
    assert force_conflict.attempts() == db.RETRIES
    assert rows(pg, "bookings") == 0


def test_try_again_and_no_seat_free_are_different_answers(api, pg, force_conflict):
    """FR-14: a definite loss (409 no_seat_free) is not the same message as retries used up (503 try_again)."""
    fill(api, 44)  # 44 Seats in Bookings of at most 10, each a 201 (AD-21)
    lost = api.book(1, 1)
    assert lost.status_code == 409 and lost.json()["detail"]["error"] == "no_seat_free"

    force_conflict("bookings", "40001", ALWAYS)
    retry = api.book(2, 1)
    assert retry.status_code == 503 and retry.json()["detail"]["error"] == "try_again"
    assert lost.json() != retry.json()


def test_a_non_temporary_error_is_not_retried(api, pg, force_conflict):
    """Only 40001/40P01 are temporary. Any other store error must fail at once instead of being retried."""
    # check_violation: the store's definite refusal, named as every store refusal is (AD-1)
    force_conflict("bookings", "23514", ALWAYS, constraint="booked_within_capacity")

    r = api.book(1, 3)

    assert r.status_code == 409, r.text
    assert force_conflict.attempts() == 1, "one attempt: a definite refusal is never retried"
    assert rows(pg, "bookings") == 0


def test_the_service_recovers_after_the_conflicts_stop(api, pg, force_conflict):
    force_conflict("bookings", "40001", ALWAYS)
    assert api.book(1, 3).status_code == 503

    pg.execute("DROP TRIGGER z_force_conflict ON bookings")
    pg.commit()

    assert api.book(1, 3).status_code == 201
    assert rows(pg, "bookings") == 1


def test_an_unnamed_store_error_is_a_500_without_store_text_and_is_not_retried(api, pg, force_conflict):
    """AD-1: a store error with no constraint name, or an unmapped one, is never a refusal: 500 internal_error,
    and the store's own text never reaches the response."""
    force_conflict("bookings", "23514", ALWAYS)  # no CONSTRAINT name

    r = api.book(1, 3)

    assert r.status_code == 500 and r.json() == {"detail": {"error": "internal_error"}}, r.text
    assert "forced" not in r.text
    assert force_conflict.attempts() == 1
    assert rows(pg, "bookings") == 0
