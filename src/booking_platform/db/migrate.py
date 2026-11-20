"""The migration runner (AD-15): numbered plain SQL files in `migrations/`, applied in order under an advisory lock,
recorded by full file name in `schema_migrations`.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import psycopg
from psycopg import sql

from .. import config

log = logging.getLogger("booking_platform.migrate")

_NAME = re.compile(r"^(\d{4})_[a-z0-9_]+\.sql$")
_LOCK_KEY = 7816201  # the advisory lock that serialises runners


class MigrationError(Exception):
    """The migrations cannot be applied. The message is one line."""


def migration_files(directory: Path | None = None) -> list[Path]:
    """The migration files in number order. Refuses badly named files and two files with one number."""
    directory = directory or config.paths.MIGRATIONS
    files = sorted(p for p in directory.iterdir() if p.suffix == ".sql")
    seen: dict[str, str] = {}
    for p in files:
        m = _NAME.match(p.name)
        if not m:
            raise MigrationError(f"migration file name {p.name!r} is not NNNN_short_name.sql")
        if m.group(1) in seen:
            raise MigrationError(f"migrations {seen[m.group(1)]} and {p.name} share the number {m.group(1)}")
        seen[m.group(1)] = p.name
    return files


def ensure_database(url: str) -> bool:
    """Create the database of the default URL (`booking_dev`) through the server's `postgres` database when it is
    missing. Any other URL is left alone. Returns True when it created the database."""
    if url != config.DEFAULT_DATABASE_URL:
        return False
    info = psycopg.conninfo.conninfo_to_dict(url)
    name = info["dbname"]
    admin = psycopg.conninfo.make_conninfo(url, dbname="postgres")
    with psycopg.connect(admin, autocommit=True) as c:
        if c.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone():
            return False
        c.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        log.info("created database %s", name)
        return True


def migrate(url: str | None = None, directory: Path | None = None) -> list[str]:
    """Apply every migration not yet recorded, in order, each in its own transaction. Returns the names applied.

    A database that has `windows` but no `schema_migrations` (the slice's) counts as having 0001 applied."""
    files = migration_files(directory)
    with psycopg.connect(url or config.settings().database_url, autocommit=True) as c:
        c.execute("SELECT pg_advisory_lock(%s)", (_LOCK_KEY,))
        try:
            has_log = c.execute("SELECT to_regclass('public.schema_migrations') IS NOT NULL").fetchone()[0]
            if not has_log:
                legacy = c.execute("SELECT to_regclass('public.windows') IS NOT NULL").fetchone()[0]
                with c.transaction():
                    c.execute("CREATE TABLE schema_migrations ("
                              "name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())")
                    first = next((p.name for p in files if p.name.startswith("0001_")), None)
                    if legacy and first:
                        c.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (first,))
            done = {r[0] for r in c.execute("SELECT name FROM schema_migrations").fetchall()}
            applied = []
            for p in files:
                if p.name in done:
                    continue
                with c.transaction():
                    c.execute(p.read_text(encoding="utf-8"))
                    c.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (p.name,))
                log.info("applied migration %s", p.name)
                applied.append(p.name)
            return applied
        finally:
            c.execute("SELECT pg_advisory_unlock(%s)", (_LOCK_KEY,))
