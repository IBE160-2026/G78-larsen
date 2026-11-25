-- Story 5.1 (FR-29, FR-30, AD-2, AD-4, AD-23, AD-24): the Whole-sauna booking shape, its pairing with the capacity row,
-- the one FR-29 predicate, the Whole-sauna Cutoff and the price per Sauna. The §4.9 migration; its number was taken
-- when the story started (re-check at merge, AD-15).
--
-- One Booking table (AD-23): a Whole-sauna booking is a `bookings` row with `kind = 'whole'`, `sauna_id` set and
-- `seats` and `price_per_seat_ore` NULL; a Seat booking has `kind = 'seats'`, 1 to 10 `seats`, a price per Seat and no
-- Sauna. One CHECK ties the columns, and `b_kind_fixed` refuses any change of `kind` (a named constraint, a 500 under
-- AD-1). `whole_bookings` stays the capacity row, now with `booking_id UNIQUE NOT NULL`. It exists exactly while its
-- Booking is active, with the same Window and Sauna: `check_whole_pair(booking_id)`, called at COMMIT by two deferred
-- constraint triggers, raises `whole_pairing` (unmapped, so a 500). Writes follow AD-23's order: the Booking first. Slice rows without a Booking are deleted (dev and
-- slice databases only).
--
-- `whole_bookable(wid, sid, ignore_booking)` is the only statement of the store-enforced part of FR-29 (AD-24). The
-- trigger `t_00_check_whole` calls it on INSERT and on a change of Window or Sauna, and raises `whole_bookable`; the
-- four names of 0003 are gone. `window_booked_seats()` counts active Seat bookings only.
--
-- `settings.cutoff_whole` (72 hours, AD-4) and `saunas.whole_price_ore` (nullable, filled by the seed only where it is
-- NULL, AD-18; NULL means the Sauna is not offered whole) are added.

-- The capacity triggers are recreated below with `kind` and `sauna_id` in their column lists; dropped first, so the
-- changes of the existing rows recompute nothing (as in 0006).
DROP TRIGGER a_lock_bookings ON bookings;
DROP TRIGGER t_bookings ON bookings;

-- A Seat booking holds 1 to 10 Seats from here on. A legacy row above 10 (slice databases only) cannot be split
-- here, so the migration stops with a message that says how many rows hold more than 10 Seats.
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM bookings WHERE seats > 10;
  IF n > 0 THEN
    RAISE EXCEPTION '0013: % Booking row(s) hold more than 10 Seats; a Seat booking holds 1 to 10 Seats. Split or remove them, then start again.', n;
  END IF;
END $$;

ALTER TABLE bookings
  ADD COLUMN kind text NOT NULL DEFAULT 'seats',
  ADD COLUMN sauna_id int CONSTRAINT bookings_sauna_id_fkey REFERENCES saunas(id),
  ALTER COLUMN seats DROP NOT NULL,
  ALTER COLUMN price_per_seat_ore DROP NOT NULL,
  ADD CONSTRAINT bookings_kind_shape CHECK (
    (kind = 'seats' AND seats BETWEEN 1 AND 10 AND sauna_id IS NULL AND price_per_seat_ore IS NOT NULL)
    OR (kind = 'whole' AND sauna_id IS NOT NULL AND seats IS NULL AND price_per_seat_ore IS NULL));
CREATE INDEX bookings_sauna_id_idx ON bookings (sauna_id);

-- 0012's ban on a Guest refund holds for Seat bookings only: a Whole-sauna booking may be refunded (FR-33, AD-31).
ALTER TABLE bookings
  DROP CONSTRAINT seat_guest_refund_forbidden,
  ADD CONSTRAINT seat_guest_refund_forbidden
    CHECK (kind <> 'seats' OR NOT (cancel_cause = 'guest' AND cancel_remedy = 'refund'));

CREATE TRIGGER a_lock_bookings BEFORE INSERT OR DELETE OR UPDATE OF window_id, seats, status, kind, sauna_id
  ON bookings FOR EACH ROW EXECUTE FUNCTION trg_lock_win();
CREATE TRIGGER t_bookings AFTER INSERT OR DELETE OR UPDATE OF window_id, seats, status, kind, sauna_id
  ON bookings FOR EACH ROW EXECUTE FUNCTION trg_bookings();

-- A Booking keeps its kind for life (AD-23).
CREATE FUNCTION trg_booking_kind_fixed() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Booking % cannot change its kind', OLD.id
    USING ERRCODE = '23514', CONSTRAINT = 'booking_kind_fixed';
END $$;
CREATE TRIGGER b_kind_fixed BEFORE UPDATE OF kind ON bookings
  FOR EACH ROW WHEN (OLD.kind IS DISTINCT FROM NEW.kind) EXECUTE FUNCTION trg_booking_kind_fixed();

-- A cancelled Booking keeps its Sauna as well as its Window and Seats (0012, AD-7): `sauna_id` joins the frozen columns.
CREATE OR REPLACE FUNCTION trg_booking_cancelled_frozen() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.status <> 'cancelled' OR NEW.window_id IS DISTINCT FROM OLD.window_id OR NEW.seats IS DISTINCT FROM OLD.seats
     OR NEW.sauna_id IS DISTINCT FROM OLD.sauna_id
  THEN
    RAISE EXCEPTION 'Booking % is cancelled', OLD.id
      USING ERRCODE = '23514', CONSTRAINT = 'booking_cancelled_frozen';
  END IF;
  RETURN NEW;
END $$;

-- Only active Seat bookings take Seats (AD-7, AD-23). Nothing else sums `bookings.seats`.
CREATE OR REPLACE FUNCTION window_booked_seats(wid int) RETURNS int LANGUAGE sql STABLE AS $$
  SELECT COALESCE(SUM(seats), 0)::int FROM bookings WHERE window_id = wid AND status = 'active' AND kind = 'seats'
$$;

-- The Whole-sauna Cutoff (AD-4), copied into each Whole-sauna booking when it is created (Story 5.2).
ALTER TABLE settings
  ADD COLUMN cutoff_whole interval NOT NULL DEFAULT interval '72 hours'
    CONSTRAINT cutoff_whole_at_least_2_hours CHECK (cutoff_whole >= interval '2 hours');

-- One price per Sauna (AD-23). Not in `t_saunas`' column list, so filling it recomputes nothing.
ALTER TABLE saunas
  ADD COLUMN whole_price_ore int CONSTRAINT saunas_whole_price_positive CHECK (whole_price_ore > 0);

-- A Sauna with no price is never offered whole (FR-29), so it cannot be marked Whole-booking-only either: the mark
-- would close it to Seats while nobody can book it whole. `mark_not_bookable` covers both (0003's check, extended).
CREATE OR REPLACE FUNCTION trg_check_mark() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NOT COALESCE((SELECT bookable_whole AND whole_price_ore IS NOT NULL FROM saunas WHERE id = NEW.sauna_id), false) THEN
    RAISE EXCEPTION 'Sauna % cannot be marked: not bookable whole', NEW.sauna_id
      USING ERRCODE = '23514', CONSTRAINT = 'mark_not_bookable';
  END IF;
  IF  NOT EXISTS (SELECT 1 FROM whole_bookings WHERE window_id = NEW.window_id AND sauna_id = NEW.sauna_id)
     AND NOT EXISTS (SELECT 1 FROM blocks b, windows w WHERE w.id = NEW.window_id AND b.sauna_id = NEW.sauna_id AND b.during && w.during) THEN
    IF window_booked_seats(NEW.window_id) + window_held_seats(NEW.window_id) > room_ahead(NEW.window_id, NEW.sauna_id) THEN
      RAISE EXCEPTION 'Seats are placed in Sauna % in this Window', NEW.sauna_id
        USING ERRCODE = '23514', CONSTRAINT = 'mark_seats_placed';
    END IF;
  END IF;
  RETURN NULL;
END $$;

-- The capacity row names its Booking. The slice's rows have none, so they are deleted (the triggers recompute).
ALTER TABLE whole_bookings ADD COLUMN booking_id bigint;
DELETE FROM whole_bookings WHERE booking_id IS NULL;
ALTER TABLE whole_bookings
  ALTER COLUMN booking_id SET NOT NULL,
  ADD CONSTRAINT whole_bookings_booking_id_key UNIQUE (booking_id),
  ADD CONSTRAINT whole_bookings_booking_id_fkey FOREIGN KEY (booking_id) REFERENCES bookings(id);

-- FR-29 (AD-24), judged as if the capacity row of `ignore_booking` did not exist: the Sauna is bookable whole and has
-- a price, is not Blocked, is not booked whole, the Seats booked plus held fit within its Room ahead unless it is
-- marked and unreleased, and the Window has not started, or has no Seat booking, or the mark applies. It never asks
-- `sauna_open_for_seats` about the Sauna it judges. An unknown Window or Sauna is not bookable.
CREATE FUNCTION whole_bookable(wid int, sid int, ignore_booking bigint DEFAULT NULL) RETURNS boolean
LANGUAGE sql VOLATILE AS $$
  SELECT EXISTS (SELECT 1 FROM windows WHERE id = wid)
     AND COALESCE((SELECT s.bookable_whole AND s.whole_price_ore IS NOT NULL FROM saunas s WHERE s.id = sid), false)
     AND NOT EXISTS (SELECT 1 FROM blocks b, windows w WHERE w.id = wid AND b.sauna_id = sid AND b.during && w.during)
     AND NOT EXISTS (SELECT 1 FROM whole_bookings wb WHERE wb.window_id = wid AND wb.sauna_id = sid
                     AND wb.booking_id IS DISTINCT FROM ignore_booking)
     AND (mark_closed(wid, sid) OR window_booked_seats(wid) + window_held_seats(wid) <= room_ahead(wid, sid))
     AND (NOT window_started(wid) OR window_booked_seats(wid) = 0 OR mark_closed(wid, sid))
$$;

CREATE OR REPLACE FUNCTION trg_check_whole() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NOT whole_bookable(NEW.window_id, NEW.sauna_id, NEW.booking_id) THEN
    RAISE EXCEPTION 'Sauna % cannot be booked whole in Window %', NEW.sauna_id, NEW.window_id
      USING ERRCODE = '23514', CONSTRAINT = 'whole_bookable';
  END IF;
  RETURN NULL;
END $$;
DROP TRIGGER t_00_check_whole ON whole_bookings;
CREATE TRIGGER t_00_check_whole AFTER INSERT OR UPDATE OF window_id, sauna_id ON whole_bookings
  FOR EACH ROW EXECUTE FUNCTION trg_check_whole();

-- The pairing rule (AD-23): an active Whole-sauna booking has exactly one capacity row, with its Window and Sauna; a
-- capacity row's Booking is an active Whole-sauna booking. Judged at COMMIT, so the Booking and its row may be out of
-- step between statements. The write order is AD-23's: create writes the Booking first (the row's foreign key is not
-- deferrable), then the row; cancel sets the status, then deletes the row; move updates the Booking, then the row.
CREATE FUNCTION check_whole_pair(bid bigint) RETURNS void LANGUAGE plpgsql AS $$
DECLARE b record; ok boolean;
BEGIN
  IF bid IS NULL THEN RETURN; END IF;
  SELECT kind, status, window_id, sauna_id INTO b FROM bookings WHERE id = bid;
  IF NOT FOUND THEN
    ok := NOT EXISTS (SELECT 1 FROM whole_bookings wb WHERE wb.booking_id = bid);
  ELSIF b.kind = 'whole' AND b.status = 'active' THEN
    ok := (SELECT count(*) = 1 AND bool_and(wb.window_id = b.window_id AND wb.sauna_id = b.sauna_id)
           FROM whole_bookings wb WHERE wb.booking_id = bid);
  ELSE
    ok := NOT EXISTS (SELECT 1 FROM whole_bookings wb WHERE wb.booking_id = bid);
  END IF;
  IF NOT ok THEN
    RAISE EXCEPTION 'Booking % and its Whole-sauna capacity row are out of step', bid
      USING ERRCODE = '23514', CONSTRAINT = 'whole_pairing';
  END IF;
END $$;

CREATE FUNCTION trg_pair_bookings() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  PERFORM check_whole_pair(NEW.id);
  RETURN NULL;
END $$;

CREATE FUNCTION trg_pair_whole() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP IN ('UPDATE', 'DELETE') THEN PERFORM check_whole_pair(OLD.booking_id); END IF;
  IF TG_OP IN ('INSERT', 'UPDATE') THEN PERFORM check_whole_pair(NEW.booking_id); END IF;
  RETURN NULL;
END $$;

CREATE CONSTRAINT TRIGGER t_pair_bookings AFTER INSERT OR UPDATE OF kind, status, window_id, sauna_id ON bookings
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION trg_pair_bookings();
CREATE CONSTRAINT TRIGGER t_pair_whole AFTER INSERT OR UPDATE OR DELETE ON whole_bookings
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION trg_pair_whole();
