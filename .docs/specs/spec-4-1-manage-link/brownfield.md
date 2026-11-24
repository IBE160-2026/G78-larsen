# Brownfield touchpoints (main @ 813c6d2)

| Where | Today | Story 4.1 |
| --- | --- | --- |
| `migrations/0001`–`0009` | last is `0009_retention.sql` | add `0010` (CAP-1) |
| `src/booking_platform/services/booking.py:79` `confirmation_email` | docstring says "No Manage link (Core)"; terms from `content.TERMS_SEATS` | add the Manage link line (CAP-2) |
| `services/booking.py:116` `create` | inserts Booking, payment, `outbox.send`, key | copy `cutoff_seats`; call `manage.issue` before building the email |
| `services/seed.py:188` `apply_bookings` | creates samples via `booking.create`, skips known keys | also issue for known samples lacking an unrevoked token (CAP-3) |
| `services/sessions.py` `token_hash`, `open_session`, `purge_expired` | session token hashing and startup purge | reuse hashing; add grant purge at startup (CAP-7) |
| `services/outbox.py:20` `link(path)` | absolute link from base URL; `config.links` holds paths | add `manage` path; fragment `#t=` appended by `services.manage` |
| `api/deps.py` | `current_session`, `require_session`, CSRF `same_origin` | new manage-grant dependency; no `401` |
| `api/errors.py` + `frontend/lib/api.js` (code→status mirror) + `frontend/lib/copy.js` (page copy) | refusal code table, mirror and copy | add `cutoff_passed` (fact `cutoff_at`) and its text |
| new `api/manage.py`, `services/manage.py` | — | router `/api/manage/…` (AD-28) |
| `frontend/components/NotAvailable.js` | "This page is not available." page, used after API 404 | reuse for CAP-5 |
| `frontend/components/FocusMover.js` | focus to `h1` after client navigation | `/manage` → `/manage/[reference]` must hit it |
| `content/terms-seats.json`, `frontend/content/terms-seats.json` | contain "A booking cannot be changed or refunded." | replace (CAP-9) |
| `frontend/app/terms/page.js:50-51` | "Changes and refunds" with the old sentence | replace |
| `tests/test_fr08_confirmation.py:48`, `tests/e2e/test_fr05_book_and_pay.py:23` | assert the old sentence | update |
| `Caddyfile` | `@manage path /manage* /api/manage /api/manage/*` → `X-Robots-Tag noindex`; `Referrer-Policy` global | no change expected; e2e asserts it |
| `tests/e2e/test_fr21_privacy.py` | Core pages only | add the Manage page |
