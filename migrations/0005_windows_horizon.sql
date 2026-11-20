-- The Booking horizon, the Window schedule and the time predicates (Story 1.4, FR-2, FR-3, FR-13, AD-4, AD-18).
--
-- Every time rule reads app_now(), and each rule is one SQL function that the listing and every later action call.
-- No timestamptz is cast to a date or a time without `AT TIME ZONE settings.venue_tz`.

-- The Booking horizon (FR-2): from the moment of booking to the Window's start. `windows_generated_through` is the
-- high-water mark of `windows.ensure_generated()`: the last Venue date it has generated (NULL = none yet). A date
-- at or before the mark is never generated again, so a removed Window stays removed.
ALTER TABLE settings
  ADD COLUMN booking_horizon_days int NOT NULL DEFAULT 28
    CONSTRAINT booking_horizon_days_range CHECK (booking_horizon_days BETWEEN 1 AND 31),
  ADD COLUMN windows_generated_through date;

-- The daily Window schedule in Venue time (AD-18): seeded from `seeds/venue.json` when empty. No two rows overlap;
-- back-to-back rows are allowed (FR-13 E1, E2). A row never crosses midnight.
CREATE TABLE window_schedule (
  start_time time PRIMARY KEY,
  end_time time NOT NULL,
  CONSTRAINT window_schedule_end_after_start CHECK (end_time > start_time),
  CONSTRAINT window_schedule_never_overlap EXCLUDE USING gist (
    tsrange(date '2000-01-01' + start_time, date '2000-01-01' + end_time, '[)') WITH &&));

-- The Venue date of app_now(), and the last Venue date the Booking horizon reaches.
CREATE FUNCTION venue_today() RETURNS date LANGUAGE sql VOLATILE AS $$
  SELECT (app_now() AT TIME ZONE st.venue_tz)::date FROM settings st
$$;
-- The horizon days are added in Venue local time, so a daylight-saving change does not shift the end by an hour.
CREATE FUNCTION horizon_end() RETURNS date LANGUAGE sql VOLATILE AS $$
  SELECT ((app_now() AT TIME ZONE st.venue_tz) + make_interval(days => st.booking_horizon_days))::date FROM settings st
$$;

-- The Venue date a Window starts on.
CREATE FUNCTION venue_date(wid int) RETURNS date LANGUAGE sql STABLE AS $$
  SELECT (lower(w.during) AT TIME ZONE st.venue_tz)::date FROM windows w, settings st WHERE w.id = wid
$$;
-- The Window starts no later than the Booking horizon from now (the days added in Venue local time).
CREATE FUNCTION within_horizon(wid int) RETURNS boolean LANGUAGE sql VOLATILE AS $$
  SELECT lower(w.during)
         <= ((app_now() AT TIME ZONE st.venue_tz) + make_interval(days => st.booking_horizon_days))
            AT TIME ZONE st.venue_tz
  FROM windows w, settings st WHERE w.id = wid
$$;
-- The Window has started (it may still be bookable until booking_deadline).
CREATE FUNCTION window_started(wid int) RETURNS boolean LANGUAGE sql VOLATILE AS $$
  SELECT app_now() >= lower(w.during) FROM windows w WHERE w.id = wid
$$;

-- t_settings recomputed every Window on any change of the row. It now runs only when a column it depends on is
-- set, so moving `windows_generated_through` (or a Venue fact) neither recomputes nor locks every Window.
-- The release behaviour is unchanged.
DROP TRIGGER t_settings ON settings;
CREATE TRIGGER t_settings BEFORE UPDATE OF release_on, release_time, venue_tz ON settings
  FOR EACH ROW EXECUTE FUNCTION trg_settings();
