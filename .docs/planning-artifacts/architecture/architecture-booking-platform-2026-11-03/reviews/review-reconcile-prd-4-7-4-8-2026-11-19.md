# Review: ARCHITECTURE-SPINE.md (AD-27 to AD-31 and amendments) reconciled against PRD §4.8 and its cross-references

- **Spine:** `ARCHITECTURE-SPINE.md` (draft, working copy of 2026-11-19: AD-27 to AD-31 added; AD-4, AD-7, AD-8, AD-9, AD-12, AD-13, AD-16, AD-19, AD-22 amended). The spine was not edited.
- **Sources:** `prd.md` FR-24 to FR-28 and FR-33; the §4.8 parts of FR-16, FR-17, FR-20 (RB-4, RB-5) and FR-21 (retention after the last Voucher expires, cookies, logs, README security section); the §7 email rows for If-time 2 and 3; the glossary entries Manage link, Voucher, Change, Cutoff and Entry time. `addendum.md` §A token table and §K (HT-1 to HT-4, RB-4, RB-5). `appendix-fr-34-51.md` FR-34 and FR-39 where §4.8 points to them. `EXPERIENCE.md`: If-time Plug-in Points (Voucher field, Manage booking), Flow 4, open items 19 to 23.
- **Date:** 2026-11-19

## Verdict

**Mostly landed. Two high findings must be fixed before the If-time 2 stories are written.** The kernel is sound and traceable. It covers the token storage and the fragment-to-grant exchange (AD-28), the single history shape and the cancellation columns (AD-29), the conditional-update Voucher (AD-30), the single refund function (AD-31), the Change idempotency (AD-9) and the HTTPS listeners and headers (AD-27). Most of the quiet requirements are explicit: "same response", "no referrer", "nothing changed on page load", "freed seats count at once", "valid one year" and "earliest expiry".

The gaps cluster in one place: **what reaches the Guest by email or on the page**.
- The spine has no way to put the Manage link into a Change confirmation email, which §7 requires (H1).
- A refund that returns a Voucher has no defined channel for the new code. The code exists only at issue, so the value can be lost for good (H2).
- The Voucher field on Review has no way to show the reduced amount, and nothing stops the card amount charged from drifting from the Pay label (M1).
- The Manage page has no response contract with the server time facts it needs (M2).

Severity: **high** = the spine contradicts the PRD or claims coverage that it does not give, so a story built on the spine fails a PRD consequence. **Medium** = a testable consequence with no architectural home, where stories are likely to diverge. **Low** = a clarification, an internal spine inconsistency, a test obligation or a documentation duty.

Counts: **2 high, 4 medium, 9 low.**

## High

| # | PRD location | Missing or contradicted | Suggested spine fix |
|---|---|---|---|
| H1 | §7 email table, row "Confirmation of a Change (FR-26, FR-33): What changed, the new Window and Seats, **the Manage link**"; FR-26 "The original Booking keeps its reference **and link**"; addendum A token table, Manage link "Revoked by: a new Manage link for the same Booking (FR-34)" | AD-28 **Issue** runs only when a Booking is created (Seat flow, Whole-sauna flow, split, seed), and "the raw token exists afterwards only in the Outbox". When the Guest moves Seats, gives Seats up, or moves or cancels a Whole-sauna booking, `services` cannot rebuild the Booking's Manage link: only its hash is stored (FR-25). A story therefore has three choices: drop the link from the email (breaks §7); call `issue()` again (that revokes the link in the confirmation email, breaks "keeps its link" and the token table, and voids the acting session's own grant through AD-28's revocation join); or dig the token out of an earlier Outbox body (couples `services` to email text, and breaks after retention). The spine does not choose, and every option conflicts with some PRD text. | Decide with Lisa and record the decision in AD-28 and AD-29. **Recommended (B):** a Change email names the reference and says "use the Manage link in your booking confirmation". Amend the §7 row to match; the split-off email still carries its own new link. This keeps one stable link per Booking, as FR-26 and the token table say. **Alternative (A):** every Change email carries a new link from `issue()`, and the previous link stops working. The acting session is re-granted on the new token in the same transaction, and addendum A's "Revoked by" column adds "a Change email". Either way, add one test: after a Change, the link in the Change email (A), or the link in the original confirmation (B), still opens the Booking. |
| H2 | FR-28 "When a Booking paid partly with a Voucher is cancelled and the Guest chooses a refund … the Voucher part as a new Voucher with the earliest expiry date"; §7 row "Voucher (FR-27, FR-28, FR-42): Code, value, expiry date"; FR-33 "Every cancellation … sends a confirmation email" | AD-31 `refund(c, booking_id)` issues a new Voucher for the Voucher-funded part. Nothing says that it returns the raw code. The Deferred entry adds that `refund()` "keeps its signature". AD-30 stores only the hash and the last four characters, so the issuing call is the only moment the code exists in clear. AD-31 FR-33 also lists the email as "naming the refund **or** the Voucher code". A refund of a mixed-funded Booking needs both: the card refund **and** the returned Voucher's code, value and expiry date. Read literally, the refund email of a part-Voucher Booking carries no code, and that value can never be spent again. This also breaks AD-30 "Never money" in spirit: the value is not refunded, it is simply gone. | AD-31: `refund()` returns `{card_ore, voucher: {id, code, value_ore, expires_at} \| None}`, and its signature is fixed in that form now (amend the Deferred sentence). FR-33 email wording: "the card refund, if any, **and** the code, value and expiry date of every Voucher issued". Add a test: cancel a Whole-sauna booking paid partly by Voucher, with remedy `refund`. The email in the response holds a code, and that code spends with the earliest expiry. |

## Medium

| # | PRD location | Missing or contradicted | Suggested spine fix |
|---|---|---|---|
| M1 | FR-28 "A Voucher can pay for all or part of a Booking, and the rest is paid by Simulated payment"; FR-6 "The pay button states both the obligation and the amount"; FR-3 "The total shown … is the amount charged"; UX Voucher field "Reduces the amount and updates the Pay label … one identical refusal as a Field error"; UX open item 23 ("Pay NOK 0") | **No read path, and no guard on the charged amount.** The SPA must show the card amount before Pay. The spine offers no way to check a code and learn its usable value, so the SPA can only submit the booking and see what happens. AD-30 also plans the Voucher part as `min(balance, total)` from a balance read **at submit time**. If the Voucher was partly spent elsewhere between Review and Pay, the card is charged more than the Pay label said, with no refusal. AD-9's "same request" comparison (`kind`, `window_id`, `seats`/`sauna_id`) ignores the Voucher, so a retry with another code returns the first outcome silently (acceptable, but unstated). | Add a read-only `POST /api/vouchers/check {code}`. It returns `{usable_ore, expires_at}` (a Venue date) or `409 voucher_invalid`, the same for every non-match. POST keeps the code in the body (AD-19), and the call writes nothing (AD-4). The booking request carries `voucher_code` and the `voucher_part_ore` the page showed. After the lock, `services` refuses `voucher_invalid` (or a new `amount_changed` with the current `usable_ore`) when its own plan differs, so the card amount charged always equals the Pay label. State that a Voucher covering the whole total gives `card_ore = 0`, which the SPA labels (UX item 23). |
| M2 | FR-25 "The link shows the Booking until its Window ends. Changes are possible only before the Cutoff"; FR-26 and FR-33 "After the Cutoff, every Change is refused with an explanation"; UX Manage booking "Shows the Booking and the Changes allowed"; UX Flow 4 step 3 (confirming step shows "a Voucher worth NOK 250, valid for one year, no money back"); AD-4 (no browser clock), AD-16 Time facts | **The Manage page has no response contract.** AD-23's serializer gives `kind, seats, sauna, window, total_ore, status`. Nothing gives the facts that the Manage page needs: whether Changes are still allowed (`change_allowed(booking_id)`), the Cutoff moment (`cutoff_at`), which actions this kind allows, `price_per_seat_ore` for the Voucher value in the confirming step, or the Booking's history. Without them a story will compute "before the Cutoff" in the SPA with the browser clock (forbidden by AD-4), or compute money in the SPA. The `cutoff_passed` refusal also has no listed facts for the "reason" copy (UX item 22). | Add to AD-28: `GET /api/manage/{reference}` returns the AD-23 serializer plus `reference`, `change_allowed`, `cutoff_at`, `window_end`, `actions` (`move`, `voucher` for Seats; `move`, `cancel` for whole), `price_per_seat_ore`, and `history[]` (from `booking_changes`). All come from the AD-4 predicates. `cutoff_passed` carries `cutoff_at`. One line, for NFR-9 and §6 tone: the SPA shows the Cutoff as a fixed time, never as a countdown. |
| M3 | FR-25 "Confirming twice (double click or retry) applies the Change once and returns the first outcome"; FR-17 (the result page shows the email that was sent) | AD-9 puts the key check first after `lock_windows`. AD-29 **Order of checks** then lists "the Booking is active (`booking_cancelled`) … `cutoff_passed` …" with no key check in front. A story that follows AD-29 turns the second click of "give up all Seats", of a Whole-sauna cancel, or of any Change pressed just over the Cutoff into `booking_cancelled` or `cutoff_passed` instead of the first outcome. Separately, "a repeat rebuilds the response from the `booking_changes` row", but that row has no link to the Outbox email(s) it sent. A Booking has several emails (confirmation, earlier Changes), so the repeat cannot reliably return the same email. | AD-29 Order of checks: start with "the key check (AD-9); a known key returns the first outcome before any other check". Add `outbox_emails.change_id` (or `booking_changes.email_ids`) so that a repeat returns exactly the emails the Change sent, including the split-off Booking's email. Add a test: double-submit "give up all Seats" and get two identical 200 responses, one Voucher and one history row. |
| M4 | §7 rows "Confirmation of a Change: What changed, the new Window and Seats, the Manage link"; "Split-off Booking: New Booking reference and its own Manage link"; "Voucher: Code, value, expiry date"; "Whole-sauna booking, cancellation or move: Sauna, Window, price, refund or Voucher"; FR-6 "every email that mentions a payment" carries "Simulated payment: no money moves"; FR-4 / FR-31 (no Sauna in Seat emails) | AD-29 says only "every Change sends its confirmation", and AD-12 "returns its emails". Nothing fixes **which** emails each Change sends or what they must contain: whether giving Seats up sends one combined email or a Change email plus a Voucher email; that the expiry date is a Venue date (AD-4); that a refund email carries the payment note; and that Seat Change emails never name a Sauna. AD-25's no-Sauna test walks "the Seat flow's responses and emails" and does not clearly include Manage responses and Change emails. | Add a small table to AD-29 with one row per action (move all, move some, Voucher some, Voucher all, whole move, whole cancel with refund, whole cancel with Voucher), giving the emails sent and the facts each must hold, as in §7, plus H1 and H2. Extend AD-25's walk to `/api/manage/` responses and Change emails for `kind = 'seats'`. |

## Low

| # | PRD location | Missing or contradicted | Suggested spine fix |
|---|---|---|---|
| L1 | FR-21 "The session cookie is set when a Guest opens Book seats or an Administrator opens Sign-in"; FR-21 privacy notice ("how long data is kept"); FR-21 README security section ("Manage-link tokens stored only as hashes … (the Outbox … holds the links as sent), whether HTTPS is in place"); UX open item 6 (the privacy text says the cookie is set on Book seats and Sign-in, retention is 12 months) | AD-8 **Creation** says "No other page load creates a session". AD-28 **Open** creates or reuses one, so the spine contradicts itself. The cookie is strictly needed, so no banner is required, but the privacy notice text will be wrong once §4.8 ships. It will also be wrong on retention (it must add "or until the last Voucher from the Booking expires"). Nothing in the spine assigns the README security section items either. | AD-8 Creation: add "and `POST /api/manage/open` (AD-28)". Add to the Capability map row FR-25 to FR-28 a documentation duty for the §4.8 epic: update the privacy notice (Manage cookie, Voucher retention) and the README security section (hashed Manage tokens, the Outbox holds links as sent, HTTPS from AD-27). |
| L2 | FR-25 "Loading a page alone never changes anything" | Covered for Bookings: AD-28 makes every Change a keyed POST. Inside the spine, though, AD-4 says "GET endpoints never write, with one exception (`ensure_generated`)", while AD-28's grant slides "on each use" and AD-8's sessions slide too, so both write on GET. A story will either break AD-4 or not slide, and a non-sliding grant expires 30 minutes after the Guest opened the link, in the middle of a Change. | Name a second AD-4 exception: "touching `expires_at` on `sessions` and `manage_grants` (no Window lock, no Booking row)". |
| L3 | FR-28 "An expired, used-up or unknown code is refused with the same message"; UX "one identical refusal as a Field error" | AD-30 normalises input, but nothing says what a malformed code (wrong length, a character outside Crockford base32) gets. A Pydantic shape rule would answer with `422 invalid_input`, a different response from `409 voucher_invalid` for the same "unknown" code. | AD-30: the code field accepts any string up to a fixed length (for example 64) at the shape level. Every code that does not match after normalisation is `voucher_invalid`. |
| L4 | FR-26 "move some or all Seats … to another Window that has room"; FR-27 "give up some or all Seats" | There is no refusal for a Seat count above the Booking's current Seats (a stale page or a second tab after a partial Change), and no rule for a move to the Booking's own Window. A 409 rule against the stored row is not a Pydantic shape error (AD-16). The move flow also needs a target listing; reusing `GET` Window listings with `seats = n` is implied but not stated. | Add a `seats_changed` code (facts: current `seats`) to AD-16, checked after the re-read. A target equal to the current `window_id` is `invalid_input`. State that the move picker reuses the public Window listing for `n` Seats (AD-5, AD-16 time facts). |
| L5 | FR-21 "deleted or anonymised 12 months after the Window, or after the last Voucher from the Booking expires if that is later" | Covered in substance: AD-30's `vouchers.booking_id` "which retention reads", plus AD-4's masking and catch-up. No predicate is named, although AD-4 wants one SQL function per time rule. It is also unstated that "the Window" means the Booking's current Window after a move, and that Vouchers returned by `refund()` count (their `booking_id` is the cancelled Booking). | Name `retention_due(booking_id)` = `app_now() >= greatest(upper(current window.during) + interval '12 months', max(vouchers.expires_at WHERE booking_id = …))`. The listing mask and the catch-up both call it. |
| L6 | FR-28 `[ASSUMPTION: a returned Voucher keeps the earliest expiry]`; FR-33 "a Voucher valid for one year" | The spine follows the PRD literally (AD-31), and two edge outcomes follow that Lisa should confirm. (a) A refund after the original Voucher has expired creates a Voucher that is expired at issue: the value is lost, and any later `CHECK (expires_at > issued_at)` would make `refund()` fail, though AD-31 says it cannot fail. (b) The remedy `voucher` on a part-Voucher Booking re-dates the Voucher-funded value to a full year, so booking and cancelling extends a Voucher. | Note both in AD-31, and forbid `CHECK expires_at > issued_at` on `vouchers`. Ask Lisa whether (a) should skip issuing and record the lost value, and whether (b) is intended. This is a PRD-level choice, not a spine defect. |
| L7 | FR-26 split (new Booking); AD-13 "payments rows record how the value was funded **and returned**" | The ER diagram has `bookings \|\|--\|{ payments` (at least one payment per Booking), but a split-off Booking has no `payments` row. AD-31's remedy `voucher` issues a Voucher of `total_ore` but says nothing about writing a `refund`/`voucher` payments row, so the audit shows a charge and never a return. | ER: `bookings \|\|--o{ payments`. AD-31: the `voucher` remedy also writes a `refund`/`voucher` row pointing at the new Voucher. |
| L8 | FR-28 "Two simultaneous uses of one Voucher never spend more than its value"; SM-2 "With §4.8: RB-4 for guessed links, and RB-5"; FR-25 "send no referrer"; FR-25 "Loading a page alone never changes anything" | These tests are not named. AD-27 names `test_fr24_https.py` for HT-1 to HT-4. Nothing names tests for the Voucher double spend (a parallel test against real PostgreSQL), for RB-4 (link and reference: unknown, revoked and expired give the same 404), for RB-5 (a grant for A gives 404 for B), for `Referrer-Policy: no-referrer` on `/manage`, or for "GET under `/api/manage/` changes no `bookings` row". | Add to the Tests convention: `test_fr25_manage.py` (RB-4, RB-5, no-referrer, read-only load), and a parallel Voucher double-spend test in `test_fr28_voucher.py` with FR-11's repetition count. |
| L9 | Addendum A token table, Manage session "When it ends, the Guest opens the link in the email again, and Changes already confirmed stay"; UX open item 21 (the Manage page after the end of the session) | AD-28 answers an expired grant with `404 not_found`, the same as a Booking that is not yours (correct under RB-4). So the SPA cannot tell the Guest "open the link in your email again" for that case only. UX item 21 is in effect decided by AD-28: after the Window ends, the token is invalid, so the page says "This page is not available." | Leave the copy to the story. The one 404 message on `/manage` should say for all cases "This page is not available. Open the link in your booking email again." Close UX item 21 with a pointer to AD-28. |

## Walk of every consequence in scope

Status: **Covered** = the spine fixes it (AD cited); **Story** = correctly left to a story, with no divergence risk the spine must close; **Gap** = see the finding.

### FR-24 HTTPS (HT-1 to HT-4)

| Consequence | Status |
|---|---|
| Plain HTTP is redirected; nothing is returned or changed over HTTP (HT-1) | Covered: AD-27 redirect-only listener, 308, reads no body or cookie, target from config |
| HSTS on every HTTPS response (HT-2) | Covered: AD-27 middleware, `BP_HSTS_MAX_AGE` (AD-22) |
| Session cookies Secure and HttpOnly, never sent over HTTP (HT-3) | Covered: AD-8, AD-27. The README notes that browsers still send `Secure` cookies to `http://localhost` and that the redirect listener ignores them (a correct reading of "never sent" for localhost) |
| Every email link starts with `https://` (HT-4) | Covered: AD-12 base URL, AD-22 default, AD-27 test reads the Outbox |

### FR-25 Manage link

| Consequence | Status |
|---|---|
| ≥128 random bits, hash only | Covered: AD-8 Link tokens, AD-28 (256 bits, SHA-256) |
| Shows the Booking until its Window ends; Changes only before the Cutoff | Covered: AD-28 Validity, AD-4 `change_allowed`. The facts the page needs are a Gap: **M2** |
| Invalid, expired or replaced link gets the same response as a link that never existed ("same response") | Covered: AD-28 Open (`404 not_found`), AD-16, AD-8 |
| A new link (§4.10) stops the old one | Covered: AD-28 Issue revokes, grant void by join; Deferred FR-34 |
| No third-party resources, no referrer ("no referrer") | Covered: AD-27 `Referrer-Policy: no-referrer` always, AD-17 no other origin, Styling self-hosted. Test: **L8** |
| Explicit confirming action; loading a page changes nothing ("nothing changed on page load") | Covered: AD-28 Access. Internal inconsistency about sliding: **L2** |
| One-time key per confirming action; a repeat returns the first outcome | Covered: AD-9 Changes. Check order and email rebuild: **M3** |
| Token never in a path, query or log | Covered: AD-12, AD-19, AD-28 (fragment, `replaceState`, POST body) |

### FR-26 Move Seats

| Consequence | Status |
|---|---|
| Atomic; the target lacks room, so nothing changes (E5) | Covered: AD-3 Booking-scoped lock of both Windows, AD-29, AD-2 store; `no_seat_free` with the target's `seats_left` (AD-16) |
| Some Seats split into a new Booking with its own reference and link, emailed and shown on the result page | Covered: AD-29 Seat move, AD-20, AD-28 (issue and grant at split), AD-12 (both emails returned) |
| Original keeps its reference and link; both keep the price per Seat and the Cutoff | Covered: AD-29, AD-4 `bookings.cutoff`. But "keeps its link" collides with the §7 Change email: **H1** |
| All Seats move the Booking and keep its reference | Covered: AD-29 (`UPDATE window_id`) |
| Target inside the horizon and before its deadline | Covered: AD-29 Order of checks, AD-24 order |
| No extra cost | Covered: AD-29 Value, AD-13 |
| Every move sends an email, shown on the result page | Covered: AD-29 Email, AD-12. Contents: **H1**, **M4** |
| Freed Seats count at once ("freed seats count at once"); the Administrator's list shows the Change | Covered: AD-5 (read from rows in the same transaction), AD-29 History read by FR-16 |
| After the Cutoff, every Change is refused with an explanation | Covered: `cutoff_passed` (AD-16, AD-29). Facts for the explanation: **M2** |
| Seat count above the current Seats; move to the same Window | Gap: **L4** |

### FR-27 Voucher instead of Seats

| Consequence | Status |
|---|---|
| Worth the price paid for the Seats given up | Covered: AD-29 (`seats × price_per_seat_ore`) |
| Emailed with code, value and an expiry one year after issue; the result page shows it ("Voucher valid one year") | Covered: AD-30 Issue (`app_now() + 1 year`), AD-12. Email contents: **M4** |
| Freed Seats count at once | Covered: AD-5, AD-29 |
| No money refunded | Covered: AD-29 CHECK (no `seats` + `guest` + `refund`), AD-30 Never money |
| All Seats given up cancels the Booking (`guest`, `voucher`) | Covered: AD-29. The page afterwards (UX item 19): Story |

### FR-28 Pay with a Voucher

| Consequence | Status |
|---|---|
| Pays all or part; the rest by card; the remainder stays until expiry | Covered: AD-30 Spend, AD-13. Read path and Pay label: **M1** |
| Expired, used-up or unknown get the same message ("same response"); never paid out | Covered: AD-16 `voucher_invalid`, AD-30. Malformed input: **L3** |
| Two simultaneous uses never overspend | Covered: AD-30 conditional UPDATE, CHECK, Lock order. Test: **L8** |
| Refund returns each part the way it was paid; the returned Voucher keeps the earliest expiry ("returned voucher keeps earliest expiry") | Covered in mechanism: AD-31. The code never reaches the Guest: **H2**. Edge outcomes: **L6** |
| One Voucher per Booking in v1 | Deliberate narrowing, in Deferred. PRD "Vouchers used" stays possible (AD-13 allows several rows) |

### FR-33 (Manage parts)

| Consequence | Status |
|---|---|
| Cancel with the choice of Simulated refund or a one-year Voucher; capacity restored; the Administrator sees it | Covered: AD-31 FR-33 cancel, AD-23 write order, AD-29 columns. Email with code: **H2** |
| Move refused where the Sauna is not available whole; original untouched | Covered: AD-23 Move, AD-24 |
| Move to a Sauna with another price refused with the reason | Covered: AD-23 Price (`price_differs`) |
| Every cancellation or move sends an email | Covered: AD-29, AD-31. Contents: **H1**, **M4** |
| After the 72 h Cutoff, refused | Covered: AD-4 per-Booking `cutoff`, `cutoff_passed` |

### FR-16, FR-17, FR-20, FR-21 (§4.8 parts)

| Consequence | Status |
|---|---|
| FR-16 status active/cancelled; Change as history (what, when, Voucher); cancelled with time, cause and choice; not counted | Covered: AD-7, AD-29 (`booking_changes`, cancellation columns), AD-23 Counting |
| FR-17 Outbox holds links as sent; hash rule applies to Booking data only | Covered: AD-12, AD-28 ("raw token only in the Outbox") |
| FR-17 Guest sees an email only on the result page of the action | Covered: AD-12 Guest read. Rebuild on repeat: **M3** |
| FR-20 RB-4 (guessed reference or link: same response) | Covered: AD-10, AD-28 Open and Access (`404 not_found`). Test: **L8** |
| FR-20 RB-5 (own link: that Booking only) | Covered: AD-28 per-Booking grant router. Test: **L8** |
| FR-20 Administrator role and grant independent | Covered: AD-8 Manage access |
| FR-21 retention extended to the last Voucher's expiry | Covered: AD-30 `booking_id`, AD-4. Predicate: **L5** |
| FR-21 cookies strictly needed; none on Landing | Covered: AD-8. The Manage open is a new set point: **L1** |
| FR-21 tokens never in logs | Covered: AD-19, AD-28 |
| FR-21 README security section / privacy notice | Gap (documentation duty): **L1** |

### §7 emails, If time 2 and 3

| Row | Status |
|---|---|
| Confirmation of a Change: what changed, new Window and Seats, **Manage link** | Gap: **H1**, **M4** |
| Split-off Booking: new reference and its own Manage link | Covered: AD-28 issue at split, AD-12 |
| Voucher: code, value, expiry date | Covered for FR-27 and the remedy `voucher`; Gap for a returned Voucher: **H2**. Contents: **M4** |
| Whole-sauna booking, cancellation or move: Sauna, Window, price, refund or Voucher | Partly: AD-23 Shape gives the facts; wording "or": **H2**, **M4** |
| Payment note in emails that mention a payment (FR-6) | Not stated for refund emails: **M4** |

### Glossary

| Term | Status |
|---|---|
| Manage link (long random token, the only way back without an account) | Covered: AD-28, AD-8 |
| Voucher (credit by email in place of money, from giving up Seats or by choice on cancellation, one year from issue) | Covered: AD-30, AD-31 (the returned Voucher keeps the earliest expiry, per FR-28) |
| Change (Seats: move or Voucher; whole: cancel or move; never Seats for money) | Covered: AD-29 `action` values, cancellation CHECK |
| Cutoff (12 h / 72 h, never under 2 h, kept per Booking) | Covered: AD-4 (`cutoff` column, `CHECK >= 2 hours`, `change_allowed`) |
| Entry time (creation, or the moving Change; a partial move gives the new Booking the time of the move; the original keeps its own) | Covered: AD-7, AD-29 Seat move; whole move unchanged (AD-23) |

### UX Manage and Voucher flows (EXPERIENCE.md)

| Item | Status |
|---|---|
| Manage booking shows the Booking and the Changes allowed | Gap: **M2** |
| Confirming step ("Nothing has changed yet"), Voucher value shown before confirming | Covered in principle (AD-28 POST only); value fact: **M2** |
| Result page with "Sent by email:" | Covered: AD-12. Repeat: **M3** |
| Partial move shows the new reference and email | Covered: AD-12 split |
| "This page is not available." for an invalid, expired or replaced link | Covered: AD-28 `404 not_found` |
| After the Cutoff the page shows the Booking and refuses with the reason | Gap: **M2** (fact); wording is a Story (UX item 22) |
| Voucher field on Review reduces the amount, updates Pay, one identical refusal | Gap: **M1**, **L3** |
| Tone: calm, no urgency (§6, NFR-9) | Story, with the one spine guard in **M2** (no countdown to the Cutoff) |
| Open items 19, 20, 22, 23 | Story (designer); 23 depends on **M1** |
| Open item 21 | Decided by AD-28: **L9** |

## Correctly left to stories (no divergence risk found)

- Page copy for the Manage page, the confirming steps, the Cutoff reason and `booking_cancelled` (AD-16 Copy, UX Voice and Tone).
- The Manage page after all Seats were given up, or after a Venue cancellation (UX items 19 and 20). AD-28 keeps the link valid regardless of status, and the serializer carries `status`.
- The SPA routes `/manage` and `/manage/:reference`, and `draft:change:<reference>` in `sessionStorage` (AD-28, AD-9).
- The Terms switch from "A booking cannot be changed or refunded" (FR-5) to the per-kind §4.8 terms. AD-12 gives `content/terms-seats` and `terms-whole` a single home. The §4.8 story must change the text.
- Retention clearing of Outbox bodies that hold Manage tokens and Voucher codes (AD-12 Retention). It runs only after the last Voucher has expired.
