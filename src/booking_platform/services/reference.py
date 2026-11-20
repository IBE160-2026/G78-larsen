"""The one way to create a Booking reference (AD-20, FR-8): 8 upper-case Crockford base32 characters, claimed by the
Booking insert itself with `ON CONFLICT (reference) DO NOTHING`, at most 5 candidates. No savepoint and no exception
for a clash, so a capacity refusal of the same insert is never swallowed. Every Booking creator uses it: the Seat flow,
the seed, and later the Whole-sauna flow and a split."""

from __future__ import annotations

import re
import secrets
from typing import Callable

from .errors import Refused

ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"  # Crockford base32: no I, L, O or U
LENGTH = 8
TRIES = 5
PATTERN = re.compile(r"[0-9A-HJKMNP-TV-Z]{8}")


def candidate() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(LENGTH))


def is_reference(text: str) -> bool:
    """True for a well-formed reference: exactly 8 upper-case Crockford characters."""
    return PATTERN.fullmatch(text) is not None


def claim(insert: Callable[[str], int | None]) -> tuple[int, str]:
    """Run `insert(reference)` with new candidates until it returns a row id. `insert` must insert with
    `ON CONFLICT (reference) DO NOTHING RETURNING id` and return None on a clash. Returns (id, reference). Five
    clashes in a row (practically impossible: 32^8 references) is `try_again`."""
    for _ in range(TRIES):
        reference = candidate()
        row_id = insert(reference)
        if row_id is not None:
            return row_id, reference
    raise Refused("try_again")
