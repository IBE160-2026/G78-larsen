# Story 5.1: A Guest sees which saunas can be booked whole

## 2026-11-25 kl. 01:05 — Lisa Larsen

### Oppgave
Bygge story 5-1 med `bmad-build`. Whole-sauna-prisene skulle settes ut fra snittprisen i Oslo-området og badstuenes størrelse, og Badstu 1 og 4 skulle kunne bookes hele. De to ventende Epic 5-avgjørelsene (feilmeldingen etter `sauna_unavailable` på Review i 5.2 og plasseringsvisningen i 5.4) skulle løses uten å spørre noen. Underveis ba Lisa om at arbeidet ble gjort med subagenter, så kontekstvinduet ikke ble for stort.

### Plan
- Kompilerte [epic-5-context.md](../../.docs/implementation-artifacts/epic-5-context.md) og skrev specen [spec-5-1](../../.docs/implementation-artifacts/spec-5-1-a-guest-sees-which-saunas-can-be-booked-whole.md) på branch `story/5-1-private-sauna-listing`.
- Én subagent implementerte, tre subagenter reviewet (Blind Hunter, Edge Case Hunter, Verification Gap), og deretter fulgte patcher og verifisering.

### Resultat
- **Avgjørelser** (EXPERIENCE.md, «Private sauna wording»; Open Item 27 lukket):
  - Rauha koster NOK 1850 og Lumo NOK 3950. Grunnlaget er Oslo-snittet, NOK 1 837 for omtrent 7 plasser, dvs. NOK 262 per plass, ganget med antall plasser og rundet til nærmeste 50.
  - Löyly og Kajo kan ikke bookes hele.
  - Etter `sauna_unavailable` (5.2) står det «This sauna can no longer be booked for this session. You have not been charged.», med lenken «Choose another sauna or session».
  - Plasseringen (5.4) vises som tabellen «Saunas» med kolonnene «Sauna» og «Seats counted», og cellene «7 of 7», «Booked whole · {ref}», «Blocked» og «Private sauna only».
- **Kode** (commit `b8afac8`):
  - Migrering `0013_whole_sauna_bookings.sql` legger til `kind` og `sauna_id`, paringen med `whole_pairing`, `whole_bookable()`, `cutoff_whole` og `whole_price_ore`.
  - Seed-prisene er lagt inn, og `GET /api/private-saunas` er nytt. Slice-endepunktet `/api/admin/whole-bookings` er fjernet, og testene bruker `raw_whole`.
  - Landing har fått Private sauna-lenken, prisene og gruppesetningen, og siden `/private-sauna` er ny.
  - De nye testene er `test_fr29_whole_sauna.py`, `test_fr29_whole_store.py` og `tests/e2e/test_fr30_private_sauna.py`.
- **Review:** 20 funn. 11 ble rettet, 5 avvist og 4 utsatt til `deferred-work.md`. Triageloggen står i specen.
- **Verifisering:**
  - API-laget: 561 passed.
  - Full e2e: 186 passed, 1 failed og 1 error, begge i `test_fr30`. Begge er rettet, og `test_fr30` alene gir 5 passed.
  - En ny full e2e-kjøring ble stoppet av Claude Code fordi maskinen hadde lite minne, så den er ikke bekreftet.
- **Lukket i issues.md:** `sauna_unavailable`-meldingen og plasseringsvisningen (5.4) er avgjort.
- Specen ble på omtrent 2500 tokens, over anbefalt 1600; den ble holdt samlet fordi storyen er definert slik i epics.
- Ikke pushet, og ingen PR er opprettet.

### Åpne punkter
- Kjør `uv run pytest tests/e2e` på nytt når det er nok minne. Hele e2e-laget er ikke bekreftet grønt etter rettingene i `test_fr30`.
- Story 5.2: e2e-flyten må booke Lumo, ikke Kajo, fordi Kajo ikke tilbys hel i seeden. epics.md sier fortsatt Kajo.
- Story 5.2: gjenopprett whole-dekningen i `test_fr14_retry`, `test_fr20_access` og `test_fr2_input` mot `POST /api/bookings` med `kind = 'whole'` (deferred-work).
- Story 5.3: `seat_guest_refund_forbidden` må begrenses til `kind = 'seats'`, og `whole_bookable(..., ignore_booking)` må se bort fra den ignorerte raden også i `room_ahead` (deferred-work).
- e2e-test der badstuene har ulike ledige sesjoner, for omgrupperingen på `/private-sauna` (deferred-work).
