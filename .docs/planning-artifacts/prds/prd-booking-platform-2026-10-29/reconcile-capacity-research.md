# Input reconciliation: capacity-model research vs PRD

- **Input:** `.docs/planning-artifacts/research/technical-kapasitetsmodell-enkeltplasser-2026-10-28/research.md` (293 lines: INV-1 to INV-7, formulas, Rec 1 to Rec 8, 85-example catalogue A–I). The run's `.memlog.md` and digests `algo-r1-1`, `impl-r1-1` were used for the confidence checks.
- **Checked against:** `prd.md` (926 lines) and `addendum.md` (287 lines), draft of 2026-10-29.
- **Decision logs:** PRD `.memlog.md` (PM) L22, L27, L28 (and v0 line L11, superseded); brief `.memlog.md` (BM) L118–L121. The brief log holds the E1/E3, H12 and H21-freeze decisions that the PRD log does not repeat.
- **Date:** 2026-10-29. Read-only check: no PRD or addendum text was changed.
- **References:** `R L…` = research.md, `P L…` = prd.md, `Add L…` = addendum.md, `PM L…` / `BM L…` = PRD / brief memlog.

**Status legend**
- **captured:** stated with matching meaning, IDs and numbers.
- **partially:** stated, but part of the research outcome or a needed qualifier is missing.
- **missing:** no home in the PRD or addendum, and no recorded reason.
- **contradicted:** PRD text conflicts with the research outcome, or with another PRD rule built on it.
- **miscited:** the ID, number or attribution does not match the report.
- **decided:** a logged decision (memlog line given), so not a gap. "decided; partially written" means the decision is logged but the PRD carries only part of it.
- **implicit:** covered only by a blanket reference ("groups A and B hold as written", "groups A to F pass"), with no FR consequence of its own.
- **n/a:** background with no PRD action.

## 1. Verdict

The PRD carries this research well. All eight recommendations are reflected or deliberately deferred with a reason. Every logged decision (D3, D7, D8, F1, F2, F3, the strict whole-sauna rule, H10, H13, H23; H6 deferred; E1/E3, H12 and the H21 freeze from the brief log) appears with the right ID. All 43 catalogue IDs in the check list match the report's numbers and outcomes, with one exception: H18 is cited for the opposite of its outcome. One attribution in addendum B (F1) is slightly off. The addendum states the research's confidence honestly (low–medium for derived Placement, inference for the formulas, high only for the SQLite mechanism).

The gaps fall into three groups:
1. One concurrency case (C6) and four D/E examples have no FR home.
2. Two decided rules (F3 and INV-4) and the default Booking deadline after the start interact in ways the PRD does not settle.
3. Three statements read stronger than the research supports: SM-5's "groups A to F pass", FR-31's "hold as written" and Q5's "proven".

## 2. Gaps that matter, ranked

### G1. F3 is decided, but its v1 meaning is undefined, and the post-start Booking deadline opens a hole
- **Where:** P L506 (INV-5 exception), L628 (FR-40, F3), L476–489 (FR-29), L605 (FR-39, Booking deadline 5 min after start), L195 (FR-4, Guests move freely).
- **Research:** F3 R L122 (decided PM L27); H12 R L161; I11 R L214 (seat guests move freely between all non-whole saunas); I19 R L232 (a derived model would move seats in a started window; F3 needs recorded state).
- **Problem 1 (contradiction between decided rules).** FR-40 says a Block in a started Window "moves no Seats", but INV-4 (P L503, "a Blocked Sauna holds no Seats") has no started-Window exception. So blocking a Sauna that holds Seats in a started Window has no valid outcome, and the Overbooking fallback runs only "if needed" (Seats booked > Seat capacity), which a single Block usually does not trigger. Under derived Placement (Q5, recommended), "no move" cannot be represented unless the Placement at the start is stored.
- **Problem 2 (rule gap; reconciler's inference from H12, I11 and F3).** Whole-sauna bookings stay open until the Booking deadline, 5 minutes after the start by default. In a started Window, Seat bookers may be sitting in any Sauna that is open for Seats, including one whose Placement is empty (FR-4, I11). FR-29 can then sell that Sauna whole while Guests are in it. H12 blocks this only after the Send time, and only in Step 2 (P L706). v1 has no equivalent rule, although the Vision promises never to "sell a sauna that guests are already booked into" (P L31).
- **Suggested fix.** Lisa must confirm, because F3 is a logged decision:
  - (a) Add to FR-29: "Once a Window has started, a Sauna that is open for Seats cannot be booked whole while the Window has any Seat booking. This is the v1 counterpart of H12, and follows F3." A simpler alternative is to close Whole-sauna bookings at the Window start.
  - (b) In FR-40 L628, state one of these:
    - (i) "In the default mode, a Block in a started Window counts Seats again like any Block (D2), and runs the Overbooking fallback only if Seats booked exceed the new Seat capacity (D3). F3's 'no moves' applies to one-Sauna access (FR-50) and, in Vision, to heater state (I19)."
    - (ii) Keep F3 literally and add an INV-4 exception: "Seats counted in a Sauna Blocked after its Window started stay counted there until the Window ends."

    Option (i) fits derived Placement.

### G2. C6 has no home: FR-32 does not serialise Blocks with Bookings
- **Where:** P L516–523. FR-32 serialises only "Seat bookings, moves and cancellations and Whole-sauna bookings". FR-40 (P L615–629) has no race rule. SM-5 (P L872) covers C6 only through "group C".
- **Research:** C6 R L90 (a Block of S3 races a booking for the last Seat). The group C header (R L81) says "the exact outcomes are the acceptance criteria". Rec 5 (R L255) says to run all of group C in parallel.
- **Suggested fix.** Add to FR-32: "Blocks, lifted Blocks, Whole-booking-only marks and releases are serialised with Bookings in every Window they touch. When a Block races a booking for the last Seats, either the booking goes first and D2/D3 then apply, or the Block goes first and the booking is judged on the reduced Seat capacity. The outcome is never a mix of the two (C6)." Optionally add to addendum A: "A Block spans several Windows, so take their locks in a fixed order" (reconciler's inference). The same sentence covers the D8 race between a mark and a Seat booking.

### G3. The catalogue is cited as executable "as written", but parts of it are not, and four A–F examples have no FR home
- **Where:** P L509 (FR-31, "Catalogue groups A and B hold as written") and P L872 (SM-5, "Catalogue groups A to F pass"). The addendum already notes the problems (Add L60, L259, L262) but does not fix the claims.
- **Research:**
  - B4 (R L76) is a single 38-Seat request, above the 10-Seat cap.
  - D5 (R L100) uses W0 14:00–16:00, which overlaps W1, so FR-13 rejects the setup.
  - The "Then" column of E1 and E3 (R L109, L111) describes the failure plus a recommendation.
  - The "Then" column of D7, D8 and F1–F3 is an open decision.
  - D1 (R L96), E4 (R L112) and E6 (R L114) have no FR consequence.
- **Suggested fix:**
  - FR-31 L509: "Catalogue groups A and B hold, with B4 rewritten as several Bookings under the 10-Seat cap (addendum A)."
  - SM-5 L872: "Catalogue groups A to F pass, with the decisions in addendum B applied and with B4 and D5 rewritten."
  - FR-40, rewritten D5: "With W1 15:00–16:30 and W2 16:30–18:00, a Block 16:30–17:00 affects W2 only. W1 ends exactly when the Block starts (D5, rewritten for FR-13)."
  - FR-40, D1: "Blocking Sauna 2 in an empty Window lowers Seat capacity and Seats left to 34 (D1)."
  - FR-13: "Windows are independent. A booking, cancellation or Whole-sauna booking in one Window never changes another (E2, E4, E6)."

### G4. The FR-40 Block preview assumes per-Booking Placement, which derived Placement does not have
- **Where:** P L620 (FR-40) and P L107 (UJ-6 step 2) both promise "the Bookings whose Seats will be counted into other Saunas".
- **Research:** R L44 recommends deriving Placement; it has no observable meaning in the default mode. D2 (R L97) says no guest is affected. D3 (R L98) has the Administrator see only the list of Bookings that lose.
- **Problem:** With counts per Window, the platform knows *how many* Seats are counted again, not *whose*. The preview quietly requires stored Placement, or a rule for ordering Bookings. That works against Rec 2, and Q5 (P L886) does not mention it.
- **Suggested fix.** Replace the phrase with "how many Seats will be counted into other Saunas (no Guest is affected, D2), and any Booking that would lose its place (D3)". If per-Booking detail is wanted, add to Q5: "With derived Placement, the Block preview needs a fixed Booking order, for example by creation time."

### G5. Step 2 (one-Sauna access, Gradual opening): cited cases conflict with PRD rules
- **H18 is contradicted.**
  - Where: P L725 (FR-50), "A Sauna emptied by cancellations closes again and becomes free for a Whole-sauna booking (H16 to H18)".
  - Conflict: H18's "Then" (R L172) is the gap: seat bookers still hold K(S2), "same gap as H12". FR-48 (P L706) therefore refuses that Whole-sauna booking after the Send time.
  - Fix: "…closes again. Before the Send time it is free for a Whole-sauna booking; after it, FR-48 applies (H18)."
- **H23 is half written** (decided PM L27). P L730 lacks the second half of R L182. Add: "Turning the mode off applies only to Windows whose Door-code email has not been sent (H23)."
- **H19 and H22 have no FR, and conflict with "never told a Sauna".**
  - Conflict: P L132 (Glossary, Placement), P L192 (FR-4) and P L513 (FR-31) have no one-Sauna-access exception. H19 (R L178) and H22 (R L181) reach the PRD only through the blanket "group H holds the detailed acceptance cases" (P L671).
  - Fix, add to FR-50: "The Door-code email names the Booking's Sauna and gives only its codes (H19). If that Sauna has no self-service lock, the email names it without codes (H22)." Add "except under one-Sauna access (FR-50)" at P L132, L192 and L513.
- **INV-5 and FR-29 fail when Bookings cannot split** (Rec 6, R L256; G1, R L128).
  - INV-5: H19 itself breaks INV-5 before the Send time. With A=3 in Sauna 1, Sauna 1 still has 4 free while B=5 sits in Sauna 2.
  - FR-29: the count test no longer proves that a Sauna is empty. Four Bookings of 4 total 16 ≤ Room ahead(Sauna 3) = 17, yet first-fit places the fourth in Sauna 3.
  - Fix at FR-31 L506: "INV-5 does not apply under one-Sauna access. FR-29 then requires that the Sauna holds no Booking, using stored Placement (addendum A L22)."
- **G1 is unanswered.** Add to §12: "Under one-Sauna access, may Bookings be repacked before the Send time? Is a Window offered for N Seats only when one Sauna has N free (G1)?" FR-3 L181–182 then needs that caveat, because "Seats left" can exceed the largest single free space.
- **H20 is adopted by blanket.** H20 contradicts itself (Add L260 notes this). At P L671 and P L873, write: "group H, except H20 (replaced by the freeze in FR-50) and H6 (deferred)".

### G6. Smaller fixes

These are listed in §9 (M-1 to M-13). M-1 (an addendum miscitation), M-3 (the model-based test's action list) and M-5 (the scope of FR-42) are the ones worth doing first.

## 3. (a) Recommendations Rec 1–8

| Rec | Report line | Point | Status | PRD location | Note |
|---|---|---|---|---|---|
| 1 | R L251 (also L22, L26) | State the rule as INV-1–INV-5 plus the catalogue, not as the move algorithm; "how Placement is computed" is an architecture decision | captured; decided (BM L120) | P L498–506 (FR-31), L509–514, L132 (Placement is "the platform's way of keeping count"), L886 (Q5); Add L19–23 | UJ-6 Climax (P L108) still says Seats "move" (cosmetic, M-13) |
| 2 | R L252 | Prefer derived Placement for v1 and If time; confirm with a model-based test | captured; decided as an architecture question (BM L120) | P L886 (Q5), L514; Add L19–23 ("low–medium confidence; no practitioner source") | Q5's "proven by" reads as done (§7 C-2). The FR-40 preview presumes stored Placement (G4) |
| 3 | R L253 | Venue-wide, non-overlapping Windows (E1, E3) | captured; decided (BM L118) | P L118, L280–285 (FR-13), L594 (FR-38); Add L66 | "Partly overlap" leaves nested or duplicate Windows unstated (M-4) |
| 4 | R L254 | Decide D3, D7, D8, F1–F3 in the PRD | decided (PM L27) | D3 P L622–625; D7 L627; D8 L636; F1 L595; F2 L596; F3 L506, L628; Add L68–73 | F3's meaning under derived Placement and INV-4 is open (G1); Add L71 misdescribes F1 (M-1) |
| 5 | R L255 | Run all of group C in parallel; one transaction per write unit (BEGIN IMMEDIATE in SQLite; Serializable with retry in PostgreSQL) | partially | P L488 (C1), L516–523 (C2–C5), L872, L761 (NFR-6), L287–292 (FR-14); Add L9, L11, L16, L58 | C6 is missing and Blocks are not serialised (G2) |
| 6 | R L256 | Skip group G unless one-sauna access is promoted; if it is, H19–H23 apply and Placement is stored | partially | Add L22 (nullable "placed in Sauna" column), L59 ("group G only if one-Sauna access is built"); P L727–730 | One-Sauna access is in Step 2, so G1, H19 and H22 apply then. They are unanswered, and INV-5 and FR-29 fail when Bookings cannot split (G5) |
| 7 | R L257 | Group H is the acceptance criteria for SC6; decide H6, H10, H12, H13, H21, H23 | decided; partially written | P L671, L873, FR-45 to FR-50. H6: deferred (PM L28), P L700, L882, Add L81–107. H10: L698 (PM L27). H12: L706 (BM L119). H13: L707 (PM L27). H21: L729, freeze decided (BM L120), fallback tagged ASSUMPTION. H23: L730 (PM L27) | H23's second half is missing; H18 is contradicted; H19 and H22 conflict with "never told a Sauna"; H20 is not excluded (G5) |
| 8 | R L258 | Group I only when heating is built, and v1 needs nothing from it; then decide I11/I12, I13, I14, I19, I22, I23; controller = derived wanted set plus recorded actual state | captured (deferred to Vision) | P L747 (§4.17), L894 (Q13), L33, L817; Add L59 | The controller design note is not carried. Optional, Vision only |

## 4. (a) Other report points meant for the PRD

| Report line | Point | Status | PRD location | Note |
|---|---|---|---|---|
| R L26, L45–48 | Formulas: free seats; a whole booking is allowed iff S is not blocked, not whole-booked, and seats(W) ≤ P(S); fill skips whole-booked and blocked Saunas | captured, extended | P L129–133 (Seat capacity, Seats left, Room ahead = P(S)), L476–481 (FR-29); Add L25–33 | The PRD adds held Seats and Whole-booking-only status and says so (Add L33, L261). FR-29 itself omits held Seats (M-6) |
| R L27, L44, L134 | Stored Placement is needed only with one-sauna access; derive it otherwise | captured | Add L19–22 | — |
| R L30 | Biggest caveat: no sauna comparable; the formula and outcomes come from the project's own addendum | captured | Add L23 | Not repeated in prd.md; acceptable |
| R L24, L34–38 | Hotels assign late [6][7]; restaurants never auto-move [8]; bin-packing theory [4][5] | n/a (background) | — | Optional: cite [6][7] at Add L19 as the analogy behind "derive, don't commit" (Rec 1's stated basis) |
| R L42 | SQLite: BEGIN IMMEDIATE, BUSY at BEGIN, WAL | captured | Add L11 ("high confidence for the mechanism"; busy timeout unsourced) | Matches ([1] verified, research memlog L11) |
| R L43 | PostgreSQL: Serializable with retry on 40001; exclusion constraints do not cover the cross-kind rule | captured | Add L9, L16 | — |
| R L49 | Fixed venue-wide slots: "same window" means window-id equality; free windows need interval logic | partially | P L280–285 (FR-13) | The hint is not carried. Optional (reconciler's inference): an exclusion constraint [3] can enforce the Windows table's own no-overlap rule, which is a same-kind overlap |
| R L50, L265 | Model-based test: check INV-1–INV-5 after every step, against a brute-force reference, with blocks and whole bookings together | captured | P L514, L872 | The test's action list is narrower than FR-31's own trigger list (M-3) |
| R L50 | INV-6, INV-7 (heating) | captured (Vision) | P L747 | — |
| R L245 | Derived Placement removes the A3/C3 race | captured | P L521 (C3) | — |
| R L264 | Open: stored vs derived Placement in practice | captured | P L886 (Q5) | — |
| R L268 | Open: overlapping PINs and editing a code after its start, on real locks | captured | P L889 (Q8) | — |
| R L269–270 | Heater warm-up; cold open sauna (I11/I12) | captured (Vision) | P L894 (Q13) | — |
| R L290 | Re-check DB claims [1]–[3] (by 2026-11-01, or when the engine is chosen) | captured | Add L12 | The date is not carried; "once an engine is chosen" is |

## 5. (b) Citation check: every cited ID

All numbers below were checked against the catalogue row (Given, When, Then).

| ID | Report line | Research outcome (short) | PRD or addendum wording (short) | Location | Status |
|---|---|---|---|---|---|
| A2 | R L61 | [7,10,5,0], 3 in S1 cancel → [7,10,2,0] | same numbers | P L510 | captured |
| A3 | R L62 | [7,10,2,0], 2 in S1 cancel → [7,10,0,0]; S3 bookable whole at once | "A Sauna emptied this way can be booked whole at once" | P L511 | captured (paraphrase: "this way" follows A2, which does not empty S3; M-8) |
| A6 | R L65 | 42 booked, book 3 → rejected as a whole, state unchanged | "With 42 of 44 … a request for 3 is rejected and nothing changes" | P L277 | captured |
| A7 | R L66 | 44 booked, book 1 → rejected, "no seat free" | "With all 44 booked, a request for 1 is rejected" | P L277 | captured |
| B1 | R L73 | [7,10,3,0], whole S4 → accepted (20 ≤ 29); free 9 | same numbers | P L483–484 | captured |
| B2 | R L74 | whole S3 at [7,10,3,0] → rejected (20 > 17) | "Sauna 3 cannot"; NOTE: refusal while the Venue has room | P L485, L472 | captured |
| B3 | R L75 | [1,0,0,0], whole S1 → rejected | same | P L486 | captured |
| B5 | R L77 | S2 whole-booked, 9 booked → [7,—,2,0] | "Seats are counted around the Sauna" | P L487 | captured (no numbers) |
| B6 | R L78 | [7,—,12,4] (23), S2's whole booking cancels → [7,10,6,0] | "counts the Seats forward again" | P L512 | captured (no numbers) |
| B7 | R L79 | S4 whole-booked → free seats exclude S4 at once | "Seats left drops at once by the Sauna's Capacity" | P L487 | captured (true only for a Sauna open for Seats; see M-8) |
| C1 | R L85 | two whole bookings of S4 → exactly one; the other is told it is taken | "exactly one succeeds" | P L488 | captured ("told it is taken" omitted; trivial) |
| C2 | R L86 | 1 Seat vs whole S4 at [7,10,12,0] → one wins, never both | same | P L520 | captured |
| C3 | R L87 | cancel 2 in S1 vs whole S3 at [7,10,2,0] → accepted only after the move | same | P L521 | captured |
| C4 | R L88 | two cancels of 3 at [7,10,12,4] → [7,10,10,0]; none moved twice or lost | same (no numbers) | P L522 | captured |
| C5 | R L89 | INV-1–INV-5 after each request, under any interleaving | same | P L523 | captured |
| D2 | R L97 | block S3 at [7,10,5,0] → [7,10,—,5]; no guest affected | same | P L621 | captured |
| D3 | R L98 | block S3 at 39 → capacity 32; latest Booking(s) cancelled in full; refund or voucher; admin sees the list first | same | P L620, L622–625; Add L68 | decided (PM L27); captured |
| D4 | R L99 | whole-booked S4 is blocked → refund or voucher, regardless of cutoff | same | P L626 | captured |
| D6 | R L101 | all blocked → capacity 0, W not offered, all cancelled | same | P L629 | captured |
| D7 | R L102 | lift block → [7,10,5,0] (recommended) | "counts Seats again so that INV-5 holds" | P L627; Add L69 | decided (PM L27); captured |
| D8 | R L103 | mark Whole-booking-only over seats → refused (or treat as a block) | "Marking is refused while Seats are placed" | P L636; Add L70 | decided (PM L27); captured |
| E1 | R L109 | overlapping windows break per-window capacity; reject partial overlap | same | P L284; Add L66 | decided (BM L118); captured |
| E2 | R L110 | 16:30 end and 16:30 start: no overlap, independent | "15:00–16:30 and 16:30–18:00 are accepted" | P L284 | captured ("independent" not stated; G3) |
| E3 | R L111 | per-sauna lengths break pooling; deviations are blocks | same | P L285; Add L66 | decided (BM L118); captured |
| E5 | R L113 | change 3 Seats W1→W2 with 2 free → rejected, atomic | same | P L445 | captured |
| F1 | R L120 | lower S2 to 6 → refused while any future window would exceed capacity (or handled like D3); needs a decision | FR-38: refused. Add B: "The research gave no recommendation; this is the PRD's choice" | P L595; Add L71 | decided (PM L27); PRD captured; **addendum miscited** (M-1) |
| F2 | R L121 | reverse fill order → apply to windows not started | same | P L596; Add L72 | decided; captured |
| F3 | R L122 | started window: no moves; overbooking fallback | same | P L506, L628; Add L73 | decided (PM L27); captured; interaction gap G1 |
| H1 | R L140 | A gets K(S1)–K(S4) | "every Sauna that is open for Seats" | P L687 | captured |
| H2 | R L141 | the whole-sauna booker gets K(S4) only; seat bookers never get K(S4) | same | P L686–687 | captured |
| H3 | R L142 | S2 blocked, S3 Whole-booking-only → A gets K(S1), K(S4) | same | P L687 | captured |
| H4 | R L143 | block with door-code override → K(S3) to the admin only | same | P L689 | captured (the override is defined nowhere in the PRD; M-9) |
| H5 | R L144 | no lock on S4 → A gets K(S1)–K(S3); B gets no door-code email | "A Sauna without a self-service lock gives no code" | P L688 | partially (M-10) |
| H7 | R L146 | partial cancel → still one email; full cancel → none | "gives up all Seats … receives no codes" | P L690 | captured |
| H8 | R L152 | email at 14:40; valid 14:40–16:30 | same | P L696 | captured |
| H9 | R L153 | booking after the send time → email at once | same | P L697 | captured |
| H10 | R L154 | changed send time → only windows with unsent email | same | P L698; Add L74 | decided (PM L27); captured |
| H12 | R L161 | after the send time, refuse whole S while seat bookers hold K(S) (default: any Seat booking) | same | P L706; Add L75 | decided (BM L119); captured |
| H13 | R L162 | correction email; replace where online; per-door "replaceable" mark | same | P L707, L676–680; Add L76 | decided (PM L27); captured |
| H16 | R L170 | Gradual opening: only the open set gives codes | Glossary "Open for Seats" plus FR-46 | P L128, L687, L724 | captured |
| H17 | R L171 | extra email when S2 opens; a late booker gets both codes at once | "extra email when another Sauna opens" | P L726 | captured |
| H18 | R L172 | S2 empties after the send time → closes, but seat bookers still hold K(S2): same gap as H12 | "closes again and becomes free for a Whole-sauna booking (H16 to H18)" | P L725 | **contradicted** (cites H18's When as a rule; conflicts with FR-48 L706; G5) |
| H23 | R L182 | refuse turning on while split; turning off only for windows with unsent email | first half only | P L730; Add L78 | decided (PM L27); partially written (G5) |

**Other IDs the PRD or addendum cites**

| ID | Report line | Location | Status |
|---|---|---|---|
| H6 | R L145 | P L699–700, L882; Add L81–107 | decided (deferred, PM L28); captured. P L699 states the "codes always differ" part untagged. It holds under all three options (M-11) |
| H11 | R L155 | P L711–717, `[ASSUMPTION]` | captured as an assumption (open per brief addendum L304). "An entered code can be changed until the email is sent" is missing (M-10) |
| H14 | R L163 | P L708, `[ASSUMPTION]` | captured. The brief's general rule (brief addendum L300) also covers a Release after the Send time (M-12) |
| H15 | R L164 | P L709, L646, `[ASSUMPTION]` | partially: "needs a resend to the others" if the code is replaced is missing (M-10) |
| H20 | R L179 | Add L260 | the inconsistency is captured, but H20 is not excluded from the group-H blanket (G5) |
| H21 | R L180 | P L729; Add L77 | decided (BM L120, freeze); the fallback half is correctly tagged `[ASSUMPTION]` |
| B4 | R L76 | Add L60, L262 | captured as needing a rewrite, but FR-31 still says "as written" (G3) |
| D5 | R L100 | Add L259 | captured as an inconsistency; no rewritten D5 in the PRD (G3) |
| I11–I23 | R L214–241 | P L894 | captured (deferred, Rec 8) |

The sample IDs at P L19 (A6, B1, D3) are correct.

## 6. (d) Coverage of groups A–F (38 examples)

| ID | Report line | Home | Status |
|---|---|---|---|
| A1 | R L60 | FR-31 blanket (P L509) | implicit |
| A2 | R L61 | P L510 | captured |
| A3 | R L62 | P L511 | captured |
| A4 | R L63 | FR-31 blanket | implicit |
| A5 | R L64 | FR-31 blanket | implicit ("S4 first, then S3" is move-order detail; Rec 1 says not to specify it, and derived Placement makes it automatic) |
| A6 | R L65 | P L277 | captured |
| A7 | R L66 | P L277 | captured |
| A8 | R L67 | FR-31 blanket; FR-26/FR-27 "freed Seats count at once" (P L447, L456) | implicit |
| B1 | R L73 | P L484 | captured |
| B2 | R L74 | P L485, L472 | captured |
| B3 | R L75 | P L486 | captured |
| B4 | R L76 | Add L60 | partially (rewrite needed; G3) |
| B5 | R L77 | P L487 | captured |
| B6 | R L78 | P L512 | captured |
| B7 | R L79 | P L487 | captured |
| C1 | R L85 | P L488 | captured |
| C2–C5 | R L86–89 | P L520–523 | captured |
| **C6** | R L90 | none | **missing** (G2) |
| **D1** | R L96 | SM-5 only | **missing** as an FR consequence (G3) |
| D2 | R L97 | P L621 | captured |
| D3 | R L98 | P L622–625 | captured; decided |
| D4 | R L99 | P L626 | captured |
| **D5** | R L100 | rule at P L619 (`[ASSUMPTION]`); example invalid under FR-13 | **missing** (rewrite needed; G3) |
| D6 | R L101 | P L629 | captured |
| D7 | R L102 | P L627 | captured; decided |
| D8 | R L103 | P L636 | captured; decided |
| E1 | R L109 | P L284 | captured; decided |
| E2 | R L110 | P L284 | captured |
| E3 | R L111 | P L285 | captured; decided |
| **E4** | R L112 | SM-5 only | **missing** as an FR consequence (G3) |
| E5 | R L113 | P L445 | captured |
| **E6** | R L114 | SM-5 only | **missing** as an FR consequence (G3) |
| F1 | R L120 | P L595 | captured; decided |
| F2 | R L121 | P L596 | captured; decided |
| F3 | R L122 | P L506, L628 | captured; decided; interaction gap G1 |

In total: 28 explicit, 4 implicit (A1, A4, A5, A8), 1 partial (B4) and 5 without an FR home (C6, D1, D5, E4, E6). Of the five, C6 and D5 matter. D1, E4 and E6 are one line each.

### Groups G, H and I (uncited items)
- **G1** (R L128): missing. It applies in Step 2 (G5).
- **H19, H22** (R L178, L181): implicit through the group-H blanket only, and conflicting with "never told a Sauna" (G5).
- **H20** (R L179): self-contradictory and flagged at Add L260, but not excluded from the blanket (G5).
- **I1–I10, I20, I21:** Vision; n/a (Rec 8).

## 7. (c) Confidence check

| # | Location | PRD claim | Research basis | Status | Fix |
|---|---|---|---|---|---|
| C-1 | P L509 (FR-31), L872 (SM-5) | "Catalogue groups A and B hold as written"; "Catalogue groups A to F pass" | The catalogue is derived from the spec (R L30, L54). B4 breaks the 10-Seat cap and D5 breaks FR-13. The "Then" of E1/E3 is a failure, and the "Then" of D7, D8 and F1–F3 is an open decision | over-claims that the catalogue can run as written | G3 wording: "with addendum B applied, B4 and D5 rewritten" |
| C-2 | P L886 (Q5) | "The research recommends derived Placement, proven by the model-based test" | R L252: low–medium confidence, no practitioner source. The test does not exist yet | reads as already done | "…to be proven by the model-based test (FR-31); low–medium confidence, no practitioner source (addendum A)" |
| C-3 | P L254 (§4.3), L263 (FR-10) | "The data store itself refuses a write that would exceed it"; "How the same guarantee is enforced once Whole-sauna bookings and Blocks…" | R L43: no store-level constraint covers the cross-kind rule (Add L16 says so) | fine for the Core; "the same guarantee" can be read as store-level beyond it | Add to FR-10: "Beyond the Core, no store-level constraint was found; the guarantee rests on one serialised transaction per Window, proven by group C (addendum A)" |
| C-4 | Add L11, L19, L23, L25 | "High for the SQLite mechanism"; "low–medium"; "inference, to be proven" | R L42, L252, L45 | captured honestly | — |
| C-5 | P L699 | "Codes for two different Windows on the same door always differ; the simulated lock rejects a duplicate PIN" (untagged) | Part of H6 (R L145), which is deferred (PM L28) | minor | It holds under every H6 option. Log it in the memlog or tag it (M-11) |
| C-6 | Add L268 | Notes the appendix-vs-memlog mismatch only for the concurrency research | This report has the same mismatch: its appendix marks [2], [3], [4] high, and its memlog L12–14 lists them as unverified | minor | Add one line. The PRD does not lean on these sources |

## 8. Decided items (not gaps)

| Item | Decision line | PRD location |
|---|---|---|
| D3, D7, D8, F1, F2, F3 | PM L27 | P L595–596, L622–628, L636 |
| Strict whole-sauna rule, seats(W) ≤ P(S) | PM L27 (finding at PM L22) | P L480, L472; Add L67 |
| H10, H13, H23 | PM L27 | P L698, L707, L730 |
| H6 deferred | PM L28 | P L700, L882; Add C |
| E1/E3 (venue-wide, no partial overlap, per-sauna deviation is a Block) | BM L118 | P L118, L280–285 |
| H12 (no rule depends on revoking; refuse a whole booking after the Send time) | BM L119 | P L702–706 |
| Invariants, not moves; stored vs derived is architecture; one-Sauna access frozen at the Send time (H21) | BM L120 | P L498–506, L886, L729 |
| v0's "D7, D8, F1, F2, H6, H12 as `[ASSUMPTION]`" | PM L11, **superseded** by PM L27–L28 and BM L119 | — |
| Still open and correctly tagged: H11, H14, H15 (brief addendum L304; BM L121) and I11–I23 | BM L121 | P L708–712, L894 |

## 9. Minor fixes

- **M-1.** Add L71 (F1) says "The research gave no recommendation". The research lists refusal first, with D3-style handling as the alternative, and asks for a decision (R L120). The brief's research-input table (brief addendum L164) records refusal as the recommended answer. Reword the row to match.
- **M-2.** §12 Q4 (P L885) says the capacity research "checked SQLite's transaction rules". It also covered PostgreSQL: Serializable with retry on 40001, and the limits of exclusion constraints (R L43). Add that, so the architecture reads both.
- **M-3.** At P L514, widen the model-based test's actions to: Seat bookings, Whole-sauna bookings, Changes, cancellations, Blocks and lifted Blocks, Whole-booking-only marks and releases, and Fill-order and Capacity changes. This answers R L265 ("blocks and whole bookings together"), and matches FR-31's own trigger list at P L499.
- **M-4.** At P L118, L281 and L594, change "partly overlap" to "overlap" (touching end-to-start stays allowed). That makes nested and duplicate Windows explicit, since they break capacity the same way as E1.
- **M-5.** P L647 (FR-42) says the fallback "exists for Blocks in Windows that have started". FR-40 L622 applies the same latest-loses rule to any Block that leaves too little Seat capacity (D3, D6). Align the wording.
- **M-6.** FR-29 (P L480) omits held Seats; addendum A L31 has them. Add "(plus Seats held, once §4.11 exists)".
- **M-7.** D3 does not say whether a Whole-sauna booking of another Sauna can be the "latest Booking" that loses. Cancelling it would restore Seat capacity. R L98 has only Seat bookings, and P L622–623 is silent. Decide; the suggested default is that only Seat bookings lose.
- **M-8.** Make A3 testable with numbers (P L511): "a further cancellation of 2 Seats at [7,10,2,0] gives [7,10,0,0], and Sauna 3 can be booked whole at once". Qualify B7 (P L487) with "for a Sauna open for Seats": an unreleased Whole-booking-only Sauna (P L489) is already excluded, so Seats left does not drop.
- **M-9.** H4's door-code override on a Block (P L689) has no defining FR. Add it in Step 2 terms to FR-40 or FR-45.
- **M-10.** Three Step 2 clauses are missing:
  - H5 (P L688): "A Booking whose only Sauna has no self-service lock gets no Door-code email."
  - H15 (P L709): "If the shared code is replaced, every remaining booker of that door gets the new code."
  - H11 (P L711–717): "An entered code can be changed until the email is sent."
- **M-11.** Add one memlog line (or a tag) for the "codes always differ / reject duplicate PIN" sub-rule of the deferred H6 (C-5).
- **M-12.** FR-48 (P L708) limits the extra email to lifted Blocks (H14). The same applies to a Release after the Send time.
- **M-13.** In UJ-6 Climax (P L108), change "Seat bookings move into other open Saunas" to "are counted into", to match FR-40 and Rec 1.
