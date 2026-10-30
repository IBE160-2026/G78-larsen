---
title: "Input reconciliation: brief addendum vs PRD"
created: 2026-10-29
input:
  - .docs/planning-artifacts/briefs/brief-booking-platform-2026-09-20/addendum.md (updated 2026-10-29, 324 lines)
checked_against:
  - prd.md (draft v1, 2026-10-29, 926 lines)
  - addendum.md (PRD addendum, sections A-J)
  - .memlog.md (PRD decision log)
  - also consulted to settle ambiguities: brief .memlog.md (BM-L30, BM-L84-L85, BM-L91, BM-L120, BM-L124-L125) and brief.md (L55-L73)
---

# Input reconciliation: brief addendum vs PRD

## How to read this

- **Input** = line in the brief addendum. Many brief rows are one long line (L49, L60, L62, L63, L73), so one line can give several rows here, each with its own quote.
- **Status:** `captured` / `partially captured` / `missing` / `contradicted` / `superseded by decision (PM-Lnn)` / `intentionally left in brief addendum` (the PRD points there: PRD §0 L16 and Add L3 say the full rule tables and the IV/PW/RB/HT/CT tables live in the brief addendum) / `n/a` (moot in v1).
- **Line refs:** `PRD Lnnn` = prd.md, `Add Lnn` = PRD addendum.md, `PM-Lnn` = PRD .memlog.md, `BM-Lnn` = brief .memlog.md, `B-Lnn` = brief addendum (used in prose).
- "Promoted" means a brief `[ASSUMPTION]` that the PRD states as a requirement without a tag, without a §13 entry and without a PM decision.
- **Gap n** refers to the ranked list at the end.

## Totals

**255 points** from the brief addendum (rules, defaults, limits, test cases, constraints and brief `[ASSUMPTION]`s):

| Status | Count | Rows |
|---|---|---|
| captured | 171 | (some carry notes) |
| partially captured | 34 | |
| superseded by decision | 27 | PM-L27: 13, PM-L32: 7, PM-L29: 3, PM-L26: 2, PM-L25, PM-L28, PM-L31: 1 each (row 100 cites PM-L27 and PM-L32) |
| intentionally left in brief addendum | 14 | Vision rules, and the per-website list after the exam |
| missing | 6 | 98, 112, 113, 119, 126, 151 |
| contradicted | 2 | 11 (Step 2 order), 127 (one-Sauna email names the Sauna) |
| n/a | 1 | 107 |

**Test cases:** CT 5 of 5, IV 7 of 7 and HT 4 of 4 have an FR consequence. PW and RB are covered only by phase. PW-1 ("password changed"), PW-2, PW-3 and the guest-account half of PW-5 have no Core path, but SM-2 counts them in the Core (Gap 1).

No number in the PRD contradicts the brief addendum except where a PM decision changed it (password length, max Seats, refund remedy, 06:00 scope). One number lost half its range: the Booking deadline can be moved "earlier or later" in the brief, only "earlier" in FR-39 (Gap 5).

## Top gaps at a glance

1. **SC9 cannot be proven in the Core as SM-2 claims.** PW-2/PW-3, RB-2, RB-5 and RB-6 need features from If time, and no Core path creates an Administrator or changes a password (Gap 1).
2. **A partial Seat move has no defined result.** The brief allows moving "1 of 4", but FR-9 says one Window per Booking (Gap 2).
3. **The refund-or-Voucher choice after a venue-caused cancellation has no flow** (Gap 3).
4. **FR-29's condition list breaks Whole-booking-only and ignores Holds**, although Add A has the right formula (Gap 4).
5. **Booking horizon and deadline:** their scope (Whole-sauna bookings, Changes) and bounds are not stated (Gap 5).

---

## Ledger

### 1. Delivery phases (L11-L22)

| # | Input | Point (short quote) | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| 1 | L17 | v1 core: "Individual seats (name and email, no account; simulated instant payment; confirmation by simulated email)" | captured | §4.1-4.2; FR-5 (PRD L203-214), FR-6 (L216-223), FR-8 (L232-245) | |
| 2 | L17 | "one price per seat (no distinction between children and adults)" | captured | FR-3 (L186), §9 (L824) | |
| 3 | L17 | "Time windows, capacity and prices set by seed or configuration without administrator screens" | captured | §4.4 (L298), §9 (L826) | |
| 4 | L17 | "the capacity invariant with atomic booking" | captured | FR-10 (L258-263), FR-11 (L265-271) | |
| 5 | L17 | "the booking horizon, booking deadline and cancellation cut-offs as fixed defaults" | captured | FR-2 (L173), FR-3 (L184), FR-18 (L342) | The cut-offs have no Core use, because Change arrives with §4.8. |
| 6 | L17 | "administrator login with a booking list, input validation, hashed passwords and role-based access with tests" | partially captured | FR-15 to FR-20; SM-2 (L867); §10.1 (L840) | FR-19/FR-20 defer PW-2, PW-3, RB-2 and RB-6 to §4.12, and RB-5 needs §4.8, yet SM-2 says all IV/PW/RB cases pass in the Core. **Gap 1.** |
| 7 | L18 | If-time order "1 Change … or a voucher …; 2 Seat placement and Whole-sauna booking …; 3 "My booking" …; 4 Seat hold; 5 Guest accounts; 6 the rest of v1 …; 7 Step 2" | superseded by decision (PM-L26) | §10.1 (L842-851) | HTTPS was inserted as item 1 ("HTTPS (2B): «hvis tid», første punkt før endring/voucher"). The brief order is otherwise kept, shifted by one. |
| 8 | L18 | "(change first, voucher last)" | captured | §4.8 (L426), §13 (L907) | Tagged `[ASSUMPTION]`, as in BM-L125 ("[ASSUMPTION on order]"). |
| 9 | L18 | "cancelling before whole-sauna booking is decided, and so is that all of v1 including its if-time items comes before step 2" | captured | §0 (L25), §10.1 (L844, L849) | |
| 10 | L18 | item 6: "Blocked periods (without door-code and heating overrides) … Overbooking fallback (without door-code text)" | captured | FR-40 (L615-629), FR-42 (L646) | |
| 11 | L19 | Step 2 "in this order": "Gradual opening and one-sauna access (seat placement options); Gift cards; Door codes (…); Mobile layout" | contradicted | §10.2 (L856), FR-50 (L719-730), Add H (L255) | The PRD follows brief.md L69-73 (Gift cards, then Door codes, then Mobile) and folds the access modes into Door codes. Add H notes this, but there is no PM decision. **Gap 10.** |
| 12 | L19 | Door codes in Step 2 cover "send time, source, resend, extra and moved-sauna emails, one-sauna access as it affects codes, door-code text in the overbooking email and block overrides" | partially captured | FR-42 (L646), FR-45 to FR-50 (L675-730) | No FR sets the Send time or a per-Block override, and the one-Sauna email that names the Sauna is missing (Gaps 6, 8, 12). "Moved-sauna emails" is stale in the brief itself, since BM-L120 superseded it. |
| 13 | L19 | "Mobile layout, after the laptop layout works" | captured | FR-51 (L735-739), §10.2 (L856) | |
| 14 | L20 | Vision list: locations, children and adults, membership, period cards, renewal, remote door control, heater and temperature | captured | §4.17 (L741-753), §9 | The detailed rules stay in the brief addendum (rows 137-140, 154, 158). |
| 15 | L22 | "simulated payment is instant, so the core books in one atomic step without a hold" | captured | §4.2 (L199), FR-6, §4.11 (L548) | |
| 16 | L22 | "in v1 all saunas not booked in full are open for individual seats and guests may move between them" | captured | FR-4 (L195), Glossary Open for Seats (L128) | |
| 17 | L22 | "Vouchers (tilgodebevis) are part of v1 … gift cards in step 2 may share their mechanism" | captured | §10.1 NOTE (L853), FR-27 to FR-28 (L450-465) | FR-28 borrows the Gift-card partial use as `[ASSUMPTION]`. |

### 2. Guest journey (L24-L42)

| # | Input | Point (short quote) | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| 18 | L26 | "The guest first chooses Individual seats or Private sauna" | captured | §4.1 (L154), FR-30 (L491-496) | The Private sauna entry appears once §4.9 is built. |
| 19 | L26 | "after pressing Book, the guest chooses whether to log in, then accepts the terms and goes on to (simulated) payment" | partially captured | FR-5 (L213), FR-35 (L553), FR-37 (L583) | No FR places the optional sign-in step in the flow (after Book, before the terms). |
| 20 | L30 | "picks a date in a calendar, and can change it at any time" | partially captured | FR-2 (L174), FR-5 (L214) | Typing, picking and the keyboard are covered. Changing the date from a later step is not. |
| 21 | L30 | "a list of time windows and the free seats in each, not a list of saunas. The guest picks a time window and the number of seats" | superseded by decision (PM-L31) | FR-2 to FR-3 (L169-186), UJ-1 | Order is date, then number of Seats, then Window ("flyt dato, antall plasser, tidsvindu"). The Window list with Seats left is kept. |
| 22 | L36-L38 | Private sauna: "a list of free private saunas and their time windows. Two routes: Pick a time window directly. Open a specific sauna, pick the time window, and press Book." | partially captured | FR-30 (L492-495), UJ-5 (L95-96), Add G (L247) | PRD route 1 is Window first, then Sauna. Add G says the brief's direct route meant "automatic Sauna assignment" and replaces it "(PRD assumption)". The brief's list is Sauna-centred and never mentions assignment. No PM decision. **Gap 11.** |
| 23 | L42 | "v1 has one location. Seats draw on the combined capacity of the saunas not booked in full" | captured | Glossary Venue (L114), Seat capacity (L129) | |
| 24 | L42 | Vision: locations A and B, free seats counted per location | intentionally left in brief addendum | §4.17 (L743) | |
| 25 | L42 | "The guest is not told which sauna the seats are placed in" | captured | FR-4 (L192), FR-31 (L513) | |

### 3. Booking rules (L44-L67)

**Individual seats, Seat placement, Gradual opening, Whole-sauna booking**

| # | Input | Point (short quote) | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| 26 | L48 | "Seats are not tied to a particular sauna: they draw on the combined capacity of all saunas not booked in full"; example 7/10/12/15, giving 22 | captured | Glossary Sauna, Seat capacity (L116, L129) | Same example set. |
| 27 | L48 | "Individual booking requires only that seats are available … Guests see the total number of free seats" | captured | FR-3 (L178-182), FR-40 (L629) | |
| 28 | L49 | "placed in one sauna until it is full, then in the next. A group may therefore be split" | captured | Glossary Fill order (L131), FR-31 | |
| 29 | L49 | "the booking flow must make clear that the guest books seats, not a sauna; a group … must book a whole sauna" | captured | FR-4 (L193-196) | |
| 30 | L49 | "The administrator sets the fill order" | captured | FR-38 (L591), §4.9 (L468) | Seed data until §4.13. |
| 31 | L49 | Invariants: "no sauna holds more seats than its capacity; a whole-booked or blocked sauna holds none; no sauna earlier in the fill order has free room while a later one holds seats", after "every cancellation, change, block and lifted block" | captured | FR-31 INV-1 to INV-5 (L499-506) | The PRD adds INV-2 and two INV-5 exceptions (F3; one-Sauna access). See row 126 for the one-Sauna clash. |
| 32 | L49 | "A whole-sauna booking is accepted only when these conditions hold with that sauna's seats removed, never over seats still in it" | superseded by decision (PM-L27) | FR-29 (L476-480), Add B (L67) | Strict rule "Seats booked ≤ Room ahead" ("streng hel-badstue-regel seats(W) <= P(S)"). The ambiguity was found in PM-L22. |
| 33 | L49 | "moving stored seats or … deriving the placement … is an architecture decision; the PRD states the rule as these invariants and as worked examples" | captured | FR-31 (L509-514), §12 Q5 (L886), Add A (L19-23) | |
| 34 | L49 | "no notice is sent when seats move (except with one-sauna access, where all seats in a booking stay in one sauna…)" | partially captured | FR-4 (L192), FR-31 (L513), Glossary Placement (L132) | The default case is captured. The one-Sauna exception is missing: the PRD says Guests are "never told a Sauna". **Gap 6.** |
| 35 | L49 | "With one-sauna access, placement is frozen at the send time" | captured | FR-31 (L506), FR-50 (L729) | |
| 36 | L49 | "The administrator can see in the system which sauna the seats are placed in" | captured | FR-31 (L513), §7 (L789) | |
| 37 | L49 | "guests can move freely between all saunas that are not booked in full … not an assignment" | captured | FR-4 (L195), Glossary Placement (L132) | |
| 38 | L50 | Gradual opening: "Optional … Off … On: saunas open for individual seats one at a time in the fill order … until the maximum … is reached" | captured | FR-50 (L723-724) | The default maximum ("All saunas", L113) is not stated (row 151). |
| 39 | L50 | "Guests see only the free seats in the open saunas; saunas not yet opened stay free for whole-sauna booking" | captured | Glossary Open for Seats (L128) | Ambiguity carried over from the brief: a group bigger than the room left in the open Sauna cannot book until that Sauna is "full" (Gap 12). |
| 40 | L50 | "An individual-seat booker gets the door codes for the open saunas only" | captured | FR-46 (L687) | |
| 41 | L50 | "When seat moves after a cancellation empty the last opened sauna, it closes again" | captured | FR-50 (L725) | |
| 42 | L51 | Whole-sauna booking: "Configurable per sauna" | captured | FR-29 (L478), FR-38 (L591) | |
| 43 | L51 | "A sauna booked in full leaves the individual-seat capacity for that window" | captured | Glossary Seat capacity (L129), FR-29 B7 (L487) | |
| 44 | L51 | "Allowed only if no individual seat is placed in that sauna in that window" | partially captured | FR-29 (L477-480, L489), Add A (L28-33) | Same as the strict rule while INV-5 holds. But FR-29's condition list refuses an unreleased Whole-booking-only Sauna that is not last in the Fill order, and it ignores held Seats. Add A fixes both; FR-29 does not. **Gap 4.** |

**Whole-booking-only, the 06:00 rule, children, pricing**

| # | Input | Point (short quote) | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| 45 | L52 | "mark a sauna's window as whole-booking-only and reverse it" | captured | FR-41 (L632-636) | Marking over placed Seats is refused (D8, decided in PM-L27). |
| 46 | L53 | "if a sauna is not booked in full for a window …, its seats open for individual booking at 06:00 the same morning" | superseded by decision (PM-L29) | FR-41 (L637), Glossary Release time (L136), Add H (L254) | Applies only to Saunas marked Whole-booking-only (PM-L29; found in PM-L19). The brief wording still reads as all Saunas. |
| 47 | L53 | "The administrator can reverse it" | captured | FR-41 (L632, L636) | BM-L30 defines "reverse" as marking the Window whole-only again. FR-41 allows that, refused while Seats are placed (D8). |
| 48 | L53 | "can also set another time than 06:00, or turn the rule off" | captured | FR-39 (L608), FR-41 (L638) | |
| 49 | L53 | [ASSUMPTION: "off" means the seats never open] | superseded by decision (PM-L29) | FR-41 (L638) | "«av» betyr at de aldri åpner". |
| 50 | L54 | No distinction in v1 and step 2; vision: "age limit (under 14 by default) and choose whether children have a lower price" | captured | §9 (L824), §4.17 (L744) | The Vision line says "a lower child price", while the brief makes it optional. Cosmetic. |
| 51 | L55 | "priced per person … a whole sauna has one price. The per-person price is the same across saunas; the whole-sauna price is set per sauna" | captured | FR-3 (L186), FR-30 (L495), FR-38 (L591) | |
| 52 | L55 | "Applies to a time window" | captured | FR-3, FR-26 (L446) | The PRD adds `[ASSUMPTION]` one Seat price in every Window (FR-26, §13 L908), a narrowing the brief does not state. |
| 53 | L55 | "Several windows can be booked, consecutive or not, together or as separate bookings …, paying for each window" | superseded by decision (PM-L32) | FR-9 (L247-251), §9 (L821) | "én booking = ett vindu" (PM-L32); "ingen kombinert handlekurv" (PM-L10). "Together" is dropped. |

**Booking deadline, Booking horizon, Seat hold, Overbooking fallback**

| # | Input | Point (short quote) | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| 54 | L56 | "5 minutes after the window starts by default" | captured | FR-39 (L605), Glossary (L138) | |
| 55 | L56 | "The administrator can set it earlier or later, also before the start" | partially captured | FR-39 (L605) | FR-39 says "may be set earlier, even before the start". "Later" is dropped, and there is no upper bound, so a deadline after the Window ends would pass IV-6. **Gap 5.** |
| 56 | L56 | "After the deadline, the window is no longer offered" | captured | FR-3 (L184), FR-18 (L342) | |
| 57 | L56 | [ASSUMPTION: applies to both individual seats and whole saunas, and to changing a booking into that window] | partially captured | FR-18 (L342) only | Not in FR-29, FR-26 or FR-33, and not in §13. **Gap 5.** |
| 58 | L57 | "within a period the administrator sets, 4 weeks ahead by default. Windows further ahead are not yet offered" | captured | FR-2 (L173), FR-18 (L342), FR-39 (L604) | |
| 59 | L57 | [ASSUMPTION: "counted from the moment of booking to the start of the window"] | captured | Glossary Booking horizon (L137) | Promoted to a definition, with no tag and no §13 entry. |
| 60 | L57 | [ASSUMPTION: applies to … whole saunas, period-card bookings and changing a booking into a later window; the administrator can still create and see windows further ahead] | partially captured | FR-18 (L342) | The Whole-sauna and Change scope is not explicit, and Administrator access beyond the horizon is missing. Period cards are Vision. **Gap 5.** |
| 61 | L58 | Seat hold "Built only if time allows … the booking is confirmed in one atomic step" | captured | §4.2 (L199), §4.11 (L547-548), §10.1 (L847) | |
| 62 | L58 | "for a fixed 10 minutes, and released if the booking is not completed" | captured | FR-35 (L552-559), Glossary Hold (L144) | FR-35 L559 says "a failed or abandoned payment releases the Hold at once", but "abandoned" is not defined and cannot be tested. Expiry already covers it. |
| 63 | L58 | "The hold time is not an administrator setting" | captured | §4.11 (L548) | |
| 64 | L58 | "check and reserve capacity in one atomic operation, both when seats are held and when a booking is confirmed" | captured | FR-10, FR-35 (L557), §4.11 (L548) | |
| 65 | L58 | "A payment completed after the hold has expired gives a booking only if the seats are still free; otherwise the payment is refunded" | captured | FR-36 (L562-567) | |
| 66 | L59 | "the latest booking loses and is refunded" | superseded by decision (PM-L32) | FR-42 (L642-645), Add B (L79), Add H (L257) | The Guest chooses a refund or a Voucher ("ved Saunalöylys avlysning velger gjesten refusjon eller voucher"; also PM-L27 D3). The decision left the choice flow unspecified. **Gap 3.** |
| 67 | L59 | Apology email: "the amount will be refunded and that it may take a few days to arrive" | partially captured | FR-42 (L646) | The text is kept, but the email "says either … refunded … or … the Voucher is attached", which assumes the choice was already made. **Gap 3.** |
| 68 | L59 | "If door codes have already been sent, the same email says they must not be used" | captured | FR-42 (L646), FR-48 (L709) | Step 2. |

**Cancellation and change, Gift cards**

| # | Input | Point (short quote) | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| 69 | L60 | "Individual seats are not offered a cash refund" | captured | §4.8 (L426), FR-27 (L457), §9 (L820) | |
| 70 | L60 | "Up to 12 hours before … change individual seats (one at a time, for example 1 of 4, or all together, e.g. to a different time window)" | partially captured | FR-26 (L441-448), FR-9 (L248) | "Some or all Seats" is captured. What a partial move does to the Booking is undefined, since FR-9 allows one Window per Booking. **Gap 2.** |
| 71 | L60 | "or, on that same notice, choose a voucher (tilgodebevis) issued by email instead of changing" | captured | FR-27 (L450-457) | Voucher value = price paid `[ASSUMPTION]`. |
| 72 | L60 | "Capacity is restored either way and the administrator sees it" | partially captured | FR-26 (L447), FR-27 (L456) | FR-27 restores capacity but does not say the Administrator sees the Voucher exchange. |
| 73 | L60 | "A whole-sauna booking can be cancelled or changed to a different time up to 72 hours before" | captured | FR-33 (L525-531) | |
| 74 | L60 | "On cancellation, the guest chooses a simulated refund or a voucher … which expires one year after issue" | captured | FR-33 (L529) | |
| 75 | L60 | "Capacity is restored, and the administrator sees the cancellation or change" | captured | FR-33 (L529) | That the Administrator sees a change is implied, not stated. |
| 76 | L60 | "can change both cut-offs … but never to less than 2 hours before the window starts" | captured | FR-39 (L606-607), Glossary Cutoff (L139) | |
| 77 | L61 | Gift cards: "no account needed, and pays (simulated); it is emailed to the buyer's own address as a coupon code … print it or forward it" | captured | §4.14 (L650), FR-43 (L654-660) | |
| 78 | L61 | "fixed denomination or an amount the buyer chooses, up to a set limit; the administrator sets the denominations and the limit" | captured | FR-43 (L658) | IA §7 (L790) has no Administrator screen for them. |
| 79 | L61 | "Whoever holds the code books … with or without an account; … individual seats and whole-sauna bookings" | captured | §4.14 (L650), FR-44 (L663) | |
| 80 | L61 | "used in part, with the remaining balance kept … partly by gift card and the rest by the ordinary (simulated) payment" | captured | FR-44 (L666) | |
| 81 | L61 | "expires one year after it is issued" | captured | FR-43 (L659), FR-44 (L667), §12 Q11 (L892) | Q11 flags the three-year limitation question. |

**Accounts, Blocked periods, Time windows, Email**

| # | Input | Point (short quote) | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| 82 | L62 | "An account is optional … buying a gift card also needs no account" | captured | FR-37 (L583), FR-43 (L655) | |
| 83 | L62 | "Either way, the booker receives a confirmation email with a booking reference and a link to change or cancel that booking" | partially captured | FR-8 (L244), FR-25, §4.8 (L426) | The Core confirmation has no Manage link (`[ASSUMPTION]`, §13 L901); the link arrives with §4.8. The phasing is reasonable and tagged. |
| 84 | L62 | "long, random token that cannot be guessed … the link is the only way into a booking" | captured | FR-20 (L368), FR-25 (L434) | The PRD adds access through the guest account that made the Booking, which matches RB-4. |
| 85 | L62 | "if they match, the link is sent again to that email" | superseded by decision (PM-L32) | FR-34 (L543), FR-25 (L437) | A new link is sent and the old one stops working ("ny lenke gjør gammel ugyldig"). A hashed token cannot be sent again anyway. |
| 86 | L62 | "the same answer whether or not they match … the number of attempts per email and per address is limited" | captured | FR-34 (L542-544) | 5 per hour each, `[ASSUMPTION]`. |
| 87 | L62 | [ASSUMPTION: how long a token stays valid, and whether it is stored hashed, are PRD decisions] | superseded by decision (PM-L32) | FR-25 (L434-437) | "token lagres hashet, gjelder til vinduet slutter, endring bare før frist". |
| 88 | L62 | "Bookings made without an account are not attached to an account created later" | captured | §4.12 (L570) | |
| 89 | L62 | "Buying and using a membership or period card requires an account" | intentionally left in brief addendum | §4.17 (L745) | Vision. |
| 90 | L62 | "There can be one or more administrator accounts" | partially captured | Glossary Administrator (L127) | "More can exist", but no FR, seed rule or command creates one. **Gap 1.** |
| 91 | L62 | "The administrator has an overview of time windows, bookings, cancellations, prices, fill order and blocked periods" | partially captured | FR-16 (L311-321), FR-31 (L513), FR-33 (L529), FR-38, FR-40 | Spread over several screens. Whether the booking list shows cancelled or changed Bookings is not stated. |
| 92 | L62 | Vision: an overview per location, and an administrator account can switch between locations | intentionally left in brief addendum | §4.17 (L743) | |
| 93 | L63 | Blocked periods: "block one sauna, several, or all of them for booking for a period" (calendar) | captured | FR-40 (L616), UJ-6 | |
| 94 | L63 | "A blocked sauna cannot be booked in full and gives no seats for individual booking" | captured | FR-40 (L619), INV-4 (L503) | |
| 95 | L63 | "A blocked sauna gets no door codes and is not heated, unless the administrator overrides this" | partially captured | FR-46 (L687, L689), §9 (L817) | Blocked Saunas get no codes, and the override's effect (H4) is stated, but no FR lets the Administrator set the override. **Gap 8.** |
| 96 | L63 | [ASSUMPTION: the override is chosen per block, separately for door codes and heating … codes … shown to the administrator, who shares them] | partially captured | FR-46 (L689) | As row 95. Heating is Vision. |
| 97 | L63 | [ASSUMPTION: a block covers every window that overlaps the period] | captured | FR-40 (L619), §13 (L916) | Still tagged. |
| 98 | L63 | [ASSUMPTION: the calendar shows windows, bookings and blocks together] | missing | UJ-6 (L104), §7 (L789, L791) | The UX workflow is told to sketch the blocking calendar first, but nothing says what it shows. **Gap 8.** |
| 99 | L63 | [ASSUMPTION: if the period already has bookings, the administrator sees them before confirming the block] | superseded by decision (PM-L27) | FR-40 (L620) | "admin ser berørte før bekreftelse". |
| 100 | L63 | [ASSUMPTION: the affected guests are told by email and get a full refund or a voucher, as they choose, regardless of the cancellation cut-offs] | superseded by decision (PM-L27, PM-L32) | FR-40 (L622-626) | The choice flow is unspecified. **Gap 3.** |
| 101 | L63 | [ASSUMPTION: seats that can move to another open sauna are moved instead, when the sauna has room] | captured | FR-40 (L621) | Promoted as catalogue case D2 with no tag. It is consistent with D3 (PM-L27), so the risk is low. |
| 102 | L63 | [ASSUMPTION: the administrator can lift a block, and the sauna is then bookable again] | superseded by decision (PM-L27) | FR-40 (L616, L627) | D7. |
| 103 | L64 | Time windows: "the same for every sauna … never partly overlap (… 16:30 … do not overlap). The platform rejects an overlapping window" | captured | FR-13 (L280-285), Glossary Window (L118) | |
| 104 | L64 | "New windows get a standard length, 1 hour 30 minutes by default" | captured | FR-38 (L594), Glossary (L118) | |
| 105 | L64 | "The administrator can set another standard length, and can give a single window another length for the whole venue" | captured | FR-38 (L594), FR-39 (L600) | The standard length is fixed in v1 (L109); the single-Window length is captured. |
| 106 | L64 | "A sauna that is unavailable for part of a window is handled with a block" | captured | FR-13 (L285) | E3. |
| 107 | L64 | [ASSUMPTION: changing the standard length does not change windows already created] | n/a | none | Moot in v1, because the standard length is fixed (L109). |
| 108 | L65 | Email: "Simulated (no real provider) in the first version" | captured | Glossary Outbox (L146), FR-17, §9 (L817) | |
| 109 | L67 | "Times, limits and options in this table are defaults. In v1 the administrator can change only the five settings" | captured | FR-39 (L599-600), Glossary Setting (L140) | |

### 4. Door codes (L71-L73), Step 2

| # | Input | Point (short quote) | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| 110 | L73 | "Door codes apply only to saunas with self-service door locks. The administrator marks per sauna whether it has one" | captured | FR-45 (L676-679) | |
| 111 | L73 | "a booking that only gives access to such saunas gets no door-code email" | captured | FR-46 (L688) | Implied: no code means no email. |
| 112 | L73 | [ASSUMPTION: the fictional venue has self-service locks on all its saunas] | missing | §12 Q3 (L884) | The seed question does not mention locks. Gap 12. |
| 113 | L73 | [ASSUMPTION: with one-sauna access, a booker whose sauna has no self-service lock is still told which sauna it is, by email at the same time, without codes] | missing | FR-50 (L727-730) | **Gap 6.** |
| 114 | L73 | "At a time the administrator chooses before a booked window starts (20 minutes by default)" | partially captured | FR-47 (L696, L698), §7 (L790) | The default and H10 are captured, but no FR or screen sets the Send time (brief.md L72: "the administrator's tools to set the timing"). Gap 12. |
| 115 | L73 | "Each door has its own code per time window … a sauna with more than one door can have a different code on each" | captured | §4.15 (L671), FR-47 | |
| 116 | L73 | "The administrator registers the doors and which sauna each one belongs to" | captured | FR-45 (L676) | |
| 117 | L73 | "two sources: the administrator enters them, or the platform fetches them from a connected lock system" (simulated) | captured | FR-45 (L676) | |
| 118 | L73 | [ASSUMPTION: the administrator chooses the source per door] | captured | FR-45 (L676, L680) | Promoted with no tag. |
| 119 | L73 | [ASSUMPTION: a code entered by the administrator can be changed until the door-code email is sent] | missing | none | Gap 12. |
| 120 | L73 | [ASSUMPTION: if a code is missing when the email is due, the administrator is alerted, and the email is sent as soon as the code is in place] | captured | FR-49 (L712-715) | Through H11, tagged. |
| 121 | L73 | "A code is shared by everyone who may use that door in that window, and is valid from the send time until the window ends" | captured | FR-47 (L693, L696) | H8. |
| 122 | L73 | "A whole-sauna booking gets the codes for that sauna" | captured | FR-46 (L686) | |
| 123 | L73 | "An individual-seat booking gets the codes only for the saunas open for individual seats in that window" | captured | FR-46 (L687) | H1 to H3. |
| 124 | L73 | "If another sauna opens for individual seats after the codes are sent …, those bookers get an extra email with its codes" | partially captured | FR-50 (L726) | FR-50 says "Seat bookers get an extra email when another Sauna opens" and drops the condition "after the codes are sent". Gap 12. |
| 125 | L73 | One-sauna access: "optional, set by the administrator … an individual-seat booking gives access to one sauna only, and all seats in the booking are placed in the same sauna" | captured | FR-50 (L720, L727-728) | |
| 126 | L73 | [ASSUMPTION: seats go to the first open sauna in the fill order with room for the whole booking; with gradual opening, the next sauna opens if no open sauna has room; seat moves after a cancellation move whole bookings, never part of one] | missing | FR-50 (L727-730), FR-31 (L504-506) | Without this rule, INV-5 cannot hold under one-Sauna access, even before the Send time. **Gap 6.** |
| 127 | L73 | "The door-code email then names that sauna and gives only its codes … the email names the sauna the seats are in at that moment" | contradicted | FR-4 (L192), FR-31 (L513), Glossary Placement (L132) | The PRD says Guests are "never told a Sauna", with no one-Sauna exception. **Gap 6.** |
| 128 | L73 | "Placement is frozen at the send time" | captured | FR-50 (L729), FR-31 (L506) | |
| 129 | L73 | "What happens when a block or cancellation would otherwise force a move after the send time is a PRD decision (the research recommends the overbooking fallback)" | partially captured | FR-50 (L729), §13 (L921) | Adopted as `[ASSUMPTION]`, not decided. Gap 12. |
| 130 | L73 | "A booking made after the send time gets the email at once" | captured | FR-47 (L697) | H9. |
| 131 | L73 | "No door-code rule depends on taking back a code already sent" | captured | §4.15 (L671), FR-48 (L703) | |
| 132 | L73 | "After the send time, a whole-sauna booking of a sauna is refused while individual-seat bookers hold its code …" | captured | FR-48 (L706) | H12. |
| 133 | L73 | "If a booking later loses to the overbooking fallback, the apology email also says the door codes must not be used" | captured | FR-42 (L646) | |
| 134 | L73 | "The administrator can see and resend the codes" | captured | FR-49 (L716) | |
| 135 | L73 | "One email is sent per booking, to the booker, who shares the codes with their group" | captured | §4.15 (L671) | |
| 136 | L73 | Remote door control (open mode, quick-open, automatic locking) and its [ASSUMPTION]s | intentionally left in brief addendum | §4.17 (L746) | Vision. |

### 5. Vision subsections (L75-L89)

| # | Input | Point (short quote) | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| 137 | L77 | Heater and temperature control, with [ASSUMPTION]s | intentionally left in brief addendum | §4.17 (L747), §9 (L817), §12 Q13 (L894) | |
| 138 | L81 | Membership: off by default; member price covers only the member; whole-sauna member price on; not refunded; tied to an account; [ASSUMPTION] on validity | intentionally left in brief addendum | §4.17 (L745) | §4.17 has no pointer to these subsections. Upkeep. |
| 139 | L85 | Period cards: off; 1 future booking; 50 per period; renewals first; calendar periods; not for whole saunas; not refunded; [ASSUMPTION]s | intentionally left in brief addendum | §4.17 (L745) | As row 138. |
| 140 | L89 | Renewal and payment: automatic renewal on; a guest can turn it off; gift cards and vouchers not allowed by default; [ASSUMPTION]s | intentionally left in brief addendum | §4.17 (L745) | As row 138. |

### 6. Administrator settings and "Fixed in v1" (L91-L136)

| # | Input | Point (short quote) | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| 141 | L93 | "only five rules are adjustable settings … Tests run against the defaults" | captured | FR-39 (L600, L613), SM-5 (L872) | |
| 142 | L97 | "How far ahead a guest can book: Up to 4 weeks before the window starts" | captured | FR-39 (L604) | |
| 143 | L98 | "Last time a window can be booked: 5 minutes after the window starts" | captured | FR-39 (L605) | See row 55 on bounds. |
| 144 | L99 | "Deadline to change individual seats or take a voucher: 12 hours … (no less than 2 hours)" | captured | FR-39 (L606) | |
| 145 | L100 | "Deadline to cancel or change a whole-sauna booking: 72 hours … (no less than 2 hours)" | captured | FR-39 (L607) | |
| 146 | L101 | "When seats open for individual booking: 06:00 the same morning; the administrator can set another time or turn the rule off" | superseded by decision (PM-L29) | FR-39 (L608), FR-41 | Narrowed to Whole-booking-only Saunas. |
| 147 | L109 | "Standard length of a time window: 1 hour 30 minutes (… a single window another length …)" | captured | FR-38 (L594) | |
| 148 | L110 | "Options when a whole-sauna booking is cancelled: Guest chooses a simulated refund or a voucher" | captured | FR-33 (L529) | |
| 149 | L111 | "When the door-code email is sent: 20 minutes before the window starts (… valid from then until the window ends)" | captured | FR-47 (L696) | Step 2. |
| 150 | L112 | "Gradual opening …: Off" | captured | FR-50 (L720) | |
| 151 | L113 | "Maximum number of saunas open for individual seats (gradual opening): All saunas" | missing | FR-50 (L724) | No default is stated. Gap 12. |
| 152 | L114 | "Door access for an individual-seat booking: All saunas open for individual seats …" | captured | FR-46 (L687), FR-50 (L720) | |
| 153 | L115, L118 | "Self-service door lock: Set per sauna"; "Source of door codes: Set per door" | captured | FR-45 (L676) | |
| 154 | L116-L117 | Remote door control; a door in open mode outside a window | intentionally left in brief addendum | §4.17 (L746) | Vision. |
| 155 | L119-L120 | "Temperature control: Off"; "External heater control: Off …" | captured | §9 (L817), §4.17 (L747) | Not built. |
| 156 | L121-L123 | Children distinction off; separate child price off; child age limit under 14 | captured | §9 (L824), §4.17 (L744) | |
| 157 | L124 | "Validity of gift cards and vouchers: One year from issue" | captured | Glossary Voucher (L142), FR-27 (L455), FR-43 (L659) | |
| 158 | L125-L132 | Memberships, period cards and their defaults (1 future booking, 50 per period, renewals above the limit on, automatic renewal on, whole-sauna member price on, no gift-card payment) | intentionally left in brief addendum | §4.17 (L745) | Vision. |
| 159 | L134 | "Already set by the administrator: time windows, capacity, prices, fill order, whole-booking-only windows, which saunas can be booked in full, and gift card denominations and limit" | captured | §4.4 (L298), §4.9 (L468), FR-38, FR-41, FR-43 | Seed data in the Core, screens in §4.13. IA §7 has no gift-card screen. |
| 160 | L136 | "A changed setting applies only to bookings made after the change; existing bookings keep the rules they were made under (… 72-hour … 48 hours)" | captured | FR-39 (L611-612) | The Cutoff is kept per Booking. Horizon, deadline and Release time apply when used (`[ASSUMPTION]`), which fits the rule. |
| 161 | L136 | [ASSUMPTION: memberships and period cards already sold stay valid … if the administrator turns the offer off or changes prices] | intentionally left in brief addendum | none | Vision. |

### 7. Per-website settings (L138-L149)

| # | Input | Point (short quote) | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| 162 | L140 | "Not built in the first version … The architecture should leave room for them" | partially captured | NFR-2 (L757), §9 (L818) | The PRD follows the stricter Constraints line L196 ("not built or prepared beyond keeping the API clean"). The brief contradicts itself (L140 vs L196). Upkeep. |
| 163 | L142-L149 | Eight per-website items: registered websites with a key or domain, venue and saunas, branding, email sender and templates, time zone and currency, languages, terms and privacy, Administrator roles per website | intentionally left in brief addendum | §4.17 (L748) | One Vision line, with no pointer. |

### 8. Research input (L151-L178)

| # | Input | Point (short quote) | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| 164 | L153 | Research limits: "PostgreSQL only, no performance figure …, no sauna comparable …, lock behaviour … mostly through integrator and forum material" | captured | Add A (L8-12, L23), NFR-7 (L762), §12 Q4 (L885), Q8 (L889) | |
| 165 | L155 | "Decided (2026-10-29): … (E1, E3, H12, H21)" | captured | FR-13 (L284-285), FR-48 (L706), FR-50 (L729), Add B (L66, L75, L77) | |
| 166 | L161 | D7: "Seats move back so the fill-order rule holds again" | superseded by decision (PM-L27) | FR-40 (L627) | |
| 167 | L162 | D8: "Refused, or treated as a block" | superseded by decision (PM-L27) | FR-41 (L636), Add B (L70) | Refused. |
| 168 | L163 | D3: "The latest booking loses, whole bookings only, with refund or voucher; the administrator sees the list before confirming" | superseded by decision (PM-L27) | FR-40 (L620-625) | |
| 169 | L164 | F1: "Refused while a future window would exceed it, or handled like D3" | superseded by decision (PM-L27) | FR-38 (L595), Add B (L71) | Refused. Add B L71 says "The research gave no recommendation", but the brief lists one. Upkeep. |
| 170 | L165 | F2: "Applies to windows that have not started" | superseded by decision (PM-L27) | FR-38 (L596) | |
| 171 | L166 | F3: "No seat moves; the overbooking fallback applies" | superseded by decision (PM-L27) | FR-31 (L506), FR-40 (L628), FR-42 (L647) | |
| 172 | L167 | H6: "Accept the overlap and say so (or start validity at the window start); the codes must differ; the simulated lock rejects a duplicate PIN on a door" | superseded by decision (PM-L28) | FR-47 (L699-700), §12 Q1 (L882), Add C | Deferred. FR-47 L699 still adopts the "codes must differ / duplicate PIN rejected" half with no tag. That is harmless and fits Add C point 3. |
| 173 | L168 | H10: "Applies only to windows whose email is not yet sent" | superseded by decision (PM-L27) | FR-47 (L698) | |
| 174 | L169 | H11: "Send only when the lock confirms the code; alert the administrator …; delete expired codes" | partially captured | FR-49 (L711-717) | Adopted as `[ASSUMPTION]` and not in PM-L27's decided list, although the brief asks the PRD to decide. Gap 12. |
| 175 | L170 | H13: "Correction email …; where a door's codes are online, also replace the code; mark per door whether its codes can be replaced" | superseded by decision (PM-L27) | FR-45 (L676), FR-48 (L707) | |
| 176 | L171 | H14: "Extra email with the code" | partially captured | FR-48 (L708) | `[ASSUMPTION]`, not decided. Gap 12. |
| 177 | L172 | H15: "'Must not be used' is a request; replacing the code is best effort" | partially captured | FR-48 (L709) | `[ASSUMPTION]`, not decided. Gap 12. |
| 178 | L173 | H23: "Refused while any future window has a split booking" | superseded by decision (PM-L27) | FR-50 (L730) | |
| 179 | L174 | Heating I11 to I23 | intentionally left in brief addendum | §12 Q13 (L894), §4.17 (L747) | |
| 180 | L176 | "when the hold is built, it is stored with an expiry and ignored once expired, even if cleanup has not run" | captured | §4.11 (L548), Add A (L36) | |
| 181 | L176 | "payment callbacks are idempotent; a seat change is atomic and cannot interleave with a whole-sauna booking" | captured | FR-6 (L223), FR-36 (L567), FR-26 (L445), FR-32 (L516-523) | |
| 182 | L176 | "serialization failures and deadlocks are retried a bounded number of times, then the guest gets a clean error; no speed or throughput figure …; any load-test target is set after measuring" | captured | FR-14 (L287-292), §4.3 NFR (L295), NFR-7 (L762), Add A (L9) | |
| 183 | L178 | "Run group C … as parallel tests. Add a model-based test … compares the derived formula with a brute-force reference" | captured | FR-32 (L520-523), FR-31 (L514), SM-5 (L872), Add A (L58) | The generator list leaves out Whole-sauna bookings, lifted Blocks and releases, which FR-31's own lead (L499) names. Cheap to add. |

### 9. Schedule and build order (L180-L188)

| # | Input | Point (short quote) | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| 184 | L184 | "one person, 27 October to 15 December 2026; two other exams, 16 November and 8 December; Claude tokens …; frontend, design and extensive testing are the likeliest overruns. Planning … 7 to 8 of the first 12 days" | captured | §8.2 (L810-812) | |
| 185 | L185 | Core (decided): "… with time windows, capacity and prices in the database, a free-text name, simulated instant payment, confirmation with a booking reference by email, the database enforcing that booked seats never exceed capacity, and the administrator as a password login with a booking list" | partially captured | §4.1-4.4, FR-10 (L263) | Everything is captured except "in the database": the PRD says "seed data" (L298, L759), and storage in the data store is only implied by FR-10. Same finding as reconcile-brainstorm.md Gap 2. Not ranked here. |
| 186 | L185 | Proposal: "no guest account; one booking page and one confirmation page" | partially captured | §7 (L781), FR-5 (L203-214) | The PRD adds a details-and-review page, on the legal basis in Add D (L113-116). Ranked in reconcile-brainstorm.md (Gap 5). |
| 187 | L185 | Proposal: "the browser's date picker; windows as a list with free seats" | captured | FR-2 (L174), FR-3 | Typing and keyboard use are added. |
| 188 | L185 | Proposal: "the simulated email as an outbox table, also shown on the confirmation page" | superseded by decision (PM-L25) | FR-8 (L243), FR-17 (L323-329), Glossary Outbox (L146) | The Guest sees only their own email, and the Outbox is for Administrators only. |
| 189 | L185 | Proposal: "one seeded administrator account" | captured | FR-15 (L306) | |
| 190 | L186 | Build order: "database engine, schema and the capacity invariant; a thin end-to-end booking first …; the rest of the core with tests written in each story; administrator login and list" | captured | Add I (L270-282), NFR-6 (L761) | Still marked unconfirmed in Add I. |
| 191 | L186 | "a freeze from 9 to 15 December for tests, README (test users, sample data, how to start the frontend) and the AI-use documentation, with no new features"; the work windows | captured | §8.2 (L813), DR-1 (L796-799), DR-2 (L800-805), Add I (L277-278) | |
| 192 | L187 | "small stories with acceptance criteria taken from the brief, a token budget per story logged in the session log …, mechanical tasks at lower effort" | captured | DR-1 (L798), Add I (L280-281) | Story ACs taken "from the brief" rely on test IDs that the brief does not carry (Gap 9). |
| 193 | L187 | "one stylesheet with a Finnish-inspired palette, laptop layout first, … mobile layout last in step 2 …, no design system" | captured | §4.6 (L388), FR-22 (L397), FR-51 | Palette per PM-L30. |
| 194 | L187 | "test depth on concurrency, capacity, validation and criterion 1, breadth only for the rest" | captured | NFR-6 (L761), SM-C1 (L876) | |
| 195 | L188 | "The 'My booking' page only resends the link …; Individual seats never get a cash refund" | captured | FR-34, §4.8 (L426), Add G (L238-239) | |

### 10. Constraints, exam, security and personal data (L190-L206)

| # | Input | Point (short quote) | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| 196 | L192 | "Delivery by 15 December 2026, by one person" | captured | §8.2 (L810), §1 (L33) | |
| 197 | L193 | "No licensed, trademarked, copyrighted or otherwise protected material … AI-generated or freely licensed, unless the author has found or invented something and checked it" | captured | DR-3 (L806), §6 (L770) | |
| 198 | L194 | "Website and platform in English; more languages may be added later" | captured | NFR-5 (L760), §4.17 (L749) | |
| 199 | L195 | "Python backend, JavaScript frontend. Specific frameworks are left to the architecture phase" | captured | §8.2 (L814) | |
| 200 | L196 | "The booking platform must be separate from the website … a single API … one website only … no website registration, no per-website keys or settings" | captured | NFR-2 (L757), §9 (L818) | |
| 201 | L200 | "Documentation must show how AI was used and how the students quality-assured the code" | captured | DR-1 (L796-799), §1 (L33) | |
| 202 | L204 | "protected against hacking, and all personal data in particular" | captured | §4.5 (L331-385) | |
| 203 | L204 | "the documentation should state what is stored, why, and how it is protected" | partially captured | FR-21 (L376-380) | The privacy notice covers what is stored, why, the legal basis, retention and rights. Nothing requires stating how the data is protected. **Gap 7.** |
| 204 | L206 | "hashed passwords, input validation against injection and cross-site scripting, role-based access" | captured | FR-18, FR-19, FR-20 | |
| 205 | L206 | "protection against brute-force login attempts" | partially captured | FR-15 (L308) | Administrator sign-in only (the architecture sets the thresholds). Guest sign-in (FR-37) has none. **Gap 7.** |
| 206 | L206 | "up-to-date dependencies" | captured | NFR-8 (L763) | |
| 207 | L206 | "storing only the data needed" | captured | FR-21 (L375) | FR-21 leaves out the guest-account password hash that §4.12 will store. |
| 208 | L206 | "security tests as part of quality assurance" | captured | §4.5 (L332), SM-2 (L867) | |

### 11. Concurrency tests (L208-L220)

| # | Input | Point (short quote) | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| 209 | L210 | "automated tests that run bookings in parallel … The cases about holds … apply once the hold is built; without it, the confirm case and the free-seats case are tested" | captured | FR-11, FR-35, NFR-6 (L761) | |
| 210 | L214 (CT-1) | "Two guests hold the last free seat at the same moment": "Exactly one hold succeeds …" | captured | FR-35 (L557) | If time 5. |
| 211 | L215 (CT-2) | "Two guests confirm …": "Exactly one booking … not charged (simulated), and gets no confirmation email" | captured | FR-11 (L269-270) | |
| 212 | L216 (CT-3) | "Zero, never negative. The administrator sees one booking, not two" | captured | FR-11 (L269) | |
| 213 | L217 (CT-4) | "The first guest's hold expires and the second guest then books": succeeds | captured | FR-35 (L558) | |
| 214 | L218 (CT-5) | "A payment completes after the hold has expired, and the seat was taken": "No booking … refunded" | captured | FR-36 (L566) | |
| 215 | L220 | [ASSUMPTION: "repeats the race many times, for example 100 … against the same storage the platform uses"] | captured | FR-11 (L271), NFR-6 (L761) | 100 is still tagged. "Same storage" is promoted into NFR-6, which is sensible. |
| 216 | L220 | "The overbooking fallback is a safety net …: in these cases the losing booking is never created" | captured | FR-11 (L270), FR-42 (L647) | |

### 12. Input validation tests (L222-L236)

| # | Input | Point (short quote) | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| 217 | L224 | "validates every input on the server … a rejected request changes no data (no hold, booking or payment)" | captured | FR-18 (L337, L340) | |
| 218 | L228 (IV-1) | "Seat count is zero, negative, fractional, not a number, or above the free seats" | captured | FR-18 (L341), FR-2 (L175), FR-12 | Adds "above 10" (PM-L32). |
| 219 | L229 (IV-2) | "Date or time window is malformed, does not exist, or is outside the booking horizon or past the booking deadline" | captured | FR-18 (L342) | The scope for Whole-sauna and Change requests is not explicit (Gap 5). |
| 220 | L230 (IV-3) | "Required field is missing, or an unknown field is sent" | captured | FR-18 (L343) | |
| 221 | L231 (IV-4) | "Text (name, email, notes) is empty, far too long, or has the wrong format" | captured | FR-18 (L344), FR-5 (L207) | There is no notes field ("Nothing else is asked"). A stray notes field is covered by IV-3. |
| 222 | L232 (IV-5) | "SQL injection strings, script tags or HTML": "Never run or shown as markup" | captured | FR-18 (L345), FR-16 (L321) | |
| 223 | L233 (IV-6) | "Administrator input is invalid, for example a negative price or capacity, or a window that ends before it starts" | captured | FR-18 (L346) | In the Core this means seed data. |
| 224 | L234 (IV-7) | "A guest sends an administrator request": "Rejected as not allowed (role-based access)" | captured | FR-20 (L364-367) | RB-1 and RB-2 cover the substance, but no FR cites IV-7, although §4.5 (L332) lists IV-1 to IV-7. Gap 9. |
| 225 | L236 | [ASSUMPTION: the exact limits (maximum text lengths, maximum seats per booking) are set in the PRD] | superseded by decision (PM-L32) | FR-2 (L170), FR-5 (L207) | 10 Seats is decided ("maks 10 plasser per booking"). The text limits are still `[ASSUMPTION]`. |

### 13. Password tests (L238-L250)

| # | Input | Point (short quote) | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| 226 | L240 | "Success Criterion 9 also requires hashed administrator passwords and strong passwords for user accounts" | partially captured | FR-19 (L348-358), SM-2 (L867) | **Gap 1.** |
| 227 | L244 (PW-1) | "An administrator account is created or its password changed": "Only a salted hash from a slow password-hashing algorithm is stored; … never stored, logged or returned by the API" | partially captured | FR-19 (L349, L352), FR-15 (L306) | The hash rule is captured. No FR or command creates an Administrator or changes a password, so "created or changed" has no tested path beyond seeding. **Gap 1.** |
| 228 | L245 (PW-2) | "A user (guest) account is created with a weak password …": "Rejected …; no account is made" | partially captured | FR-19 (L353-357), FR-37 (L578) | Runs only with §4.12 (If time 6), yet SM-2 counts every PW case in the Core. **Gap 1.** |
| 229 | L246 (PW-3) | "A user account is created with a strong password": "Accepted, and stored hashed" | partially captured | FR-19 (L357), FR-37 (L578) | As PW-2. |
| 230 | L247 (PW-4) | "No password can be read …, and the same password gives different hashes" | captured | FR-19 (L352) | |
| 231 | L248 (PW-5) | "wrong password is refused with an error that does not say whether the email exists" | partially captured | FR-15 (L307) | Administrators only. FR-37 (guest sign-in and sign-up) does not repeat it. **Gap 7.** |
| 232 | L250 | [ASSUMPTION: "strong" … "at least 12 characters and not on a list of common passwords, following current guidance rather than forced mixes"] | superseded by decision (PM-L32) | FR-19 (L353-356) | At least 15 characters, a blocklist and no composition rules ("passord minst 15 tegn med blokkliste og uten tegnkrav"). |
| 233 | L250 | "the hashing algorithm (for example Argon2id or bcrypt) is an architecture decision" | captured | Add A (L48) | Add A recommends Argon2id. |
| 234 | L250 | "Guest accounts are optional, so the strong-password rule applies only to those who create one" | captured | FR-19 (L357) | The PRD extends the rule to Administrators. |

### 14. Role-based access tests (L252-L265)

| # | Input | Point (short quote) | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| 235 | L254 | "checks the caller's role on the server for every request, whatever the website shows" | captured | FR-20 (L361), NFR-2 (L757) | |
| 236 | L258 (RB-1) | "called without logging in": "Refused as not logged in; nothing changes" | captured | FR-20 (L365) | |
| 237 | L259 (RB-2) | "called by a logged-in guest": "Refused as not allowed" | captured | FR-20 (L366), FR-37 (L581) | Only with §4.12, yet SM-2 counts it in the Core (Gap 1). |
| 238 | L260 (RB-3) | "called by a logged-in administrator": "Allowed" | captured | FR-20 (L367) | |
| 239 | L261 (RB-4) | "A guest opens, changes or cancels another guest's booking, by account or by guessing a booking reference or link": "Refused; … does not reveal whether the booking exists" | captured | FR-20 (L368), FR-8 (L245), FR-25 (L436), FR-37 (L580) | In the Core: the reference alone opens nothing. |
| 240 | L262 (RB-5) | "An account-less guest uses the link from their own confirmation email": "Allowed for that booking only" | captured | FR-25 (L431), FR-20 (L368) | Comes with §4.8 (If time 2), yet SM-2 counts it in the Core (Gap 1). |
| 241 | L263 (RB-6) | "A guest account tries to change its own role": "Refused" | captured | FR-20 (L369), FR-37 (L582) | Only with §4.12 (Gap 1). |
| 242 | L265 | "The link … carries a long, random token … the booking reference alone gives no access" | captured | FR-25 (L434), FR-8 (L245) | At least 128 bits, stored hashed. |

### 15. HTTPS tests (L267-L278)

| # | Input | Point (short quote) | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| 243 | L269 | "Success Criterion 9 also requires encrypted connections … v1 proves it with automated tests" | superseded by decision (PM-L26) | §4.7 (L411-423), §10.1 (L840, L843) | HTTPS is If time 1. The Core has three tested measures ("kjernen har tre testede sikkerhetstiltak"). |
| 244 | L273 (HT-1) | "plain HTTP …": "Redirected to the HTTPS address; no data is returned or changed over HTTP" | captured | FR-24 (L420) | |
| 245 | L274 (HT-2) | "Carries a Strict-Transport-Security header" | captured | FR-24 (L421) | |
| 246 | L275 (HT-3) | "session cookie is marked Secure and HttpOnly, and is never sent over HTTP" | captured | FR-24 (L422) | |
| 247 | L276 (HT-4) | "The change-or-cancel link starts with https://" | captured | FR-24 (L423) | Broadened to every link in an email. |
| 248 | L278 | [ASSUMPTION: "the tests use a local development certificate; the certificate setup for a real deployment … is an architecture decision"] | captured | §4.7 (L412) | Promoted with no tag. Harmless. |

### 16. Open-question sections (L280-L324)

| # | Input | Point (short quote) | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| 249 | L282 | Answered for individual seats: fill order, split groups, total free seats, same per-person price, "after a cancellation, seats move into earlier saunas from the saunas filled last", the late whole-sauna rule | captured | FR-29, FR-31 (L510-511) | A2, A3. |
| 250 | L284 | "'Moves are allowed at any time' was replaced on 2026-10-29" | captured | FR-31 (L506), Add G (L242) | |
| 251 | L286 | Open: placement under concurrent bookings, stored or derived, goes to the architecture | captured | §12 Q4-Q5 (L885-886), FR-32 | |
| 252 | L290-L294 | Gift cards answered; a shared coupon mechanism is "still an architecture decision" | captured | FR-28 (L463), FR-43 to FR-44 | |
| 253 | L298-L304 | Door codes answered; H cases open | captured | FR-45 to FR-50; rows 110-136 and 172-178 | "Replaced on 2026-10-29" (no new email for a move) fits FR-50. |
| 254 | L308-L312 | Booking without an account answered | captured | FR-25, §4.12 (L570) | |
| 255 | L316-L324 | Memberships and period cards answered | intentionally left in brief addendum | §4.17 (L745) | Vision. |

---

## Special attention

### A. Brief [ASSUMPTION]s and what the PRD did with them

| Brief [ASSUMPTION] | PRD handling | Tagged or in §13? | Decided? | Verdict |
|---|---|---|---|---|
| L53: "off" means the seats never open | FR-41 L638 | no | PM-L29 | Fine (decided) |
| L56: the deadline applies to Whole-sauna bookings and to Changes into the Window | Only the generic FR-18 L342 | no | no | Generalised silently and left incomplete (Gap 5) |
| L57: the horizon is counted from the moment of booking | Glossary L137 definition | no | no | **Promoted silently** (Gap 5) |
| L57: the horizon applies to Whole-sauna bookings and Changes; the Administrator can see Windows further ahead | Not explicit | no | no | Partly missing (Gap 5) |
| L62: token lifetime and hashing are PRD decisions | FR-25 L434-437 | n/a | PM-L32 | Fine (decided) |
| L63: a Block covers every overlapping Window | FR-40 L619 | yes (§13 L916) | no | Fine |
| L63: the Administrator sees affected Bookings before confirming | FR-40 L620 | no | PM-L27 | Fine (decided) |
| L63: refund or Voucher, regardless of Cutoffs | FR-40 L624-626 | no | PM-L27, PM-L32 | Decided, but the flow is missing (Gap 3) |
| L63: Seats move to other open Saunas where there is room | FR-40 L621 (D2) | no | Implied by PM-L27 (D3) | Acceptable |
| L63: lift a Block, and the Sauna is bookable again | FR-40 L616, L627 | no | PM-L27 (D7) | Fine (decided) |
| L63: the calendar shows Windows, Bookings and Blocks together | none | n/a | no | **Missing** (Gap 8) |
| L63: the override is chosen per Block (door codes, heating) | FR-46 L689 states the outcome only | no | no | Incomplete (Gap 8) |
| L73: every Sauna has a self-service lock | none | n/a | no | Missing (Gap 12) |
| L73: one-Sauna access with no lock: the email names the Sauna without codes | none | n/a | no | **Missing** (Gap 6) |
| L73: code source per door | FR-45 L676 | no | no | Promoted silently; low risk |
| L73: an Administrator-entered code can be edited until the email is sent | none | n/a | no | Missing (Gap 12) |
| L73: alert when a code is missing | FR-49 (as H11) | yes | no | Fine |
| L73: one-Sauna placement is first-fit, whole Bookings only | none | n/a | no | **Missing** (Gap 6) |
| L220: about 100 repetitions, against the same storage | FR-11 L271 (tagged), NFR-6 L761 | partly | no | Fine |
| L236: exact limits are set in the PRD | FR-2 (decided), FR-5 (tagged) | yes | PM-L32 for Seats | Fine |
| L250: "strong" = at least 12 characters, a blocklist, no forced mixes | FR-19 L353-356 | n/a | PM-L32 (15 characters) | Fine (decided) |
| L278: local development certificate | §4.7 L412 | no | no | Promoted silently; harmless |
| L64: changing the standard length leaves existing Windows alone | none | n/a | n/a | Moot in v1 |
| Vision [ASSUMPTION]s (L73 remote doors, L77, L81, L85, L89, L136) | none | n/a | n/a | Left in brief addendum |

### B. Numbers compared

| Item | Brief addendum | PRD | Verdict |
|---|---|---|---|
| Password minimum | "for example at least 12 characters" (L250) | 15, with at least 64 allowed (FR-19 L354) | superseded by decision (PM-L32) |
| Max Seats per booking | "set in the PRD" (L236) | 10 (FR-2 L170, FR-18 L341) | Decided in PM-L32 |
| Text limits | "set in the PRD" (L236) | Name 1-100, email up to 254 (FR-5 L207) | `[ASSUMPTION]`, indexed |
| Booking deadline | 5 min after the start; "earlier or later, also before the start" (L56) | 5 min; "may be set earlier, even before the start" (FR-39 L605) | **"Later" dropped; no upper bound** (Gap 5) |
| Booking horizon | 4 weeks (L57, L97) | 4 weeks (FR-39 L604) | Same |
| Cutoffs | 12 h and 72 h, not under 2 h (L60, L99-L100) | Same (FR-39 L606-607) | Same |
| Release time | 06:00, every Sauna not booked whole (L53, L101) | 06:00, Whole-booking-only Saunas only (FR-41) | superseded by decision (PM-L29) |
| Hold | 10 min, fixed (L58) | 10 min, fixed (FR-35) | Same |
| Window length | 1 h 30 (L64, L109) | 1 h 30 (FR-38 L594) | Same |
| Send time | 20 min (L73, L111) | 20 min (FR-47 L696) | Same |
| Voucher and gift-card validity | 1 year (L60, L61, L124) | 1 year (FR-27, FR-43) | Same; Q11 flags the legal risk |
| Child age | under 14 (L54, L123) | under 14 (§4.17 L744) | Same (Vision) |
| Gradual-opening maximum | All saunas (L113) | none stated (FR-50 L724) | Missing (Gap 12) |
| Race repetitions | "for example 100" (L220) | 100 (FR-11 L271) | Same, tagged |
| Resend limit | "limited" (L62) | 5 per hour per email and per source address (FR-34 L544) | New number, tagged |
| Period cards | 1 future booking; 50 per period (L127-L128) | none | Left in brief (Vision) |
| New in the PRD | none | Token of at least 128 bits; 12-month retention; 14-day Gift-card withdrawal; 1366×768, 1920×1080 and 360 px; 24×24 px targets | Tagged where inferred, or sourced in Add A or Add D |

### C. Brief test cases and their FR coverage

- **CT-1 to CT-5:** all five covered (FR-11, FR-35, FR-36). Group C is covered by FR-32, and the model-based test by FR-31.
- **IV-1 to IV-7:** all covered in substance. IV-7 is never cited (FR-20 carries it). Whole-sauna and Change requests are not named for IV-2 (Gap 5).
- **PW-1 to PW-5:** PW-1's "password changed" has no FR. PW-2 and PW-3 run only with §4.12. PW-5 is stated for Administrators only. SM-2 nevertheless counts every PW case in the Core (Gap 1).
- **RB-1 to RB-6:** all covered, but phased: RB-5 comes with §4.8, RB-2 and RB-6 with §4.12. SM-2 still counts them in the Core (Gap 1).
- **HT-1 to HT-4:** all covered by FR-24 (If time 1, decided in PM-L26).
- **Catalogue group G** (one-Sauna access): FR-50 does not mention it; only Add A L59 does (Gap 6).
- **Test IDs:** IV-n, PW-n, RB-n, HT-n and CT-n exist only in the PRD. The brief addendum tables (L212-L218, L226-L234, L242-L248, L256-L263, L271-L276) are unnumbered, so every citation depends on row order (Gap 9).

---

## Gaps that matter, ranked

Ranked by impact on UX, architecture and epics, with near-term phases weighted above Step 2.

### Gap 1 (high): SC9 cannot be proven in the Core the way SM-2 claims

- **Evidence:**
  - The brief Core includes "hashed passwords and role-based access with tests" (B-L17).
  - SC9 requires "strong passwords for user accounts" (B-L240), and "there can be one or more administrator accounts" (B-L62).
  - The PRD defers PW-2 and PW-3 to §4.12 (FR-19 L357), and RB-2 and RB-6 likewise (FR-20 L366, L369). RB-5 needs the Manage link (§4.8).
  - The Core has only a seeded Administrator (FR-15 L306). No FR creates an Administrator or changes a password, so PW-1's "created or changed" has no path beyond the seed.
  - Even so, SM-2 (L867) says "All validation, password and access-control cases pass (IV, PW, RB)", and §10.1 (L840) counts SC9 (without HTTPS) as Core done.
- **Impact:**
  - SC9 is a Core success criterion and SM-2 a primary metric, and the examiner checks both.
  - In the epics, no story owns account creation or password change, and the PW/RB tests have no home in the Core.
- **Fix:**
  1. Add to FR-15: "Administrator accounts are created, and their passwords changed, only through the seed or a documented command that applies FR-19. The API never returns a password. The README shows the command." PW-1 to PW-3 then run in the Core against Administrator accounts.
  2. Rewrite SM-2 by phase: "Core: IV-1 to IV-7, PW-1 to PW-5 (Administrator accounts), RB-1, RB-3, RB-4 (reference only). With §4.8: RB-5, RB-4 (link). With §4.12: RB-2, RB-6, and PW-2 and PW-3 for guest accounts. With §4.7: HT-1 to HT-4."
  3. Log in .memlog that the Core proves "strong passwords for user accounts" on Administrator accounts.

### Gap 2 (high): A partial Seat move has no defined result

- **Evidence:**
  - The brief lets a Guest change Seats "one at a time, for example 1 of 4, or all together, e.g. to a different time window" (B-L60).
  - FR-26 (L442) allows moving "some or all Seats".
  - But FR-9 (L248, decided in PM-L32) says "Each Booking covers exactly one Window", and §4.8 (L426) calls a Change "a cancellation plus a new booking".
  - Nothing says whether moving 1 of 4 Seats creates a new Booking (reference, Manage link, email), how the price and the Cutoff carry over, or what the original link then shows.
- **Impact:**
  - **Architecture:** the booking data model (a Booking per Window, references, tokens) is fixed now.
  - **UX:** what the Guest sees after a split.
  - **Epics:** FR-26 is in If time 2, the first feature after HTTPS.
- **Fix:**
  - Add to FR-26: "Moving only some Seats splits the Booking. The moved Seats become a new Booking in the target Window, with its own Booking reference and Manage link, emailed at once. The original Booking keeps its reference and link, with fewer Seats. Both keep the price per Seat paid and the original Booking's Cutoff. Moving all Seats moves the Booking and keeps its reference."
  - Add a split case to UJ-4 and to the FR-31 model-based test.
  - If Lisa would rather allow only whole moves, that contradicts B-L60 and must be logged as a decision.

### Gap 3 (high): The refund-or-Voucher choice after a venue-caused cancellation has no flow

- **Evidence:**
  - In the brief, the overbooking loser "is refunded" (B-L59). For Blocks, the brief assumes "a full refund or a voucher, as they choose" (B-L63).
  - PM-L32 made the choice general ("ved Saunalöylys avlysning velger gjesten refusjon eller voucher").
  - FR-40 (L625-626) says Guests are "emailed a choice". FR-42 (L645-646) says "Each Guest chooses", yet its single email "says either … refunded … or … the Voucher is attached", which assumes the choice is already made.
  - Nothing says how the Guest chooses, by when, or what happens without a choice.
  - The Manage link only "shows the Booking until its Window ends" (FR-25 L435). After an F3 fallback inside a started Window, that leaves minutes to choose.
- **Impact:**
  - **UX:** a choice page and a two-step email sequence.
  - **Architecture:** a "cancelled, remedy pending" state; a token that outlives the Window; an idempotent choice; a refund record.
  - **Epics:** FR-40 and FR-42 cannot be accepted without these.
- **Fix:**
  - Add to FR-42, and reference it from FR-40 and FR-33: "The cancellation email links to a remedy page (Manage-link token) with two actions, Refund and Voucher. The link works for 30 days, even after the Window ends. The choice is made once. With no choice in 30 days, a Simulated refund is made `[ASSUMPTION]`; refund as the default fits the unfair-terms note (Add D L124). The Administrator sees pending and chosen remedies. A second email confirms the refund (with the 'few days' text) or delivers the Voucher."
  - Rewrite FR-42 L646 to match.

### Gap 4 (medium-high): FR-29's condition list contradicts Whole-booking-only and ignores Holds

- **Evidence:**
  - The brief allows a Whole-sauna booking whenever "no individual seat is placed in that sauna" (B-L51). Whole-booking-only exists so that a group can book the Sauna whole (B-L52). Held Seats are "hidden from other guests" (B-L58).
  - FR-29 (L480) requires "Seats booked ≤ Room ahead" with no exception.
  - So an unreleased Whole-booking-only Sauna is refused whenever Seats are booked and it is not last in the Fill order. Example: Sauna 1 is marked, and 5 Seats sit in Sauna 2; Room ahead of Sauna 1 is 0, so 5 > 0 and Sauna 1 is refused. This contradicts FR-29's own consequence (L489).
  - Held Seats are left out, so a Whole-sauna booking can take capacity that another Guest is holding.
  - Add A (L28-32) has the right formula, but the requirement does not.
- **Impact:**
  - **Architecture:** Add A L21 asks for one capacity function.
  - **Tests:** catalogue B with Whole-booking-only marks, and the Hold vs Whole-sauna race.
  - **Epics:** the FR-29 and FR-41 ACs.
- **Fix:**
  - Replace FR-29's third condition with: "Seats booked, plus Seats held once §4.11 exists, are no more than its Room ahead. An unreleased Whole-booking-only Sauna skips this test, because it holds no Seats."
  - Add the consequence: "With Sauna 1 marked Whole-booking-only and 5 Seats booked, Sauna 1 can be booked whole."

### Gap 5 (medium): The scope and bounds of the Booking horizon and deadline are not stated

- **Evidence:**
  - The brief assumes the deadline and the horizon apply to Whole-sauna bookings and to Changes into a Window, that the horizon is counted from the moment of booking, and that the Administrator can still create and see Windows further ahead (B-L56, B-L57).
  - The PRD applies them only to the Seat flow (FR-2 L173, FR-3 L184) and generically in FR-18 (L342). FR-26 (L442), FR-29 (L477-480) and FR-33 (L526) do not mention them.
  - "Counted from the moment of booking" became a Glossary definition (L137) with no tag.
  - FR-39 (L605) dropped "or later" and gives no upper bound, so a deadline after the Window ends would pass IV-6.
- **Impact:**
  - **UX:** the Change and Private-sauna screens must list only bookable Windows.
  - **Architecture:** one availability rule for every way of taking capacity.
  - **Tests:** IV-2 for each endpoint, and IV-6 for the setting.
- **Fix:**
  - Add to FR-39: "The Booking horizon and Booking deadline apply to Seat bookings, Holds, Whole-sauna bookings and the target Window of every Change."
  - Add that condition to FR-29.
  - Change the deadline's limit in FR-39 to: "earlier or later than the default, never after the Window ends".
  - Add to FR-38: "The Administrator can create and see Windows beyond the Booking horizon."
  - Add both brief assumptions to §13, or confirm them with Lisa and log the answer.

### Gap 6 (medium): One-Sauna access is under-specified and clashes with INV-5 and "never told a Sauna"

- **Evidence:**
  - The brief assumes first-fit placement of whole Bookings, compaction by whole Bookings, a door-code email that names the Sauna, and a named Sauna without codes when it has no lock (B-L49, B-L73).
  - FR-50 (L727-730) has three bullets and none of these rules.
  - FR-31 (L506) exempts one-Sauna access from INV-5 only after the Send time. Whole-Booking placement breaks INV-5 earlier: with Sauna 1 = 7 and Sauna 2 = 10, a 5-Seat Booking goes to Sauna 1, and a 3-Seat Booking must then go to Sauna 2 while Sauna 1 still has 2 free.
  - FR-4 (L192), FR-31 (L513) and the Glossary (L132) say Guests are never told a Sauna, which contradicts the email that names it.
  - Catalogue group G (Add A L59) is not referenced in FR-50.
- **Impact:**
  - **Architecture:** the derived Placement recommended now cannot express this mode. Add A L22 already expects a "placed in Sauna" column, and the invariant set and the model-based test change.
  - **UX:** the email content.
  - **Epics:** the Step 2 ACs.
- **Fix:**
  - Add to FR-50: "A Seat booking is placed whole in the first Sauna open for Seats, in Fill order, that has room for all its Seats. With Gradual opening on, the next Sauna opens if none has room. Otherwise the request is refused for lack of room. Before the Send time, compaction moves whole Bookings only. INV-5 is replaced, for example by INV-5G: no Booking fits wholly in the free room of an earlier open Sauna. The door-code email names the Sauna; for a Sauna without a self-service lock, it names the Sauna and gives no codes. Catalogue group G holds the acceptance cases."
  - Add "except under one-Sauna access (FR-50)" to FR-4, FR-31 and the Glossary's Placement entry.

### Gap 7 (medium-low): Security documentation and guest-account sign-in

- **Evidence:**
  - The brief says the documentation should state "what is stored, why, and how it is protected" (B-L204). It also asks for brute-force protection (B-L206), and PW-5 requires login errors that do not reveal whether an email exists (B-L248).
  - FR-21 (L376-380) leaves out how data is protected.
  - Throttling (FR-15 L308) and the identical error message (FR-15 L307) apply to Administrators only. FR-37 (L578-583) has neither, and sign-up can reveal which emails are registered.
- **Impact:** The exam documentation for SC9 (DR-1), and the If time 6 epics.
- **Fix:**
  - Add to FR-21: "The privacy notice, or a security section in the README, states how data is protected: Argon2id hashing, server-side role checks, Manage-link tokens stored hashed, HTTPS status, and no third-party requests." List the guest-account password hash.
  - Add to FR-37: "Sign-in is throttled as in FR-15. A wrong email or password gives the same message (PW-5). Sign-up does not reveal whether an email already has an account."

### Gap 8 (medium-low): What the blocking calendar shows, and the per-Block door-code override

- **Evidence:**
  - The brief assumes the calendar "shows windows, bookings and blocks together" and that the override is chosen per Block (B-L63).
  - The PRD names a blocking calendar (UJ-6 L104, §4.13 L586) and tells the UX workflow to sketch it first (§7 L791), but states no content for it.
  - FR-46 (L689) refers to a "door-code override" that no FR lets the Administrator set. IA §7 (L790) lacks it too.
- **Impact:**
  - **UX:** the first screen to be sketched has no content requirement.
  - **Epics:** the Step 2 override story is missing.
- **Fix:**
  - Add to FR-40: "The blocking calendar shows, for a chosen period, each Window with Seats booked and Seats left, each Sauna's Whole-sauna booking or Whole-booking-only mark, and each Block."
  - Add to FR-45: "Per Block, the Administrator can turn on a door-code override. The Blocked Sauna then gets codes that only the Administrator sees and shares (H4)."
  - Add both to IA §7.

### Gap 9 (medium-low): The test IDs the PRD cites do not exist in the brief addendum

- **Evidence:**
  - The PRD cites IV-n, PW-n, RB-n, HT-n and CT-n in §4.5 (L332), FR-11, FR-15, FR-18 to FR-20, FR-24 and FR-35 to FR-37.
  - The brief addendum tables are unnumbered, so the IDs depend on row order.
  - IV-7 is never mapped to an FR.
- **Impact:**
  - **Epics:** story ACs are taken "from the brief" (B-L187). A miscount or a reordered row breaks the trail (DR-4).
- **Fix:**
  - Add a section K to the PRD addendum with one row per ID: brief addendum line, expected result in short, FR, phase.
  - Cite IV-7 at FR-20.
  - Upkeep: number the rows in the brief addendum.

### Gap 10 (low-medium): The Step 2 order changed without a decision

- **Evidence:**
  - The brief addendum puts "Gradual opening and one-sauna access" first in Step 2 (B-L19). brief.md (L69-73) leaves them out.
  - The PRD follows brief.md and makes them modes inside Door codes, after Gift cards (§10.2 L856, FR-50).
  - Add H (L255) notes the difference, but there is no PM line.
- **Impact:** The Step 2 epic sequence. One-Sauna access also changes the placement model (Gap 6).
- **Fix:** Ask Lisa, log the answer in .memlog, then align brief addendum L19 or brief.md.

### Gap 11 (low-medium): The Private-sauna routes were reinterpreted without a decision

- **Evidence:**
  - The brief has a Sauna-centred list: "a list of free private saunas and their time windows", reached by two routes (B-L36-L38).
  - FR-30 (L492-495) and UJ-5 (L95-96) put the Window first and the Sauna second.
  - Add G (L247) says the brief's direct route meant "automatic Sauna assignment" and replaces it "(PRD assumption)". The brief never mentions assignment.
- **Impact:** The UX of the Private-sauna entry screen, and the FR-30 ACs.
- **Fix:**
  - Confirm with Lisa. If the brief stands, write in FR-30: "The Private sauna page lists, for the chosen date, each Sauna that can be booked whole with its free Windows. The Guest picks a Window in that list, or opens a Sauna and picks a Window there."
  - Correct Add G L247, or log the decision.

### Gap 12 (low): Step 2 details for door codes and gradual opening

- **Send time:** add to FR-47 "The Administrator can change the Send time (default 20 minutes); H10 applies", and add the setting to IA §7. Source: B-L73, brief.md L72.
- **Editing a code:** add to FR-45 "An Administrator-entered code can be changed until its email is sent" (B-L73 `[ASSUMPTION]`).
- **Locks in the seed:** state that every Sauna has a self-service lock, in §12 Q3 or FR-45 (B-L73 `[ASSUMPTION]`).
- **Gradual opening, default maximum:** "All saunas" (B-L113), in FR-50.
- **Gradual opening, extra email:** only when a Sauna opens after the Send time (B-L73); fix FR-50 L726.
- **Gradual opening, large groups:** a Booking bigger than the room left in the open Saunas should open the next Sauna, up to the maximum. As written (B-L50, FR-50), a group bigger than the free room cannot book until the open Sauna fills.
- **Open decisions:** H11, H14, H15 and the one-Sauna forced-move rule are still `[ASSUMPTION]`, although the brief asks the PRD to decide them (B-L73, B-L157). Confirm them and log the answers.
- **Gift cards:** add an Administrator screen for denominations and the limit to IA §7.

---

## Upkeep outside the PRD (not PRD gaps)

- **Brief addendum L19:** "moved-sauna emails" is stale, because BM-L120 superseded the new-email-on-move rule.
- **Brief addendum L62:** "the link is sent again" should read "a new link is sent and the old one stops working" (PM-L32).
- **Brief addendum L140 vs L196:** one says "the architecture should leave room" for per-website settings, the other "not built or prepared beyond keeping the API clean". Pick one.
- **Test tables:** the IV, PW, RB, HT and CT tables need row IDs (Gap 9).
- **Points already listed in Add H:** the 06:00 wording (L53, L101), the Step 2 order (L19 vs brief.md) and the refund-only overbooking remedy (L59).
- **PRD addendum B L71:** it says "the research gave no recommendation" for F1, but brief addendum L164 lists one ("Refused … or handled like D3").
- **PRD §4.17:** add one line pointing to the brief addendum subsections for the Vision rules (Membership, Period cards, Renewal, Heater, remote door control, per-website settings).
