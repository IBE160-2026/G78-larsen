# Devil's Advocate Review — Capacity, Blocking and Concurrency Rules

*Reviewed 2026-10-30: `prd.md` (draft, updated 2026-10-30) and `addendum.md`, checked against the capacity research (INV-1 to INV-7, catalogue A–I). P L… = prd.md, Add L… = addendum.md, memlog L… = `.memlog.md`. Unless a scenario says otherwise: Saunas 1–4 = 7, 10, 12, 15 (44 Seats), Fill order 1→4, Placement written [S1,S2,S3,S4], "—" = Whole-sauna-booked or Blocked.*

## Verdict

The arithmetic core holds. The strict Room-ahead rule, derived Placement and the Core atomic check survived every scenario that runs as a single Guest request, and the catalogue numbers the PRD quotes (A2, A6, A7, B1–B3, D1) check out. The rule system breaks where state changes outside a Guest's request: held Seats are counted in Seats left but by no rule that lowers capacity, Capacity and Window edits are neither serialised with Bookings nor limited to future Windows, and time-based rules (release, Hold expiry, Booking deadline) have no defined trigger or evaluation instant. Four paths can put more people in the rooms than they hold (ADV-1, ADV-2, ADV-4, ADV-11), and most fixes are one or two sentences.

## Findings

### Critical

#### ADV-1 Held Seats count in Seats left, but in no rule that lowers Seat capacity (glossary P L134; FR-10 P L276; FR-35 P L576, L579; FR-38 P L623; FR-40 P L656; FR-41 P L670; FR-3 P L194; FR-16 P L334) — decided (D3, D8, F1: memlog L27)
- **Scenario** (If time 5 + 7):
  1. Window W, Saturday 15:00–16:30, has 25 Seats booked: [7,10,8,0]. Seat capacity 44.
  2. 10:00: Guest G presses Book for 6 Seats and gets a Hold until 10:10. Seats left = 44 − 25 − 6 = 13.
  3. 10:02: the Administrator marks Sauna 4 Whole-booking-only for W. Held Seats are not placed (INV-2, P L524, places Seats booked only), so Sauna 4 holds no Seats and D8 allows the mark. Seat capacity becomes 29. Seats left = 29 − 25 − 6 = **−2**.
  4. 10:05: G pays inside her Hold. 25 + 6 = 31 > 29.
  - A Block of Sauna 4 gives the same result. 25 ≤ 29, so D2 applies, and the preview (P L652) reports that no Booking loses.
- **What the rules say:**
  - P L134: Seats left is "Seat capacity minus the Seats booked …, and also minus the Seats held".
  - P L276: "Seats left never goes below zero".
  - P L576: the Seats "are held for that Guest for 10 minutes".
  - Every rule that lowers Seat capacity tests booked Seats only:
    - D8, P L670: "refused while Seats are placed in the Sauna";
    - D3, P L656: "If Seat capacity falls below the Seats booked";
    - F1, P L623: "more Seats booked than its Seat capacity".
  - Only FR-29 (P L501) adds "plus the Seats held".
  - FR-36 (P L587) gives an outcome only for a payment "after its Hold expired". A valid Hold that no longer fits has no outcome. P L571 ("the atomic check of FR-10 still applies") points to a refusal, while P L576 points to G keeping the Seats.
  - **Phase leak into the Core:**
    - P L194 ("Seats left equals Seat capacity minus Seats booked") becomes false once Holds exist.
    - P L334 lists capacity, booked and left, but not held, so the Administrator's numbers stop adding up.
    - P L579 ("other Guests' Seats left") makes Seats left depend on who is looking. FR-3's "matches the Administrator's booking list" then cannot hold for the Guest who holds the Seats.
- **Consequence:**
  - The architect must guess G's outcome. The candidates are:
    - book G, so the Window overflows and FR-42 cancels her a second later as the latest Booking;
    - charge G, then refund her;
    - refuse G before charging her.
  - Seats left shows −2, or is silently clamped to 0.
  - The Administrator was told that nobody is affected.
- **Fix:** add to FR-35:
  > "Held Seats count as booked for every rule that compares Seats with Seat capacity (FR-10, F1, D3, D8, FR-42), and they are placed like booked Seats (INV-2: Seats placed = Seats booked + Seats held). When an Administrator action leaves too little room, Holds end first, latest first, before any Booking loses. The Guest is told at the payment step and is not charged."
  - Alternative: the action is refused until the Holds have ended (at most 10 minutes).
  - Change P L194 to "minus Seats booked and Seats held".
  - Add "Seats held" to P L334.
  - Say whether the holder's own view counts their Hold as available.

#### ADV-2 A Capacity decrease is not serialised with Bookings, so F1 passes and capacity is still exceeded (FR-38 P L623; FR-32 P L545; Add L8, L17–19, L28; §10.3 P L915) — decided (F1: memlog L27)
- **Scenario** (If time 7):
  1. W has 40 Seats booked: [7,10,12,11]. Seat capacity 44.
  2. 10:00:00.000: the Administrator lowers Sauna 2 from 10 to 6. F1 reads W: 40 Seats booked against a new Seat capacity of 40, so the change is allowed.
  3. 10:00:00.005: a Guest books 3 Seats in W. Its atomic check still reads Sauna 2 = 10 (Seat capacity 44), and accepts, since 43 ≤ 44.
  4. Both commit. W has 43 Seats booked and a Seat capacity of 40. INV-1 cannot hold, and FR-42 then cancels the Guest who has just paid.
- **What the rules say:**
  - FR-32 (P L545) lists the Administrator actions that are serialised with Bookings: "Blocks, lifted Blocks, Whole-booking-only marks and releases". Capacity changes and Window edits are missing, and a list like this reads as complete.
  - Addendum A puts the lock on the Window: the check "runs inside one serialised transaction per Window" (Add L18), and "the Window is the natural lock unit" (Add L19).
  - A Capacity change writes one Sauna row but affects every future Window, so it takes no Window lock.
  - With Seat capacity derived from the Saunas (Add L28) and the Read Committed conditional update (Add L8), the two transactions above are a write skew.
    - SQLite's single writer (Add L11) or Serializable isolation (Add L9) would catch it.
    - Read Committed, the primary pattern, does not.
  - F1 (P L623) checks first and writes afterwards. It is correct only if the check and the change form one atomic step with Bookings.
- **Consequence:**
  - FR-10, the central guarantee, breaks as soon as Capacity can be edited.
  - The Core design in Add L17 ("Seat capacity per Window is fixed") stops being true without anyone noticing.
- **Fix:**
  - FR-32, add:
    > "A Capacity change, and every Window edit, is serialised with Bookings, Holds and Changes in every Window it affects; F1's check and the change are one atomic step. In Step 2 the same applies to the Gradual-opening maximum."
  - FR-38, add:
    > "A Capacity change applies only to Windows that have not started."

    See ADV-9.
  - §10.3: add "how per-Window Capacity is stored once Capacity can change" to the If-time choices that shape the Core data model.

### High

#### ADV-3 The data-store refusal silently stops at If time 3 (FR-10 P L277; §4.3 P L268; §1 P L33; Add L16–18) — decided (P L268 "decided 2026-10-27"; brief addendum L185)
- **Scenario:**
  1. Core: in the design of Add L17, each Window has one counter with a CHECK of booked ≤ 44. FR-10's test switches off the application check and writes a 45th Seat, and the store refuses it.
  2. If time 3: Sauna 4 is Whole-sauna-booked in W, so Seat capacity is 29. A write that skips the application check sets booked = 30. The CHECK still allows up to 44, so the store accepts it.
  3. Add L18 confirms this: once Whole-sauna bookings and Blocks change Seat capacity, "the research found no store-level constraint. The check then runs inside one serialised transaction per Window".
- **What the rules say:**
  - P L268 says the data store refuses "so the guarantee does not rest on application code alone".
  - P L277 says "How the same guarantee is enforced once Whole-sauna bookings and Blocks change Seat capacity is an architecture decision". The phrase "the same guarantee" contradicts Add L18: from §4.9 on, the guarantee rests on application code alone.
  - The test is undefined as well. "Even when the application's own check is bypassed" could mean:
    - calling the data layer without the check; or
    - a raw insert into the Booking table, which a separate counter never sees.
- **Consequence:**
  - Either the Core enforcement is rewritten at If time 3, against P L33 ("grow it feature by feature without rewrites"), or the brief's requirement is quietly dropped.
  - The examiner reads a guarantee that holds for the Core only.
- **Fix:** ask Lisa to choose one:
  - (a) Keep the store-level refusal in every phase:
    > "In every phase, the data store refuses a write that leaves Seats booked above Seat capacity in a Window."

    This works if Seat capacity is kept per Window. Every step that changes it (Whole-sauna booking and cancellation, Block, lift, mark, release, Capacity change) updates it in the same transaction, under a CHECK of Seats booked ≤ Seat capacity. This is the reviewer's inference. The Room-ahead rule and Holds still need the serialised transaction.
  - (b) State that the refusal is a Core guarantee only:
    > "The data-store refusal applies in the Core. From §4.9 on, the guarantee rests on one serialised transaction per Window and on the model-based test."
  - With either option, define the test:
    > "A Booking written through the data layer with the availability check switched off is refused."

#### ADV-4 Time-based rules have no trigger model: release is both a clock condition and a serialised event (glossary P L140; FR-41 P L671; FR-31 P L522; FR-32 P L545; FR-39 P L641; FR-42 P L681; FR-47 P L738; FR-49 P L759; NFR-1 P L795; Q9 P L951) — decided (06:00 rule: memlog L29) + assumption (P L641)
- **Scenario A (the laptop is off at 06:00):** Sauna 1 is Whole-booking-only for Saturday 18:00. The platform runs locally on a laptop (NFR-1), and Lisa starts it at 09:00.
  - If release is an event fired at 06:00, it never fires, and Sauna 1 stays out of Seat sales all day.
  - If release is a clock condition, Sauna 1 opens for Seats as soon as the platform starts.
  - The same question applies to the 30-day default refund (P L681), the Send-time email (P L738, Step 2) and deleting expired codes (P L759).
  - Only Holds have an answer: they stop counting "whether or not any cleanup has run" (P L571).
- **Scenario B (a stale clock exceeds capacity):** Sauna 1 is Whole-booking-only. Before the release, 37 Seats are booked, [—,10,12,15], so the Window is full.
  1. 05:59:59.990: transaction T_W starts a Whole-sauna booking of Sauna 1 and does its reads.
  2. 06:00:00.000: transaction T_S books 1 Seat. By the clock, Sauna 1 is now released, so Seat capacity is 44. W now has 38 Seats booked, [7,10,12,9]. T_S commits at 06:00:00.040.
  3. T_W takes the Window lock and asks "is Sauna 1 released?" using its transaction time. In PostgreSQL, `now()` is the time the transaction started, here 05:59:59.990. The answer is no, so under P L501 the unreleased Sauna "skips this test", and T_W commits.
  4. Sauna 1 is now Whole-sauna-booked, and Seat capacity is 37 with 38 Seats booked.
- **Scenario C (marked again after the Release time):** Sauna 4 is released at 06:00. At 08:00 the Administrator marks it Whole-booking-only again. D8 allows this, since Sauna 4 holds no Seats.
  - Nothing says whether Sauna 4 is released again at once (06:00 has passed) or never (the release already happened).
  - A Block that spans 06:00 and is lifted at 10:00 raises the same question.
- **What the rules say:**
  - P L140 defines the Release time as "the time at which … becomes open for Seats", which is a clock condition.
  - Three places treat release as an event instead:
    - P L522: "After every … release";
    - P L545: "releases are serialised with Bookings";
    - P L641: "when a booking or release happens".
  - Q9 (P L951) names "the data store's clock" for Holds only, and does not say at which moment the clock is read.
- **Consequence:**
  - The architect has to pick one model, and each fails differently:
    - as an event, a release silently never happens while the laptop is off;
    - as a clock condition, the race in Scenario B can exceed capacity.
  - "Hold expiry exactly at payment" has no defined boundary to test.
- **Fix:**
  - §5, add:
    > "Every time-based rule (Release time, Hold expiry, Booking deadline, Cutoff, Send time, remedy deadline) is evaluated on the data store's clock at the moment the request runs its serialised check, after its lock is taken. A time-based effect that writes data (a release, a Send-time email, a default refund, deleting expired codes) is applied by the first request or start-up after its time, so it also happens if the platform was not running."
  - FR-41, add:
    > "A mark set after that day's Release time keeps the Sauna out of Seat sales until the mark is removed."

    The alternative is to refuse such a mark.

#### ADV-5 A Hold stretches the Booking deadline past the decided 45-minute cap, and past the end of the Window (FR-35 P L576, L584; FR-36 P L587–591; FR-39 P L634, L642; glossary P L142; FR-18 P L360) — decided (45-minute cap: memlog L44) + assumption (P L642)
- **Scenario** (If time 5 + 7):
  1. The Booking deadline is set to its maximum, 45 minutes after the start. W runs 15:00–16:30, so its deadline is 15:45.
  2. 15:44: a Guest presses Book for 2 Seats. The deadline applies to Holds (P L642) and she is in time, so she gets a Hold until 15:54.
  3. 15:52: she pays inside her Hold. Both readings break a rule:
     - If the deadline is checked again (P L360 rejects a Window "past its Booking deadline"), she is refused although her Seats were held for her.
     - If it is not, a Booking is made 38 minutes before the Window ends, against "never later than 45 minutes before the Window ends" (P L142).
  4. Variant: she walks away, and the Hold expires at 15:54. At 16:40, after the Window has ended, she presses Pay.
     - P L584: "Expiry never discards what the Guest has entered. The Guest can still pay, and FR-36 decides the outcome."
     - FR-36 (P L587) creates the Booking "only if the Seats are still free". In an ended Window they are.
     - FR-36 never mentions the Booking deadline.
  - The default deadline, 5 minutes after the start, has the same problem: a Hold made at 15:04 runs past 15:05.
- **What the rules say:** the deadline "applies to … Holds" (P L642), but nothing says whether a valid Hold may finish after it, and FR-36 has no deadline condition at all.
- **Consequence:**
  - The architect must choose between three outcomes:
    - Holds are worthless in the last 10 minutes before the deadline;
    - Bookings are made after the decided cap;
    - Bookings are made for Windows that are already over.
  - CT-5 has no case for a payment that arrives after the deadline.
- **Fix:** ask Lisa to choose one:
  - (a) Holds end at the deadline:
    > "A Hold never outlasts the Booking deadline. A Hold made less than 10 minutes before the deadline ends at the deadline."

    This keeps the decided cap literal. The deadline is arguably a real-time limit, so the WCAG 2.2.1 note in FR-35 still holds.
  - (b) A valid Hold may finish after the deadline. The cap then applies to when the Hold was made.
  - With either option, add to FR-36:
    > "A payment after the Booking deadline with an expired Hold never creates a Booking. It is refunded (simulated), and the Guest is told why."

#### ADV-6 "The latest Booking" is undefined for Whole-sauna bookings and for moved Seats (FR-40 P L656–659; FR-42 P L676–679, L685; glossary P L126, L151; FR-26 P L465; UJ-6 P L112) — decided (D3: memlog L27) + assumption (P L657)
- **Scenario A (which kind of Booking loses):**
  1. W has Seat bookings B1–B5, 4 Seats each, created 1–28 Oct: [7,10,3,—]. On 29 Oct, group G books Sauna 4 whole (20 ≤ 29). Seat capacity is 29.
  2. On 30 Oct the Administrator Blocks Sauna 2. Seat capacity becomes 7 + 12 = 19, so the Window is 1 Seat over.
  3. P L126 says a Booking is "a Seat booking or a Whole-sauna booking", so literally the latest Booking is G. The two possible readings:
     - **G loses.** Cancelling it raises Seat capacity to 34. One Booking is lost: a group of up to 15 people.
     - **Only Seat bookings lose.** B5 goes, leaving 16 ≤ 19. One Booking is lost: 4 people.
  - The two readings also count "as many as needed" differently. Cancelling a Seat booking lowers Seats booked, while cancelling a Whole-sauna booking raises Seat capacity.
- **Scenario B (a moved Booking against a split one):**
  1. Window W2 has B1 (4 Seats, created 1 Oct) and B2 (4 Seats, created 20 Oct).
  2. On 25 Oct, Guest X moves all 4 Seats of BX (created 2 Sep) into W2. BX "keeps its reference" (P L465), so its creation date stays 2 Sep.
  3. The same day, Guest Y moves 3 of the 4 Seats of BY (created 2 Sep) into W2. Those Seats "become a new Booking", BY', created 25 Oct.
  4. A Block then leaves W2 4 Seats over. By "most recently created" (P L657), BY' loses. BX arrived the same day, but counts as the oldest Booking in W2 and is safe.
  - The two Guests did the same thing, and only the split rule decides who loses.
- **What the rules say:** two more cases are undefined:
  - ties between Bookings created in the same second;
  - when the check runs. FR-42 applies when Seats booked "ever exceed" Seat capacity (P L676), but outside D3 and D6 nothing runs the check, including for "failures outside the platform's control" (P L685).
- **Consequence:** the architect must guess which Guests are cancelled. The choice changes how many people lose their visit, and the arithmetic of "as many as needed".
- **Fix:** ask Lisa, then write the answer into FR-42. Recommended:
  > "Only Seat bookings lose; a Whole-sauna booking is cancelled only when its own Sauna is Blocked (D4). 'Latest' means the time the Seats entered this Window: when the Booking was created, or when a move brought them in. Ties go to the later Booking reference. The fallback runs inside the step that lowered Seat capacity."
  - Alternatives:
    - (b) Whole-sauna bookings also lose, in creation order;
    - (c) the Bookings with the fewest Guests lose first.
  - The Whole-sauna part was M-7 in `reconcile-capacity-research.md` L268 and is still open. The moved-Booking part is new.

#### ADV-7 The Block preview is not bound to what the confirmation applies (FR-40 P L652; UJ-6 P L111–112; FR-32 P L545) — decided (D3, the Administrator sees who is affected before confirming: memlog L27)
- **Scenario:**
  1. W has 39 Seats booked: [7,10,12,10]. The latest Booking is B9, with 9 Seats.
  2. 10:00: Katja opens a Block of Sauna 3 for W. The preview shows Seat capacity 32, 7 Seats over, and "B9 loses".
  3. 10:01: Guest Z books 2 Seats in W (Seats left goes from 5 to 3), pays, and gets a confirmation email.
  4. 10:02: Katja confirms. The Window now has 41 Seats booked against 32, so it is 9 over. Z, now the latest Booking, loses, and so does B9. Z is cancelled a minute after paying, and Katja never saw Z in the preview.
  5. The reverse also happens. If a Guest gives up 7 Seats at 10:01, nobody needs to lose, yet Katja has just approved B9's loss.
- **What the rules say:**
  - P L652: "Before confirming, the Administrator sees … any Booking that would lose its place."
  - FR-32 (P L545) serialises the Block with Bookings. The preview and the confirmation are two separate requests, and nothing ties them together.
- **Consequence:** the decided promise cannot be tested once Bookings arrive in between, and the Guest who loses can be one who booked while the preview was open.
- **Fix:** FR-40, add:
  > "The confirmation applies the Block only if the Bookings that would lose are exactly those in the preview. Otherwise nothing changes, and the Administrator gets a fresh preview."

#### ADV-8 Voucher-funded Bookings turn refund paths into Voucher payouts (FR-28 P L484–486; FR-27 P L475–478; FR-36 P L591; FR-42 P L680–681; FR-33 P L552; glossary P L146; Add L126) — decided (refund or Voucher on cancellation by Saunalöyly: memlog L27, L32; Add L81) + assumption (P L484; P L681, already queued in memlog L37; new angle)
- **Scenario:**
  1. Ingrid gives up 2 Seats (NOK 500) and gets Voucher V, worth NOK 500, valid until 1 Nov 2027. P L478: "No money is refunded."
  2. She books 2 Seats in W and pays the whole amount with V (FR-28).
  3. A Block makes her Booking lose (D3). On the remedy page (P L680) she picks a refund and receives NOK 500 in (simulated) money. A Voucher has been paid out in money, against P L485: "A Voucher is never paid out in money". If she never chooses, the 30-day default (P L681) does the same.
  4. Variants that are also undefined:
     - **Mixed payment:** NOK 250 by Voucher and NOK 250 by Simulated payment. Is NOK 500 refunded in money, or NOK 250 in money with NOK 250 put back on V? And what if V has expired in the meantime?
     - **Late payment:** P L591 says "the payment is refunded", but the Voucher share is not a payment.
     - **Whole-sauna cancellation:** FR-33 (P L552) has the same split.
  5. **A Voucher that never expires:** V runs out tomorrow. She books a Window 4 weeks ahead with V, gives the Seats up before the Cutoff, and gets a new Voucher "valid for one year from issue" (P L146, P L476). Done once a year, this keeps V alive for ever, and each cycle takes the Seats out of sale for weeks.
- **What the rules say:** P L680 offers "a refund" for any cancellation that Saunalöyly causes. Neither FR-28 nor FR-42 says what a refund means for the part of a Booking that a Voucher paid.
- **Consequence:**
  - The money rules disagree, and the architect has to invent a payment-split model.
  - A test that a Voucher is never paid out fails on the remedy path.
- **Fix:** FR-28, add:
  > "A refund returns money only for the part paid by Simulated payment (in Step 2, the Gift-card part goes back to the card). The part paid by Voucher goes back to a Voucher with its original expiry, or 30 days after the refund if that is later. A Voucher issued for Seats that were paid by Voucher keeps the earliest expiry of the Vouchers used."
  - The unfair-terms note (Add L126) is about money the Guest paid, not about Voucher value.

#### ADV-9 Window edits, deletions and admin edits to started or ended Windows have no rule (FR-38 P L619–626; FR-40 P L650; FR-3 P L199; FR-16 P L334; FR-42 P L676, L681; Add L22) — decided (F1, F2: memlog L27)
- **Scenario A (editing a Window that has Bookings):** W, 15:00–16:30, has 20 Seat bookings and a Whole-sauna booking of Sauna 4. The Administrator changes it to 15:30–17:00 (P L619, "create and edit Windows"). Nothing says what follows:
  - Are the Guests moved, emailed, or offered the remedy?
  - Cutoffs and Send times move with the new start, so a Guest can lose or gain the right to a Change.
  - A Guest on the Manage page who saw 15:00 confirms a move into W after the edit.
  - A Guest on the review page presses "Pay NOK 500" for a Window that has changed.
  - Deleting W has no rule either.
- **Scenario B (a Block in the past):** Katja picks last Tuesday by mistake, or to record that a Sauna was closed that day.
  - P L650 says "A Block affects every Window that overlaps its period" and sets no lower bound.
  - D3, D4 and D6 then cancel and refund visits that have already happened.
  - The remedy link "works for 30 days, even after the Window has ended" (P L681).
- **Scenario C (rewriting history):** the Administrator lowers Sauna 4 from 15 to 10.
  - F1 (P L623) checks future Windows only. With one stored Capacity and derived Placement (Add L22), last Saturday, which had 44 Seats booked, now shows Seat capacity 39 and Seats left −5 in the booking list (P L334).
  - FR-42's "ever exceed" (P L676) now applies to a past Window.
  - F2 (P L624) keeps the old Fill order for started Windows. With derived Placement and a single stored Fill order, nothing keeps it.
- **Scenario D (a price change during checkout):** the price rises from NOK 250 to 300 while a Guest is on the review page. P L199 says "the total shown … is the amount charged", and P L625 says "A price change applies only to new Bookings".
- **What the rules say:** FR-38 has consequences only for Window length and overlap, Capacity decreases (F1), the Fill order (F2), prices and Windows beyond the horizon. FR-40 has no time limit.
- **Consequence:**
  - The If-time-7 epic has no acceptance rule for its most dangerous screen.
  - The data model has to guess whether Capacity, Fill order and prices are stored per Window or with the date they take effect, and §10.3 (P L915) does not list that choice.
- **Fix:**
  - FR-38, add:
    > "A Window with Bookings, Holds, Whole-booking-only marks or Blocks cannot be edited or deleted. To close it, the Administrator Blocks all Saunas (D6), which applies the remedy. Capacity, Fill order and prices apply only to Windows that have not started; a Window keeps the values it started with. The amount charged is the total shown on the review page. If the price changed in the meantime, nothing is charged and the new total is shown."
  - FR-40, add: "A Block never covers a Window that has ended."
  - §10.3, add: "the values a Window keeps once it starts".

#### ADV-10 What a retry returns is undefined: a Guest can be charged and told "no Seat is free", and Changes have no duplicate guard (FR-6 P L236; FR-8 P L257–258; FR-11 P L284–285; FR-14 P L306; FR-17 P L347; FR-25 P L458) — assumption (P L258, which removes the Guest's way back)
- **Scenario A (Core):**
  1. W has 1 Seat left. Aino presses Pay. The atomic step books the Seat and writes her email to the Outbox, but her Wi-Fi drops and the response is lost.
  2. She presses Pay again. FR-6 (P L236) forbids a second Booking, but it does not say what the repeat returns. A naive repeat runs the check again and finds 0 Seats left. P L284 then says the losing Guest "is told that no Seat is free, is not charged". She is told exactly that, although she has been charged.
  3. In the Core she has no way to find out what happened:
     - her email exists only in the Outbox (P L257: "The Guest sees no other email"; P L347);
     - the Core confirmation has no Manage link (P L258);
     - resending the link is If time 4.
- **Scenario B ("the same review"):** FR-6 does not say how the server recognises a repeat. If it matches on the request's content, it blocks a Guest who really wants two identical Bookings, which FR-9 allows.
- **Scenario C (FR-14 against FR-11):** with a limited number of retries, the losing Guest can end with "please try again" (P L306) instead of "no Seat is free" (P L284). If both requests use up their retries, nobody wins. The 100-repetition race test (P L285) then fails at random.
- **Scenario D (If time 2):** a Guest double-clicks "Give up 1 Seat" or "Move 2 Seats". A Change needs a confirming action (P L458), but nothing stops it from running twice, so she gets two Vouchers or moves 4 Seats.
- **What the rules say:** P L236: "never creates two Bookings or two charges". No rule says what the repeat shows, and no rule covers repeated Changes.
- **Consequence:** in the Core, the product's main promise ("certain the seats are mine", §2.1) fails on an ordinary network error, with no way for the Guest to recover.
- **Fix:**
  - FR-6, add:
    > "Each review page carries a one-time key. A repeat with the same key returns the first outcome: the same confirmation page, or the same refusal. A different key is a new Booking."
  - FR-25, add: "The same applies to every Change confirmation."
  - FR-11: the race test asserts exactly one Booking, accepts either message for the losing Guest, and requires that one of two racing requests always succeeds.

#### ADV-11 "Never partly overlap" allows nested and identical Windows, which double the rooms (glossary P L122; FR-13 P L294–300; FR-38 P L622) — decided (Venue-wide Windows without overlap, E1/E3: Add L68)
- **Scenario:**
  1. The seed (Core) or the Administrator (If time 7) creates W1, 15:00–16:30, and W2, 15:00–18:00, as a long session. P L622 allows "another length". W2 contains W1, and it is unclear whether that counts as "partly overlapping".
  2. Or the seed command runs twice and creates two identical Windows at 15:00–16:30. They overlap fully, not partly.
  3. P L300: "Windows are independent". Each Window has a Seat capacity of 44, so 88 Seats are sold for 44 places from 15:00 to 16:30. This is E1's failure, inside the Core.
- **What the rules say:**
  - P L122, L295, L298 and L622 all say "partly".
  - FR-13's tests cover only a partial overlap and two Windows that touch (E1, E2).
- **Consequence:** the Core can oversell the physical rooms while FR-10 holds in each Window. Nobody notices, because each Window's own count is correct.
- **Fix:**
  - Change the rule to: "No two Windows overlap; a Window may start exactly when another ends."
  - Add tests: identical and nested Windows are rejected, and a second seed run creates no new Windows.
  - This was M-4 (`reconcile-capacity-research.md` L265) and is still open. The second seed run and the "another length" reading are new.

### Medium

#### ADV-12 Gradual opening: under the glossary, a second Sauna can never open (glossary P L132–133; FR-50 P L766–767; FR-3 P L195; FR-12 P L288) — neither
- **Scenario** (Step 2): Gradual opening is on, with the maximum at all Saunas. Only Sauna 1 is open, so Seat capacity is 7, because P L132 counts only a Sauna that is "already opened".
  1. A books 5 Seats, which leaves 2.
  2. B wants 3 Seats. FR-3 shows the Window as unavailable, and FR-12 rejects the request.
  3. FR-50's "A Booking larger than the room left in the open Saunas opens the next Sauna" is therefore never reached, and the Window is capped at 7 Seats.
- **What the rules say:** P L132–133 define Seat capacity over opened Saunas only, while P L766 needs capacity beyond them in order to open the next Sauna. Several cases are also undefined:
  - Turning the mode on, or lowering the maximum, when a Window already has Bookings. For example, W has 20 Seats booked, [7,10,3,0], and the maximum is set to 1. Seat capacity becomes 7, below 20: is this refused as F1 refuses, or do Bookings lose as under D3?
  - Turning the mode on after the Send time. Seat bookers then hold codes for Saunas that are now closed (the H18 gap).
  - A Booking that needs two more Saunas to open.
- **Consequence:** the Step 2 mode cannot work as written. Building it forces a redefinition of a glossary term that the Core and If time already use.
- **Fix:**
  - Glossary P L132: drop the Gradual-opening clause.
  - FR-50, add:
    > "Seat capacity counts every Sauna that may open, up to the maximum. Whether a Sauna is opened decides only which Door codes are sent. Turning the mode on, or lowering the maximum, is refused while a future Window would have more Seats booked than its Seat capacity. It applies only to Windows whose Door-code email has not been sent."

#### ADV-13 Door codes: no general rule for a Sauna whose access changes after the Send time (FR-46 P L729; FR-47 P L738–741; FR-48 P L748–751; FR-50 P L768; brief addendum L73) — assumption (H14, P L750, already queued in memlog L37; new angle) + decided (H10, H13: memlog L27)
- **Scenario** (Step 2; the codes for the 15:00 Window go out at 14:40):
  1. **A release after the Send time:** Sauna 4 is Whole-booking-only, and the Release time is set to 14:50.
     - At 14:40, Seat bookers get the codes for Saunas 1–3 (P L729).
     - At 14:50, Sauna 4 is released and Seats are counted into it, but no rule sends its code. P L750 covers only a lifted Block, and P L768 only Gradual opening.
     - The brief's general rule ("If another sauna opens for individual seats after the codes are sent … those bookers get an extra email", brief addendum L73) has been narrowed.
     - The same gap applies when a mark is removed, and when a Whole-sauna booking is cancelled and its Sauna is not Blocked. M-12 (`reconcile-capacity-research.md` L276) noted the release case.
  2. **A mark after the Send time:** at 14:45 the Administrator marks Sauna 3 Whole-booking-only. D8 allows it, since Sauna 3 holds no Seats.
     - Seat bookers keep Sauna 3's code and are not told it is now closed to them. P L749 sends a correction only for a Block.
     - P L748 then refuses any group booking of Sauna 3, so the mark achieves nothing.
  3. **The Send time has no bounds** (P L738).
     - Set to 24 hours before the Window, it comes before the Seat Cutoff (12 hours), so Changes happen after the codes have gone out.
     - A move of all Seats into W after its Send time keeps the Booking (P L465). P L739's "A Booking made after the Send time receives its email at once" may then never fire.
     - A Whole-sauna move (FR-33) into such a Window is checked against FR-29 only, not against P L748.
  4. **"Always differ":** P L741 says "Codes for two different Windows on the same door always differ". Taken literally, this covers every pair of Windows ever. A lock with 4-digit codes runs out after 10,000 Windows, and no test can check "always". H6 only needs codes to differ between Windows whose codes are valid at the same time, or are still stored on the lock. H6 itself is not re-argued here.
- **What the rules say:** the extra email exists only for a lifted Block (P L750) and Gradual opening (P L768). The correction email exists only for a Block (P L749).
- **Consequence:** Seat bookers can be told nothing about a Sauna they may now enter, or keep a working code for a Sauna they may no longer use. Both happen without any Guest error.
- **Fix:**
  - Replace P L750 and P L768 with:
    > "Whenever a Sauna becomes open for Seats after the Send time (lifted Block, release, removed mark, cancelled Whole-sauna booking, Gradual opening), every Seat booker of the Window gets an extra email with its codes. Whenever it stops being open for Seats after the Send time (Block, mark), they get the H13 correction email."
  - FR-47, add:
    > "Seats moved into a Window after its Send time get its codes at once (H9). A Whole-sauna move follows FR-48. A new code differs from every code still stored on the door."
  - Bound the Send time, for example to between the Seat Cutoff and the Window start.

#### ADV-14 Holds have no limit per Guest, and Whole-sauna bookings have no Hold (FR-35 P L576–582; FR-7 P L243; FR-34 P L567; FR-29 P L501; glossary P L148) — neither
- **Scenario:**
  1. **A script holds every Seat.** It presses Book for 10 Seats five times in W, so all 44 Seats are held, and it repeats this every 10 minutes. FR-3 then shows "0 seats left" all day. A Hold is made before any name or email is given (P L576, "When a Guest presses Book"). Only the resend has a rate limit (P L567).
  2. **Two tabs.** Ingrid holds 2 + 2 Seats in two tabs and pays in one. The other Hold blocks 2 Seats for 10 minutes.
  3. **Going back.** Ingrid goes back to change 2 Seats to 3. Pressing Back "releases the Hold at once" (P L582), so the new Hold for 3 can fail, and she loses the 2 she had. A failed payment has the same effect: FR-7 (P L243) offers "a way to try again", but the Hold is already gone.
  4. **A slow group loses.** Olav (UJ-5) spends 8 minutes on the details for Sauna 3. Meanwhile, Seat Holds push Seats booked plus Seats held above Room ahead for Sauna 3 (P L501), and his payment is refused. A Seat booker in the same position would have been protected, because a Hold reserves Seats only (P L148).
- **What the rules say:** P L576 creates a Hold on every press of Book, with no limit per session, address or Window, and P L148 limits Holds to Seats.
- **Consequence:**
  - One client can make the Venue look sold out.
  - Ordinary Guests lose Seats by pressing Back.
  - Groups get weaker checkout protection than Seat bookers.
- **Fix:**
  - FR-35, add:
    > "A browser session has at most one Hold per Window. Changing the number of Seats resizes the Hold in one step and keeps the Seats already held. A failed payment keeps the Hold until it expires. Holds per source address are limited `[ASSUMPTION]`."
  - Ask Lisa whether a Whole-sauna booking should hold its Sauna for 10 minutes:
    - (a) yes, and the held Sauna counts in Seat capacity and Room ahead;
    - (b) no, and the review page says that the Sauna is not held.

#### ADV-15 Time periods across midnight and daylight-saving changes are undefined (NFR-3 P L797; glossary P L140–143; FR-2 P L186; FR-16 P L329) — assumption (NFR-3)
- **Scenario:**
  1. **A Cutoff across the spring change.** Daylight saving starts on Sunday 28 March 2027, when 02:00 jumps to 03:00. A Whole-sauna booking for Tuesday 30 March at 15:00 has its Cutoff "72 hours before the start":
     - counted in elapsed hours, the Cutoff is Saturday 27 March at 14:00;
     - counted as the same clock time three days earlier, it is 15:00.

     A test run at 14:30 passes under one reading and fails under the other. The 4-week Booking horizon (P L141) has the same problem across either change.
  2. **Windows in a skipped or repeated hour.** A Window 02:00–03:30 on 28 March 2027 starts in an hour that does not exist. On 31 October 2027, 02:30 happens twice, and "a Window keeps its local clock times" (P L797) does not say which one.
  3. **A Window across midnight.** For 23:30–01:00:
     - which date do the date choice (FR-2) and the booking list (FR-16) file it under?
     - is "06:00 on the day of the Window" the day it starts?
- **What the rules say:** NFR-3 requires these days to work but says only that Windows keep their clock times. It does not say whether offsets are counted in elapsed hours or on the clock.
- **Consequence:** boundary tests for the Cutoff, the Booking horizon and the Release time cannot be written. No daylight-saving change falls between 27 Oct and 15 Dec 2026, so the risk is confined to tests that use made-up dates.
- **Fix:** NFR-3:
  > "Offsets (Booking horizon, Booking deadline, Cutoffs, Send time, Hold length, the 45-minute cap) are elapsed time from the Window's start or end. The Release time is a clock time on the date the Window starts. A Window belongs to the date it starts. No Window starts or ends inside a skipped or repeated hour."

#### ADV-16 The model-based test checks against an invariant that is false as written, and its list of actions is incomplete (FR-31 P L522–527, L535; FR-29 P L501, L511; NFR-6 P L800) — decided (INV-1 to INV-5 state the rule: research recommendation 1)
- **Scenario:**
  1. **Catalogue B5.** Sauna 2 is Whole-sauna-booked and 9 Seats are booked: [7,—,2,0]. INV-5 (P L527) says "no Sauna earlier in the Fill order has room while a later one holds Seats". Sauna 2 comes earlier, holds 0 of its 10 Seats, so it "has room", while Sauna 3 holds 2. INV-5 is false.
  2. **Catalogue D2.** Sauna 3 is Blocked: [7,10,—,5]. INV-4 requires Sauna 3 to hold 0 Seats, and INV-5 then says it "has room" while Sauna 4 holds Seats, so the two cannot both hold. Checked literally, the test fails on B5, B6 and D2, and in every Window with an unreleased Whole-booking-only Sauna.
  3. **Missing actions.** The trigger list in P L522 leaves out three actions that change Placement:
     - Whole-booking-only marks (listed in P L535);
     - Fill-order changes (F2);
     - Capacity changes (F1).

     This is M-3 (`reconcile-capacity-research.md` L264), still open.
  4. **Mixed phases.** P L535 includes Blocks, marks and releases, which arrive with §4.13 (If time 7), while FR-29 to FR-32 belong to §4.9 (If time 3).
     - §4.9 therefore cannot be "done" with its own test (P L800: "Each story includes its tests as part of being done").
     - Two §4.9 consequences need later items: P L501 needs Holds (If time 5), and P L511 needs marks (If time 7).
- **What the rules say:** the glossary's Room ahead (P L137) is limited to Saunas "open for Seats", but INV-5 is not.
- **Consequence:** the main proof of derived Placement fails on states the catalogue calls correct, and §4.9 has no test it can finish on its own.
- **Fix:**
  - INV-5: "no Sauna that is open for Seats and comes earlier in the Fill order has room while a later one holds Seats".
  - P L522: "After every booking, Change, cancellation, Whole-sauna booking, Block, lifted Block, mark, removed mark, release, Capacity change and Fill-order change".
  - Tag each consequence that needs a later item "(with §4.11)" or "(with §4.13)", and let each item add its own actions to the model-based test.

### Low

#### ADV-17 FR-29's started-Window rule and its §13 index entry disagree about the unreleased Whole-booking-only Sauna (FR-29 P L502; §13 P L975) — assumption (already queued as the F3 reading, memlog L37; new angle)
- **Scenario:** the Release time is turned off. Sauna 4 is Whole-booking-only in W, which starts at 15:00 and has 20 Seat bookings. At 15:02 a group asks for Sauna 4.
- **What the rules say:**
  - P L502 ("The Window has not started, or it has no Seat booking") refuses the group.
  - P L975 ("no Sauna open for Seats can be booked whole") allows it. Sauna 4 is not open for Seats, so no Seat booker can be sitting in it.
- **Consequence:** the Sauna that was held back for groups is the one a late group cannot book, and the architect follows whichever text they read.
- **Fix:**
  - FR-29: "Once the Window has started and has a Seat booking, a Sauna that is open for Seats cannot be booked whole."
  - Add this case to the queued F3 question.

#### ADV-18 Two reconciliation fixes that change rule outcomes are still open (FR-42 P L685; FR-40 P L656, L663; FR-29 P L509, L511) — neither
- **Scenario:**
  - **M-5:** an Administrator Blocks Sauna 3 next Saturday, and D3 cancels a Booking.
  - **M-8:** a group books an unreleased Whole-booking-only Sauna whole.
- **What the rules say:**
  - **M-5:** P L685 says the fallback "exists for Blocks in Windows that have started, and for failures outside the platform's control". But D3 (P L656) and D6 (P L663) apply it to any Block.
  - **M-8:** P L509 says "After the booking, Seats left drops at once by the Sauna's Capacity (B7)". This is false for the Sauna that P L511 allows to be booked whole: an unreleased Whole-booking-only Sauna is not in Seat capacity, so Seats left does not change.
- **Consequence:**
  - **M-5:** an architect who scopes FR-42 by P L685 skips the remedy flow for Blocks in future Windows.
  - **M-8:** the B7 test asserts the wrong number for a marked Sauna.
- **Fix:**
  - **M-5** (`reconcile-capacity-research.md` L266), P L685: "It exists for Blocks that leave too little Seat capacity (D3, D6) and for failures outside the platform's control."
  - **M-8** (L269), P L509: add "for a Sauna that is open for Seats".

## Rules that held up under attack
- **The strict whole-sauna rule.** Room ahead(S) is never more than Seat capacity minus Capacity(S), so a Whole-sauna booking never pushes Seats left below zero. Derived Placement skips S, so later Seat bookings cannot reach it. B1 (20 ≤ 29, then 9 left), B2, B3, B5 and B6 all check out.
- **Fill-order changes (F2).** They cannot break capacity, because Seat capacity does not depend on the order. A Fill-order change that races a Whole-sauna booking leaves INV-1 to INV-4 true, because the Room-ahead test applies only at booking time.
- **D8.** "Refused while Seats are placed in the Sauna" is equivalent to Seats booked ≤ Room ahead(S). A mark therefore never pushes booked Seats over Seat capacity. Held Seats are the exception (ADV-1).
- **Steps that add capacity.** Lifted Blocks (D7), releases and Whole-sauna cancellations only add capacity, so none of them can break an existing Whole-sauna booking.
- **The Core last-Seat race.** The atomic check, all-or-nothing and the store-level refusal give exactly one winner for two requests, under both patterns in addendum A (Add L8, L11). The losing Guest's message is the only gap (ADV-10).
- **Changes between two Windows.** FR-32's cross-Window rule (P L546), together with the fixed lock order (Add L12), prevents both deadlock and double counting.
- **The 45-minute deadline cap.** It works for short Windows: a 40-minute Window closes 5 minutes before it starts, and a 30-minute Window 15 minutes before.
- **Block and Window intervals.** Both are half-open (D5 rewritten), so a Block 16:30–17:00 leaves 15:00–16:30 untouched.
- **Door codes in default mode.** FR-46's code sets and FR-48's rule against taking codes back are consistent with the glossary's definition of open for Seats. The gaps appear only when that status changes after the Send time (ADV-13).
