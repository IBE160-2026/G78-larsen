"""SQL for server-side sessions (AD-8). Only token hashes are stored; expiry is judged on app_now()."""

from __future__ import annotations

import psycopg

# Sliding lifetimes per role: anonymous 24 h, Administrator 8 h.
_LIFETIME = "CASE role WHEN 'admin' THEN interval '8 hours' ELSE interval '24 hours' END"


def create(c: psycopg.Connection, token_hash: bytes, role: str) -> int:
    return c.execute(
        "INSERT INTO sessions (token_hash, role, created_at, expires_at) "
        "SELECT %(h)s, %(r)s, n, n + CASE %(r)s WHEN 'admin' THEN interval '8 hours' ELSE interval '24 hours' END "
        "FROM (SELECT app_now() AS n) x RETURNING id",
        {"h": token_hash, "r": role}).fetchone()[0]


def resolve_and_touch(c: psycopg.Connection, token_hash: bytes) -> tuple[int, str] | None:
    """(id, role) of a still-valid session, sliding its expiry in the same statement; None when unknown or expired.
    Run as one autocommit statement (`db.statement`), outside every action transaction (AD-4)."""
    return c.execute(
        f"UPDATE sessions SET expires_at = app_now() + {_LIFETIME} "
        "WHERE token_hash = %s AND expires_at > app_now() RETURNING id, role", (token_hash,)).fetchone()


def purge_expired(c: psycopg.Connection) -> int:
    return c.execute("DELETE FROM sessions WHERE expires_at <= app_now()").rowcount
