"""DR-4 / AD-15: the schema changes only through numbered SQL migrations, applied in order by the runner at startup
and at the start of the test run, recorded by full file name, never two with one number."""

from __future__ import annotations

import shutil
import subprocess
import time

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from booking_platform import config
from booking_platform.db import migrate as migrations
from conftest import ADMIN_URL, ROOT, TEST_URL, start_backend

BASELINE = "a92152ded6462f5e3c2d67935593d5180206e879"  # the commit before Story 1.1


def files() -> list[str]:
    return [p.name for p in migrations.migration_files()]


@pytest.fixture
def scratch_db():
    """An empty database of its own, dropped afterwards."""
    name = "booking_test_scratch"
    with psycopg.connect(ADMIN_URL, autocommit=True) as c:
        c.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))
        c.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    yield make_conninfo(TEST_URL, dbname=name)
    with psycopg.connect(ADMIN_URL, autocommit=True) as c:
        c.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))


def test_0001_is_the_slices_schema_unchanged():
    try:
        old = subprocess.run(["git", "rev-parse", f"{BASELINE}:src/booking_platform/schema.sql"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
        new = subprocess.run(["git", "hash-object", "migrations/0001_core.sql"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as e:
        pytest.skip(f"git history is not available: {e}")
    assert new == old


def test_the_files_are_numbered_and_in_order():
    assert files()[:3] == ["0001_core.sql", "0002_sessions.sql", "0003_named_store_refusals.sql"]


def test_the_test_database_records_every_migration_by_full_name(pg):
    got = [r[0] for r in pg.execute("SELECT name FROM schema_migrations ORDER BY name").fetchall()]
    pg.rollback()
    assert got == files()


def test_a_second_run_applies_nothing(database):
    assert migrations.migrate(database) == []


def test_a_fresh_database_gets_every_file_in_order(scratch_db):
    assert migrations.migrate(scratch_db) == files()
    assert migrations.migrate(scratch_db) == []


def test_a_legacy_database_counts_as_having_0001(scratch_db):
    """A database with `windows` but no `schema_migrations` (the slice's) gets 0001 recorded, and later files run."""
    with psycopg.connect(scratch_db) as c:
        c.execute((config.paths.MIGRATIONS / "0001_core.sql").read_text(encoding="utf-8"))
    assert migrations.migrate(scratch_db) == files()[1:]
    with psycopg.connect(scratch_db) as c:
        assert [r[0] for r in c.execute("SELECT name FROM schema_migrations ORDER BY name")] == files()
        assert c.execute("SELECT to_regclass('public.sessions') IS NOT NULL").fetchone()[0]


def test_two_files_with_one_number_are_refused(tmp_path, scratch_db):
    d = tmp_path / "migrations"
    d.mkdir()
    shutil.copy(config.paths.MIGRATIONS / "0001_core.sql", d / "0001_core.sql")
    (d / "0002_a.sql").write_text("CREATE TABLE a (x int);", encoding="utf-8")
    (d / "0002_b.sql").write_text("CREATE TABLE b (x int);", encoding="utf-8")
    with pytest.raises(migrations.MigrationError, match="share the number 0002"):
        migrations.migrate(scratch_db, d)
    with psycopg.connect(scratch_db) as c:  # nothing was applied
        assert c.execute("SELECT to_regclass('public.windows')").fetchone()[0] is None


def test_the_backend_refuses_to_start_on_a_duplicate_number(tmp_path, scratch_db):
    root = tmp_path / "root"
    shutil.copytree(config.paths.MIGRATIONS, root / "migrations")
    (root / "migrations" / "0002_duplicate.sql").write_text("SELECT 1;", encoding="utf-8")
    shutil.copytree(config.paths.SEEDS, root / "seeds")  # a valid seed, so the migrations are what stops it
    (root / "config").mkdir()
    b = start_backend(scratch_db, tmp_path, name="dup", wait=False, env={"BP_ROOT": str(root)})
    try:
        deadline = time.monotonic() + 90
        while b.proc.poll() is None and time.monotonic() < deadline:
            time.sleep(0.2)
        assert b.proc.returncode not in (None, 0), b.output()[-2000:]
        assert "share the number 0002" in b.output()
    finally:
        b.stop()


def test_ensure_database_creates_only_the_default_database(monkeypatch):
    name = "booking_test_ensure"
    url = make_conninfo(TEST_URL, dbname=name)
    assert migrations.ensure_database(url) is False  # not the default URL: left alone
    monkeypatch.setattr(config, "DEFAULT_DATABASE_URL", url)
    with psycopg.connect(ADMIN_URL, autocommit=True) as c:
        c.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))
    try:
        assert migrations.ensure_database(url) is True
        assert migrations.ensure_database(url) is False
    finally:
        with psycopg.connect(ADMIN_URL, autocommit=True) as c:
            c.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))
