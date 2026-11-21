"""SQL for server-side sessions (AD-8). Only token hashes are stored; expiry is judged on app_now()."""

from __future__ import annotations

import psycopg


def lifetime(role_sql: str) -> str:
    """The one source of the sliding lifetimes (AD-8): Administrator 8 h, anonymous 24 h. `role_sql` is the SQL
    expression that yields the role (a column or a placeholder)."""
    return f"CASE {role_sql} WHEN 'admin' THEN interval '8 hours' ELSE interval '24 hours' END"


_ADMIN = "'admin'"  # the role as an SQL literal, for lifetime()


def create(c: psycopg.Connection, token_hash: bytes, role: str) -> int:
    return c.execute(
        "INSERT INTO sessions (token_hash, role, created_at, expires_at) "
        f"SELECT %(h)s, %(r)s, n, n + {lifetime('%(r)s')} "
        "FROM (SELECT app_now() AS n) x RETURNING id",
        {"h": token_hash, "r": role}).fetchone()[0]


def resolve_and_touch(c: psycopg.Connection, token_hash: bytes) -> tuple[int, str, int | None] | None:
    """(id, role, account_id) of a still-valid session, sliding its expiry in the same statement; None when unknown
    or expired. Run as one autocommit statement (`db.statement`), outside every action transaction (AD-4)."""
    return c.execute(
        f"UPDATE sessions SET expires_at = app_now() + {lifetime('role')} "
        "WHERE token_hash = %s AND expires_at > app_now() RETURNING id, role, account_id", (token_hash,)).fetchone()


def rotate(c: psycopg.Connection, sid: int, token_hash: bytes, account_id: int) -> bool:
    """Sign-in (AD-8): the same row gets a new token hash, the Administrator role, the account and a fresh
    Administrator lifetime. The old token names no row afterwards. False when the row is gone or expired."""
    return c.execute(
        f"UPDATE sessions SET token_hash = %(h)s, role = 'admin', account_id = %(a)s, "
        f"expires_at = app_now() + {lifetime(_ADMIN)} "
        "WHERE id = %(id)s AND expires_at > app_now()",
        {"h": token_hash, "a": account_id, "id": sid}).rowcount == 1


def delete(c: psycopg.Connection, sid: int) -> int:
    """Sign-out (FR-15): the row is gone, so its token names nothing."""
    return c.execute("DELETE FROM sessions WHERE id = %s", (sid,)).rowcount


def purge_expired(c: psycopg.Connection) -> int:
    return c.execute("DELETE FROM sessions WHERE expires_at <= app_now()").rowcount


def ensure_seed_session(c: psycopg.Connection, token_hash: bytes) -> int:
    """The id of the seed's one fixed session (AD-18), created on the first start. It never expires, so the startup
    purge keeps it, and no cookie can name it: no token hashes to its `token_hash`."""
    c.execute("INSERT INTO sessions (token_hash, role, created_at, expires_at) "
              "VALUES (%s, 'guest', app_now(), 'infinity') ON CONFLICT (token_hash) DO NOTHING", (token_hash,))
    return c.execute("SELECT id FROM sessions WHERE token_hash = %s", (token_hash,)).fetchone()[0]
