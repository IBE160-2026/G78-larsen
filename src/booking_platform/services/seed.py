"""The seed (AD-18): `seeds/venue.json`, applied after the migrations and before the app serves, in every
environment.

The seed inserts the Saunas that are absent. The Venue values of the `settings` row come from 0004's column
defaults, which equal the seed (pinned by `tests/test_fr01_venue.py`); the seed only fills such a column when it is
NULL. It never overwrites, so after the first start the store owns every value. The file goes through the same validation as Administrator input
(`services.venue`, IV-6). A file that cannot be read or is invalid is a `SeedError` whose message is one line that
names the file and the field.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import ValidationError

from .. import config, db
from ..db import venue as q
from .venue import VenueSeed

log = logging.getLogger("booking_platform.seed")

VENUE_FILE = "venue.json"


class SeedError(Exception):
    """The seed cannot be used. The message is one line, fit to print before exiting."""


def _name(path: Path) -> str:
    try:
        return path.relative_to(config.paths.ROOT).as_posix()
    except ValueError:
        return str(path)


def load(directory: Path | None = None) -> VenueSeed:
    """Read and validate `seeds/venue.json`; raises SeedError."""
    path = (directory or config.paths.SEEDS) / VENUE_FILE
    name = _name(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))  # a BOM is accepted
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise SeedError(f"seed file {name} cannot be read: {type(e).__name__}") from None
    try:
        return VenueSeed.model_validate(data)
    except ValidationError as e:
        first = e.errors()[0]
        field = ".".join(str(p) for p in first.get("loc", ())) or "(file)"
        message = " ".join(str(first.get("msg", "is invalid")).split())
        raise SeedError(f"seed file {name}: {field}: {message}") from None


def apply(directory: Path | None = None) -> int:
    """Apply the seed in one transaction. Returns the number of Saunas inserted (0 on every start after the first)."""
    seed = load(directory)

    def work(c):
        q.seed_settings(c, seed.venue.row())
        return sum(q.seed_sauna(c, s.id, s.name, s.capacity, s.fill_order) for s in seed.saunas)

    inserted = db.run(work)
    log.info("applied seed %s: %d saunas inserted", VENUE_FILE, inserted)
    return inserted
