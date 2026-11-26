---
title: 'Booking list: pick the date from a pop-up calendar'
type: 'feature'
created: '2026-11-26'
status: 'done'
baseline_commit: '543fab790b6338a6b6983870fa7fac24e1203965'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/.docs/planning-artifacts/ux-designs/ux-booking-platform-2026-11-05/DESIGN.md'
  - '{project-root}/frontend/AGENTS.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** On the Administrator Booking list (`/admin/bookings`, FR-16) the only way to reach a date more than a day or two away is to type it as dd.mm.yyyy. Reception staff want to pick it.

**Approach:** Next to the date Text field, a "Choose from calendar" button opens a pop-up month calendar. Picking a day goes to that date's list, exactly as a typed date does. The Text field, "Previous day" and "Next day" stay as they are.

**Decision (Lisa, 2026-11-26):** the site's own pop-up calendar, not the browser's native date picker.

## Boundaries & Constraints

**Always:**
- The pick goes through the same address as today (`/admin/bookings?date=yyyy-mm-dd`, `router.replace`), so reload and Back behave as for a typed date.
- No clock is read in the browser (AD-4): the pop-up opens on the month of the date shown, which comes from the address or the API's `date`.
- Every day of every month can be picked, past and future: Booking list dates are not limited by FR-2's booking rules (EXPERIENCE.md "Booking list" assumption).
- Looks as the Date calendar in DESIGN.md: square corners, `cal-*` cell styles, the shown date selected as Primary button; the pop-up sits on `{colors.surface}` with a 1 px `{colors.border}`.
- Accessible (FR-23, WCAG 2.2 AA): the toggle states `aria-expanded`; the pop-up is a named group ("Pick a day, November 2026"); days are buttons named with `fullDate` ("14 November 2026"), the shown one with `aria-current="date"`; on open, focus goes to the shown day; Escape closes and returns focus to the toggle; a click outside closes it; targets at least 24 × 24 px.
- Copy lives in `frontend/lib/copy.js`.

**Never:**
- No date-picker library and no native `<input type="date">`.
- No change to the API, the Text field's typed behaviour, or the guest Date calendar (`DateCalendar.js`).
- No marking of days that have bookings (would need a new API read).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Pick a day | List shows 26.11.2026; open, click 3 | Address `?date=2026-11-03`; field shows 03.11.2026; pop-up closed | N/A |
| Other month | Open, "Next month", click 5 | `?date=2026-12-05` | N/A |
| Past month | Open, "Previous month" twice | October and September 2026 shown, all days pickable | N/A |
| Same day | Click the shown day | Pop-up closes, no navigation | N/A |
| Escape / outside click | Pop-up open | Closes, no navigation; Escape returns focus to the toggle | N/A |
| Field error showing | Typed "32.13.2026", then pick 4 | Error cleared, `?date=…-04` | N/A |

</frozen-after-approval>

## Code Map

- `frontend/components/BookingList.js:151-235` -- `BookingList`: `shown` (ISO date on screen), `commit()` (typed date → `router.replace(dayHref(iso))`), the `date-bar` markup. Add the toggle and pop-up inside `.date-bar-field`; picking reuses `dayHref` and clears `error`.
- `frontend/components/DateCalendar.js` -- guest calendar; reuse its month head / weekday / grid markup and `cal-*` classes as the model, but do not import or change it (its `MonthGrid` is radio-based and horizon-bound).
- `frontend/lib/dates.js` -- reuse `WEEKDAYS_SHORT`, `isoDate`, `daysInMonth`, `weekdayIndex`, `monthLabel`, `monthOf`, `addMonths`, `fullDate`, `dotted`.
- `frontend/lib/copy.js` -- `BOOKING_LIST` (add `chooseFromCalendar`), `BOOK.previousMonth`, `BOOK.nextMonth`, `BOOK.pickADay(label)` to reuse.
- `frontend/app/styles.css:642-736` (`.cal-*`), `:574` (`.link-button`), `:1493-1510` (`.date-bar*`) -- extend with a `.date-pop` pop-up and `.cal-pick` day buttons.
- `tests/e2e/test_fr16_booking_list.py` -- existing date tests and helpers (`a11y.tab_to`, `a11y.press`, `#date` waits); add the new ones here.
- `.docs/planning-artifacts/ux-designs/ux-booking-platform-2026-11-05/EXPERIENCE.md:390` -- Booking list date assumption to update.

## Tasks & Acceptance

**Execution:**
- [x] `frontend/components/DayPickerPopup.js` -- new client component `{ date, onPick }`: toggle button + pop-up with Previous/Next month (unbounded), weekday heads and day buttons; Escape, outside click, focus handling as in Boundaries -- keeps BookingList readable.
- [x] `frontend/components/BookingList.js` -- render it in `.date-bar-field` with `date={shown}`; `onPick` clears `error`, sets `text`, and `router.replace(dayHref(iso))` when `iso !== shown`; update the header comment.
- [x] `frontend/lib/copy.js` -- add `BOOKING_LIST.chooseFromCalendar: 'Choose from calendar'`.
- [x] `frontend/app/styles.css` -- `.date-pop` (absolute under the field, surface, border, padding, above content) and `.cal-pick` buttons matching `.cal-day span` / selected state.
- [x] `tests/e2e/test_fr16_booking_list.py` -- tests for the I/O matrix rows and a keyboard-only pick (Tab to toggle, Enter, move with Tab, Enter on a day).
- [x] `EXPERIENCE.md` -- replace the line-390 assumption with the decided behaviour; `README.md` -- mention the calendar where the Booking list is described.

**Acceptance Criteria:**
- Given the Booking list, when the pop-up is open, then axe reports no violations (existing `a11y` helper).
- Given 200 % zoom at 1280 px, when the pop-up is open, then it is fully visible without horizontal scrolling.

## Implementation Notes

## Spec Change Log

## Review Triage Log

| # | Layer | Finding | Verdict | Evidence | Route |
|---|-------|---------|---------|----------|-------|
| 1 | edge-case, blind | Tab out of toggle/pop-up leaves it open; Escape then unheard | medium | No focusout handling and Escape bound to the root only; reproduced by reading `DayPickerPopup.js`. | patch: root `onBlur` closes when focus moves outside; test `test_tab_out_of_the_calendar_closes_it` |
| 2 | blind | Escape not heard when a mouse click leaves focus on body (Safari) | low | Safari does not focus buttons on click; root `onKeyDown` never fires. Direct fix. | patch: document `keydown` listener while open |
| 3 | edge-case | Typed date in another month + click on toggle: blur commit changes date after open, focused day unmounts | medium | Blur commit runs `router.replace`; `[date]` effect moves the month and the focused button is removed. | patch: `wantFocus` ref refocuses the shown day after the month re-renders; test `test_a_typed_date_in_another_month_then_the_toggle` |
| 4 | edge-case | Years outside 1000-9999 by clicking months | low | Needs ~11,000 clicks; fix adds a guard. Rejected (unlikely, not a direct correction). | reject |
| 5 | edge-case (claim) | Unbounded picking breaks at extreme years | low | Same as 4. | reject |
| 6 | blind | Month change not announced | low | Only the group's aria-label changes while focus stays on the month button. Direct fix. | patch: `aria-live="polite"` on `.cal-month` |
| 7 | blind | `aria-current="date"` means today | false | ARIA defines it as the current date within a collection; the frozen intent chose it for the shown date. Changing it would edit the spec. | reject |
| 8 | blind | Clicking the toggle with half-typed text commits the field first | false | The Text field's typed behaviour (commit on blur) must stay unchanged per Never; the focus side effect is covered by 3. | reject |
| 9 | blind | Toggle `nowrap` can overflow the 348 px column with enlarged text | low | Fixed px column, nowrap button, shrinking field. Direct CSS fix. | patch: `.date-bar-control` wraps; field `flex-basis: 8em` |
| 10 | blind | DESIGN.md not updated for the new component | low | DESIGN.md Components is the visual source; the pop-up was undescribed. | patch: "Booking list day picker" bullet |
| 11 | blind | New tab order undocumented; change log empty | false | No spec changes were made; the tab order follows DOM order and the existing test was updated. No named harm. | reject |
| 12 | blind | Verification not recorded | false | Build and both pytest files ran green in-session (33 passed). | reject |
| 13 | blind | No arrow-key navigation in the grid | false | Intent's keyboard path is Tab between day buttons; a design choice, not a defect. | reject |
| 14 | blind | Header comment describes an impossible fallback | low | Toggle resets the month before open. Direct fix. | patch: comment rewritten, fallback removed |
| 15 | blind | Next/past-month tests check only the URL | low | Close, aria-expanded and focus return unasserted. | patch: assertions added to next-month test |
| 16 | blind | Grid maths tested on one fixed month set | low | Covered by 17. | patch (via 17) |
| 17 | verification-gap | Leading blank cells never checked against weekday columns | low | Filed pre-verified. | patch: `assert_under_its_weekday` in four months |
| 18 | blind | `.date-pick` has no CSS / extra flex child | low | Harmless, but made the flex item explicit. | patch: `.date-pick { flex: none; }` |
| 19 | verification-gap | Picking the shown day with a Field error not tested | low | Filed pre-verified. | patch: added to `test_a_pick_clears_the_field_error` |
| 20 | verification-gap | Reopen after month change not tested to return to shown month | low | Filed pre-verified. | patch: added to Escape test |
| 21 | verification-gap | Toggle closing the pop-up not tested | low | Filed pre-verified (disposition defer); a three-line addition. | patch: added to Escape test |

## Verification

**Commands:**
- `npm --prefix frontend run build` -- expected: succeeds
- `uv run pytest tests/e2e/test_fr16_booking_list.py tests/e2e/test_fr23_accessibility.py` -- expected: all pass
