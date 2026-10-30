---
title: "Saunalöyly Booking Platform"
status: draft
created: 2026-10-29
updated: 2026-10-30
---

# PRD: Saunalöyly Booking Platform
*Working title. On 2026-10-21 the venue name Saunalöyly had no hit in EUIPO TMview, and navnesok.no showed it as possibly free as a trademark. A check of existing "LÖYLY" marks is still open (§12, Q10).*

## 0. Document Purpose

This PRD states what the Saunalöyly booking platform and its website must do. It is written for Lisa (owner and sole builder), for the examiner who follows the trail from plan to finished app, and for the downstream workflows: UX, architecture, and epics and stories.

It builds on these sources and does not repeat them:
- the product brief and its addendum, `.docs/planning-artifacts/briefs/brief-booking-platform-2026-09-20/`. The full rule tables and the security test cases (IV, PW, RB, HT and CT) live there;
- the teacher's feedback on the brief, `tilbakemelding-product-brief.md` in the same folder (2026-10-06);
- the minimal-v1 brainstorm, `.docs/brainstorming/brainstorm-minste-v1-mvp-2026-10-27/`;
- three research reports under `.docs/planning-artifacts/research/`: concurrency and seat holds (2026-10-27), the seat capacity model with its 85-example catalogue (2026-10-28), and smart-lock door codes (2026-10-28). Catalogue examples are cited by ID, for example A6, B1 or D3. The catalogue is in `.docs/planning-artifacts/research/technical-kapasitetsmodell-enkeltplasser-2026-10-28/research.md`, and the architecture and the stories need it as an input.

The brief addendum's test tables are unnumbered. This PRD numbers their rows in order (IV-1 to IV-7, PW-1 to PW-5, RB-1 to RB-6, HT-1 to HT-4 and CT-1 to CT-5), and addendum K maps each test to its FR. Where this PRD and the brief addendum differ, this PRD rules for v1 (addendum H lists the differences).

Supporting material is in `addendum.md` next to this file: technical direction for the architecture, the alternatives behind each research-based decision, legal notes, comparable services and aesthetic references.

How to read it: every domain noun is defined once in the Glossary (§3) and used verbatim, capitalised. Features (§4) carry a delivery label and nest globally numbered FRs (FR-1 to FR-51) with testable consequences. Cross-cutting requirements are in §5. Inferences that Lisa has not confirmed are tagged `[ASSUMPTION: …]` inline and indexed in §13; real tensions are flagged `[NOTE FOR PM]`.

**Delivery order (decided):** the v1 **Core** comes first. The whole **If time** list follows, still part of v1, in the order of §10. **Step 2** comes after that, with the mobile layout last. **Vision** items are not built. A success criterion that is not reached is reported as not delivered.

## 1. Vision

Saunalöyly is a fictional, Finnish-inspired sauna venue with four or more saunas, and this platform is how guests reserve a place in it. A guest picks a day and the number of seats, sees at once which time windows have room and what it will cost, and pays. No account is needed, no help is needed, and nothing on the page tries to rush them. Alternatively, a group can take a whole sauna for itself. The website feels like the sauna it sells: calm, honest and plain, in light wood, forest green, birch white and sky blue, with real Finnish sauna rooms and their traditional tools in view.

The hard part is not the booking form. Individual seats and whole-sauna bookings draw on the same physical rooms. The platform must never sell a seat twice, never sell a sauna that guests are already booked into, and keep its numbers right when two people press Pay in the same second or an administrator closes a sauna for repairs. This PRD bets on one idea: **if the capacity rules are precise enough to test, one person can deliver a booking core that never oversells, and then grow it feature by feature without rewrites.** Every rule below is therefore written as a testable consequence. The riskiest rules are proven with parallel automated tests rather than argued.

The platform is a learning project: an exam submission for IBE160 (group G78), built by one person between 27 October and 15 December 2026, planned with BMAD and implemented with Claude Code. Payment, email and door locks are simulated, and heating is not built at all. The platform is built so that it could grow into a real service, but it does not pretend to be one. Its value for assessment is a working, AI-built application together with an honest record of how AI was used and how the result was checked. If it became a real service, it would compete on price, appeal and features. Its differences would be a Finnish-inspired identity for people who already like saunas, and seats and private saunas in one system. Neither is proven: the exam version tests no prices and no demand.

## 2. Target User

Guests are people who already enjoy Finnish saunas, and people who are curious to try one. Regulars want availability and price within a few clicks. First-timers also need to know what to expect, how to behave and how to stay safe, which the "Before you come" section answers. The Administrator runs the Venue: Windows, Capacity, prices and who is coming.

### 2.1 Jobs To Be Done
- **Guest:** "I want to see in seconds whether there is room for us on Saturday afternoon, and what it will cost in total."
- **Guest:** "Once I have paid, I want to be certain the seats are mine, not find a double booking at the door."
- **Guest:** "If plans change, I want to move my booking or get credit without writing to anyone." *(If time)*
- **Group:** "We want the sauna to ourselves." *(If time)*
- **Administrator:** "I want to see who is coming to each window and how full it is, without doing arithmetic."
- **Administrator:** "I want the system to refuse anything that would break capacity, so I never have to turn a paying guest away at the door."
- **Administrator:** "When a sauna needs repair, I want to close it and have the affected guests handled by clear rules." *(If time)*

### 2.2 Non-Users (v1)
- **The examiner.** The examiner evaluates the product and runs it locally from the README. There are no examiner features (teacher's feedback, 2026-10-06).
- **Vision-only users:** members and period-card holders, children as a separate guest type, and other venues and websites.

### 2.3 Key User Journeys
*Protagonist names are placeholders `[ASSUMPTION: no named personas exist in the sources; Lisa may replace them]`. Prices are illustrative: the seed prices are still open (§12, Q3).*

- **UJ-1. Ingrid books two seats for Saturday afternoon.** *[Core]*
  - **Persona + context:** Ingrid has tried a public sauna once and wants to take a friend. She does not want to create an account.
  - **Entry state:** She is anonymous, on a laptop, and arrives at the landing page.
  - **Path:**
    1. She chooses **Book seats**, picks Saturday and sets 2 seats.
    2. The page lists Saturday's Windows with the Seats left in each and the total for 2 seats. A Window with only 1 seat left is shown as unavailable, labelled "1 seat left".
    3. She picks 15:00–16:30 and enters her name and email.
    4. A review page repeats the Window, the seats and the total (NOK 500 at an example price of NOK 250 per seat) and says that a booking for a fixed date cannot be withdrawn.
    5. She accepts the terms and presses **Pay NOK 500**.
  - **Climax:** The confirmation page shows her Booking reference, the Window, 2 seats, the total, and the confirmation email exactly as it was sent.
  - **Resolution:** She has a reference and an email she can keep. The Window now shows 2 fewer Seats left.
  - **Edge case:** If someone took the last seats while she was typing, she is told how many Seats are actually left and is offered the nearest Windows with room for 2. Nothing is charged.

- **UJ-2. Aino and Jonas reach for the last seat at the same moment.** *[Core]*
  - **Persona + context:** Both want the last seat on Friday 18:00–19:30, which shows 1 Seat left.
  - **Entry state:** Both are anonymous, and both are on the review page with 1 seat.
  - **Path:** Both press Pay within the same second.
  - **Climax:** Exactly one of them gets a confirmation. The other is told that no seat is left, is not charged and gets no email.
  - **Resolution:** The Window shows 0 Seats left, and the Administrator's list shows one new Booking.

- **UJ-3. Katja checks who is coming tonight.** *[Core]*
  - **Persona + context:** Katja runs the evening shift at the Venue.
  - **Entry state:** She is not signed in and is on the Administrator sign-in page.
  - **Path:**
    1. She signs in with her email and password.
    2. She opens today's booking list. It shows the Windows in time order, each with its Seat capacity, Seats booked and Seats left, and under each Window its Bookings with reference, name, email, seats and total.
    3. She opens the Outbox to check that a guest's confirmation went out.
  - **Climax:** She sees at a glance that 18:00–19:30 is full and that 20:00–21:30 has 9 Seats left.
  - **Resolution:** She signs out. A Guest who types the Administrator address is refused.

- **UJ-4. Ingrid's friend falls ill.** *[If time]*
  - **Persona + context:** On Friday morning, more than 12 hours before the Window, Ingrid needs only one of her two seats.
  - **Entry state:** She has the confirmation email with its Manage link.
  - **Path:** She opens the link, chooses to give up 1 of her 2 Seats, and confirms.
  - **Climax:** The page confirms the change and shows the email with her Voucher, worth one seat and valid for one year.
  - **Resolution:** The freed Seat can be booked by others at once. Later she uses the Voucher to pay for another visit.
  - **Edge case:** Within 12 hours of the start, the Manage link still shows the Booking, but every change is refused with the reason.
  - **Edge case:** If she has lost the email, she enters her Booking reference and email on the "My booking" page and is sent a new Manage link (§4.10).

- **UJ-5. Olav books a whole sauna for a family reunion.** *[If time]*
  - **Persona + context:** Olav wants privacy for 10 relatives on a Sunday morning.
  - **Entry state:** He is anonymous and on the landing page.
  - **Path:**
    1. He chooses **Private sauna** and picks Sunday.
    2. The page lists each Sauna that can be booked whole that day, with its size, price and free Windows. He picks 10:00–11:30 in the 12-seat Sauna 3.
    3. He reviews the booking and pays.
  - **Climax:** The confirmation names Sauna 3 and the Window. Nobody else can book Sauna 3, or a Seat in it, for that Window.
  - **Resolution:** Seats left for that Window drop by 12. He can cancel for a refund or a Voucher until 72 hours before the start.
  - **Edge case:** If the Seats already booked in that Window would no longer fit in the Saunas ahead of Sauna 3, Sauna 3 is not offered. Saunas later in the Fill order may still be.

- **UJ-6. Katja closes Sauna 3 for repairs.** *[If time]*
  - **Persona + context:** The stove in Sauna 3 needs repair next Tuesday from 14:00 to 17:00.
  - **Entry state:** She is signed in as Administrator, in the blocking calendar.
  - **Path:**
    1. She selects Sauna 3 and the period.
    2. Before confirming, she sees each affected Window, how many Seats will be counted into other Saunas, and any Booking that would lose its place.
  - **Climax:** She confirms. Seat bookings move into other open Saunas without the Guests noticing. Where capacity runs out, the latest Seat bookings are cancelled in full, and their Guests are emailed a choice between a refund and a Voucher.
  - **Resolution:** Sauna 3 shows as Blocked for those Windows, and Seats left reflects the lower capacity.

## 3. Glossary
*Every term is used verbatim and capitalised in this PRD and downstream. The phrase "whole booking" is never used, because it is ambiguous.*

- **Venue:** Saunalöyly, the one fictional sauna venue in v1. It has four or more Saunas.
- **Venue time:** local time at the Venue (Europe/Oslo). All times in this PRD are in Venue time.
- **Sauna:** one sauna room with a Capacity (changed only by an Administrator, FR-38) and one or more doors. All examples use this set: Sauna 1 = 7, Sauna 2 = 10, Sauna 3 = 12, Sauna 4 = 15 (44 in total).
- **Capacity:** the number of Seats a Sauna holds.
- **Window:** a bookable time slot that is the same for every Sauna in the Venue. The standard length is 1 h 30 min (for example 15:00–16:30). No two Windows overlap, and intervals are half-open, so 15:00–16:30 and 16:30–18:00 do not overlap. Identical and nested Windows overlap too.
- **Seat:** one guest's place in a Window. Seats are identical, and in the guest's view a Seat is not tied to any Sauna.
- **Seat booking:** a Booking of 1 to 10 Seats in one Window.
- **Whole-sauna booking:** a Booking of one entire Sauna for one Window. Guests see it as "Private sauna".
- **Booking:** a Seat booking or a Whole-sauna booking. A Booking has a Booking reference, the Guest's name and email, the price paid and a status, which is active or cancelled. A Change is kept as history on the Booking and is not a third status (FR-16).
- **Booking reference:** a short code that identifies a Booking in messages and lists. It gives no access on its own.
- **Change:** for a Seat booking, moving Seats to another Window or giving up Seats for a Voucher. For a Whole-sauna booking, cancelling it or moving it. Guests cannot cancel Seats for money.
- **Guest:** anyone who uses the public website to find a Window, make a Booking or buy a Gift card. A Guest is anonymous by default, or holds a Guest account (If time).
- **Guest account:** an optional account that lets a Guest see their own Bookings (If time, FR-37).
- **Seat booker:** a Guest who holds a Seat booking in a given Window.
- **Administrator:** a staff user with an Administrator account. The Core has one seeded Administrator; more can exist.
- **Open for Seats:** a Sauna is open for Seats in a Window when it is not Whole-sauna-booked, not Blocked, and not an unreleased Whole-booking-only Sauna. With Gradual opening (Step 2), a Sauna that may open but has not been opened still counts as open for Seats, and only Door codes depend on whether it has been opened (FR-46, FR-50).
- **Seat capacity:** for a Window, the sum of Capacity over the Saunas that are open for Seats. In the Core, this is the sum of all Capacities.
- **Seats left:** Seat capacity minus the Seats booked in the Window, and also minus the Seats held once Holds exist.
- **Fill order:** the order, set by the Administrator, in which Seats are counted into Saunas. Each Sauna is filled before the next.
- **Placement:** which Sauna each booked Seat is counted in. Placement is the platform's way of keeping count, not an assignment. Guests move freely between the Saunas open for Seats and are never told a Sauna.
- **Room ahead:** for a Sauna S in a Window, the summed Capacity of the Saunas that come before S in the Fill order and are open for Seats. The research writes this as P(S).
- **Block:** a period in which one or more Saunas cannot be booked and hold no Seats, for example during maintenance.
- **Bookable whole:** a standing mark, set by the Administrator on a Sauna (FR-38), that lets it be sold as a Whole-sauna booking at all. Whole-booking-only is a different mark, set per Window, and applies only to a Sauna that is Bookable whole.
- **Whole-booking-only:** an Administrator's mark on a Sauna in a Window. It keeps the Sauna out of Seat sales so that a group can book it whole.
- **Release time:** the time at which a Whole-booking-only Sauna that is still not Whole-sauna-booked becomes open for Seats. The default is 06:00 on the day of the Window. This is "the 06:00 rule".
- **Booking horizon:** how far ahead a Window can be booked. The default is 4 weeks before the Window starts, counted from the moment of booking.
- **Booking deadline:** the last moment a Window can be booked. The default is 5 minutes after it starts. It is never later than 45 minutes before the Window ends.
- **Cutoff:** the last moment a Guest can Change a Booking. The default is 12 hours before the start for a Seat booking and 72 hours for a Whole-sauna booking. It is never less than 2 hours.
- **Setting:** one of the five rules the Administrator can adjust (FR-39). Every other rule is fixed in v1. Step 2 adds the Send time, the Gradual-opening maximum and the Gift-card values, which the Administrator also sets.
- **Manage link:** the link in the confirmation email. It carries a long random token and is the only way back into a Booking for a Guest without an account (If time).
- **Voucher:** a credit issued by email in place of money. A Guest gets one when giving up Seats, or by choice when a Booking is cancelled. It is valid for one year from issue.
- **Gift card:** a purchased code with a balance, used like a Voucher (Step 2).
- **Hold:** a temporary reservation of Seats for 10 minutes, and never past the Booking deadline, while a Guest completes payment (If time). A Hold reserves Seats only; a Whole-sauna booking has none (FR-29).
- **Simulated payment:** a payment step that moves no real money and needs no keys or external service. Refunds are simulated in the same way.
- **Test switch:** a setting read at start-up from a local file that git ignores. It is off by default and can never be changed through the API. Tests use it to force a failed or held Simulated payment, a conflict, a pending code or a stopped Hold cleanup. The examiner can use it only by editing that file.
- **Outbox:** the platform's store of simulated emails. It stands in for the Guests' mailboxes, so it holds links and codes exactly as sent. Only Administrators can list it.
- **Overbooking fallback:** the rule that applies if Seats booked ever exceed Seat capacity: the Seat booking with the latest Entry time loses.
- **Entry time:** the moment a Seat booking's Seats entered their Window: the time the Booking was created, or the time of the Change that moved them in. A Change that moves only some Seats gives the new Booking the time of the move, and the original Booking keeps its Entry time.
- **Remedy page:** the page, reached by the link in the apology email (the remedy link), where a Guest chooses a refund or a Voucher (FR-42).
- **Door code:** a PIN for one Sauna door, valid for one Window (Step 2).
- **Send time:** when the Door codes for a Window are emailed. The default is 20 minutes before the Window starts (Step 2).

## 4. Features

### 4.1 Find a Window *[Core]*
**Description:** A Guest lands on a calm page. It says in a few lines what Saunalöyly is and offers one main action, **Book seats**. The Guest picks a date within the Booking horizon and the number of Seats, then sees that date's Windows, each with its Seats left and the total price for the chosen number. The Guest books Seats, never a particular Sauna, and the page says so. The **Private sauna** entry appears only once §4.9 is built. Realizes UJ-1 and UJ-2.

**Functional Requirements:**

#### FR-1: Landing page
A Guest can open the website without signing in and start a Seat booking in one step. Realizes UJ-1.

**Consequences (testable):**
- The landing page shows:
  - the Venue name and a short description;
  - the **Book seats** action;
  - links to the terms and the privacy notice;
  - a "Before you come" section on sauna etiquette and safety `[ASSUMPTION: the content beyond the two towels and the bathing rules; sources in addendum F]`:
    - etiquette: bring two towels, one of them to sit on; keep quiet; throw water on the stones with consideration for others; follow the swimwear rule;
    - safety: bring water and drink plenty; no alcohol; keep rounds to 5–10 minutes, and leave the sauna if you feel unwell; bathe with caution, and never take an ice bath alone; children are supervised by an adult;
    - practical: changing time is part of the Window;
    - the section can be linked to directly (FR-8).
- The website presents the Venue:
  - the Saunas as places to visit, each with one image and one line, worded so that a Seat booking never seems to choose one (FR-4);
  - opening hours and the Window schedule;
  - the price per Seat, and the price per Sauna once §4.9 exists;
  - the fictional address and contact details that FR-5 also shows.
- Choosing **Book seats** opens the date and Seat selection directly.

#### FR-2: Date and number of Seats
A Guest can choose a date and a whole number of Seats from 1 to 10. Realizes UJ-1.

**Consequences (testable):**
- A date can be chosen only if it has at least one Window inside the Booking horizon and before that Window's Booking deadline.
- The date can be typed as well as picked, and the date control works with the keyboard alone.
- A Seat number outside 1–10 cannot be submitted, and the server rejects it (FR-18).

#### FR-3: Windows with Seats left
For the chosen date and number of Seats, a Guest sees every bookable Window with its start and end, its Seats left, and the total price for the chosen number. Realizes UJ-1 and UJ-2.

**Consequences (testable):**
- Seats left equals Seat capacity minus Seats booked (FR-10), and matches the Administrator's booking list (FR-16).
- A Window with fewer Seats left than the Guest chose is shown as unavailable and cannot be selected. A text label such as "1 seat left" says so; colour alone never does.
- If no Window on the date has room, the page offers up to three of the nearest Windows that do, the same day first, then the following days within the Booking horizon `[ASSUMPTION: same day first, then the following days, at most three]`.
- A Window whose Booking deadline has passed is not offered.
- No countdown, "people viewing" count, padded number or other urgency cue appears. Any text about scarcity states the true current Seats left.
- The total shown equals the number of Seats times the price per Seat, in NOK including VAT, and is the amount charged.

#### FR-4: Seats, not Saunas
The Seat booking flow never asks the Guest to choose a Sauna and never shows which Sauna Seats are placed in. Realizes UJ-1.

**Consequences (testable):**
- No page or email in the Seat booking flow shows a Sauna identifier.
- The flow states in plain words that:
  - the Guest books Seats in the shared Saunas;
  - on site, the Guest may move freely between the Saunas that are open for Seats;
  - a group that wants to stay together should book a Private sauna (once §4.9 exists).

### 4.2 Book and pay for Seats *[Core]*
**Description:** After choosing a Window, the Guest enters a name and an email (no account and no password), reviews the Booking, and pays through a Simulated payment that succeeds at once. Checking Seats left, recording the Simulated payment and creating the Booking happen in one atomic step. The Simulated payment is instant, so nothing is held while the Guest types; Holds come with §4.11. The Guest then gets a confirmation page and a simulated email. Realizes UJ-1 and UJ-2.

**Functional Requirements:**

#### FR-5: Guest details and review
A Guest can enter a name and an email, and review the Booking before paying. Realizes UJ-1.

**Consequences (testable):**
- The name is free text of 1–100 characters, and the email is a valid address of at most 254 characters `[ASSUMPTION: text limits]`. Nothing else is asked.
- Before the pay button, either on the details page or on a separate review step, the Guest sees:
  - the Window, the number of Seats, and the total price in NOK including VAT;
  - the Venue's identity and contact details;
  - the booking terms, including that a booking for a fixed date has no right of withdrawal (angrerettloven § 22 m), and what the Guest can and cannot Change afterwards.
- Until §4.8 is built, the terms state that a Booking cannot be changed or refunded online.
- The Guest must accept the terms before paying. Links to the full terms and the privacy notice are present.
- Going back keeps everything the Guest has entered.

#### FR-6: Simulated payment creates the Booking
A Guest can pay with a Simulated payment, and a successful payment creates the Booking at once. Realizes UJ-1.

**Consequences (testable):**
- The pay button states both the obligation and the amount, for example "Pay NOK 500" (angrerettloven § 16).
- The platform runs with no payment credentials and no external payment service.
- The pay step, and every email that mentions a payment, carry the plain note "Simulated payment: no money moves" (Lisa, 2026-10-30).
- A successful payment reduces the Window's Seats left by exactly the number of Seats booked.
- The Simulated payment is synchronous in every phase (decided 2026-10-30): the charge is recorded in the same atomic step that creates the Booking, so a request that creates no Booking charges nothing.
- Each review page carries a one-time key. Submitting the same review twice (by double click, reload or retry) never creates two Bookings or two charges, and a repeat returns the first outcome: a Guest who was booked sees the confirmation again, never "no Seat free".

#### FR-7: Failed payment
A failed Simulated payment creates nothing. Realizes UJ-1.

**Consequences (testable):**
- A test switch can force the Simulated payment to fail.
- A failed payment creates no Booking, takes no Seats and sends no email. The Guest sees a message with a way to try again. Any Hold stays until it expires (FR-35).

#### FR-8: Confirmation page and email
After a successful Booking, the Guest sees a confirmation page and receives a simulated confirmation email. Realizes UJ-1.

**Consequences (testable):**
- The page and the email both show:
  - the Booking reference;
  - the date and Window;
  - the number of Seats and the total paid;
  - the Guest's email;
  - what happens next;
  - the booking terms;
  - a link to the "Before you come" section of the landing page (etiquette and safety).
- The email is stored in the Outbox. The confirmation page shows that email as sent. Which later emails a Guest sees is set in FR-17.
- The confirmation page opens only in the browser session that paid, and for as long as that session lasts `[ASSUMPTION: the confirmation page is tied to the paying browser session]`. A reload in that session shows it again.
- The Core confirmation contains no Manage link `[ASSUMPTION: the Manage link arrives with §4.8, when there is something to manage]`.
- The Booking reference alone opens nothing (FR-20).

#### FR-9: One Window per Booking
Each Booking covers exactly one Window. A Guest who wants several Windows makes several Bookings and pays for each separately. Realizes UJ-1.

**Consequences (testable):**
- A request for Seats in more than one Window is rejected as invalid input (FR-18).

### 4.3 Capacity integrity under concurrency *[Core]*
**Description:** Capacity is a hard guarantee, and the most heavily tested part of the product. However many requests arrive at once, the Seats booked in a Window never exceed its Seat capacity. In every phase, the data store itself refuses a write that would exceed it, as the brief requires (decided 2026-10-27, confirmed for every phase on 2026-10-30), so the guarantee does not rest on application code alone. A request either gets all the Seats it asks for or none. Realizes UJ-2.

**Functional Requirements:**

#### FR-10: Never exceed capacity
The Seats booked in a Window never exceed its Seat capacity, however many requests arrive at the same time. Realizes UJ-2.

**Consequences (testable):**
- N parallel requests for a Window may together ask for more Seats than are left. The Seats accepted never exceed the Seats left, and Seats left never goes below zero.
- In every phase, the data store refuses a write that would exceed Seat capacity even when the application's own check is bypassed. A test writes an over-capacity Booking straight to the data store, around the application, and expects the store to reject it. The store's view of Seat capacity changes together with the Whole-sauna booking, Block or mark that causes the change. How the store does this is an architecture decision (addendum A).

#### FR-11: The last-Seat race has exactly one winner
When two Guests request the last Seat at the same moment, exactly one Booking is created. Realizes UJ-2.

**Consequences (testable):**
- Two parallel requests for the one remaining Seat create exactly one Booking. Seats left becomes 0, never negative, and the Administrator sees one Booking (brief tests CT-2, CT-3).
- The losing Guest is told that no Seat is free, is not charged, receives no email and holds nothing. The page offers the nearest Windows with room (FR-3).
- The race test runs in every test run `[ASSUMPTION: 100 repetitions per run]`, against the same kind of data store the platform uses, not a mock.

#### FR-12: All or nothing
A request for more Seats than are left is rejected as a whole. Realizes UJ-1.

**Consequences (testable):**
- With 42 of 44 Seats booked, a request for 3 is rejected and nothing changes (catalogue A6). With all 44 booked, a request for 1 is rejected (A7).
- The message states how many Seats are actually left, and the page offers the nearest Windows with room (FR-3).

#### FR-13: Windows are Venue-wide and never overlap
Every Window applies to all Saunas, and no two Windows overlap. Realizes UJ-1.

**Consequences (testable):**
- Seed data or Administrator input with overlapping Windows is rejected: partly overlapping, identical and nested Windows alike. 15:00–16:30 and 16:30–18:00 are accepted (catalogue E1, E2).
- The seed creates Windows from the day it runs through the end of the Booking horizon, following a schedule held in the seed data `[ASSUMPTION: the seed generates Windows from the run date; the schedule itself is open, Q3]`. Running it again adds only the missing Windows and creates no duplicates, so a fresh clone has bookable dates whenever it is started.
- A Sauna that is unavailable for part of a Window is expressed as a Block. It never gets a different Window of its own (E3).
- Windows are independent: a booking, cancellation or Whole-sauna booking in one Window never changes another (E2, E4, E6).

#### FR-14: Temporary conflicts end cleanly
A request that meets a temporary conflict in the data store is retried a bounded number of times. If it still fails, the Guest gets a clear message and nothing is written. Realizes UJ-2.

**Consequences (testable):**
- "No seat free" (a definite loss) and "please try again" (retries used up) are different messages.
- A request that ends with either message leaves no Booking, charge, email or partial data.
- A test switch can make every attempt conflict. The request then ends with "please try again" and writes nothing.

**Feature-specific NFRs:**
- No throughput or latency figure is promised. If a load target is wanted, it is set only after measuring on the project's own machine.

### 4.4 Administrator sign-in, booking list and Outbox *[Core]*
**Description:** The seeded Administrator signs in with email and password and sees all Bookings by Window in a read-only list. Windows, Capacity and prices come from seed data, which creates the Windows relative to the day it runs (FR-13), and the Core has no editing screens. The Outbox shows every simulated email, so the Administrator can see what Guests were sent. So can the examiner, using the README's test login. Realizes UJ-3.

**Functional Requirements:**

#### FR-15: Administrator sign-in and sign-out
An Administrator can sign in with email and password, and sign out. Nobody else can sign in as an Administrator. Realizes UJ-3.

**Consequences (testable):**
- A seeded Administrator account exists, and the README documents its login (DR-2).
- Administrator accounts are created, and their passwords changed, only through the seed or a documented command. Both apply FR-19, so PW-1 to PW-3 can be tested on Administrator accounts in the Core. The API never returns a password.
- A wrong email and a wrong password give the same message (brief test PW-5).
- Repeated failed sign-ins are slowed or temporarily refused `[ASSUMPTION: the architecture sets the thresholds]`.
- After sign-out, the session no longer grants access.

#### FR-16: Booking list
A signed-in Administrator can list the Bookings of a chosen date, grouped by Window. Realizes UJ-3.

**Consequences (testable):**
- For each Window, the list shows `[ASSUMPTION: grouping by date and Window with totals; the sources say only "a simple list of bookings"]`:
  - its start and end;
  - its Seat capacity, Seats booked and Seats left;
  - each Booking's reference, name, email, Seats, total and time of booking.
- A new Booking appears on the next page load.
- The per-Window figures equal the Seats left that Guests see (FR-3).
- Stored text is shown escaped: a name containing a script tag is displayed as text.
- Once Changes exist (§4.8), each Booking shows its status: active or cancelled. A Change adds a history entry to the Booking (what moved or was given up, when, and any Voucher issued) and never gives it a third status. A cancelled Booking stays in the list with the time, the cause (Guest, Block or Overbooking fallback) and, where relevant, the Guest's choice of refund or Voucher. It is not counted in Seats booked.

#### FR-17: Outbox
A signed-in Administrator can list every simulated email. Guests cannot. Realizes UJ-3.

**Consequences (testable):**
- The Outbox lists each email with its time, recipient, subject and full body, including any links.
- An anonymous or Guest request for the Outbox is refused (FR-20) and reveals nothing.
- The Outbox is a simulated mailbox. It holds each email exactly as sent, with its links in plain text, and access control (FR-20) is what protects them. The rule that Manage-link tokens are stored only as hashes (FR-25) applies to the Booking data, not to the Outbox.
- A Guest sees an email only on the page of the action that sent it: the confirmation page (FR-8) and the result pages of a Change (FR-26, FR-27, FR-33). The emails sent in answer to a request without a session, which are the new Manage link (FR-34) and the remedy emails (FR-40, FR-42), are visible only in the Outbox. Showing them on the page would give access to a Booking to anyone who knew a reference and an email. The README says where to find them (DR-2).

### 4.5 Security and personal data *[Core]*
**Description:** The Core has three security measures, each with automated tests (success criterion SC9): server-side input validation, hashed passwords and role-based access. The fourth SC9 measure, HTTPS, is the first If-time item (§4.7). The test cases are in the brief addendum (IV-1 to IV-7, PW-1 to PW-5, RB-1 to RB-6); this section states the requirements. Personal data is limited to what a Booking needs, and a privacy notice describes it. Realizes UJ-1 and UJ-3.

**Functional Requirements:**

#### FR-18: Server-side input validation
The server validates every input, whatever the website already checks. It rejects invalid or malicious input with a clear error and changes no data.

**Consequences (testable):**
- These inputs are rejected with no Hold, Booking, payment or email (IV-1 to IV-4):
  - a Seat number that is 0, negative, fractional, not a number, above 10, or above Seats left;
  - a date or Window that is malformed or unknown, outside the Booking horizon, or past its Booking deadline;
  - a request with a required field missing or an unknown field added;
  - a name or email that is empty, too long or malformed.
- SQL fragments, script tags and HTML in any text field are never executed or rendered as markup. They are either rejected or stored and shown only as escaped text (IV-5).
- Invalid Administrator input is rejected, including in seed data (IV-6). Examples are a negative price or Capacity, or a Window that ends before it starts.

#### FR-19: Hashed passwords
Passwords are stored only as salted hashes from a slow password-hashing algorithm. They are never stored, logged or returned in plain text.

**Consequences (testable):**
- The data store holds no readable password, and the same password gives different hashes for different accounts (PW-1, PW-4).
- A new or changed password must follow these rules (NIST SP 800-63B-4):
  - at least 15 characters, with at least 64 allowed and any characters permitted;
  - refused if it is on a list of common passwords or equals the account's email;
  - no required mix of character types.
- These rules apply to Administrators now, and to Guest accounts once §4.12 is built (PW-2, PW-3).
- Pasting a password and using a password manager both work.

#### FR-20: Role-based access
The server checks the caller's role on every request.

**Consequences (testable):**
- Calls to an Administrator function are handled by role:
  - anonymous: refused as not signed in, and nothing changes (RB-1, IV-7);
  - signed-in Guest: refused as not allowed (RB-2, with §4.12);
  - signed-in Administrator: allowed (RB-3).
- A Booking can be opened only with its Manage link (§4.8) or by the Guest account that made it (§4.12). Guessing a Booking reference or a link gives the same response whether or not the Booking exists (RB-4). A Guest with their own Manage link reaches that Booking and no other (RB-5).
- No account can change its own role (RB-6, with §4.12).

#### FR-21: Personal data and privacy notice
The platform stores only the personal data a Booking needs, and a privacy notice says so.

**Consequences (testable):**
- For a Guest, the platform stores name and email only; a Guest with an account (FR-37) also has a password hash. For an Administrator, it stores email and the password hash.
- A privacy notice is linked wherever data is collected and is kept separate from the terms. It states:
  - what is stored and why (to deliver the Booking);
  - the legal basis;
  - how long data is kept and who sees it;
  - the Guest's rights, including the right to complain to Datatilsynet.
- Guest names and emails are deleted or anonymised after a retention period `[ASSUMPTION: 12 months after the Window, or after the last Voucher from the Booking expires if that is later]`.
- No marketing email is sent.
- Only cookies strictly needed for the service are set, so no consent banner is needed.
- Fonts, images and scripts are served by the platform itself. No request goes to a third party.
- Passwords, Manage-link tokens and Door codes never appear in logs.
- The privacy notice, or a security section in the README, states how the data is protected: password hashing, server-side role checks, Manage-link tokens stored only as hashes in the Booking data (the Outbox, a simulated mailbox, holds the links as sent), whether HTTPS is in place, and no third-party requests.

### 4.6 Look, feel and laptop layout *[Core]*
**Description:** One stylesheet and no design system, following the direction in §6: calm, honest and plain. The Core layout targets a laptop screen; mobile comes last in Step 2. Realizes UJ-1 and UJ-3.

**Functional Requirements:**

#### FR-22: Finnish-inspired website on a laptop screen
Guests and the Administrator can use every Core page on a laptop screen, in the look described in §6.

**Consequences (testable):**
- Every Core page works without horizontal scrolling at 1366×768 and 1920×1080 `[ASSUMPTION: these two sizes define "laptop screen"]`.
- All styling comes from one stylesheet. The fonts are the self-hosted, OFL-licensed files listed in the asset register (DR-3).
- Error and sold-out messages state what happened and what the Guest can do next. "Sold out" is shown as information about availability, with alternatives, not as an error.

#### FR-23: Accessible Core pages
Every Core page meets WCAG 2.2 level AA, with one stated exception: success criterion 1.4.10 Reflow (content at 320 CSS pixels wide without two-way scrolling) is met only once the mobile layout exists (FR-51), which comes last in Step 2 (Lisa, 2026-10-30). The legal minimum for private websites in Norway is WCAG 2.0 AA, which has no Reflow criterion, so the Core meets it in full.

**Consequences (testable):**
- An automated accessibility check reports no level A or AA failures on the Core pages, except 1.4.10 Reflow, which the report lists as a known gap until FR-51. If FR-51 is not built, the README names the gap among the success criteria not delivered (DR-2).
- A manual pass confirms that the entire booking flow and the Administrator list can be completed with the keyboard alone. Focus is always visible and never hidden behind fixed elements.
- Text contrast meets AA.
- Interactive targets are at least 24×24 CSS pixels.
- No information is conveyed by colour alone.
- Form errors appear as text next to the field and in a summary.

### 4.7 HTTPS *[If time — 1]*
**Description:** The website and the API are served only over HTTPS, so passwords, sessions and Manage links never travel unencrypted. A local development certificate is acceptable for the exam, and the README explains how to use it. This completes SC9. HTTPS is first in the If-time list because Manage links arrive with §4.8.

**Functional Requirements:**

#### FR-24: HTTPS only
The platform serves the website and the API over HTTPS only.

**Consequences (testable):** (brief tests HT-1 to HT-4)
- A plain-HTTP request to the website or the API is redirected to HTTPS. No data is returned or changed over HTTP.
- Every HTTPS response carries a Strict-Transport-Security header.
- Session cookies are Secure and HttpOnly, and are never sent over HTTP.
- Every link in a simulated email starts with `https://`.

### 4.8 Change Seats or take a Voucher *[If time — 2]*
**Description:** The confirmation email now carries a Manage link. Up to the Cutoff (12 hours before the start), the Guest can move some or all Seats to another Window, or give up some or all Seats for a Voucher. When the Guest changes plans, Seats are never refunded in money. A Change is a cancellation plus a new booking, done as one atomic step. Moving Seats is built before the Voucher `[ASSUMPTION: build order within this item]`. Realizes UJ-4.

**Functional Requirements:**

#### FR-25: Manage link
A Guest with the Manage link can open that Booking and nothing else. Realizes UJ-4.

**Consequences (testable):**
- The token has at least 128 random bits. Only a hash of it is stored.
- The link shows the Booking until its Window ends. Changes are possible only before the Cutoff.
- An invalid, expired or replaced link gives the same response as a link that never existed.
- Asking for a new link (§4.10) makes the previous link stop working.
- Manage pages load no third-party resources and send no referrer.
- Any Change needs an explicit confirming action. Loading a page alone never changes anything.
- Each confirming action carries a one-time key. Confirming twice (double click or retry) applies the Change once and returns the first outcome.

#### FR-26: Move Seats to another Window
Before the Cutoff, a Guest can move some or all Seats of a Seat booking to another Window that has room. Realizes UJ-4.

**Consequences (testable):**
- The move is atomic. If the target Window lacks room, nothing changes and the original Booking is untouched (catalogue E5).
- Moving only some Seats splits the Booking. The moved Seats become a new Booking in the target Window, with its own Booking reference and Manage link, emailed at once and shown on the result page (FR-17). The original Booking keeps its reference and link, with fewer Seats. Both keep the price paid per Seat and the Cutoff setting the original was made under. Moving all Seats moves the Booking and keeps its reference.
- The target Window must be inside the Booking horizon and before its Booking deadline (FR-39).
- A move costs nothing extra, because the price per Seat is the same in every Window in v1 (Lisa, 2026-10-30).
- Every move, partial or full, sends the booker a confirmation email, shown on the result page (FR-17, §7).
- The freed Seats count in Seats left at once, and the Administrator's list shows the Change.
- After the Cutoff, every Change is refused with an explanation.

#### FR-27: Voucher instead of Seats
Before the Cutoff, a Guest can give up some or all Seats and receive a Voucher. Realizes UJ-4.

**Consequences (testable):**
- The Voucher is worth the price paid for the Seats given up `[ASSUMPTION: the Voucher equals the price paid]`.
- The Voucher is emailed (Outbox) with its code, its value and its expiry date, one year after issue. The result page shows that email (FR-17).
- The freed Seats count in Seats left at once.
- No money is refunded.

#### FR-28: Pay with a Voucher
A Guest can use a Voucher code to pay for a later Booking. Realizes UJ-4.

**Consequences (testable):**
- A Voucher can pay for all or part of a Booking, and the rest is paid by Simulated payment `[ASSUMPTION: partial use and combination work as for Gift cards]`. Any remaining value stays on the Voucher until it expires.
- An expired, used-up or unknown code is refused with the same message. A Voucher is never paid out in money.
- Two simultaneous uses of one Voucher never spend more than its value.
- When a Booking paid partly with a Voucher is cancelled and the Guest chooses a refund, each part goes back the way it was paid: the money part as a Simulated refund, and the Voucher part as a new Voucher with the earliest expiry date of the Vouchers used `[ASSUMPTION: a returned Voucher keeps the earliest expiry]`.

### 4.9 Whole-sauna booking *[If time — 3]*
**Description:** A Guest books one entire Sauna for one Window ("Private sauna"). Only Saunas marked as bookable whole are offered, each at its own price. Until §4.13 adds screens, those marks, the prices and the Fill order come from seed data.

Seats are counted into Saunas in the Fill order, so the last Saunas in the order stay free for groups as long as possible. A Sauna can be booked whole only if every Seat already booked in the Window still fits in the Saunas ahead of it. A Whole-sauna booking can be cancelled for a refund or a Voucher, or moved, until 72 hours before the start. Realizes UJ-5.

`[NOTE FOR PM]` The strict rule protects groups, but it can refuse a Private sauna while the Venue still has room in total (catalogue B2). Comparable venues deliberately limit private use (addendum E). v1 models no limit beyond the Fill order.

**Functional Requirements:**

#### FR-29: Book a whole Sauna
A Guest can book a Sauna for a Window when all of these hold. Realizes UJ-5.
- The Sauna is bookable whole, and the Window is inside the Booking horizon and before its Booking deadline.
- It is not Blocked and not already Whole-sauna-booked.
- The Seats booked in the Window, plus the Seats held once §4.11 exists, are no more than its Room ahead. An unreleased Whole-booking-only Sauna skips this test, because it holds no Seats.
- The Window has not started, or it has no Seat booking, or the Sauna is not open for Seats. Once a Window has started, Seat bookers may already be sitting in any Sauna open for Seats; this is the v1 counterpart of H12 (Lisa, 2026-10-30).

**Consequences (testable):**
- Take 20 Seats booked, with Sauna 1 full, Sauna 2 full and 3 Seats counted in Sauna 3:
  - Sauna 4 can be booked whole (20 ≤ 29), and Seats left becomes 9 (catalogue B1);
  - Sauna 3 cannot (B2).
- With 1 Seat booked, Sauna 1 cannot be booked whole (B3).
- After the booking, Seats left drops at once by the Sauna's Capacity (B7) when the Sauna was open for Seats, and Seats are counted around the Sauna (B5). A Whole-booking-only Sauna that is not released is not in Seat capacity, so Seats left does not change.
- A Whole-sauna booking has no Hold. The review page says that the Sauna is not held while the Guest pays. FR-29 is checked again when the payment is submitted, and if the Sauna was taken meanwhile, nothing is charged (FR-36).
- When two requests for the same Sauna and Window arrive at the same time, exactly one succeeds (C1).
- With Sauna 1 marked Whole-booking-only and 5 Seats booked, Sauna 1 can still be booked whole (FR-41).

#### FR-30: Choose the Sauna
For a chosen date, the Private sauna page lists each Sauna that can be booked whole, with its Capacity, its price and its free Windows. The Guest picks a Window in that list, or opens one Sauna and picks a Window there. Realizes UJ-5.

**Consequences (testable):**
- Only the Sauna and Window pairs that FR-29 allows are listed.
- The Guest always picks the Sauna; the platform never assigns one.
- The confirmation names the Sauna and the Window.

#### FR-31: Placement follows the Fill order
After every booking, Change, cancellation, Whole-sauna booking, Block, lifted Block, Whole-booking-only mark, removed mark, release, Capacity change and Fill order change, Placement satisfies these invariants:
- **INV-1:** no Sauna holds more Seats than its Capacity.
- **INV-2:** the Seats placed equal the Seats booked in the Window.
- **INV-3:** a Whole-sauna-booked Sauna holds no Seats.
- **INV-4:** a Blocked Sauna holds no Seats.
- **INV-5:** no Sauna that is open for Seats and comes earlier in the Fill order has room while a later one holds Seats.

**Consequences (testable):**
- Catalogue groups A and B hold, with B4 rewritten as several Bookings under the 10-Seat cap (addendum A). Three examples:
  - Cancelling 3 Seats counted in Sauna 1 at [7,10,5,0] gives [7,10,2,0] (A2).
  - A Sauna emptied this way can be booked whole at once (A3).
  - Cancelling a Whole-sauna booking counts the Seats forward again (B6).
- Guests are never told a Sauna. The Administrator can see the Placement of each Window.
- A model-based test applies random sequences of bookings, Changes (including partial moves), cancellations, Whole-sauna bookings, Blocks, lifted Blocks, Whole-booking-only marks, releases, Capacity changes and Fill order changes. After every step it checks INV-1 to INV-5 against a brute-force reference. Each If-time item adds its own actions to the test when it is built.

#### FR-32: Seat and Whole-sauna requests never interleave
Seat bookings, moves and cancellations and Whole-sauna bookings in the same Window are serialised, so each one completes on a consistent state. Realizes UJ-2 and UJ-5.

**Consequences (testable):**
- A Seat booking that races a Whole-sauna booking of the last Sauna able to take it: exactly one of them succeeds, never both (C2).
- A cancellation that races a Whole-sauna booking: the Whole-sauna booking succeeds only if it is valid after the cancellation, and it is never made over a Sauna holding Seats (C3).
- Two simultaneous cancellations never move a Seat twice or lose one (C4).
- INV-1 to INV-5 hold after each completed request, under any interleaving (C5).
- Blocks, lifted Blocks, Whole-booking-only marks, releases, Capacity decreases, Fill order changes and Window edits are serialised with Bookings and Holds in every Window they touch. When a Block races a booking for the last Seats, either the booking goes first and D2 or D3 then apply, or the Block goes first and the booking is judged on the reduced Seat capacity. The outcome is never a mix of the two (C6).
- A Capacity decrease that races a Seat booking for the last Seats gives the same result as if one ran wholly before the other: the booking never lands in a Window the decrease has already filled, and the decrease never passes its check on stale Seat numbers (F1).
- A Change that moves Seats from one Window to another, run in parallel with a Whole-sauna booking or an opposite Change in either Window, leaves INV-1 to INV-5 true in both Windows. No Seat is lost or counted twice.

#### FR-33: Cancel or change a Whole-sauna booking
Before its Cutoff (72 hours), a Guest with the Manage link can cancel a Whole-sauna booking or move it to another Window. Realizes UJ-5.

**Consequences (testable):**
- On cancellation, the Guest chooses a Simulated refund or a Voucher valid for one year. Capacity is restored, and the Administrator sees the cancellation.
- A move to a Window where the Sauna is not available whole (FR-29) is rejected, and the original Booking is untouched `[ASSUMPTION: a move keeps the same Sauna unless the Guest picks another one that is available]`.
- A move to a Sauna with a different price is refused with the reason, and the Guest can cancel and book again (Lisa, 2026-10-30).
- Every cancellation or move sends a confirmation email (§7).
- After the Cutoff, every Change is refused with an explanation.

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
**Description:** When the Guest presses Book after choosing a Window and Seats, those Seats are held for a fixed 10 minutes while the Guest enters details, accepts the terms and pays. The hold length is not a Setting. A Hold is stored with its expiry time and stops counting when it expires, whether or not any cleanup has run. A Hold does not by itself prevent double booking: the atomic check of FR-10 still applies when the Booking is confirmed. Payment stays synchronous (FR-6), so the Booking is created in the same step that records the charge.

**Functional Requirements:**

#### FR-35: Hold Seats for 10 minutes
When a Guest presses Book, the chosen Seats are held for that Guest for 10 minutes.

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
- Sign-in is throttled as in FR-15, and a wrong email or password gives the same message (PW-5). Sign-up does not reveal whether an email already has an account: the reply is the same, and the account is confirmed through a link emailed to the address (Outbox). A password is reset the same way, by an emailed link.
- The choice to sign in appears after **Book**. Continuing without an account is the default and the most prominent option.
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
| Booking horizon | 4 weeks before the Window starts | — |
| Booking deadline | 5 minutes after the Window starts; may be set earlier (even before the start) or later | never later than 45 minutes before the Window ends |
| Cutoff, Seat bookings | 12 hours before the start | not under 2 hours |
| Cutoff, Whole-sauna bookings | 72 hours before the start | not under 2 hours |
| Release time (06:00 rule) | 06:00 on the day of the Window; can be set to another time or turned off | — |

**Consequences (testable):**
- A changed Cutoff applies only to Bookings made after the change. Existing Bookings keep the Cutoff they were made under.
- A changed Booking horizon, Booking deadline or Release time applies from the moment of the change to every Window it has not yet affected `[ASSUMPTION: these rules are applied when a booking or release happens, not stored per Booking]`.
- The Booking horizon and Booking deadline apply to Seat bookings, Holds, Whole-sauna bookings and the target Window of every Change `[ASSUMPTION: as in the brief]`.
- A change that sets the Booking deadline later than 45 minutes before the end of a standard 1 h 30 min Window, that is, more than 45 minutes after its start, is refused. For a Window of another length (FR-38), the earlier of the setting and 45 minutes before its end applies `[ASSUMPTION: rule for Windows of another length]`.
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
- Marking is refused while Seats are placed in the Sauna in that Window, held Seats included (D8). Marking a Sauna that is not Bookable whole is refused.
- At the Release time on the day of the Window, a marked Sauna that is not Whole-sauna-booked becomes open for Seats and takes its place in the Fill order. Seats are counted again so that INV-5 holds. The release is a condition checked against the data store's clock (NFR-11), so it takes effect even if the platform was off at the Release time.
- With the Release time turned off, a marked Sauna is never released.
- If the Release time falls after a Window's Booking deadline, the Sauna is not released for that Window `[ASSUMPTION: no release after the Booking deadline]`.

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

### 4.17 Vision (not built)
The Vision items are:
- several locations (for example A and B), chosen when booking, with an overview per location for the Administrator;
- children and adults told apart, with an age limit (under 14 by default) and a lower child price;
- memberships and period cards, with renewal;
- remote opening and locking of doors;
- one-Sauna access, moved from Step 2 on 2026-10-30: each Seat booking is placed whole in one Sauna, and its Guests use only that Sauna (catalogue group G and H19 to H23);
- heating that starts only for booked Windows, with an Administrator override of temperature. Catalogue group I and invariants INV-6 and INV-7 apply then;
- several websites on one platform, with per-website settings;
- more languages, including Norwegian pre-contract information if the service is marketed to Norwegian consumers;
- real payment and email;
- bookable resources beyond saunas;
- creating Windows from a daily pattern over a period of dates.

v1 is built so that these are extensions, not rewrites. That readiness costs no v1 build time: v1 adds no tables, settings, endpoints or abstractions for Vision items, and the architecture only checks that each could be added without rewriting the capacity core. The brief addendum holds the detailed Vision rules (memberships, period cards, renewal, heating, remote doors and per-website settings). Addendum L keeps the rules worked out for one-Sauna access.

## 5. Cross-Cutting Requirements
- **NFR-1 Runs locally.** A fresh clone runs from the README alone on a laptop. It needs no keys, paid accounts or external services. The examiner may be asked to install Python with uv, Node.js and Docker, and nothing else (Lisa, 2026-10-30). Docker is allowed so that the data store can run in a container `[ASSUMPTION: one command each to start the backend and the frontend, and one to run all tests]`.
- **NFR-2 One API, and the server decides.** The website talks to the booking platform only through one API. The platform enforces every rule in this PRD, whatever the website does. Other websites are not supported, but the API is kept clean so that support can be added later.
- **NFR-3 Venue time.** All Windows, Booking deadlines, Cutoffs, Release times and Send times are in Venue time, including on the days when daylight saving time starts or ends `[ASSUMPTION: a Window keeps its local clock times across the change]`. Offsets (Booking horizon, Booking deadline, Cutoffs, Send time, Hold length and the 45-minute limit) are elapsed time from the Window's start or end. The Release time is a clock time on the date the Window starts. A Window belongs to the date it starts. A Window that would start or end in a skipped or repeated hour is refused.
- **NFR-4 Money.** Prices are in NOK including VAT and come from seed data in the Core. A Booking keeps the price it was paid at.
- **NFR-5 English.** The website and the emails are in English only.
- **NFR-6 Test depth.** Each story includes its tests as part of being done. Concurrency, capacity, validation and SC1 are tested in depth; other features are tested for breadth (Lisa, 2026-10-30). Concurrency tests run in parallel against the same kind of data store the platform uses, never against a mock. All tests run with one command.
- **NFR-7 No performance promise.** v1 states no throughput or latency target.
- **NFR-8 Dependencies.** At the freeze, dependencies are current, and a dependency audit reports no known critical vulnerability `[ASSUMPTION: an audit tool is run at the freeze]`.
- **NFR-9 Honest interface.** The interface has no dark patterns anywhere: no countdown timers, false scarcity, pre-ticked options or hidden fees (markedsføringsloven § 7; forskrift om urimelig handelspraksis § 1 nr. 7).
- **NFR-10 Real data.** Windows, Capacity, prices, Bookings and the Outbox are stored in the data store and survive a restart. Nothing the product shows is faked (Lisa, brainstorm 2026-10-27: "the database tables cannot be fake").
- **NFR-11 Time rules are checked, not scheduled.** The Release time, Booking deadline, Hold expiry, Cutoff and the 30-day remedy limit are conditions, evaluated against the data store's clock when a request is handled and after its lock is taken. No request relies on a timer having fired. Effects that need a timed action, such as counting Seats again at the Release time or making the default refund after 30 days without a choice, are caught up at the next start and by the next request that reads the affected Window or remedy, so a platform that was off at the time still reaches the right state. The platform runs no background job for this in v1. Tests control the clock and never wait in real time (Lisa, 2026-10-30).

## 6. Aesthetic and Tone
- **Feel:** calm, honest and plain: the Finnish idea of *saunarauha*, the peace of the sauna. The site should be appealing and intuitive for a first-time Guest (Lisa, 2026-10-29), and unhurried: nothing on it pushes.
- **Palette:** light wood (birch and pine), deep forest green, granite grey, birch white, a grey sea-blue and sky blue. Saturation is low, and every pair of text and background colours meets WCAG AA contrast.
- **Type:** Finlandica for headings and Source Sans 3 for text. Both are under the SIL Open Font License and self-hosted. Finlandica is Finland's country-brand typeface, so it reads as Finnish by design.
- **Imagery:** Finnish saunas outside and inside, with their traditional equipment: the *kiuas* (stove) and its stones, the *kiulu* (bucket) and *kauha* (ladle), the wooden *lauteet* (benches) and the *vihta* (birch whisk). The light is dim and indirect, with wood, water and forest in view. Every image is AI-generated or freely licensed and listed in the asset register (DR-3).
- **Copy:** short and concrete, with facts before persuasion. A few Finnish words appear, each with an English gloss.
- **Anti-references:**
  - spa-luxury cues (scents, music, coloured LED light, "pamper yourself");
  - polished stock photography;
  - boasts about enduring heat;
  - sexualised framing;
  - urgency selling.
- References to study, not copy, are in addendum F.

## 7. Information Architecture
- **Core, Guest:** Landing (with "Before you come") → Book seats (date, Seats, Windows) → Details and review → Confirmation (with the sent email and a link to "Before you come"). Also Terms and Privacy notice.
- **Core, Administrator:** Sign-in → Booking list (by date and Window) → Outbox. Also Sign-out.
- **If time, Guest:**
  - Manage booking, reached from the Manage link: view the Booking, move Seats or take a Voucher, or cancel or move a Whole-sauna booking;
  - Voucher entry at payment;
  - Private sauna (Window → Sauna, or Sauna → Window);
  - My booking (resend);
  - Remedy page, reached from the apology email: choose a refund or a Voucher;
  - guest sign-up, sign-in and My bookings.
- **If time, Administrator:** screens for Windows, Capacity, prices, the Fill order and the Settings; the blocking calendar with Whole-booking-only marks; Placement per Window.
- **Step 2:** Gift card purchase. Administrator screens for Gift card values, limits and the list of cards sold; for doors, locks, codes, the Send time, per-Block door-code overrides and resend; and for Gradual opening.
- The UX workflow sketches the booking flow and the Administrator booking list first, and the blocking calendar when §4.13 comes near, following the teacher's advice (2026-10-06).
- **UX scope for this round (Lisa, 2026-10-30):** the UX workflow designs every Core page in full, plus the places on Core pages where If-time features plug in (the Private sauna entry, the Voucher field, the sign-in choice), and the flows of §4.8 to §4.12. The screens of §4.13 come later.
- **States left to the UX designer under FR-22:** behaviour is the designer's call unless a rule above fixes it. Core: the Booking deadline passing between choosing a Window and paying; a Window that has started but can still be booked; the last day of the horizon; no Window with room anywhere in the horizon; sign-in slowed or refused; an anonymous visitor at an Administrator address; a date with no Bookings; payment in progress. If time: the Manage page after a Voucher, a Venue cancellation, the Cutoff and the end of the Window; a Voucher that covers the whole total, where "Pay NOK 0" needs other wording; a resend refused by the rate limit; the Remedy page after the choice or after 30 days; a Seat taken by another Guest while the details are entered.

**Emails.** All emails are plain text in English and appear in the Outbox. A Guest sees an email on the page of the action that sent it (FR-17).

| Email | To | Content | Phase |
|---|---|---|---|
| Booking confirmation (FR-8) | Booker | Booking reference, date and Window, Seats, total paid, terms, "Before you come", payment note | Core |
| Confirmation of a Change (FR-26, FR-33) | Booker | What changed, the new Window and Seats, the Manage link | If time 2–3 |
| Split-off Booking (FR-26) | Booker | New Booking reference and its own Manage link | If time 2 |
| Voucher (FR-27, FR-28, FR-42) | Booker | Code, value, expiry date | If time 2 |
| Manage link resend (FR-34) | Address given, on a match | New link; the old one stops working. Visible only in the Outbox | If time 4 |
| Whole-sauna booking, cancellation or move (FR-29, FR-33) | Booker | Sauna, Window, price, refund or Voucher | If time 3 |
| Apology with remedy link (FR-40, FR-42) | Booker whose Booking was cancelled | What happened, the link, 30 days to choose; Step 2: do not use any Door codes received | If time 3, 7 |
| Remedy confirmation (FR-42) | Same | The refund (may take a few days) or the Voucher | If time 3, 7 |
| Account confirmation and password reset (FR-37) | Address given | A single-use link | If time 6 |
| Gift card (FR-43) | Buyer | Code, value, expiry date, not paid out in money | Step 2 |
| Door codes, extra codes, correction (FR-46 to FR-48) | Seat or Whole-sauna booker | The codes to use, or a correction naming them | Step 2 |

## 8. Delivery Requirements and Constraints

### 8.1 Delivery requirements (exam)
- **DR-1 AI use and quality assurance.** Documentation shows:
  - how AI was used at each stage (planning with BMAD, implementation with Claude Code);
  - how it was steered (session logs, and a token budget per story, which is only a proposal until §12 Q17 is decided);
  - how the result was checked (tests, reviews, manual checks), including where AI output was wrong or rejected and how that was found.
- **DR-2 README.** The README covers:
  - how to install and start the backend and the frontend;
  - how to run all tests;
  - the Administrator test login and the seeded sample Bookings; once §4.8 is built, where to find a sample Manage link in the Outbox; once §4.12 is built, a Guest test account;
  - how to view the Outbox, which also holds the emails that Guests do not see on a page (FR-17);
  - which success criteria were not delivered.
- **DR-3 Clean assets.** No licensed, trademarked or otherwise protected material is used. Every image, font, icon and text is AI-generated, freely licensed or checked by the author, and an asset register lists the source and licence of each. The trademark check of the Venue name is described under the title and is still open (§12 Q10).
- **DR-4 Traceability.** The repository shows the path from plan to code: the planning documents, small descriptive commits and the session logs.
- **DR-5 Tidy repository.** No secret is committed. Any secret, such as the session key, is generated on first start or read from a git-ignored local file, and an example file is committed instead. The seeded Administrator password is a documented local test value. Seed and sample data live in one named folder, tests in another, and planning documents in `.docs/`. The README names each location.

The part-1 assessment criteria map to this PRD as follows:

| Criterion (weight) | Covered by |
|---|---|
| Process and AI steering (30 %) | DR-1, DR-4 |
| Functionality and scope (20 %) | §4, §10, SM-1, SM-5 |
| QA and testing (15 %) | NFR-6, SM-1, SM-2, SM-5 |
| Design and UX (10 %) | §6, §7, FR-22, FR-23, SM-3 |
| Code quality and architecture (10 %) | NFR-2, NFR-10, addendum A |
| README and runnability (10 %) | NFR-1, DR-2, SM-4 |
| Repository tidiness (5 %) | DR-3, DR-5 |

### 8.2 Constraints
- One person builds it, from 27 October to 15 December 2026, alongside two other exams on 16 November and 8 December.
- Claude tokens and long-running tasks are a real limit. Frontend, design and extensive testing are the likeliest overruns.
- Planning (PRD and architecture) takes 7–8 of the first 12 days.
- 9–15 December is a freeze for tests, the README and the AI-use documentation. No new features are added. This is only a proposal until §12 Q17 is decided.
- The backend is Python and the frontend JavaScript; the frameworks are an architecture decision. No paid services are used. The README already uses uv, so the architecture either keeps it or replaces it on purpose.

## 9. Non-Goals (Explicit)
- Not a real service: no real payment, email, door locks or lock systems. Heating and temperature control are not built at all.
- One Venue, one website, one API, in English only. v1 has no support for several venues or websites.
- No native mobile apps.
- No money back when a Guest changes plans for Seats: the Guest moves Seats or takes a Voucher. When Saunalöyly cancels, the Guest chooses between a refund and a Voucher.
- No combined basket across Windows.
- No waiting list, and no dynamic or demand pricing `[ASSUMPTION: comparable venues sometimes offer a waiting list, but the sources do not mention one]`.
- No marketing email, newsletters or tracking.
- No distinction between children and adults: every Seat costs the same.
- No rules engine for etiquette, age or safety: the website informs Guests about etiquette and safety (FR-1) but enforces none of it. Age rules come with child pricing (Vision).
- No Administrator editing screens in the Core.
- No performance or throughput guarantee.
- No market validation: prices and demand are not tested, and the seed prices are illustrative.
- No AI features in the app. AI is used only to build it.

## 10. MVP Scope

### 10.1 In scope
**Core** (§4.1 to §4.6):
- find a Window, and book and pay for Seats;
- capacity integrity under concurrency;
- Administrator sign-in, the booking list and the Outbox;
- input validation, hashed passwords and role-based access;
- the privacy notice;
- the Finnish-inspired laptop website.

**Core done** means that the website is complete, the booking platform is connected, and SC1, SC9 (without HTTPS) and the laptop part of SC10 work as intended. "Website complete" means that every Core page in §7 exists with final copy and images in the §6 look, with no placeholders, and that FR-22 and FR-23 pass.

**If time (still v1), in this order:**
1. HTTPS (§4.7). Placed first on 2026-10-29.
2. Change Seats or take a Voucher (§4.8). Placed before Whole-sauna booking on 2026-10-27.
3. Whole-sauna booking (§4.9).
4. "My booking" resend (§4.10).
5. Seat Hold (§4.11).
6. Guest accounts (§4.12).
7. Administrator tools and Venue rules (§4.13). All of v1 comes before Step 2, decided on 2026-10-29.

The relative order of items 3 to 6 is the brainstorm's proposal `[ASSUMPTION: order of items 3 to 6]`. No backcasting from 15 December has been run.

`[NOTE FOR PM]` The Core is deliberately narrower than the teacher's suggested minimum, which was SC1 to SC4 with an Administrator view. The teacher rated time and scope a high risk, and two other exams fall inside the build period. Vouchers stay in v1 (If time 2), although the teacher suggested Step 2, because changing Seats depends on them.

### 10.2 Out of scope for v1
- **Step 2, in this order:** Gift cards (§4.14), then Door codes with the optional Gradual opening (§4.15), then the mobile layout (§4.16).
- **Vision:** everything in §4.17.

### 10.3 Planning depth
*Proposal until §12 Q17 is decided.* The architecture decides everything the Core needs, plus the If-time choices that shape the Core data model: Placement, the lock unit per Window, Holds stored as data, Manage-link tokens, and how the data store refuses over-capacity writes in every phase (FR-10). The payment model is already decided: synchronous in every phase (FR-6). Epics and stories are written in full for the Core. Each If-time item gets one epic, and its stories are written when it comes next in the order of §10.1. Step 2 and Vision get no stories in this round. Step 2 starts only when every v1 item built so far passes its tests.

## 11. Success Metrics
*Success criteria SC1 to SC10 are the brief's. A criterion that is not reached is reported as not delivered (DR-2).*

| SC | Criterion | Phase |
|---|---|---|
| SC1 | Book Seats; the last Seat has exactly one winner | Core |
| SC2 | Book a whole Sauna | If time 3 |
| SC3 | Change Seats or take a Voucher | If time 2 |
| SC4 | Cancel or change a Whole-sauna booking | If time 3 |
| SC5 | Gift card | Step 2 |
| SC6 | Door codes | Step 2 |
| SC7 | Membership and period card | Vision, not built |
| SC8 | Adjustable rules: the five Settings | If time 7 |
| SC9 | Protection against hacking: validation, passwords, roles, HTTPS | Core, HTTPS at If time 1 |
| SC10 | Responsive design | Laptop in the Core, mobile last in Step 2 |

**Primary**
- **SM-1: Seats are booked end to end and never oversold.** This is SC1.
  - A Guest books 4 Seats, pays and gets a confirmation. The Administrator sees the Booking, and Seats left drops by 4.
  - The last-Seat race gives exactly one winner in every repetition, with zero over-capacity results.
  - Validates FR-1 to FR-17.
- **SM-2: The security measures pass their tests, phase by phase.** This is SC9.
  - Core: IV-1 to IV-7; PW-1 to PW-5 on Administrator accounts; RB-1, RB-3, and RB-4 for guessed Booking references.
  - With §4.7: HT-1 to HT-4. With §4.8: RB-4 for guessed links, and RB-5. With §4.12: RB-2, RB-6, and PW-2 and PW-3 on Guest accounts.
  - Validates FR-15, FR-18 to FR-21, FR-24, FR-25 and FR-37.
- **SM-3: The Core website works on a laptop and is accessible.** This is the laptop part of SC10: every Core page passes FR-22 and FR-23. Validates FR-1 to FR-4, FR-22 and FR-23.
- **SM-4: The examiner can run and check it.** A fresh clone starts, and all its tests pass, by following the README alone, with no keys or paid services. DR-1 to DR-5 are complete at the freeze. Validates NFR-1 and DR-1 to DR-5.

**Secondary**
- **SM-5: If-time features behave as specified with the defaults.** This covers SC2, SC3, SC4 and SC8, as built. Catalogue groups A to F pass, with the decisions in addendum B applied, B4 and D5 rewritten (addendum A, FR-40), and group C run as parallel tests. The model-based Placement test finds no invariant violation. Validates FR-25 to FR-42.
- **SM-6: Step 2.** SC5, SC6 (catalogue group H, without the one-Sauna cases H19 to H23) and the mobile part of SC10, if built. Validates FR-43 to FR-51.

**Counter-metrics (do not optimize)**
- **SM-C1: Number of features delivered.** Must not rise at the cost of in-depth tests of concurrency, capacity and validation. Counterbalances SM-5 and SM-6.
- **SM-C2: Booking speed and convenience.** Must never be gained by weakening the atomic check (FR-10), skipping the review page, or dropping the pre-contract information (FR-5). Counterbalances SM-1.
- **SM-C3: Persuasion.** No urgency, false scarcity or hidden fees to push a booking through (NFR-9). Counterbalances SM-3.
- **SM-C4: Visual polish.** Must not use up the freeze or the time for tests. Counterbalances SM-3.

## 12. Open Questions
1. **H6: two valid codes on one door (Step 2).** With back-to-back Windows, the next Window's code is valid during the last 20 minutes of the current one. The options are to accept the overlap and tell Guests, to start validity at the Window start, or to leave a gap between Windows. Lisa deferred this on 2026-10-29, and addendum C explains it. Revisit before Door codes are planned.
2. **How is "intuitive" verified, now that the informal three-person test is dropped?** Owner: Lisa. Decide before the UX workflow.
3. **Seed data.** The price per Seat is the same in every Window in v1 (decided 2026-10-30, Lisa; FR-26). Still open: opening hours, the Window schedule (including whether there is a changeover gap between Windows, which also affects Q1), and the prices themselves. Owner: Lisa. Decide before the architecture seeds the data.
4. **Database engine.** An architecture decision, made before the first story. The examiner may be asked to install Docker (NFR-1, Lisa 2026-10-30), so PostgreSQL in a container is possible, and so is SQLite without Docker. The concurrency research covers PostgreSQL; the capacity research checked SQLite's transaction rules. The architecture weighs the extra install for the examiner against the engine's documented concurrency behaviour, and picks an engine for which the store-level refusal of FR-10 can be built in every phase.
5. **Stored or derived Placement.** An architecture decision. The research recommends derived Placement, proven by the model-based test (FR-31).
6. **Order of If-time items 3 to 6.** It is still a proposal, and backcasting from 15 December has not been run. Owner: Lisa. Decide before sprint planning.
7. **Administrator cancellation of a single Booking.** It is not in the sources. Is it needed? It is the only way some late-cancellation cases in the catalogue can arise.
8. **Real lock behaviour (Step 2).** Two different PINs on one lock, and editing a code after its validity has started, are untested. So are how fast a create, change or delete takes effect, and how silent failures show up.
9. **Late payment after a Hold expires.** The payment is synchronous (decided 2026-10-30), so a late payment either books or charges nothing. This flow has no primary source, and expiry drift is unknown. The architecture must prove it with the parallel tests of FR-36, using the data store's clock.
10. **Trademark.** Check existing "LÖYLY" marks (classes 43 and 44) before the name is treated as clean (DR-3).
11. **Gift-card validity (Step 2).** One year is common practice, but a three-year limitation period may still apply to a paid card. This is a legal reading, not legal advice.
12. **Gaps before any real launch.** Norwegian pre-contract information if the service is marketed to Norwegian consumers, and the organisation number and VAT details. These are out of scope for the fictional exam version.
13. **Heating cases I11 to I23.** Vision.
14. **Lock unit.** Should Seat and Whole-sauna requests lock per Window, per Sauna, or through a queue per Sauna? An architecture decision, proven by the parallel tests of FR-32.
15. **One-Sauna access (Vision).** May Bookings be repacked before the Send time? Is a Window offered for N Seats only when one Sauna has N free (catalogue G1)? Moved from Step 2 on 2026-10-30; revisit only if it comes back.
16. **Step 2 order.** The brief addendum puts Gradual opening first in Step 2, while brief.md leaves it out. The PRD treats Gradual opening as an optional mode of Door codes. One-Sauna access is in Vision in the PRD, the brief and the brief addendum (Lisa, 2026-10-30). Owner: Lisa.
17. **Coach proposals not yet confirmed.** Three proposals from the brainstorm stand in the PRD without Lisa's confirmation (she confirmed only tests in every story, NFR-6, on 2026-10-30): the 9–15 December freeze (§8.2), a token budget per story (DR-1), and the planning depth (§10.3). Owner: Lisa. Decide the planning depth before the architecture starts, and the freeze and the token budget before sprint planning.

## 13. Assumptions Index
- §2.3: protagonist names are placeholders.
- FR-1: content of the "Before you come" section, apart from the two towels and the bathing rules.
- FR-3: the nearest Windows with room come from the same day first, then the following days, at most three.
- FR-5: names are 1–100 characters, and emails at most 254.
- FR-8: the Core confirmation has no Manage link.
- FR-8: the confirmation page is tied to the paying browser session.
- FR-13: the seed generates Windows from the run date; the schedule itself is open (Q3).
- FR-11: 100 race repetitions per test run.
- FR-15: the architecture sets the sign-in throttling thresholds.
- FR-16: the booking list is grouped by date and Window, with totals.
- FR-21: retention is 12 months after the Window, or until the last Voucher expires.
- FR-22: "laptop screen" means 1366×768 and 1920×1080.
- §4.8: moving Seats is built before the Voucher.
- FR-27: a Voucher is worth the price paid for the Seats given up.
- FR-28: Vouchers can be used in part and combined with payment, as Gift cards can.
- FR-28: a Voucher returned in a refund keeps the earliest expiry of the Vouchers used.
- FR-33: a move keeps the same Sauna unless the Guest picks another available one.
- FR-34: the resend limit is 5 per hour per email address and per source address.
- FR-35: Holds per source address are limited; the architecture sets the limit.
- FR-37: Guests sign in by email.
- FR-39: changes to the Booking horizon, Booking deadline and Release time apply from the moment of the change.
- FR-39: for a Window of another length, the earlier of the Booking deadline setting and 45 minutes before its end applies; the Booking horizon and Booking deadline apply to every way of taking capacity.
- FR-40: a Block covers every overlapping Window; as many Bookings lose as needed.
- FR-41: no release after the Booking deadline.
- FR-42: a refund is made if the Guest has not chosen within 30 days.
- FR-43: Gift cards carry a 14-day right of withdrawal (legal reading).
- FR-45: Administrator-entered codes can be changed until sent; every Sauna has a self-service lock in the seed data.
- FR-48: H14 (widened to every way a Sauna becomes open) and H15 as in the brief.
- FR-49: H11 as recommended.
- NFR-1: one command each to start the backend and frontend, and one to run all tests.
- NFR-3: Windows keep their local clock times across daylight-saving changes.
- §8.2, DR-1, §10.3: brainstorm proposals not yet confirmed (the freeze, a token budget per story, planning depth); open as §12 Q17.
- NFR-8: a dependency audit is run at the freeze.
- §9: no waiting list.
- §10.1: the order of If-time items 3 to 6.
