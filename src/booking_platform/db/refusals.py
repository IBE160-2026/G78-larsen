"""Store refusals by constraint name (AD-1).

`Refused` and `StoreError` are defined here, at the bottom of the layers, so that `db` can raise them without
importing anything above it; `services.errors` re-exports both, and every other layer uses them from there.
"""

from __future__ import annotations


class Refused(Exception):
    """The one refusal type: a code (declared in api/errors.py) and facts for the response envelope."""

    def __init__(self, code: str, **facts):
        super().__init__(code)
        self.code = code
        self.facts = facts


class StoreError(Exception):
    """A store error that is not a mapped refusal. Carries only the SQLSTATE and constraint name, never store text."""

    def __init__(self, sqlstate: str | None, constraint: str | None):
        super().__init__(f"sqlstate={sqlstate} constraint={constraint}")
        self.sqlstate = sqlstate
        self.constraint = constraint


MAP: dict[str, str] = {
    # a session deleted (signed out, purged) between the request's session check and its write (AD-8): before the
    # `*_fkey` rule below, so this is `401 no_session`, never `404 not_found`
    "bookings_session_id_fkey": "no_session",
    "holds_session_id_fkey": "no_session",
    "idempotency_keys_session_id_fkey": "no_session",
    # one key, two requests at once for different Windows: the loser's key is already known (AD-9)
    "idempotency_keys_key_key": "invalid_key",
    # capacity (AD-2)
    "booked_within_capacity": "no_seat_free",
    # named trigger refusals (0003_named_store_refusals.sql); window_out_of_step stays unmapped: it is a 500. The
    # Whole-sauna rule is the one name `whole_bookable` (0013); it is mapped to `sauna_unavailable` with the
    # Whole-sauna booking (Story 5.2), and until then nothing outside tests writes `whole_bookings`. `whole_pairing`
    # and `booking_kind_fixed` stay unmapped: they are 500s (AD-1, AD-23)
    "mark_not_bookable": "rule_refused",
    "mark_seats_placed": "rule_refused",
    "release_not_due": "rule_refused",
    # the slice's UNIQUE keys
    "whole_bookings_window_id_sauna_id_key": "already_exists",
    "marks_window_id_sauna_id_key": "already_exists",
    "holds_session_id_window_id_key": "already_exists",
    "saunas_fill_order_key": "already_exists",
}


def code_for(constraint: str | None) -> str | None:
    """The refusal code for a constraint name, or None when the error is not a refusal."""
    if not constraint:
        return None
    if constraint in MAP:
        return MAP[constraint]
    if constraint.endswith("_fkey"):
        return "not_found"
    return None
