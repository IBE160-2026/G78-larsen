-- Story 5.3 (FR-33, AD-15, AD-23, AD-24, AD-29): a Guest moves a Private sauna through its Manage link. The §4.9 move
-- migration; its number was taken when the story started (re-check at merge, AD-15).
--
-- A `move` Change of a Whole-sauna booking (`POST /api/manage/{reference}/whole/move`) records both Windows and both
-- Saunas, and no Seats, Voucher or new Booking; its Window or its Sauna (or both) differ. The Seat move keeps the shape
-- of 0012 unchanged, so `booking_changes_move_shape` now allows either shape.
--
-- `whole_bookable(wid, sid, ignore_booking)` judged the Room ahead with `room_ahead`, which counts the capacity row of
-- `ignore_booking` as closing its Sauna to Seats. A move within one Window to a Sauna later in the Fill order was then
-- judged as if the Booking's own Sauna were still taken. The Room-ahead clause now treats the Sauna of the
-- `ignore_booking` row as open (unless it is Blocked or marked); without `ignore_booking` it equals `room_ahead`.
-- Nothing else changes.

ALTER TABLE booking_changes
  DROP CONSTRAINT booking_changes_move_shape,
  ADD CONSTRAINT booking_changes_move_shape CHECK (
    action <> 'move'
    OR (from_window_id IS NOT NULL AND to_window_id IS NOT NULL AND from_window_id <> to_window_id
        AND seats IS NOT NULL AND from_sauna_id IS NULL AND to_sauna_id IS NULL AND voucher_id IS NULL)
    OR (from_window_id IS NOT NULL AND to_window_id IS NOT NULL AND from_sauna_id IS NOT NULL
        AND to_sauna_id IS NOT NULL AND (from_window_id <> to_window_id OR from_sauna_id <> to_sauna_id)
        AND seats IS NULL AND voucher_id IS NULL AND new_booking_id IS NULL));

CREATE OR REPLACE FUNCTION whole_bookable(wid int, sid int, ignore_booking bigint DEFAULT NULL) RETURNS boolean
LANGUAGE sql VOLATILE AS $$
  SELECT EXISTS (SELECT 1 FROM windows WHERE id = wid)
     AND COALESCE((SELECT s.bookable_whole AND s.whole_price_ore IS NOT NULL FROM saunas s WHERE s.id = sid), false)
     AND NOT EXISTS (SELECT 1 FROM blocks b, windows w WHERE w.id = wid AND b.sauna_id = sid AND b.during && w.during)
     AND NOT EXISTS (SELECT 1 FROM whole_bookings wb WHERE wb.window_id = wid AND wb.sauna_id = sid
                     AND wb.booking_id IS DISTINCT FROM ignore_booking)
     AND (mark_closed(wid, sid)
          OR window_booked_seats(wid) + window_held_seats(wid) <= (
            SELECT COALESCE(SUM(s2.capacity), 0)::int FROM saunas s1 JOIN saunas s2 ON s2.fill_order < s1.fill_order
            WHERE s1.id = sid
              AND NOT EXISTS (SELECT 1 FROM whole_bookings wb WHERE wb.window_id = wid AND wb.sauna_id = s2.id
                              AND wb.booking_id IS DISTINCT FROM ignore_booking)
              AND NOT EXISTS (SELECT 1 FROM blocks b, windows w WHERE w.id = wid AND b.sauna_id = s2.id
                              AND b.during && w.during)
              AND NOT mark_closed(wid, s2.id)))
     AND (NOT window_started(wid) OR window_booked_seats(wid) = 0 OR mark_closed(wid, sid))
$$;
