"""Data store access: the pool, `run` with the bounded retry of FR-14, `lock_windows`, and the translation of store
refusals (AD-1, AD-3). All SQL lives in this package and in `migrations/`.

The store itself refuses over-capacity writes (FR-10, AD-2); this package gives the layers above one safe way to
run a unit of work against it.
"""

from __future__ import annotations

import logging
import time
from typing import Callable, TypeVar

import psycopg
from psycopg import errors
from psycopg_pool import ConnectionPool

from .. import config
from .refusals import Refused, StoreError, code_for

RETRIES = 5  # FR-14: "a bounded number of times"
log = logging.getLogger("booking_platform.db")
T = TypeVar("T")

_pool: ConnectionPool | None = None

# SQLSTATEs that mean "a temporary conflict in the data store": serialization failure (40001), deadlock (40P01).
_TEMPORARY = (errors.SerializationFailure, errors.DeadlockDetected)


class Retry(Exception):
    """Raised by a unit of work to run it again from the start, like a temporary conflict: a row it read unlocked
    changed before it could lock it (AD-29: a Booking's `window_id` moved between the unlocked read and the locked
    re-read). Counts against the same bounded number of attempts."""

    sqlstate = "retry"


def _configure(c: psycopg.Connection) -> None:
    c.isolation_level = psycopg.IsolationLevel.READ_COMMITTED  # AD-3: set explicitly on the pool


def open_pool(url: str | None = None, max_size: int = 24) -> ConnectionPool:
    global _pool
    _pool = ConnectionPool(url or config.settings().database_url, min_size=2, max_size=max_size, open=True,
                           timeout=30, kwargs={"options": "-c TimeZone=UTC"}, configure=_configure)
    return _pool


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def _translate(e: psycopg.Error) -> Exception:
    """A store error becomes a Refused when its constraint name is mapped, otherwise a StoreError (a 500)."""
    constraint = e.diag.constraint_name
    code = code_for(constraint)
    if code is not None:
        return Refused(code)
    return StoreError(e.sqlstate, constraint)


def _force_conflict(c: psycopg.Connection) -> None:
    """Test seam (AD-14): with `force_conflict` on, a run made for an HTTP request whose transaction has written
    raises a real serialization failure before COMMIT."""
    if not (config.in_request.get() and config.switches().force_conflict):
        return
    if c.execute("SELECT pg_current_xact_id_if_assigned() IS NOT NULL").fetchone()[0]:
        c.execute("DO $$ BEGIN RAISE EXCEPTION 'forced conflict (test switch)' USING ERRCODE = '40001'; END $$")


def run(work: Callable[[psycopg.Connection], T]) -> T:
    """Run one unit of work in one READ COMMITTED transaction, retrying temporary conflicts a bounded number of
    times (`Retry` counts as one). Anything the work wrote is rolled back on every failed attempt (FR-14). Store refusals, at any
    statement or at COMMIT, are translated by constraint name. Retries used up is `Refused('try_again')`."""
    assert _pool is not None, "pool is not open"
    last: str | None = None
    for attempt in range(RETRIES):
        try:
            with _pool.connection() as c:  # commits on success, rolls back on any exception
                result = work(c)
                _force_conflict(c)
                return result
        except (*_TEMPORARY, Retry) as e:
            last = e.sqlstate
            time.sleep(0.005 * (attempt + 1))
        except psycopg.Error as e:
            raise _translate(e) from None
    log.warning("retries used up: sqlstate=%s attempts=%d", last, RETRIES)
    raise Refused("try_again")


def statement(work: Callable[[psycopg.Connection], T]) -> T:
    """One autocommit statement outside every action transaction (the sliding session touch, startup purges)."""
    assert _pool is not None, "pool is not open"
    try:
        with _pool.connection() as c:
            c.autocommit = True
            try:
                return work(c)
            finally:
                c.autocommit = False
    except psycopg.Error as e:
        raise _translate(e) from None


def lock_windows(c: psycopg.Connection, ids: list[int]) -> None:
    """Lock Window rows in id order before the first write of a multi-statement unit (AD-3)."""
    c.execute("SELECT lock_windows(%s)", (ids,))
