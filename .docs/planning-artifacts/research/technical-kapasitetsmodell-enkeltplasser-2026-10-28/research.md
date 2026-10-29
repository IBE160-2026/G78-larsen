---
title: 'technical research: seat placement capacity model for individual seats'
type: 'technical'
topic: 'seat placement capacity model (fill one sauna at a time, move seats from the last-filled sauna on cancellation)'
decision: 'Which rules and edge cases the PRD must state as examples (future acceptance criteria and tests) for seat placement, and whether the algorithm is worth building in the if-time track'
source: 'native run'
status: complete
claims_verified: 2
claims_unverified: 4
preset: 'quick'
validation: 'normal'
created: '2026-10-28'
updated: '2026-10-28'
---

# technical research: seat placement capacity model

**Decision this research serves:** Which rules and edge cases the PRD must state as examples (future acceptance criteria and tests) for seat placement, and whether the algorithm is worth building in the if-time track.

## Executive summary

**State the rules as invariants and worked examples, not as an algorithm. Seats are identical and splittable, so placement can be a pure function of counts; "move on cancel" then needs no move code.**

- **The algorithm is unusual, and comparable domains avoid it.** Hotels sell by room type and assign the physical room late, because fixing rooms at booking time causes unnecessary rejections [6][7]. A restaurant-table vendor never moves already-assigned tables [8]. No booking product using "keep the last unit free for whole-unit sale" was found.
- **Move-based repacking cannot fully prevent fragmentation in theory** [4][5], but that result concerns items that cannot be split. The brief lets seats split across saunas, so the fill is fully determined by the total seat count (inference, see Dimension 1).
- **Derived placement turns the hard rules into arithmetic (inference, not sourced).** A whole sauna S is bookable only if total seats ≤ the combined capacity of the non-blocked, non-whole saunas *before* S in fill order. Cancellation, unblock and whole-booking cancellation then restore the fill order automatically. This must be proven by a model-based test (Dimension 2).
- **Door codes (Success Criterion 6) need stored placement only with one-sauna access (group H).** In the default mode the codes follow from counts, blocks and whole bookings, so derived placement works. One-sauna access, and moves that trigger a new email, need the sauna of each booking stored. A later lock-behaviour run [11] adds: codes sent cannot be recalled on offline locks, so the rules should work without revoking (H12), and under one-sauna access placement should be frozen at the send time (H21).
- **Heating (vision) is helped by the fill order but makes placement visible (group I).** With seats compacted in fill order the fewest heaters run (I9, I10, INV-6); a stored placement without moves would heat more saunas. Three things stay open: guests move freely, so open saunas can be cold (I11, I12); late changes after the heating start need a rule (I13–I18); and in a started window the heater state must be remembered, since derived placement would switch off a heater guests may be using (I19).
- **The catalogue below (85 examples) is the deliverable.** The sharpest finds: overlapping time windows silently break per-window capacity (E1), a block can force bookings out (D3), unblocking or reordering needs an explicit rule (D7, F2), and a whole-sauna booking after the codes went out leaves seat bookers holding a valid code for that sauna (H12).
- **Biggest caveat:** no sauna, spa or fitness comparable was found, and the formula and all edge-case outcomes are derived from the project's own addendum, which is specification, not evidence.

## Dimension 1. Landscape: what this problem is, and what others do

- **Name and theory.** This is dynamic bin packing with bounded repacking ("migration factor") [4][5]. For items that cannot be split, no constant migration factor beats a 4/3 asymptotic ratio in the strip-packing variant [4] (high for that variant; transfer to saunas is inference), so bounded moves cannot guarantee zero fragmentation.
- **Why it mostly does not bite here.** Fragmentation comes from indivisible items. Individual seats are identical and may be split across saunas (the brief). With splittable seats, the first-fit fill in a fixed order puts `min(cap, remaining)` seats in each sauna, so placement is a function of the total (inference). It bites only if one-sauna access (step 2) forces a booking to stay together: then first-fit is order-dependent (example G1).
- **Hotels.** Assigning a room at booking time makes availability look smaller and causes rejections; sell by type and assign late [6]. An academic source agrees that committing rooms early causes unnecessary rejections, especially at high occupancy [7]. Moving a guest in-stay is "generally not in anyone's interest" [6] (single vendor blog, medium).
- **Restaurants.** aleno assigns by rules and never moves already-assigned tables automatically [8] (medium; one vendor).
- **Not found:** a booking product with a "keep the last unit free for whole-unit booking" rule; any two-source report of move cascades or surprised guests; documentation on blocks created after bookings exist.

## Dimension 2. Implementation: how to model it safely

- **Single-writer database makes the whole unit atomic.** In SQLite, `BEGIN IMMEDIATE` starts the write transaction up front and may fail with SQLITE_BUSY at that point; a deferred transaction that reads then writes can fail with SQLITE_BUSY on upgrade when another connection has modified the database; in WAL mode IMMEDIATE and EXCLUSIVE are the same [1] (high, re-fetched by the lead). Wrapping "check, place, move" in one `BEGIN IMMEDIATE` serializes writers (inference), with a busy timeout and a bounded retry for the loser.
- **PostgreSQL.** Serializable needs a whole-transaction retry on SQLSTATE 40001; the docs' write-skew example matches "two guests check the sauna is empty, then book different rows" [2] (high). Exclusion constraints forbid overlap between rows of the same kind per resource [3]; the cross-kind rule (whole booking vs seat group) is not covered by them (inference). Earlier locking and hold findings: see the prior concurrency run [10].
- **Store vs derive placement.** No practitioner source was found (open question). Reasoned position (inference): store only booked seats per window plus whole bookings and blocks; compute placement on read. Guests are never told their sauna and need no notice on moves (addendum), so stored placement has no observable meaning until one-sauna access exists in step 2. Heating (vision, group I) adds a second effect: which heaters run depends on placement, and in a started window the heater state must be stored (I19).
- **Derived rules (inference, to be proven by test).** Let `seats(W)` be total individual seats in window W, and `P(S)` the sum of capacities of saunas that precede S in fill order and are neither whole-booked nor blocked.
  - Free seats shown = Σ capacity of non-whole, non-blocked saunas − `seats(W)`.
  - Whole booking of S allowed iff S is not blocked, not whole-booked, and `seats(W) ≤ P(S)`.
  - Placement of seats = fill saunas in fill order, skipping whole-booked and blocked.
- **Fixed slots vs free windows.** With a venue-wide grid of fixed windows, "same window" is equality of a window id and a plain UNIQUE or partial-unique constraint works in both databases (inference, no source retrieved). Free overlapping windows need interval logic (see E1).
- **Test approach.** Model-based (stateful) testing generates action sequences and checks invariants after each step [9] (medium; mirror, snippet only). Worth using for this rule set because the examples below are sequences of bookings, cancellations and blocks. Invariants: INV-1 per sauna placed ≤ capacity; INV-2 Σ placed = Σ booked seats in the window; INV-3 a whole-booked sauna holds zero seats; INV-4 a blocked sauna holds zero seats; INV-5 compaction: no sauna earlier in fill order has free space while a later one holds seats (inference); INV-6 heating: the saunas heated for seats are the first k in fill order (skipping whole-booked and blocked) whose combined capacity covers `seats(W)`, so no heater runs without a booking except for overrides and carry-over between booked windows (follows from INV-5; inference); INV-7 in a started window no heater is switched off before its stop time (inference, I19).

## Edge-case catalogue (Given / When / Then)

Notation: saunas S1=7, S2=10, S3=12, S4=15 (total 44), fill order S1→S4, one window W unless stated. State is written `[S1,S2,S3,S4]` seats placed; `—` = whole-booked or blocked. "Basis": **add** = derived from the project addendum (spec, not evidence); **inf** = lead inference; **[n]** = source.

### A. Fill and move

| ID | Given | When | Then | Basis |
|---|---|---|---|---|
| A1 | empty | A books 5, then B books 4 | `[7,2,0,0]`; B is split 2+2; free seats shown 35 | add |
| A2 | `[7,10,5,0]` | a booking of 3 seats that sit in S1 cancels | `[7,10,2,0]`; 3 seats left S3, S1 is full again; free seats 25 | add |
| A3 | `[7,10,2,0]` | a booking of 2 seats that sit in S1 cancels | `[7,10,0,0]`; S3 is bookable whole at once | add |
| A4 | `[7,10,5,0]` | a booking of 2 seats that sit in S3 cancels | `[7,10,3,0]`; no seat moves | add |
| A5 | `[7,10,12,3]` | a booking of 5 seats that sit in S1 cancels | `[7,10,10,0]`; the moved seats come from S4 first, then S3 | add |
| A6 | 42 seats `[7,10,12,13]` | a guest books 3 | rejected as a whole; nothing placed; state unchanged | add |
| A7 | 44 seats | a guest books 1 | rejected, "no seat free" | add |
| A8 | `[7,10,5,0]` | a guest cancels 1 of their 4 seats (change) | capacity restored in W, compaction holds (INV-5) | add |

### B. Whole-sauna rules

| ID | Given | When | Then | Basis |
|---|---|---|---|---|
| B1 | `[7,10,3,0]` (20 seats) | whole S4 is booked | accepted (20 ≤ 29); free seats shown 29−20 = 9 | inf |
| B2 | `[7,10,3,0]` | whole S3 is requested | rejected: S3 holds seats. Seats cannot move to S4, because that breaks fill order (20 > 17) | add, inf |
| B3 | `[1,0,0,0]` | whole S1 is requested | rejected; S1 is bookable whole only at 0 seats | add |
| B4 | empty, S1 whole-booked | 38 seats requested | rejected: capacity is 37 (S2+S3+S4) | add |
| B5 | S2 whole-booked, empty | 9 seats are booked | `[7,—,2,0]`; fill skips S2 | add |
| B6 | `[7,—,12,4]` (23 seats) | the whole booking of S2 cancels | `[7,10,6,0]`; 10 seats move forward (4 from S4, 6 from S3) | add, inf |
| B7 | S4 whole-booked | a guest looks at W | free seats shown exclude S4 at once | add |

### C. Concurrency (parallel tests; the exact outcomes are the acceptance criteria)

| ID | Given | When (simultaneously) | Then | Basis |
|---|---|---|---|---|
| C1 | S4 free | two guests whole-book S4 | exactly one accepted; other told it is taken | add [1][2] |
| C2 | `[7,10,12,0]` | guest A books 1 seat; guest B whole-books S4 | one wins: either `[7,10,12,1]` and B rejected, or S4 whole-booked and A rejected; never both | add |
| C3 | `[7,10,2,0]` (19) | cancellation of 2 seats in S1; whole S3 requested | whole S3 accepted only after the move (`[7,10,0,0]`), else rejected; never a whole booking over a sauna with seats | add |
| C4 | `[7,10,12,4]` (33) | two cancellations of 3 seats each (one in S1, one in S2) | `[7,10,10,0]`; no seat moved twice, none lost (INV-2) | add |
| C5 | any | any interleaving of booking, cancel, whole booking | INV-1 to INV-5 hold after each completed request | inf |
| C6 | last seat in W free | block of S3 and a booking race | either booking first, then D2/D3 rules apply, or block first and booking judged on reduced capacity | add |

### D. Blocking

| ID | Given | When | Then | Basis |
|---|---|---|---|---|
| D1 | empty | S2 is blocked | capacity 34; free seats shown 34 | add |
| D2 | `[7,10,5,0]` (22) | S3 is blocked | seats move to `[7,10,—,5]` (to a later sauna is allowed here); no guest affected | add |
| D3 | `[7,10,12,10]` (39) | S3 is blocked | capacity 32, so 7 over; the latest booking loses and is refunded or given a voucher, whole bookings only (a 9-seat booking is cancelled in full → 30 seats); admin sees the list before confirming | add |
| D4 | S4 whole-booked | S4 is blocked | the guest gets refund or voucher regardless of cut-off | add |
| D5 | W1 15:00–16:30, W2 16:30–18:00, W0 14:00–16:00 | block 16:00–17:00 | W1 and W2 affected; W0 ends exactly at block start, so unaffected (half-open intervals) | add |
| D6 | seats booked in W | all saunas blocked | capacity 0; W not offered; every booking cancelled with refund or voucher | add |
| D7 | `[7,10,—,5]`, S3 blocked | block is lifted | open decision; recommended: invariant holds, seats move back to `[7,10,5,0]` | inf |
| D8 | `[7,10,3,0]` | admin marks S3 whole-booking-only in W | open decision; recommended: refused while S3 holds seats (or treated as a block) | inf |

### E. Several windows

| ID | Given | When | Then | Basis |
|---|---|---|---|---|
| E1 | W1 15:00–16:30 and W2 16:00–17:30 both exist | 7 seats are booked in each, both placed in S1 | 14 guests in a 7-seat sauna 16:00–16:30. The per-window model overcounts. Recommended: admin validation rejects partially overlapping windows in the venue | add, inf |
| E2 | W1 ends 16:30, W2 starts 16:30 | any booking | not overlapping; independent (half-open intervals) | inf |
| E3 | S3 given a different window length than other saunas | seats booked in W | pooled seat count breaks (S3 is in the pool for part of W only). Recommended: window lengths are venue-wide; per-sauna deviations are blocks | add, inf |
| E4 | `[7,10,2,0]` in W1, `[7,3,0,0]` in W2 | a booking in W1 cancels | W2 unchanged; moves never cross windows | add |
| E5 | W1 and W2 both nearly full | a guest changes 3 seats from W1 to W2 and W2 has 2 free | change rejected; W1 booking untouched; W1 capacity not restored (atomic) | add |
| E6 | whole S3 booked in W1 | seats are booked in W2 (separate window) | independent; the whole booking in W1 does not affect W2 | inf |

### F. Administrator changes

| ID | Given | When | Then | Basis |
|---|---|---|---|---|
| F1 | S2 has 10 seats placed | admin lowers S2 capacity to 6 | refused while any future window would exceed capacity (or handled like D3). Needs a decision | inf |
| F2 | `[7,10,3,0]` | admin reverses fill order | open decision; derived model gives `[0,0,5,15]` in future windows; recommended: apply to windows that have not started | inf |
| F3 | window already started | block or cancellation would move seats | open decision; recommended: no moves in started windows, use overbooking fallback (latest booking loses) | add, inf |

### G. Only if one-sauna access (step 2) is built

| ID | Given | When | Then | Basis |
|---|---|---|---|---|
| G1 | S1=7, S2=10, no-split. A=3 in S1, B=5 in S2 | C=6 books | first-fit rejects C (S1: 9>7, S2: 11>10) though a repack fits (C in S1, A+B = 8 in S2). State whether repacking is allowed. Once codes are sent, a repack is a move that triggers a new email (H20) | add, inf, [4] |

### H. Door codes (Success Criterion 6, step 2)

Notation: `K(Sn)` = the code(s) for the door(s) of Sn in window W. Unless stated: every sauna has a self-service lock, the email is sent 20 minutes before W starts, gradual opening and one-sauna access are off, and the codes are valid from the send time until W ends (addendum, Door codes). "Exactly the bookers who may use each door" means each Then also implies that nobody else gets that code.

H1–H18 depend only on counts, blocks, whole bookings and flags, so the derived model suffices (inference). H19–H23 need the sauna of each booking to be stored.

**H1–H7. Who gets which codes (default mode)**

| ID | Given | When | Then | Basis |
|---|---|---|---|---|
| H1 | empty W, no blocks. A books 5 seats | send time | A gets one email with K(S1) to K(S4), whichever saunas the 5 seats are placed in | add |
| H2 | S4 whole-booked by B. A has 5 seats | send time | B gets K(S4) only. A gets K(S1) to K(S3), never K(S4). Nobody else gets K(S4) | add |
| H3 | S2 blocked (no override), S3 whole-booking-only in W. A has seats | send time | A gets K(S1) and K(S4). No guest gets K(S2) or K(S3) | add |
| H4 | S3 blocked with the door-code override | send time | K(S3) is made and shown to the administrator; no guest gets it | add |
| H5 | S4 has no self-service lock. A has seats; B whole-booked S4 | send time | A gets K(S1) to K(S3). B gets no door-code email (S4 is B's only sauna) | add |
| H6 | W1 15:00–16:30 (A) and W2 16:30–18:00 (B), same doors | send times | A gets W1 codes, B gets W2 codes, never the other's. At 16:10 the same door has two valid codes, and B's code works while W1 is still in use. Open decision: accept, or start validity at window start. The two codes must differ: no lock vendor documents a rule against overlapping validity, none confirms it, and the only collision rule found is "same PIN twice". On locks with hour resolution the overlap is longer than 20 minutes. The simulated lock must reject a duplicate PIN on a door | add, inf, [11] |
| H7 | A has 4 seats in W, then cancels 1 (voucher or change) before the send time; C has 1 seat and cancels it | send time | A still gets one email; C gets none (no booking left) | add |

**H8–H11. Timing and the administrator's tools**

| ID | Given | When | Then | Basis |
|---|---|---|---|---|
| H8 | default send time; A booked 3 days ahead | W starts 15:00 | email at 14:40; codes valid 14:40–16:30 | add |
| H9 | administrator sets the send time to 60 minutes before; A books at 14:30 for a 15:00 window (or at 15:03, before the deadline) | booking confirmed | A gets the email at once, because the send time (14:00) has passed; codes valid until 16:30 | add |
| H10 | emails for W1 already sent; administrator changes the send time | change saved | open decision; recommended: applies only to windows whose email has not been sent; sent emails are not resent | inf |
| H11 | door D has source "administrator enters", no code set at the send time | send time passes, later the code is entered | administrator is alerted at the send time; the email goes out as soon as the code is in place on the lock (confirmed, not only accepted by the lock system, since codes can be accepted and still fail to program [11]); the code can be changed until the email is sent; "resend" sends the current code | add |

**H12–H15. Changes after the codes were sent (default mode)**

| ID | Given | When | Then | Basis |
|---|---|---|---|---|
| H12 | `[7,10,12,0]`, codes sent: A holds K(S1) to K(S4) | B whole-books S4 (0 seats there, so allowed) | gap: A holds a valid K(S4) for a sauna that is now B's. Open decision; recommended: after the send time, refuse a whole booking of S while seat bookers hold K(S) (in default mode, any seat booking in W). This works on every lock kind. Alternative: accept and replace K(S4) with a new code for B only, which cuts off A's old code; it works only for online codes, since offline (algorithmic) codes cannot be changed or revoked [11] | inf, [11] |
| H13 | `[7,10,5,0]`, codes sent: A holds K(S3) | S3 is blocked, seats move to S4 (D2) | A is unaffected in placement but holds K(S3) for a blocked sauna. Open decision; recommended: every seat booker of W gets a correction email naming the codes to use. Where the door's codes are online, also delete or replace K(S3) so the instruction is enforced; offline codes cannot be recalled, so mark per door whether its codes can be replaced [11] | inf, [11] |
| H14 | S3 blocked, codes sent without K(S3) | the block is lifted (D7) | S3 opens for individual seats after the send time, so the seat bookers get an extra email with K(S3) | add |
| H15 | codes sent; B (latest booking) loses to the overbooking fallback | fallback runs | B gets the apology email saying the codes must not be used and the refund notice. Other bookers' codes are unchanged. The code is shared, so the rule is a request, not enforced: replacing the door's code would cut off the whole group, so it is best effort and needs a resend to the others [11] | add, inf, [11] |

**H16–H18. Gradual opening (step 2)**

| ID | Given | When | Then | Basis |
|---|---|---|---|---|
| H16 | gradual opening on, maximum 4. A has 6 seats (S1 open, not full) | send time | A gets K(S1) only; unopened S2 to S4 give no codes. The open set follows from the seat count (inference) | add, inf |
| H17 | gradual opening on, codes sent with K(S1) only. S1 is full, then B books 1 seat | B confirmed | S2 opens. A (and every earlier seat booker of W) gets an extra email with K(S2). B, booking after the send time, gets K(S1) and K(S2) in one email at once | add |
| H18 | S2 open, codes sent with K(S2). Cancellations empty S2 | S2 closes and is free for whole booking | seat bookers still hold K(S2); same gap as H12 | add, inf |

**H19–H23. One-sauna access (step 2, needs stored placement)**

| ID | Given | When | Then | Basis |
|---|---|---|---|---|
| H19 | one-sauna access on, S1=7, S2=10. A books 3 (→ S1), B books 5 (→ S2: 3+5 > 7) | send time | A's email names S1 with K(S1) only; B's names S2 with K(S2) only. Neither gets the other's codes | add |
| H20 | as H19, codes sent | A cancels; B's whole booking moves S2 → S1 (5 ≤ 7) | B gets a new email naming S1 and K(S1). The extra email for newly opened saunas is not sent. The move is complete before S2 is bookable whole (A3, C3). This move happens before the send time only; see H21 | add |
| H21 | as H19, codes sent (after the send time, and also once W has started, F3) | a block or cancellation would move B | open decision; recommended: no move after the send time, use the overbooking fallback. A move after the send time needs a new code for B, and the old sauna's code is shared with others, so it cannot be taken from B alone; it would need replacing that door's code and resending it, which offline locks cannot do [11]. In a started window a move would also send people out of the sauna they are in. This is stricter than the addendum's "moves are allowed at any time" | inf, [11] |
| H22 | one-sauna access on, S1 has no self-service lock. A is placed in S1 | send time | A gets an email naming S1 without codes | add |
| H23 | one-sauna access off, a future window has a booking of 4 seats split 2+2 | administrator turns it on | open decision; recommended: refuse while any future window has a split booking. Turning it off applies only to windows whose email is not yet sent | inf |

### I. Heating (heater control, vision)

Notation: unless stated, every sauna has external heater control, heating starts 60 minutes before the window (14:00 for a window at 15:00–16:30) and stops at the window end, gradual opening and one-sauna access are off, and blocks have no heating override. These are example values; the addendum sets no defaults. "On: S1, S2" lists the heaters running for W. The rule under test (addendum, Heater and temperature control): a sauna is heated in a window only if it has at least one booking in that window. Everything below follows from that rule plus the placement rules. Heating is simulated and in the vision, so nothing here is v1.

The wanted heater set is a function of counts, blocks, whole bookings and flags (inference). The actual state (what is running now) must be recorded: the simulated platform already logs when heating would start and stop, and I13–I19 need that log.

**I1–I7. Which saunas are heated (default mode)**

| ID | Given | When | Then | Basis |
|---|---|---|---|---|
| I1 | empty W, no blocks. A books 5 seats | 14:00 | `[5,0,0,0]`. On: S1. S2 to S4 have no booking and are not heated | add |
| I2 | A books 9 seats | 14:00 | `[7,2,0,0]`. On: S1, S2 | add |
| I3 | S4 whole-booked by B. A has 3 seats | 14:00 | `[3,0,0,—]`. On: S1, S4. S2 and S3 are not heated | add |
| I4 | S2 has no external heater control. `[7,10,0,0]` | 14:00 | start and stop are recorded for S1 only. S2 is shown as "no external control", with no heating entry and no alert. Seats still fill S2 as normal | add |
| I5 | S3 blocked, no override. `[7,10,—,3]` (20 seats) | 14:00 | On: S1, S2, S4. S3 is not heated. With the heating override on the block, S3 is also heated as for a booked window, with no guest in it | add |
| I6 | S3 marked whole-booking-only in W, no whole booking. `[7,10,—,3]` | 14:00 | On: S1, S2, S4. S3 has no booking and is not heated | add |
| I7 | no booking in W | 14:00 | nothing starts; no heating entry for W | add |

**I8–I10. Compaction before heating starts (does the fill order save heaters?)**

| ID | Given | When | Then | Basis |
|---|---|---|---|---|
| I8 | `[7,10,5,0]`, heating not started | 3 seats in S1 cancel | `[7,10,2,0]`. Plan unchanged: S1 to S3, since S3 still holds 2 seats | add |
| I9 | `[7,10,2,0]`, heating not started | 2 seats in S1 cancel | `[7,10,0,0]` (A3). S3 is not heated. With stored placement and no move the state would be `[5,10,2,0]` and S3 would be heated, so the fill-order rule saves one heater. No heater was on, so nothing is switched off | add, inf |
| I10 | `[7,10,12,3]` (32 seats), heating not started | 5 seats in S1 cancel | `[7,10,10,0]` (A5). S4 is not heated: four saunas become three. The seat heaters are always the first k in fill order with combined capacity ≥ seats (INV-6) | add, inf |

**I11–I12. Warm saunas vs open saunas**

| ID | Given | When | Then | Basis |
|---|---|---|---|---|
| I11 | gradual opening off, `[7,3,0,0]`, On: S1, S2. Guests move freely between all saunas not booked in full, and hold K(S1) to K(S4) (A, H1) | guests arrive | S3 and S4 are open for seats and cold, and guests are not told which sauna their seats are in. A guest can walk into a cold sauna. Open decision; recommended: with heater control on, the email says which saunas are warm, or gradual opening is used so that codes follow the open set (I12) | add, inf |
| I12 | gradual opening on, maximum 4. S1 is full (`[7,0,0,0]`) and S2 has opened empty | 14:00 | strict rule: On: S1 only, although S2 is open and its code has gone out (H17). Open decision; recommended: while heating applies to W, also heat the sauna that is open for seats but empty. Cost: one extra heater at most; it extends the addendum's "at least one booking" to "or open for seats" | add, inf |

**I13–I18. Changes after heating has started**

| ID | Given | When | Then | Basis |
|---|---|---|---|---|
| I13 | `[7,10,2,0]`, On: S1, S2, S3 since 14:00 | 14:30: 2 seats in S1 cancel | `[7,10,0,0]`; S3 is on without a booking. Open decision; recommended: switch S3 off at once, because "no booking, no heating" holds at every moment, and switch it on again if a later booking needs it (I14). Alternative: leave it on until the stop time | add, inf |
| I14 | `[7,10,0,0]`, On: S1, S2 since 14:00 | 14:40: A books 1 seat (before the booking deadline) | `[7,10,1,0]`. S3 heating starts at 14:40, 40 minutes late (compare H9). The booking is accepted; the administrator sees "started late" for S3. Refusing is the alternative; not recommended (lost sale, and the default deadline is 5 minutes after the start) | add, inf |
| I15 | `[7,10,0,0]`, On: S1, S2 since 14:00. Codes go out at 14:40 | 14:30: B whole-books S4 (17 ≤ 29) | accepted; S4 heating starts at 14:30. H12 does not apply yet, because the codes are not sent; from 14:40 it does (recommended refusal) | add, inf |
| I16 | `[7,10,5,0]`, On: S1 to S3 since 14:00 | 14:30: S3 is blocked | seats move to S4 (D2): `[7,10,—,5]`. S3 off (no override). S4 on from 14:30, 30 minutes late | add, inf |
| I17 | state of I16 | 14:50: the block is lifted | recommended D7: `[7,10,5,0]`. S3 on again, S4 off. A short block flips two heaters twice; accept | add, inf |
| I18 | `[7,—,12,4]` (23 seats), On: S1 to S4 (S2 whole-booked) | 14:30: the whole booking of S2 cancels | `[7,10,6,0]` (B6). S2 stays on (now holds seats), S4 goes off. The heater set changes by sauna, not only by count | add, inf |

**I19. Window already started**

| ID | Given | When | Then | Basis |
|---|---|---|---|---|
| I19 | W has started (15:00). `[7,10,2,0]`, On: S1 to S3 | 15:20: 2 seats in S1 cancel | F3 recommends no moves in a started window. The derived model would give `[7,10,0,0]` and switch S3 off while guests, who move freely, may be in it. Recommended: no heater is switched off before its stop time in a started window, and the heater state is recorded when it is switched on, not recomputed. This is the first effect of placement that is visible in default mode, and it is why F3 needs the heater events remembered (INV-7) | add, inf |

**I20–I23. Several windows and settings**

| ID | Given | When | Then | Basis |
|---|---|---|---|---|
| I20 | W1 15:00–16:30 and W2 16:30–18:00, S1 booked in both | 16:30 | S1 stays on; no stop and start (addendum assumption) | add |
| I21 | W1 `[7,10,3,0]`, W2 `[7,2,0,0]`, different bookers | 16:30 | S1 and S2 stay on. S3 stops at 16:30 and is not restarted for W2. The fill order is the same in every window, so S1 is the sauna most often carried over, which saves stop/start cycles | add, inf |
| I22 | S3 booked in W1 (15:00–16:30) and W3 (18:00–19:30), none in W2. Stop is set 45 minutes after the window end | 16:30 to 18:00 | the stop (17:15) is later than the W3 start (17:00), so S3 stays on. Open decision; recommended: stays on. The addendum names only consecutive booked windows; this extends it to booked windows with an empty one between | add, inf |
| I23 | heating for W started at 14:00. Administrator changes the heating start to 90 minutes before | 14:20 | open decision; recommended: applies only to windows whose heating has not started (compare H10) | inf |

## Cross-dimension insights

The theory and the hotel evidence point the same way: the cost of the move algorithm comes from *committing* a placement and then repairing it [4][6][7]. The addendum already says guests are not told their sauna, so committing a placement buys nothing until step 2. Deriving it removes the move step, removes the "move must finish before the sauna is bookable" race (A3, C3) by making it one atomic count, and shrinks the if-time work for cancellation to "decrement the count". The stored-placement version remains the right choice only if one-sauna access must be built.

Heating points the same way on the fill rule and the other way on state. Compaction is what keeps the number of running heaters at the minimum (I9, I10), so heating is a second reason to keep the fill order and not to let seats stay where they were first placed. But a heater is a side effect that cannot be taken back like a count, just as a sent door code cannot (H12). The wanted heater set can be derived; the actual state must be recorded and reconciled against it (I13–I19).

## Recommendations

1. **Write the PRD rule as invariants INV-1 to INV-5 plus the catalogue, not as the move algorithm.** Mark "how placement is computed" as an architecture decision. Basis: inference from the addendum and [6][7] (medium).
2. **Prefer derived placement for v1 and the if-time track** (counts per window plus whole bookings and blocks). Confirm with a model-based test against the catalogue. Basis: inference, no practitioner source (low-medium).
3. **Require venue-wide, non-overlapping time windows** (E1, E3). Without it the capacity guarantee does not hold. Basis: addendum plus reasoning (medium).
4. **Decide D3, D7, D8, F1–F3 in the PRD.** Each is silent in the addendum; the catalogue gives a recommended answer for each.
5. **Run all of group C as parallel tests; wrap each write unit in one transaction** (`BEGIN IMMEDIATE` in SQLite [1]; Serializable with retry in PostgreSQL [2]). Basis: official docs (high for the mechanism).
6. **Skip group G unless one-sauna access is promoted.** If it is, H19–H23 apply and placement must be stored.
7. **Write group H into the PRD as the acceptance criteria for Success Criterion 6.** Decide H6, H10, H12, H13, H21 and H23. The addendum is silent on each; the catalogue gives a recommended answer. H6, H11–H13, H15 and H21 now rest partly on the lock-behaviour run [11]. Basis: addendum plus reasoning (medium).
8. **Write group I into the PRD only when heating is built (vision); v1 needs nothing from it.** Then decide I11/I12, I13, I14, I19, I22 and I23; the addendum is silent on each, and the catalogue gives a recommended answer. Keep the heater controller as "wanted set derived from the bookings, actual state recorded, reconcile on every booking, cancellation and block". Basis: addendum plus reasoning (low-medium; no source on heaters).

## Open questions

| Question | What would answer it |
|---|---|
| Stored vs derived placement in real booking systems | A practitioner retrospective; none found. A prototype plus the model-based test settles it for this project |
| Is the derived formula correct under blocks and whole bookings together? | A model-based test comparing the formula to a brute-force reference |
| Sauna, spa or fitness comparables for private-vs-shared booking and moves | A vendor documentation search (not run, budget) |
| Full text of the migration-bound papers [4][5] and the RoomTetris algorithm [7] | Optional; matters only if no-split groups are built |
| Can two codes with different PINs overlap on one real lock (H6), and can a standard code be edited or deleted after its validity started (H12–H14)? | Partly answered by a later run [11]: several codes per door is normal, offline codes cannot be revoked, online codes can be changed. Overlap and after-start edits are unanswered; test on a real or Seam sandbox lock |
| How long does a sauna heater need to warm up, and can a remote-controlled heater be switched on and off freely? | Manufacturer and controller documentation; not searched. Decides whether late starts (I14–I18) and flipping heaters (I13, I17) matter in practice, and what start lead time is sensible |
| Is an open but cold sauna acceptable (I11, I12)? | A product decision in the PRD; the catalogue recommends warm-sauna information or heating the open set |

## Source appendix

| [n] | Supports | Publisher | Pub date | Accessed | Confidence |
|---|---|---|---|---|---|
| [1] | BEGIN IMMEDIATE, deferred upgrade BUSY, WAL | [SQLite docs, transaction](https://www.sqlite.org/lang_transaction.html) | living doc | 2026-10-28 | high (re-fetched by lead) |
| [2] | Serializable retry on 40001, write-skew example | [PostgreSQL docs, transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html) | current (v18) | 2026-10-28 | high |
| [3] | Exclusion constraints over ranges | [PostgreSQL docs, range types](https://www.postgresql.org/docs/current/rangetypes.html) | current (v18) | 2026-10-28 | high on definition |
| [4] | Migration factor, 4/3 bound (strip packing) | [arXiv 1706.04939](https://arxiv.org/abs/1706.04939) | 2017-06-15 | 2026-10-28 | high for variant |
| [5] | Fully dynamic bin packing, migration bounds | [Univ. Lübeck, Berndt, Jansen, Klein](https://research.uni-luebeck.de/en/publications/fully-dynamic-bin-packing-revisited/) | n/d | 2026-10-28 | medium (snippet) |
| [6] | Late room assignment, moving guests undesirable | [GuestCentric (hetras repost)](https://blog.guestcentric.com/?p=12293) | 2013-03-20 | 2026-10-28 | medium |
| [7] | Early room commitment causes unnecessary rejections | [Emerald, RoomTetris (JHTT)](https://www.emerald.com/jhtt/article/11/4/589/223396/RoomTetris-an-optimal-procedure-for-committing) | n/d | 2026-10-28 | medium (abstract, lead-fetched) |
| [8] | Restaurant tables not moved automatically | [aleno knowledge base](https://knowledge.aleno.me/en/kb/1.1-automatische-tischzuteilung-was-ist-das-en) | n/d | 2026-10-28 | medium |
| [9] | Model-based (stateful) testing | [Hypothesis docs (mirror)](https://hypothesis-test-zhd.readthedocs.io/en/latest/stateful.html) | n/d | 2026-10-28 | medium (snippet) |
| [10] | Locking, hold and move concurrency | Prior run `technical-booking-concurrency-seat-holds-2026-10-27` (this repo) | 2026-10-27 | 2026-10-28 | see that report |
| [11] | Lock behaviour for H6, H11, H12–H15, H21: several codes per door, no documented overlap rule, same-PIN collisions, offline codes cannot be revoked, online codes editable, hour resolution, delivery not confirmed by an accepted request | Later run `technical-smart-lock-door-code-overlap-and-revoke-2026-10-28` (this repo; sources Seam, Allegion, igloohome, RemoteLock, TTLock, Nuki) | 2026-10-28 | 2026-10-28 | see that report; Seam, Allegion and igloohome claims re-fetched, others medium or low |

## Staleness map

- **Version-bound, re-check by 2026-11-01** (1-month bar): the SQLite and PostgreSQL behaviour in [1]-[3]. Re-check when the database engine and version are chosen in architecture.
- **Older than the 2-year pattern bar:** [4] (2017) and [6] (2013). [4] is a theoretical result and ages slowly; [6] is a vendor blog, corroborated by the undated academic source [7]. Treat both as background, not current practice.
- **Ecosystem signal [8]** is within its 6-month bar; re-check by 2027-04-01.
- **Not date-checked:** inference items (derived formula, E1/E3 recommendations) have no source to age. They are checked by the model-based test, not by a re-run.
