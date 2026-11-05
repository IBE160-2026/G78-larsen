# Source extract: Saunalöyly Booking Platform (UX run, 2026-11-05)

Extract only: no design proposals. Source terms are verbatim and capitalised as in the PRD.

**Sources:** `PRD` = prd.md; `Add` = PRD addendum.md; `Arch` = ARCHITECTURE-SPINE.md; `Brief` = brief.md. Where they disagree the PRD rules, and §14 lists the disagreement. A brief addendum, a research catalogue and a teacher's feedback file are cited by the PRD but were not read for this extract. Case IDs such as A6, B1, D3 and H12 refer to that catalogue.

**Markers:** `[A]` = tagged `[ASSUMPTION]` in the source (not confirmed by Lisa). `[Core]`, `[IT-n]` (If time, item n), `[S2]` (Step 2) and `[Vision]` give the delivery phase.

---

## 1. Glossary

All from PRD §3, unless noted. The phrase "whole booking" is never used, because it is ambiguous.

| Term | Meaning |
|---|---|
| Venue | Saunalöyly, the one fictional sauna venue in v1. Four or more Saunas. |
| Venue time | Local time at the Venue (Europe/Oslo). All PRD times are Venue time. |
| Sauna | One sauna room with a Capacity and one or more doors. Examples: Sauna 1 = 7, Sauna 2 = 10, Sauna 3 = 12, Sauna 4 = 15 (44 total). Named smallest to largest Rauha, Löyly, Kajo, Lumo. |
| Capacity | The number of Seats a Sauna holds. |
| Window | A bookable time slot, the same for every Sauna. Standard length 1 h 30 min. No two overlap; intervals are half-open. |
| Seat | One guest's place in a Window. Identical; in the guest's view not tied to any Sauna. |
| Seat booking | A Booking of 1 to 10 Seats in one Window. |
| Whole-sauna booking | A Booking of one entire Sauna for one Window. Guests see it as "Private sauna". |
| Booking | A Seat booking or a Whole-sauna booking. Has a Booking reference, Guest's name and email, price paid, and status active or cancelled. A Change is history, not a third status. |
| Booking reference | Short code identifying a Booking in messages and lists. Gives no access on its own. |
| Change | Seat booking: moving Seats to another Window, or giving up Seats for a Voucher. Whole-sauna booking: cancelling or moving it. Guests cannot cancel Seats for money. |
| Guest | Anyone using the public website to find a Window, make a Booking or buy a Gift card. Anonymous by default, or holds a Guest account. |
| Guest account | Optional account to see one's own Bookings [IT-6]. |
| Seat booker | A Guest who holds a Seat booking in a given Window. |
| Administrator | Staff user with an Administrator account. Core has one seeded; more can exist. |
| Open for Seats | A Sauna in a Window that is not Whole-sauna-booked, not Blocked, and not an unreleased Whole-booking-only Sauna. |
| Seat capacity | For a Window, the sum of Capacity over Saunas open for Seats. In Core, the sum of all Capacities. |
| Seats left | Seat capacity minus Seats booked, and minus Seats held once Holds exist. |
| Fill order | Administrator-set order in which Seats are counted into Saunas; each is filled before the next. |
| Placement | Which Sauna each booked Seat is counted in. Bookkeeping, not an assignment; Guests are never told a Sauna. |
| Room ahead | For a Sauna S in a Window, the summed Capacity of Saunas before S in the Fill order that are open for Seats. |
| Block | A period in which one or more Saunas cannot be booked and hold no Seats. |
| Bookable whole | Standing Administrator mark on a Sauna that lets it be sold as a Whole-sauna booking at all. |
| Whole-booking-only | Administrator's per-Window mark keeping a Bookable-whole Sauna out of Seat sales so a group can book it whole. |
| Release time | When a Whole-booking-only Sauna not yet Whole-sauna-booked becomes open for Seats. Default 06:00 on the day of the Window: "the 06:00 rule". |
| Booking horizon | How far ahead a Window can be booked. Default 4 weeks before the Window starts, counted from the moment of booking. |
| Booking deadline | Last moment a Window can be booked. Default 5 minutes after it starts; never later than 45 minutes before it ends. |
| Cutoff | Last moment a Guest can Change a Booking. Default 12 hours before start (Seat booking), 72 hours (Whole-sauna booking). Never less than 2 hours. |
| Setting | One of the five rules the Administrator can adjust (FR-39). Everything else is fixed in v1. |
| Manage link | Link in the confirmation email, carrying a long random token. The only way back into a Booking for a Guest without an account [IT-2]. |
| Voucher | Credit issued by email in place of money, when giving up Seats or by choice on cancellation. Valid one year from issue. |
| Gift card | A purchased code with a balance, used like a Voucher [S2]. |
| Hold | Temporary reservation of Seats for 10 minutes, never past the Booking deadline, while a Guest completes payment [IT-5]. Seats only. |
| Simulated payment | A payment step that moves no real money and needs no keys or external service. Refunds simulated the same way. |
| Test switch | Start-up setting from a git-ignored local file, off by default, never changeable through the API. |
| Outbox | The store of simulated emails. Stands in for Guests' mailboxes; holds links and codes as sent. Only Administrators can list it. |
| Overbooking fallback | If Seats booked ever exceed Seat capacity, the Seat booking with the latest Entry time loses. |
| Entry time | When a Seat booking's Seats entered their Window: creation, or the Change that moved them in. |
| Remedy page | Page reached by the link in the apology email (the remedy link), where a Guest chooses a refund or a Voucher (FR-42). |
| Door code | A PIN for one Sauna door, valid for one Window [S2]. |
| Send time | When Door codes for a Window are emailed. Default 20 minutes before start [S2]. |

**Further UI labels and terms used in the PRD:** Book seats; Private sauna; Before you come; My booking; Manage booking (§7); Pay; "1 seat left"; Gradual opening (FR-50); booker (FR-46). Finnish words with glosses are in §10.

---

## 2. Actors and roles

| Actor | Can do | Source |
|---|---|---|
| Guest (anonymous) | Browse Venue; find a Window; book and pay for 1–10 Seats with name and email only. Later: Private sauna, Change via Manage link, resend link, Voucher, Gift card. | PRD §3, §4.1, §4.2 |
| Guest segments | **Regulars** want availability and price within a few clicks. **First-timers** also need what to expect, how to behave, how to stay safe. | PRD §2 |
| Group | Takes a whole Sauna ("We want the sauna to ourselves"). | PRD §2.1 [IT-3] |
| Seat booker / Whole-sauna booker | Holder of a Booking; recipient of confirmations and, in S2, Door codes. | PRD §3, FR-46 |
| Guest with a Guest account | Sign up, in and out; see Bookings made while signed in. Cannot reach Administrator functions or change own role. | FR-37 [IT-6] |
| Gift card buyer / holder | Anyone can buy without an account; whoever holds the code can pay with it. | FR-43, FR-44 [S2] |
| Administrator | Core: sign in/out, read-only booking list, Outbox. IT-7: Windows, Capacity, prices, Fill order, Bookable whole, five Settings, Blocks, Whole-booking-only marks, Placement view. S2: Gift cards, doors, locks, codes, Send time, Gradual opening. | §2, §4.4, §4.13, §7 |

**Out of scope / non-users:** the examiner (no examiner features; runs it locally from the README, uses the README test login to see the Outbox: §2.2, §4.4); members and period-card holders, children as a separate guest type, other venues and websites (§2.2, Vision). Administrator accounts are created only through the seed or a documented command, with no sign-up (FR-15, AD-18).

---

## 3. Named personas and journeys

**Protagonist names are placeholders** `[A: no named personas exist in the sources; Lisa may replace them]`. Prices are illustrative (§2.3). Journey times are mostly not on the seed schedule (see §14, C1).

### Jobs To Be Done (PRD §2.1, verbatim)
- Guest: "I want to see in seconds whether there is room for us on Saturday afternoon, and what it will cost in total."
- Guest: "Once I have paid, I want to be certain the seats are mine, not find a double booking at the door."
- Guest: "If plans change, I want to move my booking or get credit without writing to anyone." *(If time)*
- Group: "We want the sauna to ourselves." *(If time)*
- Administrator: "I want to see who is coming to each window and how full it is, without doing arithmetic."
- Administrator: "I want the system to refuse anything that would break capacity, so I never have to turn a paying guest away at the door."
- Administrator: "When a sauna needs repair, I want to close it and have the affected guests handled by clear rules." *(If time)*

### UJ-1. Ingrid books two seats for Saturday afternoon [Core]
Ingrid has tried a public sauna once, wants to take a friend, does not want to create an account. Anonymous, on a laptop, at the landing page.
1. Chooses **Book seats**, picks Saturday, sets 2 seats.
2. Page lists Saturday's Windows with Seats left in each and the total for 2 seats. A Window with only 1 seat left is shown as unavailable, labelled "1 seat left".
3. Picks 15:00–16:30, enters name and email.
4. A review page repeats the Window, seats and total (NOK 500 at NOK 250 per seat) and says that a booking for a fixed date cannot be withdrawn.
5. Accepts the terms and presses **Pay NOK 500**.

Climax: confirmation page shows Booking reference, Window, 2 seats, total, and the confirmation email exactly as sent. Resolution: "She has a reference and an email she can keep"; the Window shows 2 fewer Seats left. Edge case: if someone took the last seats while she was typing, she is told how many Seats are actually left and offered the nearest Windows with room for 2. Nothing is charged.

### UJ-2. Aino and Jonas reach for the last seat at the same moment [Core]
Both on the review page with 1 seat for Friday 18:00–19:30 (1 Seat left), both anonymous, both press Pay within the same second. Exactly one gets a confirmation. The other is told no seat is left, is not charged and gets no email. Window shows 0 Seats left; the Administrator's list shows one new Booking.

### UJ-3. Katja checks who is coming tonight [Core]
Katja runs the evening shift. Not signed in, on the Administrator sign-in page.
1. Signs in with email and password.
2. Opens today's booking list: Windows in time order, each with Seat capacity, Seats booked and Seats left, and under each Window its Bookings with reference, name, email, seats and total.
3. Opens the Outbox to check that a guest's confirmation went out.

Climax: sees at a glance that 18:00–19:30 is full and 20:00–21:30 has 9 Seats left. Resolution: signs out. A Guest who types the Administrator address is refused.

### UJ-4. Ingrid's friend falls ill [IT-2]
Friday morning, more than 12 hours before the Window, Ingrid needs only one of two seats. Has the confirmation email with its Manage link. Opens the link, chooses to give up 1 of 2 Seats, confirms. Page confirms the change and shows the email with her Voucher, worth one seat and valid for one year. Freed Seat is bookable at once; later she uses the Voucher.
Edge cases: within 12 hours of the start, the Manage link still shows the Booking but every change is refused with the reason. If she lost the email, she enters Booking reference and email on the "My booking" page and is sent a new Manage link (§4.10).

### UJ-5. Olav books a whole sauna for a family reunion [IT-3]
Wants privacy for 10 relatives on a Sunday morning. Anonymous, on the landing page.
1. Chooses **Private sauna**, picks Sunday.
2. Page lists each Sauna bookable whole that day, with size, price and free Windows. Picks 10:00–11:30 in the 12-seat Sauna 3.
3. Reviews and pays.

Climax: confirmation names Sauna 3 and the Window; nobody else can book Sauna 3 or a Seat in it for that Window. Seats left drops by 12. He can cancel for a refund or a Voucher until 72 hours before start. Edge case: if Seats already booked would no longer fit in the Saunas ahead of Sauna 3, Sauna 3 is not offered; Saunas later in the Fill order may still be.

### UJ-6. Katja closes Sauna 3 for repairs [IT-7]
Stove repair next Tuesday 14:00–17:00. Signed in, in the blocking calendar. Selects Sauna 3 and the period. Before confirming, sees each affected Window, how many Seats will be counted into other Saunas, and any Booking that would lose its place. Confirms. Seat bookings move into other open Saunas without Guests noticing. Where capacity runs out, the latest Seat bookings are cancelled in full and their Guests are emailed a choice between a refund and a Voucher. Sauna 3 shows as Blocked for those Windows; Seats left reflects lower capacity.

### Brief's guest journey (Brief, "The guest's journey")
Guest first chooses **Individual seats** or **Private sauna**, picks a date in a calendar, sees the time windows, picks a window and number of seats, presses Book, logs in or continues without an account, accepts terms, pays. In the core every guest continues without an account. (Differs from the PRD: §14, C3.)

---

## 4. Stated needs and requirements with a UI surface

### 4.1 Guest, Core

| ID | User-visible behaviour |
|---|---|
| FR-1 Landing page | Open without signing in; start a Seat booking in one step. Shows: Venue name and short description; **Book seats** action; links to terms and privacy notice; "Before you come" section (see below), directly linkable. Website presents the Venue: the Saunas as places to visit, each with one image and one line, worded so a Seat booking never seems to choose one; opening hours and the Window schedule; price per Seat (and per Sauna once §4.9 exists); fictional address and contact details. **Book seats** opens date and Seat selection directly. §4.1: page says in a few lines what Saunalöyly is and offers one main action. **Private sauna** entry appears only once §4.9 is built. |
| FR-1 "Before you come" content `[A beyond the two towels and bathing rules]` | **Etiquette:** bring two towels, one of them to sit on; ask the others before throwing water on the stones; follow the swimwear rule. **Safety:** bring water and drink plenty; alcohol is not allowed at the venue; keep rounds to 5–10 minutes, and leave the sauna if you feel unwell; bathe with caution, and never alone; children must be supervised by an adult. **Practical:** changing time is part of the Window. |
| FR-2 Date and Seats | Choose a date and a whole number of Seats, 1 to 10. A date is choosable only if it has at least one Window inside the Booking horizon and before that Window's Booking deadline. Date can be typed as well as picked; date control works with keyboard alone. A number outside 1–10 cannot be submitted. |
| FR-3 Windows with Seats left | For chosen date and number: every bookable Window with start and end, Seats left, total price for the chosen number. Seats left matches the Administrator's list. Too few Seats left: shown as unavailable and not selectable, with a text label such as "1 seat left"; colour alone never says so. No room on the date: offers up to three nearest Windows that do, same day first, then following days within horizon `[A]`. Past-deadline Window not offered. No countdown, "people viewing" count, padded number or other urgency cue; any scarcity text states the true current Seats left. Total = Seats × price per Seat, NOK incl. VAT, and is the amount charged. |
| FR-4 Seats, not Saunas | Flow never asks to choose a Sauna, never shows which Sauna Seats are placed in. No page or email in the Seat booking flow shows a Sauna identifier. Flow states in plain words: the Guest books Seats in the shared Saunas; on site the Guest may move freely between Saunas open for Seats; a group that wants to stay together should book a Private sauna (once §4.9 exists). |
| FR-5 Details and review | Name: free text 1–100 chars; email: valid, max 254 `[A]`. Nothing else is asked. Before the pay button, on the details page or a separate review step: Window, Seats, total in NOK incl. VAT; Venue's identity and contact details; booking terms, including no right of withdrawal for a fixed date (angrerettloven § 22 m) and what the Guest can and cannot Change afterwards. Until §4.8 is built, terms state a Booking cannot be changed or refunded online. Must accept the terms before paying. Links to full terms and privacy notice. Going back keeps everything entered. |
| FR-6 Payment | Pay button states obligation and amount, e.g. "Pay NOK 500" (angrerettloven § 16). Pay step carries "Simulated payment: no money moves". Success creates the Booking at once and reduces Seats left by the Seats booked. Double click, reload or retry never creates two Bookings; a repeat returns the first outcome: a Guest who was booked sees the confirmation again, never "no Seat free". |
| FR-7 Failed payment | Creates no Booking, takes no Seats, sends no email. Guest sees a message with a way to try again. |
| FR-8 Confirmation | Page and email both show: Booking reference; date and Window; number of Seats and total paid; Guest's email; what happens next; booking terms; link to "Before you come". Page shows the email as sent. Opens only in the browser session that paid, for as long as that session lasts `[A]`; reload in that session shows it again. No Manage link in Core `[A]`. |
| FR-9 One Window per Booking | Several Windows mean several Bookings paid separately. No combined basket (§9). |
| FR-11 Last-Seat race | Loser told no Seat is free, not charged, no email, holds nothing; page offers nearest Windows with room. |
| FR-12 All or nothing | A request for more Seats than left is rejected whole. Message states how many Seats are actually left; page offers nearest Windows with room. |
| FR-14 Conflicts | "No seat free" (definite loss) and "please try again" (retries used up) are different messages. Either leaves nothing written. |
| FR-18 Validation | Invalid input is rejected with a clear error and no data change. Script/HTML shown only as escaped text. |
| FR-21 Privacy | Privacy notice linked wherever data is collected, separate from terms. States what is stored and why, legal basis, retention and who sees it, Guest's rights including complaint to Datatilsynet. No consent banner. No marketing email. |
| FR-22 Look | Every Core page on a laptop without horizontal scrolling. Error and sold-out messages state what happened and what the Guest can do next. "Sold out" is availability information with alternatives, not an error. |
| FR-23 Accessible | See §9 here. |

### 4.2 Guest with a Manage link [IT-2, IT-3]

| ID | User-visible behaviour |
|---|---|
| FR-25 Manage link | Opens that Booking and nothing else. Shows the Booking until its Window ends; Changes possible only before the Cutoff. Invalid, expired or replaced link gives the same response as one that never existed. New link stops the old one. Any Change needs an explicit confirming action; loading a page alone changes nothing. Confirming twice applies once and returns the first outcome. |
| FR-26 Move Seats | Before Cutoff, move some or all Seats to another Window with room (inside horizon, before its deadline). Atomic: no room, nothing changes. Partial move splits: moved Seats become a new Booking with own reference and Manage link, emailed at once and shown on the result page; original keeps reference and link, with fewer Seats. Full move keeps the reference. Move costs nothing extra. Each move sends a confirmation email shown on the result page. After Cutoff, refused with an explanation. |
| FR-27 Voucher instead of Seats | Before Cutoff, give up some or all Seats for a Voucher worth the price paid for them `[A]`. Emailed with code, value, expiry (one year after issue); result page shows that email. No money refunded. |
| FR-33 Cancel or change Whole-sauna booking | Before 72-hour Cutoff: cancel, choosing a Simulated refund or a Voucher valid one year; or move to another Window. Move where the Sauna is not available whole is rejected, original untouched. Move keeps the same Sauna unless the Guest picks another available one `[A]`. Move to a Sauna with a different price is refused with the reason, and the Guest can cancel and book again. Every cancellation or move sends a confirmation email. After Cutoff, refused with an explanation. |

### 4.3 Guest, other If-time flows

| ID | Phase | User-visible behaviour |
|---|---|---|
| FR-28 Pay with a Voucher | IT-2 | Voucher code pays all or part; rest by Simulated payment `[A]`. Remaining value stays until expiry. Expired, used-up or unknown code refused with the same message. Never paid out in money. |
| FR-29 Book a whole Sauna | IT-3 | Allowed when: Sauna Bookable whole, Window inside horizon and before deadline; not Blocked and not already Whole-sauna-booked; Seats booked (plus held) ≤ Room ahead (unreleased Whole-booking-only skips this); and Window has not started, or has no Seat booking, or Sauna is not open for Seats. **Review page says the Sauna is not held while the Guest pays.** Checked again at payment; if taken meanwhile, nothing is charged. Seats left drops at once by the Capacity when the Sauna was open for Seats. |
| FR-30 Choose the Sauna | IT-3 | For a date, Private sauna page lists each Sauna bookable whole, with Capacity, price, free Windows. Guest picks a Window in that list, or opens one Sauna and picks a Window there. Only FR-29-valid pairs listed. Guest always picks the Sauna. Confirmation names Sauna and Window. §7: "Window → Sauna, or Sauna → Window". |
| FR-34 Resend Manage link | IT-4 | "My booking" page: enter Booking reference and email. Same response for match and no match; page shows no Booking data. On match, new Manage link emailed (Outbox only) and old one stops. Limit 5 per hour per email and per source address `[A]`. |
| FR-35 Hold | IT-5 | When Guest presses Book, Seats held 10 minutes. **Guest is not told: no page or email mentions it or shows a time limit.** Other Guests see held Seats as taken, with no comment. Going back and choosing another number resizes the Hold; if extra Seats are not free, old Hold stays and the Guest is told. Guest pressing Cancel releases it at once. Failed payment keeps it. Expiry never discards what was entered. |
| FR-36 Late payment | IT-5 | After expiry: creates a Booking if Seats still free and deadline not passed. Otherwise no Booking, no charge, Guest told why. |
| FR-37 Guest account | IT-6 | Sign up with email and FR-19 password `[A]`. Sign-up reply does not reveal whether the email has an account; account confirmed through emailed link. Password reset by emailed link. **Choice to sign in appears after Book; continuing without an account is the default and the most prominent option.** Signed-in Guest sees only Bookings made while signed in, books with the account's email. Earlier anonymous Bookings are not attached. |
| FR-42 Remedy | IT-7 | See §6 here. Guest chooses once between refund and Voucher on the Remedy page. |

### 4.4 Gift card buyer and holder [S2]

| ID | User-visible behaviour |
|---|---|
| FR-43 Buy | Without an account, Simulated payment. Chooses a fixed value, or an amount up to a limit. Before purchase, told about the 14-day right of withdrawal `[A]`. Emailed code, value, expiry (one year after issue), states not paid out in money; can print or forward. |
| FR-44 Pay | Pays all or part of a Seat or Whole-sauna booking, rest by Simulated payment; with or without an account. Balance stays until expiry. Expired or used-up card refused. No fees after sale. |

### 4.5 Administrator, Core

| ID | User-visible behaviour |
|---|---|
| FR-15 Sign-in | Email and password. Wrong email and wrong password give the same message. After 5 failed sign-ins in a row for one email, further attempts for that email refused for 15 minutes, even with the correct password `[A: values]`; success resets. Refusal gives the same message as a wrong password, for any email known or not. After sign-out, the session grants nothing. |
| FR-16 Booking list | List Bookings of a chosen date, grouped by Window `[A]`. Per Window: start and end; Seat capacity, Seats booked, Seats left. Per Booking: reference, name, email, Seats, total, time of booking. New Booking appears on next page load. Figures equal what Guests see. Stored text is shown escaped. Read-only (§4.4). Once Changes exist: status active or cancelled, history entries (what moved or was given up, when, any Voucher); a cancelled Booking stays with time, cause (Guest, Block or Overbooking fallback) and the Guest's choice, and is not counted in Seats booked. |
| FR-17 Outbox | Lists each email with time, recipient, subject, full body, links in plain text. Guests refused. |
| FR-19 Passwords | Apply on seed or documented command only in Core. Pasting and password managers both work. |
| FR-20 Roles | Anonymous call to Administrator function: refused as not signed in. Signed-in Guest: refused as not allowed. |

### 4.6 Administrator, later

Screens of §4.13 are outside this UX round (§7), recorded so that Core pages leave room.

| ID | Phase | User-visible behaviour |
|---|---|---|
| FR-31 | IT-3 | Administrator can see the Placement of each Window. |
| FR-38 | IT-7 | Create and edit Windows, one at a time; set Capacity, price per Seat, price per Sauna; choose Bookable whole and Fill order. New Windows default to 1 h 30 min; a single Window may have another length Venue-wide. Overlap refused. Capacity decrease refused while a not-started Window would overflow. Fill order applies to Windows not started. Price change applies to new Bookings only; a Guest at the review page pays the price shown. Window with Bookings or Holds cannot be deleted or moved. Can create and see Windows beyond the horizon. |
| FR-39 | IT-7 | Change five Settings (limits in §5). Refused changes that conflict with a Whole-booking-only Window name the Windows. |
| FR-40 | IT-7 | Block one, several or all Saunas for a period; lift a Block. Blocking calendar shows, for a chosen period, each Window with Seats booked and Seats left, each Sauna's Whole-sauna bookings and Whole-booking-only marks, and each Block. Preview before confirming; if affected Bookings or Holds changed, nothing is applied and a new preview is shown. |
| FR-41 | IT-7 | Mark or unmark Whole-booking-only. Refused while Seats placed in it (held included), if not Bookable whole, or if Release time is later than the Booking deadline. |
| FR-42 | IT-7 | Sees each cancelled Booking with its remedy: pending, refunded or Voucher. |
| FR-43 | S2 | Sets fixed values and limit; lists Gift cards sold with value, balance, expiry. |
| FR-45 | S2 | Registers doors; marks self-service locks; per door, code source (by hand or simulated lock) and "replaceable" mark. Per-Block door-code override. |
| FR-47, FR-49 | S2 | Sets Send time; alerted if a code is unconfirmed at the Send time; sees codes of every Window and resends. |
| FR-50 | S2 | Turns on Gradual opening and sets the maximum (default all Saunas). |

### 4.7 System requirements with UI effects only

FR-10 (Seats booked never exceed Seat capacity), FR-13 (Windows Venue-wide, seed always gives bookable dates), FR-24 (HTTPS only [IT-1]: every email link starts `https://`), FR-32 (Seat and Whole-sauna requests never interleave), FR-46 and FR-48 (Door-code recipients, see §7 here), FR-51 (mobile, see §8 here).

**NFRs with a UI surface:** NFR-3 (Venue time), NFR-4 (NOK incl. VAT; a Booking keeps its price), NFR-5 (English only), NFR-9 (no dark patterns anywhere: no countdown timers, false scarcity, pre-ticked options or hidden fees), NFR-10 (nothing shown is faked; data survives restart), NFR-11 (time rules checked at request time).

**Counter-metrics (§11):** SM-C2: speed must never be gained by skipping the review page or dropping FR-5 information. SM-C3: no urgency, false scarcity or hidden fees. SM-C4: visual polish must not use up the freeze or test time.

---

## 5. User-visible rules and limits

### Venue, capacity and time
| Rule | Value | Source |
|---|---|---|
| Saunas (seed) | Rauha 7, Löyly 10, Kajo 12, Lumo 15 = 44 Seats; filled in that order | §3, §12 Q3, Add J |
| Opening hours (seed) | Every day 10:00–22:00 Venue time, the same each day | Q3, Add J |
| Windows (seed) | Eight back-to-back Windows of 1 h 30 min, starting 10:00, 11:30, 13:00, 14:30, 16:00, 17:30, 19:00, 20:30; last ends 22:00; no changeover gap | Q3, Add J |
| Daily and total | 352 Seats a day; about 230 Windows generated from the run date through the horizon | Add J |
| Changing time | Part of the Window | FR-1 |
| Seats per Booking | Whole number 1 to 10 | §3, FR-2 |
| Windows per Booking | Exactly one | FR-9 |
| Name / email | 1–100 chars / valid, max 254 `[A]`; nothing else asked | FR-5 |
| Time zone | All times Venue time (Europe/Oslo), including across DST `[A]`; a Window belongs to its start date; a Window starting or ending in a skipped or repeated hour is refused | §3, NFR-3 |
| Age / group rules | None enforced. No distinction between children and adults; every Seat costs the same. "No rules engine for etiquette, age or safety." Children must be supervised by an adult is information only. Age rules come with child pricing [Vision: under 14 by default] | §9, FR-1, §4.17 |

### Settings (FR-39; fixed in Core; editable from IT-7)
| Setting | Default | Limit |
|---|---|---|
| Booking horizon | 4 weeks before the Window starts | never more than 1 month |
| Booking deadline | 5 minutes after the Window starts; may be set earlier (even before the start) or later | never later than 45 minutes before the Window ends |
| Cutoff, Seat bookings | 12 hours before the start | not under 2 hours |
| Cutoff, Whole-sauna bookings | 72 hours before the start | not under 2 hours |
| Release time (06:00 rule) | 06:00 on the day of the Window; another time or off | never later than the Booking deadline of the Window it applies to |

Changed Cutoff: applies only to Bookings made after the change. Changed horizon, deadline or Release time: applies at once to every Window not yet affected `[A]`. Horizon and deadline apply to Seat bookings, Holds, Whole-sauna bookings and the target Window of every Change `[A]`.

### Timers and expiry
| Item | Value | Source |
|---|---|---|
| Hold | 10 minutes, fixed, not a Setting; ends at the earlier of 10 minutes and the Booking deadline; one per browser session per Window; not shown to Guest | FR-35 |
| Whole-sauna Hold | None | §3, FR-29 |
| Voucher validity | One year from issue | §3, FR-27 |
| Gift card validity | One year after issue | FR-43 |
| Remedy link | 30 days, even after the Window has ended; no choice in 30 days means a Simulated refund `[A]` | FR-42 |
| Manage link | Until its Window ends; replaced by a new one | FR-25, Add A |
| Session after first Manage link load | Short-lived; lifetime `[A]`; when it ends the Guest opens the link in the email again | Add A |
| Anonymous session | 24 h, sliding | AD-8 |
| Administrator session | 8 h, sliding | AD-8 |
| Sign-in throttle | 5 consecutive failures for one email, then 15 minutes refused `[A: values]` | FR-15 |
| Resend limit | 5 per hour per email and per source address `[A]` | FR-34 |
| Door code Send time | Default 20 minutes before start; no earlier than the Seat Cutoff (12 hours), no later than Window start | FR-47 |
| Door code validity | From the Send time until the Window ends | FR-47 |
| Data retention | Names and emails deleted or anonymised 12 months after the Window, or after the last Voucher from the Booking expires if later `[A]` | FR-21 |

### Pricing and payment
| Rule | Value | Source |
|---|---|---|
| Price per Seat | NOK 250 incl. VAT, the same in every Window; illustrative | Q3, Add J, FR-26 |
| Price per Sauna (Private sauna) | **Not set**; waits until §4.9 is planned. Each Sauna has its own price. Oslo comparables NOK 1,125–2,900 for 6–8 seats | Q3, Add J, §4.9 |
| Total | Seats × price per Seat, NOK incl. VAT; the amount charged | FR-3 |
| Payment | Simulated, instant, synchronous in every phase; charge and Booking are one atomic step | FR-6, AD-13 |
| Price lock | A Booking keeps the price paid; a Guest on the review page pays the price shown | NFR-4, FR-38 |
| Voucher, Gift card | Part or whole of a Booking, rest by Simulated payment; Voucher `[A]`; never paid out in money; no fees after sale | FR-28, FR-44 |
| Money format | Integer øre internally; displayed as "NOK 500" | AD-13, Arch Conventions |

### Cancellation and refund
| Case | Rule | Source |
|---|---|---|
| Seat booking, Core | Terms state a Booking cannot be changed or refunded online (until §4.8 is built) | FR-5 |
| Seat booking, before Cutoff | Move Seats, or give up Seats for a Voucher. No money refunded | FR-26, FR-27, §9 |
| Whole-sauna booking, before 72-hour Cutoff | Cancel with Guest's choice of Simulated refund or Voucher, or move. No move to a Sauna at another price | FR-33 |
| After Cutoff | Every Change refused with an explanation; Manage link still shows the Booking | FR-26, FR-33, UJ-4 |
| Saunalöyly cancels | Cancelled in full regardless of Cutoffs; Guest chooses refund or Voucher | FR-40, FR-42, §9 |
| Partial Voucher funding | Each part goes back the way it was paid; Voucher part as a new Voucher with the earliest expiry `[A]` | FR-28, FR-42 |
| Right of withdrawal | None for a fixed-date Booking (angrerettloven § 22 m); must be said before the contract (§ 8 k). Gift cards: 14 days `[A]` | FR-5, Add D, FR-43 |

### Door codes [S2]
Each door has its own code per Window, shared by everyone allowed through. The booker gets one email and shares it with their group (§4.15). Whole-sauna booker: that Sauna's codes only (H2). Seat booker: every Sauna open for Seats in the Window (H1), never a Whole-sauna-booked, Blocked or unreleased Whole-booking-only Sauna (H2, H3). In seed data every Sauna has a self-service lock `[A]`. A Sauna without one gives no code (H5). Guest who gives up all Seats before Send time gets none (H7). Booking made, or Seats moved in, after Send time: email at once (H9). After Send time, a Whole-sauna booking is refused while Seat bookers hold its code (H12). A code is emailed only after the lock confirms it `[A]`.

---

## 6. States and failure cases the user can encounter

### Guest, Core
| State | Required behaviour | Source |
|---|---|---|
| Fewer Seats left than chosen | Window shown unavailable, not selectable, text label such as "1 seat left" | FR-3 |
| No room on chosen date | Offer up to three nearest Windows with room (same day first, then following days, within horizon) `[A]` | FR-3 |
| Sold out | Information about availability, with alternatives, not an error | FR-22 |
| Booking deadline passed | Window not offered | FR-3 |
| Date with no bookable Window | Date cannot be chosen | FR-2 |
| Seat number outside 1–10 | Cannot be submitted; server rejects | FR-2, FR-18 |
| Seats taken while typing | Told how many Seats are actually left; offered nearest Windows with room; nothing charged | UJ-1, FR-12 |
| Lost last-Seat race | Told no Seat is free; not charged; no email; nearest Windows offered | FR-11 |
| Request exceeds Seats left | Rejected whole; message states Seats actually left; alternatives | FR-12 |
| Temporary conflict, retries used up | "please try again", distinct from "No seat free"; nothing written | FR-14 |
| Payment failed | No Booking, Seats or email; message with a way to try again | FR-7 |
| Double submit or reload | First outcome returned; booked Guest sees the confirmation again | FR-6, AD-9 |
| Back from review | Everything entered is kept | FR-5 |
| Confirmation reload | Shows again in the paying session; elsewhere unavailable (404) | FR-8, AD-12 |
| Booking reference used alone | Opens nothing | FR-8, FR-20, FR-34 |
| Guessed reference or link | Same response whether or not the Booking exists | FR-20 |
| Form error | Text next to the field and in a summary | FR-23 |
| Guest write with no session | `401 no_session` | AD-8 |
| Key from another session | `409 invalid_key` | AD-9 |

### Administrator, Core
| State | Required behaviour | Source |
|---|---|---|
| Wrong email or password | Same message | FR-15 |
| Throttled | Same message as wrong password; does not reveal account existence | FR-15, AD-11 |
| Anonymous at Administrator function | Refused as not signed in; nothing changes (401) | FR-20, AD-10 |
| Signed-in Guest at Administrator function | Refused as not allowed (403) [IT-6] | FR-20 |
| Unknown or not yours | Answers like something that does not exist (404) | AD-10 |

### Guest, If time and Step 2
| State | Required behaviour | Source |
|---|---|---|
| After Cutoff | Manage page shows the Booking; every Change refused with the reason | FR-25, FR-26, UJ-4 |
| Move target lacks room | Nothing changes; original untouched | FR-26 |
| Invalid, expired or replaced Manage link | Same response as a link that never existed | FR-25 |
| Voucher expired, used-up or unknown | Same refusal message | FR-28 |
| Gift card expired or used-up | Refused | FR-44 |
| Sauna taken before Private sauna payment | Nothing charged | FR-29 |
| Sauna not allowed under Room ahead | Not offered | FR-30, UJ-5 |
| Move to another-priced Sauna | Refused with reason; Guest can cancel and book again | FR-33 |
| Extra Seats unavailable on Hold resize | Old Hold stays; Guest is told | FR-35 |
| Hold expired, Seats free, before deadline | Payment still books | FR-36 |
| Hold expired, Seats gone or deadline passed | No Booking, no charge, Guest told why | FR-36 |
| Hold ended by a Block | Guest holds nothing | FR-40 |
| Resend, match or not | Identical response | FR-34 |
| Booking cancelled by a Block or fallback | Cancelled in full; apology email with remedy link | FR-40, FR-42 |
| All Saunas Blocked | Window not offered; every Booking in it cancelled | FR-40 D6 |
| Sauna Blocked with Whole-sauna booking | Cancelled regardless of Cutoff; same remedy choice | FR-40 D4 |
| Blocked Sauna, Seats fit elsewhere | No Guest is affected or told | FR-40 D2, UJ-6 |
| Remedy link | Works 30 days; one choice; then default refund | FR-42, Add A |
| Whole-booking-only Sauna | Left out of Seats left until released, then Seats left rises | FR-41 |
| Door code not confirmed | Administrator alerted; email goes out once confirmed | FR-49 |
| Sauna stops being open for Seats after Send time | Correction email naming the codes to use; code replaced for a Block where the door allows | FR-48 |
| Sauna becomes open for Seats after Send time | Extra email with its code `[A]` | FR-48 |
| Booking cancelled after Send time | Email says the codes must not be used `[A]` | FR-48 |

### Administrator, If time
Capacity decrease refused while a not-started Window would overflow (FR-38). Window with Bookings or Holds cannot be deleted or moved (FR-38). Overlapping Window refused (FR-13, FR-38). Setting over its limit refused; conflicts name the Windows (FR-39). Block preview stale: nothing applied, new preview shown (FR-40). Marking refused as in FR-41.

### States the PRD leaves to the UX designer (§7, under FR-22)
Behaviour is the designer's call unless a rule above fixes it.
- **Core:** the Booking deadline passing between choosing a Window and paying; a Window that has started but can still be booked; the last day of the horizon; no Window with room anywhere in the horizon; sign-in slowed or refused; an anonymous visitor at an Administrator address; a date with no Bookings; payment in progress.
- **If time:** the Manage page after a Voucher, a Venue cancellation, the Cutoff and the end of the Window; a Voucher that covers the whole total, where "Pay NOK 0" needs other wording; a resend refused by the rate limit; the Remedy page after the choice or after 30 days; a Seat taken by another Guest while the details are entered.

---

## 7. Notifications and messages

**No SMS and no in-app push are specified.** All emails are simulated, plain text, in English, and appear in the Outbox (§7, NFR-5, Add M, AD-12). Links are absolute (AD-12). No marketing email (FR-21). No HTML email (Add M).

**Where a Guest sees an email (FR-17):** only on the page of the action that sent it: the confirmation page (FR-8) and the result pages of a Change (FR-26, FR-27, FR-33). The new Manage link (FR-34) and remedy emails (FR-40, FR-42) are visible **only** in the Outbox, because showing them would give access to a Booking to anyone who knew a reference and an email.

| Email | Trigger | To | Required content | Phase |
|---|---|---|---|---|
| Booking confirmation | Successful Booking | Booker | Booking reference, date and Window, Seats, total paid, Guest's email, what happens next, terms, link to "Before you come", payment note. No Sauna identifier for Seat bookings (FR-4). Manage link from IT-2 | Core |
| Confirmation of a Change | Every move, partial or full; Change | Booker | What changed, new Window and Seats, Manage link | IT-2–3 |
| Split-off Booking | Partial move | Booker | New Booking reference and its own Manage link | IT-2 |
| Voucher | Seats given up; Voucher chosen | Booker | Code, value, expiry date | IT-2 |
| Manage link resend | "My booking" request with a match | Address given | New link; the old one stops working. Outbox only | IT-4 |
| Whole-sauna booking, cancellation or move | That action | Booker | Sauna, Window, price, refund or Voucher | IT-3 |
| Apology with remedy link | Booking cancelled by Saunalöyly (FR-40, FR-42) | Booker whose Booking was cancelled | What happened, the link, 30 days to choose; S2: do not use any Door codes received. Outbox only | IT-3, 7 |
| Remedy confirmation | Guest's choice | Same | The refund (may take a few days to arrive) or the Voucher. Outbox only | IT-3, 7 |
| Account confirmation, password reset | Sign-up; reset | Address given | A single-use link | IT-6 |
| Gift card | Purchase | Buyer | Code, value, expiry date, not paid out in money | S2 |
| Door codes | Send time; at once if booked after it | Seat or Whole-sauna booker | Codes for exactly the doors allowed | S2 |
| Extra codes | Sauna becomes open for Seats after Send time | Every Seat booker of the Window | Its code | S2 |
| Correction | Sauna stops being open for Seats after Send time | Every Seat booker of the Window | Names the codes to use | S2 |
| Codes-invalid notice | Booking cancelled after Send time | Booker | Codes must not be used (in the cancellation email) `[A]` | S2 |
| New shared code | Code replaced on a replaceable door | Every remaining holder | The new code, before the old one stops working | S2 |

**Every email that mentions a payment** carries "Simulated payment: no money moves" (FR-6).

**Administrator alert** when a code is unconfirmed at Send time (FR-49); channel not stated.

### Required copy, verbatim
| Text | Where | Source |
|---|---|---|
| "Simulated payment: no money moves" | Pay step and every email that mentions a payment | FR-6 |
| "Pay NOK 500" (example: must state obligation and amount) | Pay button | FR-6, UJ-1 |
| "1 seat left" (example: true current number) | Unavailable Window | FR-3 |
| "No seat free" / "no Seat free" | Definite loss | FR-14, FR-6 |
| "please try again" | Retries used up | FR-14 |
| "Before you come" | Section name | FR-1 |
| **Book seats**, **Private sauna**, "My booking" | Actions, page | FR-1, §4.1, §4.10 |
| "Sold out" | Availability information | FR-22 |

### Required statements, meaning fixed, wording free
- Seat flow: books Seats in the shared Saunas; may move freely on site; a group that wants to stay together should book a Private sauna (FR-4).
- Review: no right of withdrawal for a fixed date (FR-5); what can and cannot be Changed (FR-5); in Core, cannot be changed or refunded online (FR-5).
- Private sauna review: the Sauna is not held while the Guest pays (FR-29).
- Seat flow: no mention of any Hold or time limit (FR-35).
- Gift card purchase: 14-day right of withdrawal `[A]` (FR-43).
- Wording that does not satisfy § 16: "Complete booking" is not enough. The statute's phrase is "bestilling med forpliktelse til å betale", "or something equally clear" (Add D).

### Copy ownership (AD-12, AD-16)
Page copy in the SPA; email copy in `services`; text used by both (booking terms, "what happens next") once in `content/`. The server returns codes and facts, never page copy. Venue facts come from the API.

---

## 8. Platform and form factor

- **Web only.** Responsive website; no native mobile apps (§9, Brief).
- **Core: laptop.** Every Core page works without horizontal scrolling at 1366×768 and 1920×1080 `[A: these define "laptop screen"]` (FR-22). UJ-1 is on a laptop.
- **Mobile: last in Step 2** [S2-3]: every page without horizontal scrolling from 320 px upward, same stylesheet, FR-23 at every width (FR-51). "If time, last in step 2" (Brief SC10). May not be built; if not, reported as not delivered, including the Reflow gap (FR-23).
- **"Mobile first" was rejected:** "replaced by laptop first; 'desktop' was removed as a layout level" (Add G, 2026-10-29).
- **Forward-compatibility:** "no fixed widths that would block FR-51" (Arch Conventions).
- **Browsers:** no list stated. Tests use Chromium via Playwright (Arch Commands).
- **Offline:** not stated. Runs locally only; no public deployment (NFR-1, Arch Deferred).
- **Reliance on JavaScript:** React SPA (Arch); see §14, C13.

---

## 9. Accessibility, language and legal

**Accessibility**
- WCAG 2.2 AA on every Core page, one stated exception: 1.4.10 Reflow, until FR-51 (FR-23). Legal minimum for private websites in Norway is WCAG 2.0 AA, met in full (FR-23, Add D).
- Automated check: no A or AA failures except Reflow. Manual pass: entire booking flow and Administrator list with keyboard alone (FR-23).
- Focus always visible, never hidden behind fixed elements. Text contrast AA. Targets at least 24×24 CSS px. No information by colour alone. Form errors as text next to the field and in a summary (FR-23).
- Every pair of text and background colours meets AA (§6).
- Date typed as well as picked, keyboard-operable (FR-2). Paste and password managers work (FR-19).
- Focus moves to the page heading on every route change (Arch Conventions). axe-core checks in `tests/e2e/` (Arch).
- Hold: the 10 minutes limit only the reservation, not the Guest's task, for WCAG 2.2.1 (FR-35, Add A).
- WCAG 2.2 additions noted: 2.4.11, 2.5.8, 3.3.7 Redundant Entry, 3.3.8 Accessible Authentication (Add E).

**Language:** English only, website and emails (NFR-5, Brief). A few Finnish words appear, each with an English gloss (§6). Other languages Vision (§4.17).

**Consumer law (Add D: research, not legal advice)**
- Pay button states obligation (§ 16; FR-6). No right of withdrawal stated before the contract (§ 22 m, § 8 k; FR-5). Total includes taxes (§ 8 e). Confirmation on a durable medium such as email (§ 18).
- Ehandelsloven: identity and contact details, organisation number, VAT status, total cost (§§ 8–9); before the order, technical steps, how to correct mistakes, language of the contract (§ 11); confirm receipt (§ 12). Organisation number and VAT details are out of scope for the fictional version (Q12).
- Norwegian pre-contract information needed for a real launch; a gap (Add D, Q12).
- Keeping money when the trader cancels may be unfair, hence refund or Voucher (Add D).
- Scarcity: truthful, live "X seats left" acceptable in principle; no false scarcity; countdown timers that restart warned against (Add D, NFR-9).

**Privacy (FR-21, Add D)**
- Guest: name and email only (password hash with account). Administrator: email and password hash.
- Privacy notice linked wherever data is collected, separate from terms; contents in §4.1 here. Legal basis GDPR art. 6(1)(b). Must state how data is protected, or the README does.
- Only strictly needed cookies, so **no consent banner**. No third-party requests: fonts, images, scripts self-hosted. No tracking (§9).

**Terms:** acceptance required before paying (FR-5), never pre-ticked (NFR-9). Terms shown on review, confirmation page and email (FR-5, FR-8). Full terms and Privacy notice are pages (§7). Their text is not supplied in the sources.

**Receipts:** no separate receipt is specified; the confirmation shows the total paid (FR-8). Accounting records 5 years (Add D).

**Assets:** every image, font, icon and text AI-generated, freely licensed or checked; listed in the asset register, `ASSETS.md` (DR-3, Arch). Visit Finland image bank not used (Add F). Name "Saunalöyly" kept although "Löyly" marks exist; fictional, not used in trade (PRD title note, Q10).

---

## 10. Brand and visual input

Direction is stated in PRD §6. **No hex values, logo, wordmark or icon set are stated.**

- **Name:** Saunalöyly (working title; Venue name kept, Q10). Sauna names: Rauha, Löyly, Kajo, Lumo (§3).
- **Vision line:** "The website feels like the sauna it sells: calm, honest and plain, in light wood, forest green, birch white and sky blue, with real Finnish sauna rooms and their traditional tools in view" (§1). "nothing on the page tries to rush them" (§1).
- **Feel:** "calm, honest and plain: the Finnish idea of *saunarauha*, the peace of the sauna. The site should be appealing and intuitive for a first-time Guest (Lisa, 2026-10-29), and unhurried: nothing on it pushes." (§6)
- **Palette:** "light wood (birch and pine), deep forest green, granite grey, birch white, a grey sea-blue and sky blue. Saturation is low" (§6). Dark smoked timber rejected (Add F, G).
- **Type:** Finlandica for headings, Source Sans 3 for text, OFL, self-hosted (§6). Listed alternatives: Finlandica Text; Atkinson Hyperlegible Next, Inter, Hanken Grotesk (Add F).
- **Imagery:** "Finnish saunas outside and inside, with their traditional equipment: the *kiuas* (stove) and its stones, the *kiulu* (bucket) and *kauha* (ladle), the wooden *lauteet* (benches) and the *vihta* (birch whisk). The light is dim and indirect, with wood, water and forest in view." AI-generated or freely licensed (§6).
- **Copy:** "short and concrete, with facts before persuasion" (§6).
- **Anti-references:** spa-luxury cues (scents, music, coloured LED light, "pamper yourself"); polished stock photography; boasts about enduring heat; sexualised framing; urgency selling (§6).
- **References, to study not copy (Add F):** Löyly Helsinki (short copy, a booking bar that is always visible, public, morning and private sauna kept separate); Kulttuurisauna ("We aim to keep the bath-peace", 90-minute slots, list of what to bring); KOK Oslo (plain rules); Oslo Badstuforening (warm tone, clearly separated products).
- **Finnish glosses (Add F):** *löyly* steam from water thrown on the stones, the spirit of the sauna; *kiuas* stove; *kiuaskivet* its stones; *kiulu* bucket; *kauha* ladle; *laude*, plural *lauteet*, wooden bench; *vihta* or *vasta* whisk of birch twigs; *avanto* hole in the ice; *savusauna* smoke sauna; *saunarauha* the peace of the sauna.
- **Brief:** "calm, Finnish-inspired style".

---

## 11. Technical constraints on UX

**Stack:** React 19.3 SPA in `frontend/` on Vite 8; `react-router` 8.5 Data mode; FastAPI (Python 3.12); PostgreSQL 18 in Docker; served on :8000 (Arch Stack, AD-17).

**UI system: decided. None.** "One stylesheet and no design system" (§4.6). `frontend/src/styles.css` with CSS custom properties for the §6 palette; "No UI library or CSS framework"; fonts and images self-hosted in `frontend/public/` (Arch Conventions).

**Auth:** Administrator email and password, Argon2id (AD-11). Server-side session rows, HttpOnly SameSite=Strict cookie; `Secure` once HTTPS is on; no CSRF tokens (AD-8). Guests anonymous in Core.

**Payment provider:** none; `services.payment.charge()`, synchronous (AD-13). Test switch `payment = "ok" | "fail" | "hold"`; `hold` gives `409 payment_pending` (AD-14).

**Performance:** no target (NFR-7, FR-14, Arch Deferred).

**Real-time:** none stated. No push or live updates. Administrator list: "A new Booking appears on the next page load" (FR-16). No background jobs or timers (AD-4, NFR-11).

**Decisions that shape the UI**
| AD | Effect on UI |
|---|---|
| AD-2, NFR-2 | The store and server have the last word; SPA checks are "UX checks (never authoritative)", so any screen can be overtaken by a refusal at submit. |
| AD-3 | One user action is one transaction, so a refused action leaves nothing partly done. |
| AD-4 | SPA never uses the browser clock for a rule; server time decides. Effects are evaluated when read. |
| AD-5 | Seats left and related numbers always come from the server, never computed in the SPA. |
| AD-6 | A Booking carries a Window and a Seat count, never a Sauna. |
| AD-7 | Bookings are never deleted; a cancellation sets status, so cancelled Bookings stay listable (FR-16). |
| AD-8 | SPA calls `POST /api/session` on load; anonymous sessions 24 h, Administrator 8 h, sliding. Confirmation depends on this session. |
| AD-9 | SPA creates a UUID on reaching the review page, reuses it for retries. Only success is stored, so retry after refusal or failure runs again. |
| AD-10 | Administrator endpoints under `/api/admin/`: 401, 403, 404. |
| AD-11 | Throttle refusal is identical to a wrong password (401). |
| AD-12 | Route `/confirmation/:reference`; `GET /api/bookings/{reference}/confirmation` returns Booking facts and stored email, checked against the paying session. Shared text in `content/`. |
| AD-13 | Every page and email shows `bookings.total_ore`, never recomputed. |
| AD-16 | Every refusal is a code plus facts; SPA owns copy and mirrors the code table. 422 only for shape errors, with `fields`; rules judged against store or clock are 409. Venue facts come from the API. |
| AD-17 | One client module `frontend/src/api.js`; relative `/api/…`; no other origin. |
| AD-20 | Booking reference: 8 characters of upper-case Crockford base32. Internal ids never shown (Conventions). |

**Error envelope (Arch Conventions):** `{"detail": {"error": "<code>", "message"?: "<dev text>", …facts}}`. 401 not signed in, sign-in refused or no session; 403 not allowed; 404 unknown or not yours; 409 rule refused; 422 `invalid_input` with `fields`; 503 `try_again`. Named codes: `no_session`, `invalid_key`, `payment_pending`, `invalid_input`, `try_again`. `message` is for developers, not page copy.

**Date and money formatting:** API sends ISO 8601 with an offset; a Venue date is `YYYY-MM-DD`; SPA formats with `Intl.DateTimeFormat` in `Europe/Oslo`, money as "NOK 500" (Conventions).

**Manage pages (Add A, later):** `Referrer-Policy: no-referrer`, `noindex`, no third-party resources; GET only shows, Change needs POST with a confirmation step; token swapped for a short-lived session cookie and stripped from the URL. Flow to be amended in the spine before the first IT-2 story (Arch Deferred).

**Build constraints:** one person, to 15 December 2026; feature cutoff 11 December; freeze 12–15 December. "Frontend, design and extensive testing are the likeliest overruns" (§8.2). Design and UX is 10 % of the assessment (§8.1).

---

## 12. Scope

**Core (§10.1):** find a Window, book and pay for Seats; capacity integrity under concurrency; Administrator sign-in, booking list, Outbox; validation, hashed passwords, role-based access; privacy notice; Finnish-inspired laptop website. **"Website complete" means every Core page in §7 exists with final copy and images in the §6 look, with no placeholders, and FR-22 and FR-23 pass.**

**Core pages (§7):** Landing (with "Before you come"), Book seats (date, Seats, Windows), Details and review, Confirmation, Terms, Privacy notice; Administrator Sign-in, Booking list, Outbox, Sign-out.

**If time, still v1, in order (§10.1):** 1 HTTPS (§4.7); 2 Change Seats or take a Voucher (§4.8); 3 Whole-sauna booking (§4.9); 4 "My booking" resend (§4.10); 5 Seat Hold (§4.11); 6 Guest accounts (§4.12); 7 Administrator tools and Venue rules (§4.13). Order of 3–6 `[A]`, decided when IT-2 is merged (Q6). **Likely v1 is the Core plus HTTPS** (§10.1, §10.3, Q6). Items 3–6 "probably out of reach".

**Step 2, out of scope for v1 (§10.2):** Gift cards; Door codes with optional Gradual opening; mobile layout, last. Starts only when every v1 item built so far passes its tests (§10.3).

**Vision (§4.17), not built:** several locations; children and adults told apart; memberships, period cards; remote door opening; one-Sauna access; heating; several websites; more languages; real payment and email; other bookable resources; Windows from a daily pattern.

**Explicit non-goals (§9):** real payment, email, locks; heating; several venues or websites; native apps; money back when a Guest changes plans for Seats; combined basket across Windows; waiting list `[A]`; dynamic or demand pricing `[A]`; marketing, newsletters, tracking; child/adult distinction; rules engine for etiquette, age or safety; Administrator editing screens in the Core; performance guarantee; market validation; AI features in the app.

**UX scope for this round (§7, Lisa 2026-10-30; Add M):** every Core page in full; the places on Core pages where If-time features plug in (Private sauna entry, Voucher field, sign-in choice); and the flows of §4.8 to §4.12. Screens of §4.13 come later. The UX workflow sketches the booking flow and Administrator booking list first, and the blocking calendar when §4.13 comes near (teacher's advice).

---

## 13. Open questions and notes for UX

**Open and owned by UX or Lisa**
1. **§12 Q2: "How is 'intuitive' verified, now that the informal three-person test is dropped?" Owner: Lisa. "Decide before the UX workflow."** Still open. The three-person test was rejected (Add G). SM-3 measures only FR-22 and FR-23.
2. **§7 states left to the UX designer:** full list at the end of §6 here.
3. **FR-5:** review may be on the details page or a separate step. UJ-1, Add E (check-answers page) and §7 "Details and review" differ in wording; layout is open.
4. **Protagonist names** are placeholders Lisa may replace (§2.3).
5. **Q7:** Administrator cancellation of a single Booking: "Is it needed?" Open; would affect the booking list.

**Content not supplied by the sources**
6. **What happens next** (FR-8) has no stated content. In Core there is no Manage link and no Door code.
7. **How a Guest enters the Venue in the Core** is not stated: Door codes are Step 2, and no reception or check-in rule appears.
8. **The swimwear rule:** FR-1 says "follow the swimwear rule", but no rule is defined; "Swimwear rules vary between venues" (Add F).
9. **Fictional address and contact details** (FR-1, FR-5) are not given. Only `admin@saunaloyly.example` exists (Add J).
10. **Booking terms and privacy notice text** are not written. Their required contents are in FR-5, FR-21.
11. **One line per Sauna and one image per Sauna** (FR-1) are not written or supplied.
12. **Private sauna prices** not set (Q3). Needed for the plug-in point and IT-3 flow.
13. **How a Core Guest changes plans:** terms say not online (FR-5); no alternative is stated. Contact details exist, but no process.

**Assumptions directly shaping screens:** names and email limits (FR-5); three nearest Windows, same day first (FR-3); confirmation tied to paying session (FR-8); no Manage link in Core (FR-8); booking list grouping (FR-16); laptop sizes (FR-22); Voucher value (FR-27); Voucher partial use (FR-28); resend limit (FR-34); Guests sign in by email (FR-37); default refund after 30 days (FR-42). Full index in PRD §13.

**PM notes**
- FR-29 `[NOTE FOR PM]`: the strict rule can refuse a Private sauna while the Venue still has room in total (B2). v1 models no limit beyond the Fill order.
- FR-35 `[NOTE FOR PM]`: Hold compatible with WCAG 2.2.1.
- FR-47 and Q1 `[NOTE FOR PM]`: H6 undecided, two codes valid on one door during the 20 minutes before a back-to-back Window. Options (Add C): accept and inform; validity from Window start; a changeover gap. Revisit before Door codes are planned. If W1 is a Private sauna, its group may get visitors 20 minutes early. Seed schedule has no gap.

**Observations from reading (not stated as issues in the sources)**
- UJ-1 says Ingrid has "an email she can keep", but email is simulated: a Guest sees it only on the confirmation page, tied to the paying session (FR-8, FR-17, AD-8: 24 h sliding). No download or copy of the reference is stated.
- "bathe with caution, and never alone" (FR-1) sits beside single-Seat bookings (FR-2).
- A Guest's Booking can include Seats in a Window that started up to 5 minutes ago (Booking deadline), and changing time is part of the Window.
- FR-35 silence on Holds and FR-29's "not held" statement are deliberately asymmetric (Add M).
- A Cancel control exists in the Hold flow (FR-35), and a **Book** action precedes it (§4.11, FR-37), but no Core page names a **Book** button.
- FR-17 names no Guest-visible page for Gift card, account confirmation or password reset emails.
- Session expiry mid-flow (24 h, 8 h) is not in the §7 list of states.

**From this run's `.memlog.md` (not one of the four sources):** Lisa stated most guests book in advance and "some book on the way to the sauna". The sources put mobile last in Step 2, possibly not built, and the likely v1 is Core plus HTTPS (§8 here, §10.3). Lisa's other stated goals in that log: make people want to visit; a place for unwinding from stress, relaxation and happiness; booking simple and clear.

**Comparable and UX evidence on record (Add E; not requirements)**
Oslo Badstuforening: sold per person, calendar shows open places, opens 21 days ahead, 1.5 h including 15 min changing. KOK Oslo: up to 8 single seats, 1.5 h. Baymard: checkout abandonment from extra costs (40 %), forced account creation (18 %), total not visible up front (12 %); guest checkout should be most prominent; time-slot users overlook suitable options. NN/g, GOV.UK: allow typing a date; a short list of radio buttons beats a date picker when few options; check-answers page; confirmation shows reference and what happens next; errors next to field and in a summary, keep input, not used for "sold out". The "sticky call-to-action +4.2 %" figure was not found and must not be cited.

---

## 14. Contradictions between documents

The PRD rules in each case unless noted.

| # | Topic | Disagreement | Effect on UX |
|---|---|---|---|
| C1 | Window times, PRD internal | UJ-1 15:00–16:30, UJ-2 and UJ-3 18:00–19:30, UJ-3 20:00–21:30, and Glossary/FR-13 examples do not fit the seed schedule (10:00, 11:30, 13:00, 14:30, 16:00, 17:30, 19:00, 20:30; Q3, Add J). Only UJ-5's 10:00–11:30 fits. | Use seed times in designs. Q3 and Add J are the decided values. |
| C2 | Price basis | Brief: "set per time window". PRD: same price in every Window in v1 (FR-26, Q3, Add J); FR-38 sets one price per Seat and a price per Sauna. | No per-Window price variation to show. Moves are free. |
| C3 | Booking flow order and labels | Brief: first choose **Individual seats** or **Private sauna**; date in a calendar; then window and seats; Book; log in or continue. PRD: **Book seats** as one main action, Private sauna only once §4.9 exists; date and Seats first, then Windows; date also typed (FR-1, FR-2, FR-3). | Follow PRD order and labels. |
| C4 | Several Windows | Brief: "Guests can book several windows." PRD: one Window per Booking, several paid separately, no combined basket (FR-9, §9). | No multi-Window basket. |
| C5 | Cancel | Brief: guests need to "cancel easily". PRD: Guests cannot cancel Seats for money; Core has no online change at all (§3, FR-5, §9). | Terms must say so plainly. |
| C6 | HTTPS | Brief: undecided, not placed. PRD: first If-time item (§4.7). | None for screens. |
| C7 | If-time order and Step 2 | Brief numbers Changes first and Step 2 as item 7 of "If time allows". PRD puts HTTPS first and Step 2 outside v1 (§10). | Follow PRD. |
| C8 | Settings changes | Brief: "A changed setting applies only to new bookings." PRD: only Cutoffs do; horizon, deadline and Release time apply from the change `[A]` (FR-39). | Later Administrator Settings copy. |
| C9 | Overlap wording | Brief: windows "never partly overlap". PRD: no overlap at all, including identical and nested (§3, FR-13). | Later Administrator screens. |
| C10 | Who sees an email | AD-12: "the only Guest-facing Outbox read" is the confirmation endpoint. FR-17: Guests also see emails on Change result pages (FR-26, FR-27, FR-33). Arch Deferred says the spine is amended before IT-2. | FR-17 holds; spine needs amending. |
| C11 | "Only way" into a Booking | Glossary and FR-20: Manage link or account is the only way. FR-8 and AD-12: the paying session also opens the confirmation. | Different pages, but the wording conflicts. |
| C12 | Apology email phase | §7 table: "If time 3, 7". FR-40 and FR-42 are IT-7 only (§4.13), and FR-33 issues no apology. | Treat as IT-7 unless Lisa says otherwise. |
| C13 | JavaScript reliance | Add E evidence: "do not rely on a JavaScript-only calendar". Arch: the whole site is a React SPA. | Evidence, not a requirement; typed date (FR-2) still applies. |
| C14 | Catch-up on read | NFR-11: effects caught up by "the next request that reads". AD-4: reads never write; effects evaluated as a condition on read, materialised at startup or on a write. | Same visible result; UI shows the evaluated state. |
| C15 | Cookies | FR-21: only strictly needed cookies. AD-8: a session cookie is created when the SPA loads, for every visitor, before any booking. | Not a stated conflict; check before asserting "no consent banner" in the privacy notice. |
| C16 | Palette list | PRD §1 names four colours; §6 lists six, adding granite grey and grey sea-blue. | §6 is the fuller list. |
| C17 | Booking list fields | UJ-3 lists reference, name, email, seats, total. FR-16 adds time of booking. | Follow FR-16. |

**Noted in Add H, not checkable from these four files:** brief addendum says overbooking remedy is refund only (PRD: Guest chooses); CT-5 expected a simulated refund (PRD: nothing charged); the brief's "notes" field does not exist in the PRD (Add K).
