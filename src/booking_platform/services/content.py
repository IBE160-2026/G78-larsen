"""Text shared by pages and emails (AD-12, AD-17): `content/*.json`, each `{"paragraphs": [...]}`. The frontend build
reads the same files (copied to `frontend/content/` by `frontend/scripts/run-next.mjs`). A file is read once."""

from __future__ import annotations

import functools
import json

from .. import config

TERMS_SEATS = "terms-seats"  # the booking terms of a Seat booking (FR-5)
RECEPTION = "reception"  # what happens next (FR-8); never under a heading


@functools.cache
def paragraphs(name: str) -> tuple[str, ...]:
    data = json.loads((config.paths.CONTENT / f"{name}.json").read_text(encoding="utf-8-sig"))
    items = data["paragraphs"]
    if not isinstance(items, list) or not items or not all(isinstance(p, str) and p for p in items):
        raise ValueError(f"content/{name}.json: paragraphs must be a list of text")
    return tuple(items)
