---
title: 'Input reconciliation: concurrency and smart-lock research vs PRD'
type: input-reconciliation
prd: 'prd.md + addendum.md (draft v1, 2026-10-29 21:20)'
inputs:
  - '.docs/planning-artifacts/research/technical-booking-concurrency-seat-holds-2026-10-27/research.md'
  - '.docs/planning-artifacts/research/technical-smart-lock-door-code-overlap-and-revoke-2026-10-28/research.md'
created: '2026-10-29'
---

# Input reconciliation: concurrency and smart-lock research vs PRD

**Scope.** This checks four things in `prd.md` and `addendum.md`:
- (a) each requirement-level recommendation in the two reports appears as a testable consequence, or the PRD records why not;
- (b) mechanisms stay in addendum A and keep the research's confidence labels;
- (c) sourced and inferred claims are marked correctly;
- (d) the open questions that matter appear in PRD §12.

Items that are decided in `.memlog.md` or the brief addendum are labelled "decided" and not reported as gaps. This was a read-only check: no other file was changed.

**Also checked:**
- both research memlogs, for claim status;
- the digests, with two spot checks: `40P01` in d1 L19, and Stripe "dedupe by event ID" in d2-d3 L12;
- the brief addendum, for decision status, the Seat-hold rule and the concurrency-test rows;
- catalogue groups C and E in the capacity research;
- the session logs and `issues.md`.

**Notation.**
- `CR Lnn` is a line in the concurrency report, and `LR Lnn` a line in the smart-lock report.
- `prd Lnn` and `add. Lnn` are lines in `prd.md` and `addendum.md`.
- `memlog Lnn` is a line in this PRD's `.memlog.md`, and `brief add. Lnn` a line in the brief addendum.
- Status values: captured, partially, missing, contradicted, over-claimed, decided, and n/a (does not need to be in the PRD).

## Verdict

Both reports are carried well:
- All six concurrency recommendations and all six door-code rows (H6, H12 to H15 and the confirmation gate) appear in the PRD or the addendum.
- The PRD body states no throughput figure and names no engine-specific mechanism.
- H6 is deferred, and H12 and the frozen Placement are decided, as the logs record.
- Nothing contradicts a report, and nothing is labelled "high" where a report says low or unverified.

The weak spots are testability and one traceability problem:
- The Core requires the data store to refuse over-capacity writes, but no input asks for that.
- Changes that span two Windows have no concurrency consequence, and the research's lock-order rule was dropped.
- The late-payment path of the Hold cannot be tested as written.
- Two Step 2 rules are underspecified: replacing a shared code (H15), and a forced move under one-Sauna access.

| Status | Rows |
|---|---|
| captured | 22 |
| decided | 4 |
| partially | 12 |
| missing | 2 |
| over-claimed (mild) | 1 |
| contradicted | 0 |
| n/a | 10 |

## 1. Concurrency research (2026-10-27)

### 1.1 Recommendations R1 to R6 (CR L59–66)

| # | Report line | Point | Status | PRD location | Note |
|---|---|---|---|---|---|
| R1 | CR L61 | Bookings never exceed capacity under concurrent requests. The loser gets a clear "no seat free" and nothing is held. Parallel tests prove it. | captured | FR-10 (prd L258–263), FR-11 (L265–271), FR-12 (L273–278), NFR-6 (L761), SM-1 (L863–866) | Fully testable. FR-11 adds 100 repetitions `[ASSUMPTION]` and "not a mock", which matches brief add. L220. |
| R2 | CR L62 | A Hold is stored with an expiry and ignored once expired, even if cleanup has not run (low). | partially | §4.11 description (prd L548), FR-35 (L552–560) | "Whether or not any cleanup has run" is only in the description. No FR-35 consequence tests it: CT-4 (L558) tests expiry, but not with cleanup off. |
| R3 | CR L63 | Payment callbacks are idempotent, and there is a defined outcome when payment arrives after expiry. | partially | FR-36 (prd L562–567), FR-35 (L560), FR-6 (L223) | The outcome is defined and follows the brief's Seat-hold rule (brief add. L58): the payment books if the Seats are still free, and is refunded otherwise. R3's "(no booking, simulated refund)" describes the seat-taken row (brief add. L218), so there is no contradiction. Gaps: the still-free branch exists only as "only if", a necessary condition with no consequence; there is no parallel race test for a late payment; and nothing says how a Simulated payment produces duplicate, late or out-of-order confirmations in a test. |
| R4 | CR L64 | A seat move is atomic and cannot interleave with a Whole-sauna booking. The mechanism is left to the architecture. | partially | FR-26 (prd L445), FR-31 (L509–514), FR-32 (L516–523), FR-33 (L530) | Same-Window cases are covered (C2 to C5, A3), and the mechanism is left to the architecture. A Change that spans two Windows (FR-26 W1→W2, FR-33) is atomic (E5) but has no non-interleaving consequence, and the catalogue has no such case (C1 to C6 and E4 to E5 checked). The brief reads R4 as "a seat change is atomic and cannot interleave with a whole-sauna booking" (brief add. L176). |
| R5 | CR L65 | No TPS or latency figure. Any load-test target is set after measuring and marked unverified. | captured | §4.3 NFR (prd L294–295), NFR-7 (L762), §9 (L827) | None. |
| R6 | CR L66 | Serialization failures and deadlocks are retried a bounded number of times, then the Guest gets a clean error. | captured | FR-14 (prd L287–292), add. L9 | The engine-neutral wording ("temporary conflict") is good. Testing "please try again" needs a forced conflict, and no test switch is stated (FR-7 has one for payment). |

### 1.2 Other findings in the report body

| Report line | Point (research label) | Status | PRD location | Note |
|---|---|---|---|---|
| CR L24, L31 | A conditional UPDATE under Read Committed: one request wins and the loser updates 0 rows. Mechanism high and verified; its application here medium. | captured | add. L8 | The label is intact: "documented and verified … inference (medium confidence)". |
| CR L24, L32, L47 | Serializable as a backstop; retry 40001 (high, [1] verified); keep the check indexed and the transaction short. | partially | add. L9 | The retry on 40001 and 40P01 and the short transaction are carried. `40P01` comes from digest d1 L19, so it is sourced. The line has no confidence label, and "keep the check indexed" was dropped. |
| CR L33 | Never hold a lock across payment; the Hold carries the Guest (low–medium). | captured | add. L10; prd L199, L548 | The label is intact. |
| CR L26, L34 | No defensible throughput number. | captured | NFR-7, §4.3 NFR | None. |
| CR L38 | Lazy expiry plus a sweeper; the sweeper figures are design choices (low). | captured | add. L35–36 | The label is intact. |
| CR L39 | Redis TTL keys as an alternative (low). | n/a | None | An alternative that was not taken, so omitting it is fine. |
| CR L40 | Stripe: duplicates and out-of-order delivery require an idempotent handler. The report says high; the research memlog lists [4] as unverified. The re-check and refund are inference. | partially (label) | add. L37–38; FR-36 (prd L567) | The requirement is captured. But add. L37 sits under "Holds are data (low confidence …)", so it reads as low, while the report says high and the memlog says unverified. "Dedupe by event ID" is sourced (digest d2-d3 L12). L38 correctly labels the re-check as inference. |
| CR L41 | Using the database's `now()` as the single clock avoids clock skew (unverified belief). | missing | None | Not in addendum A. This matters for the FR-35 expiry tests. |
| CR L25, L45, L53 | Taking locks in a consistent order is the best defence against deadlocks. The report says high; the research memlog lists [2] as unverified. | missing | None | The cross-dimension rule at CR L53 has four parts. Addendum A carries three (short transaction, retry, no lock across payment) and drops "locks in a fixed order". That part is needed once one request touches two Windows (FR-26, FR-33) or a Block spans several Windows (FR-40). |
| CR L46, L49 | A per-Sauna aggregate lock, or locking the Saunas' capacity rows in ascending id order (inference). | partially | add. L16–17 | Replaced by "one serialised transaction per Window (inference)" and "the Window is the natural lock unit … still open", which is reasonable with derived Placement. |
| CR L48 | Exclusion constraints cannot express "at most N seats" (unverified belief). | partially (label) | add. L16 | "The research found no store-level constraint" drops the "unverified belief" label. |
| CR L27, L94 | The findings cover PostgreSQL only, are tied to a version, and must be re-checked when an engine is chosen. | captured | add. L12; §12 Q4 (prd L885) | None. |
| CR L57 | Red team was off. | n/a | None | None. |
| CR L82, L84 vs research memlog | The appendix labels [2] and [4] "high", but the research memlog lists both as unverified. | captured (generic) | add. H (L268) | Correct, but the line names neither reference nor what rests on them: [4] supports FR-36, and [2] supports FR-14 and FR-32. No PRD or addendum statement over-claims as a result. |

### 1.3 Open questions (CR L68–75) and PRD §12

| Report line | Question | Status | PRD location | Note |
|---|---|---|---|---|
| CR L72 | Which database engine? The findings cover PostgreSQL only. | captured | §12 Q4 (prd L885) | Q4 does not say that choosing an engine other than PostgreSQL or SQLite needs a short new check: neither research run covers MySQL. |
| CR L73 | The realistic single-row update rate. | n/a (by design) | NFR-7 | Not needed, because the PRD states no figure. |
| CR L74 | Hold-expiry drift and the payment-after-expiry flow. | partially | §12 Q9 (prd L890) | The flow is carried; drift is not. Q9 says to "prove it with parallel tests (§4.11)", but §4.11 defines no such test (gap 3). |
| CR L75 | Is one aggregate lock enough, or is a queue per Sauna needed? | partially | add. L17 ("still open") | Not in §12, although it is an architecture-owned question like Q4 and Q5. |

## 2. Smart-lock door-code research (2026-10-28)

### 2.1 Recommended PRD wording (LR L72–79)

| Report line | Point | Status | PRD location | Note |
|---|---|---|---|---|
| LR L74 | H6: each door has one code per Window, and the codes differ. A code is valid from the Send time to the Window end. Either accept the overlap and say so, or start validity at the Window start. The simulated lock rejects a duplicate PIN. Whole-hour locks lengthen the overlap. | decided (deferred, memlog L28) | FR-47 (prd L696, L699–700); §12 Q1 (L882); add. C (L81–107); add. L51, L55 | The distinct-PIN and duplicate-rejection parts are testable consequences. The overlap disclosure is deferred and flagged with a NOTE FOR PM. Add. C explains the overlap as Lisa asked, and adds a third option, a changeover gap, which is the PRD's own and is linked to Q3. |
| LR L75 | H12: rules never depend on revoking a code. After the Send time, a Whole-sauna booking of S is refused while Seat bookers hold its code. Replacing the code on online locks is an optional extra. | decided (memlog L11; brief add. L155) | FR-48 (prd L706); add. B (L75) | The optional extra is recorded as the alternative not taken. |
| LR L76 | H13: a Block after the Send time sends a correction email to every Seat booker; the code is replaced where the lock is online; each door is marked replaceable or not. | decided (memlog L27) | FR-48 (prd L707); FR-45 (L676–680); add. B (L76); add. L52 | A replacement after the Send time means editing a code whose validity has started. No source answers whether that works (LR L53), and FR-48 does not point to §12 Q8. |
| LR L77 | H14: lifting a Block after the Send time sends a new code or resends the same one (inference). | captured | FR-48 (prd L708) `[ASSUMPTION: H14 as in the brief]` | The tag is correct: brief add. L171 leaves H14 to the PRD. |
| LR L78 | H15: the code is shared, so cancelling one Booking cannot cut off that Guest without replacing the code and resending it to the others. "Must not be used" is a request, and replacing the code is best effort. | partially | FR-48 (prd L709); FR-42 (L646) | "Must not be used" is testable, but "best effort only" is not. The PRD also drops the research's condition that a replaced shared code is resent to the remaining holders (LR L78; capacity research H15, "needs a resend to the others"). |
| LR L79 | Gate: the email is sent only when the lock confirms the code; the Administrator is alerted if it is not confirmed by the Send time; expired codes are deleted. | captured | FR-49 (prd L711–717) `[ASSUMPTION: H11 as recommended]`; add. L53–54 | The tag is correct (brief add. L169). Testing the "not confirmed" path needs a way to hold the simulated lock in pending or failed, and the PRD body does not require one. |

### 2.2 Findings in the summary and body

| Report line | Point | Status | PRD location | Note |
|---|---|---|---|---|
| LR L22 | Rules work without revoking a sent code. Replacing or deleting a code is a best-effort extra. | captured | §4.15 (prd L671); FR-48 (L702–709) | None. |
| LR L24, L37 | Several codes on one door are normal. The real risk is expired codes left on the lock, so they are deleted ([11], low). | captured | FR-49 (prd L717); add. L54 | None. |
| LR L25 | No vendor states a rule on overlap either way, so the simulated lock must enforce a distinct PIN per door and Window. | captured | FR-47 (prd L699); add. L51; add. C point 1 (L97); §12 Q8 | None. |
| LR L26, L51, L65 | Online codes can be replaced. Offline codes cannot be changed or revoked before they expire. | captured | FR-45 (prd L676); add. L52 | None. |
| LR L27, L43 | Locks that work in whole hours widen the overlap. | captured | add. L55; add. C point 4 (L100), option (b) (L106) | "Sometimes up to 60" is the PRD's own arithmetic, not stated in the report. It is plausible but unlabelled. |
| LR L28, L57–61 | Delivery is not instant and can fail silently (the Nuki 204 report). No vendor gives a latency figure. | captured (via the gate) | FR-49; add. L53 | Latency is not carried (2.4). |
| LR L57 ([4], [5] medium; research memlog: unverified) | Seam's `pending_mutations`, and `status` deprecated in favour of `display_status`. | over-claimed (mild) | add. L53 | Stated as fact with no label. This is harmless for a simulated lock, but the label should be there. |
| LR L62 | Times are sent explicitly in the Venue's time zone. | captured | add. L54; NFR-3 (prd L758) | None. |
| LR L42 | Some vendors cap offline codes per time slot. | n/a | None | Irrelevant with one code per door per Window. |
| LR L58 | Seam re-sets codes removed outside it, and offers backup codes. | n/a | None | A detail of real locks. |

### 2.3 Seat moves and the freeze (LR L81–88, the lead's inference)

| Report line | Point | Status | PRD location | Note |
|---|---|---|---|---|
| LR L85 | In the default mode, door codes do not force any moves; the codes follow from counts. | captured | FR-46 (prd L686–687); add. L19–22 | None. |
| LR L86 | Optional: freeze compaction at the Send time in the default mode. | n/a (not adopted, no effect) | FR-31 INV-5 exceptions (prd L506) | The research says this "costs nothing either way" with derived Placement. |
| LR L29, L87 | Under one-Sauna access, no moves after the Send time; use the Overbooking fallback instead. This conflicts with "moves are allowed at any time". | decided (memlog L11; brief add. L49, L155) | FR-50 (prd L729); FR-31 (L506); add. B (L77); add. G (L242) | The freeze is decided. The fallback part is correctly `[ASSUMPTION]`, because brief add. L73 leaves it to the PRD. But FR-42's trigger (Seats booked exceed Seat capacity) and its loser (the latest Booking in the Window) do not fit a stranded one-Sauna Booking (gap 4). The research calls the whole recommendation inference, while the tag says only "research recommendation". |
| LR L88 | Placement needs to be stored only for one-Sauna access. | captured | add. L22 | None. |

### 2.4 Open questions (LR L90–100) and PRD §12

| Report line | Question | Status | PRD location | Note |
|---|---|---|---|---|
| LR L94 | Can two codes with different PINs overlap on one lock (all vendors)? | captured | §12 Q8 (prd L889); Q1 (L882) | None. |
| LR L95 | Can a code be edited or deleted after its validity has started, and how fast does that take effect? | partially | §12 Q8 | "How fast" is not carried. It matters for H13 and H15, but only on real locks. |
| LR L96 | Does the Schlage API offer single-code edit and delete? | n/a until real locks | None | Step 2 locks are simulated, and real locks are Vision. |
| LR L97 | Nuki and TTLock first-party behaviour in 2026. | n/a until real locks | None | As above. |
| LR L98 | The rest of the RemoteLock API. | n/a until real locks | None | As above. |
| LR L99 | Is the Nuki 204-without-PIN fault fixed? | n/a (the gate handles it) | FR-49 | None. |
| LR L100 | Latency of creating, changing and deleting a code. | partially | None | No effect on a simulated lock, but it would test the 20-minute Send time on a real one. |

## 3. Confidence labels and mechanism placement (check b)

**PRD body.** The PRD body names no engine-specific mechanism. A search for PostgreSQL, Serializable, 40001, advisory, row lock, Seam, webhook, sweeper and `expires_at` finds only §12 Q4, which names the research scope. The one mechanism-level requirement in the body is the store-level refusal in FR-10 (gap 1). FR-32's "serialised" reads as a correctness property (the outcome equals some serial order), which is acceptable. "Behave as if handled one at a time" would avoid suggesting an isolation level.

**Addendum A against the research labels:**

| Addendum line | Statement | Label in addendum | Label in research | Verdict |
|---|---|---|---|---|
| L8 | Conditional UPDATE under Read Committed | verified; medium for this use | high and verified (CR L24, L31; memlog); medium for this use | intact |
| L9 | Serializable backstop; retry 40001 and 40P01 | none | high ([1] verified); 40P01 from digest d1 L19 | under-labelled (harmless) |
| L10 | No lock held across payment | low–medium | low–medium (CR L33) | intact |
| L15 | Seat counter with a CHECK constraint in the Core | none | not in either report | unlabelled inference |
| L16 | No store-level constraint once capacity varies | "(inference)" for the transaction only | exclusion constraints: unverified belief (CR L48) | label softened |
| L35–36 | Holds are data; the sweeper interval is an example | low | low (CR L38, L62) | intact |
| L37 | Idempotent confirmations, deduplicated by event ID | "low", from the heading | high in the report (CR L40, L63) and digest; unverified in the research memlog | mismatch; needs its own label |
| L38 | The handler re-checks the Hold in a transaction | inference | inference (CR L40) | intact |
| L53 | Seam `display_status` and `pending_mutations`; `status` deprecated | none | medium ([4], [5]; LR L109–110); unverified in the research memlog | mild over-claim |
| L55 | Whole-hour locks lengthen the overlap | none | high [2], medium [8], medium (2016) [6] | acceptable |

No addendum statement says "high" where the research says low or unverified. The only "high" in addendum A (L11, SQLite) comes from the capacity research, which this check does not cover.

## 4. Sourced vs inferred (check c)

**Represented correctly:**
- §12 Q9 (prd L890), "This flow has no primary source": matches CR L40 and L63.
- §12 Q4: findings cover PostgreSQL only, as CR L27 says.
- §12 Q8: overlap and edits after the start are untested, as LR L30 and L53 say.
- §4.15 (prd L671), "many real locks cannot do that": sourced (LR L26; Seam [1] and igloohome [2], both high).
- Add. L8, L16 and L38: the inferences are labelled.
- Add. C L97, "none of them documents … untested": matches LR L25 and L40.
- Add. H L268, on the concurrency report's labels: confirmed against its memlog ([2] and [4] unverified).
- FR-48 (H14, H15) and FR-49 (H11) are tagged `[ASSUMPTION]`, which matches brief add. L169–172 ("to be decided in the PRD").

**Problems:**
1. **FR-10 (prd L263) and §4.3 (L254).** The requirement that the data store refuse an over-capacity write "even when the application's own check is bypassed" has no source in either report, the brief, the brainstorm, the PRD memlog or the session logs (all searched). It is not tagged `[ASSUMPTION]`. The brief says the opposite is open: "How the atomic operation is built is an architecture decision" (brief add. L220).
2. **Add. L15.** The CHECK constraint is an unlabelled inference.
3. **FR-50 (prd L729).** The tag says "research recommendation", but the research calls the freeze the lead's analysis: inference, not sourced (LR L81–83). Minor.
4. **Add. B (L62–79), "Decisions taken from research".** The table does not show which rows rest on sources and which on the lead's inference; H12 to H15 and H21 rest mostly on inference. Minor.
5. **CT-1 to CT-5 (FR-11, FR-35, FR-36).** The brief's concurrency-test table has no IDs (brief add. L212–218). The PRD numbers the rows in order without saying so, and the same applies to IV, PW, RB and HT. A traceability nit.

## 5. Gaps that matter, ranked

### 1. The Core's store-level refusal is an unsourced mechanism requirement

**PRD location:** FR-10 (prd L263), §4.3 description (L254), add. L15.

**Problem:**
- FR-10 requires the data store to refuse an over-capacity write "even when the application's own check is bypassed". No input asks for this:
  - R1 asks for the behaviour;
  - R4 leaves the mechanism to the architecture;
  - the brief leaves the atomic operation to the architecture (brief add. L220);
  - no log decides it.
- It is untagged, so it reads as sourced. It also shapes the first build step: the schema needs a per-Window counter with a CHECK constraint, or a trigger, on top of the research's conditional UPDATE.
- The §4.3 description states it for the whole feature, yet add. L16 admits that no store-level constraint is known once Whole-sauna bookings and Blocks change Seat capacity.

**Fix:** Choose one:
- Keep it as deliberate defence in depth: tag it `[ASSUMPTION: defence in depth; not from research or brief]`, add it to §13, log it in `.memlog.md`, and add "(inference; not in the research)" to add. L15.
- Or remove it from FR-10, and keep it in addendum A as a recommended mechanism.

In either case, begin prd L254 with "In the Core, …" so the description matches FR-10.

### 2. Changes that span two Windows have no concurrency consequence, and the lock-order rule is missing

**PRD location:** FR-26 (prd L445), FR-32 (L516–523), FR-33 (L530), add. L7–17.

**Problem:**
- The PRD makes these Changes atomic (E5), and FR-32 serialises requests within one Window. But no consequence covers a Change from W1 to W2 that runs in parallel with a Whole-sauna booking or with an opposite Change, and the catalogue has no such case either.
- Addendum A dropped the research's rule "locks in a fixed order" (CR L45, L53). Requests that lock two Windows need it to avoid deadlocks: FR-26, FR-33, and a Block across several Windows (FR-40).
- Without it, FR-14 turns each deadlock into a "please try again" for the Guest. A two-Window request is also the classic deadlock case, so by the PRD's own thesis it should be proven by a parallel test.

**Fix:**
- Add to FR-32: "A Change that moves Seats from W1 to W2, run in parallel with a Whole-sauna booking or an opposite Change in W1 or W2, leaves INV-1 to INV-5 true in both Windows. No Seat is lost or counted twice, and two requests never both succeed with the same Seats."
- Add to addendum A, under "Check and reserve capacity": "A request that touches several Windows locks them in one fixed order, for example by Window start time (PostgreSQL docs [2]: high in the report, unverified in the research memlog)."

### 3. The Hold and late-payment path cannot be fully tested

**PRD location:** FR-35 (prd L552–560), FR-36 (L562–567), §4.11 (L548), §12 Q9 (L890).

**Problem:**
- R2's "ignored once expired, even if cleanup has not run" appears only in the description.
- FR-36 says a late payment "creates a Booking only if the Seats are still free", which is a necessary condition only. The still-free branch, which the WCAG argument in add. L39 depends on, has no consequence.
- §12 Q9 asks the architecture to prove the flow with parallel tests "(§4.11)", but §4.11 defines no such test.
- A Simulated payment has no callbacks, so "repeated or out-of-order confirmations" (L567) cannot be produced in a test unless the PRD says how. The research calls this path the weak spot and finds no source for it (CR L40), so tests are the only evidence.

**Fix:**
- Add to FR-35: "With cleanup switched off, an expired Hold no longer reduces Seats left."
- Add to FR-36:
  - "A payment that completes after expiry while the Seats are still free creates exactly one Booking."
  - "Run in parallel: a late payment for an expired Hold and another Guest's Hold or payment for the same last Seat. Exactly one gets the Seat. The other gets no Booking and, if charged, a simulated refund."
  - "A test switch can make the Simulated payment confirm late, twice or out of order (as FR-7 does for failure)."

### 4. Two Step 2 door-code rules are underspecified: H15 and a forced move under one-Sauna access

**PRD location:** FR-48 (prd L709), FR-50 (L729), FR-42 (L642–647).

**Problem:**
- "Replacing the shared code is best effort only" cannot be tested, and the PRD drops the research's condition that a replaced shared code is resent to the remaining holders (LR L78; capacity research H15).
- FR-50 sends a forced move after the Send time to the Overbooking fallback. But FR-42 only triggers when Seats booked exceed Seat capacity, and then cancels the latest Booking in the Window. Under one-Sauna access, a Block of S after the Send time can strand the Bookings placed in S while the Venue still has room overall. The latest Booking may also sit in another Sauna.

**Fix:**
- In FR-48: "A shared code is replaced only on doors marked replaceable. When it is, every remaining holder receives the new code before the old one stops working. Otherwise no code is replaced." Alternatively, drop replacement on cancellation for Step 2.
- In FR-50: "Under one-Sauna access, a Booking that would have to move after the Send time is cancelled as in FR-42, with refund or Voucher, even when Seat capacity is not exceeded. Other Bookings are untouched."

### 5. Missing test switches for exhausted retries and for lock confirmation

**PRD location:** FR-14 (prd L287–292), FR-49 (L711–717).

**Problem:** A normal test run rarely or never reaches two paths:
- "please try again" in FR-14: under the research's main mechanism, the Read Committed conditional UPDATE, conflicts wait instead of failing;
- "not confirmed by the Send time" in FR-49: a simulated lock has no reason to be slow or to fail unless told to.

FR-7 already sets the pattern, with a test switch for failed payment.

**Fix:**
- Add to FR-14: "A test switch can make every attempt conflict. The request then ends with 'please try again' and writes nothing."
- Add to FR-49: "A test switch can hold a code in pending or failed."

### 6. Some confidence labels in addendum A are missing or inherited

**Location:** add. L9, L15, L37, L53 and H L268.

**Fix:**
- L37: "(Stripe docs [4]: high in the report, unverified in the research memlog)".
- L53: "(Seam docs [4], [5]: medium, unverified)".
- L15: "(inference; not in the research)".
- L9: "(PostgreSQL docs [1]: high, verified)".
- H L268: name the references, "[2] lock order and advisory locks, [4] Stripe webhooks".

### 7. §12 is missing a few research questions

**Location:** §12 Q8 (prd L889), Q9 (L890), add. L17.

**Fix:**
- Add an architecture-owned question: "Lock unit for Seat and Whole-sauna requests (per Window, per Sauna, or a queue per Sauna). Prove it with the parallel tests of FR-32." This is CR L75.
- Extend Q9 with "expiry drift; use the data store's clock" (CR L41, L74).
- Extend Q8 with "how fast create, change and delete take effect, and silent failures, before any real lock (Vision)" (LR L95, L99–100).

### 8. The CT test IDs are not traceable

**Location:** §0 (prd L16), FR-11 (L269), FR-35 (L557–558), FR-36 (L566).

**Fix:** Add one sentence to §0: "CT-1 to CT-5, and IV, PW, RB and HT, number the rows of the brief addendum's test tables in order." Alternatively, add the IDs to the brief's tables.

## 6. Noticed outside these two inputs (low priority)

- FR-40 cites no race case. Catalogue C6, a Block racing a booking (capacity research L90), is covered only by SM-5's "groups A to F pass". Consider citing C6 in FR-40 or FR-32.
- FR-35 (prd L559) says "a failed or abandoned payment releases the Hold at once". "Abandoned" cannot be observed unless it is defined, for example as the Guest pressing Back or Cancel. Otherwise expiry handles it.
- The double-spend rules for Vouchers and Gift cards (FR-28 L465, FR-44 L668) rely on the same atomic-check pattern as FR-10. Addendum A could say that its conditional-update guidance applies to balances too.
- Both research runs skipped the semantic citation check, as their memlogs and `issues.md` record. Their confidence labels are therefore the lead's own, not cross-checked.
- `issues.md` still lists H12 and the freeze as open, although the brief addendum (L155) records them as decided. Add. H L263–266 already flags this.
