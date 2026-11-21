# Story 1.6: avvisninger uten belastning

## 2026-11-20 kl. 21:13 — Lisa Larsen

### Oppgave
Planlegge Story 1.6, «A Guest who cannot get the seats is told why and charged nothing», som er siste story i Epic 1. Specen skulle skrives med `/bmad-build` og godkjennes. Implementeringen gjøres i en ny økt.

### Plan
- `bmad-build` steg 1–2: lastet epic-1-konteksten, spec 1.5, deferred-work og Story 1.6 i `epics.md` (L707–764), og undersøkte backend, Review og testene.
- Skrev specen: [spec-1-6-refusals-charged-nothing.md](../../.docs/implementation-artifacts/spec-1-6-refusals-charged-nothing.md).

### Resultat
- Specen er godkjent med status `ready-for-dev`.
- Funn under undersøkelsen:
  - `no_seat_free` mangler faktumet `seats_left`.
  - Når man betaler, sjekkes ikke bookinghorisonten (`outside_horizon`).
  - Ny økt etter `401` finnes alt i `Review.js`.
  - Testene for `fail`/`hold`, `invalid_key` og `try_again` finnes alt og skal utvides.
- Beslutninger (Lisa):
  - 1A: migrering `0007` setter `idempotency_keys.session_id` til `ON DELETE SET NULL`. Nøkkelen overlever økten, og et nytt forsøk gir `invalid_key` i stedet for en ny belastning.
  - 2A: teksten blir «Only N seats left in this session. You have not been charged.»
  - 3A: de nærmeste øktene er andre økter samme dag som har plass, ellers listingens `nearest`. Bare frontend endres.
  - 4: specen beholdes hel (omtrent 2300 tokens).
- `epic-1-context.md` ble ikke laget på nytt. Plandokumentene er nyere, men endringene er trivielle: et rettet migreringsnummer og en bildesti.
- Specen er ikke committet ennå.

### Åpne punkter
- Implementer Story 1.6 i en ny økt med `/bmad-build .docs/implementation-artifacts/spec-1-6-refusals-charged-nothing.md`.
