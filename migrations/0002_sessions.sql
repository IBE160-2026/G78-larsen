-- Server-side sessions (AD-8). The cookie holds a 256-bit random token; the store keeps only its SHA-256 hash.
-- One table for anonymous and signed-in browsers, with a role per row. Expiry is judged on app_now().
CREATE TABLE sessions (
  id bigserial PRIMARY KEY,
  token_hash bytea NOT NULL UNIQUE CHECK (length(token_hash) = 32),
  role text NOT NULL CHECK (role IN ('guest', 'admin')),
  created_at timestamptz NOT NULL DEFAULT app_now(),
  expires_at timestamptz NOT NULL);

-- The slice's client-chosen holds.session_id is replaced by a reference to sessions.id.
-- Existing Holds are 10-minute rows in dev databases only, so they are deleted (the triggers recompute).
DELETE FROM holds;
ALTER TABLE holds
  ALTER COLUMN session_id DROP NOT NULL,
  ALTER COLUMN session_id TYPE bigint USING NULL::bigint,
  ADD CONSTRAINT holds_session_id_fkey FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL;
