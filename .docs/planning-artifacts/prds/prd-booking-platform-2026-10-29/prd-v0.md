---
title: "Saunalöyly Booking Platform"
status: draft
created: 2026-10-29
updated: 2026-10-29
---

# PRD: Saunalöyly Booking Platform
*Working title — confirm.*

## 0. Document Purpose

This PRD defines what the booking platform and its website must do, for the project owner (Lisa), the examiner, and the downstream workflows (UX, architecture, epics and stories). It builds on the product brief and its addendum (`.docs/planning-artifacts/briefs/brief-booking-platform-2026-09-20/`), the minimal-v1 brainstorm (2026-10-27), and three technical research reports (concurrency and seat holds, seat capacity model, smart-lock door codes) under `.docs/planning-artifacts/research/`. It does not duplicate them: the full rule tables, the 85-example capacity catalogue and the research reasoning stay there and are referenced.

Vocabulary is anchored in the Glossary (§3); features are grouped in §4 with globally numbered FRs nested under them. Inferred points are tagged `[ASSUMPTION]` inline and indexed in §9. This is a first draft produced on the fast path — every `[ASSUMPTION]` needs a yes/no from Lisa.

**Delivery order (decided 2026-10-29):** the **v1 core** first, then **the whole "if time" list** (still counted as v1), then **step 2**. Mobile layout comes last in step 2. Each feature below is labelled **[Core]**, **[If time]**, **[Step 2]** or **[Vision]**.

## 1. Vision

Saunalöyly is a fictional sauna facility with at least four saunas, and this platform is how guests reserve it. Guests book **individual seats** in a shared sauna session, or — once the platform supports it — book an **entire sauna** privately for their group. The website is inspired by Finnish sauna culture: calm, warm, uncluttered, and so intuitive that a first-time guest can find a free window, pick how many seats they want, and pay without help.

The hard part is not the booking form; it is running two kinds of booking against the same physical capacity. When many guests share open saunas and one group takes a whole sauna, capacity must never be double-sold, cancellations must not leave the facility in a muddle, and the rules must be precise enough to test. That precision, and honest documentation of how it was built and verified with AI, is what this project is judged on.

The platform is a learning project delivered as a 2026 exam submission (IBE160, group G78), built by one person between 27 October and 15 December 2026. Payment, email, door locks and heating are simulated. It is built so it *could* grow into a real service, but does not pretend to be one.

## 2. Target User

### 2.1 Jobs To Be Done
- **Guest:** "I want to spend 90 minutes in a sauna with my friends this weekend, and I want to see in seconds whether there is room and what it costs."
- **Guest:** "I want to be sure that when I have paid, my seats are really mine."
- **Guest:** "If my plans change, I want to change or cancel without writing to anyone."
- **Guest (group):** "We want to be on our own — I want the whole sauna." *(If time)*
- **Administrator:** "I want to see who is coming and how full each window is, without doing arithmetic."
- **Administrator:** "I want the system to refuse bookings that would break capacity, so I never have to apologise at the door."
- **Builder/examiner:** "I want rules that are precise enough to test automatically, and a record of how AI was used and checked."

### 2.2 Non-Users (v1)
- **The examiner** is not a user of the platform; they evaluate it. No dedicated examiner features.
- Operators of other facilities, and other websites using the same platform (the platform is *kept* clean for this, but only one website exists).
- Members and card holders (membership, period cards) — Vision.

### 2.3 Key User Journeys
*Protagonist names are placeholders `[ASSUMPTION: no named personas exist in the sources; confirm or replace]`.*

- **UJ-1. Ingrid books two seats for Saturday afternoon.** *[Core]*
  - **Persona + context:** Ingrid, a student in Oslo, wants a relaxed Saturday sauna with a friend. She has never used the site and does not want to create an account.
  - **Entry state:** Anonymous, on a laptop, arrives at the landing page.
  - **Path:** She picks **Individual seats**, chooses Saturday in the calendar, and sees the day's windows with seats left for each. She picks 15:00–16:30, sets seats to 2, and sees the total price. She enters her name and email, accepts the terms, and pays (simulated).
  - **Climax:** The confirmation page shows her booking reference, the window, seats and price, and the confirmation email (simulated) appears in the outbox view.
  - **Resolution:** She holds a booking reference and a confirmation she can screenshot. The window's seats-left count has dropped by 2.
  - **Edge case:** If someone else has just taken the last seats, she sees "not enough seats left" with the actual number remaining and the next window that has room; she is not charged.

- **UJ-2. Two guests reach for the last seat at the same moment.** *[Core]*
  - **Persona + context:** Aino and Jonas both view 18:00–19:30, which shows 1 seat left.
  - **Entry state:** Both anonymous, on the booking step with 1 seat selected.
  - **Path:** Both press pay within the same second.
  - **Climax:** Exactly one receives a confirmation. The other is told no seat is left and is not charged.
  - **Resolution:** The window shows 0 seats left; the administrator's list shows one new booking.

- **UJ-3. Katja checks who is coming.** *[Core]*
  - **Persona + context:** Katja, facility administrator, prepares for the evening shift.
  - **Entry state:** Not logged in, on the admin sign-in page.
  - **Path:** She signs in with her admin account, opens the booking list, filters to today, and sees each window with its bookings (name, email, seats, reference) and total seats booked against capacity.
  - **Climax:** She sees at a glance that 18:00–19:30 is full and 20:00–21:30 has 9 seats open.
  - **Resolution:** She signs out. A guest account cannot reach this page.

- **UJ-4. Ingrid cannot come and changes her booking.** *[If time]*
  - **Persona + context:** Ingrid learns on Friday morning that her friend is ill.
  - **Entry state:** Has the confirmation email; booking is more than 12 hours from start.
  - **Path:** She opens the manage link in her email, reduces from 2 seats to 1 (or moves to Sunday, or cancels for a voucher).
  - **Climax:** The page confirms the change and shows the new state; no cash is refunded for seats — she gets a voucher if she cancels.
  - **Resolution:** The freed seats are available to other guests immediately.
  - **Edge case:** Within 12 hours of start, the manage page says changes are closed and nothing can be altered.

- **UJ-5. Olav books a whole sauna for his family's reunion.** *[If time]*
  - **Persona + context:** Olav wants privacy for 10 relatives on a Sunday morning.
  - **Entry state:** Anonymous, on the landing page.
  - **Path:** He picks **Private sauna**, picks a window directly (or opens a specific sauna and picks a window), sees the whole-sauna price, enters name and email, pays.
  - **Climax:** Confirmation names the sauna and the window; that sauna can no longer be booked by anyone else in the window.
  - **Resolution:** Seats for that window drop by that sauna's capacity.
  - **Edge case:** If individual seats are already placed in the sauna he chose, he is told it is unavailable in that window and is offered other saunas or windows.

## 3. Glossary
*Used verbatim everywhere in this PRD and downstream.*

- **Facility** — Saunalöyly, the single fictional sauna facility in v1. Has four or more Saunas.
- **Sauna** — One physical sauna room with a fixed seat Capacity. Example set used in all calculations: Sauna 1 = 7, Sauna 2 = 10, Sauna 3 = 12, Sauna 4 = 15 (total 44).
- **Seat** — One guest's place in a Window. Seats are identical and are not tied to a particular Sauna in the guest's view.
- **Capacity** — Number of Seats a Sauna holds; also the facility-wide sum over Saunas that are neither privately booked nor Blocked.
- **Window** — A bookable time slot, identical for all Saunas, never partially overlapping another Window (standard length 1 h 30 min, e.g. 15:00–16:30). Intervals are half-open: a Window ending 16:30 and one starting 16:30 do not overlap.
- **Individual seat booking** — A Booking of one or more Seats in one Window.
- **Private sauna booking** — A Booking of one entire Sauna for one Window.
- **Booking** — Either of the two above, with a **Booking reference**, guest name and email, price paid and status.
- **Guest** — Anyone making a Booking. May be **anonymous** (no account, the default) or hold an **account** (If time).
- **Administrator** — Staff user with an admin account who sees all Bookings and, in later features, manages Windows, prices and rules.
- **Fill order** — The administrator-set order in which Saunas are filled with Seats (Sauna 1 first). Seats fill one Sauna before the next.
- **Block** — A period in which one or more Saunas cannot be booked or hold Seats (maintenance).
- **Manage link** — A link with a long random token in the confirmation email; the only way back into a Booking.
- **Voucher** — A credit issued instead of cash when Seats are cancelled; valid one year.
- **Hold** — A temporary reservation of Seats during payment (10 minutes). *(If time)*
- **Outbox** — The in-app list of simulated emails.
- **Cutoff** — The latest moment a change or cancellation is allowed (12 h before start for Seats, 72 h for private Sauna).

## 4. Features

### 4.1 Discover and see availability *[Core]*
**Description:** The guest lands on a calm, Finnish-inspired page that explains Saunalöyly in a few lines and offers the booking path **Individual seats**. (**Private sauna** is added when 4.8 is built; until then it is not shown `[ASSUMPTION]`.) A calendar limits dates to the booking horizon (4 weeks). For a chosen date the guest sees a list of Windows with seats left and the price per seat. The guest books *seats*, never a particular sauna, and the interface makes that clear. Realizes UJ-1, UJ-2.

**Functional Requirements:**

#### FR-1: Landing page and booking entry
A guest can open the website and start an Individual seat booking in one click from the landing page. Realizes UJ-1.

**Consequences (testable):**
- The landing page loads without login and shows the facility name, a short description and a primary booking action.
- The page contains no text, image, font or icon whose licence is unknown (see FR-21).

#### FR-2: Date and Window selection
A guest can pick a date within the booking horizon and see its Windows with seats left and price. Realizes UJ-1.

**Consequences (testable):**
- Dates beyond the horizon (default 4 weeks ahead) cannot be selected.
- Each Window shows the number of seats left, which equals the total Capacity of non-booked, non-Blocked Saunas minus Seats booked in that Window.
- A Window with 0 seats left is shown as unavailable, and the next Window with room is suggested `[ASSUMPTION: from comparable-service UX practice]`.
- A Window whose start is more than 5 minutes past is not bookable (default booking cutoff).

#### FR-3: Seats, not Saunas
The booking flow presents quantity of Seats and never asks the guest to choose or see a particular Sauna for an Individual seat booking. Realizes UJ-1.

**Consequences (testable):**
- No screen in the Individual seat flow displays a Sauna identifier.
- Copy states that guests book seats and that groups wanting to stay together should book a whole sauna (once available).

**Notes:** `[NOTE FOR PM]` The research found no comparable product that hides which room the guest is placed in until check-in; hotels do this routinely, but test with someone unfamiliar with the idea.

### 4.2 Book individual seats *[Core]*
**Description:** The guest chooses a Window and number of Seats, sees the total price early, enters name and email (no account), accepts the terms and pays through a simulated payment that succeeds instantly. Reservation of the Seats and the payment are one atomic step (no Hold in the core). On success the guest gets a confirmation page and a simulated email. Realizes UJ-1, UJ-2.

**Functional Requirements:**

#### FR-4: Book 1+ Seats in a Window without an account
A guest can book one or more Seats in one Window by giving name (free text) and email, accepting the terms, and paying. Realizes UJ-1.

**Consequences (testable):**
- Total price = seats × Window price per seat and is shown before payment is requested.
- A booking with 0, negative, fractional or more-than-available seats is rejected with a clear message and changes no data (see FR-15).
- Successful booking reduces that Window's seats left by exactly the booked number.
- No account or password is requested.

#### FR-5: Simulated payment
Payment is simulated, instant and requires no keys or external service. Realizes UJ-1.

**Consequences (testable):**
- The platform runs locally with no payment credentials.
- A test switch can force payment failure `[ASSUMPTION]`; a failed payment creates no Booking and holds no Seats.

#### FR-6: Confirmation
After a successful Booking the guest sees a confirmation page and receives a simulated email with the Booking reference. Realizes UJ-1.

**Consequences (testable):**
- The confirmation page shows reference, Window, seats, total price and the guest's email.
- The email appears in the Outbox and on the confirmation page.
- The reference alone gives no access to the Booking (see FR-17).

#### FR-7: One Window per Booking
Each Booking covers exactly one Window; guests wanting several Windows make several Bookings, each paid separately `[ASSUMPTION: from addendum "payment per Window"; no combined cart in v1]`. Realizes UJ-1.

### 4.3 Capacity integrity under concurrency *[Core]*
**Description:** Capacity is a hard guarantee. The database, not only the application, prevents Seats booked in a Window from exceeding Capacity. Checking and reserving happen as one atomic step, so simultaneous requests can never oversell. This is the single most heavily tested part of the product. Realizes UJ-2.

**Functional Requirements:**

#### FR-8: Never exceed Capacity
The system never holds more booked Seats in a Window than the Window's Capacity, however many requests arrive at once. Realizes UJ-2.

**Consequences (testable):**
- With N parallel requests for a Window with fewer than N seats, accepted seats ≤ seats left; this holds when the test is repeated 100 times.
- A constraint in the data store rejects an over-capacity write even if the application check is bypassed.

#### FR-9: Last-seat race gives exactly one winner
When several guests request the last remaining Seats simultaneously, the system accepts exactly as many as fit, and each loser receives a clear "no seat available" message and is not charged. Realizes UJ-2.

**Consequences (testable):**
- Two parallel requests for the one remaining seat: exactly one Booking is created.
- The losing request creates no Booking, no charge and no Outbox confirmation, and holds nothing.

#### FR-10: Orders are accepted whole or not at all
A request for more Seats than are left is rejected as a whole. Realizes UJ-1.

**Consequences (testable):**
- 42 of 44 seats taken, request for 3: rejected, nothing placed (catalogue A6).

#### FR-11: Windows are venue-wide and never overlap
The platform rejects any Window definition that overlaps another or differs between Saunas. Realizes UJ-1.

**Consequences (testable):**
- Seed or admin input of overlapping Windows is rejected (half-open intervals; 15:00–16:30 and 16:30–18:00 are accepted).
- A Sauna that is unavailable for part of a Window is expressed as a Block, not as a different Window.

**Feature-specific NFRs:**
- Concurrency is verified by automated parallel tests against the same storage the platform uses, not by mocks.
- Concurrent conflicts that need a retry are retried a bounded number of times; if still unsuccessful, the guest sees a clean error and no partial data is written.
- **No throughput or latency figures are promised in v1**; load-test targets are set after measurement.

### 4.4 Administrator booking list *[Core]*
**Description:** One admin account signs in with a password and sees all Bookings, by Window. No admin editing screens exist in the core: Windows, Capacity and prices come from seed data. Realizes UJ-3.

**Functional Requirements:**

#### FR-12: Admin sign-in
An administrator can sign in with email and password; guests cannot. Realizes UJ-3.

**Consequences (testable):**
- A seeded admin account exists and is documented in the README.
- Wrong credentials give the same message whether or not the email exists.

#### FR-13: Booking list
A signed-in administrator can list Bookings, filter by date, and see per Window: bookings (name, email, seats, reference, status), total seats booked, Capacity and seats left. Realizes UJ-3.

**Consequences (testable):**
- A Booking created by a guest appears in the list without manual refresh beyond reloading the page.
- The per-Window totals match the guest-facing seats-left figure.

### 4.5 Security and personal data *[Core]*
**Description:** Four measures, each with automated tests (success criterion SC9): server-side input validation, hashed passwords, role-based access, and HTTPS. The test cases are in the brief addendum; this section states the requirements. Realizes UJ-1, UJ-3.

**Functional Requirements:**

#### FR-14: Server-side input validation
The server validates every input and rejects invalid or malicious input with a clear error and no data change.

**Consequences (testable):**
- Rejected, with no change: seats 0 / negative / fractional / above available, invalid date, missing or unknown fields, over-long text, invalid email, and SQL or script/HTML payloads in name and email.
- Stored text is output-escaped; a script payload in a name is displayed as text in the admin list.

#### FR-15: Hashed passwords
Passwords are stored only as salted, slow hashes and never logged or returned.

**Consequences (testable):**
- The data store contains no plaintext password.
- Sign-in failure messages do not reveal whether the email exists.
- If guest accounts are built (4.11), weak passwords are rejected `[ASSUMPTION: at least 12 characters and not on a common list]`.

#### FR-16: Role-based access
The server checks the caller's role on every request.

**Consequences (testable):**
- A guest or anonymous caller invoking an admin function is refused (HTTP 403/401) and nothing changes.
- A guest can see and change only their own Bookings; guessing a Booking reference or link does not reveal whether it exists.
- No account can change its own role.

#### FR-17: Booking access by link only
Access to a Booking requires the Manage link token, not the reference alone. `[ASSUMPTION: token validity and whether it is stored hashed are open — see §8]`

#### FR-18: HTTPS `[OPEN: core or if time]`
If included: HTTP redirects to HTTPS, HSTS is set, cookies are Secure and HttpOnly, and email links start with `https://` (a local development certificate is acceptable).

#### FR-19: Personal data documented
The documentation states which personal data is stored (name, email, credentials), why, and how it is protected. `[NOTE FOR PM]` The sources mention only "personal data"; GDPR is not explicitly addressed. For a fictional facility with simulated email this is documentation only.

### 4.6 Look, feel and layout *[Core]*
**Description:** One stylesheet, no design system, Finnish-inspired and calm; laptop layout first. The brief gives no palette, fonts or tone of voice. `[ASSUMPTION: tone is warm, quiet and plain; copy is short and concrete; no sales pressure or urgency tricks]`. Realizes UJ-1, UJ-3.

**Functional Requirements:**

#### FR-20: Finnish-inspired, intuitive website on a laptop screen
The website uses a single English-language stylesheet with a calm, natural Finnish-inspired look, laid out for a laptop-sized screen.

**Consequences (testable):**
- A person who has not seen the site completes an Individual seat booking without assistance `[ASSUMPTION: informal test with 3 people]`.
- Text contrast and keyboard operability meet a baseline `[ASSUMPTION: WCAG 2.1 AA contrast; every booking action reachable by keyboard — the sources set no accessibility level]`.
- Error and sold-out messages state what happened and what the guest can do next.

#### FR-21: Clean assets
Every image, font, icon and name is AI-generated, freely licensed, or checked by the author; none is licensed or trademarked third-party material. The facility name "Saunalöyly" was checked on 2026-10-21 (no TMview hit).

### 4.7 Change and cancel individual seats *[If time — first]*
**Description:** Before the Cutoff (12 hours before start), the guest changes a Booking or cancels it for a Voucher. Seats are never refunded in cash. Change (cancel + rebook) is built first, Voucher last `[ASSUMPTION]`. Realizes UJ-4.

**Functional Requirements:**

#### FR-22: Change Seats
Before the Cutoff, a guest with the Manage link can reduce Seats, cancel some or all, or move the Booking to another Window with room. Realizes UJ-4.

**Consequences (testable):**
- A move to a Window without enough room is rejected and the original Booking is untouched (catalogue E5).
- After the Cutoff, all change actions are refused with an explanation.
- Freed Seats are immediately counted in seats left, and the administrator sees the change.

#### FR-23: Cancel for a Voucher
Before the Cutoff, a guest can cancel and receive a Voucher valid for one year; no cash refund. Realizes UJ-4.

**Consequences (testable):**
- The Voucher amount equals the amount paid for the cancelled Seats.
- The Voucher can be applied to a later Booking `[ASSUMPTION: shared mechanism with gift cards is an architecture decision]`.

**Out of Scope:** cash refunds for individual Seats.

### 4.8 Private sauna booking *[If time]*
**Description:** A guest books one entire Sauna for one Window, via two routes: pick a Window directly (the system assigns a free Sauna) or open a specific Sauna and pick a Window `[ASSUMPTION: assignment rule when several Saunas are free is open]`. The Sauna must hold no Seats in that Window and is then removed from the Seat Capacity. Cancel or change is allowed until 72 hours before start (simulated refund or Voucher valid one year). Realizes UJ-5.

**Functional Requirements:**

#### FR-24: Book a whole Sauna
A guest can book an entire Sauna for a Window if it is not Blocked, not already privately booked, and holds no Seats. Realizes UJ-5.

**Consequences (testable):**
- Two parallel requests for the same Sauna and Window: exactly one succeeds (catalogue C1).
- A request for a Sauna with Seats placed in that Window is rejected; the guest is offered alternatives.
- After a Private sauna booking, the Window's seats left falls by that Sauna's Capacity.

#### FR-25: Seat placement stays consistent
Seat placement follows the Fill order and these invariants after every booking, cancellation, change and Block:
- **INV-1** No Sauna holds more Seats than its Capacity.
- **INV-2** Seats placed equal Seats booked in the Window.
- **INV-3** A privately booked Sauna holds no Seats.
- **INV-4** A Blocked Sauna holds no Seats.
- **INV-5** No earlier Sauna in the Fill order has room while a later one holds Seats.

**Consequences (testable):**
- When Seats are cancelled, the gap is filled from the last-filled Sauna so earlier Saunas are full first (catalogue A2–A5); a Sauna emptied this way is immediately bookable whole.
- A Private sauna booking is accepted only if the existing Seats still fit in the Saunas ahead of it in the Fill order (e.g. 20 Seats ≤ 29 available, catalogue B1).
- Guests are never told which Sauna their Seats are in `[ASSUMPTION: derived placement — computed from the number of Seats rather than stored per Seat — is the v1 approach recommended by research; confidence low-to-medium, proved by model-based testing; see addendum]`.

#### FR-26: Cancel or change a Private sauna booking
Before 72 hours prior to start, a guest can cancel for a simulated refund or Voucher, or move to another time. Realizes UJ-5.

**Consequences (testable):**
- Capacity is restored and visible to the administrator.
- After the Cutoff, changes are refused.

### 4.9 "My booking" resend *[If time]*
**Description:** A guest who lost their email enters reference + email and receives the Manage link again. The page gives the same answer whether or not a Booking matches, and is rate-limited per email and per address. Realizes UJ-4.

#### FR-27: Resend Manage link
**Consequences (testable):**
- The response is identical for matching and non-matching input.
- Repeated requests are throttled per email and per source address.
- Reference + email alone never opens the Booking; only the link in the email does.

### 4.10 Seat Hold during payment *[If time]*
**Description:** When the guest starts payment the Seats are held for 10 minutes (fixed, not an admin choice). A Hold is stored with an expiry and is ignored after expiry even if cleanup has not run. A Hold alone does not prevent double-booking; the atomic check in FR-8 still applies.

#### FR-28: Hold Seats for 10 minutes
**Consequences (testable):**
- Held Seats are excluded from seats left for others until the Hold expires.
- Payment confirmed after expiry creates a Booking only if the Seats are still free; otherwise no Booking and a simulated refund, with a clear message.
- Repeated or out-of-order payment confirmations never create two Bookings or two refunds.

### 4.11 Guest accounts *[If time]*
**Description:** Optional accounts for guests. Anonymous Bookings are not linked to an account created later.

#### FR-29: Optional guest account
**Consequences (testable):**
- Booking works identically without an account.
- A guest with an account sees their own Bookings only.

### 4.12 Administrator screens and rules *[If time — last part of v1]*
**Description:** Administrators manage Windows, Capacity and prices in screens, and adjust five settings. Changed settings affect only new Bookings. Blocks, the 06:00 rule, whole-only Windows and the overbooking fallback belong here. Realizes UJ-3.

#### FR-30: Manage Windows, Capacity, prices, Fill order
**Consequences (testable):**
- Overlapping Windows are refused (FR-11).
- Capacity decrease is refused while a future Window would be over-booked `[ASSUMPTION F1 — alternative: treat as overbooking]`.
- A Fill order change applies only to Windows that have not started `[ASSUMPTION F2]`.

#### FR-31: Five adjustable settings
| Setting | Default | Limit |
|---|---|---|
| Booking horizon | 4 weeks ahead | — |
| Last booking time | 5 min after Window start | — |
| Change / voucher Cutoff, Seats | 12 h before start | not under 2 h |
| Cancel / change Cutoff, private Sauna | 72 h before start | not under 2 h |
| Seats opening for individual booking | 06:00 same morning (not privately booked Saunas); time changeable or off | — |

**Consequences (testable):** A changed setting applies to new Bookings only.

#### FR-32: Blocks
An administrator can Block one, several or all Saunas for a period. Realizes UJ-3.

**Consequences (testable):**
- A Blocked Sauna cannot be booked whole and holds no Seats.
- The administrator sees affected Bookings before confirming the Block.
- If remaining capacity is too small, the most recent whole Bookings lose and are fully cancelled with refund or Voucher regardless of Cutoffs (D3).
- A privately booked Sauna that is Blocked is cancelled with refund or Voucher regardless of Cutoff (D4).
- Lifting a Block moves Seats back so INV-5 holds (D7 `[ASSUMPTION]`).
- A Block in an already started Window moves no Seats; the overbooking fallback applies (F3).

#### FR-33: Whole-booking-only Windows
An administrator can mark a Sauna and Window as whole-booking-only. `[ASSUMPTION D8: refused while Seats are placed there]`.

#### FR-34: Overbooking fallback
If capacity is lost after Bookings exist, the most recent Booking loses, is cancelled in full and refunded, and the guest receives an apology email.

### 4.13 Gift cards *[Step 2 — first]*
A guest buys a gift card without an account; it is emailed as a code, usable for Seats and for private Saunas, with remaining balance, partial payment, and a one-year expiry. Success criterion SC5.

#### FR-35: Buy and redeem a gift card
**Consequences (testable):** A code can be used until its balance is zero; a partly used card keeps its balance; an expired card is refused.

### 4.14 Door codes *[Step 2]*
Saunas marked as having a self-service lock get a door code emailed to exactly the guests entitled to that door, at a time the administrator chooses (default 20 min before the Window), valid from sending until the Window ends. Success criterion SC6.

#### FR-36: Send door codes
**Consequences (testable):**
- No rule depends on withdrawing a code already sent.
- Codes for consecutive Windows on one door are different.
- After sending, a Private sauna booking is refused while Seat holders hold the Sauna's code (H12).
- A Block after sending triggers a correction email to Seat holders (H13).
- The email is sent only when the (simulated) lock confirms the code; the administrator is warned otherwise (H11).

**Notes:** `[NOTE FOR PM]` Real lock behaviour (two different PINs on one lock; editing a code after it becomes valid) is untested. Optional step-2 variants: gradual opening of Saunas and one-Sauna access, where placement is frozen at send time (replaces the earlier "moves any time" rule).

### 4.15 Mobile layout *[Step 2 — last]*
#### FR-37: Mobile and any window size
The website works on a phone-sized screen and any window size with the same stylesheet. Success criterion SC10 (mobile part).

### 4.16 Vision (not built)
Multiple facilities, child/adult pricing, memberships, period cards, remote door control, heating and temperature control, multiple websites on one platform, real payment/email/languages.

## 5. Non-Goals (Explicit)
- Not a real payment, email, door, heating or temperature system — all simulated.
- Not a marketplace or multi-facility product; one facility, one website, one API in v1.
- No multi-language support; English only.
- No native mobile apps.
- No cash refunds for individual Seats.
- No performance or throughput guarantees.
- No sauna etiquette, age or safety rules engine `[NON-GOAL for MVP]`; age limits come with child pricing (Vision).
- No waiting list, no dynamic or demand pricing `[ASSUMPTION: comparable services offer a waiting list; not in the sources]`.
- The product does not claim to be a live service.

## 6. MVP Scope

### 6.1 In Scope
**v1 core:** FR-1 to FR-21 — browse, book Seats, simulated payment, confirmation, capacity integrity, admin sign-in and booking list, security measures with tests, Finnish-inspired laptop website. SC1, SC9, and the laptop part of SC10 define "core done".

**v1 "if time", in this order:** change/cancel Seats (4.7) → Private sauna booking (4.8) → "My booking" (4.9) → Hold (4.10) → guest accounts (4.11) → admin screens and rules (4.12). Cancellation comes before Private sauna booking (decided). The order after the first two is a proposal.

### 6.2 Out of Scope for MVP
- **Step 2:** gift cards, door codes, mobile layout (last).
- **Vision:** everything in 4.16.
- Planning is limited to the core; the freeze is 9–15 December (tests, README, AI documentation, no new features).

`[NOTE FOR PM]` The core is deliberately narrow. The teacher rated scope "large risk". The "if time" list is sized for what is left after the core, not for a commitment.

## 7. Success Metrics

*Goals are defined by the brief's success criteria (SC). Not met = "not delivered", reported plainly.*

**Primary**
- **SM-1**: Seat booking works end to end and concurrency holds — SC1: 4 seats booked and paid, confirmation received, admin sees the Booking; the last-seat race leaves exactly one winner in 100 repeated parallel runs, with zero over-capacity results. Validates FR-4 to FR-10.
- **SM-2**: Security measures pass automated tests — SC9: all validation, password, access-control (and HTTPS if included) cases pass. Validates FR-14 to FR-18.
- **SM-3**: The core website works on a laptop screen — SC10 (laptop). Validates FR-1 to FR-3, FR-20.

**Secondary**
- **SM-4**: Private sauna booking, change/cancel and adjustable rules behave as specified with defaults — SC2, SC3, SC4, SC8, if built. Validates FR-22 to FR-34.
- **SM-5**: Unassisted booking — 3 of 3 people complete a seat booking without help `[ASSUMPTION]`. Validates FR-20.
- **SM-6**: Gift cards, door codes, mobile layout — SC5, SC6, SC10 (mobile), step 2.

**Counter-metrics (do not optimize)**
- **SM-C1**: Number of features delivered — must not rise at the cost of tests on concurrency, capacity and validation. Counterbalances SM-4.
- **SM-C2**: Booking speed — must not be bought by weakening the atomic capacity check (FR-8). Counterbalances SM-1.
- **SM-C3**: Booking conversion — no urgency pressure or hidden fees; total price shown early. Counterbalances SM-5.

## 8. Open Questions
1. Database: SQLite or PostgreSQL? Concurrency research covers only PostgreSQL; the platform must run locally without extra infrastructure.
2. HTTPS: core or if time? (Lisa postponed.)
3. Exact limits: maximum seats per booking, text lengths, password rules.
4. Manage link token: validity period, stored hashed?
5. Admin edge cases awaiting a decision (each with a research recommendation): D3, D7, D8, F1–F3.
6. Door codes (step 2): H6 overlapping codes, H10, H11, H13–H15, H23; real lock behaviour untested.
7. Does the "if time" order after change/cancel and Private sauna hold? Backcasting from 15 December has not been run.
8. Which Sauna is assigned when a Window is booked privately via the direct route and several are free?
9. Accessibility level: confirm WCAG 2.1 AA as baseline.
10. Palette, typography and copy tone for the Finnish-inspired look.
11. Privacy: how far should GDPR documentation go for a fictional facility?
12. Brief length is over its target; it also has stale wording (see addendum).

## 9. Assumptions Index
- §2.3 — Protagonist names are placeholders.
- 4.1 — Private sauna entry hidden until 4.8 exists.
- FR-2 — Greyed-out full Windows with the next available suggestion.
- FR-5 — A test switch can force payment failure.
- FR-7 — One Window per Booking; no combined cart.
- FR-15 — Guest password minimum 12 characters and common-password check.
- FR-17 — Token validity and hashing open.
- 4.6 — Tone is warm, quiet, plain.
- FR-20 — Unassisted-booking test with 3 people; WCAG 2.1 AA baseline.
- 4.7 — Change built before Voucher; Voucher mechanism shared with gift cards.
- 4.8 — Assignment rule for the direct route; derived placement as the v1 approach.
- FR-30/33 — F1, F2 and D8 recommendations adopted.
- FR-32 — D7: lifting a Block moves Seats back.
- §5 — Waiting list not in v1.
- §7 — SM-5 target.
