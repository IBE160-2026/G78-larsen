# Manual accessibility passes — Core (FR-23)

The manual passes confirm the automated checks; they do not repeat them. Run them on the compose stack
(`docker compose up --build --wait`, then `http://localhost:8000`). Screen-reader pass: NVDA with Chrome.
A failure is fixed in the story that finds it, or recorded in `.logs/lisa-larsen/issues.md` with its WCAG criterion.

| # | Check | What to look for | Date | Browser (+ screen reader) | Outcome | Covering automated test |
|---|---|---|---|---|---|---|
| 1 | Keyboard only: Landing → Book seats → Details → Review → Confirmation, then Sign-in → Booking list → Outbox → Sign out | An order that makes no sense, a stop that does nothing, a focus ring that cannot be seen | | | Pending | `tests/e2e/test_fr05_book_and_pay.py::test_keyboard_alone_from_landing_to_confirmation`, `tests/e2e/test_fr15_sign_in.py::test_sign_in_and_out_with_the_keyboard_alone`, `tests/e2e/test_fr16_booking_list.py::test_previous_and_next_day_with_the_keyboard_alone`, `tests/e2e/test_fr17_outbox.py::test_the_confirmation_of_a_browser_booking_from_the_bar_with_the_keyboard_alone` |
| 2 | 200 % zoom at 1366×768 and 1920×1080 (WCAG 1.4.4), plus the screenshots in `test-results/zoom/` from `uv run pytest` | Nothing cut off or overlapping; every control still reachable. Known from part A: at 683 px the email on Review wraps mid-word, and the rail stays mostly empty (1.4.10 territory, see README "Ikke levert") | | | Pending | `tests/e2e/test_fr23_keyboard_and_zoom.py::test_the_booking_flow_at_200_percent_zoom_with_the_keyboard_alone` |
| 3 | Book seats tab order, seen once against the `tab_order` test (WCAG 2.4.3) | Date field, calendar, Seat picker and Session list come before the rail's total and "Continue booking" | | | Pending | `tests/e2e/test_fr23_keyboard_and_zoom.py::test_book_seats_tab_order_puts_the_questions_before_continue` |
| 4 | Screen reader on Book seats, Review and Confirmation (UX-DR35) | Session rows are read with their Seats left ("13:00 to 14:30, 12 seats left"); unavailable rows are read as unavailable; Next.js's route announcer does not double the page announcement | | | Pending | `tests/e2e/test_fr23_keyboard_and_zoom.py::test_the_session_list_names_each_row_with_its_seats_left` |
