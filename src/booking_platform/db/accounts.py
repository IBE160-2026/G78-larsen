"""SQL for accounts and the sign-in throttle (AD-11). Emails are lower-cased here, in SQL, the same way the
`accounts` CHECK does. Only Argon2id hashes are stored; this module never sees a readable password."""

from __future__ import annotations

import psycopg


def find(c: psycopg.Connection, email: str) -> tuple[int, str, str] | None:
    """(id, password_hash, role) of the account with this email (any case), or None."""
    return c.execute("SELECT id, password_hash, role FROM accounts WHERE email = lower(%s)", (email,)).fetchone()


def exists(c: psycopg.Connection, email: str) -> bool:
    return c.execute("SELECT 1 FROM accounts WHERE email = lower(%s)", (email,)).fetchone() is not None


def insert_if_absent(c: psycopg.Connection, email: str, password_hash: str, role: str) -> bool:
    """The seed (AD-18): a new account only when the email is absent, so a restart never rehashes. True when
    inserted."""
    return c.execute("INSERT INTO accounts (email, password_hash, role) VALUES (lower(%s), %s, %s) "
                     "ON CONFLICT (email) DO NOTHING", (email, password_hash, role)).rowcount == 1


def upsert(c: psycopg.Connection, email: str, password_hash: str, role: str) -> tuple[int, bool]:
    """`create-admin` (AD-18): a new account, or a new hash and role for an existing one. Returns (id, inserted)."""
    return c.execute("INSERT INTO accounts (email, password_hash, role) VALUES (lower(%s), %s, %s) "
                     "ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash, role = EXCLUDED.role "
                     "RETURNING id, (xmax = 0)", (email, password_hash, role)).fetchone()


def end_sessions(c: psycopg.Connection, account_id: int) -> int:
    """A changed password signs the account out everywhere: its session rows are deleted."""
    return c.execute("DELETE FROM sessions WHERE account_id = %s", (account_id,)).rowcount


def set_hash(c: psycopg.Connection, account_id: int, password_hash: str) -> None:
    """A rehash at sign-in when the Argon2 parameters have changed."""
    c.execute("UPDATE accounts SET password_hash = %s WHERE id = %s", (password_hash, account_id))


def lock_throttle(c: psycopg.Connection, email: str) -> tuple[int, bool]:
    """Upsert the throttle row of `lower(email)` and lock it `FOR UPDATE` (AD-11). Returns (failures, locked), where
    locked means `locked_until` is still after app_now(). Parallel attempts for one email queue here."""
    c.execute("INSERT INTO sign_in_throttle (email_lower) VALUES (lower(%s)) ON CONFLICT (email_lower) DO NOTHING",
              (email,))
    return c.execute("SELECT failures, coalesce(locked_until > app_now(), false) "
                     "FROM sign_in_throttle WHERE email_lower = lower(%s) FOR UPDATE", (email,)).fetchone()


def record_failure(c: psycopg.Connection, email: str, lock_minutes: int | None) -> None:
    """A refused attempt adds 1 to `failures`. With `lock_minutes`, `locked_until` becomes app_now() + that."""
    if lock_minutes is None:
        c.execute("UPDATE sign_in_throttle SET failures = failures + 1 WHERE email_lower = lower(%s)", (email,))
    else:
        c.execute("UPDATE sign_in_throttle SET failures = failures + 1, "
                  "locked_until = app_now() + %s * interval '1 minute' WHERE email_lower = lower(%s)",
                  (lock_minutes, email))


def reset_throttle(c: psycopg.Connection, email: str) -> None:
    """A success: `failures` 0 and no lock."""
    c.execute("UPDATE sign_in_throttle SET failures = 0, locked_until = NULL WHERE email_lower = lower(%s)", (email,))
