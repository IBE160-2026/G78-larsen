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
- **The catalogue below (39 examples) is the deliverable.** The sharpest finds: overlapping time windows silently break per-window capacity (E1), a block can force bookings out (D3), and unblocking or reordering needs an explicit rule (D7, F2).
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
- **Store vs derive placement.** No practitioner source was found (open question). Reasoned position (inference): store only booked seats per window plus whole bookings and blocks; compute placement on read. Guests are never told their sauna and need no notice on moves (addendum), so stored placement has no observable meaning until one-sauna access exists in step 2.
- **Derived rules (inference, to be proven by test).** Let `seats(W)` be total individual seats in window W, and `P(S)` the sum of capacities of saunas that precede S in fill order and are neither whole-booked nor blocked.
  - Free seats shown = Σ capacity of non-whole, non-blocked saunas − `seats(W)`.
  - Whole booking of S allowed iff S is not blocked, not whole-booked, and `seats(W) ≤ P(S)`.
  - Placement of seats = fill saunas in fill order, skipping whole-booked and blocked.
- **Fixed slots vs free windows.** With a venue-wide grid of fixed windows, "same window" is equality of a window id and a plain UNIQUE or partial-unique constraint works in both databases (inference, no source retrieved). Free overlapping windows need interval logic (see E1).
- **Test approach.** Model-based (stateful) testing generates action sequences and checks invariants after each step [9] (medium; mirror, snippet only). Worth using for this rule set because the examples below are sequences of bookings, cancellations and blocks. Invariants: INV-1 per sauna placed ≤ capacity; INV-2 Σ placed = Σ booked seats in the window; INV-3 a whole-booked sauna holds zero seats; INV-4 a blocked sauna holds zero seats; INV-5 compaction: no sauna earlier in fill order has free space while a later one holds seats (inference).

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
| G1 | S1=7, S2=10, no-split. A=3 in S1, B=5 in S2 | C=6 books | first-fit rejects C (S1: 9>7, S2: 11>10) though a repack fits (C in S1, A+B = 8 in S2). State whether repacking is allowed | add, inf, [4] |

## Cross-dimension insights

The theory and the hotel evidence point the same way: the cost of the move algorithm comes from *committing* a placement and then repairing it [4][6][7]. The addendum already says guests are not told their sauna, so committing a placement buys nothing until step 2. Deriving it removes the move step, removes the "move must finish before the sauna is bookable" race (A3, C3) by making it one atomic count, and shrinks the if-time work for cancellation to "decrement the count". The stored-placement version remains the right choice only if one-sauna access must be built.

## Recommendations

1. **Write the PRD rule as invariants INV-1 to INV-5 plus the catalogue, not as the move algorithm.** Mark "how placement is computed" as an architecture decision. Basis: inference from the addendum and [6][7] (medium).
2. **Prefer derived placement for v1 and the if-time track** (counts per window plus whole bookings and blocks). Confirm with a model-based test against the catalogue. Basis: inference, no practitioner source (low-medium).
3. **Require venue-wide, non-overlapping time windows** (E1, E3). Without it the capacity guarantee does not hold. Basis: addendum plus reasoning (medium).
4. **Decide D3, D7, D8, F1–F3 in the PRD.** Each is silent in the addendum; the catalogue gives a recommended answer for each.
5. **Run all of group C as parallel tests; wrap each write unit in one transaction** (`BEGIN IMMEDIATE` in SQLite [1]; Serializable with retry in PostgreSQL [2]). Basis: official docs (high for the mechanism).
6. **Skip group G unless one-sauna access is promoted.**

## Open questions

| Question | What would answer it |
|---|---|
| Stored vs derived placement in real booking systems | A practitioner retrospective; none found. A prototype plus the model-based test settles it for this project |
| Is the derived formula correct under blocks and whole bookings together? | A model-based test comparing the formula to a brute-force reference |
| Sauna, spa or fitness comparables for private-vs-shared booking and moves | A vendor documentation search (not run, budget) |
| Full text of the migration-bound papers [4][5] and the RoomTetris algorithm [7] | Optional; matters only if no-split groups are built |

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

## Staleness map

- **Version-bound, re-check by 2026-11-01** (1-month bar): the SQLite and PostgreSQL behaviour in [1]-[3]. Re-check when the database engine and version are chosen in architecture.
- **Older than the 2-year pattern bar:** [4] (2017) and [6] (2013). [4] is a theoretical result and ages slowly; [6] is a vendor blog, corroborated by the undated academic source [7]. Treat both as background, not current practice.
- **Ecosystem signal [8]** is within its 6-month bar; re-check by 2027-04-01.
- **Not date-checked:** inference items (derived formula, E1/E3 recommendations) have no source to age. They are checked by the model-based test, not by a re-run.
