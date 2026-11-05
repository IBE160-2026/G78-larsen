---
name: Saunalöyly Booking Platform
status: final
sources:
  - {planning_artifacts}/prds/prd-booking-platform-2026-10-29/prd.md
  - {planning_artifacts}/prds/prd-booking-platform-2026-10-29/addendum.md
  - {planning_artifacts}/architecture/architecture-booking-platform-2026-11-03/ARCHITECTURE-SPINE.md
  - {planning_artifacts}/briefs/brief-booking-platform-2026-09-20/brief.md
updated: 2026-11-05
---

# Saunalöyly Booking Platform: Experience Spine

## Foundation

**Mocks.** The rendered references are in `mockups/`: [colours](mockups/color-themes-3.html), [Landing and Book seats](mockups/directions-3.html), [Details](mockups/key-details.html), [Review](mockups/key-review.html), [Confirmation](mockups/key-confirmation.html) and [Booking list](mockups/key-booking-list.html). `DESIGN.md` and this spine win on any conflict with a mock.

**Form factor.** Web, laptop first. All Core pages are designed for laptop (FR-22). The guest booking flow also has a specified narrow layout so it is ready if mobile is built, but FR-51 is last in Step 2, so that layout is specified, not promised for v1. Guests who book on the way to the sauna may be poorly served in v1; Lisa accepted this risk.

**UI system.** None. One stylesheet with CSS custom properties, React SPA, no UI library. `DESIGN.md` is the visual identity reference and every `{path.to.token}` below resolves there. This spine covers behaviour and defers requirements to the PRD by FR, UJ and AD number.

**Core experience.** Booking is simple and clear for the Guest. Three questions on one page, then details, then review, then a confirmation that says what to do on arrival. Light mode only. [ASSUMPTION] No dark mode, because only light values were chosen (memlog).

**Language.** English only (NFR-5). A few Finnish words appear, each with an English gloss (PRD §6).

### The word Session

**Session** is the Guest-facing word for the domain term **Window**. It is used in all UI copy and emails, including Administrator pages, so one product has one word. Window stays the term in the PRD, the architecture and the code.

Session here never means the browser session. Copy must not use the word for that: a message about an expired sign-in or browser session says what the person should do, without the word "session".

In sentences it is lower case, as in the mock ("Choose a session"). All other terms mirror the PRD verbatim. The Whole-sauna booking is "Private sauna" to Guests (PRD §3).

## Information Architecture

[ASSUMPTION] IA closes on the PRD §7 Core pages plus the plug-in points for Private sauna, Voucher and sign-in (memlog).

**Core, Guest**

| Surface | Reached from | Purpose |
|---|---|---|
| Landing | Direct | Present the Venue, make people want to visit, start a booking in one step (FR-1). Holds "Before you come", directly linkable |
| Book seats | Book seats action on Landing | Date, Seats and Session on one page, with the total (FR-2, FR-3, FR-4) |
| Details | Continue on Book seats | Name and email (FR-5) |
| Review | Continue on Details | Check everything, accept the terms, pay (FR-5, FR-6) |
| Confirmation | Pay succeeds. Route `/confirmation/:reference` (AD-12) | Booking reference, what to do on arrival, the email as sent (FR-8) |
| Terms | Text link | Full booking terms (FR-5) |
| Privacy notice | Text link wherever data is collected | Separate from Terms (FR-21) |

Details and Review are two separate pages. PRD §7 lists them as one, and FR-5 allows either.

**Core, Administrator (laptop only)**

| Surface | Reached from | Purpose |
|---|---|---|
| Sign-in | Administrator address | Email and password (FR-15) |
| Booking list | After sign-in; Administrator bar | Sessions and Bookings for a chosen date (FR-16), read-only |
| Outbox | Administrator bar | Every email as sent (FR-17). Also how the examiner sees emails |
| Sign-out | Administrator bar | An action, not a page |

**Arrival.** In Core the Guest gives the Booking reference at reception. This is the content of "what happens next" on the Confirmation page and in the email (FR-8). [ASSUMPTION] Reception staff find a reference in the read-only Booking list; there is no check-in marking in v1, because the PRD has none (memlog).

**If time, Guest.** Private sauna, Manage booking, My booking, guest sign-up, sign-in and My bookings. See If-time Plug-in Points. The Remedy page and the screens of §4.13 are outside this round.

## Content Homes

**The no-repetition rule (Lisa).** Each fact has one home per page. A fact may appear on several pages, but never twice on one. A page must not say the same thing to fill space, and a new element must name which home it takes.

**Accepted exceptions (Lisa).** These repetitions are required:

- The amount is in the Booking summary and on the Pay button on Review. FR-5 and FR-6 each require it.
- An error is in the Error summary and at its field. FR-23 requires both.
- Confirmation has the page facts and the email as sent. FR-8 requires both, and the email is a record of what was sent, not a second statement.

[ASSUMPTION] Two more follow from the same requirements. On Review, the name is in the Wordmark and the Venue row (FR-5). After a refusal, a date can be in both the Booking summary and the Nearest sessions rows, because each row needs its own date.

**Landing**

| Item | Home |
|---|---|
| Name | Rail, Wordmark |
| Book seats action | Rail |
| Opening hours, Session length | Rail |
| Price per seat | Rail |
| Venue description | Main, under the hero |
| Etiquette, safety, practical notes | Main, "Before you come" |
| How Seats work (the Seat statement) | Main, intro of "The saunas" |
| Saunas, one image and one line each | Main, "The saunas" |
| Address and contact details | Main, "Find us" |
| Terms and Privacy notice links | Main, "Find us" |
| Session schedule | Not on this page. It lives on Book seats, which FR-1 allows |

**Book seats**

| Item | Home |
|---|---|
| Page heading | Main |
| Date | Main, question 1 |
| Number of seats | Main, question 2 |
| Sessions: start, end, Seats left | Main, question 3 |
| Total and price per seat | Rail only, never per Session |
| Continue | Rail, once |
| Name, link to Landing | Rail, Wordmark |
| Seat statement | Rail |
| Changing time note | Rail |
| Terms and Privacy notice links | Rail |

Session length stays once on Landing so first-time Guests know how long a visit lasts. On Book seats the times say it.

**Other pages.** Order from top to bottom, built from what FR-5, FR-8 and FR-15 to FR-17 require. Details, Review, Confirmation and Booking list are rendered in `mockups/`. Terms, Privacy notice, Sign-in and Outbox are spine only, as Lisa chose, so [ASSUMPTION] their order has not been reviewed.

| Page | Order |
|---|---|
| Details | Heading, Back, name, email, Privacy notice link, Continue |
| Review | Heading and Back. Then two columns: Booking summary on the left, and on the right booking terms with the two required statements, Terms and Privacy notice links, Terms checkbox, Pay with the payment note beside it. Reading order follows that sequence |
| Confirmation | "Booking confirmed" in `{colors.success}`, Reference display, the reception sentence directly under it with no heading, Booking summary, booking terms, link to "Before you come", Email as sent |
| Terms, Privacy notice | Heading, text |
| Sign-in | Administrator bar, heading, email, password, Sign in |
| Booking list | Administrator bar, heading, date, Session groups in time order |
| Outbox | Administrator bar, heading, Outbox entries |

## Voice and Tone

Microcopy. Brand voice lives in `DESIGN.md`, Brand & Style. Copy is short and concrete, with facts before persuasion (PRD §6).

| Do | Don't |
|---|---|
| "12 seats left" | "Only 12 left, hurry!" |
| "Sold out" with the nearest Sessions | "Oops! Error" |
| Say what happened, then what the Guest can do (FR-22) | A message with no next step |
| "A booking gives you seats in the shared saunas open during your session. On site you can move freely between them." | Any wording that implies all four Saunas are always available |
| Let the place carry the feeling | "Pamper yourself", "Treat yourself", heat boasts (PRD §6) |

**The Seat statement must stay true** when a Sauna is Whole-sauna-booked or otherwise not open for Seats (Lisa, FR-4). Use the wording above. Once §4.9 exists, add that a group that wants to stay together should book a Private sauna.

**Fixed copy, verbatim**

| Text | Where | Source |
|---|---|---|
| "Simulated payment: no money moves" | Pay step and every email that mentions a payment | FR-6 |
| "Pay NOK 500" (states obligation and the real amount) | Pay button | FR-6 |
| "1 seat left" (true current number) | Unavailable Session | FR-3 |
| "No seat free" | Definite loss | FR-14 |
| "please try again" | Retries used up | FR-14 |
| "Before you come" | Section name | FR-1 |
| "Book seats", "Private sauna", "My booking" | Actions, page | FR-1 |
| "Sold out" | Availability information | FR-22 |

"Complete booking" is not an acceptable pay label (addendum D).

The "Before you come" text follows FR-1, with one change for the UI word: "Changing time is part of your session." The swimwear rule is missing (see Open Items).

**Required statements, meaning fixed by the PRD, wording accepted by Lisa**

| Statement | Wording | Source |
|---|---|---|
| No right of withdrawal for a fixed date | "A booking for a fixed date cannot be withdrawn." | FR-5 |
| What can be changed, in Core | "A booking cannot be changed or refunded." | FR-5, Lisa |
| What happens next | "Keep your booking reference and give it at reception when you arrive." | FR-8, Lisa |
| Private sauna is not held | "The sauna is not held while you pay." | FR-29 |

**Page and message wording, accepted by Lisa**

| Text | Where |
|---|---|
| "Continue booking" | Book seats and Details action. The page heading tells them apart |
| "Your details" | Details heading |
| "Review" | Review heading |
| "Booking terms" | Heading on Review and Confirmation |
| "Date", "Session", "Seats", "Total", "Venue", "Contact", "Email" | Booking summary labels |
| "The nearest sessions with room:" | Notice after a refusal on Review |
| "Sent by email:" | Label above Email as sent |

| "1 seat left, too few for this booking" | Unavailable Session row |
| "Holds 7" | Sauna card |
| "Already started" | Started Session that can still be booked |
| "Processing" | Pay button during payment |
| "No bookings" | Booking list, Session without Bookings |
| `14.11.2026`, "Type it as dd.mm.yyyy, or pick a day below" | Date format and hint |
| "Back" | Details and Review |
| "I accept the booking terms" | Terms checkbox |
| "Booking confirmed" | Confirmation heading |
| "Only 1 seat left in this session. You have not been charged." | Seats taken while typing |
| "No seat free. You have not been charged." | Lost last-Seat race (extends the fixed text) |
| "This session can no longer be booked. You have not been charged." | Deadline passed |
| "The payment failed. You have not been charged. You can pay again." | Failed payment |
| "No room for 2 seats on Saturday. The nearest sessions with room:" | No room on the date |
| "Booking opens 4 weeks ahead." | Last horizon day |
| "There is no room for 2 seats in the next 4 weeks." | No room in the horizon |
| "Choose a session", as an error | Continue with a choice missing |
| "Enter a valid email address" | Email field (from `color-themes-3.html`) |
| "Enter your name" | Name field |
| "Wrong email or password" | Sign-in, every refusal |
| "This page is not available." | Unknown or not-yours address |
| "Loading sessions" | Book seats while reading |
| "No emails" | Empty Outbox |

"What happens next" is not a heading, on the page or in the email. The reception sentence stands by itself.

**Capitals.** Guest copy uses plain sentence case: seats, saunas and session are lower case. Only names such as Rauha and Before you come take capitals. Domain terms in this spine stay capitalised, as in the PRD.

## Component Patterns

Behavioural. Visual specs live in `DESIGN.md`, Components.

**Shared**

| Component | Use | Behavioural rules |
|---|---|---|
| Primary button | The one action on a page | One per page. Label says what happens. On Pay it states the amount (FR-6). Pay shows "Processing" and takes no second press while payment runs, with no countdown. Keeps focus while processing |
| Text link | Secondary navigation | Never starts a Booking or takes payment. Leaving Details or Review for Terms or Privacy notice and coming back keeps everything entered (FR-5) |
| Wordmark | Rail on guest pages | Landing: the page heading, not a link. Elsewhere: link to Landing |
| Rail | Left column on guest pages | Sticky on laptop, so the action stays in view without covering anything. Own column, so focus is never hidden behind it |
| Rail note | Book seats rail | Plain text. Never a place for new requirements or marketing |
| Text field | Date, name, email, sign-in | Label always visible. Name and email limits per FR-5. Paste and password managers work (FR-19). Values kept on Back (FR-5) |
| Terms checkbox | Review | Never pre-ticked (NFR-9). Pay without it gives an Error summary and a Field error. Nothing is charged |
| Image block | Landing | Not interactive. Each image has alt text that says what it shows |

**Book seats**

| Component | Use | Behavioural rules |
|---|---|---|
| Date calendar | Question 1 | Date can be typed or picked; the two stay in step (FR-2). Only dates FR-2 allows can be chosen. A sold-out date can still be chosen, and it then shows availability. Calendar ends at the horizon. "Next month" moves the month; [ASSUMPTION] a matching "Previous month" appears once forward, because the mock shows only the first month |
| Seat picker | Question 2 | Ten choices, 1 to 10 (FR-2). Changing the number updates the total and which Sessions are too small. No free number entry, so a number outside 1 to 10 cannot be sent |
| Session list | Question 3 | All Sessions for the date in time order, including unavailable ones, so the schedule is visible (FR-1, FR-3). Past-deadline Sessions are left out. Numbers always come from the server (AD-5). No urgency cue of any kind (NFR-9) |
| Session row | Session list | Click anywhere on the row to select. Unavailable rows cannot be selected and say why in text. No price in the row. A selected Session that stops fitting the number is cleared, and step 3 says so in a Notice |
| Total block | Rail | Appears once a number is chosen. Equals Seats × price per Seat, which is what is charged (FR-3). Announced when it changes. One total, not one per Session: price is equal across Sessions in v1 |
| Fixed action bar | Narrow screens | Holds the page's one action, always visible, exists once. Must never cover focus or content |

[ASSUMPTION] On arrival nothing is pre-selected: no date, number or Session. NFR-9 forbids pre-ticked options, and a Guest's own choice keeps the total honest. The Session list appears once a date is chosen, so the schedule is one step away.

[ASSUMPTION] Continue is always enabled. Pressing it with a choice missing shows a Field error at that question and moves focus there, because a disabled button gives no reason.

[ASSUMPTION] Changing the date clears the chosen Session, because a Session belongs to one date.

**Landing**

| Component | Use | Behavioural rules |
|---|---|---|
| Rule list | "Before you come" | Static text. The section has its own address so Confirmation and emails can link to it (FR-1, FR-8) |
| Sauna card | "The saunas" | Not a link and not selectable. Worded so a Seat booking never seems to choose a Sauna (FR-4). Sauna names appear here and never in the Seat booking flow |
| Find us block | End of Landing | Static text and two Text links. Holds the Venue facts that Review also shows (FR-1, FR-5) |

**Messages and confirmation**

| Component | Use | Behavioural rules |
|---|---|---|
| Notice | Availability and neutral messages | Says what happened and what to do next. Availability is not an error (FR-22). Announced as a status message |
| Nearest sessions | No room, refused requests | Up to three Sessions with room for the chosen number, same day first, then following days within the horizon (FR-3). Choosing one selects that date and Session and keeps the number, name and email |
| Error summary | Top of a form with errors | Lists each error as a link to its field. Takes focus when it appears (FR-23) |
| Field error | Next to a field | Always with an Error summary. Input is kept (FR-23) |
| Booking summary | Review, Confirmation | Date, Session, Seats, total incl. VAT. On Review it also holds Venue identity and contact details (FR-5). On Confirmation it also holds the Guest's email (FR-8), and the amount is the stored total (AD-13) |
| Reference display | Confirmation | 8 characters (AD-20). Selectable text. Opens nothing by itself (FR-8) |
| Email as sent | Confirmation, result pages | Labelled "Sent by email:". Shows the stored email, not a rebuilt one (FR-8, AD-12). Only on the page of the action that sent it (FR-17). Never holds a Manage link resend or remedy email |

**Administrator**

| Component | Use | Behavioural rules |
|---|---|---|
| Administrator bar | Every Administrator page | Booking list, Outbox, Sign out. On Sign-in it shows only the name |
| Session group | Booking list | One per Session, in time order, with Seat capacity, Seats booked, Seats left (FR-16). Figures equal what Guests see. Shown even with no Bookings |
| Booking table | Inside a Session group | Reference, name, email, Seats, total, time of booking (FR-16). [ASSUMPTION] Time of booking is `dd.mm.yyyy HH:MM`, oldest first. Read-only. Stored text is escaped (FR-18). Refreshes on page load only |
| Outbox entry | Outbox | Time, recipient, subject, full body, links in plain text (FR-17), always open. [ASSUMPTION] Newest first, because the usual check is the email just sent |

[ASSUMPTION] The date on the Booking list is a Text field defaulting to today, with "Previous day" and "Next day" Text links. UJ-3 opens on today, and the Date calendar's rules are about what Guests may book, which does not apply here.

**If-time plug-ins**

| Component | Use | Behavioural rules |
|---|---|---|
| Private sauna entry | Landing rail | See If-time Plug-in Points. Absent until §4.9 is built |
| Voucher field | Review | See If-time Plug-in Points. Absent until §4.8 is built |
| Sign-in choice | Between Book seats and Details | See If-time Plug-in Points. Absent until §4.12 is built |
| Sauna option | Private sauna page | One per Sauna that FR-29 allows, with Capacity, price and free Sessions (FR-30). The Guest always picks the Sauna |

## State Patterns

Any screen can be overtaken by a refusal when the Guest submits (AD-2). A refused action leaves nothing partly done (AD-3). The server sends codes and facts, and the SPA owns the copy (AD-16). The SPA never uses the browser clock for a rule (AD-4), so every time-based state below is decided by the server. Wording is in Voice and Tone.

**Landing**

| State | Treatment |
|---|---|
| Venue facts loading or failed | [ASSUMPTION] The rail action is always there. Facts come from the API (AD-16), so if the read fails the Notice says "please try again", because Book seats still works without them |

**Book seats**

| State | Treatment |
|---|---|
| First arrival | Date and number empty, no Sessions, no total. The per-seat line is in the rail |
| Reading Sessions | [ASSUMPTION] The text "Loading sessions" in the list, with no spinner or skeleton, in keeping with minimal motion |
| Read failed or offline | [ASSUMPTION] Notice with "please try again". Choices kept. No separate offline design: this runs locally only |
| Fewer Seats left than chosen | Row unavailable, not selectable, with the true number in text (FR-3) |
| Session with no Seats left | Row unavailable, "Sold out" |
| Started but still bookable | Listed as usual, with "Already started" |
| Past the Booking deadline | Not listed (FR-3) |
| No room on the date | Notice with Nearest sessions (FR-3). Availability, not an error (FR-22) |
| Last horizon day | Calendar ends there, with one line saying booking opens 4 weeks ahead. The number comes from the server, because the horizon becomes a Setting (FR-39) |
| No room anywhere in the horizon | Say so plainly, with no alternatives |
| Date not bookable, typed | Field error at the date. Calendar unchanged |
| Date mistyped | Field error at the date with the expected format |

**Details**

| State | Treatment |
|---|---|
| Empty or invalid field | Error summary and Field error (FR-23). Input kept. Server repeats the check (FR-18) |
| Back, then forward | Everything entered is kept (FR-5) |

**Review**

| State | Treatment |
|---|---|
| Terms not accepted | Error summary and Field error |
| Payment in progress | Pay shows "Processing", no second press, no countdown |
| Double click, reload or retry | First outcome returned. A Guest who was booked sees Confirmation, never "No seat free" (FR-6, AD-9) |
| Payment failed | Error summary with a way to pay again. No Booking, no Seats taken, no email (FR-7) |
| Seats taken while typing | Notice with the true Seats left and Nearest sessions. Nothing charged (FR-12, UJ-1) |
| Lost the last Seat | Notice with "No seat free" and Nearest sessions. Nothing charged, no email (FR-11) |
| Deadline passed before payment | Notice that the Session can no longer be booked, with Nearest sessions. Nothing charged |
| Retries used up | Notice with "please try again", different from "No seat free". Nothing written (FR-14) |
| After a refusal | Guest stays on Review with the name and email kept. The Notice sits under Back. Pay, the payment note and the Terms checkbox are removed for the refused Session (Lisa). The Booking summary and booking terms stay. Choosing a nearest Session reloads Review with Pay, the note and the checkbox back. This gives one place to recover without retyping (WCAG 3.3.7) |

**Confirmation**

| State | Treatment |
|---|---|
| Reload in the paying browser session | Shows again (FR-8) |
| Any other browser, or no browser session | "This page is not available." The reference alone opens nothing (AD-12) |

**Terms and Privacy notice**

| State | Treatment |
|---|---|
| Normal | Static text, reachable from every page that links to it. Coming back keeps a booking in progress (FR-5) |

**Not available and browser-session states**

| State | Treatment |
|---|---|
| Unknown address or unknown Booking | "This page is not available." with a link to Landing. [ASSUMPTION] One plain page for all of these, because the response must be the same whether or not a Booking exists (FR-20) |
| Browser session gone during a booking (`401 no_session`, `409 invalid_key`) | [ASSUMPTION] The SPA makes a new browser session and a new key without comment, entered values stay, and the Guest sees "please try again". Not in the PRD's §7 list. Copy must not call this a session |
| Payment held by the test switch (`409 payment_pending`) | [ASSUMPTION] Treated as "please try again", with the same key. Test only (AD-14) |

**Administrator**

| State | Treatment |
|---|---|
| Wrong email or password | Same message for both, in an Error summary with no Field error, so it does not say which was wrong (FR-15) |
| Sign-in throttled | Same message as a wrong password (FR-15, AD-11) |
| Anonymous at an Administrator address | Sent to Sign-in |
| After Sign out | Back at Sign-in. The sign-in grants nothing after this, so the browser back button leads to Sign-in too (FR-15) |
| Sign-in expires during work | [ASSUMPTION] Sent to Sign-in on the next action, same as anonymous, without using the word "session" |
| Date with no Bookings | All Sessions with their figures and "No bookings" |
| Session with no Seats left | Session group header in `{colors.unavailable}`, with "Sold out" and "Seats left 0" in weight 600, so a full Session reads at a glance (Lisa) |
| Outbox empty | [ASSUMPTION] "No emails". Unusual, because seed Bookings send email |
| Booking list read failed | [ASSUMPTION] Notice with "please try again" |

Focus states are in Interaction Primitives. If-time states are in If-time Plug-in Points and Open Items.

## Interaction Primitives

- Click or keyboard, always both. No hover-only information, no drag, no gestures.
- Focus ring: 3 px `{colors.focus}`, 2 px offset, on every interactive element. On hidden radios the ring shows on the visible cell.
- Date, Seat and Session choices are radio groups, each one tab stop, with arrow keys inside.
- Focus moves to the page heading on every route change (architecture Conventions). On Landing the heading is the Wordmark. [ASSUMPTION] The Wordmark is the page's one top-level heading, so that this rule has a target.
- No live updates (AD-4). Sessions are read again when the date or number changes. The server decides at submit.
- Back in the browser and the Back link do the same thing, and neither loses input (FR-5).
- [ASSUMPTION] Motion is minimal and respects reduced motion (memlog). No transitions are needed for any Core behaviour.
- [ASSUMPTION] No dialogs in Core. Everything is a page or an inline message, because no modal was rendered.
- **Banned:** countdown timers, "people viewing" counts, padded numbers, pre-ticked options, hidden fees (NFR-9, FR-3), any mention of a Hold or time limit in the Seat flow (FR-35), consent banner (FR-21), marketing email, combined basket across Sessions (FR-9).

## Accessibility Floor

Behavioural. Contrast lives in `DESIGN.md`, Colors. The floor is FR-23: WCAG 2.2 AA on every Core page, with the one stated exception of 1.4.10 Reflow until FR-51. Manual pass with keyboard alone covers the whole booking flow and the Booking list.

- **Keyboard order on Book seats, to verify against WCAG 2.4.3.** The rail is visually on the left and last in tab order. Main comes first in the source, so the order runs date field, month link, calendar, seats, Sessions, Continue. Within the rail the Wordmark is visually first but comes after Continue in tab order. This is deliberate, so the Guest meets the questions before the action, but it has not been tested. If it fails, the fix must not repeat the action.
- **Session rows.** The accessible name of each radio must include the Seats left text, for example "13:00 to 14:30, 12 seats left". The mock names only the time, which would hide availability from a screen reader. Check that unavailable rows, whose radios are disabled, can still be reached by reading.
- **Calendar.** Days have full names ("14 November 2026"). The radio pattern is a list to arrow keys, not a grid: confirm this in the manual pass.
- **Status messages.** Total block changes, Notices and "Processing" are announced without moving focus (WCAG 4.1.3).
- **Errors.** Text next to the field and in a summary (FR-23). Colour is never the only cue.
- **Focus not obscured.** The Fixed action bar must leave room, so a focused element always scrolls clear of it (WCAG 2.4.11, FR-23).
- **Targets.** At least 24 × 24 CSS px (FR-23). Calendar days at `{spacing.calendar-cell-height}` and Session rows at `{spacing.session-row-height}` meet this.
- **Redundant entry.** Name and email are never asked twice in a flow (WCAG 3.3.7).
- **Accessible sign-in.** No cognitive test; paste and password managers work (WCAG 3.3.8, FR-19).
- **Language.** Page language is English. Finnish words other than names are marked as Finnish (WCAG 3.1.2).
- **Images.** Alt text says what is shown. Image-free text must still make sense.
- **Automated.** axe-core in `tests/e2e/`.

## Responsive & Platform

Laptop sizes per FR-22. Everything below 1366 px is specified for FR-51, not promised for v1.

| Width | Behaviour |
|---|---|
| 1366 px and up | As in `DESIGN.md`, Layout & Spacing. No horizontal scrolling at 1366 × 768 or 1920 × 1080 (FR-22). Review keeps Pay in the first view (Lisa) |
| 1024 to 1365 px | [ASSUMPTION] Rail stays. Book seats stacks the date above seats and Sessions, and Review stacks the Booking summary above the terms and Pay, because the two columns no longer fit beside the rail |
| Below 1024 px | [ASSUMPTION] Narrow layout: one column, rail dissolved as below. The threshold is a starting value, to be set when the layout is built |
| 320 px | Lower limit. No horizontal scrolling, FR-23 applies (FR-51) |

**Narrow layout**

- The Book seats control is fixed at the bottom of the screen, always visible, and exists once. It must not hide focus or content.
- [ASSUMPTION] On Landing the Wordmark moves to the top and the rail facts move under the hero, in the same order, because they need a place and must not repeat.
- [ASSUMPTION] On the Book seats page the Total block and Continue collapse into the same Fixed action bar, because this keeps the total and the action visible and each fact exists once. The Wordmark moves to the top, and the Rail notes and links go below the Session list.
- [ASSUMPTION] The Sauna cards and "Before you come" go to one column, and the Find us block stacks.
- [ASSUMPTION] Details, Review and Confirmation need no change beyond one column.

**Administrator pages stay laptop-only**, with no narrow layout.

**Browsers.** No list is stated. Tests use Chromium through Playwright.

## Inspiration & Anti-patterns

- **Direction history.** Open Guide combines the earlier Long Look and Leaflet directions. Four Rooms and Timetable were not carried forward. Forest green as the page background (variant B) was not chosen. These are in `.working/` as history only.
- **References on record, to study and not copy (addendum F):** Löyly Helsinki, Kulttuurisauna, KOK Oslo, Oslo Badstuforening.
- **Evidence on record (addendum E):** typed dates, check-answers page, errors by the field and in a summary, not used for "sold out". The "sticky call-to-action +4.2 %" figure was not found and must not be cited.
- **Rejected:** urgency selling, spa-luxury cues, polished stock photography, heat boasts, sexualised framing (PRD §6). A total per Session (Lisa, no-repetition). The Session schedule on Landing (Lisa).

## Emails

Plain text, English, simulated, listed in the Outbox (PRD §7). [ASSUMPTION] Notifications are the PRD's simulated emails only, with no SMS or push (memlog).

- Content per email is in the PRD §7 table. This spine adds only the UI word.
- The Booking confirmation carries the reception sentence as FR-8's "what happens next", with no heading. That text and the booking terms are one shared text, used by page and email (AD-12).
- [ASSUMPTION] The confirmation email's line layout follows the block in `mockups/key-confirmation.html`, with its content from the PRD §7 table. The base URL for absolute links is not set yet.
- The fixed payment note goes in every email that mentions a payment (FR-6). Links are absolute (AD-12).
- Seat booking emails never name a Sauna (FR-4).

## If-time Plug-in Points

Core pages leave room for these and show none of them until built. None of them changes the Core flow. Copy follows the same rules: fixed where the PRD fixes it, otherwise proposed.

| Feature | Where it plugs in | Behaviour |
|---|---|---|
| Private sauna entry (§4.9) | [ASSUMPTION] Landing rail, directly under Book seats, as a Text link, because the page keeps one main action (§4.1). On narrow screens it is in the page flow, not in the Fixed action bar | Opens the Private sauna page. Landing also gains the price per Sauna: [ASSUMPTION] on each Sauna card, under the size line |
| Seat statement (§4.9) | Landing "The saunas" intro and Book seats rail | Gains the group sentence (FR-4) |
| Voucher field (§4.8) | [ASSUMPTION] Review, between the Booking summary and the terms, always visible, because PRD §7 says "at payment" and the total must be settled before accepting | Reduces the amount and updates the Pay label (FR-28). Expired, used-up and unknown codes get one identical refusal as a Field error. Rest paid by Simulated payment |
| Sign-in choice (§4.12) | After Continue, before Details. Space reserved in the flow by keeping Details as its own page | Continuing without an account is the default and most prominent option, as the Primary button. Sign-in is a Text link (FR-37). A signed-in Guest books with the account's email |
| Hold (§4.11) | Starts when Continue is pressed. No visible element | The Guest is told nothing (FR-35). [ASSUMPTION] Cancel is a Text link on Details and Review that returns to Book seats and releases the Hold, because FR-35 needs a Cancel and no page names one |
| My booking (§4.10) | [ASSUMPTION] Text link in the Find us block, which is the home for ways to reach the Venue | Booking reference and email, same reply whether or not they match, no Booking data shown (FR-34). The new link appears only in the Outbox |
| Manage booking (§4.8) | From the Manage link in the confirmation email | Shows the Booking and the Changes allowed (FR-25). Each Change has a confirming step, then a result page with Email as sent. See Flow 4 |
| Private sauna page, and its Review and Confirmation (§4.9) | Own page, then the same Details, Review and Confirmation | See Flow 5. Review says the Sauna is not held while paying (FR-29). Confirmation names the Sauna |
| Guest sign-up, sign-in, My bookings (§4.12) | [ASSUMPTION] Same forms and refusal rules as Administrator Sign-in | Sign-up reply never says whether the email has an account (FR-37). My bookings lists only Bookings made while signed in. Guest with no Bookings: a Notice |

The Book action in FR-35 and FR-37 is the Continue action on Book seats.

**If-time states fixed by the PRD:** after the Cutoff the Manage page shows the Booking and refuses every Change with the reason (FR-26, FR-33). A move without room changes nothing (FR-26). An invalid, expired or replaced Manage link gets "This page is not available.", the same as a link that never existed (FR-25). A move to a Sauna at another price is refused with the reason (FR-33). A Sauna taken before Private sauna payment means nothing is charged (FR-29). Undecided states are in Open Items.

## Key Flows

Times are seed times (extract §14, C1). Prices are the seed example. Wording in flows is as in Voice and Tone.

### Flow 1: UJ-1. Ingrid books two seats for Saturday afternoon

Ingrid has tried a public sauna once and wants to take a friend. She is anonymous, on a laptop, and does not want an account.

1. On Landing she sees the Venue, the rail facts and **Book seats** without scrolling, and presses it.
2. Book seats opens with the three questions. She picks Saturday in the Date calendar and 2 in the Seat picker.
3. The Session list shows Saturday's eight Sessions. 16:00–17:30 shows "1 seat left, too few for this booking" and cannot be chosen. The rail shows Total NOK 500 incl. VAT.
4. She picks 14:30–16:00 and presses "Continue booking".
5. On Details she types her name and email and continues.
6. Review shows Saturday 14:30–16:00, 2 seats, NOK 500 incl. VAT, the Venue's details, and the booking terms: a booking for a fixed date cannot be withdrawn, and a booking cannot be changed or refunded.
7. She accepts the terms and presses **Pay NOK 500**, beside "Simulated payment: no money moves". The button shows "Processing".
8. **Climax:** Confirmation shows her Booking reference, the Session, 2 seats, the total and her email, and tells her to give the reference at reception. The email is below, exactly as sent. She knows the seats are hers and what to do when she arrives.

Failure: someone took the seats while she typed. She stays on Review, is told how many Seats are left, and is offered the nearest Sessions with room for 2, keeping her name and email. Nothing is charged. If the payment fails, she can pay again and nothing is booked.

### Flow 2: UJ-2. Aino and Jonas reach for the last seat at the same moment

Both are anonymous, on Review, with 1 seat for Friday 17:30–19:00, which shows 1 seat left. Which of them wins is not decided by design; this telling has Aino first. [ASSUMPTION] Aino and Jonas keep their PRD names (memlog).

1. Both press **Pay NOK 250** within the same second.
2. Both buttons show "Processing".
3. **Climax:** Aino lands on Confirmation with her reference. On the same page he was on, Jonas sees "No seat free. You have not been charged." with the nearest Sessions with room for 1. He loses nothing he typed.
4. Jonas picks 19:00–20:30 and is back on Review with his name and email in place, or he leaves. Either way he got no email and owes nothing.

The Session now shows "Sold out" to Guests and 0 Seats left in the Booking list, with one new Booking.

Failure: if the server used up its retries, Jonas sees "please try again" instead, which is a different message from "No seat free" (FR-14).

### Flow 3: UJ-3. Katja checks who is coming tonight

Katja runs the evening shift. She is not signed in and is on the Sign-in page.

1. She signs in with her email and password.
2. The Booking list opens on today, with Sessions in time order.
3. **Climax:** she sees at a glance that 17:30–19:00 is full and 20:30–22:00 has 9 Seats left, with no arithmetic.
4. She reads the Bookings under a Session, then opens the Outbox and finds a Guest's confirmation.
5. A Guest arrives and gives a reference. Katja finds it in the Booking list. A Guest who has lost the reference gives their name and email instead, and Katja finds the Booking the same way (Lisa). [ASSUMPTION] This is how reception works in Core (see Information Architecture).
6. She signs out.

Failure: a wrong password gives the same message as a wrong email, and so does a throttled sign-in. A Guest who types the Administrator address is sent to Sign-in and gets nothing else. A date with no Bookings shows all Sessions with "No bookings".

### Flow 4: UJ-4. Ingrid's friend falls ill

*If time.* It is Friday morning, more than 12 hours before Ingrid's Saturday 14:30–16:00 Session, and she needs only one of her two seats. She has the confirmation email with its Manage link.

1. She opens the Manage link. Manage booking shows the Booking and what she can change.
2. She chooses to give up 1 of her 2 Seats.
3. A confirming step shows what will happen: 1 Seat given up, a Voucher worth NOK 250, valid for one year, no money back. Nothing has changed yet (FR-25).
4. She confirms.
5. **Climax:** the result page confirms the change and shows the email with her Voucher code, value and expiry date. She has lost nothing but the seat she could not use.
6. Later she books again and enters the code in the Voucher field on Review.

Failure: within 12 hours of the start, the Manage page still shows the Booking, and every Change is refused with the reason. If she has lost the email, she enters her Booking reference and email on My booking, gets the same reply either way, and a new Manage link is emailed. Move Seats follows the same steps, and a partial move shows the new Booking's reference and email on the result page (FR-26).

### Flow 5: UJ-5. Olav books a whole sauna for a family reunion

*If time.* Olav wants privacy for 10 relatives on a Sunday morning. He is anonymous, on Landing.

1. He chooses **Private sauna** and picks Sunday.
2. The page lists each Sauna that can be booked whole that day, as Sauna options with size, price and free Sessions. No price is set yet (see Open Items).
3. He picks 10:00–11:30 in Kajo, the 12-seat Sauna 3.
4. Details are as in Flow 1. Review adds that the Sauna is not held while he pays, and he pays.
5. **Climax:** Confirmation names Kajo and the Session. It is his family's, and nobody else can book it or a Seat in it for that Session.

Seats left for that Session drop by 12 at once. He can cancel for a refund or a Voucher, or move it, until 72 hours before the start.

Failure: if the Seats already booked would no longer fit in the Saunas ahead of Kajo, Kajo is not offered, though Lumo may be. If someone takes Kajo while he pays, nothing is charged and he is told so.

### UJ-6. Katja closes Sauna 3 for repairs

Out of scope for this round. The blocking calendar belongs to §4.13 (PRD §7) and is sketched when that work comes near.

## Open Items

Nothing here has been decided unless marked closed. Every `[ASSUMPTION]` above is a working default for the build until Lisa confirms or changes it.

### Content that does not exist yet

The mock's bracketed text and flat image blocks are placeholders, not content. The PRD says the Core website is complete only when every Core page has final copy and images in the §6 look, with no placeholders (§10.1). The Core website is therefore **not complete** until all of this exists:

1. Venue description, a few lines (Landing).
2. One line for each of the four Saunas (Landing, FR-1).
3. The swimwear rule. FR-1 refers to it, but no rule is defined.
4. Fictional address and contact details (FR-1, FR-5). Only `admin@saunaloyly.example` exists.
5. Terms text. Required contents are in FR-5. It should also cover the steps, how to correct mistakes and the contract language (addendum D). The part shown on Review must stay short, about six lines at most, or Pay leaves the first view at 1366 × 768. The rest belongs on the Terms page.
6. Privacy notice text. Required contents are in FR-21. Check the "no consent banner" claim against the session cookie (extract §14, C15).
7. Real images, each AI-generated or freely licensed and in the asset register (DR-3): hero, sauna from outside at the water; towels on the bench; one image per Sauna (lauteet, kiuas and stones, kiulu and kauha, the door); vihta on a wooden wall.
8. Alt text for each image.
9. Logo and favicon. None exists, and the Wordmark is typeset text. Decide whether that is enough.

### Decisions for Core

10. Closed by Lisa: all wording and the date format in Voice and Tone are accepted, and may be adjusted during the build.
11. Closed by Lisa: "A booking cannot be changed or refunded." "Online" is dropped, because no other route exists.
12. Closed by Lisa: "Bathe with caution, and never alone" stays. The saunas are shared, so a Guest with 1 seat is not alone.
13. Closed by Lisa: reception finds the Booking by name and email in the day's Booking list, and no new function is added. Confirmation asks the Guest to keep the reference.
14. Keyboard order on Book seats: test against WCAG 2.4.3 (see Accessibility Floor).
15. JavaScript reliance: the site is an SPA, and addendum E warns against a JavaScript-only calendar (extract §14, C13). Typed date still applies. No no-script behaviour is specified.
16. Closed by Lisa: the Administrator does not cancel single Bookings in Core. The Booking list stays read-only.
17. Closed by Lisa: Details, Review, Confirmation and Booking list have key-screen mocks. Terms, Privacy notice, Sign-in, Outbox and the narrow layout are spine only.
18. Closed by Lisa: guest copy uses plain sentence case, with seats, saunas and session in lower case. Only names such as Rauha and Before you come take capitals. The PRD and code keep theirs.

### If-time states left to the designer (PRD §7)

19. Manage page after a Voucher: what remains shown if all Seats were given up.
20. Manage page after a Venue cancellation.
21. Manage page after the end of the Session. FR-25 says the link shows the Booking until then, and the page after that is undecided. It may simply be "This page is not available."
22. Wording of the reason shown after the Cutoff.
23. A Voucher that covers the whole total, where "Pay NOK 0" needs other wording.
24. A resend refused by the rate limit. FR-34 requires the same response for match and no match, so check how the two fit together.
25. Remedy page after the choice or after 30 days. Depends on FR-42 in §4.13.
26. A Seat taken by another Guest while the details are entered, once Holds exist. Core treats this at Pay (Flow 1).

### Other If-time gaps

27. Private sauna prices are not set (Q3). Flow 5 and the Sauna option cannot be finished without them.
28. Hold resize: FR-35 says the Guest is told when extra Seats are not free, while no page may mention a Hold. Wording is needed that does both.
29. How a Guest reaches their own Bookings once signed in, and where sign-in lives apart from the Sign-in choice.
30. Which emails a Guest sees for Gift cards and account links (Step 2 and §4.12). FR-17 names no page.

### PRD impact

Changes or confirmations the PRD needs. None have been made.

1. **Q2 closed by Lisa:** intuitiveness has no separate measure. FR-22 and FR-23 are the only checks. Close §12 Q2 with this answer.
2. **Reception is a new fact.** The Venue has a reception in Core, and the Guest gives the Booking reference there. Add to FR-8 ("what happens next") and to §3 or §2. Reception staff are not an actor in the PRD; the assumption is that they use the Administrator Booking list.
3. **Session as the UI word.** Guest-facing word in all UI copy and emails, including Administrator pages. The PRD keeps Window, but it needs a line in §3 and §6. FR-1's "changing time is part of the Window" becomes "your session" in the UI, and the example wording in FR-3 and §7 needs the same reading.
4. **FR-3 one total.** FR-3 reads as a total per Window. Agreed reading: one total, for the chosen number, visible for the chosen Window, in the rail. It holds while price is equal across Windows in v1, and needs to change if per-Window prices ever arrive.
5. **Core change statement.** Terms and confirmation say "A booking cannot be changed or refunded." with no contact route. FR-5's "online" implies another route, so reword FR-5.
6. **Details and review are two pages.** PRD §7 lists one page, and FR-5 leaves it open. Record the choice.
7. **Session schedule location.** FR-1's schedule is on Book seats, not Landing. FR-1 allows this, so no change is needed, but the §4.1 summary should not be read otherwise.
8. **The Book action.** §4.11, FR-35 and FR-37 name a Book action. No Core page has one. It is the Continue action on Book seats, and the PRD should say so, or say "Continue".
9. **Journey times.** UJ-1, UJ-2 and UJ-3 use times not on the seed schedule (extract §14, C1). This spine uses seed times. Update the journeys or note it.
10. **Administrator address.** UJ-3 says a Guest who types it "is refused". The design sends them to Sign-in. FR-20 still holds, because the API refuses.
11. **Sauna names.** UJ-5 says Sauna 3 and this spine says Kajo, matching §3. Consider aligning the journey.
12. **Browser-session expiry during a booking** is missing from the §7 list of states. Consider adding it.
13. **New states need server support (architecture).** The server must report "already started", the end of the horizon and the horizon length, because the SPA may not use the browser clock (AD-4). The deadline-passed and too-few-Seats refusals need codes with facts in the code table (AD-16).
14. **Confirmation copy with Session (architecture).** The `content/` text shared by page and email (AD-12) should use the UI word.
15. **Q7 closed by Lisa:** no Administrator cancel of a single Booking in Core. Close §12 Q7 with this answer.
