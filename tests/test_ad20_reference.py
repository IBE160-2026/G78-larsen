"""AD-20: `services.reference.claim` tries a fresh 8-character Crockford candidate for every clash, at most 5 times,
and then answers `try_again`. A unit test with a stub insert: no store, no backend."""

from __future__ import annotations

import pytest

from booking_platform.services import reference
from booking_platform.services.errors import Refused


def stub(clashes: int, row_id: int = 42):
    """An insert that reports a taken reference `clashes` times, then inserts; it records every candidate."""
    tried: list[str] = []

    def insert(ref: str) -> int | None:
        tried.append(ref)
        return None if len(tried) <= clashes else row_id

    return insert, tried


@pytest.mark.parametrize("clashes", [0, 1, reference.TRIES - 1])
def test_a_clash_tries_a_fresh_candidate_and_the_first_free_one_is_used(clashes):
    insert, tried = stub(clashes)
    row_id, ref = reference.claim(insert)
    assert (row_id, ref) == (42, tried[-1])
    assert len(tried) == clashes + 1
    assert all(reference.is_reference(t) for t in tried)
    assert len(set(tried)) == len(tried)  # a fresh candidate each try (32^8 makes a repeat practically impossible)


def test_five_clashes_in_a_row_is_try_again():
    insert, tried = stub(reference.TRIES)
    with pytest.raises(Refused) as e:
        reference.claim(insert)
    assert e.value.code == "try_again"
    assert len(tried) == reference.TRIES == 5
