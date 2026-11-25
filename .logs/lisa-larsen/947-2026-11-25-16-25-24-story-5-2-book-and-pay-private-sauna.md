# Story 5.2: Book and pay for a private sauna

## 2026-11-25 kl. 16:25 — Lisa Larsen

### Oppgave
Starte Story 5.2 (bestille og betale en privat badstue) med `bmad-build`. Økten stoppet etter godkjent spec ("Godkjenn og stopp"); implementeringen tas i en ny `bmad-build`-økt.

### Plan
- `bmad-build` steg 1–2: lastet `epic-5-context.md`, spec 5.1 og Story 5.2 i epics.md, undersøkte Seat-flyten (`services/booking.py`, `db/__init__.py:run`, `api/schemas.py`, `services/voucher.py`, `services/manage.py`, `db/booking_list.py`, frontend `Review`/`Details`/`draft.js`).
- Spec: [spec-5-2-book-and-pay-for-a-private-sauna.md](../../.docs/implementation-artifacts/spec-5-2-book-and-pay-for-a-private-sauna.md)

### Resultat
- Ny branch `story/5-2-book-and-pay-private-sauna` fra `f64b83c` (tar med loggcommiten for 5.1).
- Spec skrevet og godkjent, status `ready-for-dev`, route `dispatch` (ukommittert i arbeidskopien).
- Lisas beslutninger (i specens frosne blokk):
  - `content/terms-whole.json` får endelig FR-33-tekst nå: "A booking for a fixed date cannot be withdrawn." / "Up to 72 hours before the session starts, you can cancel for a refund or a voucher, or move the booking to another session." / "If Saunalöyly cancels your session, you choose a refund or a voucher."
  - Før 5.3 viser Manage-siden en hel-badstue-booking uten handlinger; Seat-endepunktene for flytt/voucher avviser den med `404 not_found`.
  - Specen beholdes hel (ca. 3000 tokens).
  - Subagenter godkjent for implementering og review.
- Valgt i specen: `sauna_unavailable` mappes per handling via en overstyring i `db.run` (globalt `MAP` uendret); nye ruter `/private-sauna/details` og `/private-sauna/review` med de eksisterende komponentene; `BookingIn` diskriminert på `kind` med `'seats'` som standard.

### Åpne punkter
- Implementere Story 5.2 etter specen (ny `bmad-build`-økt starter på steg 3).
- Føre terms-whole-teksten inn i EXPERIENCE.md ("Private sauna wording") under implementeringen.
