-- Story 2.1 (AD-11, AD-15): only what sign-in needs.
-- Accounts hold an Argon2id hash in PHC format, never a readable password (PW-1). The email is stored lower-cased,
-- so one address is one account whatever case it is typed in.
CREATE TABLE accounts (
  id bigserial PRIMARY KEY,
  email text NOT NULL UNIQUE CHECK (lower(email) = email),
  password_hash text NOT NULL,
  role text NOT NULL CHECK (role IN ('admin')));

-- A signed-in session names its account; an anonymous one (a Guest's booking session) has none (RB-1).
-- Deleting an account ends its sessions.
ALTER TABLE sessions ADD COLUMN account_id bigint NULL REFERENCES accounts(id) ON DELETE CASCADE;

-- The sign-in throttle (PW-6): one row per lower-cased email, known or not, so it has no foreign key to accounts.
CREATE TABLE sign_in_throttle (
  email_lower text PRIMARY KEY,
  failures int NOT NULL DEFAULT 0,
  locked_until timestamptz);
