"""SQL for server-side sessions (AD-8). Only token hashes are stored; expiry is judged on app_now()."""

from __future__ import annotations

import psycopg


def lifetime(role_sql: str) -> str:
    """The one source of the sliding lifetimes (AD-8): Administrator 8 h, anonymous 24 h. `role_sql` is the SQL
    expression that yields the role (a column or a placeholder)."""
    return f"CASE {role_sql} WHEN 'admin' THEN interval '8 hours' ELSE interval '24 hours' END"


def create(c: psycopg.Connection, token_hash: bytes, role: str) -> int:
    return c.execute(
        "INSERT INTO sessions (token_hash, role, created_at, expires_at) "
        f"SELECT %(h)s, %(r)s, n, n + {lifetime('%(r)s')} "
        "FROM (SELECT app_now() AS n) x RETURNING id",
        {"h": token_hash, "r": role}).fetchone()[0]


def resolve_and_touch(c: psycopg.Connection, token_hash: bytes) -> tuple[int, str] | None:
    """(id, role) of a still-valid session, sliding its expiry in the same statement; None when unknown or expired.
    Run as one autocommit statement (`db.statement`), outside every action transaction (AD-4)."""
    return c.execute(
        f"UPDATE sessions SET expires_at = app_now() + {lifetime('role')} "
        "WHERE token_hash = %s AND expires_at > app_now() RETURNING id, role", (token_hash,)).fetchone()


def purge_expired(c: psycopg.Connection) -> int:
    return c.execute("DELETE FROM sessions WHERE expires_at <= app_now()").rowcount
