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


def test_0006_backfills_legacy_bookings_and_counts_only_active_ones(tmp_path, scratch_db):
    """AD-7 / AD-13 (Story 1.5): a legacy Booking gets a reference from its id, its `guest` text as the name (or
    "Guest"), an email that reaches no one, the current price and its time of booking as entry time; `guest` is gone.
    Afterwards only active Bookings take Seats, and the triggers keep their names."""
    before = tmp_path / "before"
    before.mkdir()
    for name in files():
        if name < "0006":
            shutil.copy(config.paths.MIGRATIONS / name, before / name)
    migrations.migrate(scratch_db, before)
    with psycopg.connect(scratch_db) as c:
        c.execute("INSERT INTO saunas (id, name, capacity, fill_order) VALUES (1, 'A', 20, 1), (2, 'B', 24, 2)")
        c.execute("INSERT INTO windows (during) VALUES (tstzrange('2026-12-01 09:00Z', '2026-12-01 10:30Z'))")
        c.execute("INSERT INTO bookings (window_id, seats, guest, created_at) VALUES "
                  "(1, 3, '  Ada  ', '2026-11-01 12:00Z'), (1, 40, '', '2026-11-02 12:00Z')")
    assert "0006_bookings_pay.sql" in migrations.migrate(scratch_db)
    with psycopg.connect(scratch_db) as c:
        rows = c.execute("SELECT id, reference, name, email, price_per_seat_ore, total_ore, status, "
                         "entry_time = created_at, session_id FROM bookings ORDER BY id").fetchall()
        assert rows == [(1, "00000001", "Ada", "unknown@example.invalid", 25000, 75000, "active", True, None),
                        (2, "00000002", "Guest", "unknown@example.invalid", 25000, 1000000, "active", True, None)]
        assert c.execute("SELECT count(*) FROM information_schema.columns "
                         "WHERE table_name = 'bookings' AND column_name = 'guest'").fetchone()[0] == 0
        assert c.execute("SELECT seats_left(1)").fetchone()[0] == 1
        c.execute("UPDATE bookings SET status = 'cancelled' WHERE id = 2")  # the trigger fires on status
        assert c.execute("SELECT booked, seats_left(1) FROM windows WHERE id = 1").fetchone() == (3, 41)
        triggers = c.execute("SELECT tgname FROM pg_trigger WHERE tgrelid = 'bookings'::regclass "
                             "AND NOT tgisinternal ORDER BY tgname").fetchall()
        assert triggers == [("a_lock_bookings",), ("t_bookings",)]
        with pytest.raises(psycopg.errors.CheckViolation):
            c.execute("UPDATE bookings SET status = 'gone' WHERE id = 1")
