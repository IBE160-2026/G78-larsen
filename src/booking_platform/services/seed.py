"""The seed (AD-18): `seeds/venue.json`, applied after the migrations and before the app serves, in every
environment.

The seed inserts the Saunas that are absent, and the daily Window schedule when `window_schedule` is empty. The
Venue values of the `settings` row come from 0004's column defaults, which equal the seed (pinned by
`tests/test_fr01_venue.py`); the seed only fills such a column when it is NULL. It never overwrites, so after the
first start the store owns every value. The file goes through the same validation as Administrator input
(`services.venue`, IV-6). A file that cannot be read or is invalid is a `SeedError` whose message is one line that
names the file and the field.

The sample Bookings (`seeds/bookings.json`, Story 1.5) are applied after `windows.ensure_generated()`: each entry is a
Window given as days after the Venue date of the run plus a start time, created through `services.booking.create`
under one fixed seed session with the entry's fixed idempotency key. An entry whose key is already stored is skipped,
so a restart, on any day, creates no duplicates. The seed always pays `ok` (the payment switch applies only to HTTP
requests).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import uuid
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .. import config, db
from ..db import bookings as bq
from ..db import sessions as sq
from ..db import venue as q
from ..db import windows as wq
from . import booking
from .errors import Refused
from .venue import VenueSeed

log = logging.getLogger("booking_platform.seed")

VENUE_FILE = "venue.json"
BOOKINGS_FILE = "bookings.json"
# The seed session's token hash: fixed, and no token hashes to it, so no browser can act as the seed (AD-18).
SEED_TOKEN_HASH = hashlib.sha256(b"booking-platform seed session, never a cookie").digest()


class SeedError(Exception):
    """The seed cannot be used. The message is one line, fit to print before exiting."""


def _name(path: Path) -> str:
    try:
        return path.relative_to(config.paths.ROOT).as_posix()
    except ValueError:
        return str(path)


def _read(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))  # a BOM is accepted
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise SeedError(f"seed file {_name(path)} cannot be read: {type(e).__name__}") from None


def _invalid(path: Path, e: ValidationError) -> SeedError:
    first = e.errors()[0]
    field = ".".join(str(p) for p in first.get("loc", ())) or "(file)"
    message = " ".join(str(first.get("msg", "is invalid")).split())
    return SeedError(f"seed file {_name(path)}: {field}: {message}")


def load(directory: Path | None = None, tz: str | None = None) -> VenueSeed:
    """Read and validate `seeds/venue.json`; raises SeedError. `tz` is the Venue time zone the schedule is checked
    against (default: the `settings.venue_tz` default, since the store is not read before startup)."""
    path = (directory or config.paths.SEEDS) / VENUE_FILE
    data = _read(path)
    try:
        return VenueSeed.model_validate(data, context={"tz": tz} if tz else None)
    except ValidationError as e:
        raise _invalid(path, e) from None


def apply(directory: Path | None = None) -> int:
    """Apply the seed in one transaction. Returns the number of Saunas inserted (0 on every start after the first).
    The schedule is checked again against the store's Venue time zone."""
    seed = load(directory, tz=db.run(wq.venue_tz))

    def work(c):
        q.seed_settings(c, seed.venue.row())
        rows = wq.seed_schedule(c, [(r.start, r.end) for r in seed.schedule])
        if rows:
            log.info("seeded the window schedule: %d rows", rows)
        return sum(q.seed_sauna(c, s.id, s.name, s.capacity, s.fill_order) for s in seed.saunas)

    inserted = db.run(work)
    log.info("applied seed %s: %d saunas inserted", VENUE_FILE, inserted)
    return inserted


# ------------------------------------------------------------------ sample Bookings (AD-18, Story 1.5)


class SampleBooking(BaseModel):
    """One sample Booking, validated like a Guest's request (FR-18 IV-6): 1 to 10 Seats, a name of 1 to 100
    characters and a valid email of at most 254."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    key: uuid.UUID
    days: int = Field(ge=0, le=31)  # after the Venue date of the run
    start: dt.time  # Venue clock time of the Window's start
    seats: int = Field(ge=1, le=10)
    name: Annotated[str, Field(min_length=1, max_length=100)]
    email: Annotated[str, Field(min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]


class BookingsSeed(BaseModel):
    """The shape of `seeds/bookings.json`."""

    model_config = ConfigDict(extra="forbid")

    bookings: list[SampleBooking]

    @model_validator(mode="after")
    def _unique_keys(self) -> BookingsSeed:
        keys = [b.key for b in self.bookings]
        if len(keys) != len(set(keys)):
            raise ValueError("two sample bookings share one key")
        return self


def load_bookings(directory: Path | None = None) -> BookingsSeed:
    """Read and validate `seeds/bookings.json`; raises SeedError. A missing file means no sample Bookings."""
    path = (directory or config.paths.SEEDS) / BOOKINGS_FILE
    if not path.exists():
        return BookingsSeed(bookings=[])
    data = _read(path)
    try:
        return BookingsSeed.model_validate(data)
    except ValidationError as e:
        raise _invalid(path, e) from None


def apply_bookings(directory: Path | None = None) -> int:
    """Create the sample Bookings whose keys are not yet stored. Call after `windows.ensure_generated()`. An entry whose
    Window does not exist or that the rules refuse (sold out, past its deadline) is skipped with a log line; it never
    stops startup. Returns the Bookings created."""
    seed = load_bookings(directory)
    if not seed.bookings:
        return 0
    session_id = db.run(lambda c: sq.ensure_seed_session(c, SEED_TOKEN_HASH))
    created = 0
    for i, entry in enumerate(seed.bookings):
        def find(c, entry=entry):
            if bq.key_exists(c, entry.key):
                return None, True
            return bq.window_at(c, bq.venue_today(c) + dt.timedelta(days=entry.days), entry.start), False

        window_id, known = db.run(find)
        if known:
            continue
        if window_id is None:
            log.warning("sample booking %d skipped: no window at +%d days %s", i, entry.days, entry.start)
            continue
        try:
            booking.create(session_id, window_id, entry.seats, entry.name, entry.email, entry.key)
        except Refused as e:
            log.warning("sample booking %d skipped: %s", i, e.code)
            continue
        created += 1
    log.info("applied seed %s: %d bookings created", BOOKINGS_FILE, created)
    return created
