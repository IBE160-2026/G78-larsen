---
title: 'Story 2.1: Administrator signs in and out'
type: 'feature'
created: '2026-11-21'
status: 'done'
baseline_commit: 'f692aa6c4c212f805e0c3ac872b7ee63afb74b95'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/.docs/planning-artifacts/epics.md'
  - '{project-root}/.docs/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** There are no accounts, no passwords and no sign-in. `/api/admin/` admits any session whose `role` is `'admin'`, and the tests insert such rows by hand (`tests/client.py:79`). Staff therefore have no way in, and nothing yet proves FR-15, FR-19 or PW-1 to PW-6.

**Approach:** Build Story 2.1 as written in `.docs/planning-artifacts/epics.md` (L771–845). It adds migration `0008`, a seeded Administrator, `services/auth.py` (password rules, Argon2id, a throttled sign-in), sign-in and sign-out endpoints, the `create-admin` command, the Sign-in page, the shared Administrator bar and a guard on Administrator pages. The test fixture's Administrator then comes from a real sign-in.

## Boundaries & Constraints

**Always:**
- One refusal for every failed sign-in: a wrong password, an unknown email and a throttled email all get `401 sign_in_refused`. Argon2 verify runs on every attempt that has a session, against a module-level dummy hash when the email is unknown. The page shows only "Wrong email or password".
- Throttle (AD-11), in one `db.run(work)`: upsert the `sign_in_throttle` row for `lower(email)`, `SELECT … FOR UPDATE` it, verify, then decide.
  - A refused attempt adds 1 to `failures`, whether it was a wrong password or a locked attempt.
  - When an attempt that was not locked leaves `failures` ≥ 5, `locked_until` becomes `app_now() + 15 min`. A locked attempt never extends `locked_until`.
  - A success sets `failures` to 0 and `locked_until` to NULL.
  - A refusal is *returned* from `work` so that its count commits.
- A sign-in without a valid session cookie is `401 no_session` and touches no throttle row. The frontend then calls `POST /api/session` and retries once.
- Sign-in success happens in the same `work`. The session row gets a new token, `role 'admin'`, `account_id` and `expires_at = app_now() + lifetime`, and the row id stays the same. The answer is `{"role": "admin"}`, and the cookie is set as in `POST /api/session`. If the hash needs rehashing, the new hash is stored.
- `require_admin`: no session, or a session with a NULL `account_id`, is `401 not_signed_in`. A session with an account but a role other than `admin` is `403 not_allowed`.
- `POST /api/admin/sign-in` sits on a second router under `/api/admin`, with no dependency. Everything else, including `sign-out` and the new `GET /api/admin/me` (`{"role":"admin"}`, used by the page guard), stays on the guarded router.
- `check_password_rules(password, email)` is the only rule check. It raises `PasswordRuleError(reason)` (not a `Refused`, because no endpoint sets passwords yet), where reason is one of `too_short` (< 15 characters after NFC), `common` (the lower-cased value is in the list) or `equals_email` (case-insensitive). There is no upper limit below 1024 characters. The API schema caps the password at 1024 and the email at 254.
- `create-admin`: `getpass` twice, with no argument and no environment variable. It migrates first, and creates `booking_dev` when the URL is the default. It upserts by email (a new account, or a new hash for an existing one), prints the email and "created" or "password changed", and prints a rule failure as one line with exit code 2.
- No log line contains a password, hash or token. Copy comes from `frontend/lib/copy.js`, styling only from `app/styles.css`, browser calls only through `lib/api.js`, and keyboard steps in e2e tests only through `a11y.press`/`a11y.tab_to`.
- Existing tests keep their assertions, with one exception: `tests/test_fr20_access.py` "a guest session gets 403" becomes 401 `not_signed_in`. A Guest's booking session has no account, so it counts as anonymous (RB-1). 403 stays for an account session without the `admin` role, which is unreachable in Core.

**Never:** Edit migrations `0001`–`0007`. Store or log a readable password. Add sign-up, password reset, per-IP throttling or a permanent lock. Build the Booking list content (Story 2.2) or the Outbox page (Story 2.3). Create a session on any page load other than Sign-in and Book seats.

**Decisions (Lisa, 2026-11-21):**
- Test password: `badstue-admin-test-2026` for `admin@saunaloyly.example`, in `seeds/admin.json` and the README.
- Common-password list: SecLists `Passwords/Common-Credentials/100k-most-used-passwords-NCSC.txt` (MIT), filtered to entries of 15 or more characters, lower-cased and de-duplicated, with its source, commit, licence and the filter recorded in `ASSETS.md`.
- Scope: the story stays whole (about 2800 tokens).

**Decisions (planning, confirmed by Lisa at approval 2026-11-21):**
- Addresses: `/admin/sign-in` (Sign-in) and `/admin/bookings` (Booking list: for now the bar plus an `h1` "Booking list"). `/admin` redirects to `/admin/bookings`. The bar's Outbox link points at `/admin/outbox`, which is a 404 until Story 2.3.
- Seed: `seeds/admin.json` `{"email", "password"}` is read by `seed.load()`, which checks it with `check_password_rules`; a failure is a one-line `SeedError`. `seed.apply()` inserts the account only when the email is absent, so a restart never rehashes.
- An expired Administrator is sent to Sign-in like an anonymous one, with no extra copy (EXPERIENCE.md L378). A Sign-in page whose `POST /api/session` answers `role: "admin"` goes to the Booking list.
- A network error, `5xx` or `503` on sign-in shows a Notice: "Sign-in could not be completed, please try again."

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected | Error Handling |
|---|---|---|---|
| Correct | seeded email (any case) and password | 200 `{"role":"admin"}`, new cookie, old token gets 401, `failures` 0 | — |
| Wrong / unknown | wrong password, or unknown email | 401 `sign_in_refused`, `failures` +1 | Error summary "Wrong email or password", no Field error |
| Throttled | 5 failures, then the correct password within 15 min | 401 `sign_in_refused` | same message |
| Lock over | `clock.off` moved 15 min + 1 s | correct password gives 200, `failures` 0 | — |
| Parallel | 10 parallel wrong attempts for one email | `failures` = 10 exactly | — |
| No session | no cookie | 401 `no_session`, no throttle row | page re-opens the session and retries once |
| Cross-origin | sign-in or sign-out with a foreign `Origin` | 403 `cross_origin`, nothing written | — |
| Sign out | `POST /api/admin/sign-out` | row deleted, cookie cleared, old token gets 401 on `/api/admin/me` | page goes to Sign-in; Back also leads to Sign-in |
| Guarded page | anonymous at `/admin/bookings` | nothing rendered, replaced by `/admin/sign-in` | — |
| Rules | 14 characters / a listed password / equal to the email / 64 characters with spaces and `ø` | refused / refused / refused / accepted | seed: `SeedError`; CLI: exit 2, nothing written |

</frozen-after-approval>

## Code Map

- `migrations/0007_keys_outlive_sessions.sql` -- the latest migration. The new `0008_accounts_sign_in.sql` adds `accounts(id bigserial, email text UNIQUE NOT NULL CHECK lower(email)=email, password_hash text NOT NULL, role text NOT NULL CHECK IN ('admin'))`, `sessions.account_id bigint NULL REFERENCES accounts ON DELETE CASCADE`, and `sign_in_throttle(email_lower text PK, failures int NOT NULL DEFAULT 0, locked_until timestamptz)`. `tests/test_dr4_migrations.py` pins the migration files.
- `src/booking_platform/db/sessions.py` -- `lifetime()` is the one lifetime source. `resolve_and_touch` must also return `account_id`. Add `rotate(c, sid, token_hash, account_id)` and `delete(c, sid)` here. A new `db/accounts.py` holds the account and throttle SQL.
- `src/booking_platform/services/sessions.py` -- `Session` gains `account_id`, and `open_session` is the pattern for creating a token and its hash.
- `src/booking_platform/api/deps.py` -- `require_admin` (L37) and `COOKIE`. The `RequestGuard` in `app.py` already enforces CSRF on every POST.
- `src/booking_platform/api/admin.py` -- the guarded router. Add `sign-out` and `me` to it, and a sibling `sign_in_router` with the `/api/admin` prefix that `app.py` includes.
- `src/booking_platform/api/public.py:42` -- the `set_cookie` arguments to reuse. `api/schemas.py` gets a `SignInIn` with extra fields forbidden. `api/errors.py` and `frontend/lib/api.js` `STATUS` get `sign_in_refused: 401`.
- `src/booking_platform/services/seed.py` -- `load()`/`apply()` and the `SeedError` one-line style. `src/booking_platform/__init__.py` -- argparse; add the `create-admin` subcommand. `db/migrate.py` provides `ensure_database` and `migrate`.
- `pyproject.toml` -- add `argon2-cffi>=25.1.0` (spine version table). `Dockerfile` already copies `src/` and `seeds/`.
- `tests/client.py:79` `admin_client` -- replace it with a real sign-in: an api_client session, then `POST /api/admin/sign-in` with `seeds/admin.json`. `tests/conftest.py:208` `world` must truncate `sign_in_throttle` (accounts survive, since the seed creates them at backend start). Users of the fixture: `test_fr18_csrf.py`, `test_fr21_sessions.py:88`, `test_fr20_access.py`, `test_fr10_*`, `test_fr14_retry.py`, `test_application_rules.py`, `test_fr2_input.py`.
- `frontend/app/layout.js` -- the title template and `FocusMover`. `components/Details.js:85` is the text-field pattern (label and autocomplete). Also reuse `ErrorSummary.js` and `Notice.js`. `components/Review.js` is the pattern for retrying after `no_session`. `GuestShell.js` must not be used on Administrator pages.
- `tests/e2e/conftest.py` -- `Stack.compose("logs", …)` for the log search. `tests/e2e/a11y.py` provides `check_axe` and `no_horizontal_scroll`. `tests/e2e/test_fr11_refusals.py` shows the patterns.

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml`, `uv.lock`, `src/booking_platform/data/common-passwords.txt`, `ASSETS.md` -- the dependency and the list -- FR-19, AD-11
- [x] `migrations/0008_accounts_sign_in.sql`, `db/accounts.py`, `db/sessions.py`, `services/sessions.py` -- the schema and its SQL -- AD-11, AD-15
- [x] `services/auth.py` -- `check_password_rules`, `hash_password`, `sign_in(session, email, password)` (throttle, verify, rotate, rehash) and `sign_out(session)` -- FR-15, FR-19, PW-1–6
- [x] `seeds/admin.json`, `services/seed.py`, `__init__.py` (`create-admin`) -- the seeded Administrator and the CLI -- AD-18, AD-19
- [x] `api/admin.py`, `api/deps.py`, `api/schemas.py`, `api/errors.py`, `app.py` -- the endpoints and the resolved caller -- AD-8, AD-10
- [x] `tests/client.py`, `tests/conftest.py`, `tests/test_fr20_access.py` -- real sign-in in the fixture, throttle truncated, the guest case changed to 401 -- AD-21
- [x] `tests/test_fr15_sign_in.py` (the matrix rows; rotation; the old token after sign-out; the clock; 10 in parallel; unknown-email and wrong-password responses are byte-identical; a unit test of `services.auth` shows that verify runs for an unknown email), `tests/test_fr19_passwords.py` (rule cases, two accounts give two hashes, no readable column, PHC `$argon2id$`, seed restart keeps the hash, `create-admin` via `main(["create-admin"])` with `getpass` monkeypatched) -- FR-15, FR-19
- [x] `frontend/components/AdminBar.js`, `AdminGuard.js` (calls `GET /api/admin/me` on mount and on `pageshow`; renders nothing until it answers 200; on 401 does `router.replace('/admin/sign-in')`), `SignIn.js`, `app/admin/sign-in/page.js`, `app/admin/bookings/page.js`, `app/admin/page.js`, `lib/copy.js`, `lib/api.js`, `app/styles.css` -- UX-DR3, UX-DR30, UX-DR33
- [x] `tests/e2e/test_fr15_sign_in.py` -- sign in and out with the keyboard only; a wrong password gives the Error summary and the "Error: " title; anonymous `/admin/bookings` goes to Sign-in; Back after sign-out also leads to Sign-in; axe A/AA; no horizontal scroll at 1024/1366/1920; the test password and the cookie token are absent from `compose logs` -- FR-15, FR-21–23
- [x] `README.md` -- the test login, `create-admin` (with the PowerShell form) and the status line

**Acceptance Criteria:**
- Given `uv run pytest`, then every test passes, including those of Stories 1.1–1.6, with the Administrator fixture now signing in for real.
- Given `npm --prefix frontend run build`, then it succeeds.
- Given a fresh database, when the backend starts twice, then exactly one `accounts` row exists for `admin@saunaloyly.example`, and its hash is unchanged.

## Implementation Notes

- `seeds/admin.json` is optional, like `bookings.json`: a seed directory without it (the tests' `tmp_path` seeds) seeds no account. `tests/conftest.py`'s `root_without_sample_bookings` copies it.
- Passwords are NFC-normalised before hashing and before verify, as in the rule check, so one password typed on two keyboards is one password.
- `SignInIn` caps the fields (254 / 1024) and sets no minimum, so an empty or odd value is an ordinary `sign_in_refused` (counted), never a different answer. The page sends nothing for an empty field and shows the same Error summary; it also maps a `422` to that summary.
- `create-admin` reads the email with `input()` and the password with `getpass` twice. It also refuses a mismatch, an email that is not an email, and a password over 1024 characters, each with one line and exit code 2.
- `FocusMover`: after a client navigation to a page whose `h1` is not rendered yet (an Administrator page waiting for its guard), it focuses the `h1` when it appears, unless something else has taken focus.
- On the Booking list the `h1` is the last focus stop for now, so the e2e test reaches Sign out with `Shift+Tab` (through `a11y.press`).
- Matrix audit: the "No session" row's page behaviour (re-open the session, retry once) is covered by `tests/e2e/test_fr15_sign_in.py::test_a_lost_session_is_reopened_and_the_sign_in_retried_once`, added during verification.
- The stack's own log lines for sign-in say only "sign-in refused", "signed in: session N" and "signed out: session N".

## Spec Change Log

## Review Triage Log

Iteration 0 (blind-hunter BH, edge-case-hunter EC, verification-gap VG):

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| 1 | BH: seeded test login reaches any deployment | low | Real, but the seeded login is Lisa's recorded decision (Decisions, 2026-11-21) and there is no production target in scope | reject |
| 2 | BH+EC: Argon2 verify runs inside the transaction holding the throttle lock and a pool connection | medium | `auth.sign_in` `work`; the frozen Always block prescribes verify inside the one `db.run(work)`, so parallel sign-ins hold pool connections ~100 ms each | defer |
| 3 | BH: one wrong attempt every 15 min keeps the Administrator locked out; `create-admin` does not clear the throttle | low | The lock ends after 15 min and a correct password then succeeds unless an attacker strikes first; frozen throttle rules prescribe this; fix adds recovery behaviour | reject |
| 4 | BH+EC: `sign_in_throttle` grows without bound | low | Real; needs arbitrary-email flooding; fix is a new purge job, not a direct correction | reject |
| 5 | BH: `create-admin` "password changed" leaves the account's sessions valid | medium | `accounts.upsert` touches no sessions; a password change after a leak keeps an attacker signed in (sliding 8 h) | patch |
| 6 | BH: `require_admin` trusts the role copied onto the session | false | Core has one role and no role-changing path; `rotate` sets role and account together | reject |
| 7 | BH+EC: sign-in on a Guest session moves its Bookings/Holds to the Administrator session; sign-out NULLs them | low | Real, but the frozen intent mandates reusing the row; needs a Guest booking and signing in as staff in the same browser | reject |
| 8 | BH: common list has artefacts/handles; context words not checked | low | Harmless entries in a public MIT list filtered exactly per Lisa's decision; context words are not a rule in the intent | reject |
| 9 | BH: `_fail` typed `-> None` though it always exits | low | Direct correction to `NoReturn` | patch |
| 10 | BH+VG: `create-admin` email-shape, >1024 and EOF/cancel refusals untested | medium | `test_create_admin_refuses_*` covers only short/common/email/mismatch | patch |
| 11 | BH: byte-identical refusal compared only for wrong vs unknown, not throttled | low | `test_five_failures_*` checks only JSON; direct test addition | patch |
| 12 | BH: no busy state on Sign in / Sign out buttons | low | Not in the intent or UX-DR; adds UI state | reject |
| 13 | BH: sign-in/out/me responses lack `Cache-Control: no-store` | false | `Caddyfile:17` sets `Cache-Control no-store` on every `/api` response | reject |
| 14 | BH: "to be confirmed by Lisa" comment; unused `pg` param on `admin_client` | low | Copy confirmation is tracked in the session log; the param keeps existing callers unchanged | reject |
| 15 | BH: `test_fr20_access.py` docstring line over 120 columns | low | Direct re-wrap | patch |
| 16 | BH+EC: `FocusMover` observer/timer not cleaned up on pathname change | low | It only focuses when nothing has focus, so a stale observer can at most focus an h1 nobody focused; cleanup would break the Strict-Mode rerun the comment describes | reject |
| 17 | EC: NUL in sign-in email/password gives 500 instead of a uniform answer | low | `SignInIn` lacks the control-character pattern the Guest email has; psycopg refuses NUL in text → `StoreError` 500 | patch |
| 18 | EC: `create-admin` Ctrl-C/OSError during migrate prints a traceback | low | Interactive Ctrl-C traceback is ordinary CLI behaviour; connection failures are `psycopg.Error` and already handled | reject |
| 19 | EC: AdminGuard Notice has no retry short of reload | low | Notice copy says "please try again"; reload is the retry, as on Guest pages | reject |
| 20 | VG: Sign-in's "already an Administrator → Booking list" branch untested | medium | Pre-verified gap; no test opens Sign-in while signed in | patch |
| 21 | VG: Back after sign-out never restores an Administrator page; `pageshow` re-check never runs | medium | Pre-verified gap; Back reaches Sign-in by construction (`router.replace`), but the bfcache re-check is unproven and Chromium bfcache is unreliable under Playwright | defer |
| 22 | VG: Sign-in outage Notice and sign-out failure Notice untested | medium | Pre-verified gap; `page.route` stubs suffice | patch |
| 23 | VG: `rotate` failing (session gone between resolve and sign-in) untested | medium | Pre-verified gap; the branch must give `no_session` and leave the throttle untouched | patch |
| 24 | VG: NFC normalisation at sign-in untested | medium | Pre-verified gap; no NFD sign-in test | patch |
| 25 | VG: Administrator pages not checked against "only Sign-in and Book seats open a session" | medium | Pre-verified gap; `test_fr21_privacy.py` PAGES has no `/admin` path and its docstring omits the Sign-in exception | patch |

## Verification

**Commands:**
- `uv run pytest -q` -- expected: all pass
- `npm --prefix frontend run build` -- expected: success
