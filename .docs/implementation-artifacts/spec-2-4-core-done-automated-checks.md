---
title: 'Story 2.4 (part A): Core done — the automated checks'
type: 'feature'
created: '2026-11-21'
status: 'done'
baseline_commit: '8865f62ff4c5b882a55032f4ef3e6df287dd126d'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/.docs/planning-artifacts/epics.md'
  - '{project-root}/.docs/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The Core's accessibility, privacy and log checks are spread over per-story e2e files, and the ones Story 2.4 names do not exist: no single pass over every Core page and state, no automated keyboard/zoom pass of the booking flow (FR-23), no privacy checks on the Administrator pages (FR-21, AD-17), no log check after Bookings (AD-19), and the asset test checks only one direction (DR-3).

**Approach:** Build the automated part of Story 2.4 (`.docs/planning-artifacts/epics.md` L990–1021): two new e2e files, extensions of `test_fr21_privacy.py` and `test_dr3_assets.py`, and a fix in this story for any failure they reveal. Part B (README, fresh clone, manual passes, Core-done log) is deferred (`deferred-work.md`, 2026-11-21).

## Boundaries & Constraints

**Always:**
- Every keyboard step goes through `a11y.press`/`a11y.tab_to`/`a11y.tab_order`; every URL comes from `base_url`; every compose call through `stack.compose`.
- `test_fr23_accessibility.py` visits each Core page in each state below, and runs `a11y.check_axe` and `a11y.no_horizontal_scroll` (1024, 1366, 1920) there. `a11y.KNOWN_GAPS` is pinned to exactly `{"wcag1410"}`.
- States: Landing and `/#before-you-come`; Book seats empty, with its Error summary (Continue with nothing chosen), and with a sold-out Session listed; Details with its Error summary; Review, and Review with a refusal Notice; Confirmation; Terms; Privacy notice; Sign-in, and with its Error summary; Booking list with a sold-out Session; Outbox; the not-available page (`/nope`).
- Tests that change data clean up after themselves (as `test_fr02_book_seats.py`'s `db` fixture and `test_fr11_refusals.py`'s `fill` do), so other modules still see what they expect.
- A failure an automated check reveals in product code is fixed in this story; one that cannot be fixed is recorded as an issue with its WCAG criterion.

**Never:** Rewrite the README, add `tests/manual/`, or touch the Core-done session-log entry (part B). Remove or weaken existing tests. Add a dependency. Relax `check_axe` or add a known gap.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected |
|---|---|---|
| Book seats tab order | date and 2 Seats chosen, focus from the top | the stops for `#date`, the calendar, `#seats-*` and a Session radio all come before "Continue booking" |
| Session list names | a date with one Session at 1 Seat left and one full, 2 Seats chosen | `ariaSnapshot` of `.session-rows` shows "HH:MM to HH:MM, N seats left" for open rows and disabled rows "… 1 seat left, not enough for 2" and "… Sold out" |
| Zoom 1366×768 and 1920×1080 | `a11y.zoomed` page from Book seats | Book seats, Details and Review completed by keyboard alone; Continue booking and Pay pressed; Confirmation reached; full-page PNGs of Book seats, Details, Review in `test-results/zoom/` named by page and screen |
| Anonymous admin | `/admin`, `/admin/bookings`, `/admin/outbox` | ends on `/admin/sign-in` |
| Sign-in privacy | open Sign-in, sign in, open Booking list, then Outbox | exactly one cookie `bp_session`; every request to `base_url`'s origin; each page exactly one stylesheet of ours and no `<style>` |
| Logs | browser booking with a unique name and email, sign-in, sign-out | `stack.compose("logs","--no-color")` contains none of: the test password, any `bp_session` value seen, the unique name, the email, the JSON request body; it does contain `POST /api/bookings` (access log is on) |
| Asset rows | `ASSETS.md` | every `images/…`/`fonts/…` path named in a row's first cell exists under `frontend/public/`, and the row has a source link; a test with a temp dir proves a missing file is named |

</frozen-after-approval>

## Code Map

- `tests/e2e/a11y.py` -- `press`, `tab_to`, `tab_order`, `check_axe` (`KNOWN_GAPS`), `no_horizontal_scroll`, `zoomed`. Reuse only; no change expected.
- `tests/e2e/conftest.py` -- `stack` (`compose`, `db_port`), `base_url`.
- `tests/e2e/guest.py` -- `free_windows`, `open_session`, `book_in_browser`. `tests/e2e/admin.py` -- `LOGIN`, `no_throttle` (import it so it applies), `open_sign_in`, `type_login`, `db_url`.
- `tests/e2e/test_fr05_book_and_pay.py:37-50,57-128` -- `set_draft`, `review_draft`, and the keyboard flow Landing → Confirmation to copy for the zoom test.
- `tests/e2e/test_fr02_book_seats.py:34-68,264-285` -- `facts`, `full_day`, `open_page`, `choose_by_typing`, `db` fixture with cleanup (deletes `blocks` and `bookings WHERE name='E2E fill'`).
- `tests/e2e/test_fr11_refusals.py:42-105` -- `fill(db, window, seats)` and `to_review`, `pay`, `refusal_notice` for the Review refusal state.
- `tests/e2e/test_fr16_booking_list.py:47-66,143-159` -- `sign_in`, `open_day`, the seeded sold-out day. `tests/e2e/test_fr17_outbox.py:37-50` -- `sign_in`, `open_outbox`.
- `tests/e2e/test_fr15_sign_in.py:129-140` -- existing password/token log test; the new log test is broader, keep this one.
- `tests/e2e/test_fr21_privacy.py` -- extend with the Administrator rows; keep its origin/stylesheet assertions' shape.
- `frontend/components/SessionList.js:15-41` -- row `aria-label` and `availability()`; `lib/copy.js:30-32` `soldOut`, `notEnough`.
- `tests/test_dr3_assets.py` -- add `missing_files(public, text)` beside `missing_rows`, same style.
- `.gitignore:38` -- `test-results/` already ignored.

## Tasks & Acceptance

**Execution:**
- [x] `tests/e2e/test_fr23_accessibility.py` -- every page and state above with axe and the three widths; `KNOWN_GAPS` pinned -- FR-22, FR-23
- [x] `tests/e2e/test_fr23_keyboard_and_zoom.py` -- Book seats tab order, Session list `ariaSnapshot`, zoomed keyboard flow with screenshots -- FR-23, WCAG 1.4.4, 2.4.3, UX-DR19, UX-DR35
- [x] `tests/e2e/test_fr21_privacy.py` -- anonymous admin redirects, Sign-in cookie, origin and stylesheet on Sign-in/Booking list/Outbox, the log check -- FR-21, AD-17, AD-19
- [x] `tests/test_dr3_assets.py` -- rows point to existing files with a source -- DR-3
- [x] product code, only if a check fails -- the smallest fix, noted in Implementation Notes

**Acceptance Criteria:**
- Given `uv run pytest`, then every test passes, including those of Stories 1.1–2.3.
- Given `npm --prefix frontend run build`, then it succeeds.
- Given the e2e run, then `test-results/zoom/` holds six PNGs and `git status` does not list them.

## Implementation Notes

- No check failed, so no product code changed (task 5 needed no fix).
- `test_fr23_accessibility.py` runs one parametrized test per state (16) plus `test_the_only_known_gap_is_reflow`. The sold-out states use the seed's full session (today + 3, 19:00); the Review refusal fills the Window with `RAW_FILL` after Review loads, and its `db` fixture deletes the `E2E fill` rows.
- The Book seats tab order is taken after a reload (the draft is restored and nothing has focus), stepping with `a11y.press("Tab")` until "Continue booking" has focus.
- The log check builds the booking request itself (not `guest.book_in_browser`, whose email is fixed) so the name, the email and the exact JSON body are unique to the test.
- `test_dr3_assets.py` gets `asset_rows` and `missing_files`; a source counts when the row holds a Markdown link to `http(s)://`.
- Seen in the 200 % screenshots, for the manual zoom pass (part B): at 683 px the email on Review wraps inside the word, and the two-column shell keeps a mostly empty rail (1.4.10 Reflow territory).
- Verification: `uv run pytest -q` 536 passed (12 min 32 s); `npm --prefix frontend run build` succeeded; the six PNGs are under `test-results/zoom/` and git ignores them.

## Spec Change Log

## Review Triage Log

| # | Source | Location | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|---|---|
| 1 | verification-gap, blind | `test_fr21_privacy.py` log test | no refused sign-in or refused booking body before the logs are read; idempotency key unchecked | medium | `services/auth.py:122` logs on refusal and `api/errors.py` logs on 4xx; no test reads the logs after either path | patch |
| 2 | blind, edge-case, verification-gap | `test_fr21_privacy.py` log test | `cookies()[0]` assumed to be `bp_session`; no token collected after sign-out | low | direct correction: read the cookie by name, collect after sign-out | patch |
| 3 | blind | `test_fr21_privacy.py` log test | exact-string search misses an escaped body | low | an escaped body still holds the 16-hex marker; checking the marker alone is a direct addition | patch |
| 4 | blind, verification-gap | `test_fr21_privacy.py` `_same_origin` | name says the opposite of what it returns | low | renamed `_other_origins` | patch |
| 5 | blind, edge-case | `test_fr21_privacy.py` `_one_stylesheet_of_ours` | `href=None` raises AttributeError | low | `(sheets[0] or "")` gives the assertion with the sheets | patch |
| 6 | blind, edge-case | `test_fr23_keyboard_and_zoom.py` tab order | `next()` raises bare StopIteration; `order[-1] < len(stops)-1` always holds | low | default `None` + `assert None not in order`; vacuous assertion removed | patch |
| 7 | blind | `test_fr23_keyboard_and_zoom.py` zoom | old screenshots satisfy the size check | low | each run unlinks its three files first | patch |
| 8 | edge-case | `test_dr3_assets.py` `missing_files` | `is_file()` ignores case on Windows | low | compared against the exact relative paths | patch |
| 9 | verification (rerun) | `test_fr23_keyboard_and_zoom.py` `choose` | `networkidle` can return before the 2-Seat re-read, so Tab lands on rows that are then replaced (1 in 5 runs) | medium | seen failing at `choose` line 66; now waits on the `/api/windows?…seats=2` response; 4 clean repeat runs | patch |
| 10 | edge-case | `test_fr21_privacy.py` log test | logs read before sign-out lines are flushed | low | sign-out has no body and the access log does not hold cookies; a poll adds complexity | reject |
| 11 | edge-case, blind | `test_fr23_accessibility.py` sold-out states | today + 3 breaks if a run crosses midnight | low | same assumption as `test_fr16_booking_list.py:143`; unlikely, fix adds an API scan | reject |
| 12 | edge-case, blind | `test_fr23_keyboard_and_zoom.py` Session names | assumes rows 0/1 are 10:00/11:30 | low | the API lists Windows in time order and the seed schedule starts 10:00 every 1 h 30 (`test_fr02` pins `SLOTS`) | reject |
| 13 | blind | new e2e tests | Bookings made by tests are never removed | false | the e2e stack is created per run and removed with `down -v`; `free_windows` only skips used dates | reject |
| 14 | blind | new e2e files | duplicated `db`, `dotted`, mixed import sources | low | style only; same pattern in the existing modules, no caller diverges | reject |
| 15 | blind | `test_fr23_accessibility.py` | missing states (filled Details, empty Outbox, throttled Sign-in, after sign-out) | false | the frozen state list is the story's; filled Details is in `test_fr05:130`, empty Outbox in `test_fr17:140` | reject |
| 16 | blind | zoom test | axe and scroll not run in the zoomed layout | low | the story asks for completion and screenshots; axe at 200 % already runs for Terms/Privacy (`test_fr22`) | reject |
| 17 | blind | privacy tests | no session-rotation or cookie-attribute check; API refusals for anonymous callers | false | rotation in `test_fr15_sign_in.py:46`, attributes in `test_fr21_privacy.py` Book seats test, 401s in `tests/test_fr20_access.py` | reject |
| 18 | blind, edge-case | `test_dr3_assets.py` | source link anywhere in the row; only `images/`/`fonts/` rows checked | low | the two tables have different columns; `frontend/public/` holds only images and fonts, and `missing_rows` covers every file | reject |

## Verification

**Commands:**
- `uv run pytest -q` -- expected: all pass
- `uv run pytest -q tests/e2e/test_fr23_accessibility.py tests/e2e/test_fr23_keyboard_and_zoom.py tests/e2e/test_fr21_privacy.py tests/test_dr3_assets.py` -- expected: all pass
- `npm --prefix frontend run build` -- expected: success
