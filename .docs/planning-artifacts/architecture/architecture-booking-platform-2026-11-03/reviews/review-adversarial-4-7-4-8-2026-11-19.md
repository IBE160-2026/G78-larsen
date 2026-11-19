---
review: adversarial
target: ../ARCHITECTURE-SPINE.md (amendment of 2026-11-19 for PRD §4.7 and §4.8: AD-27 to AD-31; amended AD-4, AD-8, AD-9, AD-12, AD-13, AD-16, AD-22)
date: '2026-11-19'
lens: 'Two units one level down that each obey every AD to the letter yet still build incompatibly: clashing shared-data shapes, two owners of one entity, conflicting state-mutation paths, lock-order deadlocks, races, security holes and time-rule edges'
inputs:
  - ARCHITECTURE-SPINE.md (updated 2026-11-19)
  - .memlog.md (2026-11-19 entries for §4.7 and §4.8)
  - prds/prd-booking-platform-2026-10-29/prd.md (§3, §4.4 FR-16, §4.5 FR-20 and FR-21, §4.7, §4.8, FR-33, §7)
  - prds/prd-booking-platform-2026-10-29/addendum.md (§A Manage-link hardening, token table)
  - prds/prd-booking-platform-2026-10-29/appendix-fr-34-51.md (FR-34, FR-39, FR-42)
  - ux-designs/ux-booking-platform-2026-11-05/EXPERIENCE.md (open items 19 to 21)
  - src/booking_platform/db.py (slice: isolation level)
---

# Adversarial review: §4.7 HTTPS and §4.8 Changes and Vouchers (AD-27 to AD-31)

## Verdict

The amendment is sound in its main choices: the token stays out of paths and logs, Voucher writes always come after the Window locks, refunds go through one function, and capacity stays with the store. None of the holes below lets capacity be exceeded. But two pairs of stories will collide as soon as they are built:

- **The Change confirmation email.** PRD §7 says it carries the Manage link, but AD-28 throws the raw token away. The move story then either revokes the Guest's own link or breaks §7.
- **Two Changes on one Booking.** Two tabs or two devices can each send a Change for the same Booking, and no rule says what a stale request means. A partial move can quietly become a full move, and a request for more Seats than the Booking still holds ends in a 500.

Thirteen medium holes leave shapes and edge cases open. The main ones are idempotency comparisons against a Booking that a Change has already altered, sliding grants that write on GET, an unstated isolation level, the payments ledger, kind-specific routes, HSTS on `localhost` and an unconstrained local CA. Each one needs a rule written into the spine before the If-time 1 and 2 stories are drafted.

## Method

The units are the stories one level down from the amendment:

| # | Unit | Main ADs |
| --- | --- | --- |
| U1 | HTTPS listeners and certificate (`main()`, `tls.py`) | AD-27, AD-22 |
| U2 | Headers middleware, Secure cookie, HT-1 to HT-4 tests | AD-27, AD-8, AD-12 |
| U3 | Manage link: `access_tokens`, `issue()` in every creator, `POST /api/manage/open`, grant router, Manage page read | AD-28, AD-8, AD-10 |
| U4 | FR-26 Seat move, full and split | AD-29, AD-3, AD-20, AD-28 |
| U5 | FR-27 Voucher instead of Seats | AD-29, AD-30 |
| U6 | FR-28 pay with a Voucher (Review page field, spend) | AD-30, AD-13, AD-9 |
| U7 | FR-33 cancel with a remedy, `refund()` | AD-31, AD-23, AD-29 |
| U8 | FR-33 Whole-sauna move (built in §4.9, now with grant, key and history) | AD-23, AD-24, AD-29 |
| U9 | FR-16 Administrator list with history and cancellations | AD-29 |
| U10 | FR-21 retention catch-up that reads Vouchers | AD-4, AD-30 |
| U11 | SPA Manage pages and `api.js` | AD-9, AD-16, AD-17 |
| U12 | Group-C, Hypothesis and test harness changes | AD-26, Conventions |
| Dev | Lisa's dev loop (`booking-platform dev`, Vite) | AD-27 Environments |

A pair counts as a hole when both units comply literally and the merged result is wrong. Wrong here means a crash or 500, a rule silently lost, one fact in two shapes, two writers of one row, a deadlock, a leak, or a PRD consequence that cannot be met.

## Summary

| # | Hole | Units | Severity |
| --- | --- | --- | --- |
| 1 | Change emails must carry the Manage link (§7), but the raw token exists only in the Outbox; reissuing revokes the Guest's link and voids the open grant | U3 ↔ U4/U7/U8 | high |
| 2 | Two Changes on one Booking (two tabs or devices): a stale request has no meaning, a partial move becomes a full move, more Seats than held gives a 500 | U4 ↔ U5 ↔ U7/U8 ↔ U11 | high |
| 3 | Idempotency compares against the current Booking, which Changes alter; keys of one kind replayed on the other kind | U6/Core ↔ U4/U5 | medium |
| 4 | One `sessionStorage` key slot per reference, reused across actions; after `409 invalid_key` the Guest is stuck | U11 ↔ AD-9 server | medium |
| 5 | A repeated Change cannot rebuild its response: emails are not linked to the Change, and Voucher codes are hashed | U4/U5/U7 ↔ AD-9 | medium |
| 6 | Sliding grant: it writes on GET (AD-4), deadlocks if it slides inside the action, stores a Window end that a move changes, and judges time before the lock | U3 ↔ U4/U7/U8 | medium |
| 7 | Isolation level is not stated; pre-lock reads (Voucher plan, Booking `window_id`) are correct only under READ COMMITTED | U6 ↔ U4 ↔ db | medium |
| 8 | `booking_changes` has many writers and no per-action shape; the Change response has no shape | U4/U5/U7/U8 ↔ U9 ↔ AD-9 | medium |
| 9 | Change routes are not per kind: `/cancel` on a Seat booking duplicates FR-27, and a refund on it hits an unmapped CHECK (500) | U7 ↔ U5 ↔ U11 | medium |
| 10 | Payments ledger: FR-27 and the voucher remedy write no `payments` row; `refund()` sums charges, not `total_ore`; a split-off Booking has none, against the ER | U5/U7 ↔ U9 ↔ later FR-42 | medium |
| 11 | Review page cannot show "Pay NOK 0" or the card part: no quote endpoint; the order of `voucher_invalid` among the other refusals is open | U6 ↔ U11 | medium |
| 12 | HSTS on host `localhost` upgrades `http://localhost:8000` and `:5173` to TLS: the redirect listener and the dev loop break for an hour | U1/U2 ↔ Dev ↔ examiner | medium |
| 13 | Local CA with an unconstrained key in `certs/`: importing `ca.pem` (as the README invites) trusts that key for every domain | U1 ↔ README | medium |
| 14 | HT-3 "never sent over HTTP" is literally false on `localhost`; the test contract is undefined | U2 ↔ PRD FR-24 | medium |
| 15 | No canonical origin: the certificate covers `127.0.0.1` and `::1`, but cookies, CSRF and the base URL are `localhost` | U1 ↔ U2 ↔ AD-8 CSRF | medium |
| 16 | Manage page read: no time facts (Cutoff, can change), and nothing forbids it from returning Voucher codes or emails | U3 ↔ U11 ↔ FR-17 | medium |
| 17 | Headers miss 500s and server errors; no `Cache-Control: no-store`; addendum's `noindex` missing | U2 ↔ U3 | low |
| 18 | Redirect listener: decoded path, CRLF, base URL from port, one server dying | U1 | low |
| 19 | Voucher expiry: stored instant vs printed date; a refund Voucher born expired; the voucher remedy extends an old expiry | U5/U7 ↔ U6 ↔ PRD | low |
| 20 | AD-8 "no other page load creates a session" vs AD-28 open; FR-21 sentence; sign-out deletes grants | U3 ↔ Core session ↔ privacy notice | low |
| 21 | Bookings made before If-time 2 (seed samples) never get a Manage link | U3 ↔ seed | low |
| 22 | `access_tokens` concurrent issue hits the partial unique index; grants pile up | U3 ↔ later FR-34 | low |
| 23 | Test server: ports, `ca.pem` race, base URL for HT-4 | U12 ↔ U1 | low |

Counts: critical 0, high 2, medium 14, low 7.

---

## 1. The Change email needs a link that no longer exists (high)

**Units.** U3 owns tokens. U4 (move and split), U7 (Whole-sauna cancel) and U8 (Whole-sauna move) write the Change emails.

**How each obeys.**
- **U3** follows AD-28: `issue()` runs only in the transaction that creates a Booking. Only the hash is stored, and "the raw token exists afterwards only in the Outbox".
- **U4** follows PRD §7, which AD-12 makes binding for email content. The row "Confirmation of a Change (FR-26, FR-33)" lists "What changed, the new Window and Seats, the Manage link". FR-26 adds: "The original Booking keeps its reference and link".

**Incompatibility.** U4 has no raw token for the original Booking, so it has three ways out, and each one breaks something:
- **It calls `manage.issue(c, booking_id)` to get a fresh token.** AD-28 does not forbid this. `issue()` revokes the earlier token, so the link in the Guest's confirmation email dies, against FR-26 ("keeps its … link"). The acting session's grant is "void as soon as its token is revoked", so the next request from the open Manage page returns 404 and shows "This page is not available" right after a successful move.
- **It parses the token out of an earlier Outbox body.** That couples the Change to email text. It also fails once retention has cleared the body.
- **It leaves the link out.** That breaks §7, and a Whole-sauna move email built by U8 under the same rule then differs from U4's.

**Severity: high.** The first §4.8 story hits this at once, and two of its three readings break a PRD consequence or the open page.

**Closing wording.** Lisa chooses between two options.

> **Option B (recommended, needs one PRD §7 edit). AD-12, Links:** only an email about a new Booking carries a Manage link: the Booking confirmation and the split-off Booking email. A Change confirmation never repeats a link. It says "Use the Manage link in your booking confirmation email". PRD §7, row "Confirmation of a Change": "the Manage link" becomes "a pointer to the Manage link already sent".
>
> **Option A (keeps §7, adds a secret). AD-28, Storage:** a Manage token is derived, never stored: `token = base64url(HMAC-SHA256(link_key, 'manage:' || access_tokens.id))`. `link_key` is 32 random bytes that `main()` creates at first start in `BP_KEY_DIR` (git-ignored, beside `certs/`). The store keeps only `SHA-256(token)`. `services.manage.link(c, booking_id)` recomputes the current link for any email.
>
> **Both options, AD-28, Issue:** `issue()` is called only by Booking creators (and later FR-34). No Change calls it for an existing Booking, and no Change revokes a token.

## 2. Two Changes on one Booking (high)

**Units.** U4 (move, split), U5 (Voucher for some or all Seats), U7/U8 (Whole-sauna cancel or move), U11 (Manage page). The Guest opens the Manage link on a phone and on a laptop. That gives two sessions and two grants, and each confirming step has its own key.

**How each obeys.** AD-3's Booking-scoped order serialises the two requests on the source Window. The second one re-reads the Booking after the lock. If `window_id` changed, it retries and runs again against the moved Booking. AD-29 checks `booking_cancelled`, then horizon, deadline and Cutoff, then capacity. AD-29 defines "All Seats → UPDATE window_id; Some Seats → split" by comparing with the Booking as re-read.

**Incompatibility.** Take a Booking of 3 Seats in W1.
- **Laptop:** "give up 1 Seat for a Voucher" commits. The Booking now holds 2 Seats.
- **Phone:** "move 2 of 3 Seats to W2" runs next. After the re-read, 2 equals all the Seats, so U4 performs a full move: no split, no new reference, no new link. The Guest asked for a split and keeps 0 Seats in W1. The phone's result page expects a `new_booking` that does not exist.
- **Phone instead asks "move 3" or "Voucher for 2" after the laptop gave up 2.** The requested Seats now exceed the Booking's Seats. No refusal code exists for this, because 422 is for shape only (AD-16). Story A computes `seats - req` = −1 and hits the `bookings.seats` CHECK, which is an unnamed store refusal and so a 500 under AD-1. Story B clamps the request and issues a Voucher worth less than the response states.
- **Whole-sauna move on one device, cancel on the other.** The second request retries onto a moved Booking and cancels it, although the Guest asked to cancel a different Window.

**Severity: high.** The behaviour is undefined, and FR-25 (confirming twice applies once) only covers the same key.

**Closing wording (AD-29, new bullet "Concurrent Changes"; AD-16 adds the code):**
> **Version:** `bookings.version int NOT NULL DEFAULT 0` is incremented by every Change and every cancellation, in the same UPDATE. Every Booking JSON carries `version`, and every Change request carries the `version` the Guest saw. After the lock, the re-read and the idempotency key read, the order of checks is:
> 1. `booking_cancelled`;
> 2. `409 booking_changed` when the version differs, with the current Booking as its fact;
> 3. AD-24's order;
> 4. capacity in the store.
>
> **Seats:** a Seat Change names `seats` from 1 to the Booking's Seats at that version. Equal means all Seats, and fewer means a split or a partial Voucher. A target Window equal to the current Window is `409 same_window`. `version` is not in AD-7's trigger column list, so it fires no capacity trigger.

## 3. Idempotency compares against a Booking that Changes alter (medium)

**Units.** Core Booking creation and U6 (AD-9 "Same request") against U4 and U5, which alter `window_id`, `seats` and `status` in place (AD-29).

**How each obeys.** AD-9 says: "a known key whose Booking's `kind`, `window_id`, or `seats` or `sauna_id` differ from the request is refused with `409 invalid_key`". It also says: "A repeat rebuilds the original response from the Booking." For Changes: "differs in Booking, action, target Window … compared with the `booking_changes` row".

**Incompatibility.**
- **A lost response after a Change.** The paying tab's response is lost, and the Guest opens the Manage link from the Outbox email and moves the Booking. The paying tab then retries with its key. The Booking's `window_id` now differs from the request, so the paying Guest gets `409 invalid_key` for a paid Booking. That is exactly what AD-9 exists to prevent. A rebuild that does succeed shows the moved Window as if it were the first outcome.
- **A key replayed on the other kind.** A key stored for a creation (`booking_id` set, `change_id` NULL) arrives at a Change endpoint, or the reverse. One story reads `booking_changes` by a NULL `change_id` and crashes. Another treats the request as a repeat and returns the creation response from a Change URL.

**Severity: medium.**

**Closing wording (AD-9):**
> **Fingerprint:** `idempotency_keys` gains `endpoint text NOT NULL` and `request_hash bytea NOT NULL`. The hash is SHA-256 of the canonical outcome-defining fields: kind, Window, Seats, Sauna, reference, action, target Window, target Sauna, remedy and `version`. It never covers name, email or Voucher code. A known key from the same session is a repeat only when both the endpoint and the hash match. Anything else is `409 invalid_key`. Repeats never compare against the current Booking or Change row.
>
> **Rebuild:** a repeat returns the first outcome. That is the emails recorded at first success, read by id (finding 5), plus the Booking as it is now, in the AD-23 serializer.

## 4. The SPA's key slot is shared by every confirming step of a Booking (medium)

**Units.** U11's move dialog and Voucher dialog. AD-9's server rule.

**How each obeys.**
- **AD-9, Changes:** the key is "made when the confirming step opens and kept in `sessionStorage` as `draft:change:<reference>`".
- **AD-9, Core:** the SPA "reuses the same key for every retry until the booking is paid", and "after `409 invalid_key` the SPA never makes a new key on its own".

**Incompatibility.** The move dialog writes `draft:change:ABCD1234` and succeeds. Nothing says it clears the key, because the Core rule clears it only "until paid". The Voucher dialog finds a key in the same slot and reuses it. The server answers `409 invalid_key` because the action differs. The SPA may not make a new key, so the Guest cannot give up Seats until the tab is closed.

The same thing happens when a first attempt at W2 got a lost response, the Guest picks W3, and the stored key is replayed against a different target.

**Severity: medium.**

**Closing wording (AD-9, Changes):**
> The slot is `draft:change:<reference>:<action>`. It is created when that step opens and deleted on success, on any refusal other than `503 try_again`, and when the Guest leaves the step. A refusal stores nothing on the server, so dropping the key is safe. After `409 invalid_key` or `409 booking_changed`, the Manage page reloads the Booking and starts a fresh step with a new key. The Core's "never on its own" rule applies only to `draft:seats` and `draft:whole`.

## 5. A repeated Change cannot rebuild its own response (medium)

**Units.** U4, U5 and U7 send emails. AD-9 says repeats are rebuilt "from the `booking_changes` row".

**How each obeys.** AD-12 says each Change returns its emails in its response, and a split returns two. `outbox.send(…, booking_id=)` links an email to a Booking only. AD-30 stores a Voucher as `code_hash` and `code_last4`.

**Incompatibility.**
- **The emails.** The history row does not name the emails it sent. Story A rebuilds a repeat by taking "the latest email for this Booking". If a second Change happened in between, that returns another Change's email. Story B returns no email.
- **The Voucher code.** A repeat of an FR-27 Change must show the Voucher code (the FR-27 result page), but the code exists only in the email. A third story might store the raw code "for the repeat", which breaks AD-30.

**Severity: medium.**

**Closing wording (AD-12, Guest read; AD-29, History):**
> `outbox_emails` gains `change_id` (nullable, FK `booking_changes`). `outbox.send(c, …, booking_id=None, change_id=None)` sets it for every email a Change sends. A creation's emails are found through the key's `booking_id` and the confirmation email id the creation stores. A repeat returns exactly those emails, read by id, and never "the latest email of the Booking". A Voucher code or Manage link reaches a repeat only through that stored email. Once retention has cleared the body, the repeat returns the facts without it.

## 6. The sliding grant: writes on GET, lock order, a stored Window end, and time before the lock (medium)

**Units.** U3 (grant router) against U4, U7 and U8 (Change actions), and against AD-4.

**How each obeys.**
- **AD-28:** "a grant lasts 30 minutes, sliding on each use, and never past the end of the Booking's Window", stored as `manage_grants(session_id, token_id, expires_at)`. Loading a Manage page "never changes anything".
- **AD-4:** "GET endpoints never write", with a single exception (`ensure_generated`).
- **AD-3:** every write in an action comes after `lock_windows`.

**Incompatibility.**
- **GET writes.** Sliding on "each use" includes `GET /api/manage/{ref}`, and that GET writes `expires_at`. A test written to AD-4 flags it. The session's own sliding expiry (AD-8) has the same unnamed exception.
- **Lock order.** Story A slides the grant inside the Change's `db.run`, before `lock_windows`, in the same transaction. Two tabs of one session then confirm two Changes: T1 slides the grant row and waits for W1, while T2 holds W1 and slides the same grant row. That deadlock is retried, so it costs latency rather than correctness. AD-3's "no write before the lock" is broken either way.
- **The stored Window end.** `expires_at` is capped at the Window end when the grant is opened. A move to an earlier Window leaves a grant that outlives the new Window. A move to a later Window kills the grant at the old end, while the token is still valid.
- **Time before the lock.** Validity is a time rule (`app_now()`) judged in the router dependency, before any lock. AD-4 says every time rule is judged after the lock.

**Severity: medium.**

**Closing wording (AD-28, Grant; AD-4, Reads never write):**
> **Shape:** `manage_grants(session_id, token_id, last_used_at)`, with UNIQUE `(session_id, token_id)`. `open` upserts it.
>
> **Validity:** a grant is valid while all of these hold, judged by one SQL function `grant_valid(session_id, booking_id)`:
> - `app_now() < last_used_at + interval '30 minutes'`;
> - `app_now() < upper(during)` of the Booking's current Window, by join, never stored;
> - its token is unrevoked.
>
> **Where it is checked:** the router dependency judges it before the action. That is an access check, exempt from AD-4's "after the lock", because the Cutoff that every Change judges after the lock is always earlier. The action re-checks it by join, read-only, right after the Booking re-read.
>
> **Sliding:** the dependency touches `last_used_at`, and AD-8 touches the session's expiry, in one autocommit statement outside every action transaction. These touches are AD-4's second named exception to "reads never write". No action transaction writes `sessions` or `manage_grants` before `lock_windows`. The split's new grant is inserted after the lock.

## 7. Isolation level is not stated (medium)

**Units.** U6 (Voucher planned before the lock), U4 (`window_id` read before the lock) and `db.run`.

**How each obeys.** AD-3 and AD-30 both read before the lock and rely on a fresh view after it. The slice's `db.py` sets no isolation level, so it runs at READ COMMITTED. The addendum says "Serializable isolation can act as a backstop".

**Incompatibility.** A story that follows the addendum's hint sets REPEATABLE READ or SERIALIZABLE on the pool:
- **Snapshot.** The pre-lock planning read fixes the snapshot. After the lock, AD-9's key read and AD-3's re-read see data from before the lock. A concurrent duplicate's committed key is invisible, so the INSERT of the key hits UNIQUE and returns 23505, unmapped, a 500.
- **Retries.** The conditional Voucher UPDATE turns into a serialisation failure and a retry rather than a re-check.

None of AD-3's ordering arguments hold any more.

**Severity: medium.**

**Closing wording (AD-3, new bullet "Isolation"):**
> `db.run` runs every transaction at READ COMMITTED, set explicitly on the pool. AD-3's read-lock-re-read, AD-9's key read after the lock and AD-30's planning read and conditional spend are correct only at this level, because each statement after the lock sees every commit before it. No story raises the level, and serializable is not used as a backstop.

## 8. History rows: many writers, no shape (medium)

**Units.** U4, U5, U7 and U8 each write `booking_changes`. U9 reads it, and so do AD-9 repeats.

**How each obeys.** AD-29 says: "Only `services` writes it". The table lists twelve columns, all nullable, and gives no rule for which columns each action fills.

**Incompatibility.**
- **`seats`.** U4 writes the Seats moved, and U5 writes the Seats remaining. U9 shows "3 Seats" for both.
- **Whole-sauna move.** U8 leaves `from_sauna_id` NULL when the Sauna does not change. U9 then cannot tell "same Sauna" from "unknown".
- **Remedy.** U7 sets `remedy` on a `cancel` row. U5 sets `remedy = 'voucher'` on a `voucher` row as well.
- **Response shape.** Each story returns its own response shape: `{booking, emails}`, `{original, new}`, `{voucher_code, …}`. U11 needs one shape.

**Severity: medium.**

**Closing wording (AD-29, History):**
> `services.history.record(c, booking_id, action, **cols)` is the only writer of `booking_changes`. CHECK constraints fix each action's shape:
>
> | `action` | Required | Must be NULL |
> | --- | --- | --- |
> | `move` | `from_window_id`, `to_window_id`, and `seats` for a Seat booking or both Sauna ids for a Whole-sauna booking | `new_booking_id`, `voucher_id`, `remedy` |
> | `split` | `from_window_id`, `to_window_id`, `seats`, `new_booking_id` | `voucher_id`, `remedy` |
> | `voucher` | `seats`, `voucher_id` | the Window ids, `remedy` |
> | `cancel` | `remedy`; `voucher_id` when a Voucher was issued | |
>
> `seats` always means the Seats moved or given up.
>
> **Response:** every Change response comes from one serializer: `{booking, new_booking?, voucher?: {code_last4, value_ore, expires_at}, emails: [{id, subject, body}]}`.
>
> **FR-27 email:** FR-27 sends one email, the Voucher email of §7, which also states the Seats left on the Booking.

## 9. Change routes are not per kind (medium)

**Units.** U7 (`POST /api/manage/{reference}/cancel {remedy}`, AD-31), U5 (FR-27 "all Seats → cancelled with guest and voucher") and U11.

**How each obeys.** AD-31 names a cancel route but does not limit it to `kind = 'whole'`. AD-29's CHECK forbids `seats` + `guest` + `refund`.

**Incompatibility.**
- **Two paths for one effect.** A Seat booking cancelled through `/cancel {remedy: voucher}` gets a `cancel` history row and the Whole-sauna email text. FR-27 for all Seats gets a `voucher` row and the Voucher email. Both end in the same state.
- **A refund on a Seat booking.** `/cancel {remedy: refund}` on a Seat booking reaches the CHECK. The CHECK is unnamed in the mapping, so AD-1 makes it a 500.
- **Seat-only actions on a Whole-sauna booking.** Move-some-Seats or Voucher on a Whole-sauna booking has no defined code.

**Severity: medium.**

**Closing wording (AD-28, Access; AD-31):**
> Change routes are per kind:
> - `/api/manage/{reference}/seats/move` and `/seats/voucher` for `kind = 'seats'`;
> - `/whole/move` and `/whole/cancel {remedy}` for `kind = 'whole'`.
>
> A route of the other kind answers `404 not_found`, the same as no grant. Giving up all Seats is only `/seats/voucher`. The CHECK is named `seat_guest_refund_forbidden` and maps to a 500, since no route can reach it.

## 10. The payments ledger does not add up (medium)

**Units.** U5 (FR-27), U7 (voucher remedy, `refund()`), U9 (audit and list), and later FR-42.

**How each obeys.**
- **AD-13:** `payments` rows "record how the value was funded and returned".
- **AD-29:** FR-27 issues a Voucher and sets `total_ore = seats × price`, and mentions no `payments` row.
- **AD-31:** `refund()` "refunds the whole `total_ore`: the card charges as one … row … and the Voucher charges as one new Voucher of their sum".
- **The ER diagram:** `bookings ||--|{ payments`, so every Booking has at least one payment.

**Incompatibility.**
- **`refund()` contradicts itself.** Take a Seat booking of 3 × 500 paid as 1000 card plus 500 Voucher, which then gives up 2 Seats for a Voucher (FR-27). `total_ore` is 500, but the charges sum to 1500. A later `refund()`, which keeps its signature for FR-42, returns 1000 card plus 500 Voucher, three times the remaining value. The spine says "refunds the whole `total_ore`" and "the charges … their sum", and these disagree as soon as any value has been returned.
- **Voucher remedy.** FR-33's voucher remedy writes no `payments` row, so U9 cannot tell from `payments` how the value went back.
- **Split-off Booking.** It has no payment at all, which breaks the ER cardinality that U9's audit may assert.

**Severity: medium.** In the planned v1 only Whole-sauna bookings are refunded, and their totals never change, so the fault is latent. It goes off with the first If-time 7 story.

**Closing wording (AD-13, Payments; AD-31; ER):**
> **Every return writes a row.**
> - FR-27 writes `refund`/`voucher` of the Voucher's value.
> - FR-33's voucher remedy writes `refund`/`voucher` of `total_ore`.
> - `refund()` writes its own rows.
>
> **Ledger rule:** for a Booking with no `split` in its history, `sum(charge) − sum(refund) = total_ore` while active, and `= 0` once cancelled with a remedy. The model test (AD-26) asserts this after every step.
>
> **`refund()` scope:** it applies only to a Booking whose `payments` are charges only and that has no `split`. Otherwise it raises an internal error (500) until If-time 7 decides attribution (Deferred).
>
> **ER:** a split-off Booking has no `payments` rows, so the ER reads `bookings ||--o{ payments`.

## 11. The Review page cannot price a Voucher, and its refusal has no place in the order (medium)

**Units.** U6 (server spend) and U11 (Review page with the Voucher field; UX state "a Voucher that covers the whole total, where 'Pay NOK 0' needs other wording").

**How each obeys.** AD-30 plans the Voucher part before the lock and spends it after. AD-16 lists `voucher_invalid` but does not place it. AD-24 orders horizon, then deadline, then Cutoff, then capacity. AD-30 also says "unknown, expired and used-up codes get the same refusal before the lock", while AD-16 says every rule judged against the store or the clock is decided after the lock.

**Incompatibility.**
- **No quote.** U11 must show the card part before the Guest pays, but no endpoint returns it. One story adds `GET /api/vouchers/{code}`, which puts the code in a path and the access log (against AD-19) and reveals the balance and expiry. Another computes the split in the SPA from a balance it cannot get.
- **Order.** A full Window combined with an invalid code returns `voucher_invalid` in U6 (checked before the lock) and `no_seat_free` in U11's tests.
- **Expiry before the lock.** The pre-lock expiry test is a time rule judged before the lock.

**Severity: medium.**

**Closing wording (AD-30, new bullet "Quote"; AD-16):**
> **Quote:** `POST /api/vouchers/quote {code, kind, window_id, seats | sauna_id}` needs a session (`401 no_session`), takes no lock and writes nothing. It returns `{voucher_part_ore, card_part_ore}` or `409 voucher_invalid` with no facts. It is a hint only. No response ever states a Voucher's balance or expiry; only the Voucher email does.
>
> **Order in a paying action:** the payment outcome is decided before the lock (AD-13). After the lock the order is `outside_horizon`, `deadline_passed`, capacity, then `voucher_invalid`. The pre-lock read only plans and never refuses. A code that matches no spendable Voucher is `voucher_invalid` after the lock, even when the planned part is 0.

## 12. HSTS on `localhost` breaks the redirect listener and the dev loop (medium)

**Units.** U1 and U2 (HSTS on every HTTPS response, host `localhost`). The dev loop (`http://localhost:5173`, backend `:8000`). The examiner demonstrating HT-1.

**How each obeys.** AD-27 sends `max-age=3600` with no `includeSubDomains`, and runs the redirect listener at `http://localhost:8000`. The memlog notes that "HSTS is per host, not per port".

**Incompatibility.** After one HTTPS page load, the browser itself rewrites every `http://localhost:<any port>` to `https://localhost:<same port>` for an hour (RFC 6797 §8.3 keeps the port).
- **The redirect listener.** `http://localhost:8000` becomes a TLS handshake against a plain-text listener and fails with a protocol error. The examiner who types `http://localhost:8000` to see HT-1 gets a browser error instead of the redirect.
- **The dev loop.** Lisa's `http://localhost:5173` breaks the same way for an hour after every examiner-mode run.

IP literals are exempt (RFC 6797 §8.1), and the Vite proxy already targets `127.0.0.1`.

**Severity: medium.**

**Closing wording (AD-27, Environments and README):**
> **Dev host:** dev uses `127.0.0.1` everywhere: Vite `server.host = '127.0.0.1'` and the README dev URL `http://127.0.0.1:5173`. IP literals ignore HSTS.
>
> **Showing HT-1:** HT-1 is shown with `curl -i http://localhost:8000/` or at `http://127.0.0.1:8000/`. The README says that after the first HTTPS visit a browser upgrades `http://localhost:8000` itself and shows a TLS error for that port, which is HSTS working.
>
> **Tests:** HT-1 is tested with an HTTP client that keeps no HSTS state, and HT-2 with the header value.

## 13. The local CA can sign for any domain (medium)

**Units.** U1 (`tls.py` creates the CA) and the README, which says "how to import `certs/ca.pem` if wanted".

**How each obeys.** AD-27 creates "a local CA, and a leaf for `localhost`…, valid 365 days", reuses an existing CA, and keeps `certs/` git-ignored. It sets no constraint on the CA and no validity for it.

**Incompatibility.**
- **Trust for every domain.** An examiner who imports `ca.pem` into the OS store trusts `ca-key.pem` for every domain. On Windows that key sits in a folder any local process can read, so anyone who can read it can intercept the examiner's bank's TLS.
- **CA validity.** If the CA is made valid for 365 days like the leaf, the leaf renewed in year 2 is signed by an expired CA. The "existing CA is reused" rule then serves an invalid chain.

**Severity: medium.** It is a security hole the README invites.

**Closing wording (AD-27, Certificate):**
> **CA extensions:** the CA carries a critical `NameConstraints` that permits only `DNS:localhost`, `IP:127.0.0.1/32` and `IP:::1/128`, `BasicConstraints(ca=True, path_length=0)` and `KeyUsage(key_cert_sign, crl_sign)`. It is valid for 10 years.
>
> **Leaf extensions:** the leaf has `BasicConstraints(ca=False)` and `ExtendedKeyUsage(serverAuth)`.
>
> **Renewal:** the leaf is renewed when it expires within 30 days. The CA, and with it the leaf, is renewed only when `ca.pem` or `ca-key.pem` is missing, or when the CA would expire before the new leaf.
>
> **Key file:** `ca-key.pem` is written owner-only where the OS supports it.
>
> **README:** importing `ca.pem` trusts it only for those names, and removing the import and `certs/` undoes it.

## 14. HT-3 "never sent over HTTP" cannot pass on `localhost` (medium)

**Units.** U2 (HT-3 test) against PRD FR-24 ("Session cookies are Secure and HttpOnly, and are never sent over HTTP").

**How each obeys.** AD-27's README note says that browsers still send `Secure` cookies to `http://localhost`, and that the redirect listener ignores them. The PRD bullet is absolute.

**Incompatibility.**
- **A browser test fails.** Story A writes HT-3 as a Playwright test: obtain a cookie over HTTPS, request `http://localhost:8000`, and assert that no cookie was sent. Chromium treats `localhost` as a secure context and sends the cookie, so the test fails.
- **A header test passes.** Story B asserts only the `Set-Cookie` attributes and passes.

The exam evidence (SC9) then depends on which story is written.

**Severity: medium.**

**Closing wording (AD-27, Tests):**
> **What HT-3 asserts:**
> - with HTTPS on, every `Set-Cookie` has `Secure`, `HttpOnly`, `SameSite=Strict` and `Path=/`;
> - the redirect listener answers byte for byte the same with and without a `Cookie` header, reads none and sets none.
>
> **README:** the README and the security section state the `localhost` exception as a deviation from FR-24's wording. On a real host, `Secure` cookies are never sent over HTTP. Lisa confirms the deviation note in PRD addendum H.

## 15. No canonical origin (medium)

**Units.** U1 (the certificate covers `localhost`, `127.0.0.1` and `::1`), U2 (the cookie), the AD-8 CSRF check and U12.

**How each obeys.**
- **AD-8:** "every state-changing request must be same-origin". It does not say against what.
- **AD-22:** the base URL defaults to `https://localhost:8443`.
- **AD-27:** the certificate also names `127.0.0.1` and `::1`.

**Incompatibility.** A Guest at `https://127.0.0.1:8443` gets a valid TLS page and a separate cookie jar, because cookies are per host.
- **Story A** checks `Origin` against the base URL, so every POST is refused there and the page looks broken.
- **Story B** checks `Origin` against the request's `Host` header, so it accepts both hosts. The Guest's emails still point at `localhost`, so the session holding the Manage grant is a different one.
- **Tests** pass under either check.

**Severity: medium.**

**Closing wording (AD-27, Listeners; AD-8, CSRF):**
> **One origin:** the base URL's origin is the platform's only origin. The HTTPS app answers any request whose `Host` is not the base URL's host and port with `308` to the base URL plus the same path and query. That is why the certificate keeps `127.0.0.1` and `::1`.
>
> **CSRF check:** AD-8's same-origin test compares the `Origin` header with the base URL's origin. When `Origin` is absent, the request needs `Sec-Fetch-Site: same-origin`. The check never compares with `Host`.

## 16. The Manage page read: missing time facts, possible secret exposure (medium)

**Units.** U3 (`GET /api/manage/{reference}`) and U11 (Manage page). EXPERIENCE.md leaves "Manage page after a Voucher: what remains shown" open (item 19).

**How each obeys.**
- **AD-28:** "Loading a Manage page never changes anything".
- **AD-16:** time facts are sent "so the SPA never computes them", but are named only for listings.
- **FR-17:** a Guest sees an email only on the page of the action that sent it.

**Incompatibility.**
- **Time facts.** U11 needs to know whether Changes are still allowed, and the Cutoff time, to show or grey out actions. The GET does not provide them, so the SPA would compute `start − cutoff` with the browser clock, which AD-4 forbids.
- **Secrets on reload.** To answer UX item 19, one story returns "your Voucher" on the GET, with its code read from the Outbox. Anyone holding a forwarded link then sees a spendable code on every reload.

**Severity: medium.**

**Closing wording (AD-28, Access; AD-16, Time facts):**
> **What the GET returns:** `GET /api/manage/{reference}` returns the AD-23 serializer plus `version`, `change_allowed` (from `change_allowed(booking_id)`), `cutoff_at`, `window_ended` and the history entries (action, `at`, Seats, Windows, Saunas, remedy, and `code_last4` and `value_ore` of any Voucher).
>
> **What it never returns:** an Outbox body, a Voucher code or a Manage link. Those appear only in the response of the action that created them (FR-17, AD-12).

## 17. Headers on every response (low)

**Units.** U2 (middleware in `app.py`) and the HT-2 test. U3 (the addendum's Manage hardening).

**Incompatibility.**
- **Error responses.** Starlette's `ServerErrorMiddleware` sits outside user middleware, so an unhandled 500 carries neither HSTS nor `Referrer-Policy`. Neither do uvicorn's own protocol errors. HT-2 says every HTTPS response.
- **Caching.** `/api/manage/*` and confirmation responses that hold Manage links or Voucher codes carry no `Cache-Control`.
- **`noindex`.** The addendum's `noindex` is missing.

**Closing wording (AD-27, Headers):**
> **How the headers are added:** they come from a pure ASGI wrapper that `main()` places around the whole app, outside `ServerErrorMiddleware`, or from uvicorn's `headers=` option. Every response then carries them, error responses included.
>
> **The headers:**
> - `Strict-Transport-Security` when HTTPS is on;
> - `Referrer-Policy: no-referrer`;
> - `Cache-Control: no-store` on every `/api/` response;
> - `X-Robots-Tag: noindex` on `/manage*` and `/api/manage/*`.
>
> **Test:** HT-2 asserts them on a 200, a 404 envelope and a static asset.

## 18. The redirect listener (low)

**Units.** U1's redirect app and AD-22.

**Incompatibility.**
- **Decoded path.** If the listener builds `Location` from the decoded `scope["path"]`, `%0D%0A` becomes CR LF in a header, so h11 raises and answers 500. Non-ASCII bytes do the same.
- **Port mismatch.** `BP_HTTPS_PORT=9443` with the default base URL still redirects to `:8443`.
- **One server failing.** If the app's lifespan fails (a migration error), the HTTPS server exits while the redirect server keeps sending 308s to a dead port.

**Closing wording (AD-27, Listeners; AD-22):**
> **Location:** the redirect app builds `Location` from the base URL and the request's raw `raw_path` and `query_string` bytes, never decoded. A target with CR, LF or bytes outside visible ASCII gets `400` with no `Location`.
>
> **Base URL:** `config` derives the default base URL from `BP_HTTPS_PORT`. It refuses to start when `BP_HTTPS` is on and the base URL is not `https://`, or its host is not a certificate name.
>
> **Shutdown:** `main()` stops both servers when either one exits, and exits non-zero if either failed.

## 19. Voucher expiry edges (low)

**Units.** U5 and U7 (issue), U6 (spend), the emails, and PRD FR-27, FR-28 and FR-33.

**Incompatibility.**
- **Printed date vs stored instant.** `expires_at = app_now() + 1 year` is an instant, such as 14:37. The email prints a date. A Guest who uses the code at 18:00 on the printed date is refused.
- **Refund Voucher born expired.** A refund Voucher takes "the earliest `expires_at` of the Vouchers used" (FR-28 assumption). If that Voucher expired between booking and cancellation, the refund is issued already expired, and the value is lost.
- **Voucher remedy extends expiry.** The FR-33 voucher remedy issues a new 1-year Voucher for the whole `total_ore`, including a part funded by a nearly expired Voucher. Book and cancel then extends any Voucher indefinitely.

The last two need a product decision.

**Closing wording (AD-30, Issue; questions for Lisa):**
> **Expiry is a Venue date:** `expires_at = ((venue_date(app_now()) + interval '1 year')::date + 1)::timestamp AT TIME ZONE settings.venue_tz`. That is the end of the Venue date one year after issue, exclusive. Emails print that last valid Venue date.
>
> **Refund floor [Lisa]:** `refund()` never issues a Voucher whose `expires_at` is earlier than `app_now() + interval '30 days'`.
>
> **Remedy expiry [Lisa]:** the voucher remedy's 1-year validity covers the card-funded part only. The Voucher-funded part keeps the earliest expiry, as in `refund()`.

## 20. Session creation and sign-out vs Manage access (low)

**Units.** U3 (`POST /api/manage/open` "creates or reuses the session"), the Core session story (AD-8 Creation: "No other page load creates a session") and the privacy notice (FR-21: the cookie "is set when a Guest opens Book seats or an Administrator opens Sign-in").

**Incompatibility.**
- **Cookie test.** A Core e2e test written to AD-8 asserts that only two pages set a cookie. U3 adds a third.
- **Privacy notice.** The FR-21 sentence in the privacy notice becomes inaccurate.
- **Sign-out.** AD-8 sign-out deletes the row, so an Administrator who opened a Guest's link at Reception loses that grant at sign-out. The addendum token table calls the two "separate".

**Closing wording (AD-8, Creation and Sign-out):**
> **Creation:** add `POST /api/manage/open` (AD-28) as the third moment that creates a session. The privacy notice and FR-21's sentence list it. [PRD wording, Lisa]
>
> **Sign-out:** sign-out deletes the row and its grants. The Guest opens the Manage link again. "Separate" in the addendum means that role and grant never imply each other.

## 21. Bookings made before If-time 2 have no Manage link (low)

**Units.** U3 (`issue()` runs only at creation) and AD-18 (sample Bookings created once under fixed keys, after which a rerun is a no-op).

**Incompatibility.** On the examiner's or Lisa's existing database, the sample Bookings and every Booking made before the §4.8 migration never get a token. The FR-25 demo then needs a new Booking, and nothing says so.

**Closing wording (AD-28, Issue):**
> No token is issued retroactively. The README says that a demo of §4.8 needs either a new Booking or a fresh database (`docker compose down -v`), so that the seed recreates the sample Bookings with Manage links.

## 22. `access_tokens` and `manage_grants` housekeeping (low)

**Units.** U3, and later FR-34.

**Incompatibility.**
- **Concurrent issues.** Two concurrent `issue()` calls for one Booking (a double resend in FR-34) both revoke the old token. Each then inserts, because neither sees the other's insert. The second insert hits the partial unique index: 23505, unmapped, a 500.
- **Grant pile-up.** Every `open` inserts another grant row.

**Closing wording (AD-28, Storage and Issue):**
> **Serialised issues:** `issue()` first locks the Booking row `FOR NO KEY UPDATE` (after `lock_windows` when the action has one), then revokes and inserts, so issues for one Booking run one at a time.
>
> **Grants:** `manage_grants` has UNIQUE `(session_id, token_id)`, and `open` upserts.
>
> **Purge:** startup purges grants of expired sessions and of tokens whose Booking's Window has ended.

## 23. The test server under HTTPS (low)

**Units.** U12 (the fixture starts `uv run booking-platform` with its own `BP_CERT_DIR`) and U1.

**Incompatibility.**
- **Ports.** The fixture keeps the default ports. It collides with an examiner or dev server already running, and its Outbox links point at `:8443`, not at the test server, so HT-4 passes for the wrong reason.
- **`ca.pem` race.** The client reads `ca.pem` before the subprocess has written it.

**Closing wording (AD-27, Tests):**
> **Ports and base URL:** the fixture picks two free ports and sets `BP_HTTPS_PORT`, `BP_HTTP_PORT`, the base URL and `BP_CERT_DIR`.
>
> **Certificate first:** it calls `tls.ensure(cert_dir)` itself before starting the subprocess. This is the one exception to "only from `main()`". It then waits for `/api/health` over TLS.
>
> **HT-4:** HT-4 asserts that the links start with the test base URL.

---

## PRD check (§4.7, §4.8, FR-16, FR-20, FR-21, FR-33, addendum token table)

| PRD consequence | Spine | Status |
| --- | --- | --- |
| FR-24: plain HTTP redirected, nothing returned or changed | AD-27 redirect listener | met; edges in 18, browser demo in 12 |
| FR-24: every HTTPS response carries STS | AD-27 middleware | gap: error responses (17) |
| FR-24: cookies Secure, HttpOnly, never sent over HTTP | AD-8, AD-27 | "never sent" not provable on `localhost` (14) |
| FR-24: every email link starts with `https://` | AD-12 | met; test base URL (23) |
| FR-25: ≥128 bits, hash only | AD-28 (256 bits) | met |
| FR-25: shows the Booking until the Window ends; Changes only before the Cutoff | AD-28 Validity, AD-4 | met; grant cap after a move (6); no Cutoff fact for the page (16) |
| FR-25: invalid, expired or replaced = never existed | AD-28, AD-16 `404 not_found` | met; wrong-kind routes also 404 (9) |
| FR-25: a new link stops the old | `issue()` revokes | met; concurrency (22) |
| FR-25: no third-party resources, no referrer | AD-17, AD-27 | met; `noindex` missing (17) |
| FR-25: explicit confirming action; one-time key returns first outcome | AD-9, AD-28 | shape gaps (3, 4, 5) |
| FR-26: atomic; original untouched on refusal | AD-3, AD-29 | met; stale requests (2) |
| FR-26: split gets own reference and link; original keeps its link | AD-20, AD-28, AD-29 | met for the split-off Booking; at risk from the Change email (1) |
| FR-26: both keep price per Seat and Cutoff | AD-4, AD-29 | met |
| FR-26: target inside horizon, before deadline | AD-29 order | met |
| FR-26 and §7: every move emails a confirmation with the Manage link | AD-12, AD-29 | **cannot be met as written** (1) |
| FR-27: Voucher = price paid; emailed with code, value, expiry; no money | AD-29, AD-30 | met; expiry date vs instant (19); ledger (10) |
| FR-28: partial use, rest by card; remainder stays | AD-30, AD-13 | met; no quote for the Review page (11) |
| FR-28: same message for expired, used-up, unknown | AD-16 `voucher_invalid` | met; order among refusals (11) |
| FR-28: two simultaneous uses never overspend | AD-30 conditional UPDATE | met under READ COMMITTED (7) |
| FR-28: refund returns each part the way it was paid | AD-31 | met for v1 Whole-sauna bookings; ledger contradiction (10); born-expired Voucher (19) |
| FR-16: status, history entry, cancellation time, cause and remedy | AD-29 | met; history shape (8) |
| FR-20: RB-4 guessed links, RB-5 own link only | AD-28 router | met |
| FR-21: retention after the last Voucher expires | `vouchers.booking_id` | met |
| FR-21: cookie only on Book seats or Sign-in | AD-8 | third moment from AD-28 not listed (20) |
| FR-21: tokens never in logs | AD-19, fragment | met |
| FR-33: refund or Voucher valid one year; capacity restored; Administrator sees it | AD-31, AD-23 | met; per-kind route (9); remedy expiry question (19) |
| FR-33: move to unavailable Sauna or other price refused; email per Change | AD-23, AD-24 | met; email link (1) |
| Addendum: Manage link valid until the Window ends; split-off link likewise | AD-28 Validity | met |
| Addendum: session after first load, lifetime set by the architecture, revoked by expiry or a new link | AD-28 Grant (30 min sliding, void on revoke) | met; sliding mechanics (6) |
| Addendum: Administrator session separate from the Manage session, both in one browser | AD-8 Manage access | met; sign-out cascades the grants (20) |
| Addendum: token stripped with `replaceState`; GET only shows | AD-28 Open, Access | met |

## Not holes (checked)

- **Voucher writes and Window locks.** Voucher rows are written only after `lock_windows`. `refund()` and `issue()` only insert. The FKs `payments.voucher_id` and `vouchers.booking_id` take KEY SHARE locks, which never conflict with a balance UPDATE (NO KEY UPDATE). No cycle with Window locks.
- **Voucher spend vs refund of a Booking paid with that Voucher.** The refund issues a new Voucher and never updates the spent row, so the two share no row.
- **Opposite cross-Window Changes, and a split against a Whole-sauna booking.** `lock_windows` sorts by id, so both lock sets are taken in one order.
- **Split plus cancel.** Whole-sauna bookings never split. A split and "all Seats for a Voucher" on one Seat booking serialise on the source Window, and their outcome is fixed by finding 2.
- **Grant vs token revocation.** In the planned v1 nothing revokes a token after its Booking is created (FR-34 is not planned), and finding 6's in-transaction re-check covers FR-34 later.
- **The fragment across the 308.** A fragment never reaches the server. Browsers carry it over a redirect whose `Location` has none.
- **Link scanners that run JavaScript.** They only create a grant on their own session. The token is not single-use, so a scanner does not consume it.
- **No grant vs no Booking.** Both come from the same router dependency as `404 not_found`. FastAPI solves router dependencies before body validation, and malformed JSON is 422 for both, so there is no existence oracle.
- **80-bit Voucher codes.** Online guessing is infeasible without a throttle. The unsalted hash and `code_last4` leave 60 bits even if the database leaks.
- **A Seat refund through the API.** It is blocked by AD-29's CHECK and, with finding 9, by the routes.
