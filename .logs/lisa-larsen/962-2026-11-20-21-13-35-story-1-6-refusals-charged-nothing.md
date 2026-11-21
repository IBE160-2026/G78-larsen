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

## 2026-11-21 kl. 00:19 — Lisa Larsen

### Oppgave
Implementere Story 1.6 fra specen med `/bmad-build .docs/implementation-artifacts/spec-1-6-refusals-charged-nothing.md`: gjesten får vite hvorfor bookingen ble avvist, og ingenting belastes.

### Plan
- `bmad-build` steg 3–5 etter [specen](../../.docs/implementation-artifacts/spec-1-6-refusals-charged-nothing.md).
- Steg 3: en subagent implementerte specen. Den stoppet midt i arbeidet fordi bruksgrensen ble nådd, og fortsatte etterpå.
- Steg 4: tre reviewere gikk gjennom diffen. De fant 23 punkter, og hvert punkt er vurdert i triageloggen i specen.
- Steg 5: specen ble satt til `done`, sprint-status til `review`, og arbeidet ble committet lokalt.

### Resultat
- Commit `7dbe87a` (ikke pushet). Commiten inneholder:
  - **Backend:** en booking sjekkes etter låsen i rekkefølgen `outside_horizon`, `deadline_passed`, `no_seat_free` (med det sanne `seats_left`). Horisontsjekken ligger i den delte `ensure_open_for_booking`, så Holds og hele badstuer får den også.
  - **Migrering `0007`:** nøkkelen overlever økten (`ON DELETE SET NULL`).
  - **Review:** hver avvisning har sin egen tilstand, med opptil tre nærmeste økter.
  - **Tester:** `test_fr11_last_seat_race.py` (100 runder), `test_fr12_all_or_nothing.py` og `tests/e2e/test_fr11_refusals.py`.
- **Verifisert:** `uv run pytest -q` ga 387 passert i én kjøring med e2e. `npm --prefix frontend run build` gikk gjennom.
- **Matrisen:** raden «Pending / retries used» manglet en test. Jeg la til en e2e-test med `page.route` for `payment_pending`, `try_again` og ingen svar.
- **Review:** 9 punkter er rettet. De viktigste:
  - en gammel avvisning ble stående under neste betalingsforsøk;
  - når det ikke finnes noen nærmeste økter, får gjesten nå en «Book seats»-lenke;
  - nye tester for `outside_horizon` på Holds, hele badstuer og Review, og for rekkefølgen på nærmeste økter.

  1 punkt er utsatt til `deferred-work.md`, og 13 er avvist.
- **Lukket:** de to Story 1.5-punktene om nøkkelen og ny økt etter `401`, og punktet «implementer Story 1.6». Story 1.5-oppføringen i `deferred-work.md` om e2e-test av Review er merket som ferdig.

### Åpne punkter
- Gå gjennom Story 1.6, for eksempel med `bmad-walkthrough` og i nettleseren, og sett den til `done` i `sprint-status.yaml`.
- Godkjenn tre valg subagenten tok som ikke står i specen:
  - Etter `invalid_key` starter «Book seats» et nytt utkast, men tar med navn og e-post.
  - «please try again»-meldingen tar også fokus.
  - Etter `invalid_key` fjernes Pay, betalingsnotatet og avkrysningsboksen.
- Utsatt test (`deferred-work.md`): Review faller tilbake til listingens `nearest` på andre datoer når dagen er full. Det kjøres aldri i noen test.
- Vurder en oppbevaringsregel for `idempotency_keys`. Nøklene blir ikke lenger slettet sammen med økten (review-rad 17, avvist som liten).
