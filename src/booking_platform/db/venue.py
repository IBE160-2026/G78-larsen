"""SQL for the Venue facts (FR-1, AD-16) and their seed (AD-18): the Venue columns of the one `settings` row and
the Saunas in Fill order. Every function takes the connection of the caller's transaction (`db.run`)."""

from __future__ import annotations

import psycopg

# The seed-owned Venue columns of `settings`, in the order the functions below use.
VENUE_COLUMNS = ("venue_name", "address_lines", "phone", "email", "opening_time", "closing_time", "session_minutes",
                 "price_per_seat_ore")


def venue_facts(c: psycopg.Connection) -> tuple | None:
    """The Venue columns of the `settings` row, in `VENUE_COLUMNS` order."""
    return c.execute(f"SELECT {', '.join(VENUE_COLUMNS)} FROM settings").fetchone()


def saunas(c: psycopg.Connection) -> list[tuple]:
    """(id, name, capacity) of every Sauna, in Fill order."""
    return c.execute("SELECT id, name, capacity FROM saunas ORDER BY fill_order").fetchall()


def seed_settings(c: psycopg.Connection, values: tuple) -> None:
    """Insert the `settings` row when it is absent, otherwise fill only a seed-owned column that is NULL. In practice
    the row always exists (0001 inserts it) and its Venue values come from 0004's column defaults, which equal the
    seed (`tests/test_fr01_venue.py` pins this), so this writes nothing. A value already in the store is never
    overwritten, and a row with nothing to fill is not updated at all (so `t_settings` does not run)."""
    cols = ", ".join(VENUE_COLUMNS)
    marks = ", ".join(["%s"] * len(VENUE_COLUMNS))
    c.execute(f"INSERT INTO settings ({cols}) VALUES ({marks}) ON CONFLICT (only_row) DO NOTHING", values)
    fill = ", ".join(f"{col} = COALESCE({col}, %s)" for col in VENUE_COLUMNS)
    any_null = " OR ".join(f"{col} IS NULL" for col in VENUE_COLUMNS)
    c.execute(f"UPDATE settings SET {fill} WHERE {any_null}", values)


def seed_sauna(c: psycopg.Connection, sauna_id: int, name: str, capacity: int, fill_order: int) -> bool:
    """Insert a Sauna that is absent; one that exists is left as the store has it, and so is a store Sauna that
    already holds the seeded Fill order (no conflict target). True when it was inserted."""
    return c.execute("INSERT INTO saunas (id, name, capacity, fill_order) VALUES (%s, %s, %s, %s) "
                     "ON CONFLICT DO NOTHING", (sauna_id, name, capacity, fill_order)).rowcount == 1
