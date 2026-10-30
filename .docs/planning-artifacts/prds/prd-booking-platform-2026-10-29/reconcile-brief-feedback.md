# Input reconciliation: brief and teacher feedback against the PRD

| | |
|---|---|
| **PRD checked** | `prd.md` and `addendum.md` in this folder (draft v1, 2026-10-29) |
| **Input 1** | `.docs/planning-artifacts/briefs/brief-booking-platform-2026-09-20/brief.md` (status final, updated 2026-10-29) |
| **Input 2** | `tilbakemelding-product-brief.md` in the same folder (teacher, 2026-10-06, written about brief commit 5666cfd) |
| **Decision sources** | PRD `.memlog.md` (cited as "PRD memlog Lnn"), brief `.memlog.md` ("brief memlog Lnn"), brief commits (by hash) |
| **Done** | 2026-10-29, as a read-only pass. No other file was changed. |

**How to read this.** "Line" is the line number in the input file. Section numbers (§) and FR, NFR, DR, SM and Q IDs point into `prd.md`; "add. X" points into the PRD `addendum.md`. Each point gets one status:

- **captured**: the PRD has it. A refinement that keeps the input's intent also counts as captured.
- **partially captured**: some of it is there.
- **missing**: the PRD does not have it.
- **contradicted**: the PRD says something different, and no decision explains why.
- **superseded by decision**: a deliberate, logged change, so not a gap.

**About the feedback.** The teacher reviewed an older brief: 12 success criteria, with child prices, memberships, door control and heating all in v1. Most of the feedback reached the PRD through the brief revisions of 2026-10-14 to 2026-10-29 (commits c55c757, 6eeb493, 42c411b, a63c7c5, e48b9e2, 182f12e, 8bcfbbc, fa91b30, a1e57a6, 8ea73ec, fed9275 and a1c1780). Feedback line 107 repeats lines 70–71 and is covered under F26 to F30.

## Summary

| Input | Points | Captured | Partially captured | Missing | Contradicted | Superseded by decision |
|---|---|---|---|---|---|---|
| brief.md | 101 | 81 | 13 | 2 | 1 | 4 |
| Teacher feedback | 54 | 39 | 9 | 0 | 0 | 6 |
| **Total** | **155** | **120** | **22** | **2** | **1** | **10** |

The PRD carries almost all of the brief's rules, numbers, scope tiers, success criteria and delivery requirements. Every deliberate departure from the teacher's advice is logged, and where it matters it is flagged in §10.1. What gets lost sits mostly outside the FR structure:

- the price model;
- how deep the next planning steps should go;
- what the website itself shows;
- who the guests are;
- the brief's honest statement that its differentiators are unproven.

## 1. Gaps that matter, ranked

The ranking is by impact on how useful the PRD is as input to UX, architecture and epics.

### G1. The price model is never stated, and the PRD's assumption contradicts the brief
*Status: contradicted (by an assumption that was never logged). Affects: architecture, UX, epics.*

- **Input:**
  - Brief L26: "Pricing: set per time window: one price per seat and one price per whole sauna."
  - The brief memlog supports a price per Window: prices "apply to a given time window" (L38), and the Seat price is "venue-wide per window" (L47).
- **PRD now:**
  - FR-26 assumes "one price per Seat in every Window in v1", so that moving Seats costs nothing.
  - FR-3, FR-38, NFR-4, §12 Q3 and add. J all say "the price per Seat" and never say whether it can differ between Windows.
  - No memlog entry records the choice. PRD memlog L32 settles only "NOK inkl. mva i seed".
  - The per-Sauna price for Whole-sauna bookings (FR-30, FR-38) matches brief addendum L55 and is fine.
- **Why it matters:**
  - The architecture has to decide where a price is stored: once for the Venue, on each Window, or per Sauna and Window.
  - UX has to know whether the Window list can show different prices.
  - Epics have to know whether FR-38 edits prices per Window, and what FR-26 and FR-27 do when a Guest moves between Windows that cost different amounts.
- **Fix:** Lisa decides between the two options below. The PRD then states the model once, as a Glossary entry "Price" plus one sentence in NFR-4. Until she decides, keep the question open in §12 Q3.
  - *Option A, which keeps FR-26:* "In v1 the price per Seat is the same in every Window. The price of a Whole-sauna booking is set per Sauna. A price buys one Window. Prices per Window come later." Also note the wording mismatch in add. H, so that brief L26 can be aligned.
  - *Option B, which follows brief L26:* "Each Window has its own price per Seat and, for each Sauna, its own Whole-sauna price." Then:
    - FR-3 shows each Window's own total;
    - FR-38 edits prices per Window;
    - FR-26 says what happens when Seats move to a dearer or cheaper Window: the move is refused, or the difference is paid or issued as a Voucher.

### G2. No rule for how deep planning goes, and no gate before Step 2
*Status: partially captured. Affects: epics, architecture.*

- **Input:**
  - Feedback L57: "Antallet stories blir høyt med dagens scope; færre funksjoner gir en mer overkommelig plan."
  - Feedback L56 rates time and scope as "Stor risiko".
  - Feedback L71 says Step 2 comes "når v1 er stabil og testet".
  - Brief L119 says the backward check of the build order from 15 December "was not run".
- **PRD now:**
  - All 51 FRs are specified at the same depth: Core FR-1 to FR-23, If time FR-24 to FR-42, and Step 2 FR-43 to FR-51.
  - Only add. I says "Planning covers the Core first", and Lisa has not confirmed it.
  - §10 orders the tiers but sets no condition for starting Step 2.
  - §12 Q6 (the order of If-time items, and the missing backward check) has no owner and no deadline, unlike Q2 and Q3.
- **Why it matters:**
  - Without a rule, the epics workflow will turn all 51 FRs into stories. That is the story count the teacher warned about, and §8.2 already names tokens and time as hard limits.
  - The architecture also needs to know whether Step 2 (the simulated lock and Door codes) is in scope for this round.
- **Fix:** once Lisa confirms, add §10.3 "Planning depth":
  > The architecture decides everything the Core needs, plus the If-time choices that shape the Core data model (Placement, the lock unit per Window, Holds stored as data, Manage-link tokens). Epics and stories are written in full for the Core. Each If-time item gets one epic, and its stories are written when it comes next in the §10.1 order. Step 2 and Vision get no stories in this round. Step 2 starts only when every v1 item built so far passes its tests.

  Also give §12 Q6 an owner (Lisa) and a deadline (before sprint planning).

### G3. What the website itself shows, and what "website complete" means
*Status: partially captured. Affects: UX, and the epics' definition of done for the Core.*

- **Input:**
  - Brief L12: the platform is "delivered together with a website".
  - Brief L22: "A website that presents the sauna venue in a calm, Finnish-inspired style".
  - Brief L84: "The core is done when the website is complete".
  - Feedback L76: the app is judged on whether it is well designed ("om den er godt designet").
- **PRD now:**
  - FR-1 limits the website's own content to the Venue name, "a few lines", **Book seats**, two links, and a "Before you come" section that is only an assumption.
  - §7 has no page about the Venue.
  - §10.1 repeats "the website is complete" without saying what it means.
  - Nothing says how the website shows the Saunas, the opening hours or Window schedule, the price per Seat, or the Venue's fictional address. Contact details appear only on the review page (FR-5).
- **Why it matters:**
  - UX has no content list for the part of the product that carries the brief's identity, which the brief calls its clearest differentiator (L39).
  - Epics have no testable definition of "Core done".
- **Fix:** add FR-1a "Venue presentation" with a minimal content list:
  - the Saunas as places to visit, each with one image and one line, worded so that a Seat booking never seems to choose one (FR-4);
  - opening hours and the Window schedule;
  - the price per Seat, and the price per Sauna once §4.9 exists. Add. E reports that guests abandon a booking when they cannot see the price up front.
  - the fictional address and contact details, the same ones FR-5 shows;
  - the "Before you come" section.

  Then define the term in §10.1: "Website complete" means every Core page in §7 exists with final copy and images (no placeholders) in the §6 look, and FR-22 and FR-23 pass.

### G4. Who the guests are, and the honest note that the differentiators are unproven
*Status: partially captured and missing. Affects: UX, and how the examiner reads the PRD.*

- **Input:**
  - Brief L43: guests are "people who already enjoy Finnish saunas or are curious to try".
  - Brief L39:
    - it "competes ... on price, on how well it attracts guests, and on features";
    - its differences are "the Finnish-inspired identity for an audience that already likes saunas" and one system for both booking types;
    - "None of this is proven yet: the exam version does not test prices or customer demand."
  - Feedback L85 praises exactly this honesty.
- **PRD now:**
  - §2 has jobs to be done and placeholder journeys, but does not describe the guests.
  - §6 designs for "a first-time Guest". The regulars who already love saunas, the audience the Finnish identity is aimed at, are missing.
  - §1 describes the identity and the shared rooms, but not as differentiators. The sentence saying they are unproven and untested is gone.
- **Why it matters:**
  - UX needs both groups. Regulars want availability and price within a few clicks. First-timers need to know what to expect and how to behave, which is what "Before you come" is for.
  - The brief's candour is one of the strengths the teacher assessed.
- **Fix:**
  - Add §2.0 "Who it serves", describing two Guest groups (regulars and curious first-timers) and what each needs. In UJ-1, say which group Ingrid belongs to, or add one short journey for a regular.
  - Add to §1: "If it became a real service, it would compete on price, appeal and features. Its differences are a Finnish-inspired identity for people who already like saunas, and seats and private saunas in one system. Neither is proven: the exam version tests no prices and no demand."
  - Add to §9: "No market validation. Prices and demand are not tested, and the seed prices are illustrative."

### G5. Nothing checks the design intent (tracked as §12 Q2)
*Status: partially captured. Affects: UX, and the definition of done for UI stories.*

- **Input:**
  - Brief L22 asks for a "calm, Finnish-inspired style".
  - Feedback L76 judges whether the app is well designed ("godt designet"), and L100 weights Design and UX at 10 %.
  - Lisa's goal is a site that is "tiltalende og intuitiv", appealing and intuitive (PRD memlog L7).
  - Rejecting the informal three-person test was a decision (PRD memlog L33), not a gap. But it left open how the goal will be checked.
- **PRD now:**
  - SM-3 checks only FR-22 (layout) and FR-23 (WCAG).
  - Nothing in §6 can be checked.
  - §12 Q2 is still open and is to be decided "before the UX workflow".
- **Why it matters:** the UX workflow and every UI story need a standard to meet. Without one, §6 is advice, not a requirement.
- **Fix:** close Q2 with a method that needs no outside testers, and add it to SM-3. For example:
  - a §6 checklist run on every UI story: only the palette tokens and the two typefaces, no anti-reference cues, the copy rules followed, and no urgency cues;
  - a review of the Core flow against Nielsen's ten usability heuristics, with findings and fixes logged;
  - a scripted first-time walkthrough that books 2 Seats from the landing page with no help, counting the screens against the §7 flow.

### G6. No plan for where secrets, test data and documentation live
*Status: partially captured. Affects: architecture, and the epics' setup story.*

- **Input:** feedback L103, part-1 criterion 7 (tidy repository, 5 %): "En plan for hvor hemmeligheter, testdata og dokumentasjon skal ligge."
- **PRD now:**
  - DR-3 covers only clean assets.
  - NFR-1 says no keys are needed, but the platform still needs a secret to sign sessions and a seeded Administrator password.
- **Fix:** add DR-5 "Tidy repository":
  > No secret is committed. Any secret, such as the session key, is generated on first start or read from a git-ignored local file, with a committed example file. The seeded Administrator password is a documented local test value. Seed and sample data live in one named folder, tests in one folder, and planning documents in `.docs/`. The README names each location.

### G7. The limit on preparing for the future covers only extra websites
*Status: partially captured. Affects: architecture.*

- **Input:**
  - Feedback L23: "ikke la forberedelser for fremtiden ta tid fra kjerneflyten i v1". L58 and L101 make the same point.
  - Brief L110: the first version is built so that later steps are "extensions, not rewrites".
- **PRD now:**
  - NFR-2 limits preparation for extra websites to keeping the API clean.
  - §4.17 repeats "extensions, not rewrites" for every Vision item (locations, child prices, memberships, heating) and puts no limit on what that may cost.
- **Fix:** add to §4.17:
  > Readiness for later extensions costs no v1 build time. v1 adds no tables, settings, endpoints or abstractions for Vision items. The architecture only checks that each Vision item could be added without rewriting the capacity core.

### G8. The Administrator cannot see cancellations and changes in the list
*Status: partially captured. Affects: UX, epics.*

- **Input:** brief L31 and L44: the administrator "sees every booking and cancellation".
- **PRD now:**
  - FR-16 lists Bookings without a status.
  - FR-26 and FR-33 say only that the Administrator "sees" a Change or a cancellation.
  - Nothing covers Bookings cancelled by a Block or by the Overbooking fallback (FR-40, FR-42), or the Guest's choice between a refund and a Voucher.
- **Fix:** add to FR-16:
  > Once Changes exist, each Booking shows its status: active, changed or cancelled. A cancelled Booking stays in the list with the time, the cause (Guest, Block or Overbooking fallback) and the Guest's choice of refund or Voucher. It is not counted in Seats booked.

### G9. DR-2 asks for a Guest test user that the Core cannot have
*Status: partially captured. Affects: the epics' README story, and SM-4.*

- **Input:** feedback L61: "Husk testbrukere (administrator og gjest) og eksempeldata i README."
- **PRD now:** DR-2 asks for "the test users (Administrator and Guest)", but guest accounts are If time 6 (§4.12), so the Core has no Guest account.
- **Fix:** reword DR-2:
  > The README gives the Administrator test login. Once §4.12 is built, it also gives a Guest test account. Until then, it lists the seeded sample Bookings and, once §4.8 is built, where to find a sample Manage link in the Outbox.

### G10. The assessment rubric is not used, and DR-1 could be more concrete
*Status: partially captured (low impact). Affects: the record of the process.*

- **Input:**
  - Feedback L93–L103 lists the seven part-1 assessment criteria, weighted 30, 20, 15, 10, 10, 10 and 5 %.
  - Brief L14 asks to "document honestly how AI was used".
- **Fix:**
  - Add a small table to §8.1 that maps each assessment criterion to the DRs and SMs that cover it. Making that map is how G6 was found.
  - Add to DR-1: "including where AI output was wrong or rejected, and how that was found."

## 2. Small fixes (low impact)

- **M1.** §1 calls Saunalöyly "a fictional Finnish sauna venue". The brief says Finnish-*inspired* (L12, L22), and the Venue runs on Europe/Oslo time and NOK. Write "a fictional, Finnish-inspired sauna venue".
- **M2.** The PRD's title note ("passed ... check") and DR-3 ("shown as free") overstate the name check. navnesok.no showed the name only as "possibly free as a trademark" (brief L105).
- **M3.** FR-39 drops the end of SC8: "(and 5 and 6 once step 2 is built)" (brief L93).
- **M4.** FR-47 only implies that the Send time can be changed. State that the Administrator sets it (brief L72, and L91: "at the time the administrator has chosen").
- **M5.** FR-43 lets the Administrator set the fixed values and the limit, but not see the Gift cards sold. Add a list showing each card's value, balance and expiry (brief L31: "manage gift cards").
- **M6.** FR-37 does not say where the sign-in choice appears in the booking flow. Put it after **Book**, and make continuing without an account the default and most prominent option (brief L35; the "Guest journey" section of the brief addendum; add. E, Baymard).
- **M7.** Add to §9: "No AI features in the app. AI is used only to build it" (feedback L40).
- **M8.** §7 has the blocking calendar sketched first, following the teacher's advice to sketch "administratorkalenderen" early (feedback L100). The blocking calendar is now If time 7. Sketch the Core Administrator booking list together with the booking flow as well.
- **M9.** §8.2 should note that the README already uses uv (feedback L58, L102), so that the architecture either keeps it or replaces it on purpose.

## 3. Superseded by decision (not gaps)

| Input point | What changed | Where it is logged | PRD location |
|---|---|---|---|
| Brief L55, L98, L119: HTTPS "not yet placed" | HTTPS is the first If-time item | PRD memlog L26; add. G | §4.7, §10.1 |
| Brief L35: choose the Window, then the number of Seats | The order is date, then Seats, then Window, as in brief L51 | PRD memlog L31 | FR-2, FR-3, UJ-1 |
| Brief L117: open cases for Administrator changes | D7, D8, F1, F2 and F3 decided | PRD memlog L27 | FR-38, FR-40, FR-41; add. B |
| Brief L118: open Door-code cases | H10, H13 and H23 decided; H6 deferred | PRD memlog L27, L28 | FR-47, FR-48, FR-50; §12 Q1; add. C |
| Feedback L48, L70, L98, L107: the minimal v1 is SC1 to SC4 with admin tools | The Core is SC1, SC9 (without HTTPS) and the laptop part of SC10. SC2–SC4 and SC8 are If time. Administrator screens come last in v1; the Core uses seed data | brief memlog L124; PRD memlog L7; add. G | §10.1 (NOTE FOR PM), §4.4, §4.13 |
| Feedback L71: vouchers ("verdikoder") in Step 2 | Vouchers stay in v1, because Changes depend on them | commit c55c757; brief addendum L22 | §4.8; §10.1 NOTE FOR PM |
| Feedback L39: booking without an account, "med referanse" | The Booking reference opens nothing; "My booking" only resends the link | brief memlog L126; add. G | FR-8, FR-20, FR-34 |
| Feedback L42: Seats held for 10 minutes | The Hold is If time 5; the Core books in one atomic step | brief memlog L123; add. G | §4.2, §4.11 |
| Feedback L100: responsive design | Laptop layout in the Core, mobile last in Step 2, no separate desktop level | commits 7ff954a, 37db707, 5a9dcbc; add. G | FR-22, FR-51 |
| Feedback L108: 3 to 5 security measures | Three measures in the Core; HTTPS is If time 1 | PRD memlog L26 | §4.5, §4.7 |
| Not in these inputs: the palette | Light wood replaces dark smoked timber. brief.md asks only for a "calm, Finnish-inspired style", which §6 keeps | PRD memlog L30; add. G | §6 |
| Not in these inputs: an informal test with three people | Rejected; how to verify "intuitive" is still open | PRD memlog L33; add. G | §12 Q2 (see G5) |

Some refinements keep the input's intent and are counted as captured:
- the strict Whole-sauna rule (brief L25; PRD memlog L22, L27);
- one Window per Booking (brief L26; PRD memlog L32);
- the 06:00 rule applying only to Whole-booking-only Saunas (brief L64; PRD memlog L19, L29);
- NIST password rules for every account (brief L96; PRD memlog L32).

## 4. brief.md, point by point

### Executive Summary (L12–L14)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| B01 | 12 | "a reservation system for saunas, delivered together with a website inspired by Finnish sauna culture" | captured | §1, §6, FR-1, FR-22 | |
| B02 | 12 | "reserve seats for themselves, their family or friends, or book an entire sauna privately" | captured | FR-2, §4.9, UJ-1, UJ-5 | |
| B03 | 12 | "Payment is simulated" | captured | FR-6, FR-7; Glossary "Simulated payment" | |
| B04 | 12 | "one fictional sauna venue, Saunalöyly, with at least four saunas" | partially captured | Glossary "Venue"; §1 | §1 says "Finnish sauna venue" (M1) |
| B05 | 14 | "a learning project delivered as an exam submission in 2026" | captured | §1 | |
| B06 | 14 | "a working, AI-built application, and to document honestly how AI was used and how the result was quality-assured" | captured | §1 ("honest record"), DR-1 | DR-1 could be more concrete (G10) |
| B07 | 14 | "can grow into a real service later, but the exam version does not pretend to be one" | captured | §1 | |
| B08 | 14 | "one person between 27 October and 15 December 2026" | captured | §1, §8.2 | |
| B09 | 14 | "a core that must finish, and additions that are built in a set order only if time allows" | captured | §0 "Delivery order", §10.1 | |

### The Problem (L18)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| B10 | 18 | "People who like Finnish saunas, or want to try one, need a simple way to see which times are open" | partially captured | §2.1, §6, UJ-1 | the two guest groups are not described (G4) |
| B11 | 18 | "the mix of two booking types in the same venue" | captured | §1, second paragraph | |
| B12 | 18 | "a private booking can collide with individual seats, capacity is double-sold, and cancellations leave the venue guessing" | captured | §1; FR-10, FR-29, FR-31, FR-32 | |

### The Solution (L22–L31)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| B13 | 22 | "A website that presents the sauna venue in a calm, Finnish-inspired style" | partially captured | §6 (style); FR-1 | the style is fully captured; the venue itself gets "a few lines" (G3) |
| B14 | 22 | "connected to a booking platform that handles the full guest journey" | captured | NFR-2, §7 | |
| B15 | 24 | "guests book seats in a time window, not a particular sauna" | captured | FR-4 | |
| B16 | 24 | "see the total number of free seats across the saunas not booked in full" | captured | FR-3; Glossary "Seat capacity", "Seats left" | |
| B17 | 24 | "fills one sauna at a time in an order the administrator sets" | captured | Glossary "Fill order"; FR-31 (INV-5); FR-38 | |
| B18 | 24 | "a group can be split; a group that wants to stay together books a whole sauna" | captured | FR-4; Glossary "Placement" | Placement is a count, not an assignment |
| B19 | 25 | "bookable in full ... as long as no individual seats are placed in them" | captured | FR-29 | made strict (Room ahead) by decision: PRD memlog L22, L27 |
| B20 | 25 | "keeps the last saunas in the fill order free where it can ... left to the architecture" | captured | FR-31; §12 Q5; add. A | |
| B21 | 26 | "Pricing: set per time window: one price per seat and one price per whole sauna" | contradicted | FR-26 [ASSUMPTION]; FR-3, FR-38, NFR-4, §12 Q3, add. J | the PRD assumes no price differences between Windows, with no logged decision (G1). The per-Sauna Whole-sauna price matches brief addendum L55 |
| B22 | 26 | "no distinction between children and adults" | captured | §9, §4.17 | |
| B23 | 26 | "Guests can book several windows" | captured | FR-9, §9 | one Window per Booking (PRD memlog L32) |
| B24 | 27 | "Payment and email: both are simulated. Guests get a booking reference by email." | captured | FR-6, FR-8, FR-17 | |
| B25 | 28 | "anyone can buy a gift card without an account, and whoever holds the code books with it" | captured | FR-43, FR-44 | |
| B26 | 29 | "individual seats can be changed, or swapped for a voucher, up to 12 hours before the start" | captured | FR-26, FR-27; Glossary "Cutoff" | |
| B27 | 29 | "a whole sauna can be cancelled, with a refund or voucher, or changed up to 72 hours before" | captured | FR-33 | |
| B28 | 30 | "bookers get their door codes by email shortly before the window" | captured | FR-46, FR-47 | 20 minutes by default |
| B29 | 30 | "never depend on taking back a code ... cannot be booked in full while seat bookers hold its code" | captured | FR-48 (H12) | |
| B30 | 31 | "administrators manage time windows, capacity and prices" | captured | FR-38 (If time 7); §4.4 (seed data in the Core) | |
| B31 | 31 | "and see every booking and cancellation" | partially captured | FR-16; FR-26; FR-33 | the list has no status or cancellations (G8) |
| B32 | 31 | "Time windows are the same for every sauna and never partly overlap" | captured | FR-13; Glossary "Window" | |
| B33 | 31 | "In step 2 they also manage gift cards and door codes" | partially captured | FR-43; FR-45, FR-49 | no admin view of the Gift cards sold (M5) |
| B34 | 31 | "In a calendar, they can block one or all saunas for a period" | captured | FR-40; §7 | |
| B35 | 31 | "only five rules are settings with defaults; all other rules are fixed" | captured | FR-39; Glossary "Setting" | |
| B36 | 31 | "A changed setting applies only to new bookings" | captured | FR-39 | the horizon, deadline and Release time apply from the moment of the change [ASSUMPTION] |

### The guest's journey (L35)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| B37 | 35 | "first chooses Individual seats or Private sauna, picks a date in a calendar, and sees the time windows" | captured | FR-1, FR-2, FR-3, FR-30; §7 | the date can also be typed (FR-2) |
| B38 | 35 | "picks a window (and the number of seats)" | superseded by decision | FR-2, FR-3, UJ-1 | PRD memlog L31: date, then Seats, then Window (as in brief L51) |
| B39 | 35 | "presses Book, logs in or continues without an account" | partially captured | §4.2; FR-37 | the Core needs no account (captured), but the PRD does not say where sign-in appears once accounts exist (M6) |
| B40 | 35 | "accepts the terms and pays" | captured | FR-5, FR-6 | |
| B41 | 35 | "In the core every guest continues without an account" | captured | §4.2, §7 | |

### What Makes This Different (L39)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| B42 | 39 | "competes with other booking platforms on price, on how well it attracts guests, and on features" | missing | belongs in §1 | G4 |
| B43 | 39 | "the Finnish-inspired identity for an audience that already likes saunas, and one system that handles individual seats and whole-sauna bookings side by side" | partially captured | §1, §6 | both are described, but not as differentiators, and the audience is missing (G4) |
| B44 | 39 | "None of this is proven yet: the exam version does not test prices or customer demand" | missing | belongs in §1 and §9 | G4 |
| B45 | 39 | "the booking rules are defined precisely enough to be tested, and ... the process is documented for assessment" | captured | §1, second paragraph; DR-1, DR-4 | |

### Who This Serves (L43–L44)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| B46 | 43 | "people who already enjoy Finnish saunas or are curious to try" | partially captured | §6 ("first-time Guest"); UJ-1 | the regulars are missing (G4) |
| B47 | 43 | "book for themselves or a group, and need to see availability and price clearly and cancel easily" | captured | §2.1; FR-3; FR-26, FR-27, FR-33 | until §4.8, the terms say a Booking cannot be changed online (FR-5) |
| B48 | 44 | "manages when saunas are open, at what capacity and price, and sees every booking and cancellation" | captured | §2.1; FR-16, FR-38; §12 Q3 | for the cancellation view, see B31 |

### Scope: core of v1 (L50–L55)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| B49 | 50 | "One fictional sauna location with at least four saunas, and one website in English" | captured | Glossary "Venue"; NFR-5 | |
| B50 | 50 | "A Python backend and JavaScript frontend" | captured | §8.2 | |
| B51 | 50 | "kept separate from the website through a single API. v1 supports one website only" | captured | NFR-2, §9 | |
| B52 | 51 | "picks a date, a number of seats and a time window, then books and pays (simulated, instant)" | captured | §4.1, §4.2 | |
| B53 | 51 | "gives a name and an email, with no account, and gets a booking reference by simulated email" | captured | FR-5, FR-8 | |
| B54 | 52 | "set by a seed or configuration file, with no administrator screens" | captured | §4.4, NFR-4, §9 | |
| B55 | 52 | "booking horizon, booking deadline, cancellation cut-offs ... are fixed defaults" | captured | Glossary; FR-2, FR-3; FR-39 table | |
| B56 | 53 | "The database enforces that booked seats in a window never exceed capacity ... one atomic step" | captured | FR-10; §4.2; add. A | |
| B57 | 54 | "one account with password login, and a simple list of bookings" | captured | FR-15, FR-16 | the grouping is [ASSUMPTION] |
| B58 | 55 | "Input validation, hashed passwords and role-based access, each tested automatically" | captured | FR-18, FR-19, FR-20; SM-2 | |
| B59 | 55 | "HTTPS is not yet placed" | superseded by decision | §4.7, §10.1 | PRD memlog L26: If time 1 |
| B60 | 55 | "A simple layout for a laptop screen; the mobile layout comes last in step 2" | captured | FR-22, FR-51 | |

### Scope: if time allows (L59–L67)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| B61 | 59 | "Changing individual seats ... or taking a voucher instead"; no refund; change first, voucher last | captured | §4.8, FR-26, FR-27 | now If time 2, after HTTPS (PRD memlog L26) |
| B62 | 60 | "Whole-sauna booking ..., which needs seats placed in specific saunas" | captured | §4.9, FR-31 | |
| B63 | 61 | "My booking": reference and email, "the change-or-cancel link sent again"; the link is "the only way into a booking" | captured | §4.10 (FR-34); FR-20 | |
| B64 | 62 | "The 10-minute seat hold while a guest pays" | captured | §4.11 | |
| B65 | 63 | "Guest accounts" | captured | §4.12 | |
| B66 | 64 | "administrator screens ..., the five adjustable settings, the blocking calendar, the 06:00 rule, whole-booking-only windows, and the overbooking fallback" | captured | §4.13 (FR-38 to FR-42) | the 06:00 rule covers only Whole-booking-only Saunas (PRD memlog L19, L29) |
| B67 | 65, 67 | cancelling before whole-sauna booking; v1 before step 2; mobile last; "the rest of the order is a proposal" | captured | §0, §10.1 | items 3 to 6 marked [ASSUMPTION] |

### Scope: step 2 (L71–L73)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| B68 | 71 | "Gift cards: buying without an account, and booking with the code" | captured | §4.14 | |
| B69 | 72 | "Door codes sent by email to exactly the bookers who may use each door, with the administrator's tools to set the timing" | partially captured | FR-46, FR-47 | that the Administrator sets the timing is only implied (M4) |
| B70 | 73 | "Mobile layout, last, after the laptop layout works" | captured | §4.16 (FR-51) | |

### Scope: not in the first version or step 2 (L77–L80)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| B71 | 77 | "Real payment, email, door locks, lock systems, heaters and temperature sensors" | captured | §9 | |
| B72 | 78 | "Other languages, more than one location, other bookable resources, and native mobile apps" | captured | §9, §4.17 | |
| B73 | 79 | "Support for more than one website" | captured | NFR-2, §9 | |
| B74 | 80 | "Memberships, period cards, the distinction between children and adults ..., remote door control and heating control: see the vision" | captured | §4.17, §9 | |

### Success Criteria (L84–L99)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| B75 | 84 | "The core is done when the website is complete, the booking platform is connected, and criteria 1 and 9 and the laptop part of 10 work" | partially captured | §10.1 "Core done" | SC9 without HTTPS (PRD memlog L26); "website is complete" is undefined (G3) |
| B76 | 84 | "Criteria 2 to 4 and 8 follow the if-time order ..., and 5, 6 and the mobile part of 10 belong to step 2" | captured | SM-5, SM-6 | |
| B77 | 84 | "A criterion not reached is reported as not delivered" | captured | §0, §11, DR-2 | |
| B78 | 86 | SC1: four Seats; at the last Seat "exactly one gets it"; "Parallel automated tests prove it; no speed figure" | captured | SM-1; FR-10, FR-11, FR-12; NFR-7 | |
| B79 | 87 | SC2: "it cannot be booked again and its seats are no longer available" | captured | FR-29; SM-5 | |
| B80 | 88 | SC3: "changes seats or takes a voucher, and capacity is restored" | captured | FR-26, FR-27; SM-5 | |
| B81 | 89 | SC4: "cancels with a refund or voucher, or changes the time, and capacity is restored" | captured | FR-33; SM-5 | |
| B82 | 90 | SC5: gift card without an account; whoever holds the code books with it | captured | FR-43, FR-44; SM-6 | |
| B83 | 91 | SC6: "codes for exactly the doors they may use, at the time the administrator has chosen" | captured | FR-46, FR-47, FR-48; SM-6 | see M4 |
| B84 | 92 | SC7: membership and period card (vision) | captured | §4.17 | correctly has no SM |
| B85 | 93 | SC8: "applies to new bookings only; with the defaults, criteria 1 to 4 behave as described (and 5 and 6 once step 2 is built)" | partially captured | FR-39; SM-5 | the part about SC5 and SC6 is missing (M3) |
| B86 | 95 | Input validation: "checks all input on the server and rejects ... without changing any data" | captured | FR-18 | |
| B87 | 96 | "passwords are stored hashed, and guest accounts require strong passwords" | captured | FR-19 | the same rules apply to Administrators (PRD memlog L32) |
| B88 | 97 | "only a logged-in administrator can reach administrator functions, and a guest can see and change only their own bookings" | captured | FR-20, FR-25, FR-37 | |
| B89 | 98 | HTTPS: "served only over HTTPS ... Whether HTTPS is core or if-time is not yet decided" | captured | FR-24 | the placement was decided in PRD memlog L26 |
| B90 | 99 | "a laptop screen (core), and then on mobile and at any window size ... one stylesheet" | captured | FR-22, FR-51 | |

### Delivery Requirements (L105–L106)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| B91 | 105 | "no licensed, trademarked or otherwise protected material; everything is AI-generated, freely licensed or checked by the author" | captured | DR-3; §6; add. F | |
| B92 | 105 | navnesok.no shows the domain and company name as free "and the name as possibly free as a trademark" | partially captured | title note; DR-3; §12 Q10 | the word "possibly" was dropped (M2); the PRD adds a check of existing LÖYLY marks (PRD memlog L24) |
| B93 | 106 | "working code, with documentation of how AI was used and how the code was quality-assured" | captured | DR-1 | |

### Vision (L110)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| B94 | 110 | real payment and email, languages, locations A and B, several websites, other resources, children, memberships, period cards, remote doors, heating | captured | §4.17 | |
| B95 | 110 | "The first version is built so those steps are extensions, not rewrites" | captured | §4.17 | no limit on what this may cost (G7) |

### Open Questions (L114–L120)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| B96 | 114 | "The exact limits for input validation and password strength ..., and the password-hashing algorithm" | captured | FR-2, FR-5 [ASSUMPTION], FR-19; add. A (Argon2id) | 10 Seats and 15 characters decided (PRD memlog L32) |
| B97 | 115 | "the database engine ... and whether seat placement is stored or derived from counts" | captured | §12 Q4, Q5; add. A | |
| B98 | 117 | Administrator changes: "lifting a block, marking a sauna whole-booking-only while it holds seats, lowering capacity, changing the fill order, and changes in a window that has started" | superseded by decision | FR-38, FR-40, FR-41; add. B | PRD memlog L27 |
| B99 | 118 | Door codes: two codes on one door, a changed send time, a block after sending, one-sauna access while bookings are split | superseded by decision | FR-47, FR-48, FR-50; §12 Q1; add. C | H10, H13 and H23 decided (PRD memlog L27); H6 deferred (L28) |
| B100 | 119 | HTTPS core or if-time; whether each seat carries its sauna; "the backward check of the build order from 15 December, which was not run" | partially captured | §4.7; §12 Q5, Q6 | HTTPS decided (PRD memlog L26); Q6 has no owner or deadline (G2) |
| B101 | 120 | "whether a real lock accepts two codes with different PINs on one door, and whether a code can be changed after its validity started" | captured | §12 Q8; add. C | |

## 5. Teacher feedback, point by point

### Overall assessment (L16–L23)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| F01 | 16 | "Bookingreglene er usedvanlig presise ... 12 og 72 timer. Det gjør domenet testbart" | captured | §1, second paragraph; FR-29, FR-31; Glossary "Cutoff" | |
| F02 | 17 | "Suksesskriterium 1–8 er konkrete scenarioer som nesten direkte kan bli automatiske tester" | captured | testable consequences on every FR; NFR-6; SM-1, SM-5, SM-6 | |
| F03 | 17 | "mange små, beskrivende steg – akkurat den typen sporbarhet sensor ser etter" | captured | DR-4 | |
| F04 | 21 | "V1 er svært stort for én person ... Flytt flere av disse til senere trinn" | captured | §10 (Core, If time, Step 2, Vision); §4.17 | |
| F05 | 22 | "Suksesskriterium 9 ... kan ikke testes slik det står. Erstatt det med konkrete tiltak" | captured | FR-18, FR-19, FR-20, FR-24; SM-2 | |
| F06 | 23 | "ikke la forberedelser for fremtiden ta tid fra kjerneflyten i v1" | partially captured | NFR-2, §9 | the limit covers only websites; §4.17 has none (G7) |

### Difficulty (L29–L48)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| F07 | 29–31 | "Vanskelig ... omfattende domenelogikk som må stemme" | captured | §1, second paragraph; §10.1 NOTE FOR PM | |
| F08 | 37 | "Fordeling av plasser ..., konflikt ..., frister, verdikoder, refusjon, medlemspris, periodekort og regler som bare gjelder nye bookinger" | captured | FR-26 to FR-33, FR-39; member price and period cards in §4.17 | |
| F09 | 38 | "Badstue, tidsvindu, booking, plass, gjest, gavekort, verdikode, medlemskap, periodekort, dørkode, blokkering og innstillinger" | captured | §3 Glossary | the Vision entities are left out of v1 |
| F10 | 39 | "Administrator (påkrevd) og gjest (valgfri konto)" | captured | FR-15; FR-37 (If time 6) | |
| F11 | 39 | "pluss booking uten konto med referanse" | superseded by decision | FR-8, FR-20, FR-34 | the Booking reference opens nothing; only the link is resent (brief memlog L126; add. G) |
| F12 | 40 | "Ingen KI i appen. KI brukes i utviklingen" | partially captured | §1, DR-1 | "no AI in the app" is not a stated non-goal (M7) |
| F13 | 41 | "Betaling, e-post, dørlåser og oppvarming er simulert ... Simuleringene må likevel bygges og testes" | captured | FR-6, FR-7 (test switch), FR-17; add. A "Simulated lock"; §9 | heating is not built at all |
| F14 | 42 | "Flere gjester booker samme tidsvindu, plasser holdes i 10 minutter, og dobbeltbooking må hindres" | captured | FR-10, FR-11, FR-14; FR-35, FR-36 | the Hold moved to If time (brief memlog L123) |
| F15 | 43 | "Filhåndtering ... Ikke en del av v1" | captured | (nothing required) | |
| F16 | 44 | "Kontoer med navn, e-post og passord, og rollebasert tilgang" | captured | FR-18 to FR-21 | |
| F17 | 48 | "Definer en minimal versjon som sikkert kan bli ferdig ... suksesskriterium 1–4 ... med administratorvisning" | superseded by decision | §10.1 NOTE FOR PM | the Core is SC1, SC9 and the laptop part of SC10 (brief memlog L124; PRD memlog L7) |

### Feasibility with BMAD and Claude Code (L52–L72)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| F18 | 52 | "det må være tid til hele denne flyten, og til testing, retting og README til slutt" | captured | §8.2 (freeze 9–15 December); add. I | |
| F19 | 56 | "Stor risiko ... Kjernen (1–4) er realistisk; alt er det neppe" | captured | §8.2; §10.1 NOTE FOR PM | |
| F20 | 57 | "Antallet stories blir høyt med dagens scope; færre funksjoner gir en mer overkommelig plan" | partially captured | §10; add. I | no rule for how deep planning goes (G2) |
| F21 | 58 | "Python-backend og JavaScript-frontend med uv ... Hold separasjonen ... enkel (ett API)" | captured | §8.2, NFR-2 | uv is not named (M9) |
| F22 | 59 | "Dere har selv definert reglene og kan avgjøre om koden følger dem" | captured | §1, second paragraph; DR-1 | |
| F23 | 60 | "Legg til tester for samtidighet (to gjester som booker siste plass samtidig)" | captured | FR-11; NFR-6; SM-1 | |
| F24 | 61 | "Husk testbrukere (administrator og gjest) og eksempeldata i README" | partially captured | DR-2; NFR-1 | the Core has no Guest account (G9) |
| F25 | 62 | "Ingen betalte tjenester" | captured | §8.2; NFR-1 | |
| F26 | 70 | "V1: enkeltplasser og hele badstuer, ..., endring og avbestilling med frister, og administratorverktøy for tidsvinduer, kapasitet, priser og blokkering" | superseded by decision | §10.1; §4.4; §4.13 | all of it is in v1, but only Seats are Core; the admin tools are If time 7, with seed data in the Core (brief memlog L124; add. G) |
| F27 | 71 | "Trinn 2 ...: gavekort ..., deretter dørkoder" | captured | §10.2; §4.14, §4.15 | |
| F28 | 71 | "gavekort og verdikoder" in Step 2 | superseded by decision | §4.8; §10.1 NOTE FOR PM | Vouchers stay in v1 (commit c55c757; brief addendum L22) |
| F29 | 71 | "Trinn 2 (når v1 er stabil og testet)" | partially captured | §0, §10 | the order is kept, but there is no stability or test gate (G2) |
| F30 | 71 | "Flytt medlemskap, periodekort, fjernstyring av dører og styring av oppvarming til visjonen" | captured | §4.17; §9 | commit c55c757 |
| F31 | 72 | "Begrens de justerbare reglene til noen få innstillinger med standardverdier" | captured | FR-39 | commit e48b9e2 |

### Why the brief matters (L76)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| F32 | 76 | "sporbar vei fra plan til ferdig app ... gjør det dere har beskrevet, ... testet, ... kan kjøres etter README" | captured | §0; DR-2, DR-4; SM-4 | |
| F33 | 76 | "om den er godt designet" | partially captured | §6; SM-3 | nothing checks the design intent; Q2 is open (G5) |

### Part 1: the brief's sections (L82–L89)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| F34 | 82 | "Klart og ærlig ... som ikke later som det er en ekte tjeneste" | captured | §1, third paragraph | |
| F35 | 83 | "Konflikten mellom enkeltplasser og private bookinger, dobbeltsalg og avbestillinger" | captured | §1, second paragraph | |
| F36 | 84 | "mangler en kort beskrivelse av gjestens vei ... (velg tid → velg plasser eller hel badstue → betal → få bekreftelse)" | captured | §2.3 (UJ-1, UJ-5); §7 | the journey was added to the brief in commit 8bcfbbc; the PRD's order follows PRD memlog L31 |
| F37 | 85 | "Ærlig om at markedsfordelen ikke er bevist, og at styrken nå er presise, testbare regler" | partially captured | §1, second paragraph | the strength is kept; "not proven" is dropped (G4) |
| F38 | 86 | "Sensor er ikke en bruker av appen" | captured | §2.2 | |
| F39 | 87 | "Kriterium 9 er for vagt, og 11–12 er krav til leveransen, ikke appen" | captured | §4.5; §8.1 | commits fed9275, 182f12e |
| F40 | 88 | "«In» er for stort for én person. Del i v1 og trinn 2" | captured | §10 | |
| F41 | 89 | Vision: "Realistisk og tydelig adskilt fra v1" | captured | §4.17 | |

### Part 2: assessment criteria for part 1 of the portfolio (L97–L103)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| F42 | 97 | "Prosess og KI-styring (30 %) ... krav kan spores fra brief til kode ... Fortsett slik" | captured | DR-1, DR-4; FRs cite brief tests and catalogue IDs; each SM lists the FRs it covers | the PRD does not use the rubric (G10) |
| F43 | 98 | "Funksjonalitet og omfang (20 %) ... nok innhold til å vise reell funksjonalitet ... En stabil v1 med kriterium 1–4" | superseded by decision | §10.1 NOTE FOR PM | narrower Core (brief memlog L124; PRD memlog L7); the remaining risk is flagged in the PRD |
| F44 | 99 | "Legg til samtidighetstester og konkrete sikkerhetstester" | captured | FR-11; FR-18, FR-19, FR-20; NFR-6 | |
| F45 | 100 | "Finsk-inspirert, rolig stil" | captured | §6 | |
| F46 | 100 | "og responsivt design gir god retning" | superseded by decision | FR-22, FR-51 | laptop in the Core, mobile last in Step 2, no desktop level (commits 7ff954a, 37db707, 5a9dcbc; add. G) |
| F47 | 100 | "Skisser bookingflyten og administratorkalenderen tidlig" | captured | §7, last bullet | the blocking calendar is now If time 7 (M8) |
| F48 | 101 | "ett enkelt API i v1, uten støtte for flere nettsider" | captured | NFR-2; §9; §8.2 | |
| F49 | 102 | "Legg til oppstart av frontend, testbrukere og eksempeldata" | captured | DR-2; NFR-1 | see F24 |
| F50 | 103 | "En plan for hvor hemmeligheter, testdata og dokumentasjon skal ligge" | partially captured | DR-3 only | G6 |
| F51 | 103 | "Kravet om «rene» ressurser ... er også bra" | captured | DR-3 | |

### Next steps (L107–L111)

| ID | Line | Point | Status | PRD / addendum | Note |
|---|---|---|---|---|---|
| F52 | 108 | "3–5 konkrete, testbare sikkerhetstiltak, og flytt 11–12 til en egen liste over leveransekrav" | captured | §4.5 (three in the Core), §4.7; §8.1 | HTTPS placed as If time 1 (PRD memlog L26) |
| F53 | 109 | "Lukk de åpne spørsmålene i addendumet som gjelder v1 (enkeltplasser og booking uten konto)" | partially captured | §12 Q2, Q3; FR-5 [ASSUMPTION] | Q2 and Q3 still affect the Core; both have an owner and a deadline |
| F54 | 111 | "Oppdater product brief i repoet ... slik at historikken viser hvordan planen utviklet seg" | captured | DR-4; add. H (list of upkeep) | the brief was updated through 2026-10-29 |
