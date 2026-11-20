"""Blocks (FR-40). The store refuses a Block that would leave less Seat capacity than the Seats booked and held.
A single-statement write: the BEFORE trigger locks every overlapping Window in id order (AD-3)."""

from __future__ import annotations

import datetime as dt

from .. import db
from ..db import venue_admin as q


def block(sauna_id: int, start: dt.datetime, end: dt.datetime) -> int:
    return db.run(lambda c: q.insert_block(c, sauna_id, start, end))


def lift(block_id: int) -> int:
    return db.run(lambda c: q.delete_block(c, block_id))
