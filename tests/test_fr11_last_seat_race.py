"""FR-11 / CT-2 / CT-3: two parallel requests for the one remaining Seat, through the real API against real PostgreSQL,
100 repetitions per run. Exactly one Booking is created, Seats left becomes 0 and never negative, and the loser gets
`409 no_seat_free` with the fact `seats_left` 0, no payment row, no Outbox email and no stored key.

The 43 other Seats are one Booking written straight to the store (AD-21), with no payment, email or key, so every row
in those tables after a round belongs to the winner.
"""

from __future__ import annotations

from conftest import clear, raw_booking, state
from test_fr10_through_the_api import guests, left, parallel

ROUNDS = 100  # FR-11: 100 repetitions per run


def rows(pg, sql: str, *params) -> int:
    pg.rollback()
    n = pg.execute(sql, params).fetchone()[0]
    pg.rollback()
    return n


def test_the_last_seat_has_exactly_one_winner(api, world, pg):
    """FR-11: two parallel requests for the one remaining Seat create exactly one Booking. 100 repetitions."""
    for r in range(ROUNDS):
        clear(pg)
        pg.execute(raw_booking(1, 43))
        pg.commit()
        assert left(api) == 1
        ca, cb = guests(world, 2)
        a, b = parallel([lambda: ca.book(1, 1), lambda: cb.book(1, 1)])
        loser = cb if a.status_code == 201 else ca
        lost = b if a.status_code == 201 else a
        loser_session = loser.session_id
        ca.close(), cb.close()
        assert sorted([a.status_code, b.status_code]) == [201, 409], (r, a.text, b.text)
        assert lost.json() == {"detail": {"error": "no_seat_free", "seats_left": 0}}, (r, lost.text)
        assert left(api) == 0
        s = state(pg)
        assert s["booked"] == s["real_booked"] == 44 and s["left"] == 0, (r, s)
        # one row each, all the winner's: the loser has no payment, no email and no key
        assert rows(pg, "SELECT count(*) FROM bookings WHERE session_id IS NOT NULL") == 1, r
        assert rows(pg, "SELECT count(*) FROM payments") == 1, r
        assert rows(pg, "SELECT count(*) FROM outbox_emails") == 1, r
        assert rows(pg, "SELECT count(*) FROM idempotency_keys") == 1, r
        assert rows(pg, "SELECT count(*) FROM idempotency_keys WHERE session_id = %s", loser_session) == 0, r
        assert rows(pg, "SELECT count(*) FROM bookings WHERE session_id = %s", loser_session) == 0, r
