-- Story 5.3 (FR-33, AD-15, AD-29, AD-31): a Guest cancels a Private sauna through its Manage link. The §4.9 cancel
-- migration; its number was taken when the story started (re-check at merge, AD-15).
--
-- A `cancel` Change is the history row of a Whole-sauna cancellation (`POST /api/manage/{reference}/whole/cancel`).
-- It sets no Seats, no Window, no Sauna and no new Booking; `voucher_id` is set exactly when the Booking's remedy is a
-- Voucher. That last rule needs the Booking's `cancel_remedy`, so `services.change.whole_cancel` keeps it (and
-- `test_fr33_whole_change.py` tests it); the store fixes only the shape. Nothing else changes.

ALTER TABLE booking_changes
  DROP CONSTRAINT booking_changes_action_known,
  ADD CONSTRAINT booking_changes_action_known CHECK (action IN ('move', 'voucher', 'cancel')),
  ADD CONSTRAINT booking_changes_cancel_shape CHECK (
    action <> 'cancel' OR (seats IS NULL AND from_window_id IS NULL AND to_window_id IS NULL AND from_sauna_id IS NULL
                           AND to_sauna_id IS NULL AND new_booking_id IS NULL));
