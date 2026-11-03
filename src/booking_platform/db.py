"""Data store access: connection pool, schema installation and the bounded retry of FR-14.

The data store is PostgreSQL (PRD §12 Q4). The store itself refuses over-capacity writes (FR-10, addendum A);
this module only gives the application one safe way to run a unit of work against it.
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from importlib import resources
from typing import Callable, Iterator, TypeVar

import psycopg
from psycopg import errors
from psycopg_pool import ConnectionPool

DEFAULT_URL = "postgresql://postgres:booking@localhost:55432/booking"
RETRIES = 5  # FR-14: "a bounded number of times"
T = TypeVar("T")

_pool: ConnectionPool | None = None


def database_url() -> str:
    return os.environ.get("BP_DATABASE_URL", DEFAULT_URL)


def open_pool(url: str | None = None, max_size: int = 24) -> ConnectionPool:
    global _pool
    _pool = ConnectionPool(url or database_url(), min_size=2, max_size=max_size, open=True, timeout=30)
    return _pool


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def migrate(url: str | None = None) -> bool:
    """Install the schema if the database is empty. Returns True when it installed it."""
    sql = resources.files("booking_platform").joinpath("schema.sql").read_text(encoding="utf-8")
    with psycopg.connect(url or database_url()) as c:
        if c.execute("SELECT to_regclass('public.windows')").fetchone()[0] is not None:
            return False
        c.execute(sql)
        return True


class TryAgain(Exception):
    """Retries are used up (FR-14): the request wrote nothing and the Guest is asked to try again."""


# SQLSTATEs that mean "a temporary conflict in the data store": deadlock detected, serialization failure.
_TEMPORARY = (errors.DeadlockDetected, errors.SerializationFailure)


def run(work: Callable[[psycopg.Connection], T]) -> T:
    """Run one unit of work in one transaction (Read Committed), retrying temporary conflicts a bounded
    number of times. Anything the work wrote is rolled back on every failed attempt (FR-14)."""
    assert _pool is not None, "pool is not open"
    last: Exception | None = None
    for attempt in range(RETRIES):
        try:
            with _pool.connection() as c:  # commits on success, rolls back on any exception
                return work(c)
        except _TEMPORARY as e:
            last = e
            time.sleep(0.005 * (attempt + 1))
    raise TryAgain(str(last))


def lock_windows(c: psycopg.Connection, ids: list[int]) -> None:
    """Lock Window rows in id order before the first write of a multi-statement unit (addendum A, rules)."""
    c.execute("SELECT lock_windows(%s)", (ids,))


@contextmanager
def raw_connection(url: str | None = None) -> Iterator[psycopg.Connection]:
    """A connection that goes around the application (used by tests that bypass it)."""
    with psycopg.connect(url or database_url()) as c:
        yield c
