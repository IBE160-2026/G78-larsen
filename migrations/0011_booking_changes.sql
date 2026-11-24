-- Story 4.2 (FR-26, AD-9, AD-12, AD-29): the Change history, and the Outbox emails and one-time keys of a Change.
--
-- `booking_changes` holds one row per Change of a Booking. Only `services.history.record` writes it; no trigger does
-- (AD-7, AD-29). `action` is 'move' now; Story 4.3 adds 'voucher' and its shape CHECK, Epic 5 the Whole-sauna moves.
-- A `move` sets both Window ids and `seats`, never a Sauna id; `new_booking_id` is set only when the move split the
-- Booking (the moved Seats became a new Booking).
--
-- An email a Change sends carries its `change_id` (AD-12), so a repeat of the Change reads the same emails back. A
-- one-time key of a Change points at the Change, not at a Booking: exactly one of `booking_id` and `change_id` is set
-- (AD-9). No column here is in the capacity triggers' column list (AD-7), so nothing is recomputed.

CREATE TABLE booking_changes (
  id bigserial PRIMARY KEY,
  booking_id bigint NOT NULL CONSTRAINT booking_changes_booking_id_fkey REFERENCES bookings(id),
  action text NOT NULL CONSTRAINT booking_changes_action_known CHECK (action IN ('move')),
  at timestamptz NOT NULL DEFAULT app_now(),
  seats int CONSTRAINT booking_changes_seats_positive CHECK (seats > 0),
  from_window_id int CONSTRAINT booking_changes_from_window_id_fkey REFERENCES windows(id),
  to_window_id int CONSTRAINT booking_changes_to_window_id_fkey REFERENCES windows(id),
  from_sauna_id int CONSTRAINT booking_changes_from_sauna_id_fkey REFERENCES saunas(id),
  to_sauna_id int CONSTRAINT booking_changes_to_sauna_id_fkey REFERENCES saunas(id),
  new_booking_id bigint CONSTRAINT booking_changes_new_booking_id_fkey REFERENCES bookings(id),
  CONSTRAINT booking_changes_move_shape CHECK (
    action <> 'move' OR (from_window_id IS NOT NULL AND to_window_id IS NOT NULL AND from_window_id <> to_window_id
                         AND seats IS NOT NULL AND from_sauna_id IS NULL AND to_sauna_id IS NULL)),
  CONSTRAINT booking_changes_new_booking_not_itself CHECK (new_booking_id IS NULL OR new_booking_id <> booking_id));
CREATE INDEX booking_changes_booking_id_idx ON booking_changes (booking_id);
CREATE INDEX booking_changes_new_booking_id_idx ON booking_changes (new_booking_id);

ALTER TABLE outbox_emails
  ADD COLUMN change_id bigint CONSTRAINT outbox_emails_change_id_fkey REFERENCES booking_changes(id);
CREATE INDEX outbox_emails_change_id_idx ON outbox_emails (change_id);

ALTER TABLE idempotency_keys
  ADD COLUMN change_id bigint CONSTRAINT idempotency_keys_change_id_fkey REFERENCES booking_changes(id),
  ALTER COLUMN booking_id DROP NOT NULL,
  ADD CONSTRAINT idempotency_keys_one_target CHECK (num_nonnulls(booking_id, change_id) = 1);
CREATE INDEX idempotency_keys_change_id_idx ON idempotency_keys (change_id);
