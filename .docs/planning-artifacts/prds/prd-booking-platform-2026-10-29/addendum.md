# Addendum: Saunalöyly Booking Platform PRD

This file holds supporting material that does not belong in `prd.md`. The decision history and audit trail live in `.memlog.md`, not here. The brief addendum (`.docs/planning-artifacts/briefs/brief-booking-platform-2026-09-20/addendum.md`) remains the home of the full rule tables and the security test tables. The capacity research report holds the 85-example catalogue. Unless a section says otherwise, the web findings were checked on 2026-10-29.

## A. Technical direction carried to the architecture

**Check and reserve capacity.**
- PostgreSQL: a conditional update under Read Committed (`… SET booked = booked + n WHERE booked + n <= capacity`). When two such updates race, PostgreSQL re-checks the condition against the newer row, so one wins and the other updates 0 rows. This behaviour is documented and verified; applying it to capacity is an inference (medium confidence).
- Serializable isolation can act as a backstop. Retry SQLSTATE 40001 (serialization failure) and 40P01 (deadlock) a bounded number of times, and keep transactions short.
- Never hold a lock across a payment step (low–medium confidence). In the Core this does not arise, because the Simulated payment is recorded inside the same transaction.
- SQLite: use `BEGIN IMMEDIATE` around check-and-reserve. This comes from the capacity research (sqlite.org, high confidence for the mechanism). The busy-timeout values are unsourced.
- A request that touches several Windows, such as a Change between Windows or a Block across several Windows, locks them in one fixed order, for example by Window start time, to avoid deadlocks. (PostgreSQL docs: "high" in the report, unverified in the research memlog.)
- Voucher and Gift-card balances use the same atomic conditional-update pattern as Seat capacity, so two simultaneous uses never overspend (FR-28, FR-44).
- Every database claim is version-bound. Re-check them once an engine and version are chosen.

**The Core data-store guarantee (FR-10).**
- In the Core, Seat capacity per Window is fixed, so a seat counter with a CHECK constraint can refuse an over-capacity write at store level. (Inference; not in the research. The requirement itself comes from the brief.)
- Once Whole-sauna bookings and Blocks change Seat capacity, the research found no store-level constraint. The check then runs inside one serialised transaction per Window (inference).
- The concurrency research assumed a capacity row per Sauna. With derived Placement, the Window is the natural lock unit for Seat bookings. This is still open.

**Derived Placement** (recommended; low–medium confidence; no practitioner source).
- Store the Seats booked per Window, plus Whole-sauna bookings and Blocks, and compute Placement when it is read.
- Put a Sauna reference on Blocks and Whole-sauna bookings, not on each Seat. Use one capacity function from v1.
- Add a nullable "placed in Sauna" column only if one-Sauna access is built (Vision, section L).
- Prove the approach with the model-based test against a brute-force reference (FR-31). The formula is the project's own inference; the research found no sauna or spa comparable.

**Formulas** (inference, to be proven by test).
- Seat capacity = Σ Capacity of the Saunas open for Seats.
- Seats left = Seat capacity − Seats booked − Seats held.
- A Whole-sauna booking of S is allowed only if all of these hold:
  - S is bookable whole;
  - S is not Blocked and not booked;
  - Seats booked (plus Seats held, once Holds exist) ≤ Room ahead(S).
- An unreleased Whole-booking-only Sauna is left out of Seat capacity. It skips the Room-ahead test, because it holds no Seats by definition.
- The research formulas omitted held Seats and Whole-booking-only status; both are added here.

**Holds are data** (low confidence: one weak source plus reasoning).
- Store a row with `expires_at`, and filter on it whenever availability is read. A cleanup sweeper is optional; its 30-second interval is an example, not a measurement.
- Payment confirmations are idempotent: deduplicate them by event ID. (Stripe docs: "high" in the report, unverified in the research memlog.)
- The confirmation handler re-checks the Hold inside a transaction. No source states this; it is the project's own inference.
- **WCAG 2.2.1 (adjustable time limits).** The Hold never discards entered data, because a payment after expiry still books if the Seats are free (FR-36). The 10 minutes therefore limit only the reservation, not the Guest's task.

**Manage-link hardening** (W3C TAG on capability URLs; OWASP).
- The token is at least 128 bits from a secure random generator, and only its hash is stored.
- Send `Referrer-Policy: no-referrer` and `noindex`, and load no third-party resources.
- GET only shows the Booking; any Change needs POST with a confirmation step.
- After the first load, swap the token for a short-lived session cookie and strip it from the URL with `replaceState`. A resend revokes the old link.
- This departs from OWASP ASVS 5.0 V14.2.1 (no sensitive data in URLs). It is accepted because the data is of low sensitivity.

**Passwords.** Use Argon2id. The `argon2-cffi` defaults exceed the OWASP minimum (19 MiB of memory, 2 iterations, parallelism 1). Store the hashes in PHC format and rehash at login when parameters change.

**Simulated lock.**
- It rejects a duplicate PIN on a door.
- It records per door whether codes are online (replaceable) or offline.
- It models the code states pending, set and failed. Follow Seam's `display_status` and `pending_mutations`; its `status` field is deprecated. (Seam docs: medium, unverified.)
- It deletes expired codes, and receives times explicitly in Venue time.
- Locks that work only in whole hours make every overlap longer.

**Test approach.**
- Run catalogue group C as parallel tests, and use group H, without H19 to H23, as the acceptance cases for SC6.
- Use group G and H19 to H23 (one-Sauna access) and group I (heating) only in Vision.
- Catalogue examples that use one request above 10 Seats, such as B4 (38 Seats), must be rewritten as several Bookings under the 10-Seat cap.

## B. Decisions taken from research, with the alternative

| Topic | PRD position | Alternative not taken |
|---|---|---|
| Windows (E1, E3) | Venue-wide; no partial overlap; a deviation for one Sauna is a Block | Windows per Sauna, which breaks the pooled Seat count |
| Whole-sauna rule | Strict: Seats booked ≤ Room ahead | Lenient: the Seats only need to fit in the remaining Saunas. With 20 Seats booked, this would allow Sauna 2, push Seats into Sauna 4 and make it unbookable |
| D3, a Block leaves too little capacity | The latest Bookings lose and are cancelled in full; the Guest chooses a refund or a Voucher; the Administrator sees who is affected first | None named in the research |
| D7, a Block is lifted | Seats are counted back so INV-5 holds | Seats stay where they are, which breaks INV-5 and needs stored Placement |
| D8, Whole-booking-only marked over Seats | Refused | Treat the mark as a Block |
| F1, Capacity is lowered | Refused while a future Window would overflow. The research row says "needs a decision"; the brief addendum lists refusal first | Handle it like D3 and displace Guests |
| F2, the Fill order changes | Applies to Windows that have not started | Apply only to Windows without Bookings, or to all Windows |
| F3, a Window has started | No moves; the Overbooking fallback applies | Moves at any time, which would send people out of the sauna they are sitting in |
| H10, the Send time changes | Applies only to Windows whose email is unsent | Resend to everyone |
| H12, a Whole-sauna booking after the Send time | Refused while Seat bookers hold the code | Accept it, and replace the code for the whole-sauna booker on online locks only |
| H13, a Block after the Send time | Correction email, the code replaced where the lock allows it, and a "replaceable" mark per door | Correction email only |
| H21, Placement under one-Sauna access (Vision) | Frozen at the Send time | Allow moves, with a new code email for each move |
| H23, turning on one-Sauna access (Vision) | Refused while any future Booking is split | Repack Bookings automatically |
| Overbooking remedy | The Guest chooses a refund or a Voucher | Refund only (brief addendum) |

## C. H6 explained: why two codes are valid on one door

The decided rules create the overlap:
- Each door has its own code for each Window, shared by everyone allowed through it.
- Codes are emailed at the Send time (20 minutes before the start by default) and are valid from then until the Window ends.

Take two back-to-back Windows, W1 15:00–16:30 and W2 16:30–18:00:

```
15:00 ─────────── W1 ─────────── 16:30 ─────────── W2 ─────────── 18:00
            code W1 valid ─────────────┤
                         16:10 ├─────────── code W2 valid ───────────┤
                               └ overlap 16:10–16:30: both codes open the door
```

**Why the overlap matters:**
1. **The lock must hold two different codes at once.** The vendors checked store many codes per door, but none of them documents whether two codes with overlapping validity times both work. This is untested.
2. **W2's Guests can open the door while W1 is still in use.** If W1 is a Private sauna, its group may get visitors 20 minutes early.
3. **The two codes must differ.** If they were the same, W1's Guests could walk back in during W2.
4. **Locks that work only in whole hours make the overlap longer.** A 16:10 start can become 16:00, so the overlap is 30 minutes, and sometimes up to 60.

**What "accept and inform" would mean:** the rule stays as it is, and the email tells W2's Guests that the code works from 16:10 but the sauna is in use until 16:30, so they should wait. In a Private sauna, W1's Guests are told that the next group may arrive early.

**Options for later:**
- (a) Accept the overlap and inform Guests, as above.
- (b) Make codes valid from the Window start. The email still arrives 20 minutes early with a code that does not yet work. On whole-hour locks, Windows starting at :30 still overlap.
- (c) Leave a changeover gap between Windows that is at least as long as the Send-time lead. Then no overlap is possible, but this affects the Window schedule (§12 Q3).

## D. Legal notes (research for the PRD, not legal advice)

**Withdrawal and pre-contract information** (angrerettloven).
- § 22 m: there is no right of withdrawal for leisure services tied to "en bestemt dato eller et bestemt tidsrom" (a specific date or period). This covers Seat bookings and Whole-sauna bookings.
- § 8 k: the trader must say so before the contract is made.
- § 8 e: the total price must include taxes.
- § 16: the pay button must say "bestilling med forpliktelse til å betale" (an order with an obligation to pay) or something equally clear. "Complete booking" is not enough (CJEU C-249/21).
- § 18: the confirmation must be given on a durable medium, such as email.
- § 8 third paragraph: when marketing to Norwegian consumers, this information must be given in Norwegian. This is a gap for any real launch.

**E-commerce** (ehandelsloven).
- §§ 8–9: show identity and contact details, organisation number, VAT status and the total cost.
- § 11: before the order, explain the technical steps, how to correct mistakes, and the language of the contract.
- § 12: confirm receipt without undue delay.

**Unfair terms.** Keeping the money when the trader cancels may be unfair (Directive 93/13/EEC annex 1(d), (f); avtaleloven § 36). The PRD therefore lets the Guest choose a refund or a Voucher when Saunalöyly cancels.

**Gift cards and Vouchers.**
- No Norwegian statute sets a validity period. Per ung.no (citing Forbrukerrådet), a gift card is valid for three years unless a period is stated.
- In 2023 the Minister of Justice placed gift cards under the three-year limitation period in foreldelsesloven, which cannot be shortened by contract. In the same year the Storting asked the government to consider stronger gift-card rules; no resulting law was found.
- One year is common: KOK Oslo uses it, and the Danish Consumer Ombudsman accepts it.
- Undated gift cards are not covered by § 22 m, so the 14-day right of withdrawal applies.

**Accessibility.**
- Private websites must meet at least WCAG 2.0 A and AA, apart from criteria 1.2.3–1.2.5, which leaves 35 criteria (forskrift FOR-2013-06-21-732 § 4; Uutilsynet 2025).
- WCAG 2.2 is not yet part of Norwegian law. EN 301 549 V4.1.1, which builds on WCAG 2.2 AA, was published on 2026-09-02.
- The European Accessibility Act is not in force in Norway and is still under EEA scrutiny. Microenterprises are exempt from it.

**Privacy.**
- The legal basis is GDPR art. 6(1)(b), covering only data that is necessary for the contract. Data is minimised and kept for a limited time.
- An art. 13 notice is required, kept separate from the terms. Requests are answered within one month.
- Accounting records are kept 5 years (bokføringsloven § 13).
- Marketing email needs consent (markedsføringsloven § 15).
- Cookies other than strictly necessary ones need consent (ekomloven § 3-15).
- A German court found that loading Google Fonts from Google's servers without consent was unlawful (LG München I, 2022). Fonts are therefore self-hosted.

**Passwords.** NIST SP 800-63B-4 (final, 2025-07-31) sets the rules:
- at least 15 characters when the password is the only factor, and at least 64 allowed;
- a blocklist instead of composition rules;
- no forced rotation, and paste allowed;
- at most 100 consecutive failed attempts.

**Scarcity messaging.**
- Forskrift om urimelig handelspraksis § 1 nr. 7 bans falsely claiming limited availability in order to force a quick decision. Markedsføringsloven § 7 bans misleading claims about availability.
- Forbrukertilsynet has warned against countdown timers that restart.
- A truthful, live "X seats left" is acceptable in principle. No Norwegian ruling was found.

## E. Comparable services and UX evidence

**Norway**
- **Oslo Badstuforening** (booking software: Periode):
  - Shared sauna:
    - Sold per person; the calendar shows the open places.
    - Booking opens 21 days ahead.
    - A visit is 1.5 h including 15 min of changing time.
    - Prices: NOK 150 for members, 260 for non-members, 95 for children.
  - Terms:
    - Shared tickets are not refundable, but can be changed up to 24 h before. Cancelling ≥ 48 h before gives a Voucher valid for one year.
    - Private bookings cancelled ≥ 72 h before give a 50 % refund or a 100 % gift card.
  - Private use is 13.8 % of seat capacity but about 33 % of revenue (2026 budget). A members' proposal to cap private use went to the AGM on 26 May 2026; the outcome was not found.
- **KOK Oslo:** up to 8 single seats per session; 1.5 h including changing; from NOK 270 shared and NOK 1,360 private. Shared bookings cannot be cancelled or moved without paid insurance.
- **Badstuvogna:** NOK 250 drop-in and NOK 1,250 private, from classified-ad snippets only (low confidence).
- **Eggedal Badstue** (booking software: Gibbs, not Periode): NOK 179 drop-in and NOK 1,125 private for up to 8. A unique code arrives by SMS or email and works only for the booked period. Guests must be 18 to book.
- **Wild Sauna Norway** (Gibbs): no refunds without a paid "Flex" option. A fine of NOK 2,000 for unauthorised guests at Voss, Gudvangen and Lærdal. The terms cite § 22 m.

**Finland and the UK**
- **Löyly Helsinki** (booking software: Asio):
  - Public sauna: 2 h for €29.
  - Private sauna for up to 10: €500–600 per 2 h. Cancellation is free ≥ 3 days before, 50 % at 1–2 days and 100 % on the day.
- **Allas Sea Pool:** sells only part of its capacity online. Prebooked tickets cannot be exchanged.
- **Community Sauna Baths** (London): a full refund when cancelled ≥ 24 h before.

**Patterns.**
- Sessions are 90 minutes including changing in Oslo, and 2 h in Finland.
- Shared seats are non-refundable, or have a 24–48 h cutoff. Private hire has a 48–72 h cutoff.
- Venues actively ration private capacity.
- No vendor page confirms that drop-in and private bookings share capacity.

**Corrections to the earlier pass.**
- Eggedal runs on Gibbs, not Periode.
- The tiered cancellation attributed to Allas is no longer on its pages.
- Wild Sauna's NOK 2,000 is a fine for unauthorised guests.
- The "sticky call-to-action +4.2 %" figure was not found and must not be cited.

**UX evidence.**
- Baymard: shoppers abandon checkout because of extra costs (40 %), forced account creation (18 %) and a total they cannot see up front (12 %). Guest checkout should be the most prominent option.
- Baymard: users of time-slot interfaces overlook options that would suit them. Present slots in a clear hierarchy.
- NN/g and GOV.UK: allow typing a date, and do not rely on a JavaScript-only calendar. A short list of radio buttons beats a date picker when there are few options.
- GOV.UK: use a check-answers page. The confirmation page shows the reference and what happens next. Error messages sit next to the field and in a summary, keep what the user typed, and are not used for "sold out".
- WCAG 2.2 adds 2.4.11 Focus Not Obscured, 2.5.8 Target Size (24×24 px), 3.3.7 Redundant Entry and 3.3.8 Accessible Authentication.

## F. Aesthetic references

**Sites to study, not copy:**
- **Löyly Helsinki:** short copy, a booking bar that is always visible, and public, morning and private sauna kept separate.
- **Kulttuurisauna:** "We aim to keep the bath-peace", 90-minute slots, and a list of what to bring.
- **KOK Oslo:** plain rules.
- **Oslo Badstuforening:** a warm tone and clearly separated products.

**Images.**
- AI-generated or freely licensed only, and listed in the asset register.
- The Visit Finland image bank is licensed only for promoting Finland as a destination, so it is not used.
- The palette follows Lisa's direction of 2026-10-29: light wood instead of dark smoked timber, plus deep forest green. Sky blue was added on 2026-10-30.

**Typefaces** (licences checked in the google/fonts METADATA files):
- Finlandica (OFL): Finland's country-brand typeface, by Helsinki Type Studio.
- Finlandica Text (OFL-1.1).
- Source Sans 3 (OFL).
- Alternatives: Atkinson Hyperlegible Next, Inter and Hanken Grotesk (OFL).

**Finnish words, with glosses:**
- *löyly*: steam from water thrown on the stones; the spirit of the sauna.
- *kiuas*: stove; *kiuaskivet*: its stones.
- *kiulu*: bucket; *kauha*: ladle.
- *laude*, plural *lauteet*: the wooden bench.
- *vihta* or *vasta*: a whisk of birch twigs; the name depends on the region.
- *avanto*: a hole in the ice.
- *savusauna*: a smoke sauna.
- *saunarauha*: the peace of the sauna.

**For "Before you come":**
- Peace is the most important principle, and guests shower first. The PRD asks instead for two towels, one of them to sit on (Lisa, 2026-10-30).
- Use löyly with consideration for others.
- Rounds of 5–10 minutes, with plenty of water.
- No alcohol: about 80 % of Finland's 30–40 yearly sauna heat deaths involved intoxication (Statistics Finland, 2011).
- Swimwear rules vary between venues.
- Children must be supervised.
- Bathe with caution, and never take an ice bath alone (Lisa, 2026-10-30).

## G. Rejected or replaced alternatives
- Looking up a Booking by reference and email: replaced by resending the link only (2026-10-29).
- A simulated refund for Seats: replaced by a Change or a Voucher only (2026-10-29).
- Mobile first: replaced by laptop first; "desktop" was removed as a layout level (2026-10-29).
- A Hold in the Core: moved to If time (2026-10-27).
- Placement that "moves any time": replaced by invariants, and by Placement frozen at the Send time under one-Sauna access (2026-10-29).
- An informal usability test with three people: rejected by Lisa (2026-10-29).
- Dark smoked timber in the palette: replaced by light wood (Lisa, 2026-10-29).
- An open Outbox: replaced by an Administrator-only Outbox (2026-10-29).
- HTTPS in the Core: moved to first in the If-time list (2026-10-29).
- Administrator screens in the Core: replaced by seed data (2026-10-27).
- Window lengths per Sauna: replaced by Venue-wide Windows (2026-10-29).
- Child pricing, memberships, period cards, remote door control and heating: moved to Vision on the teacher's advice (2026-10-14).
- Placement stored per Seat: not recommended.
- One-Sauna access as an optional Step 2 mode: moved to Vision (Lisa, 2026-10-30). Its rules are kept in section L.
- "Shower first" in "Before you come": replaced by two towels, one of them to sit on (Lisa, 2026-10-30).

## H. Source inconsistencies noticed (for upkeep, not PRD decisions)
- **The 06:00 rule.** The brief addendum's rule text (L53) and settings row (L101) do not tie the rule to Whole-booking-only Saunas, but the brief memlog (L24, L30) does. Lisa confirmed the PRD reading on 2026-10-29; the brief addendum wording should be aligned.
- **Step 2 contents.** The Step 2 list in brief.md has no gradual opening or one-Sauna access, while the brief addendum puts them first in Step 2. The PRD treats Gradual opening as an optional mode within Door codes, and Lisa moved one-Sauna access to Vision on 2026-10-30. The brief and its addendum were aligned the same day.
- **"Cancel" and "change" for Seats.** The brief, its addendum and its memlog use these words differently. The PRD defines Change in its Glossary.
- **The overbooking remedy.** The brief addendum says refund only, while D3 says refund or Voucher. The PRD lets the Guest choose.
- **The research catalogue:**
  - D5 uses overlapping Windows, which contradicts E1.
  - H20 contradicts itself under H21.
  - The formulas omit held Seats and Whole-booking-only status.
  - B4 uses a single request above the 10-Seat cap.
- **issues.md:**
  - L12 (E1/E3) is still open although it was decided on 2026-10-29.
  - L15, L17 and L31 treat H12 and the frozen Placement as open.
  - L28–29 still mention desktop.
- **Brief memlog.** Its front matter and its success-criterion numbers are out of date.
- **Concurrency research.** Its appendix labels some references "high" that its memlog lists as unverified.

## I. Build order and risk handling
The brainstorm of 2026-10-27 proposed this; Lisa has not confirmed it.
- **Planning** covers the Core first.
- **Build:**
  - Start with the database engine, the schema and the capacity invariant.
  - Then build a thin end-to-end booking, so that an interruption always leaves a running app.
  - Each story includes its tests. The Administrator login and list come next.
- **Freeze:** 9–15 December.
- **Work windows:** 27 October to about 8 November, 17 November to about 1 December, then the freeze.
- **Risk handling:**
  - Keep stories small, with a token budget per story logged in the session log.
  - Run mechanical tasks at lower effort.
  - Test concurrency, capacity, validation and SC1 in depth; give the rest breadth only.

## J. Illustrative seed data (not decided; see PRD §12 Q3)
- **Saunas:** 7, 10, 12 and 15 Seats, filled in the order 1 → 4.
- **Prices:** NOK 250 per Seat, in line with Oslo drop-in prices of NOK 250–270.
- **Private sauna prices:** to be set per Sauna. Oslo comparables range from NOK 1,125 to 2,900 for 6–8 seats.

## K. Test map: brief test IDs to PRD requirements
The brief addendum's test tables are unnumbered, so these IDs follow row order. "Core (Administrator)" means the case runs on Administrator accounts until guest accounts exist.

| ID | Case (short) | FR | Phase |
|---|---|---|---|
| CT-1 | Two Guests hold the last Seat at once: exactly one Hold | FR-35 | If time 5 |
| CT-2 | Two Guests confirm the last Seat: exactly one Booking; the other is not charged and gets no email | FR-11 | Core |
| CT-3 | Seats left afterwards is 0, never negative; the Administrator sees one Booking | FR-11 | Core |
| CT-4 | The first Hold expires; the second Guest books | FR-35 | If time 5 |
| CT-5 | Payment after expiry with the Seat taken: no Booking, simulated refund | FR-36 | If time 5 |
| IV-1 | Seat number zero, negative, fractional, not a number or above Seats left | FR-18 | Core |
| IV-2 | Date or Window malformed, unknown, outside the horizon or past the deadline | FR-18 | Core |
| IV-3 | Required field missing or unknown field sent | FR-18 | Core |
| IV-4 | Name or email empty, too long or malformed (the brief's "notes" field does not exist in the PRD) | FR-18 | Core |
| IV-5 | SQL, script or HTML never run or shown as markup | FR-18, FR-16 | Core |
| IV-6 | Invalid Administrator input: negative price or Capacity, Window ending before it starts | FR-18, FR-38 | Core (seed), If time 7 |
| IV-7 | A Guest sends an Administrator request: refused | FR-20 | Core |
| PW-1 | Account created or password changed: only a salted slow hash is stored | FR-19, FR-15 | Core |
| PW-2 | Weak password refused | FR-19, FR-37 | Core (Administrator), If time 6 |
| PW-3 | Strong password accepted and hashed | FR-19, FR-37 | Core (Administrator), If time 6 |
| PW-4 | No password readable; the same password gives different hashes | FR-19 | Core |
| PW-5 | A wrong password gives an error that does not reveal whether the email exists | FR-15, FR-37 | Core |
| RB-1 | Administrator function without sign-in: refused, nothing changes | FR-20 | Core |
| RB-2 | Administrator function by a signed-in Guest: refused | FR-20, FR-37 | If time 6 |
| RB-3 | Administrator function by a signed-in Administrator: allowed | FR-20 | Core |
| RB-4 | Another Guest's Booking by account or by guessed reference or link: refused, existence not revealed | FR-20, FR-25 | Core (reference), If time 2 (link), If time 6 (account) |
| RB-5 | An account-less Guest uses their own link: allowed for that Booking only | FR-25 | If time 2 |
| RB-6 | A guest account tries to change its own role: refused | FR-20, FR-37 | If time 6 |
| HT-1 | Plain HTTP is redirected; nothing is returned or changed over HTTP | FR-24 | If time 1 |
| HT-2 | Every HTTPS response carries Strict-Transport-Security | FR-24 | If time 1 |
| HT-3 | Session cookies are Secure and HttpOnly | FR-24 | If time 1 |
| HT-4 | Links in emails start with https:// | FR-24 | If time 1 |

## L. One-Sauna access (Vision)
Lisa moved one-Sauna access from Step 2 to Vision on 2026-10-30. These are the rules the PRD had worked out for it while it was an optional Step 2 mode (FR-50), kept for when it is picked up. Catalogue group G and H19 to H23 hold the cases, section B rows H21 and H23 the decisions, and PRD §12 Q15 the open questions.
- The Administrator turns the mode on; it is off by default.
- A Seat booking is placed whole in the first Sauna open for Seats, in the Fill order, that has room for all its Seats. If no Sauna has room, the request is refused for lack of room.
- Before the Send time, compaction moves whole Bookings only. INV-5 does not apply (FR-31), and a Whole-sauna booking (FR-29) requires that the Sauna holds no Booking. This needs stored Placement (section A).
- Guests may not move between Saunas, so they are told their Sauna, as an exception to FR-4. The Door-code email names the Booking's Sauna and gives only its codes (H19). For a Sauna without a self-service lock, it names the Sauna without codes (H22).
- Placement is frozen at the Send time, and F3's "no moves after the start" applies (FR-40). A Booking that would have to move after the Send time is cancelled with the remedy of FR-42, even when Seat capacity is not exceeded, and other Bookings are untouched. This follows the research recommendation; Lisa has not confirmed it.
- The mode cannot be turned on while any future Window has a Booking split across Saunas. Turning it off applies only to Windows whose Door-code email has not been sent (H23).
