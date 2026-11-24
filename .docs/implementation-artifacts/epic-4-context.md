# Epic 4 Context: A Guest changes seats or takes a voucher

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Give every Seat booking a Manage link in its confirmation email. With it, a Guest can open that Booking, and only that Booking, without an account. Until the Cutoff (12 hours before the start), the Guest can move some or all Seats to another session (Window) or give them up for a Voucher worth what was paid. Seats are never refunded in money. A Voucher can later pay for all or part of a new Booking. The Administrator sees each Booking's status and its Change history in the Booking list. Moving Seats is built before the Voucher. The Manage page and its confirming-step pattern are shared components that Epic 5 (Whole-sauna booking) reuses.

## Stories

- Story 4.1: The Manage link opens the Booking
- Story 4.2: Move all or some Seats to another session
- Story 4.3: Give up Seats for a Voucher
- Story 4.4: Pay with a Voucher

## Requirements & Constraints

- **Manage link:** the token has at least 128 random bits, and only its hash is stored. It opens exactly one Booking, until that Booking's session ends. Unknown, malformed, revoked, expired and other people's links all get the same `404 not_found` and the page "This page is not available." The token never appears in a path, a query, a log line or a table (except as its hash).
- **No accidental changes:** loading a page never changes anything. Every Change needs an explicit confirming step that carries a one-time idempotency key. A repeated confirm applies the Change once and returns the first outcome.
- **Privacy:** Manage pages load no third-party resources and send no referrer. Caddy adds `X-Robots-Tag: noindex` and `Referrer-Policy: no-referrer` to `/manage*` and `/api/manage*`.
- **Cutoff:** after the Cutoff, the page still shows the Booking and refuses every Change with the reason and the time. Changes are possible only while `change_allowed` holds.
- **Move:** the move is atomic. If the target lacks room, nothing changes (catalogue E5: 3 Seats to a Window with 2 left is refused). The target must be inside the Booking horizon and before its Booking deadline. A partial move splits the Booking: the moved Seats get a new reference and their own Manage link, and both Bookings keep the price per Seat and the Cutoff. Freed Seats count in Seats left at once.
- **Voucher:** it is worth the Seats given up × the price paid per Seat, is valid for one year, and no money is refunded. The code, value and last valid date appear only in the Change's email, which the result page shows under "Sent by email:".
- **Paying with a Voucher:** it can pay for all or part of a Booking, and the rest goes through Simulated payment. The remaining balance stays on the Voucher until it expires. Expired, used-up and unknown codes get one identical refusal. Parallel uses never spend more than the Voucher's value.
- **Concurrency proofs:** a race test runs 100 times. Cross-Window moves in opposite directions and a move racing a new booking must never deadlock or oversell. Parallel Voucher spends must never take `balance_ore` below 0.
- **Accessibility:** axe finds no A or AA failure on the Manage page, the confirming steps, the result pages or Review with the Voucher field. Everything works with the keyboard alone, with no horizontal scroll at 1024, 1366 and 1920 px. Review's Pay button stays inside the first view at 1366×768.
- **Terms text:** the old "cannot be changed or refunded" wording is replaced everywhere (shared terms, the Terms page, Review, Confirmation, the email) with what a Guest can do up to 12 hours before the start.

## Technical Decisions

- **Manage token (AD-28):** `access_tokens(purpose='manage', token_hash bytea UNIQUE, revoked_at)`, with at most one unrevoked manage token per Booking (a partial unique index). Only `services.manage` writes it. `services.manage.issue(c, booking_id)` locks the Booking, revokes any previous token and stores the SHA-256 of `secrets.token_urlsafe(32)`. Only Booking creators call it: the Seat flow, a split, the seed, and later Whole-sauna and FR-34. No Change revokes or issues the original's token. A token's validity is judged by join and never stored.
- **Open flow:** the email link is `<BP_BASE_URL>/manage#t=<token>`. The `/manage` client component reads the fragment once (guarded against Strict Mode), clears it with `history.replaceState`, and calls `POST /api/manage/open {token}`. That call creates or reuses the session, upserts `manage_grants(session_id, token_id, last_used_at)` and returns `{reference}`. The client then navigates to `/manage/[reference]`.
- **Grant:** `manage_grant_valid(session_id, booking_id)` is the one predicate: last use within 30 minutes, the token unrevoked, and before the end of the Booking's Window. Grants cascade with their session. Startup purges stale grants. All grant routes live under `/api/manage/{reference}/` on one router. Its dependency checks the grant (404 otherwise, never 401) and then touches `last_used_at` in its own autocommit statement. Actions re-check the grant by join after the Booking re-read.
- **Routes:** `GET /api/manage/{reference}` returns the AD-23 serializer plus `version`, `change_allowed`, `cutoff_at` and history. It never returns an Outbox body, a Voucher code, a Manage link or a Sauna name. The Seat routes are `POST …/seats/move {window_id, seats, version}` and `…/seats/voucher {seats, version}`. A route of the wrong kind is `404`.
- **Cutoff (AD-4):** `settings.cutoff_seats` (default 12 h, `CHECK >= 2 hours`) is copied into `bookings.cutoff` at creation and kept on a move or split. `change_allowed(booking_id)` is the only Cutoff predicate. Time always comes from `app_now()`, and tests move the clock through `clock.off`.
- **Change transaction (AD-3, AD-29):** the action reads the Booking unlocked, calls `lock_windows` (current and target, in id order) and re-reads the Booking `FOR NO KEY UPDATE`. If `window_id` changed, it retries through `db.run`. It then re-checks the grant and reads the key. The refusal order is `booking_cancelled`, `booking_changed` (version mismatch), `change_invalid` (`seats_exceed` or `same_target`), `outside_horizon`, `deadline_passed`, `cutoff_passed` (with `cutoff_at`), then capacity in the store (`no_seat_free` with `seats_left`). `bookings.version` rises in the same UPDATE as every Change.
- **History:** `booking_changes` is written only by `services.history.record`, never by triggers. Per-`action` shape CHECKs: `move` sets both Window ids, `seats` and `new_booking_id` when the move is a split; `voucher` sets `seats` and `voucher_id`.
- **Cancellation:** `cancelled_at`, `cancel_cause` and `cancel_remedy` are bound by CHECKs, including `seat_guest_refund_forbidden`. A trigger refuses un-cancelling and any change to the Seats or Window of a cancelled row. Giving up all Seats for a Voucher is the only way to cancel a Seat booking.
- **Change response:** one serializer: `{booking, new_booking?, voucher?: {value_ore, last_valid_date}, emails: [{id, subject, body}]}`. Each Change sends one email, plus the split-off Booking's own confirmation, all through the Outbox with `change_id`. The emails carry no original Manage link and no Sauna name.
- **Idempotency (AD-9):** `idempotency_keys.change_id` exists, with exactly one of `booking_id` and `change_id` set. The same key from the same session returns the first outcome. A different request or another session gets `409 invalid_key`. The frontend key slot is `draft:change:<reference>:<action>`.
- **Voucher (AD-30):** `vouchers(code_hash, value_ore, balance_ore, issued_at, expires_at, booking_id)`. Only `services.voucher` writes it. The code is 16 Crockford base32 characters (`XXXX-XXXX-XXXX-XXXX`), and only its unkeyed SHA-256 hash is stored. Input is normalised (upper case, hyphens and spaces removed, I/L→1, O→0) and anything invalid is `voucher_invalid`, never 422. `expires_at` is 00:00 venue time on the day after the last valid date. Spending is one conditional `UPDATE … WHERE balance_ore >= :part AND expires_at > app_now() RETURNING id`, run after `lock_windows`, the deadline checks and the Booking insert. `POST /api/vouchers/quote` takes no lock, writes nothing and never reveals the balance or expiry.
- **Ledger (AD-31):** a partial or full Voucher Change writes a `payments` row `refund`/`voucher` with `voucher_id`. A payment with a Voucher writes `charge`/`voucher`, plus `charge`/`card` for any rest. A split writes no payments rows. For a Booking with no split, charges minus returns equal `total_ore` while it is active and 0 once it is cancelled. `retention_due(booking_id)` becomes the one retention predicate, including Voucher expiry.
- **Secrets (AD-19):** the e2e log search must find no Manage token and no Voucher code in any container's log.

## UX & Interaction Patterns

- The Manage page shows the reference, date, session, Seats, total paid and until when Changes are possible (from `cutoff_at`, in Venue time), then the available Changes. Focus moves to the `h1` on arrival.
- The shared components live in `frontend/components/`: `ManageBookingSummary`, `ConfirmingStep` (states what will happen, changes nothing until confirmed) and `ChangeResult` (shows the emails under "Sent by email:"). The move step reuses the Date calendar, the Seat picker, the Session list and the Windows listing from Epic 1.
- A refusal shows a Notice with the reason from the frontend code table and keeps the Guest's choices. After `booking_changed` or `invalid_key`, the page reloads the Booking and opens a fresh step with a new key.
- On Review, the Voucher field (a Text field with a Text link) sits between the Booking summary and the terms and is always visible. A valid code shows the Voucher part in the summary and updates the Pay label to the card part. Any invalid code shows one identical Field error and an Error summary entry. After a refusal, the code stays in the draft and is quoted again.
- Lisa still has to decide: what the page shows after the session has ended (Open Item 21; possibly "not available"), the wording of the Cutoff reason (22), how the current session appears in the move target list, the page after all Seats were given up (19), and the Pay wording when a Voucher covers the whole total, plus the Text link label (23).

## Cross-Story Dependencies

- **Depends on Epics 1–3:** the Seat flow, `lock_windows`, sessions (AD-8), the Outbox, idempotency, the Booking list and HTTPS. Manage links must be `https://` before they are emailed.
- **Within the epic:** 4.1 builds the token, the grant, the read and the shared components. 4.2 adds `booking_changes`, history and the Change pattern. 4.3 adds `vouchers` and the cancellation columns. 4.4 spends Vouchers in `POST /api/bookings`.
- **Seed and README:** sample Bookings get Manage links through the seed's Outbox emails, idempotently. The README explains where to find a sample Manage link and how to get a Voucher. After 4.4, "Not delivered" no longer lists SC3 or FR-25 to FR-28.
- **Enables Epic 5:** the Whole-sauna routes (`…/whole/move`, `…/whole/cancel`), `cutoff_whole` and `services.payment.refund` reuse this epic's token, grant, Change, history, Voucher and ledger patterns.
