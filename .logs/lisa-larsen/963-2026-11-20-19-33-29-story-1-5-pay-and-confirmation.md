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
- Spesifikasjonen er skrevet, godkjent og committet på `main` som `86e122e`, slik 1.4-spesifikasjonen ble committet før storygrenen. Pushet til `origin/main` (`e04f97a..f5cf1c7`).
- Avgjørelser Lisa tok i økten:
  - De to Notice-tekstene fra 1.4 er godkjent: «The session you chose no longer has room for N seats. Choose another session.» og «The sessions could not be loaded, please try again.»
  - `nearest` i `GET /api/windows` kommer bare når både `date` og `seats` er gitt (og ingen økt den dagen har plass). Dagens kode (`services/windows.py:141`) er riktig.
  - Seed-bookingene er godkjent (vist i nettleseren): +1 dag 14:30 2 plasser, +2 dager 17:30 42 av 44, +3 dager 19:00 fullt, +5 dager 10:00 4 plasser; tolv fiktive bookinger, ingen i dag, slik at resultatet ikke avhenger av oppstartstidspunktet.
  - Spesifikasjonen holdes samlet (ca. 3 300 tokens).
- Viktige valg i spesifikasjonen: migrering `0006_bookings_pay.sql` (AD-7 rettes til 0006), `bookings_session_id_fkey`, `holds_session_id_fkey` og `idempotency_keys_session_id_fkey` → `no_session`, nye koder `invalid_key`, `payment_pending`, `payment_failed`, betalingsbryteren leses bare ved HTTP-kall, e-postemne «Booking confirmed: <referanse>», rutene `/book-seats/details`, `/book-seats/review`, `/confirmation/[reference]`. Avvisningsmeldingene på Review hører til Story 1.6.

### Åpne punkter
- Implementer Story 1.5 fra spesifikasjonen i en ny `bmad-build`-sesjon: `/bmad-build .docs/implementation-artifacts/spec-1-5-pay-and-confirmation.md`.

## 2026-11-20 kl. 20:42 — Lisa Larsen

### Oppgave
Kjøre `bmad-build` på [spec-1-5-pay-and-confirmation.md](../../.docs/implementation-artifacts/spec-1-5-pay-and-confirmation.md) (`ready-for-dev`): implementere Story 1.5, verifisere, reviewe og committe.

### Plan
- Steg 3: specen satt til `in-progress` (baseline `9ae9165`), story 1-5 til `in-progress` i `sprint-status.yaml`. Lisa godkjente subagenter for hele kjøringen; én agent implementerte fra specen.
- Leste hele diffen mot oppgavene og edge-case-matrisen; sjekket e-posten mot `key-confirmation.html` L89–112.
- Steg 4: tre review-lag i parallell (Blind Hunter, Edge Case Hunter, Verification Gap); triage i specens `## Review Triage Log`; patch-funnene sendt tilbake til implementeringsagenten.
- Steg 5: spec `done`, story `review`, lokal commit.

### Resultat
- **Commit `386518d`** på `main` (ikke pushet): migrering `0006_bookings_pay.sql`, `services/{payment,reference,outbox,content}.py`, `db/bookings.py`, `POST /api/bookings` med `Idempotency-Key`, `GET /api/bookings/{reference}/confirmation`, bekreftelses-e-post i Outbox, tolv eksempelbookinger (`seeds/bookings.json`), sidene Details, Review og Confirmation, `content/` i begge Docker-images, AD-7 i spinen rettet til `0006`, README oppdatert.
- **Review:** 23 funn triagert. 11 rettet (bl.a. Pay skjules når økttiden ikke kan lastes, kontrolltegn i navn/e-post gir 422 i stedet for 500, ingen «Booking confirmed»-blink før lasting, indekser på `idempotency_keys`, nye tester for betalingsbryteren `fail`/`hold`, kappløp med samme nøkkel, `reference.claim`, pris 0 og purge av økt med booking og nøkkel). 2 testhull utsatt til `deferred-work.md`, 10 avvist.
- **Verifisert etter rettingene:** `uv run pytest` — API 277 bestått, e2e 93 bestått; `npm --prefix frontend run build` lister `/book-seats/details`, `/book-seats/review` og `/confirmation/[reference]`.
- Første fulle testkjøring ble stoppet av Claude Code på grunn av lite minne. Dev-stakken ble stoppet (`docker compose stop`, data beholdt), Docker Desktop og WSL avsluttet og startet igjen, og testene kjørt i to deler (API, så e2e).
- Lukket åpent punkt: «implementer Story 1.5» (issues.md).
- Manuell sjekk: dev-stakken bygget på nytt (`docker compose up --build --wait`); `0006` kjørt mot dev-databasen (ingen gamle bookinger å backfille), 12 eksempelbookinger lagt inn som planlagt. Lisa booket i nettleseren på http://localhost:8000: ok. Punktet er lukket i issues.md.
- Lisa godkjente de tre tekstene («Accept the booking terms», «The booking could not be completed, please try again.», «The booking could not be loaded, please try again.») og satte Story 1.5 til `done` i `sprint-status.yaml`.
- Pushet til `origin/main` (`9ae9165..0b954c7`): Story 1.5 (`386518d`), sprint-status `done` (`4046fa1`) og loggene.

### Åpne punkter
- ~~Godkjenn tre tekster~~ — godkjent, se Resultat.
- Story 1.6: hvis gjestens økt slettes (purge) etter en betaling der svaret gikk tapt, forsvinner nøkkelen med økten (`ON DELETE CASCADE`), og et nytt forsøk kan booke og belaste to ganger; uten purge gir nytt forsøk `invalid_key` i det uendelige. Se triage-rad 2 i specen.
- Review.js åpner en ny økt etter `401 no_session` og beholder nøkkelen — oppførsel fra Story 1.6 som kom med i 1.5; vurder den i 1.6.
- ~~Manuell sjekk i nettleseren~~ — gjort, se Resultat.
- ~~Sett Story 1.5 til `done`~~ — gjort, se Resultat.
