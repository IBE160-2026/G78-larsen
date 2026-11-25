"""The seed (AD-18): `seeds/venue.json`, applied after the migrations and before the app serves, in every
environment.

The seed inserts the Saunas that are absent, fills a Sauna's `whole_price_ore` only where the store holds NULL (Story
5.1, AD-23), and inserts the daily Window schedule when `window_schedule` is empty. The
Venue values of the `settings` row come from 0004's column defaults, which equal the seed (pinned by
`tests/test_fr01_venue.py`); the seed only fills such a column when it is NULL. It never overwrites, so after the
first start the store owns every value. The file goes through the same validation as Administrator input
(`services.venue`, IV-6). A file that cannot be read or is invalid is a `SeedError` whose message is one line that
names the file and the field.

The sample Bookings (`seeds/bookings.json`, Story 1.5) are applied after `windows.ensure_generated()`: each entry is a
Window given as days after the Venue date of the run plus a start time, created through `services.booking.create`
under one fixed seed session with the entry's fixed idempotency key. An entry whose key is already stored is skipped,
so a restart, on any day, creates no duplicates. The seed always pays `ok` (the payment switch applies only to HTTP
requests). A sample created this way gets its Manage link in its confirmation email (Story 4.1). A sample Booking that
already existed without an unrevoked Manage token (made before migration 0010) and whose Window has not ended gets one
through `services.manage.issue`, with its own Outbox email "Manage your booking: <reference>"; a restart issues
nothing again (AD-18, AD-28).

The seeded Administrator (`seeds/admin.json`, Story 2.1) is `{"email", "password"}`: the documented local test login.
`load()` checks it with `services.auth.check_password_rules`, so a password that breaks a rule stops startup with one
line that never contains the password. `apply()` inserts the account only when its email is absent, so a restart
never rehashes and never overwrites a password set with `create-admin`. A missing file means no seeded account.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import uuid
from pathlib import Path
from typing import Annotated
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .. import config, db
from ..db import bookings as bq
from ..db import manage as mq
from ..db import sessions as sq
from ..db import venue as q
from ..db import windows as wq
from . import auth, booking, manage, outbox, voucher
from .errors import Refused
from .venue import VenueSeed

log = logging.getLogger("booking_platform.seed")

VENUE_FILE = "venue.json"
BOOKINGS_FILE = "bookings.json"
ADMIN_FILE = "admin.json"
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
    """Read and validate `seeds/venue.json` and `seeds/admin.json`; raises SeedError. `tz` is the Venue time zone the
    schedule is checked against (default: the `settings.venue_tz` default, since the store is not read before
    startup)."""
    path = (directory or config.paths.SEEDS) / VENUE_FILE
    data = _read(path)
    try:
        venue = VenueSeed.model_validate(data, context={"tz": tz} if tz else None)
    except ValidationError as e:
        raise _invalid(path, e) from None
    load_admin(directory)
    return venue


def apply(directory: Path | None = None) -> int:
    """Apply the seed in one transaction. Returns the number of Saunas inserted (0 on every start after the first).
    The schedule is checked again against the store's Venue time zone."""
    seed = load(directory, tz=db.run(wq.venue_tz))

    def work(c):
        q.seed_settings(c, seed.venue.row())
        rows = wq.seed_schedule(c, [(r.start, r.end) for r in seed.schedule])
        if rows:
            log.info("seeded the window schedule: %d rows", rows)
        return sum(q.seed_sauna(c, s.id, s.name, s.capacity, s.fill_order, s.whole_price_ore) for s in seed.saunas)

    inserted = db.run(work)
    log.info("applied seed %s: %d saunas inserted", VENUE_FILE, inserted)
    admin = load_admin(directory)
    if admin is not None:
        created = db.run(lambda c: auth.set_account(c, admin.email, admin.password, overwrite=False))
        log.info("applied seed %s: %d accounts created", ADMIN_FILE, int(created))
    return inserted


# ------------------------------------------------------------------ the seeded Administrator (AD-18, Story 2.1)


class AdminSeed(BaseModel):
    """The shape of `seeds/admin.json`. The password is checked by `check_password_rules` in `load_admin`."""

    model_config = ConfigDict(extra="forbid")

    email: Annotated[str, Field(min_length=3, max_length=auth.EMAIL_MAX, pattern=auth.EMAIL.pattern)]
    password: Annotated[str, Field(max_length=auth.MAX_LENGTH)]


def load_admin(directory: Path | None = None) -> AdminSeed | None:
    """Read and check `seeds/admin.json`; raises SeedError (one line, never the password). None when it is absent."""
    path = (directory or config.paths.SEEDS) / ADMIN_FILE
    if not path.exists():
        return None
    data = _read(path)
    try:
        admin = AdminSeed.model_validate(data)
    except ValidationError as e:
        first = e.errors()[0]
        field = ".".join(str(p) for p in first.get("loc", ())) or "(file)"
        raise SeedError(f"seed file {_name(path)}: {field}: is invalid") from None  # the message could quote the value
    try:
        auth.check_password_rules(admin.password, admin.email)
    except auth.PasswordRuleError as e:
        raise SeedError(f"seed file {_name(path)}: password: {e.reason}") from None
    return admin


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
    issued = issue_sample_links([e.key for e in seed.bookings])
    if issued:
        log.info("applied seed %s: %d manage links issued", BOOKINGS_FILE, issued)
    return created


def manage_email(facts: tuple, link: str, paid: tuple[int, int] = (0, 0),
                 voucher_until: dt.date | None = None) -> tuple[str, str]:
    """(subject, body) of the email that brings an existing sample Booking its Manage link: the reference, the date,
    the session, the Seats, how it was paid, the link and the change statement. No Sauna (FR-4).

    `paid` is (voucher_ore, card_ore) as `bq.charges` sums them: "Paid with voucher" and "Paid by card" each show
    when that part is above zero, so a Booking paid both ways shows both. `voucher_until` is the last valid date of
    the Voucher that paid it, which a Voucher for Seats given up keeps (`voucher.next_last_valid_date`)."""
    ref, seats, _wid, date, start, end = facts[:6]
    tz_name = facts[12]  # `db.manage.booking`'s Venue time zone; the kind and Sauna follow it
    tz = ZoneInfo(tz_name)
    lines = [
        "Manage your booking",
        "",
        f"Booking reference: {ref}",
        f"Date: {booking.long_date(date)}",
        f"Session: {start.astimezone(tz):%H:%M}–{end.astimezone(tz):%H:%M}",
        f"Seats: {seats}",
        *([f"Paid with voucher: {booking.nok(paid[0])}"
           + (f", valid until {booking.long_date(voucher_until)}" if voucher_until else "")] if paid[0] > 0 else []),
        *([f"Paid by card: {booking.nok(paid[1])}"] if paid[1] > 0 else []),
        "",
        manage.change_statement(),
        "",
        link,
    ]
    return f"Manage your booking: {ref}", "\n".join(lines)


def issue_sample_links(keys: list[uuid.UUID]) -> int:
    """Give each sample Booking that has no unrevoked Manage token, and whose Window has not ended, a Manage link and
    an Outbox email with it. Returns the links issued (0 on every start after the first)."""
    if not keys:
        return 0
    issued = 0
    for booking_id in db.run(lambda c: mq.samples_without_token(c, keys)):
        def work(c, booking_id=booking_id):
            token = manage.issue(c, booking_id)
            facts = mq.booking(c, booking_id)
            recipient = mq.recipient(c, booking_id)
            paid = bq.charges(c, booking_id)
            until = voucher.next_last_valid_date(c, booking_id) if paid[0] > 0 else None
            subject, body = manage_email(facts, manage.link(token), paid, until)
            outbox.send(c, recipient, subject, body, booking_id=booking_id)

        db.run(work)
        issued += 1
    return issued
