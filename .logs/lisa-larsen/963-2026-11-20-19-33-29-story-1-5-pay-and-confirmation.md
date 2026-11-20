# Story 1.5: A Guest pays and gets a confirmation

## 2026-11-20 kl. 19:33 — Lisa Larsen

### Oppgave
Kjøre `bmad-build` for Story 1.5 («a guest pays and gets a confirmation») og ta med tre åpne punkter fra tidligere logger: FK-ene til `sessions` skal gi `no_session` (401), migreringen for `bookings.status` får neste ledige nummer (spinen rettes), og to Notice-tekster og `nearest`-regelen fra 1.4 avklares før 1.5 bygger videre.

### Plan
- `bmad-build` steg 1 (avklaring) og steg 2 (planlegging). Implementeringen tas i en ny sesjon for å få et rent kontekstvindu (Lisa valgte «Godkjenn og stopp»).
- Epic-konteksten `epic-1-context.md` ble brukt som den var. UX-filene er nyere, men endringen gjelder bare bildestier (Story 1.3).
- En Explore-underagent kartla backend, tester og frontend. Spesifikasjonen ble skrevet fra den kartleggingen, spinen (AD-3/7/8/9/12/13/14/16/17/20), EXPERIENCE.md og `key-confirmation.html`.
- Spesifikasjon: [spec-1-5-pay-and-confirmation.md](../../.docs/implementation-artifacts/spec-1-5-pay-and-confirmation.md), `status: ready-for-dev`, `route: dispatch`.

### Resultat
- Spesifikasjonen er skrevet og godkjent. Den er ikke committet; den ligger som ny fil i arbeidskopien på `main`.
- Avgjørelser Lisa tok i økten:
  - De to Notice-tekstene fra 1.4 er godkjent: «The session you chose no longer has room for N seats. Choose another session.» og «The sessions could not be loaded, please try again.»
  - `nearest` i `GET /api/windows` kommer bare når både `date` og `seats` er gitt (og ingen økt den dagen har plass). Dagens kode (`services/windows.py:141`) er riktig.
  - Seed-bookingene er godkjent (vist i nettleseren): +1 dag 14:30 2 plasser, +2 dager 17:30 42 av 44, +3 dager 19:00 fullt, +5 dager 10:00 4 plasser; tolv fiktive bookinger, ingen i dag, slik at resultatet ikke avhenger av oppstartstidspunktet.
  - Spesifikasjonen holdes samlet (ca. 3 300 tokens).
- Viktige valg i spesifikasjonen: migrering `0006_bookings_pay.sql` (AD-7 rettes til 0006), `bookings_session_id_fkey`, `holds_session_id_fkey` og `idempotency_keys_session_id_fkey` → `no_session`, nye koder `invalid_key`, `payment_pending`, `payment_failed`, betalingsbryteren leses bare ved HTTP-kall, e-postemne «Booking confirmed: <referanse>», rutene `/book-seats/details`, `/book-seats/review`, `/confirmation/[reference]`. Avvisningsmeldingene på Review hører til Story 1.6.

### Åpne punkter
- Implementer Story 1.5 fra spesifikasjonen i en ny `bmad-build`-sesjon: `/bmad-build .docs/implementation-artifacts/spec-1-5-pay-and-confirmation.md`.
