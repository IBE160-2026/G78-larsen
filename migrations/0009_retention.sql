-- Story 2.2 (FR-21, AD-4, AD-30): the one retention predicate.
--
-- A Booking is due for retention once app_now() is more than 12 months after the end of its Window. Reads mask the
-- name and email of a due Booking (`db.booking_list`) and the startup catch-up anonymises it and clears its Outbox
-- emails (`services.catchup`); nothing else decides retention. Epic 4 extends this function with the Voucher clause.
-- VOLATILE, because app_now() is. An unknown Booking id is not due.
CREATE FUNCTION retention_due(bid bigint) RETURNS boolean LANGUAGE sql VOLATILE AS $$
  SELECT COALESCE((SELECT app_now() > upper(w.during) + interval '12 months'
                   FROM bookings b JOIN windows w ON w.id = b.window_id
                   WHERE b.id = bid), false)
$$;
