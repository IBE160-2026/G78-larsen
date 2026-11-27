-- Story 5.4 (FR-31, AD-6, AD-10, AD-25): the Administrator sees where Seats are counted. The one computation of
-- Placement; its number was taken when the story started (re-check at merge, AD-15).
--
-- `placement(wid)` returns one row per Sauna in Fill order, `(sauna_id, state, seats)`. `state` is the first that
-- applies of `whole` (a `whole_bookings` row), `blocked` (a Block overlapping the Window), `marked` (`mark_closed`,
-- so a released mark is `open`) and `open`: a Block can be inserted over a Whole-sauna booking, and staff must still
-- see the Guest's booking. Only the Window's booked Seats are placed (`window_booked_seats`, no Holds), greedily in
-- Fill order over the `open` Saunas: an open Sauna counts LEAST(capacity, GREATEST(0, booked - the capacity of the
-- open Saunas before it)); every other state counts 0. Placement is derived, never stored (AD-6): the function is
-- volatile and read-only, takes no lock, and is read only under `/api/admin/` (AD-25). Nothing else changes.

CREATE FUNCTION placement(wid int) RETURNS TABLE (sauna_id int, state text, seats int)
LANGUAGE sql VOLATILE AS $$
  WITH judged AS (
    SELECT s.id AS sid, s.capacity AS cap, s.fill_order AS fo,
           CASE WHEN EXISTS (SELECT 1 FROM whole_bookings wb WHERE wb.window_id = w.id AND wb.sauna_id = s.id)
                  THEN 'whole'
                WHEN EXISTS (SELECT 1 FROM blocks b WHERE b.sauna_id = s.id AND b.during && w.during) THEN 'blocked'
                WHEN mark_closed(w.id, s.id) THEN 'marked'
                ELSE 'open' END AS st
    FROM windows w CROSS JOIN saunas s
    WHERE w.id = wid),
  ahead AS (
    SELECT sid, cap, fo, st,
           COALESCE(SUM(CASE WHEN st = 'open' THEN cap END)
                      OVER (ORDER BY fo ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING), 0)::int AS before
    FROM judged)
  SELECT sid, st,
         CASE WHEN st = 'open' THEN LEAST(cap, GREATEST(0, window_booked_seats(wid) - before))::int ELSE 0 END
  FROM ahead ORDER BY fo
$$;
