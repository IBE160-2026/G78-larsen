-- Story 1.6 (AD-9): an idempotency key outlives its session. Before this, a purged session took its keys with it
-- (ON DELETE CASCADE), so a retry of a paid request from a new session after a purge could charge a second time.
-- Now the key row stays with `session_id` NULL: the same key from any session is `409 invalid_key` and never a
-- second charge. The constraint keeps its name, so `db/refusals.py` still maps it to `no_session`.
ALTER TABLE idempotency_keys ALTER COLUMN session_id DROP NOT NULL;
ALTER TABLE idempotency_keys
  DROP CONSTRAINT idempotency_keys_session_id_fkey,
  ADD CONSTRAINT idempotency_keys_session_id_fkey
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL;
