# Addendum: Saunalöyly Booking Platform PRD

Supporting material that does not belong in `prd.md`. Audit and decision history lives in `.memlog.md`, not here. The brief addendum (`.docs/planning-artifacts/briefs/brief-booking-platform-2026-09-20/addendum.md`) remains the home of the full rule tables and test tables (concurrency, validation, passwords, access, HTTPS).

## A. Technical choices carried to architecture
- **Atomic check-and-reserve.** One short transaction per write; conditional update; locks taken in fixed ascending order; bounded retry on serialization failure or deadlock; the database clock is the only clock. PostgreSQL: Read Committed with a conditional update, Serializable as backstop. SQLite: `BEGIN IMMEDIATE` around check-place-move, with busy timeout and bounded retry. Confidence high for the mechanisms, unknown for the chosen engine; re-check once a version is picked. *(Concurrency research.)*
- **Holds are data, not locks.** A row with `expires_at`, ignored after expiry even if cleanup has not run; optional sweeper. Never hold a lock across payment. Payment confirmations are idempotent, and the handler re-validates the Hold inside a transaction. The sweeper interval (30 s) is an example, not a measurement.
- **Derived placement (recommended, not decided).** Store seats booked per Window plus private bookings and Blocks; compute placement on read. Remove `sauna_id` per Seat; keep `sauna_id` on Blocks and private bookings; one capacity function from v1; a nullable "placed in sauna" column only if one-sauna access is built in step 2. Prove the formula with model-based tests (random sequences of bookings, cancellations, Blocks; check INV-1 to INV-5 after every step; compare with a brute-force reference). Confidence low-to-medium; no practitioner source.
- **Capacity formula (inference).** Seats shown = Σ Capacity of Saunas neither privately booked nor Blocked − Seats booked. A private booking of Sauna S is allowed if S is free and Seats(W) ≤ P(S), the summed Capacity of Saunas before S in the Fill order, excluding booked and Blocked ones.
- **Test approach.** Run group C of the capacity catalogue as parallel tests; group H as acceptance criteria for SC6; group G (indivisible groups) only if one-sauna access is built; group I (heating) only in Vision.
- **Simulated lock.** Rejects a duplicate PIN on a door; models per door whether codes are online (replaceable) or offline (not); states pending/set/failed; deletes expired codes; sends the venue time zone explicitly. Hour-resolution locks can stretch the H6 overlap beyond 20 minutes.

## B. Decisions the PRD took from research, with the alternative
| Topic | PRD position | Alternative |
|---|---|---|
| Placement after send time (one-sauna access) | Frozen at send time (replaces "moves any time" in the brief addendum) | Allow moves, issue a new code per move |
| Private booking after codes are sent | Refused while Seat holders hold the code (H12) | Accept and rely on "do not use" emails |
| Overlapping codes (H6) | Accept and state it; codes must differ | Start validity at Window start |
| Capacity decrease (F1) | Refuse while a future Window would overflow | Treat as overbooking |
| Lifting a Block (D7) | Move Seats back so INV-5 holds | Leave Seats in place |

## C. Comparable services (web research, 2026-10-29; mostly vendor marketing, verify before citing)
- Badstuvogna (Oslo): about NOK 250 per person drop-in; about NOK 1,250 for a whole sauna (6 people, 90 min) — from classified ads.
- Eggedal Badstue and Periode: drop-in and private in one calendar with shared capacity; Vipps/card at booking; one-time SMS code valid only in the booking window.
- Oslo Badstuforening has a member proposal to limit private rental because it displaces shared use (outcome unknown). Relevant to the Seat vs private balance; not modelled in v1.
- Allas Sea Pool (Helsinki): tiered cancellation — free at 10+ days, half at 5 days, full later. Not adopted; the brief's 12 h / 72 h Cutoffs stand.
- Wild Sauna: spot checks and NOK 2,000 fee without valid booking (door-code context).
- UX: show total price early; allow guest checkout; grey out unavailable times and suggest the next free one; time buttons rather than native pickers; show "X seats left"; sticky call-to-action (+4.2% in one source).
- Not found: Löyly's official terms, Norwegian official safety/age rules, no-show statistics. Age rules vary by venue (adult required under 6, 16 or 18). Sessions of 10–20 minutes recommended; alcohol banned everywhere.

## D. Rejected or replaced alternatives
- Lookup by reference + email (dropped 2026-10-29): the Manage link is the only way in.
- Simulated refund first for Seats (dropped): Seats get change or Voucher only.
- "Mobile first" (replaced by laptop first); "desktop" as a layout level (removed).
- Age-differentiated pricing, membership, period cards, remote control, heating (moved to Vision on the teacher's advice).
- Stored placement per Seat (not recommended; see A).

## E. Source inconsistencies noticed
- `.logs/lisa-larsen/issues.md` line 28 still says "mobile and desktop are if-time"; brief and addendum now say laptop (core) and mobile (step 2, last).
- The brainstorm says "mobile first"; the brief says laptop first and wins.
