# Downstream Readiness Review — Saunalöyly Booking Platform PRD

*Reviewed `prd.md` (draft, updated 2026-10-30) and `addendum.md`, reading as three cold readers who hold only those two files. `P L…` = prd.md, `Add L…` = addendum.md. "Already queued" = on the last `(assumption)` line of `.memlog.md` (L37). "Touches a decided item" = the finding concerns a `(decision)`/`(change)` line or a "(decided)" statement in the PRD.*

## Verdict
All three readers can start on the Core, and none is blocked on the capacity core itself. The biggest blocker is a clash between two decided items: FR-23 promises WCAG 2.2 AA on every Core page, which includes 1.4.10 Reflow down to 320 CSS px, while the decided order puts the mobile layout last (FR-51). Close behind, the simulated-email model leaves If-time Guests unable to read the emails their flows depend on, and If time 5 quietly makes the instant Core payment asynchronous.

## Readiness per reader
- **Architect — ready with guesses —** the stack, the Core capacity core and the test strategy can start, but the database engine (NFR-1's "infrastructure of its own"), the reach of the store-level refusal beyond the Core (FR-10), the payment model once Holds exist (FR-36) and how far the Outbox and tokens are trusted must be settled before the Core schema is fixed.
- **UX designer — ready with guesses —** look, tone, palette, type, IA and most Core content are given, but the layout strategy is stuck between WCAG 2.2 AA reflow and mobile-last, and the confirmation page's lifecycle, which emails a Guest can see, and most expired and already-changed states would have to be invented.
- **Story writer — ready with guesses —** Core epics cut cleanly from §4.1–§4.6 with mostly testable consequences, but the seed-data story waits on Q3, several Core and If-time-3 consequences only become testable in later phases, and If time 5 reworks the Core payment story without saying so.

## Findings

### Critical

- **[DS-1] [UX designer, Story writer]** Core WCAG 2.2 AA requires a reflowing layout, and the decided order defers that to Step 2. Locations:
  - FR-23 P L420, "Every Core page meets WCAG 2.2 level AA"
  - §4.6 P L407, "The Core layout targets a laptop screen; mobile comes last in Step 2"
  - FR-22 P L415, "without horizontal scrolling at 1366×768 and 1920×1080"
  - FR-51 P L777, "from 360 px wide upward, and FR-23 holds at every width"

  WCAG 2.2 AA includes 1.4.10 Reflow. Content must work at 320 CSS px wide (a 1280 px window at 400 % zoom) without scrolling in two directions, except for data tables. So FR-23 already asks, in the Core, for a single-column layout narrower than the 360 px that FR-51 puts last in Step 2.

  The UX designer must pick one reading, and either one breaks a decided item. A laptop-only layout makes FR-23 false, and the automated check (P L423) will not catch it, because automated checkers generally do not test reflow. A reflowing Core layout pulls mobile work ahead of the decided "mobile layout last" (P L27). The story writer cannot write the Core layout AC or the FR-51 AC until this is settled. Touches two decided items: WCAG 2.2 AA as the target (memlog L32) and mobile last (P L27, brief SC10).

  *Fix:* ask Lisa to choose:
  - (a) The Core layout reflows to one column down to 320 CSS px. FR-51 then covers only mobile polish: navigation, touch, phone testing.
  - (b) FR-23 says "WCAG 2.2 AA except 1.4.10 Reflow until FR-51", and DR-2 reports reflow as not delivered until then.
  - (c) The Core targets WCAG 2.0 AA, the legal minimum (Add L135), which has no reflow criterion. 1.4.4 Resize text still applies, so pages must work at 200 % zoom (683 CSS px on a 1366 px laptop). 2.2 AA starts with FR-51.

  Whichever is chosen, add a manual 400 % zoom check to FR-23.

### High

- **[DS-2] [Architect]** NFR-1's "infrastructure of its own" can be read two ways, and the database engine depends on which. Locations:
  - NFR-1 P L795, "It needs no keys, paid accounts, external services or infrastructure of its own"
  - Q4 P L946, "The engine must run locally without infrastructure of its own (NFR-1). The concurrency research covers PostgreSQL; the capacity research checked SQLite's transaction rules"
  - Add L8–L11

  The engine is the first architecture decision ("made before the first story"). It fixes the capacity mechanism (a conditional update under Read Committed, or `BEGIN IMMEDIATE`), the retry codes of FR-14, and what the parallel race tests of FR-11 and NFR-6 prove.
  - If a local PostgreSQL server or a container counts as "infrastructure of its own", the main research mechanism is out, and SQLite is the only engine that fits.
  - If it does not count, the README must have the examiner install a database server.

  A wrong choice means rebuilding the capacity core, or failing SM-4 on the examiner's machine. Also, SQLite allows only one writer at a time, so its race tests prove less than PostgreSQL's would.

  *Fix:* ask Lisa what the examiner may need beyond the clone:
  - (a) only Python with uv and Node.js, so an embedded engine (add "no database server, container or service" to NFR-1);
  - (b) a locally installed PostgreSQL, with README steps.

  The architecture then records what the race tests prove for that engine.

- **[DS-3] [Architect]** The store-level refusal is required only "In the Core", and nothing says whether it must survive Whole-sauna bookings, Blocks and Holds. Locations:
  - §4.3 P L268, "In the Core, the data store itself refuses a write that would exceed it, as the brief requires (decided 2026-10-27)"
  - FR-10 P L277, "How the same guarantee is enforced once Whole-sauna bookings and Blocks change Seat capacity is an architecture decision"
  - Add L17–L18, "Once Whole-sauna bookings and Blocks change Seat capacity, the research found no store-level constraint. The check then runs inside one serialised transaction per Window"

  The architect fixes the Core schema now (§10.3 P L915), and the PRD's own bet is growth "without rewrites" (P L33). There are two readings:
  - **Reading 1:** the guarantee holds for all of v1. The Core schema then needs a stored Seat capacity per Window, updated in the same transaction as Whole-sauna bookings, Blocks and marks, and constrained by the store. Holds cannot be part of that stored count, because they stop counting when time runs out, whether or not any cleanup has run (P L571).
  - **Reading 2:** the guarantee is Core-only, and from §4.9 one serialised transaction per Window replaces it.

  Under reading 2, the Core's CHECK counter (Add L17) is throwaway work. Under reading 1, it is the foundation. Touches a decided item (2026-10-27).

  *Fix:* ask Lisa: "Must the data store itself refuse over-capacity writes in every v1 phase, or only in the Core?" Rewrite FR-10's second consequence to match, and say whether held Seats fall inside or outside the store-level check.

- **[DS-4] [Architect, Story writer]** Holds (If time 5) make the instant Core payment asynchronous without saying so. Locations:
  - §4.2 P L212, "Checking Seats left, recording the Simulated payment and creating the Booking happen in one atomic step. The Simulated payment is instant"
  - FR-11 P L284, the losing Guest "is not charged"
  - FR-36 P L591, "no Booking is created, the payment is refunded (simulated)"
  - FR-36 P L592, "if charged, a simulated refund"
  - FR-36 P L593, "Repeated or out-of-order payment confirmations never create two Bookings or two refunds. A test switch can make the Simulated payment confirm late, twice or out of order"
  - Add L39–L40, "deduplicate them by event ID … The confirmation handler re-checks the Hold"

  "Charge, then refund" and confirmations that arrive twice or out of order only make sense if payment becomes a separate step with its own confirmation event. That is a different payment adapter from the Core's. It also weakens the Core promise that the race loser "is not charged" (FR-11, CT-2): in a late-payment race, the loser is charged and then refunded.

  §10.3 asks the architecture to decide "Holds stored as data" now, but not the payment model that Holds imply. The story writer would build the Core payment story synchronously, then find a hidden rework of FR-6 and FR-11 in the If-time 5 epic.

  *Fix:* add to §4.11: "From §4.11 on, pressing Pay starts a Simulated payment. A separate confirmation, which may arrive late, twice or out of order, creates the Booking. FR-11's 'is not charged' then reads 'is not charged, or is refunded at once'." Add the payment adapter's confirmation model to the §10.3 list, or ask Lisa whether If time 5 may rework FR-6.

- **[DS-5] [Architect]** The Outbox stores what FR-25 says is never stored. Locations:
  - FR-25 P L453, "Only a hash of it is stored"
  - FR-17 P L345, "full body, including any links"
  - NFR-10 P L804, the Outbox is "stored in the data store"
  - FR-21 P L404, the security statement says "Manage-link tokens stored only as hashes"
  - DR-2 P L843, "where to find a sample Manage link in the Outbox"

  Every Manage link in the Outbox carries its token in plain text, in the same data store. So do Voucher codes (FR-27 P L476), Gift-card codes and Door codes. Three consequences:
  - A test that checks "no plaintext token in the store" fails.
  - The README's security statement to the examiner is false.
  - Any Administrator can open and change any Guest's Booking from the Outbox. DR-2 relies on this, but FR-20 (P L386, "can be opened only with its Manage link … or by the guest account") does not say so.

  The architect must choose how far the Outbox is trusted, with no guidance. Hiding secrets in the Outbox breaks the examiner path in DR-2. Keeping them breaks FR-25 as written. Touches two decided items: the token is stored hashed (memlog L32), and the Outbox is for Administrators only (Outbox 1A, memlog L25).

  *Fix:* add to the Outbox Glossary entry (P L150) or to FR-17: "The Outbox stands in for the Guests' mailboxes, so the booking store's security rules do not cover it. It keeps each email as sent, including Manage links, Voucher codes and Door codes. An Administrator who opens a link from it acts as that Guest." Reword FR-25 and FR-21 to "the booking store keeps only a hash of the token".

- **[DS-6] [Architect, UX designer]** The Core confirmation page has no access rule and no lifetime. Locations:
  - FR-8 P L257, "The confirmation page shows that email as sent. The Guest sees no other email"
  - FR-8 P L259, "The Booking reference alone opens nothing (FR-20)"
  - FR-17 P L347, "A Guest sees only their own confirmation email, on the confirmation page"
  - UJ-1 P L67, "She has a reference and an email she can keep"
  - SM-2 P L926, the Core tests include "RB-4 for guessed Booking references"

  The page shows personal data and the full email, but it cannot be opened by the Booking reference. The architect must invent the access mechanism: either the page belongs to the browser session that paid, or a one-time token in the URL opens it. The UX designer must invent what reload, Back, a bookmark and a later visit show.

  In the Core there is no Manage link, so once the page is closed, the Guest can never see the Booking or the email again. UJ-1's "an email she can keep" cannot happen in the simulation unless the page tells the Guest to print or save it. The obvious build, `/bookings/{reference}`, breaks FR-8 and FR-20. SM-2's Core RB-4 test also has nothing to probe, because no Core request accepts a reference.

  *Fix:* add to FR-8: "The confirmation page opens only for the browser that paid [or: through a confirmation token with at least 128 random bits]. It can be reloaded until [the session ends / the Window ends]. After that, it shows a neutral 'This page is no longer available'. The page tells the Guest to keep the reference, and says the email is shown here because emails are simulated." Name the route that the Core RB-4 test probes.

- **[DS-7] [UX designer, Story writer]** Apart from the confirmation email, a Guest cannot read any email their flows depend on. Locations:
  - Glossary P L150, "Only Administrators can list it"
  - FR-8 P L257, "The Guest sees no other email"
  - UJ-4 P L91–L92, a Voucher "arrives by email … Later she uses the Voucher to pay for another visit"
  - FR-27 P L476, "The Voucher is emailed (Outbox) with its code"
  - FR-26 P L465, the split-off Booking's Manage link is "emailed at once"
  - FR-34 P L566, "a new Manage link is emailed (Outbox)"
  - FR-42 P L680, "emailed an apology with a link to a remedy page"

  In the simulation, four things land only in the Administrator-only Outbox: the Voucher code, the second Manage link after a partial move, the resent link and the remedy link. So a Guest cannot complete UJ-4, FR-34 or FR-42 alone, and the story writer cannot write a Guest-side AC for them. The UX designer must guess whether the Manage page may show the Voucher email or the new link; a strict reading of FR-17's "only their own confirmation email" forbids it. Touches a decided item (Outbox 1A, memlog L25: the Guest sees only their own email, on the confirmation page).

  *Fix:* ask Lisa to choose:
  - (a) Generalise FR-8 and FR-17: every page that triggers an email shows that email as sent. For example, the Manage page shows the Voucher email or the new-link email after a Change. Emails with no triggering page (resend, remedy, Door codes, account emails) are reached only through the Administrator's Outbox, and the README explains this. Resend must stay Outbox-only, because showing its email would reveal a match (FR-34 P L565).
  - (b) Keep FR-17 strict, and rewrite UJ-4 and the If-time ACs so that the examiner reads the Outbox in place of the Guest.

- **[DS-8] [Architect, UX designer, Story writer]** What happens to a Booking after a Change is undefined. Locations:
  - §4.8 P L445, "A Change is a cancellation plus a new booking, done as one atomic step"
  - FR-26 P L465, "Moving all Seats moves the Booking and keeps its reference"
  - FR-16 P L339, "active, changed or cancelled … the cause (Guest, Block or Overbooking fallback)"
  - FR-26 P L468, "the Administrator's list shows the Change"
  - FR-40 P L657, "'latest' means most recently created"

  One sentence says a Change cancels the Booking and creates a new one. The next says the same Booking moves and keeps its reference. The architect must choose between one Booking that changes in place, with a log of its Changes, and a chain of Booking records linked by reference. That choice fixes the reference, token and Outbox model now (§10.3). Four things depend on it and are also undefined:
  - what "changed" means, and whether a changed Booking counts in Seats booked;
  - what a Booking becomes when all its Seats are given up for a Voucher: cancelled with cause Guest, or changed with 0 Seats;
  - where a fully moved Booking appears in the Administrator's list: the old Window, the new Window, or both;
  - which timestamp decides "latest Booking loses" for a moved or split-off Booking (the original booking time or the move time). The same answer sets "time of booking" in FR-16 (P L335).

  This overlaps the rules reviewer on "latest"; the point here is the data model and the list UI.

  *Fix:* add a Booking status list to the Glossary, with its transitions. For example: active; cancelled, with cause and remedy; "changed" as a flag with a Change history. State in FR-26: "A move updates the Booking in place and records a Change. The old Window's list shows it as moved out." Say what giving up all Seats leaves behind, and ask Lisa which timestamp "latest" uses after a move.

- **[DS-9] [Architect, Story writer, UX designer]** Seed data has no schedule and no date rule. Locations:
  - §4.4 P L314, "Windows, Capacity and prices come from seed data"
  - FR-1 P L177, the site shows "opening hours and the Window schedule"
  - Q3 P L945, "Also open: opening hours, the Window schedule (including whether there is a changeover gap …) … Decide before the architecture seeds the data"
  - Glossary P L141, the Booking horizon is "4 weeks … counted from the moment of booking"
  - DR-2 P L843, "the seeded sample Bookings"
  - SM-4 P L930

  The Core has no screen for editing Windows, so the seed is the only source of Windows. Nothing says whether the seed holds fixed dates or creates Windows relative to the day it runs. A seed with fixed November 2026 dates leaves the examiner, who runs it later, with no date to book, so SM-4 fails. A seed that runs only once also stops offering Windows as the 4-week horizon rolls past it.

  There is also no schedule to seed from, and the examples imply different schedules: P L122 has back-to-back 15:00–16:30 and 16:30–18:00, while UJ-3 (P L84) leaves a gap from 19:30 to "20:00–21:30". The UX designer also needs the number of Windows per day, to lay out the Window list and the schedule on the landing page. The price-model part of Q3 is already queued; the schedule and the date rule are not.

  *Fix:* answer the schedule part of Q3: opening hours, Window start times, changeover gap. Add to §4.4 or NFR-10: "The seed creates Windows from a daily schedule for every day from the run date to at least the end of the Booking horizon, and puts the sample Bookings in the coming days. Windows are created again [at start-up / by a documented command], so the horizon is always covered." Align UJ-3's times with the schedule.

### Medium

- **[DS-10] [Story writer]** Some consequences of Core and If-time-3 FRs can only be tested in later phases. Examples:
  - FR-13 P L298, "Seed data or Administrator input". Administrator input arrives with §4.13.
  - FR-13 P L299, "expressed as a Block". Blocks arrive with §4.13.
  - FR-13 P L300, "a booking, cancellation or Whole-sauna booking in one Window never changes another". Cancellations and Whole-sauna bookings arrive with §4.8 and §4.9.
  - FR-29 P L500–L501, "not Blocked", "plus the Seats held once §4.11 exists", "An unreleased Whole-booking-only Sauna skips this test".
  - FR-29 P L511, the Whole-booking-only example (FR-41, §4.13).
  - FR-31 P L522 and P L535: the model-based test applies "Blocks, lifted Blocks, Whole-booking-only marks and releases" (§4.13).
  - FR-32 P L545, the C6 serialisation of Blocks and marks (§4.13).

  A story for FR-13 (Core), or for FR-29, FR-31 or FR-32 (If time 3), cannot pass these ACs when it is built, because the features they need do not exist yet. The story writer must split each FR by phase and remember to put the deferred ACs back into epics 5 and 7. The model-based test must also grow with each epic.

  *Fix:* tag each such consequence with the phase where it becomes testable, for example "[with §4.13]", as FR-20 already does. Add to §10.3: "Each epic extends the model-based test (FR-31) and the C-group tests (FR-32) with the actions it adds."

- **[DS-11] [Story writer]** What each If-time feature changes in earlier pages is spread across "once §4.x exists" clauses. Locations:
  - P L158, the Private sauna entry
  - P L178, the price per Sauna
  - P L209, FR-4's copy
  - P L225, the terms, "Until §4.8 is built"
  - P L258, the Manage link in the confirmation
  - P L339, the list statuses
  - P L375 and P L393, password rules and stored data for guest accounts
  - P L404, the security statement
  - P L843, the README
  - P L134, Seats held

  No If-time feature lists the earlier pages and FRs it must touch. The epic for §4.8, for example, could miss updates to the terms (FR-5), the confirmation email (FR-8), the list (FR-16), the privacy notice (FR-21) and the README (DR-2).

  One case is not covered at all: Bookings made before §4.8. They have no Manage link and were sold under terms that ruled out online Changes (P L225, P L258). Once resend (§4.10) can issue a link for them, they become changeable.

  *Fix:* add a "Changes to earlier features" line to each of §4.7–§4.13. Add one sentence on Bookings made before §4.8, for example "they stay unchangeable; the seed is reset when §4.8 ships".

- **[DS-12] [UX designer, Story writer]** If-time pages have no accessibility or layout requirement until Step 2. Locations:
  - FR-22 P L412, "every Core page on a laptop screen"
  - FR-23 P L420, "Every Core page meets WCAG 2.2 level AA"
  - FR-51 P L777, "FR-23 holds at every width"

  §4.7–§4.13 add Manage, Private sauna, Voucher, resend, account and Administrator pages. FR-22 and FR-23 cover only Core pages, and only FR-51 (Step 2, last) brings every page under FR-23. The story writer cannot tell whether If-time stories carry FR-22 and FR-23 ACs, and the UX designer cannot tell whether the blocking calendar must meet them.

  *Fix:* change FR-22 and FR-23 from "every Core page" to "every page, from the phase in which it is built". Or say explicitly that If-time pages are checked only at the freeze.

- **[DS-13] [UX designer]** It is unclear what the Guest is told about the 10-minute Hold, given the ban on countdowns. Locations:
  - FR-3 P L198, "No countdown, 'people viewing' count, padded number or other urgency cue appears"
  - NFR-9 P L803, "no countdown timers"
  - §4.11 P L571, "held for a fixed 10 minutes"
  - FR-35 P L579, "Held Seats are left out of other Guests' Seats left"
  - FR-35 P L584, "Expiry never discards what the Guest has entered"

  Honesty argues for telling the Guest that the Seats are held until a set time. The urgency ban argues against showing any time limit. Other Guests see held Seats vanish and may see them return, and nothing says whether "held by someone else, may free up" may be shown. Each choice changes the details page, the review page and the Window list.

  *Fix:* ask Lisa to choose:
  - (a) Show a fixed clock time ("We're holding 2 seats for you until 15:42"), with no ticking timer, and show held Seats to others as taken, with no comment.
  - (b) Say nothing about the Hold.

  Add the chosen rule to FR-35.

- **[DS-14] [Architect, UX designer]** It is undefined what a "test switch" is, and how visible the simulation is to visitors. Locations:
  - FR-7 P L242, "A test switch can force the Simulated payment to fail"
  - FR-14 P L308
  - FR-36 P L593
  - FR-35 P L583, "With cleanup switched off"
  - §1 P L35, "it does not pretend to be one"

  The architect must decide what a switch is: an environment or config setting, a per-request flag in tests, or an Administrator control. They must also decide whether the examiner can reach it in the running app. If a switch can be flipped through the API, any caller could force failures.

  The UX designer must decide two things:
  - whether the failed-payment state of FR-7 is ever visible outside tests;
  - whether pages and emails say that the payment, the emails and the Venue are simulated or fictional. A pay step with no card form may puzzle the examiner, and a fake card form is a choice the PRD does not make.

  Touches a decided item (a test switch for failed payment, memlog L32).

  *Fix:* define "test switch" once in §5, for example: "a setting read at start-up from a git-ignored local file, off by default, never changeable through the API". Ask Lisa:
  - (a) the website shows a plain "Simulated payment: no money moves" note at Pay and in emails;
  - (b) no notice.

- **[DS-15] [Architect, Story writer]** Idempotency covers payment only; repeated or stale Changes are not covered. Locations:
  - FR-6 P L236, "Submitting the same review twice (by double click, reload or retry) never creates two Bookings or two charges"
  - FR-25 P L458, "Any Change needs an explicit confirming action"
  - FR-32 P L543 and P L546, which cover only cancellations and races across Windows

  A double-submitted "Move 2 Seats" on a 4-Seat Booking would split it twice. A Change confirmed from an old browser tab acts on a state the Guest no longer sees. The UX designer has no "already changed" rule to design for.

  FR-6 has a gap of its own. "Reload" means the submission key must survive a page reload, and nothing defines "the same review". Two genuinely identical Bookings are allowed, so matching on content will not do.

  *Fix:* add to FR-25: "Replaying a confirmed Change never applies it twice. A Change confirmed against an outdated view of the Booking is refused, and the current state is shown." Add to FR-6: "A review carries one submission key, kept across reloads. A second submission with the same key returns the first result."

- **[DS-16] [Architect]** The PRD does not define token types or their lifetimes beyond the Manage link. Locations:
  - FR-25 P L454, "The link shows the Booking until its Window ends"
  - FR-42 P L681, "The remedy link works for 30 days, even after the Window has ended"
  - FR-26 P L465, the split-off Booking's "own … Manage link"
  - FR-25 P L456, a new link revokes the old one
  - Add L47, "swap the token for a short-lived session cookie and strip it from the URL"

  Because the remedy link outlives the Window, it is either a separate single-purpose token or a Manage link with a longer life. Core-era Bookings have no Manage link at all.

  The session that replaces the token has no stated lifetime, and the UX designer needs to know what a Guest sees when it expires in the middle of a Change. Nothing says whether an Administrator session and a Manage-link session can exist in the same browser, which DR-2's README path needs.

  *Fix:* add a short token table to §4.8 or addendum A. Columns: token, issued when, valid until, revoked by, what it opens. Rows: Manage link, split-off Manage link, remedy link, and the session after first load (with its lifetime).

- **[DS-17] [Architect, Story writer]** Time-triggered actions and the test clock are not stated. Locations:
  - FR-21 P L399, the retention purge, in the Core
  - FR-41 P L671, release "At the Release time"
  - FR-42 P L681, the default refund after 30 days
  - FR-35 P L583, optional Hold cleanup
  - FR-47 P L738, Send time, in Step 2
  - Q9 P L951, "using the data store's clock"

  The architect must decide which of these run as scheduled jobs and which are worked out when data is read. They must also decide whether the Core needs a scheduler at all, given that the 12-month purge is the only Core job.

  Many ACs depend on time: the Booking deadline, the horizon, the Cutoff, the 06:00 release, Hold expiry, Voucher expiry and the 30 days. No requirement says tests can set the clock, and Q9's "data store's clock" makes that harder.

  *Fix:* add to NFR-3 or NFR-6: "Every time rule reads one platform clock that tests can set." List the time-triggered actions per phase, marking each "scheduled" or "evaluated on read", or explicitly leave that choice to the architecture.

- **[DS-18] [Architect, Story writer]** Money edge cases in Changes have no rule. Locations:
  - FR-28 P L484–L485, a Voucher pays "all or part of a Booking" and "is never paid out in money"
  - FR-33 P L552, "the Guest chooses a Simulated refund or a Voucher"
  - FR-42 P L680, refund or Voucher
  - FR-33 P L553, a move may go to "another one that is available"
  - FR-38 P L619, "the price per Sauna"

  Two cases are open:
  - A Booking paid partly by Voucher is cancelled by the Venue, and the Guest picks a refund. Either the Voucher part is paid out in money, against FR-28, or each payment method must be refunded separately.
  - A Whole-sauna booking moves to a Sauna with another price. Nothing says whether to charge the difference, refund it, or refuse the move.

  Neither case is part of the queued price-model item.

  *Fix:* add to FR-28: "A refund returns the Voucher-paid part as a Voucher with its original expiry, and the rest as a Simulated refund." Add to FR-33: "A move to a Sauna with a different price is [refused / charged or refunded the difference]."

- **[DS-19] [UX designer, Architect, Story writer]** There is no list of emails and no email format. Emails mentioned today:
  - FR-8 P L249–L256, the confirmation's content
  - FR-27 P L476, Voucher
  - FR-26 P L465, the split-off Booking
  - FR-34 P L566, resend
  - FR-42 P L680 and P L682, two remedy emails

  Nothing covers a full move, a cancelled or moved Whole-sauna booking (FR-33 P L552), or guest sign-up (FR-37). Add L118 notes that "§ 18: the confirmation must be given on a durable medium".

  The UX designer must write every email, the architect must template them, and the story writer must tie each to a story. But the PRD names an email only where an FR happens to mention one. Two things are guesses: whether a Change is confirmed by email (the durable-medium note suggests yes), and whether emails are plain text or HTML ("exactly as it was sent", P L66).

  *Fix:* add an email table to §7 with event, recipient, required content and phase. State "plain text" or "simple HTML in the §6 look".

- **[DS-20] [UX designer]** Many states are left for the UX designer to invent.

  Core:
  - the Booking deadline passes between choosing a Window and paying (FR-18 P L360);
  - a Window that has started but can still be booked for 5 more minutes (Glossary P L142);
  - the last day of the horizon, where later Windows cannot be booked yet (P L141);
  - no Window with room anywhere in the horizon (FR-3 P L196);
  - sign-in "slowed or temporarily refused" (FR-15 P L325): which one, and what the message says;
  - an anonymous visitor at an Administrator address (UJ-3 P L85, "is refused");
  - a date with no Bookings in the list;
  - Pay in progress.

  If time:
  - the Manage page after all Seats became a Voucher, after a Venue cancellation, after the Cutoff, and after the Window ends (FR-25 P L455, "same response as a link that never existed");
  - a Voucher that covers the whole total, where "Pay NOK 0" (FR-6 P L233) needs other wording;
  - resend when the rate limit is hit (FR-34 P L565, P L567);
  - the remedy page after the choice, or after 30 days;
  - a Hold lost to another Guest (FR-35 P L580).

  FR-22's rule (say what happened and what to do next) covers tone, not behaviour.

  *Fix:* add a short list of Core states to §7, with the behaviour wherever it is a product decision. For example: "a Window can be booked until its deadline and is labelled 'Started 15:00'". Say that the rest is the UX designer's call under FR-22.

- **[DS-21] [UX designer]** The UX scope for this round is unclear. Locations:
  - §7 P L831, "sketches the booking flow and the Administrator booking list first, and the blocking calendar when §4.13 comes near"
  - §4.1 P L158, "The Private sauna entry appears only once §4.9 is built"
  - §7 P L823–L829, the If-time pages

  Nothing says whether DESIGN.md and EXPERIENCE.md cover the If-time 2–6 pages now (Manage booking, Private sauna, Voucher entry, Hold, accounts), or only the Core. If only the Core is designed, the landing page, the review page and the pay step may need redesign once the Private sauna entry, the Voucher field, the Hold notice and the sign-in choice arrive.

  *Fix:* add to §7 or §10.3: "This UX round designs every Core page in full, plus the places on Core pages where If-time features plug in, and the flows for §4.8–§4.12. The §4.13 screens come later."

- **[DS-22] [Story writer, Architect]** Some IDs cannot be looked up in prd.md and addendum.md. Locations:
  - FR-31 P L530, "Catalogue groups A and B hold"
  - SM-5 P L933, "Catalogue groups A to F pass … group C run as parallel tests"
  - §4.15 P L710, group H
  - §0 P L19 names only the research folder
  - FR-39 P L644, "With the defaults, SC1 to SC4 behave as this PRD describes, and so do SC5 and SC6 … (SC8)"
  - SM-5 P L933, "SC2, SC3, SC4 and SC8"
  - §11 P L918, "Success criteria SC1 to SC10 are the brief's"
  - §0 P L16, "The full rule tables … live there"

  Many catalogue cases are quoted inline, but "groups A to F pass" is an AC about cases the reader does not hold. SC2–SC4 and SC8 are never defined, and SC7 is never mentioned, so FR-39's last consequence cannot be tested as written. §0 also leaves open whether the brief addendum's rule tables still bind v1. Addendum K resolves the brief's test IDs well; the catalogue and the SC numbers have nothing like it.

  *Fix:* in §0, name the catalogue file (`.docs/planning-artifacts/research/technical-kapasitetsmodell-enkeltplasser-2026-10-28/research.md`) as a required input for architecture and stories. Say that for v1, prd.md overrides the brief addendum. Add a one-line SC1–SC10 table to §11. Rewrite FR-39's last consequence as "with the default Settings, the tests of §4.1–§4.12 pass unchanged".

- **[DS-23] [Architect, UX designer, Story writer]** Window administration (If time 7) does not cover Windows that already have Bookings. Locations:
  - FR-38 P L619, "create and edit Windows"
  - FR-38 P L622–L626, which cover only length, Capacity, Fill order, price and the horizon
  - FR-13 P L299, a Sauna out of use for part of a Window "is expressed as a Block"
  - FR-1 P L177, a "Window schedule"

  Nothing says whether the Administrator may change the times of a Window with Bookings, or delete one. Either would move or cancel Guests outside the D-rules.

  Windows can only be created one at a time, so a 4-week horizon means creating dozens of Windows a week. That is a UX problem, and it ties to the missing schedule in DS-9.

  *Fix:* add to FR-38: "Changing the times of a Window with active Bookings, or deleting it, is refused. Use a Block of every Sauna instead (D6)." Decide whether Windows are created from a recurring daily schedule.

- **[DS-24] [Architect, UX designer]** Guest accounts (If time 6) leave out the email step that the no-disclosure rule needs. Locations:
  - FR-37 P L605, "Sign-up does not reveal whether an email already has an account"
  - FR-37 P L604
  - FR-21 P L393, "For a Guest, the platform stores name and email only"

  If sign-up never reveals an existing account, it must reply "check your email" in both cases. That implies an email confirmation step the PRD does not specify, and under DS-7 a Guest could not read that email anyway.

  Three more gaps:
  - Guest accounts have no password reset; Administrators use a command (P L323).
  - FR-21's list of stored data is wrong once accounts store password hashes.
  - Nothing says whether a signed-in Guest may book under another email.

  *Fix:* add to FR-37: "Sign-up is confirmed through a link emailed to the address (Outbox). Password reset is [out of scope / by emailed link]. A signed-in Guest books with the account's email." Update FR-21 for guest accounts.

### Low

- **[DS-25] [Architect]** Q14 offers per-Sauna lock options that cannot meet FR-32. Locations:
  - Q14 P L956, "lock per Window, per Sauna, or through a queue per Sauna"
  - FR-32 P L538, "in the same Window are serialised"
  - Add L19, "the Window is the natural lock unit … This is still open"
  - §10.3 P L915, "the lock unit per Window"

  A Seat booking draws on every Sauna open for Seats, so a lock per Sauna cannot serialise a Window as FR-32 requires. §10.3's wording reads as if the Window has already been chosen as the lock unit.

  *Fix:* reword Q14 as "how FR-32's serialisation per Window is achieved: a row lock, a serialisable transaction, or a queue per Window".

- **[DS-26] [Architect]** Addendum A's Whole-sauna formula leaves out two FR-29 conditions. Locations:
  - Add L30–L33, whose "allowed only if all of these hold" list has only bookable whole, not Blocked or booked, and Room ahead
  - FR-29 P L499, the horizon and the Booking deadline
  - FR-29 P L502, "The Window has not started, or it has no Seat booking"

  An architect who builds the capacity function from the addendum would miss the rule for Windows that have started.

  *Fix:* add the two conditions to Add L30–L33, or point the list at FR-29.

- **[DS-27] [Architect]** Addendum B's F3 row contradicts FR-40. Already queued. Locations:
  - Add L75, "F3, a Window has started | No moves; the Overbooking fallback applies"
  - FR-40 P L662, "A Block in a Window that has started counts Seats again like any other Block"

  With derived Placement, "no moves" can only work if Placement is stored when the Window starts, so the answer also decides Q5. The F3 interpretation is already queued.

  *Fix:* once Lisa confirms, align addendum B with FR-40.

- **[DS-28] [Architect, UX designer]** Some requirements dictate implementation. Locations:
  - §4.6 P L407, "One stylesheet and no design system"
  - FR-22 P L416, "All styling comes from one stylesheet"
  - FR-51 P L774, "with the same stylesheet"
  - FR-35 P L583, "With cleanup switched off"
  - FR-2 P L187, "The date can be typed as well as picked", versus Add L198, "A short list of radio buttons beats a date picker"

  "One stylesheet" rules out the per-component styles of most JavaScript frameworks, which limits the architect's frontend choice. The UX designer may read "no design system" as "no tokens or component rules", which are what DESIGN.md is for. FR-35 assumes a cleanup sweeper, but addendum A calls the sweeper optional. FR-2 and addendum E point to different date controls. "One stylesheet" touches a decided item (brief SC10).

  *Fix:* explain the phrase once in §4.6: "one hand-written CSS file using custom properties; no third-party UI kit or CSS framework; design tokens are fine". Reword FR-35's check: "an expired Hold no longer reduces Seats left, even if no cleanup has run".

- **[DS-29] [Architect]** HTTPS with a local certificate may clash with "from the README alone". Locations:
  - §4.7 P L431, "A local development certificate is acceptable for the exam"
  - FR-24 P L440, HSTS on every response
  - NFR-1 P L795
  - SM-4 P L930

  Nothing says which of these is acceptable for the examiner:
  - installing and trusting a local certificate authority, which is intrusive;
  - clicking through a browser warning, in which case it is unclear whether HSTS and Secure cookies still work.

  Nothing says how the HTTP-to-HTTPS redirect works with two local servers (website and API) either.

  *Fix:* add to §4.7 which option is acceptable for the examiner.

- **[DS-30] [UX designer]** The Saunas have no defined identity. Locations:
  - FR-1 P L176, "each with one image and one line, worded so that a Seat booking never seems to choose one"
  - FR-4 P L205, "No page or email in the Seat booking flow shows a Sauna identifier"
  - Glossary P L120, "Sauna 1 = 7 …"
  - FR-30 P L519, "The confirmation names the Sauna"
  - FR-4 P L208, "may move freely between the Saunas that are open for Seats"

  The landing page and the Private sauna page need Sauna names and a one-line description of each, but the PRD gives only numbers. From §4.9 on, nothing tells a Seat booker at the Venue which Saunas are private in their Window, because FR-4 forbids naming Saunas.

  *Fix:* give the Saunas display names, or let the UX designer name them. Say how Seat bookers learn which Saunas are closed to them, for example "marked at the door; outside the platform".

- **[DS-31] [UX designer, Story writer]** Smaller UX guesses:
  1. FR-3's assumption contradicts itself (P L196, "If no Window on the date has room … [ASSUMPTION: same day first, then the following days …]"). The date has no room, so "same day first" cannot apply. It also leaves out earlier days and how many alternatives to show.
  2. The Private sauna flow (FR-30 P L514, UJ-5 P L99–L100) asks for no group size, and never says the Sauna's Capacity is the most Guests it takes.
  3. Nothing says whether the Administrator sign-in page is linked from the site or reached only by its address (UJ-3 P L79).
  4. Holds and guest accounts hang on a "Book" step (§4.11 P L571, "When the Guest presses Book"; FR-37 P L606, "after **Book**"), but the Core flow never names that step (UJ-1 P L63, §7 P L821).

  *Fix:* reword the FR-3 assumption as "the nearest Windows with room, before or after, up to N". State "up to [Capacity] people" for a Private sauna. Name the Core step "Book" in FR-5 or §7.

- **[DS-32] [Story writer]** The inputs for numbering and sizing epics are soft. Partly already queued. Locations:
  - §10.1 P L906, "The relative order of items 3 to 6 is the brainstorm's proposal … No backcasting from 15 December has been run"
  - Q6 P L948
  - §10.3 P L915, "Each If-time item gets one epic"
  - §8.2 P L863–L866
  - Add L282, work windows not confirmed

  If-time items 3–6 may still be reordered. §4.13 (FR-38 to FR-42) is a lot for one epic. No figure says how many build days the stories must fit into. The freeze, the token budget per story and the planning depth are already queued; Q6 is not.

  *Fix:* number epics by feature, not by position, until Q6 is decided. Add one sentence giving the available build days once backcasting has been run.

- **[DS-33] [Architect]** Voucher codes have no format and no limit on attempts. Locations:
  - FR-28 P L485, "An expired, used-up or unknown code is refused with the same message"
  - FR-34 P L567 limits resend requests; FR-28 has no such limit

  A Voucher is credit that anyone holding the code can spend, and it is typed by hand. So the code must be hard to guess, easy to type, and protected by a limit on attempts. Without guidance, the architect will pick defaults.

  *Fix:* add to FR-28: "Codes cannot be guessed (at least N random bits) and are easy to type, and attempts are limited as in FR-34."

- **[DS-34] [Architect]** It is unclear whether the Step 2 adapter (the simulated lock) belongs to this architecture round. Already queued. Locations:
  - §10.3 P L915, the architecture covers "everything the Core needs, plus the If-time choices that shape the Core data model"
  - Add L52–L57, direction for the simulated lock

  By §10.3 the lock adapter is out of scope, yet addendum A carries direction for it. Planning depth (§10.3) is already queued.

  *Fix:* once confirmed, say in §10.3: "the simulated lock is designed when Step 2 is planned".

- **[DS-35] [Story writer]** Two cross-references are off:
  - FR-20 (P L386) cites RB-5 for "Guessing … gives the same response". Add L319 defines RB-5 differently: "An account-less Guest uses their own link: allowed for that Booking only".
  - No SM validates FR-17 (Outbox) or FR-21 (personal data). SM-1 covers FR-1 to FR-16, and SM-2 covers FR-15, FR-18 to FR-20 and FR-24.

  *Fix:* move RB-5 to FR-25's first consequence, and add FR-17 and FR-21 to SM-1 or SM-2.

## Questions each reader would send back to the PM

- **Architect:**
  1. Under NFR-1, may the examiner need a locally installed database server or container, or only Python (uv) and Node.js? (DS-2)
  2. Must the data store itself refuse over-capacity writes in every v1 phase, or only in the Core? Are held Seats covered by that guarantee? (DS-3)
  3. From §4.11 on, does the Simulated payment become two steps (start, then a confirmation event)? If so, should the Core adapter be built that way from day one? (DS-4)
  4. Is the Outbox a simulated mailbox that the booking store's security rules do not cover, so plaintext links and codes are allowed there? May an Administrator act as a Guest through it? (DS-5)
  5. What opens the confirmation page, and for how long? (DS-6)
  6. Does a full move update the Booking in place, or cancel it and create a new one? What do "changed" and "cancelled" mean, and which timestamp decides "latest"? (DS-8)
  7. Are seed Windows created relative to the run date, and what is the daily Window schedule? (DS-9; price model already queued)
  8. Is the remedy link a separate token? How long does the session that replaces a Manage-link token last? (DS-16)
  9. Which time rules are scheduled and which are evaluated on read? May tests set the clock? (DS-17)
  10. How is a Booking paid partly by Voucher refunded? How is a Whole-sauna move to a Sauna with another price priced? (DS-18)
  11. What is a test switch, and can the examiner reach one in the running app? (DS-14)
  12. May a Window with Bookings be edited or deleted? Are Windows created from a recurring schedule? (DS-23)
  13. Is the examiner expected to trust a local certificate authority for HTTPS? (DS-29)
- **UX designer:**
  1. Does the Core layout reflow to 320 CSS px (WCAG 2.2 AA), or is there a stated exception until FR-51? (DS-1)
  2. What do reload, Back and a later visit show on the confirmation page? (DS-6)
  3. Which emails may a Guest see on a page, and which does only the Administrator see, in the Outbox? (DS-7)
  4. May we tell the Guest that their Seats are held until a set time, and how do held Seats look to other Guests? (DS-13)
  5. Do pages and emails say that payment and email are simulated? Can a failed payment be shown outside tests? (DS-14)
  6. What are the opening hours, the number of Windows a day and the changeover gap? (DS-9)
  7. What are the Saunas called, and may the landing page name them? (DS-30)
  8. Does this round design the If-time 2–6 pages, or only the Core? (DS-21)
  9. Are emails plain text or HTML, and which events send one? (DS-19)
  10. What does the Manage page show for each Booking status? What does the pay button say when a Voucher covers the whole total? (DS-20)
  11. How will "intuitive" be verified? (Q2, already queued)
- **Story writer:**
  1. Which phase owns WCAG reflow: the Core layout story or FR-51? (DS-1)
  2. May If time 5 rework the Core payment story, or should the Core story already use two-step payment? (DS-4)
  3. May I move each consequence of FR-13, FR-29, FR-31 and FR-32 to the epic where it first becomes testable? (DS-10)
  4. Do If-time stories carry FR-22 and FR-23 ACs when they are built? (DS-12)
  5. Where is the research catalogue, and what are SC2, SC3, SC4 and SC8? (DS-22)
  6. What exactly does the seed-data story create: schedule, dates, sample Bookings? (DS-9)
  7. How can a Guest-side AC for UJ-4 pass if the Voucher code reaches only the Outbox? (DS-7)
  8. Is the order of If-time items 3–6 final enough to number epics, and how many build days are there? (DS-32; partly queued)
  9. Does every Change send a confirmation email? (DS-19)

## What works well for downstream
- **A Glossary the architect can build from.** Open for Seats, Seat capacity, Seats left, Room ahead and Fill order are stated as rules. Placement is defined as a way of counting, not an assignment. The ambiguous phrase "whole booking" is banned.
- **Testable consequences with concrete numbers.** Examples: A6 at 42 of 44 Seats, B1 "20 ≤ 29", A2 [7,10,5,0] → [7,10,2,0], D1 = 34. INV-1 to INV-5 come with a model-based test against a brute-force reference. That gives the architect a ready test oracle and the story writer ready ACs.
- **Phase tags that match §10.** Every feature and every UJ is tagged, and the tags and FR IDs match §10.1 and §10.2 with no gaps (FR-1 to FR-51 are contiguous). "Core done" and "website complete" are defined. §10.3 names the If-time choices the architecture must fix now: Placement, lock unit, Holds as data and Manage-link tokens.
- **Honest technical direction.** Addendum A separates sourced mechanisms from inference, with confidence levels and caveats that depend on the database version. Addendum K maps every brief test ID to an FR and a phase.
- **Clear limits.** §9 lists the non-goals. The Vision rule says v1 "adds no tables, settings, endpoints or abstractions for Vision items". The "In the Core …" statements show where later features plug in, for example that Seat capacity in the Core is the sum of all Capacities.
- **A strong UX starting point.** §6 gives palette, type, imagery, tone and anti-references. FR-5 lists the information Guests must get before paying. "Before you come" is written. FR-22 treats "sold out" as information, not an error. FR-23 lists concrete checks, and NFR-9 bans dark patterns.
- **Security specific enough to build.** FR-18 lists the inputs to reject. The password rules follow NIST. Sign-in, resend and Vouchers all use the same-message rule, and the token entropy is given.
