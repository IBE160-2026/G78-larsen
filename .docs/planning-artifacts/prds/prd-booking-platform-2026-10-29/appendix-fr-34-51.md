---
title: "Saunalöyly Booking Platform — PRD appendix: FR-34 to FR-51"
status: final
created: 2026-11-19
updated: 2026-11-19
---

# PRD appendix: FR-34 to FR-51 (specified, not planned)

This appendix belongs to `prd.md` in the same folder. It holds §4.10 to §4.16, moved out of the PRD on 2026-11-19 so that the main document shows only what is planned (§10). The requirements are unchanged and fully specified, but they have no epics or stories in this round (§10.3). §4.9 was moved back into the PRD the same day, when it was planned (PRD §10.1). Sections and FRs keep their numbers, so references such as "§4.13" or "FR-40" in the PRD and in downstream documents point here. The Glossary (PRD §3) applies, and the assumptions tagged here are indexed in PRD §13.

### 4.10 "My booking" link resend *[If time — 4]*
**Description:** A Guest who has lost the email enters the Booking reference and their email. If both match, a fresh Manage link is sent to that email. The page itself shows no Booking data, and it answers the same way whether or not anything matched. Realizes UJ-4.

**Functional Requirements:**

#### FR-34: Resend the Manage link
A Guest can ask for a new Manage link by giving the Booking reference and email. Realizes UJ-4.

**Consequences (testable):**
- The response is the same for matching and non-matching input.
- On a match, a new Manage link is emailed (Outbox), and the previous one stops working (FR-25).
- Requests are limited per email address and per source address `[ASSUMPTION: 5 per hour for each]`.
- The reference and email alone never open a Booking.

### 4.11 Seat Hold during payment *[If time — 5]*
**Description:** When the Guest presses **Continue booking** on Book seats after choosing a Window and Seats, those Seats are held for a fixed 10 minutes while the Guest enters details, accepts the terms and pays. The hold length is not a Setting. A Hold is stored with its expiry time and stops counting when it expires, whether or not any cleanup has run. A Hold does not by itself prevent double booking: the atomic check of FR-10 still applies when the Booking is confirmed. Payment stays synchronous (FR-6), so the Booking is created in the same step that records the charge.

**Functional Requirements:**

#### FR-35: Hold Seats for 10 minutes
When a Guest presses **Continue booking** on Book seats, the chosen Seats are held for that Guest for 10 minutes.

**Consequences (testable):**
- Held Seats are left out of other Guests' Seats left until the Hold expires or ends.
- A Hold ends at the earlier of 10 minutes after it was made and the Booking deadline of its Window, so a Hold never lets a Guest book past the deadline.
- If two Guests try to hold the last Seat at once, exactly one Hold succeeds and the other Guest holds nothing (CT-1).
- After a Hold expires, another Guest can book those Seats (CT-4).
- A browser session has at most one Hold per Window. Going back and choosing another number of Seats resizes that Hold in one step and keeps the Seats already held; if the extra Seats are not free, the old Hold stays and the Guest is told. Holds per source address are limited `[ASSUMPTION: the architecture sets the limit]`.
- The Guest pressing Cancel releases the Hold at once. A failed payment keeps it until it expires, so the Guest can try again (FR-7).
- The Guest is not told about the Hold: no page or email mentions it or shows a time limit. Other Guests see held Seats as taken, with no comment (Lisa, 2026-10-30; addendum M).
- With cleanup switched off, an expired Hold no longer reduces Seats left.
- Expiry never discards what the Guest has entered. The Guest can still pay, and FR-36 decides the outcome. `[NOTE FOR PM]` This keeps the fixed 10 minutes compatible with WCAG 2.2.1 (adjustable time limits); addendum A explains why.

#### FR-36: Payment after a Hold expires
A payment that completes after its Hold expired creates a Booking only if the Seats are still free and the Booking deadline has not passed.

**Consequences (testable):**
- A payment that completes after expiry while the Seats are still free and the Booking deadline has not passed creates exactly one Booking.
- If the Seats are no longer free, or the Booking deadline has passed, no Booking is created, nothing is charged, and the Guest is told why (CT-5; addendum M).
- When a late payment for an expired Hold runs in parallel with another Guest's Hold or payment for the same last Seat, exactly one of them gets the Seat. The other gets no Booking and is not charged.
- A repeated submission never creates two Bookings or two charges (FR-6). A test switch can hold the Simulated payment until after the Hold has expired, as FR-7 does for failure.

### 4.12 Guest accounts *[If time — 6]*
**Description:** A Guest can create an optional account and see their own Bookings. Booking without an account works exactly as before. Bookings made without an account are not attached to an account created later.

**Functional Requirements:**

#### FR-37: Optional Guest account
A Guest can create an account, sign in and sign out, and see the Bookings made with that account.

**Consequences (testable):**
- A Guest signs up with an email and a password that meets FR-19 `[ASSUMPTION: Guests sign in by email, as Administrators do]`.
- Sign-in is throttled as in FR-15 (PW-6), and a wrong email or password gives the same message (PW-5). Sign-up does not reveal whether an email already has an account: the reply is the same, and the account is confirmed through a link emailed to the address (Outbox). A password is reset the same way, by an emailed link.
- The choice to sign in appears after **Continue booking** on Book seats, before Details. Continuing without an account is the default and the most prominent option.
- A signed-in Guest:
  - sees only the Bookings made while signed in to that account (RB-4);
  - cannot reach Administrator functions (RB-2);
  - cannot change their own role (RB-6);
  - books with the account's email.
- Booking, paying and using the Manage link work the same with or without an account.

### 4.13 Administrator tools and Venue rules *[If time — 7, the last part of v1]*
**Description:** The Administrator gets screens to manage Windows, Capacity, prices, the Fill order and which Saunas can be booked whole. The Administrator can also adjust the five Settings, keep a blocking calendar, and mark Saunas Whole-booking-only for a Window. The Overbooking fallback is the safety net for capacity lost after Bookings exist. Realizes UJ-3 and UJ-6.

**Functional Requirements:**

#### FR-38: Manage Windows, Capacity, prices and Fill order
An Administrator can create and edit Windows, set each Sauna's Capacity, the price per Seat and the price per Sauna for Whole-sauna bookings, and choose which Saunas can be booked whole and the Fill order.

**Consequences (testable):**
- New Windows get the standard length of 1 h 30 min. A single Window may have another length across the whole Venue. An overlapping Window is refused (FR-13).
- A Capacity decrease is refused while any Window that has not started would then have more Seats booked and held than its Seat capacity (case F1). It never applies to a Window that has started.
- A new Fill order applies to Windows that have not started (F2).
- A price change applies only to new Bookings. Existing Bookings keep the price paid. A Guest who has reached the review page is charged the price shown there, even if the price changes meanwhile.
- A Window that has Bookings or Holds cannot be deleted or moved in time. Its Saunas can be Blocked instead (FR-40).
- The Administrator can create and see Windows beyond the Booking horizon.
- Windows are created one at a time. The seed supplies the standard programme (FR-13), and v1 has no recurring schedule (Vision; Lisa, 2026-10-30).

#### FR-39: Five Settings
An Administrator can change five Settings. Every other rule is fixed in v1.

| Setting | Default | Limit |
|---|---|---|
| Booking horizon | 4 weeks before the Window starts | never more than 1 month |
| Booking deadline | 5 minutes after the Window starts; may be set earlier (even before the start) or later | never later than 45 minutes before the Window ends |
| Cutoff, Seat bookings | 12 hours before the start | not under 2 hours |
| Cutoff, Whole-sauna bookings | 72 hours before the start | not under 2 hours |
| Release time (06:00 rule) | 06:00 on the day of the Window; can be set to another time or turned off | never later than the Booking deadline of the Window it applies to |

**Consequences (testable):**
- A changed Cutoff applies only to Bookings made after the change. Existing Bookings keep the Cutoff they were made under.
- A changed Booking horizon, Booking deadline or Release time applies from the moment of the change to every Window it has not yet affected `[ASSUMPTION: these rules are applied when a booking or release happens, not stored per Booking]`.
- The Booking horizon and Booking deadline apply to Seat bookings, Holds, Whole-sauna bookings and the target Window of every Change `[ASSUMPTION: as in the brief]`.
- A change that sets the Booking horizon to more than 1 month is refused (Lisa, 2026-11-03).
- A change that sets the Booking deadline later than 45 minutes before the end of a standard 1 h 30 min Window, that is, more than 45 minutes after its start, is refused. For a Window of another length (FR-38), the earlier of the setting and 45 minutes before its end applies `[ASSUMPTION: rule for Windows of another length]`.
- The Release time is never later than the Booking deadline of a Window with a Whole-booking-only Sauna that has not been released (FR-41). A Release time is a clock time and a Booking deadline belongs to a Window, so the limit is checked per Window `[ASSUMPTION: the limit is checked per Window, not as one global time]`:
  - a change that sets the Release time later than such a Window's Booking deadline is refused, and the message names the Windows;
  - a change that sets the Booking deadline earlier than the Release time of such a Window is refused in the same way;
  - with the Release time turned off, the limit does not apply.
- With the default Settings, SC1 to SC4 behave as this PRD describes, and so do SC5 and SC6 once Step 2 is built (SC8). The tests of §4.1 to §4.12 pass unchanged.

#### FR-40: Blocks
An Administrator can Block one, several or all Saunas for a period, and can lift a Block. Realizes UJ-6.

**Consequences (testable):**
- A Block affects every Window that overlaps its period, using half-open intervals `[ASSUMPTION: half-open intervals]`. A Blocked Sauna cannot be booked whole and holds no Seats. A Block never changes a Window that has ended, even when its period reaches into the past.
- The blocking calendar shows, for a chosen period, each Window with its Seats booked and Seats left, each Sauna's Whole-sauna bookings and Whole-booking-only marks, and each Block.
- Before confirming, the Administrator sees each affected Window, how many Seats will be counted into other Saunas, and any Booking that would lose its place. The Block is applied only if the Bookings and Holds that would lose their place are still the ones the Administrator saw. Otherwise nothing is applied and a new preview is shown.
- Blocking Sauna 2 in an empty Window lowers Seat capacity and Seats left to 34 (D1).
- With Windows 15:00–16:30 and 16:30–18:00, a Block from 16:30 to 17:00 affects only the second. The first ends exactly when the Block starts (D5, rewritten so that the Windows do not overlap).
- Seats in the Blocked Sauna are counted into other Saunas that are open for Seats, later ones included, where there is room. No Guest is affected (D2).
- If Seat capacity falls below the Seats booked and held, the latest Seat bookings lose (D3):
  - Holds that no longer fit end first, newest first, and their Guests hold nothing (FR-35). Seat bookings then lose by Entry time, the latest first, then the next, until the rest fit `[ASSUMPTION: as many lose as needed]`. A Whole-sauna booking never loses its place this way (decided 2026-10-30);
  - each losing Booking is cancelled in full, regardless of Cutoffs;
  - each Guest chooses a refund or a Voucher, as in FR-42.
- A Whole-sauna booking of a Blocked Sauna is cancelled regardless of its Cutoff, with the same choice (D4).
- Lifting a Block counts Seats again so that INV-5 holds (D7).
- A Block in a Window that has started counts Seats again like any other Block. The Overbooking fallback applies only if Seats booked exceed the new Seat capacity. F3's "no moves after the start" applies only where Placement is visible to Guests. In this PRD that happens only in Vision, under one-Sauna access and for heating (this reading of F3 confirmed by Lisa, 2026-10-30).
- When every Sauna is Blocked, the Window is not offered, and every Booking in it is cancelled as above (D6).

#### FR-41: Whole-booking-only Saunas and the Release time
An Administrator can mark a Sauna in a Window as Whole-booking-only, and remove the mark.

**Consequences (testable):**
- While the Sauna is marked and not released, it is not open for Seats: it is left out of Seat capacity and Seats left, and it can be booked whole.
- Marking is refused while Seats are placed in the Sauna in that Window, held Seats included (D8). Marking a Sauna that is not Bookable whole is refused. Marking is also refused if the Release time (when on) is later than the Window's Booking deadline (FR-39).
- At the Release time on the day of the Window, a marked Sauna that is not Whole-sauna-booked becomes open for Seats and takes its place in the Fill order. Seats are counted again so that INV-5 holds. The release is a condition checked against the data store's clock (NFR-11), so it takes effect even if the platform was off at the Release time.
- With the Release time turned off, a marked Sauna is never released.
- The Release time never falls after a Window's Booking deadline (FR-39), so a marked Sauna is always released while its Window can still be booked. Release is therefore never skipped for that reason (decided 2026-10-31, Lisa).

#### FR-42: Overbooking fallback
If the Seats booked in a Window ever exceed its Seat capacity, the Seat booking with the latest Entry time loses.

**Consequences (testable):**
- The Seat booking with the latest Entry time is cancelled in full, and as many more as needed, latest first. A Whole-sauna booking never loses its place this way.
- The Guest is emailed an apology with a link to the Remedy page, where they choose once between a refund and a Voucher. In Step 2 the email also says that any Door codes received must not be used.
- The remedy link works for 30 days, even after the Window has ended. The 30 days are a condition checked as in NFR-11. With no choice in 30 days, a Simulated refund is made `[ASSUMPTION: refund as the default, in line with the unfair-terms note in addendum D]`.
- A second email confirms the choice: either the refund, which may take a few days to arrive, or the Voucher.
- The Administrator sees each cancelled Booking with its remedy: pending, refunded or Voucher.
- The same remedy flow serves every cancellation that Saunalöyly causes (FR-40).
- A refund goes back the way each part was paid (FR-28): a Voucher-funded part returns as a Voucher, never as money.
- In normal operation, FR-10 and FR-32 keep Bookings from exceeding capacity. The fallback applies whenever Seats booked exceed Seat capacity afterwards, most of all after a Block that leaves too little capacity (FR-40: D3, D6).

### 4.14 Gift cards *[Step 2 — 1]*
**Description:** Anyone can buy a Gift card without an account and pay by Simulated payment. It is emailed to the buyer as a code they can print or forward. Whoever holds the code can use it to pay for Seat bookings and Whole-sauna bookings, with or without an account. Success criterion SC5.

**Functional Requirements:**

#### FR-43: Buy a Gift card
Anyone can buy a Gift card without an account.

**Consequences (testable):**
- The buyer chooses a fixed value, or an amount up to a limit. The Administrator sets the fixed values and the limit.
- The Administrator can list the Gift cards sold, with each card's value, balance and expiry date.
- The email shows the code, the value and the expiry date (one year after issue), and states that a Gift card is not paid out in money.
- Before purchase, the buyer is told about the 14-day right of withdrawal for Gift cards `[ASSUMPTION: legal reading; angrerettloven § 22 m exempts date-bound bookings but does not cover undated Gift cards]`.

#### FR-44: Pay with a Gift card
Whoever holds a Gift card code can use it to pay for a Booking.

**Consequences (testable):**
- A Gift card pays for all or part of a Booking, and the rest is paid by Simulated payment. The remaining balance stays on the card until it expires.
- An expired or used-up card is refused. No fees are charged after sale.
- Two simultaneous uses of one card never spend more than its balance.

### 4.15 Door codes *[Step 2 — 2]*
**Description:** For Saunas with a self-service lock, each door gets its own Door code for each Window, shared by everyone allowed through that door. At the Send time, the booker of each Booking receives one email with the codes for exactly the doors they may use, and shares them with their group. The locks are simulated. No rule depends on taking back a code already sent, because many real locks cannot do that. Catalogue group H holds the detailed acceptance cases, apart from H19 to H23, which belong to one-Sauna access (Vision). Success criterion SC6.

**Functional Requirements:**

#### FR-45: Doors, locks and code sources
An Administrator can register the doors of each Sauna and mark which Saunas have a self-service lock. For each door, the Administrator chooses whether codes are entered by hand or supplied by the simulated lock system, and whether a sent code can be replaced.

**Consequences (testable):**
- A Sauna without a self-service lock never produces a Door code.
- The code source and the "replaceable" mark are stored per door, and the Administrator can see them.
- A code the Administrator enters can be changed until its email is sent `[ASSUMPTION: as in the brief]`.
- For each Block, the Administrator can turn on a door-code override. The Blocked Sauna then gets codes that only the Administrator sees (H4).
- In the seed data, every Sauna has a self-service lock `[ASSUMPTION: as in the brief]`.

#### FR-46: Who receives which codes
Each booker receives the Door codes for exactly the doors their Booking allows.

**Consequences (testable):**
- A Whole-sauna booker receives the codes of that Sauna only (H2).
- A Seat booker receives the codes of every Sauna that is open for Seats in the Window (H1). With Gradual opening, only Saunas already opened give codes (FR-50). A Seat booker never receives the code of a Sauna that is Whole-sauna-booked, Blocked, or Whole-booking-only and not released (H2, H3).
- A Sauna without a self-service lock gives no code (H5).
- A Blocked Sauna with the door-code override gives its code to the Administrator only (H4).
- A Guest who gives up all Seats before the Send time receives no codes (H7).

#### FR-47: Send time and validity
Door codes are emailed at the Send time and are valid until the Window ends.

**Consequences (testable):**
- The Administrator sets the Send time. By default, codes are emailed 20 minutes before the Window starts, and they are valid from the Send time until the Window ends (H8). The Send time is no earlier than the Cutoff for Seat Changes (12 hours before the start) and no later than the Window start.
- A Booking made after the Send time, and Seats moved into the Window after it, receive the email at once (H9). A Whole-sauna move follows FR-48.
- A changed Send time applies only to Windows whose email has not been sent (H10).
- A new code differs from every code still stored on that door, and the simulated lock rejects a duplicate PIN on a door.
- `[NOTE FOR PM]` With back-to-back Windows, two codes are valid on one door during the 20 minutes before the second Window starts (H6). This is undecided; see §12 Q1 and addendum C.

#### FR-48: Rules that never depend on revoking a code
No Door-code rule depends on taking back a code already sent.

**Consequences (testable):**
- After the Send time, a Whole-sauna booking of a Sauna is refused while Seat bookers hold its code. In the default mode, that means while the Window has any Seat booking and the Sauna is open for Seats (H12).
- Whenever a Sauna stops being open for Seats after the Send time (Block, Whole-booking-only mark), every Seat booker of the Window gets a correction email naming the codes to use. For a Block, where the Sauna's door allows it, its code is also replaced (H13).
- Whenever a Sauna becomes open for Seats after the Send time (lifted Block, release, removed mark, cancelled Whole-sauna booking whose Sauna is not Blocked, Gradual opening), every Seat booker of the Window gets an extra email with its code `[ASSUMPTION: H14 as in the brief, widened to every way a Sauna becomes open]`.
- When a Booking is cancelled after the Send time, its email says that the codes must not be used `[ASSUMPTION: H15 as in the brief]`. A shared code is replaced only on doors marked replaceable. When it is, every remaining holder receives the new code before the old one stops working. Otherwise no code is replaced.

#### FR-49: Codes are sent only when the lock confirms them
A Door code is emailed only after the lock confirms it `[ASSUMPTION: H11 as recommended]`.

**Consequences (testable):**
- If a code is not confirmed by the Send time, the Administrator is alerted, and the email goes out as soon as the code is confirmed.
- The Administrator can see the codes of every Window and resend them.
- Expired codes are deleted from the lock after the Window.
- A test switch can hold a code in the pending or failed state.

#### FR-50: Gradual opening
An Administrator can turn on Gradual opening, an optional access mode that is off by default (H16 to H18).

**Consequences (testable):**
- Saunas open for Seats one at a time in the Fill order, up to a maximum the Administrator sets (default: all Saunas). Seat capacity counts every Sauna that may open, up to the maximum, so a Booking larger than the room left in the open Saunas is accepted and opens as many next Saunas as it needs. Whether a Sauna is opened decides only which Door codes are sent.
- A Sauna emptied by cancellations closes again. Before the Send time it is free for a Whole-sauna booking; after it, FR-48 applies (H18).
- When a Sauna opens after the Send time, every Seat booker of the Window gets an extra email with its code (H17, FR-48).
- Turning the mode on, or lowering the maximum, is refused while a future Window would have more Seats booked than the Seat capacity it would then have. It applies only to Windows whose Door-code email has not been sent.

### 4.16 Mobile layout *[Step 2 — 3, last]*
**Description:** The website also works on a phone-sized screen and at any window size, with the same stylesheet. This closes the Reflow exception of FR-23 and completes SC10.

**Functional Requirements:**

#### FR-51: Mobile and any window size
Guests and Administrators can use the website on a phone-sized screen and at any window size, with the same stylesheet. This is the mobile part of SC10.

**Consequences (testable):**
- Every page works without horizontal scrolling from 320 px wide upward, and FR-23 holds at every width, including 1.4.10 Reflow. The exception in FR-23 ends here.
