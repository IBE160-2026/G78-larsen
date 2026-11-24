-- Story 4.3 (FR-27, FR-21, AD-13, AD-29, AD-30, AD-31): Vouchers, the cancellation of a Booking, and the Voucher
-- Change's history row and ledger row.
--
-- `vouchers` holds one row per Voucher. Only `services.voucher` writes it (AD-30). The code is never stored: only its
-- unkeyed SHA-256 hash (32 bytes). `expires_at` is 00:00 Venue time on the day after the last valid date.
--
-- A Booking is cancelled with when (`cancelled_at`), why (`cancel_cause`) and the remedy (`cancel_remedy`, NULL while
-- the Guest has not yet chosen, FR-42). A Seat booking is cancelled only by giving up all its Seats for a Voucher
-- (`guest`, `voucher`); a Seat booking is never refunded in money at the Guest's request (`seat_guest_refund_forbidden`;
-- every `bookings` row is a Seat booking until Epic 5 adds `kind`). A cancelled row is frozen: the trigger
-- `b_cancelled_frozen` refuses `cancelled` -> `active` and any change of its Window or Seats (a named constraint, a 500
-- under AD-1). The new columns are not in the AD-7 trigger column lists: only `status` changes capacity, and it is
-- already listed.
--
-- A `voucher` Change sets `seats` and `voucher_id` and no Window, Sauna or new Booking; a `move` never sets
-- `voucher_id`. A `payments` row carries `voucher_id` exactly when its method is `voucher` (AD-13).
--
-- `retention_due` gains the Voucher clause (AD-30): a Booking is due only once app_now() is past both 12 months after
-- its Window's end and the latest `expires_at` of the Vouchers issued from it.

CREATE TABLE vouchers (
  id bigserial PRIMARY KEY,
  code_hash bytea NOT NULL CONSTRAINT vouchers_code_hash_key UNIQUE
    CONSTRAINT vouchers_code_hash_length CHECK (length(code_hash) = 32),
  value_ore int NOT NULL,
  balance_ore int NOT NULL,
  issued_at timestamptz NOT NULL DEFAULT app_now(),
  expires_at timestamptz NOT NULL,
  booking_id bigint CONSTRAINT vouchers_booking_id_fkey REFERENCES bookings(id),
  CONSTRAINT vouchers_balance_within_value CHECK (value_ore > 0 AND 0 <= balance_ore AND balance_ore <= value_ore),
  CONSTRAINT vouchers_expires_after_issue CHECK (expires_at > issued_at));
CREATE INDEX vouchers_booking_id_idx ON vouchers (booking_id);

-- Legacy cancelled rows (dev databases only; no path cancelled a Booking before this migration): cancelled by hand at
-- their entry time, recorded with cause `block` (the Venue-side cause of AD-29) and no remedy.
ALTER TABLE bookings
  ADD COLUMN cancelled_at timestamptz,
  ADD COLUMN cancel_cause text CONSTRAINT bookings_cancel_cause_known CHECK (cancel_cause IN ('guest', 'block', 'overbooking')),
  ADD COLUMN cancel_remedy text CONSTRAINT bookings_cancel_remedy_known CHECK (cancel_remedy IN ('refund', 'voucher'));
UPDATE bookings SET cancelled_at = entry_time, cancel_cause = 'block' WHERE status = 'cancelled';
ALTER TABLE bookings
  ADD CONSTRAINT bookings_active_not_cancelled
    CHECK (status <> 'active' OR (cancelled_at IS NULL AND cancel_cause IS NULL AND cancel_remedy IS NULL)),
  ADD CONSTRAINT bookings_cancelled_has_time_and_cause
    CHECK (status <> 'cancelled' OR (cancelled_at IS NOT NULL AND cancel_cause IS NOT NULL)),
  ADD CONSTRAINT bookings_guest_cancel_has_remedy CHECK (cancel_cause <> 'guest' OR cancel_remedy IS NOT NULL),
  ADD CONSTRAINT seat_guest_refund_forbidden CHECK (NOT (cancel_cause = 'guest' AND cancel_remedy = 'refund'));

CREATE FUNCTION trg_booking_cancelled_frozen() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.status <> 'cancelled' OR NEW.window_id IS DISTINCT FROM OLD.window_id OR NEW.seats IS DISTINCT FROM OLD.seats
  THEN
    RAISE EXCEPTION 'Booking % is cancelled', OLD.id
      USING ERRCODE = '23514', CONSTRAINT = 'booking_cancelled_frozen';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER b_cancelled_frozen BEFORE UPDATE ON bookings
  FOR EACH ROW WHEN (OLD.status = 'cancelled') EXECUTE FUNCTION trg_booking_cancelled_frozen();

ALTER TABLE booking_changes
  ADD COLUMN voucher_id bigint CONSTRAINT booking_changes_voucher_id_fkey REFERENCES vouchers(id),
  DROP CONSTRAINT booking_changes_action_known,
  ADD CONSTRAINT booking_changes_action_known CHECK (action IN ('move', 'voucher')),
  DROP CONSTRAINT booking_changes_move_shape,
  ADD CONSTRAINT booking_changes_move_shape CHECK (
    action <> 'move' OR (from_window_id IS NOT NULL AND to_window_id IS NOT NULL AND from_window_id <> to_window_id
                         AND seats IS NOT NULL AND from_sauna_id IS NULL AND to_sauna_id IS NULL
                         AND voucher_id IS NULL)),
  ADD CONSTRAINT booking_changes_voucher_shape CHECK (
    action <> 'voucher' OR (seats IS NOT NULL AND voucher_id IS NOT NULL AND from_window_id IS NULL
                            AND to_window_id IS NULL AND from_sauna_id IS NULL AND to_sauna_id IS NULL
                            AND new_booking_id IS NULL));
CREATE INDEX booking_changes_voucher_id_idx ON booking_changes (voucher_id);

ALTER TABLE payments
  ADD COLUMN voucher_id bigint CONSTRAINT payments_voucher_id_fkey REFERENCES vouchers(id),
  ADD CONSTRAINT payments_voucher_id_matches_method CHECK ((method = 'voucher') = (voucher_id IS NOT NULL));
CREATE INDEX payments_voucher_id_idx ON payments (voucher_id);

-- The one retention predicate (FR-21, AD-30). VOLATILE, because app_now() is. An unknown Booking id is not due.
CREATE OR REPLACE FUNCTION retention_due(bid bigint) RETURNS boolean LANGUAGE sql VOLATILE AS $$
  SELECT COALESCE((SELECT app_now() > upper(w.during) + interval '12 months'
                          AND app_now() > COALESCE((SELECT max(v.expires_at) FROM vouchers v WHERE v.booking_id = b.id),
                                                   '-infinity'::timestamptz)
                   FROM bookings b JOIN windows w ON w.id = b.window_id
                   WHERE b.id = bid), false)
$$;
