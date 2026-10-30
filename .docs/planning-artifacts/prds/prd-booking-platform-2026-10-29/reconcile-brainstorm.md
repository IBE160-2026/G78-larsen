---
title: "Input reconciliation: brainstorm-minste-v1 vs PRD"
created: 2026-10-29
inputs:
  - .docs/brainstorming/brainstorm-minste-v1-mvp-2026-10-27/brainstorm-intent.md
  - .docs/brainstorming/brainstorm-minste-v1-mvp-2026-10-27/.memlog.md
checked_against:
  - prd.md (draft v1, 2026-10-29)
  - addendum.md
  - .memlog.md (PRD decision log)
  - also consulted for decision trail: brief .memlog.md (L124-L126), brief.md, brief addendum.md (Schedule and build order, L180-L188), .logs/lisa-larsen/994-...-oppdater-brief-etter-research.md, .logs/lisa-larsen/issues.md
---

# Input reconciliation: brainstorm (2026-10-27) vs PRD

## How to read this

- **Origin:** `user` = Lisa's decision, idea or insight ("[user]" in the intent; "(decision/idea/insight by user)" in the memlog). `coach` = coach proposal ("[proposal]"; "(idea by coach)"). `source` = teacher or brief context carried by the brainstorm. `synthesis` = the memlog wrap-up line.
- **Status:** captured / partially captured / missing / contradicted / superseded by decision (with the line that decided it).
- **Line refs:** `I-Lnn` = brainstorm-intent.md, `M-Lnn` = brainstorm .memlog.md, `PRD Lnn` = prd.md, `Add Lnn` = addendum.md, `PM-Lnn` = PRD .memlog.md, `BM-Lnn` = brief .memlog.md, `SL994` = session log 994 (2026-10-29).
- "Untagged" marks a coach proposal that the PRD states as decided, without `[ASSUMPTION]`, although PRD §0 (PRD L23) says unconfirmed inferences are tagged.

## Totals

- **brainstorm-intent.md:** 56 points. 41 captured (4 of them untagged coach proposals stated as decided), 7 partially captured, 1 contradicted, 2 missing, 5 superseded by decision.
- **brainstorm .memlog.md:** 36 lines. 4 are process lines (n/a). Of the 32 substantive lines: 24 captured, 7 partially captured, 1 superseded by decision. The missing and contradicted parts sit inside partially captured lines (M-L18, M-L30, M-L35).

---

## Table A: brainstorm-intent.md

### Context and constraints

| Input | Point (short quote) | Origin | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| I-L14 | "One person, 27.10.2026 to 15.12.2026 … teacher rates the schedule risk as high" | source | captured | PRD L33, §8.2 L810, §10.1 NOTE L853 | |
| I-L15 | "Two other exams … 16.11.2026 and 08.12.2026" | user | captured | §8.2 L810 | |
| I-L16 | "Claude tokens and long-running tasks are a real limit" | user | captured | §8.2 L811 | |
| I-L17 | "Frontend/design and extensive testing are the likeliest overruns" | user | captured (as a constraint) | §8.2 L811; SM-C1, SM-C4 L876-879 | The constraint is stated, but Core frontend scope grew past the brainstorm's mitigation (see Gap 5). |
| I-L18 | "Planning (PRD and architecture) takes 7-8 days of the first 12; coding starts after, as tokens allow" | user | captured | §8.2 L812 | "as tokens allow" dropped; harmless. |

### MVP (the one feature: individual seats)

| Input | Point (short quote) | Origin | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| I-L22 | "Book individual seats end to end" | user | captured | §4.1-4.3, §10.1 L832-840, SM-1 | |
| I-L24 (a) | "Time windows, capacity and prices live in the database" | user | **partially captured** | §4.4 L298 and NFR-4 L759 say "come from seed data" | The PRD never says these are stored in the data store. The brief does ("kept in the database", brief.md L52). See Gap 2. |
| I-L24 (b) | "seeded by script or config, no admin screens for them" | coach | captured | §4.4 L298, §9 L826, Add G L248 | Adopted via the brief (brief.md L52; Lisa placed admin screens in If time, BM-L124). Add G L248 dates the change to 2026-10-27, when it was still a proposal (Gap 8). |
| I-L25 (a) | "pick date, number of seats, time window, then book and pay" | user | captured, extended | UJ-1 L53-64, FR-2, FR-3, FR-5, FR-6; PM-L31 (6A) | The PRD inserts a separate review step with terms acceptance. |
| I-L25 (b) | "One booking page and one confirmation page" | coach | **contradicted** (proposal not adopted; no decision logged) | §7 L781 (Book seats → Details and review → Confirmation); FR-5 L203-214 | PM-L32 decides the pre-purchase information and the "Pay NOK …" button, not a separate page. See Gap 5. |
| I-L25 (c) | "native date picker" | coach | partially captured | FR-2 L174 | FR-2 (typed and keyboard-operable) is compatible with the browser's native date input but does not name it. Add E L196 leans towards a radio list. |
| I-L25 (d) | "time windows as a list with free seats" | coach | captured | FR-3 L177-186 | |
| I-L26 (a) | "free-text name plus email … name kept minimal" | user | captured | FR-5 L207 ("Nothing else is asked") | |
| I-L26 (b) | "no account" | coach | captured | §4.2 L199, FR-5 L207 | Also brief Scope; account-less booking confirmed earlier (BM-L67). |
| I-L27 | "Simulated payment is instant" | user | captured | §4.2 L199, FR-6 | Extended by FR-7, a failed-payment test switch (PM-L32). |
| I-L28 (a) | "Confirmation with a booking reference by email" | user | captured | FR-8 L232-245 | |
| I-L28 (b) | "the email is an outbox table, also shown on the confirmation page" | coach | captured; refined by decision | FR-8 L243, FR-17 L323-329, Glossary L146 | Outbox restricted to Administrators; the Guest sees only their own email (PM-L25, 1A). |
| I-L29 (a) | "The database enforces 'never two bookings on the last seat'" | user | captured (Core) | §4.3 L254, FR-10 L258-263, FR-11 L265-271 | FR-10 L263 limits the store-level refusal to the Core and leaves If time to the architecture (Add A L16). Honestly flagged; see watch item W1. |
| I-L29 (b) | "Booking is atomic in one transaction" | coach (follows from user decision M-L22) | captured | §4.2 L199, FR-6 | |
| I-L29 (c) | "concurrency test (two guests, last seat)" | coach | captured | FR-11 L269-271, UJ-2, NFR-6 L761 | |
| I-L30 (a) | "Admin: password login and a simple booking list" | user | captured | FR-15, FR-16, UJ-3 | |
| I-L30 (b) | "one seeded admin account, hashed password, session cookie, role check tested as guest and unauthenticated" | coach | captured | FR-15 L306, FR-19, FR-20 L364-367, DR-2 L803 | Session mechanics left to architecture. RB-2 needs §4.12; in the Core, RB-1 covers the anonymous caller. |
| I-L31 | "Server-side input validation, hashed passwords and role-based access, each with an automated test … HTTPS see open items" | source (brief SC9) | captured | §4.5 FR-18-FR-20; HTTPS → §4.7 | HTTPS placement superseded by PM-L26 (2B). |

### If time

| Input | Point (short quote) | Origin | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| I-L33 | "(order is a proposal)" | coach | captured | §10.1 L851, §12 Q6 L887 | Items 3-6 are tagged `[ASSUMPTION]`. |
| I-L35 (a) | "Cancel individual seats up to 12 hours before start, capacity restored" | user (order decided at M-L44) | captured; position superseded by decision | §4.8, FR-26, FR-27, §10.1 L844 | Now If time 2, after HTTPS (PM-L26). |
| I-L35 (b) | "refund simulated and no voucher at first" | coach | **superseded by decision** | §4.8 L426, §9 L820, Add G L239 | BM-L125: "Cancelled individual seats give only a voucher or a change, never a refund … Drops the brainstorm's interim simulated refund." |
| I-L35 (c) | "change as cancel plus new booking" | coach | captured | §4.8 L426, Glossary L124 | |
| I-L35 (d) | "Voucher last" | coach | captured (tagged) | §4.8 L426 `[ASSUMPTION]`, §13 L907 | Matches BM-L125 "[ASSUMPTION on order]". |
| I-L36 | "Whole-sauna booking … bookable only when no individual seats are placed in it" | coach (order) | captured; rule superseded by decision | §4.9, FR-29-FR-33, Glossary L132-133, §12 Q5 | Strict rule Seats booked ≤ Room ahead (PM-L27, 3A). |
| I-L37 | "'My booking' lookup by reference plus email" | coach | **superseded by decision** | §4.10 FR-34, Add G L238 | BM-L126: "only resends the change-or-cancel link … reference plus email as access is dropped." |
| I-L38 | "10-minute seat hold [user: postponed]" | user | captured | §4.11, §10.1 L847, Add G L241 | M-L22. |
| I-L39 | "Guest accounts" | coach (order) | captured | §4.12 (If time 6) | |
| I-L40 | "Step 2 from the brief: gift cards, door codes" | coach (order) | captured; order superseded by decision | §4.14, §4.15, §10.2 L856 | §4.13 (rest of v1) now comes before Step 2, and mobile is last in Step 2: Lisa, 2026-10-29 (SL994 13:54, 14:03). Not in any memlog; BM-L124 still says "after step 2" (Gap 7). |

### Build order

| Input | Point (short quote) | Origin | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| I-L44 (a) | "PRD derived from the brief and limited to the MVP" | coach | **superseded by decision** (for the PRD itself) | Whole PRD: 51 FRs over Core, If time, Step 2 and Vision | PM-L13 "kjøre hele PRD-en på nytt (Opus, effort max)"; PM-L15 "grundigere enn v0"; PM-L8 phase labels per feature. |
| I-L44 (b) | "architecture limited to decisions that must be consistent (database engine, booking transaction, API shape)" | coach | **missing** | — (§0 L13 names architecture as a downstream reader) | No scoping instruction. Add A also carries If-time and Step-2 direction (Holds, Manage-link hardening, simulated lock). See Gap 1. |
| I-L44 (c) | "epics and stories for the MVP only" | coach | **missing** | — (§0 L13) | §7 L791 asks UX to sketch the blocking calendar (If time 7) first. See Gap 1. |
| I-L45 | "Database engine decision, schema and the capacity invariant" first | coach | partially captured | Add I L274 (flagged as unconfirmed); §12 Q4 L885 | Q4 has no timing ("week 1", M-L19) and no deciding constraint. See Gap 3. |
| I-L46 | "Walking skeleton: a thin booking … so an interruption always leaves a running app" | coach | captured (addendum only) | Add I L275 | Not in the PRD body, so the epics workflow will not see it as a first story. See Gap 1. |
| I-L47 (a) | "tests written inside each story as part of 'done'" | coach | captured, **untagged** | NFR-6 L761 | Stated as a requirement. Add I L271 says "Lisa has not confirmed it". See Gap 4. |
| I-L47 (b) | "Window 17.11 to about 1.12" | coach | captured (addendum) | Add I L278 | |
| I-L48 | "Admin list and login [user]" | user (content); synthesis (position) | captured | §4.4; Add I L276 | Add I L271 lumps this user decision in with "Lisa has not confirmed it" (Gap 8). |
| I-L49 | "Freeze 9.12-15.12: tests, README (test users, sample data, frontend start), AI-use documentation, no new features" | coach | captured, **untagged** | §8.2 L813, DR-1 L796-799, DR-2 L800-805, SM-4 | §8.2 states it as a constraint, while Add I L277 and the brief addendum (L186, "Build order (proposal)") call it a proposal. See Gap 4. |
| I-L51 | "27.10 to about 8.11 … 17.11 to about 1.12 … 9.12 to 15.12" | coach | captured (addendum) | Add I L278 | |

### Mitigations for the named risks

| Input | Point (short quote) | Origin | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| I-L55 (a) | "small stories with acceptance criteria taken from the brief" | coach | partially captured | Add I L280 ("Keep stories small") | "AC from the brief" is not carried. The PRD's testable consequences can serve, but no text says so. |
| I-L55 (b) | "a token budget per story logged in the session log as evidence of AI steering (counts 30% of part 1)" | coach | partially captured, **untagged** | DR-1 L798; Add I L280 | DR-1 makes it a delivery requirement without a tag. The reason (30 % of part 1) is dropped. See Gap 4. |
| I-L55 (c) | "mechanical tasks at lower effort" | coach | captured (addendum) | Add I L281 | |
| I-L55 (d) | "[user: tokens can be an advantage]" | user | captured | DR-1 L797-798 | |
| I-L56 (a) | "one stylesheet" | coach (adopted in brief SC10, brief.md L99) | captured | FR-22 L397, §4.6 L388 | |
| I-L56 (b) | "Finnish-inspired palette and typography" | coach | captured; refined by decision | §4.6, §6 L766-778 | PM-L30 (5B). |
| I-L56 (c) | "mobile first" | coach | **superseded by decision** | PRD L25, §4.6 L388, §4.16, §10.2 L856; Add G L240 | Laptop first, mobile last in Step 2: Lisa, 2026-10-29 (SL994 13:39, 13:54, 14:03; brief.md L99). No line in the PRD or brief memlog (Gap 7). |
| I-L56 (d) | "no design system" | coach | captured, **untagged** (minor) | §4.6 L388 | The brief addendum (L187) marks it a proposal. |
| I-L57 | "depth on concurrency, capacity, validation and criterion 1; breadth only for the rest" | coach | captured, **untagged** | NFR-6 L761, SM-C1 L876 | See Gap 4. |

### Open decisions

| Input | Point (short quote) | Origin | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| I-L61 | "HTTPS … core or if-time. Deferred by the user." | user | **superseded by decision** | §4.7, §10.1 L843, Add G L246 | PM-L26 (2B): "«hvis tid», første punkt før endring/voucher". issues.md still lists it as open (U1). |
| I-L62 | "Database engine: SQLite or PostgreSQL … the reviewer must be able to run the app locally without own infrastructure" | coach / open item | partially captured | §12 Q4 L885; NFR-1 L756 | Q4 lists research coverage but drops the deciding constraint. NFR-1 together with FR-11 L271 ("same kind of data store … not a mock") leaves an unstated tension if PostgreSQL is chosen. See Gap 3. |
| I-L63 | "Whether the schema carries a sauna per seat from day one, so whole-sauna booking later is an extension and not a rewrite" | user question (SL997) | captured | §12 Q5 L886; Add A L19-23; PRD L31 ("without rewrites") | Recommendation (Sauna reference on Blocks and Whole-sauna bookings, not per Seat) carried, and left open for the architecture. |
| I-L64 | "Backcasting from 15.12 was not run; the build order has not been tested backwards" | coach / direction | partially captured | §10.1 L851, §12 Q6 L887 | Q6 narrows it to the order of If-time items 3-6. The brainstorm concern covered the whole build order, including whether the Core fits. No owner or deadline. See Gap 6. |

---

## Table B: brainstorm .memlog.md

Lines that repeat an intent point refer to Table A.

| Input | Point (short quote) | Origin | Status | PRD / addendum location | Note |
|---|---|---|---|---|---|
| M-L9 | "lærerens forslag: v1 = suksesskriterium 1-4 + adminverktøy, gavekort/dørkoder til trinn 2" | source (teacher) | captured | §10.1 NOTE L853 | The PRD explains why the Core is narrower and why Vouchers stay in v1. |
| M-L10 | Style and technique batch | process | n/a | — | |
| M-L11 | technique started | process | n/a | — | |
| M-L12 | "Den ene funksjonen: booke enkeltplasser" | user | captured | §10.1 L832; PM-L7 | |
| M-L13 | "seedes via skript eller konfigfil … admin starter som skrivebeskyttet bookingliste" | coach | captured | §4.4 L298 ("read-only list") | = I-L24 (b). |
| M-L14 | "tidsvinduer, kapasitet og priser i databasen; gjestens navn; simulert betaling; bekreftelse … på epost" | user | partially captured | §4.4, NFR-4, FR-5, FR-6, FR-8 | "i databasen" not carried (= I-L24 (a), Gap 2). |
| M-L15 | "utboks-tabell … uten SMTP; gjest = bare navn + epost, ingen konto; samtidighetstest for siste plass hører til kjernen" | coach | captured | FR-8, FR-17, NFR-1 L756, FR-11 (Core) | |
| M-L16 | "Gjestenavn er delen som kan gjøres aller enklest/nesten falsk" | user | captured | FR-5 L207 | |
| M-L17 | "Gjestenavn = ett fritekstfelt (kun lengdegrense + serversjekk) ; 'min booking' … bookingreferanse + epost" | coach | captured (name) / superseded by decision (lookup) | FR-5 L207, FR-18 L344; §4.10 | Lookup: BM-L126. |
| M-L18 | **"Databasetabellene kan ikke være falske, uansett tidspress"** | **user** | **partially captured** (missing as a requirement) | FR-10 L263 (store-level refusal, Core); FR-11 L271 (no mock) | No requirement that Windows, Capacity, prices, Bookings and the Outbox are stored rows that survive a restart. An in-memory store could pass several Core FRs. Gap 2. |
| M-L19 | "la databasen selv håndheve regler … databasevalg … tas tidlig, i uke 1" | coach | partially captured | §4.3 L254, FR-10; Q4 L885 | No week-1 timing; run-locally constraint not linked (Gap 3). |
| M-L20 | "aldri to bookinger på den siste plassen" | user | captured | FR-11 | |
| M-L21 | "kjernen kan booke atomært i én transaksjon uten 10-minutters hold" | coach | captured | §4.2 L199 | Confirmed by M-L22. |
| M-L22 | "(decision by user) 10-minutters hold utsettes … booker atomært i én transaksjon" | user | captured | §4.2 L199, §4.11, Add G L241 | |
| M-L23 | technique started | process | n/a | — | |
| M-L24 | "to andre fag med eksamener konkurrerer om tiden" | user | captured | §8.2 L810 | The mitigation (build windows around the exams) is only in Add I L278. |
| M-L25 | "tokens/kvote går tom" | user | captured | §8.2 L811 | |
| M-L26 | "Walking skeleton først … hold hver story liten … siste uke til buffer/README/test" | coach | captured (addendum); freeze untagged | Add I L275, L280; §8.2 L813 | = I-L46, I-L49. |
| M-L27 | "Eksamensdatoer … 16.11.2026 og 08.12.2026" | user | captured | §8.2 L810 | |
| M-L28 | "Tre byggevinduer … planlegging … må komprimeres i første vindu" | coach | captured (addendum) | Add I L278 | |
| M-L29 | "(decision by user) Planlegging (PRD + arkitektur) 7-8 dager av første 12" | user | captured | §8.2 L812 | |
| M-L30 | "PRD avledet fra briefen og avgrenset til kjernen, arkitektur bare beslutninger som må være konsistente …, epics/stories kun for kjernen; mål: kode kan starte ca. dag 8" | coach | partially captured: PRD part superseded by decision (PM-L13, PM-L15); architecture and epics part **missing** | — | = I-L44. Gap 1. |
| M-L31 | "frontend og design tar lengre tid enn planlagt" | user | captured (as a constraint) | §8.2 L811 | Gap 5. |
| M-L32 | "testing blir omfattende" | user | captured | §8.2 L811; NFR-6; SM-C1 | |
| M-L33 | "ett enkelt stilark … mobil først, ingen eget designsystem; … dybde på invariant …; tester skrives i hver story" | coach | partially captured | §4.6, FR-22, NFR-6 | Mobile first superseded (SL994); the rest is captured but untagged. = I-L56, I-L57, I-L47 (a). |
| M-L34 | "Minste gjestflyt … velg dato, antall plasser, tidsrom, book/betal" | user | captured, extended | UJ-1; PM-L31 | The review step was added. |
| M-L35 | "Én bookingside + én bekreftelsesside; … innebygd datovelger …; navn/epost i samme skjema som betal-knappen; admin = skrivebeskyttet bookingliste" | coach | partially captured / **contradicted** | §7 L781, FR-2, FR-3, FR-5, §4.4 | Separate Details-and-review page; native date input not named. Gap 5. |
| M-L36 | "Admin i kjernen: enkel bookingliste, innlogging med passord" | user | captured | FR-15, FR-16 | |
| M-L37 | "Én seedet adminkonto (påloggingsinfo i README), hashet passord, sesjonscookie; rollestyringen dekkes av en test …" | coach | captured | FR-15, FR-19, FR-20, DR-2 | |
| M-L38 | "HTTPS: kjerne eller hvis tid? Besluttes senere" | user | superseded by decision | §4.7 | PM-L26. |
| M-L39 | technique started | process | n/a | — | |
| M-L40 | "Tokenbegrensningen kan snus til en fordel" | user | captured | DR-1 L798 | |
| M-L41 | "Tokenbudsjett som metode: små stories med presise akseptkriterier hentet fra briefen …, budsjett per story logget i sesjonsloggen som bevis på KI-styring (30 % prosess), enkle/mekaniske oppgaver på lavere innsats" | coach | partially captured, untagged | DR-1 L798; Add I L280-281 | = I-L55. Gap 4. |
| M-L42 | "Constraint Mapping delvis kjørt; Backcasting ikke kjørt" | user (direction) | captured | §10.1 L851, Q6 | Gap 6 (narrowed scope). |
| M-L43 | Synthesis: MVP, If time, order, open items | synthesis | captured, with logged changes | §4.1-4.6, §10, §12, Add I | Changes since: HTTPS is If time 1 (PM-L26); refund dropped (BM-L125); My booking is resend-only (BM-L126); §4.13 before Step 2 (SL994); laptop first (SL994). |
| M-L44 | "(decision by user) Hvis-tid-rekkefølge: avbestilling før hel badstue" | user | captured | §10.1 L844 | |

---

## Coach proposals the PRD states as decided without a tag

| Proposal (input) | PRD location | Conflicting label elsewhere |
|---|---|---|
| Tests inside each story as part of "done"; depth/breadth split (I-L47, I-L57) | NFR-6 L761 | Add I L271 "Lisa has not confirmed it"; brief addendum L186-187 "proposal" |
| Freeze 9-15 December (I-L49) | §8.2 L813 | Add I L271, L277; brief addendum L186 "Build order (proposal)" |
| Token budget per story in the session log (I-L55) | DR-1 L798 | Add I L280; brief addendum L187 "Risk handling (proposal, tokens partly decided)" |
| No design system (I-L56) | §4.6 L388 | brief addendum L187 |

Coach proposals adopted through a logged decision, so they are not flagged: seed data with no Core admin screens (brief.md L52, BM-L124), one stylesheet (brief SC10, brief.md L99), the Outbox (PM-L25), the atomic transaction (M-L22), no guest account (BM-L67).

## User-originated points the PRD dropped or weakened

| User point | What the PRD has | Gap |
|---|---|---|
| "Databasetabellene kan ikke være falske" (M-L18); windows, capacity and prices "in the database" (I-L24, M-L14) | "seed data" only; never says the data is stored or persists | Gap 2 |
| "Frontend/design … likeliest overrun" (I-L17, M-L31) | Stated as a constraint, but the Core adds a review page, nearest-Window suggestions and "Before you come" | Gap 5 |
| "Tokens … real limit" (I-L16, M-L25), together with the token-thrift proposal it motivated (M-L30) | Stated as a constraint; no Core-first scoping for downstream planning | Gap 1 |
| Backcasting not run (M-L42) | Narrowed to the order of If-time items 3-6 | Gap 6 |

No user decision is contradicted by the PRD without a logged decision.

---

## Gaps that matter, ranked

### Gap 1 (high): no Core-first scoping for the downstream workflows
**Where:** PRD §0 L13-23, §7 L791, §10.1; Add I L270-282.
**Input:** I-L44 (b, c), I-L46, M-L30 (coach), driven by the user-named token risk (I-L16, M-L25).
**Problem:** the PRD is the chain top for UX, architecture and epics (PM-L16) and specifies every phase at the same depth: 51 FRs, of which 34 are outside the Core. Nothing tells the architecture to limit itself to the decisions that must be consistent, or tells the epics workflow to write Core stories first, starting with a walking skeleton. §7 L791 asks UX to sketch the blocking calendar (If time 7) first. That advice is the teacher's (2026-10-06) and predates the brainstorm. Lisa's decision to write a thorough PRD (PM-L13, PM-L15) supersedes "PRD limited to MVP" only for the PRD itself.
**Fix:** add a short "Downstream use" paragraph to §0 or §10.1:
- architecture decides the engine, the booking transaction and the API shape, plus only the If-time hooks the Core schema must not block (one capacity function; a Sauna reference on Blocks and Whole-sauna bookings, Add A L19-23);
- epics and stories cover §4.1-4.6 first, with a walking-skeleton story first; If-time epics are written after "Core done" (L840);
- UX sketches the Core booking flow first, and the blocking calendar when §4.13 is planned.

Tag it `[ASSUMPTION: brainstorm proposal]`, or confirm it with Lisa and log it in .memlog.md.

### Gap 2 (high): the user's "database tables cannot be fake" is not a requirement
**Where:** §4.4 L298, NFR-4 L759, FR-10 L258-263.
**Input:** M-L18 (user), I-L24 (a) and M-L14 (user); brief.md L52 says "kept in the database".
**Problem:** the PRD says only that Windows, Capacity and prices "come from seed data". It never requires that they, or the Bookings and the Outbox, are stored in the data store and survive a restart. A config file read at run time, or an in-memory store, would satisfy most Core FRs.
**Fix:** add a Core consequence, for example under FR-10 or as NFR-4a: "Windows, Capacity, prices, Bookings and Outbox emails are stored in the platform's data store, which a seed script loads. The platform reads them only from there. After a backend restart, the booking list and Seats left are unchanged." Cite M-L18.

### Gap 3 (medium-high): the database-engine question lost its deciding constraint and its timing
**Where:** §12 Q4 L885; NFR-1 L756; FR-11 L271; NFR-6 L761.
**Input:** I-L45, I-L62, M-L19 (coach; constraint from the user's examiner requirement).
**Problem:** Q4 names only research coverage. It omits the constraint the brainstorm made decisive: the examiner must run the app locally without infrastructure of their own. It also omits the timing ("i uke 1", first in the build order). NFR-1 forbids infrastructure, while FR-11 and NFR-6 require race tests against "the same kind of data store", so a PostgreSQL choice must explain how NFR-1 still holds. The PRD does not surface this.
**Fix:** rewrite Q4: "Decide first in the architecture, before any story. The deciding constraint is NFR-1 (README only, no infrastructure of the examiner's own), weighed against research coverage (PostgreSQL for concurrency; SQLite `BEGIN IMMEDIATE` from the capacity research). If PostgreSQL is chosen, NFR-1 must state how it is provided."

### Gap 4 (medium): coach proposals are stated as decided, and addendum I contradicts them
**Where:** NFR-6 L761, §8.2 L813, DR-1 L798, §4.6 L388, compared with Add I L271.
**Input:** I-L47 (a), I-L49, I-L55 (b), I-L56 (d), I-L57; M-L26, M-L33, M-L41 (coach).
**Problem:** PRD §0 L23 promises that unconfirmed inferences are tagged. These are untagged in the PRD, while Add I says "Lisa has not confirmed it" and the brief addendum labels them proposals. The reason for the token budget (it counts towards the 30 % process part of the assessment) is also dropped.
**Fix:** ask Lisa. If she confirms, log one PM decision line and delete "Lisa has not confirmed it" from Add I. If not, tag each item `[ASSUMPTION: brainstorm proposal, 2026-10-27]` and add them to §13. Add the 30 % rationale to DR-1 either way.

### Gap 5 (medium): Core frontend grew past the minimal flow that mitigated the frontend risk
**Where:** FR-5 L203-214 (separate review page, back-navigation keeps input), FR-3 L183 and UJ-1 L64 (nearest Windows across days), FR-1 L166 ("Before you come"), §7 L781, FR-2 L174.
**Input:** I-L25 (b, c), M-L35 (coach), addressing I-L17 and M-L31 (user risk).
**Problem:** the brainstorm proposed one booking page plus one confirmation page, the browser's date picker, and name and email in the same form as Pay. The PRD adds a third page, a cross-day suggestion feature and extra content. No memlog line decides the separate page or the suggestions. PM-L32 requires the pre-purchase information and the "Pay NOK …" button, which can sit on one page.
**Fix:**
- let FR-5 allow details, the pre-purchase information, the terms checkbox and "Pay NOK …" on the same page as the Window choice (the § 8 k and § 16 consequences stay testable);
- state that the browser's native date input satisfies FR-2;
- tag the nearest-Window suggestion `[ASSUMPTION]` or move it to If time;
- or log Lisa's decision if she wants the extra page.

### Gap 6 (low-medium): the backcasting gap was narrowed
**Where:** §10.1 L851, §12 Q6 L887.
**Input:** I-L64, M-L42.
**Problem:** the PRD limits "backcasting not run" to the order of If-time items 3-6. The brainstorm's concern was the whole build order: whether the skeleton and the core rule fit 27.10 to about 8.11 once planning takes to about day 8, and whether the Core is done by about 1.12.
**Fix:** broaden Q6: "Run backcasting from 15.12 over the Core and If-time items 1-2 before sprint planning. Owner: Lisa."

### Gap 7 (low): decisions applied without a memlog line
**Where:** PRD L25 and §10.1 L849 (both say "decided"); Add G L240.
**Input:** I-L56 (c), I-L40.
**Problem:** "laptop first, mobile last in Step 2" and "§4.13 rest of v1 before Step 2" are Lisa's decisions of 2026-10-29. They are recorded only in SL994 (13:39, 13:54, 14:03), which notes ".memlog.md er ikke oppdatert". BM-L124 still says the rest of v1 comes after Step 2, so a reader of the memlogs sees the opposite of the PRD.
**Fix:** add one PRD .memlog decision line citing SL994 for both, and consider a correcting line in the brief memlog.

### Gap 8 (low): attribution slips in the addendum
**Where:** Add G L248; Add I L271.
**Problem:** Add G dates "Administrator screens in the Core: replaced by seed data" to 2026-10-27, but on that date it was a coach proposal. It was adopted on 2026-10-29 through the brief (brief.md L52, BM-L124). Add I labels the whole build order "Lisa has not confirmed it", which also covers user decisions such as the Administrator login and list in the Core (I-L48, M-L36).
**Fix:** re-date Add G L248 to 2026-10-29 (via the brief). In Add I, split decided items (constraints, admin in Core, planning 7-8 days) from proposals, as the brief addendum L182-187 does.

### Watch item W1 (no change needed now)
FR-10 L263 ends the store-level guarantee at the Core. That is honest and matches Add A L16, but the user's rule "the database itself enforces it" (M-L19, M-L20) should survive into If time. The architecture should state that the If-time check runs inside the data store's serialised transaction, never in an in-process lock, in line with §4.3 L254 ("does not rest on application code alone").

## Upkeep outside the PRD (not PRD gaps)
- **U1:** `.logs/lisa-larsen/issues.md` still lists "HTTPS: kjerne eller «hvis tid»; beslutning utsatt" as open, although PM-L26 decided it. Add H L263-266 lists other stale issues.md entries but not this one.
- **U2:** BM-L124 still orders the rest of v1 after Step 2 (see Gap 7).
