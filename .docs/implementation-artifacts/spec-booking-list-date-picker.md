---
title: 'Booking list: pick the date from a pop-up calendar'
type: 'feature'
created: '2026-11-26'
status: 'ready-for-dev'
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
- [ ] `frontend/components/DayPickerPopup.js` -- new client component `{ date, onPick }`: toggle button + pop-up with Previous/Next month (unbounded), weekday heads and day buttons; Escape, outside click, focus handling as in Boundaries -- keeps BookingList readable.
- [ ] `frontend/components/BookingList.js` -- render it in `.date-bar-field` with `date={shown}`; `onPick` clears `error`, sets `text`, and `router.replace(dayHref(iso))` when `iso !== shown`; update the header comment.
- [ ] `frontend/lib/copy.js` -- add `BOOKING_LIST.chooseFromCalendar: 'Choose from calendar'`.
- [ ] `frontend/app/styles.css` -- `.date-pop` (absolute under the field, surface, border, padding, above content) and `.cal-pick` buttons matching `.cal-day span` / selected state.
- [ ] `tests/e2e/test_fr16_booking_list.py` -- tests for the I/O matrix rows and a keyboard-only pick (Tab to toggle, Enter, move with Tab, Enter on a day).
- [ ] `EXPERIENCE.md` -- replace the line-390 assumption with the decided behaviour; `README.md` -- mention the calendar where the Booking list is described.

**Acceptance Criteria:**
- Given the Booking list, when the pop-up is open, then axe reports no violations (existing `a11y` helper).
- Given 200 % zoom at 1280 px, when the pop-up is open, then it is fully visible without horizontal scrolling.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `npm --prefix frontend run build` -- expected: succeeds
- `uv run pytest tests/e2e/test_fr16_booking_list.py tests/e2e/test_fr23_accessibility.py` -- expected: all pass
