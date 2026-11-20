-- Every refusal a store trigger raises names itself (AD-1), so db maps it by constraint name, at COMMIT too.
-- The logic of each function is identical to 0001_core.sql; only the CONSTRAINT names are added.

CREATE OR REPLACE FUNCTION trg_check_whole() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE bk int; hd int;
BEGIN
  IF NOT (SELECT bookable_whole FROM saunas WHERE id = NEW.sauna_id) THEN
    RAISE EXCEPTION 'Sauna % cannot be booked whole', NEW.sauna_id
      USING ERRCODE = '23514', CONSTRAINT = 'whole_not_bookable';
  END IF;
  IF EXISTS (SELECT 1 FROM blocks b, windows w WHERE w.id = NEW.window_id AND b.sauna_id = NEW.sauna_id AND b.during && w.during) THEN
    RAISE EXCEPTION 'Sauna % is Blocked', NEW.sauna_id
      USING ERRCODE = '23514', CONSTRAINT = 'whole_blocked';
  END IF;
  IF  NOT mark_closed(NEW.window_id, NEW.sauna_id) THEN
    bk := window_booked_seats(NEW.window_id);
    hd := window_held_seats(NEW.window_id);
    IF bk + hd > room_ahead(NEW.window_id, NEW.sauna_id) THEN
      RAISE EXCEPTION 'Seats booked or held (%) would be placed in or before Sauna %', bk + hd, NEW.sauna_id
        USING ERRCODE = '23514', CONSTRAINT = 'whole_seats_placed';
    END IF;
    IF bk > 0 AND (SELECT lower(during) <= app_now() FROM windows WHERE id = NEW.window_id) THEN
      RAISE EXCEPTION 'Window has started and has Seat bookings'
        USING ERRCODE = '23514', CONSTRAINT = 'whole_window_started';
    END IF;
  END IF;
  RETURN NULL;
END $$;

CREATE OR REPLACE FUNCTION trg_check_mark() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NOT (SELECT bookable_whole FROM saunas WHERE id = NEW.sauna_id) THEN
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

CREATE OR REPLACE FUNCTION trg_check_release() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM marks WHERE window_id = NEW.window_id AND sauna_id = NEW.sauna_id)
     OR NOT (SELECT release_on FROM settings) OR app_now() < release_due(NEW.window_id) THEN
    RAISE EXCEPTION 'release of Sauna % in Window % is not due', NEW.sauna_id, NEW.window_id
      USING ERRCODE = '23514', CONSTRAINT = 'release_not_due';
  END IF;
  RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION verify_window() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  PERFORM 1 FROM windows w WHERE w.id = NEW.id
    AND (w.seat_capacity > window_open_capacity(w.id) OR w.booked <> window_booked_seats(w.id)
         OR w.held < window_held_seats(w.id));  -- stale-high held (an expiry since the last write) is safe
  IF FOUND THEN
    RAISE EXCEPTION 'window % is out of step with its bookings, Blocks or Whole-sauna bookings', NEW.id
      USING ERRCODE = '23514', CONSTRAINT = 'window_out_of_step';
  END IF;
  RETURN NULL;
END $$;
