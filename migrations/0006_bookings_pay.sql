-- Pay and confirmation (Story 1.5, FR-5, FR-6, FR-8, AD-7, AD-9, AD-12, AD-13, AD-20). AD-7 names migration "0002";
-- 0002 to 0005 were taken by Stories 1.1 to 1.4, so this is the next free number.
--
-- A Booking gains its Guest-facing reference, the Guest's name and email, its value in øre, the paying session, a
-- status and an entry time. Bookings are never deleted (AD-7): a cancelled Booking keeps its row and stops counting.
-- The tables `payments`, `outbox_emails` and `idempotency_keys` are created as AD-13, AD-12 and AD-9 define them,
-- without the columns of later stories (`voucher_id`, `change_id`).

-- The capacity triggers are recreated below with a column list; dropped first, so the backfill recomputes nothing.
DROP TRIGGER a_lock_bookings ON bookings;
DROP TRIGGER t_bookings ON bookings;

ALTER TABLE bookings
  ADD COLUMN reference text,
  ADD COLUMN name text,
  ADD COLUMN email text,
  ADD COLUMN price_per_seat_ore int,
  ADD COLUMN total_ore int,
  ADD COLUMN session_id bigint,
  ADD COLUMN status text NOT NULL DEFAULT 'active',
  ADD COLUMN entry_time timestamptz NOT NULL DEFAULT app_now();

-- Legacy rows (dev databases only): a reference from the id in hex (a subset of Crockford base32), the old free-text
-- `guest` as the name, an email that cannot reach anyone, and the current price.
UPDATE bookings b
SET reference = lpad(upper(to_hex(b.id)), 8, '0'),
    name = COALESCE(NULLIF(left(btrim(b.guest), 100), ''), 'Guest'),
    email = 'unknown@example.invalid',
    price_per_seat_ore = st.price_per_seat_ore,
    total_ore = b.seats * st.price_per_seat_ore,
    entry_time = b.created_at
FROM settings st;

ALTER TABLE bookings
  ALTER COLUMN reference SET NOT NULL,
  ALTER COLUMN name SET NOT NULL,
  ALTER COLUMN email SET NOT NULL,
  ALTER COLUMN price_per_seat_ore SET NOT NULL,
  ALTER COLUMN total_ore SET NOT NULL,
  ADD CONSTRAINT bookings_reference_key UNIQUE (reference),
  ADD CONSTRAINT bookings_reference_format CHECK (reference ~ '^[0-9A-HJKMNP-TV-Z]{8}$'),
  ADD CONSTRAINT bookings_name_length CHECK (char_length(name) BETWEEN 1 AND 100),
  ADD CONSTRAINT bookings_email_length CHECK (char_length(email) BETWEEN 1 AND 254),
  ADD CONSTRAINT bookings_price_not_negative CHECK (price_per_seat_ore >= 0),
  ADD CONSTRAINT bookings_total_is_seats_times_price CHECK (total_ore = seats * price_per_seat_ore),
  ADD CONSTRAINT bookings_status_known CHECK (status IN ('active', 'cancelled')),
  ADD CONSTRAINT bookings_session_id_fkey FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL,
  DROP COLUMN guest;

CREATE INDEX bookings_session_id_idx ON bookings (session_id);

-- Only active Bookings take Seats (AD-7). seats_left() and recompute_window() read this function.
CREATE OR REPLACE FUNCTION window_booked_seats(wid int) RETURNS int LANGUAGE sql STABLE AS $$
  SELECT COALESCE(SUM(seats), 0)::int FROM bookings WHERE window_id = wid AND status = 'active'
$$;

-- The same triggers, now only for the columns that change capacity (AD-7): a change of name, email or session
-- neither locks nor recomputes a Window.
CREATE TRIGGER a_lock_bookings BEFORE INSERT OR DELETE OR UPDATE OF window_id, seats, status ON bookings
  FOR EACH ROW EXECUTE FUNCTION trg_lock_win();
CREATE TRIGGER t_bookings AFTER INSERT OR DELETE OR UPDATE OF window_id, seats, status ON bookings
  FOR EACH ROW EXECUTE FUNCTION trg_bookings();

-- How a Booking's value was funded and returned (AD-13). Only refunds and the audit read it.
CREATE TABLE payments (
  id bigserial PRIMARY KEY,
  booking_id bigint NOT NULL CONSTRAINT payments_booking_id_fkey REFERENCES bookings(id),
  direction text NOT NULL CONSTRAINT payments_direction_known CHECK (direction IN ('charge', 'refund')),
  method text NOT NULL CONSTRAINT payments_method_known CHECK (method IN ('card', 'voucher')),
  amount_ore int NOT NULL CONSTRAINT payments_amount_positive CHECK (amount_ore > 0),
  created_at timestamptz NOT NULL DEFAULT app_now());
CREATE INDEX payments_booking_id_idx ON payments (booking_id);

-- Every email the platform sends (AD-12): written only by services.outbox.send, inside the action's transaction.
CREATE TABLE outbox_emails (
  id bigserial PRIMARY KEY,
  created_at timestamptz NOT NULL DEFAULT app_now(),
  recipient text NOT NULL,
  subject text NOT NULL,
  body text NOT NULL,
  booking_id bigint CONSTRAINT outbox_emails_booking_id_fkey REFERENCES bookings(id));
CREATE INDEX outbox_emails_booking_id_idx ON outbox_emails (booking_id);

-- One-time keys of confirming requests (AD-9). Only successes are stored; ids and hashes only, never personal data.
CREATE TABLE idempotency_keys (
  id bigserial PRIMARY KEY,
  key uuid NOT NULL CONSTRAINT idempotency_keys_key_key UNIQUE,
  session_id bigint NOT NULL
    CONSTRAINT idempotency_keys_session_id_fkey REFERENCES sessions(id) ON DELETE CASCADE,
  endpoint text NOT NULL,
  request_hash bytea NOT NULL CONSTRAINT idempotency_keys_hash_length CHECK (length(request_hash) = 32),
  booking_id bigint NOT NULL CONSTRAINT idempotency_keys_booking_id_fkey REFERENCES bookings(id),
  created_at timestamptz NOT NULL DEFAULT app_now());
CREATE INDEX idempotency_keys_session_id_idx ON idempotency_keys (session_id);
CREATE INDEX idempotency_keys_booking_id_idx ON idempotency_keys (booking_id);
