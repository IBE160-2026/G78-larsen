-- Story 4.1 (FR-25, AD-4, AD-8, AD-28, AD-29): Manage links, their grants, each Booking's own Cutoff and its version.
--
-- A Manage link carries a token in its fragment; the store keeps only its SHA-256 hash (`access_tokens`), and only
-- `services.manage` writes the table. Opening the link gives the browser's session a grant (`manage_grants`), which
-- cascades with the session, so sign-out ends it. Validity is judged by join, never stored: `manage_token_valid` (the
-- token is unrevoked and its Booking's Window has not ended) and `manage_grant_valid` (the one access predicate: the
-- grant was used in the last 30 minutes and its token is valid). `change_allowed` is the one Cutoff predicate.
-- The predicates are VOLATILE, because app_now() is.

-- The Seat Cutoff (AD-4): a Venue rule in `settings`, copied into each Booking when it is created.
ALTER TABLE settings
  ADD COLUMN cutoff_seats interval NOT NULL DEFAULT interval '12 hours'
    CONSTRAINT cutoff_seats_at_least_2_hours CHECK (cutoff_seats >= interval '2 hours');

-- The column default of `bookings.cutoff`, so a Booking written straight to the store gets the setting too.
-- `db.seats.insert_booking` still passes the value explicitly.
CREATE FUNCTION seat_cutoff() RETURNS interval LANGUAGE sql STABLE AS $$
  SELECT cutoff_seats FROM settings
$$;

-- Neither column is in the capacity triggers' column list (AD-7), so the backfill recomputes nothing.
ALTER TABLE bookings
  ADD COLUMN cutoff interval,
  ADD COLUMN version int NOT NULL DEFAULT 0;
UPDATE bookings SET cutoff = (SELECT cutoff_seats FROM settings);  -- every Booking is a Seat booking now
ALTER TABLE bookings
  ALTER COLUMN cutoff SET NOT NULL,
  ALTER COLUMN cutoff SET DEFAULT seat_cutoff();

-- Link tokens (AD-8, AD-28): only the hash. `purpose` is 'manage' now; later purposes extend the CHECK.
CREATE TABLE access_tokens (
  id bigserial PRIMARY KEY,
  purpose text NOT NULL CONSTRAINT access_tokens_purpose_known CHECK (purpose IN ('manage')),
  booking_id bigint CONSTRAINT access_tokens_booking_id_fkey REFERENCES bookings(id),
  token_hash bytea NOT NULL CONSTRAINT access_tokens_token_hash_key UNIQUE
    CONSTRAINT access_tokens_hash_length CHECK (length(token_hash) = 32),
  created_at timestamptz NOT NULL DEFAULT app_now(),
  revoked_at timestamptz,
  CONSTRAINT access_tokens_manage_has_booking CHECK (purpose <> 'manage' OR booking_id IS NOT NULL));
-- At most one unrevoked Manage token per Booking.
CREATE UNIQUE INDEX access_tokens_one_manage ON access_tokens (booking_id)
  WHERE purpose = 'manage' AND revoked_at IS NULL;

-- A session's grant to one Booking through one token. Never a second cookie (AD-8).
CREATE TABLE manage_grants (
  id bigserial PRIMARY KEY,
  session_id bigint NOT NULL
    CONSTRAINT manage_grants_session_id_fkey REFERENCES sessions(id) ON DELETE CASCADE,
  token_id bigint NOT NULL
    CONSTRAINT manage_grants_token_id_fkey REFERENCES access_tokens(id) ON DELETE CASCADE,
  last_used_at timestamptz NOT NULL,
  CONSTRAINT manage_grants_session_token_key UNIQUE (session_id, token_id));
CREATE INDEX manage_grants_token_id_idx ON manage_grants (token_id);

-- The Cutoff (AD-4): Changes are allowed while app_now() is before the Window's start minus the Booking's own Cutoff.
-- An unknown Booking allows nothing.
CREATE FUNCTION change_allowed(bid bigint) RETURNS boolean LANGUAGE sql VOLATILE AS $$
  SELECT COALESCE((SELECT app_now() < lower(w.during) - b.cutoff
                   FROM bookings b JOIN windows w ON w.id = b.window_id
                   WHERE b.id = bid), false)
$$;

-- A Manage token opens its Booking while it is unrevoked and app_now() is before the end of the Booking's current
-- Window (AD-28, Validity). An unknown token is not valid.
CREATE FUNCTION manage_token_valid(tid bigint) RETURNS boolean LANGUAGE sql VOLATILE AS $$
  SELECT COALESCE((SELECT t.revoked_at IS NULL AND app_now() < upper(w.during)
                   FROM access_tokens t JOIN bookings b ON b.id = t.booking_id JOIN windows w ON w.id = b.window_id
                   WHERE t.id = tid AND t.purpose = 'manage'), false)
$$;

-- The one access predicate (AD-28, Grant): the session holds a grant for the Booking, used in the last 30 minutes,
-- through a valid token.
CREATE FUNCTION manage_grant_valid(sid bigint, bid bigint) RETURNS boolean LANGUAGE sql VOLATILE AS $$
  SELECT EXISTS (SELECT 1 FROM manage_grants g JOIN access_tokens t ON t.id = g.token_id
                 WHERE g.session_id = sid AND t.booking_id = bid AND t.purpose = 'manage'
                   AND app_now() < g.last_used_at + interval '30 minutes'
                   AND manage_token_valid(t.id))
$$;
