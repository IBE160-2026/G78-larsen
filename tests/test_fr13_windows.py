"""FR-13, NFR-3, AD-4, AD-18: the Window schedule and Window generation.

The seed's schedule is refused when rows partly overlap, are identical or nested (E1), and accepted back to back
(E2); the store refuses the same overlaps itself. A row that starts or ends in an hour skipped or repeated on a
daylight-saving change day of the Venue time zone is refused. `windows.ensure_generated()` (run by every Window
listing) inserts the scheduled Windows from today to the end of the Booking horizon once, keeps their local clock
times across a daylight-saving change, and never re-inserts a date at or before its high-water mark. The clock
moves only through `clock.off` (`set_clock`).
"""

from __future__ import annotations

import datetime as dt
import json
import shutil
import time

import psycopg
import pytest
from psycopg import errors, sql
from psycopg.conninfo import make_conninfo

from booking_platform import config
from booking_platform.services import seed
from booking_platform.services.windows import ScheduleRow, check_schedule
from conftest import ADMIN_URL, TEST_URL, set_clock, start_backend

SEED = json.loads((config.paths.SEEDS / "venue.json").read_text(encoding="utf-8"))
SLOTS = ["10:00", "11:30", "13:00", "14:30", "16:00", "17:30", "19:00", "20:30"]
TODAY = dt.date(2026, 12, 1)  # the Venue date of conftest.EARLY


def rows(*pairs: tuple[str, str]) -> list[ScheduleRow]:
    return [ScheduleRow(start=a, end=b) for a, b in pairs]


def _seed_dir(tmp_path, schedule) -> object:
    d = tmp_path / "seeds"
    d.mkdir(exist_ok=True)
    data = json.loads(json.dumps(SEED))
    data["schedule"] = schedule
    (d / "venue.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return d


def count(pg, where: str = "true", params: tuple = ()) -> int:
    pg.rollback()
    n = pg.execute(f"SELECT count(*) FROM windows WHERE {where}", params).fetchone()[0]
    pg.rollback()
    return n


def mark(pg):
    pg.rollback()
    m = pg.execute("SELECT windows_generated_through FROM settings").fetchone()[0]
    pg.rollback()
    return m


# ------------------------------------------------------------------ the seed's schedule


def test_the_seed_holds_eight_windows_a_day_of_1_h_30_min():
    assert [(r["start"], r["end"]) for r in SEED["schedule"]] == [
        ("10:00", "11:30"), ("11:30", "13:00"), ("13:00", "14:30"), ("14:30", "16:00"), ("16:00", "17:30"),
        ("17:30", "19:00"), ("19:00", "20:30"), ("20:30", "22:00")]
    assert len(seed.load().schedule) == 8


def test_the_store_holds_the_seeded_schedule(pg, server):
    got = pg.execute("SELECT to_char(start_time, 'HH24:MI'), to_char(end_time, 'HH24:MI') FROM window_schedule "
                     "ORDER BY start_time").fetchall()
    pg.rollback()
    assert [a for a, _ in got] == SLOTS


@pytest.mark.parametrize("pairs", [
    (("10:00", "11:30"), ("11:00", "12:30")),  # partly overlapping
    (("10:00", "11:30"), ("10:00", "11:30")),  # identical
    (("10:00", "13:00"), ("11:00", "12:00")),  # nested
    (("11:00", "12:00"), ("10:00", "13:00")),  # nested, listed the other way round
], ids=["partly", "identical", "nested", "nested-reversed"])
def test_e1_overlapping_rows_are_refused(pairs, tmp_path, pg, server):
    with pytest.raises(ValueError, match="overlap"):
        check_schedule(rows(*pairs))
    # the seed file names the file and the field in one line
    d = _seed_dir(tmp_path, [{"start": a, "end": b} for a, b in pairs])
    with pytest.raises(seed.SeedError) as e:
        seed.load(d)
    msg = str(e.value).replace("\\", "/")
    assert "\n" not in msg and "venue.json" in msg, msg
    assert "schedule" in msg and "overlap" in msg, msg
    # the store refuses the same rows itself (the test rolls back, so the seeded schedule stays)
    (a1, b1), (a2, b2) = pairs
    pg.execute("DELETE FROM window_schedule")
    with pytest.raises((errors.ExclusionViolation, errors.UniqueViolation)):
        pg.execute("INSERT INTO window_schedule VALUES (%s, %s), (%s, %s)", (a1, b1, a2, b2))
    pg.rollback()


def test_e2_back_to_back_rows_are_accepted(pg, server):
    check_schedule(rows(("15:00", "16:30"), ("16:30", "18:00")))
    pg.execute("DELETE FROM window_schedule")
    pg.execute("INSERT INTO window_schedule VALUES ('15:00', '16:30'), ('16:30', '18:00')")
    assert pg.execute("SELECT count(*) FROM window_schedule").fetchone()[0] == 2
    pg.rollback()  # the seeded schedule stays


@pytest.mark.parametrize("pair", [("02:30", "04:00"), ("01:00", "02:30"), ("02:00", "03:30")],
                         ids=["starts-02:30", "ends-02:30", "starts-02:00"])
def test_a_time_skipped_or_repeated_on_a_daylight_saving_day_is_refused(pair):
    with pytest.raises(ValueError, match="daylight saving"):
        check_schedule(rows(pair), "Europe/Oslo", TODAY)


def test_times_outside_the_changed_hour_and_another_zone_are_accepted():
    check_schedule(rows(("00:30", "01:30"), ("03:00", "04:30")), "Europe/Oslo", TODAY)  # 02:00 itself is skipped
    check_schedule(rows(("02:30", "04:00")), "UTC", TODAY)  # UTC has no daylight saving


def test_the_check_works_from_29_february():
    check_schedule(rows(("10:00", "11:30")), "Europe/Oslo", dt.date(2028, 2, 29))
    with pytest.raises(ValueError, match="daylight saving"):
        check_schedule(rows(("02:30", "04:00")), "Europe/Oslo", dt.date(2028, 2, 29))


@pytest.mark.parametrize("row", [{"start": "11:30", "end": "10:00"}, {"start": "10:00", "end": "10:00"},
                                 {"start": "10:00", "end": "11:30", "sauna": 1}],
                         ids=["backwards", "empty", "unknown-field"])
def test_a_malformed_row_is_refused(tmp_path, row):
    with pytest.raises(seed.SeedError, match="schedule"):
        seed.load(_seed_dir(tmp_path, [row]))


@pytest.fixture
def fresh_db(database):
    name = "booking_test_schedule"
    with psycopg.connect(ADMIN_URL, autocommit=True) as c:
        c.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))
        c.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    yield make_conninfo(TEST_URL, dbname=name)
    with psycopg.connect(ADMIN_URL, autocommit=True) as c:
        c.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))


def test_an_overlapping_seed_schedule_stops_startup_with_one_line(fresh_db, tmp_path):
    root = tmp_path / "root"
    shutil.copytree(config.paths.MIGRATIONS, root / "migrations")
    (root / "config").mkdir()
    _seed_dir(root, [{"start": "10:00", "end": "11:30"}, {"start": "11:00", "end": "12:30"}])
    b = start_backend(fresh_db, tmp_path, name="overlap", wait=False, env={"BP_ROOT": str(root)})
    try:
        deadline = time.monotonic() + 90
        while b.proc.poll() is None and time.monotonic() < deadline:
            time.sleep(0.2)
        assert b.proc.returncode not in (None, 0), b.output()[-2000:]
        lines = [line for line in b.output().splitlines() if "venue.json" in line]
        assert len(lines) == 1, b.output()[-2000:]
        assert "seeds/venue.json" in lines[0] and "schedule" in lines[0], lines[0]
        assert "Traceback" not in b.output()
    finally:
        b.stop()


def test_a_fresh_start_seeds_the_schedule_and_generates_the_horizon(fresh_db, tmp_path):
    b = start_backend(fresh_db, tmp_path, name="fresh")
    b.stop()
    with psycopg.connect(fresh_db) as c:
        today, end, gen = c.execute("SELECT venue_today(), horizon_end(), windows_generated_through FROM settings"
                                    ).fetchone()
        n = c.execute("SELECT count(*) FROM windows").fetchone()[0]
        days = c.execute("SELECT count(DISTINCT venue_date(id)) FROM windows").fetchone()[0]
    assert gen == end
    assert days == (end - today).days + 1
    assert n == 8 * days


# ------------------------------------------------------------------ generation through the listing


def test_the_first_listing_generates_today_to_the_horizon_end_and_a_second_adds_none(api, pg):
    assert count(pg) == 3 and mark(pg) is None
    body = api.get("/api/windows").json()
    assert body["today"] == "2026-12-01" and body["horizon_end"] == "2026-12-29" and body["horizon_days"] == 28
    # 29 Venue dates of 8 Windows; the three world Windows sit on scheduled slots and are kept, not duplicated
    assert count(pg) == 29 * 8
    assert count(pg, "id <= 3") == 3
    assert mark(pg) == dt.date(2026, 12, 29)
    per_day = pg.execute("SELECT venue_date(id), count(*) FROM windows GROUP BY 1 ORDER BY 1").fetchall()
    pg.rollback()
    assert [d for d, _ in per_day] == [TODAY + dt.timedelta(days=i) for i in range(29)]
    assert {n for _, n in per_day} == {8}
    api.get("/api/windows")
    api.get("/api/windows", params=dict(date="2026-12-02"))
    assert count(pg) == 29 * 8


def test_generation_moves_with_the_clock_and_never_reinserts_a_removed_window(api, pg):
    api.get("/api/windows")
    removed = pg.execute("SELECT id FROM windows WHERE venue_date(id) = '2026-12-10' ORDER BY lower(during) LIMIT 1"
                         ).fetchone()[0]
    pg.execute("DELETE FROM windows WHERE id = %s", (removed,))
    pg.commit()
    set_clock(pg, dt.datetime(2026, 12, 3, 3, 0, tzinfo=dt.timezone.utc))
    body = api.get("/api/windows").json()
    assert body["horizon_end"] == "2026-12-31"
    assert count(pg, "id = %s", (removed,)) == 0
    assert count(pg, "venue_date(id) = '2026-12-10'") == 7
    assert count(pg, "venue_date(id) IN ('2026-12-30', '2026-12-31')") == 16
    assert mark(pg) == dt.date(2026, 12, 31)


def test_generation_takes_no_lock_on_existing_windows(api, pg, database):
    """A Window locked by another transaction does not block generation (no recompute of existing Windows)."""
    api.get("/api/windows")
    set_clock(pg, dt.datetime(2026, 12, 2, 3, 0, tzinfo=dt.timezone.utc))
    with psycopg.connect(database) as other:
        other.execute("SELECT 1 FROM windows WHERE id = 1 FOR UPDATE")
        other.execute("SELECT 1 FROM settings FOR KEY SHARE")
        r = api.get("/api/windows", timeout=10)
        assert r.status_code == 200
        other.rollback()
    assert mark(pg) == dt.date(2026, 12, 30)


def test_windows_keep_their_local_clock_times_across_daylight_saving(api, pg):
    set_clock(pg, dt.datetime(2027, 3, 20, 3, 0, tzinfo=dt.timezone.utc))
    for date, offset in (("2027-03-27", "+01:00"), ("2027-03-28", "+02:00"), ("2027-03-29", "+02:00")):
        body = api.get("/api/windows", params=dict(date=date)).json()
        assert [w["start"][11:16] for w in body["windows"]] == SLOTS, date
        assert [w["end"][11:16] for w in body["windows"]][-1] == "22:00"
        assert {w["start"][-6:] for w in body["windows"]} == {offset}, date
    utc = pg.execute("SELECT to_char(lower(during) AT TIME ZONE 'UTC', 'HH24:MI') FROM windows "
                     "WHERE venue_date(id) = '2027-03-29' ORDER BY lower(during) LIMIT 1").fetchone()[0]
    pg.rollback()
    assert utc == "08:00"
