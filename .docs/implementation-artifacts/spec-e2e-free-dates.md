---
title: 'e2e: free dates stay free across a full run'
type: 'bugfix'
created: '2026-11-26'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** In a full `uv run pytest tests/e2e` run, e2e tests leave their bookings (and any holds or Blocks they add) on the store, so each one uses up a date. With a 28-day horizon there are only about 20 usable dates, so fixtures that need a date with no bookings run out: `tests/e2e/guest.py` `free_windows` ("no date without bookings") and `tests/e2e/test_fr30_private_sauna.py` `day`/`booking_day` ("no (second) later date without bookings"). On main 442cd02 (2026-11-26, 21:54) all 10 fr30 tests errored at setup and 5 fr24/fr33-cancel tests failed for the same reason; the result depends on run order and time of day.

**Approach:** Test-only change. One autouse, module-scoped fixture in `tests/e2e/conftest.py` records the highest id of `bookings`, `holds`, `blocks` and `marks` when a test module starts. When the module ends, it deletes, in one transaction on the stack's database (`admin.db_url(stack)`), every row the module added: the new Bookings with their dependent rows (`idempotency_keys`, `outbox_emails`, `payments`, `booking_changes` — also those whose `new_booking_id` is a new Booking — `vouchers`, `access_tokens`, `whole_bookings`) and the new holds, Blocks and marks. Rows that existed before the module (the seeded sample Bookings and their history) are never deleted. Cleanup runs per module, not per test, so tests in one module may still rely on each other's Bookings. No product code, migration or seed changes.

</frozen-after-approval>

## Implementation Notes

- One file: `tests/e2e/conftest.py` gains `module_leaves_no_rows` (autouse, module scope, takes `stack`) and its two SQL lists; the module docstring says what it guarantees. No test module changed; `guest.free_windows` and the fr30 fixtures keep their strict "no Booking at all" rule.
- The database URL is a new `Stack.db_url` property; `admin.db_url(stack)` now returns it, so the URL is written once (fr02, fr11 and fr15 still build it inline, as before).
- All deletes run in one transaction: deleting `whole_bookings` before `bookings` would otherwise trip the deferred `check_whole_pair` (`whole_pairing`) at a commit in between. The capacity triggers on DELETE recompute the Windows.
- A Change of an older Booking whose `new_booking_id` is a new Booking (a split during the module) is deleted too, with its emails and keys; otherwise the FK blocks the delete. Older Bookings themselves are never deleted or reverted.
- `releases` has no id and is removed by `marks`' own delete trigger (`trg_marks_cleanup`).
- On the 5.3 branch, `test_fr33_whole_move.py`'s `made` fixture does the same per test; with this fixture it becomes redundant but harmless.
- Verified: full `uv run pytest tests/e2e` on this branch (base main 442cd02), started 22:25 on 2026-11-26: 217 passed, 0 failed (13 min; main at 21:54 the same evening had 10 errors and 5 failures from used-up dates). After the review patches: fr15, fr17 and fr30 e2e, 28 passed.

## Review Triage Log

| # | Finding | Verdict | Evidence / route |
|---|---|---|---|
| 1 | The docstring promises "leaves the store as it found it", but changes to older rows stay | low | True: only rows above the id marks go. Direct rewording. Patched: the docstring says what is not undone |
| 2 | A split of an older Booking leaves it short of Seats after cleanup | low | Real only if a module splits a seeded Booking; restoring Seats needs new logic. Rejected; now named in the docstring |
| 3 | Older payments/Changes may point at a Voucher of a new Booking, so the Voucher delete fails | false | A payment is written when its Booking is made, and a Change's Voucher belongs to the Booking it changed, so an older row cannot point at a Voucher issued after the mark. The reverse case (an older Voucher spent) does not take up a date. Rejected |
| 4 | The database URL is duplicated from `admin.db_url` | low | Two copies of the credentials. Patched: `Stack.db_url`, used by both |
| 5 | A failed cleanup is hard to trace | low | The full run passed; better messages would add code for a failure nobody has seen. Rejected |
| 6 | Nothing checks that the store was restored | low | Same: adds code; the full run is the check. Rejected |
| 7 | The id marks break under `pytest-xdist` | false | `pytest-xdist` is not in `pyproject.toml` or `uv.lock`. One-process use is now stated in the docstring. Rejected |
| 8 | One large module can still exceed the date budget | low | No module uses more than a few dates. Rejected |
| 9 | The backend's own background writes may race the teardown | low | Unseen in the full run; the Outbox only stores emails. Rejected |
| 10 | "made is redundant but harmless" is untested | low | `made` exists only on the 5.3 branch; it deletes per test, so this fixture finds nothing left. To be confirmed when the branches meet. Rejected |
