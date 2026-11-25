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

## 2026-11-25 kl. 01:15 — Lisa Larsen

### Oppgave
Endre punktet om at e2e-flyten i Story 5.2 må booke Lumo, siden epics.md fortsatt sa Kajo.

### Plan
- Rette e2e-kriteriet i Story 5.2 i epics.md og lukke punktet i issues.md.

### Resultat
- `.docs/planning-artifacts/epics.md` Story 5.2: «a Guest books Lumo for a session with the keyboard alone (Kajo is not offered whole in the seed, Lisa 2026-11-24)». De andre Kajo-eksemplene i Epic 5 er katalogtester som setter egne priser i testfixturen, og de er ikke endret.
- `epic-5-context.md` er oppdatert, og punktet i issues.md er lukket.

### Åpne punkter
Ingen.

## 2026-11-25 kl. 01:40 — Lisa Larsen

### Oppgave
Lisa presiserte at alle badstuer skal være åpne for både helbadstu-booking og enkeltseter, hvis ikke annet er markert. Det erstatter valget fra 2026-11-24 om at bare Badstu 1 og 4 kan bookes hele.

### Plan
- Rette dokumentene selv (EXPERIENCE.md, epics.md, epic-5-context.md og specens Decisions).
- La implementasjonsagenten rette seed, tester og README.

### Resultat
- Prisene er Oslo-snittet NOK 262 per plass ganget med antall plasser, rundet til nærmeste 50: Rauha NOK 1850, Löyly NOK 2600, Kajo NOK 3150 og Lumo NOK 3950.
- En badstue tilbys ikke hel bare når den har `bookable_whole = false` eller mangler pris.
- epics.md 5.2 booker Kajo i e2e igjen; endringen til Lumo fra forrige seksjon er tilbakeført.
- En eksisterende database får prisene for Löyly og Kajo ved neste oppstart, fordi seeden fyller felt som er NULL.
- Tester: API-laget 561 passed. e2e-filene `test_fr30_private_sauna.py` og `test_fr01_landing.py` ga 19 passed.

### Åpne punkter
- Hele e2e-laget må fortsatt kjøres, slik punktet i issues.md allerede sier.

## 2026-11-25 kl. 01:55 — Lisa Larsen

### Oppgave
Begrense regelen som forbyr refusjon ved gjestekansellering til setebookinger, så en privat badstu kan refunderes (FR-33, AD-31). Før var dette satt til Story 5.3.

### Plan
- Rette CHECK-en i migrering 0013, som ikke er merget ennå, i stedet for å vente til 5.3.

### Resultat
- `migrations/0013_whole_sauna_bookings.sql`: `seat_guest_refund_forbidden` er gjenopprettet med samme navn som `CHECK (kind <> 'seats' OR NOT (cancel_cause = 'guest' AND cancel_remedy = 'refund'))`.
- Ny test, `test_fr29_whole_store.py::test_a_whole_sauna_booking_may_be_cancelled_by_the_guest_with_a_refund`:
  - En helbadstu-booking som avbestilles med refusjon, går gjennom.
  - En setebooking med samme verdier avvises fortsatt.
- Tester: `test_fr29_whole_store`, `test_fr27_voucher_for_seats` og `test_dr4_migrations` ga 69 passed.
- Punktet er lukket i deferred-work.md og issues.md. Punktet om `ignore_booking` står fortsatt.

### Åpne punkter
Ingen nye.

## 2026-11-25 kl. 09:01 — Lisa Larsen

### Oppgave
Lisa ville at «Book seats» og «Book private sauna» på landingssiden skulle se like ut. Hun fikk fem forslag og deretter fem blå varianter av forslag E, og valgte E1 uten pil. Prisen «NOK 250 per seat, incl. VAT» blir stående i railen; Lisa trakk tilbake ønsket om å fjerne den.

### Plan
- Forslagene ble vist som artifact: https://claude.ai/artifact/TuGZHGyrs3fNAjUbk39XGf
- Bytte tekstlenken «Private sauna» med to like Booking choices, og rette UX-DR41 i dokumentene.

### Resultat
- Ny komponent `frontend/components/BookingChoice.js` og `LANDING_CHOICES` i `frontend/lib/copy.js`: «Book seats» / «Share a sauna with others» og «Book private sauna» / «A whole sauna for your group». Primærknappens blå fyll og kant, venstrestilt, uten pil.
- Lenkens navn er bare handlingen. Forklaringen er `aria-hidden` og leses som beskrivelse via `aria-describedby`. En første versjon med `aria-label` feilet axe (`label-content-name-mismatch`).
- `frontend/app/page.js` og `frontend/app/styles.css`: `.rail-private` er erstattet av `.booking-choices` og `.booking-choice`. Landingssiden har nå ingen `.button-primary`.
- Dokumenter rettet: UX-DR41 og akseptkriteriet for Story 5.1 i `epics.md`, `EXPERIENCE.md` (tekstabell og §4.9-raden), `DESIGN.md` (Private sauna entry), `epic-5-context.md` og en ny merknad i spec-5-1.
- Tester rettet: `test_fr01_landing.py` og `test_fr30_private_sauna.py`. De ga 19 passed etter at frontend ble bygget på nytt.
- Kodeendringene er ikke committet.

### Åpne punkter
Ingen.

## 2026-11-25 kl. 09:06 — Lisa Larsen

### Oppgave
Lisa syntes knappene på landingssiden fikk for lang tekst. De skulle bare si «Book seats» og «Book private sauna», og være like store.

### Plan
- Fjerne forklaringslinjene fra Booking choice og gi begge knappene samme bredde og høyde.

### Resultat
- `BookingChoice.js` har bare handlingsteksten. Forklaringene og `aria-describedby` er fjernet, og `seatsNote` og `privateNote` er tatt ut av `LANDING_CHOICES`.
- `.booking-choice` har full bredde i railen og samme høyde som primærknappen (minst 48 px). Teksten er venstrestilt. `.booking-choice-note` er fjernet.
- `test_fr01_landing.py` sjekker nå at knappene har samme bredde og høyde. `epics.md`, `EXPERIENCE.md`, `DESIGN.md` og spec-5-1 er rettet tilsvarende.
- Tester: `test_fr01_landing` og `test_fr30_private_sauna` ga 19 passed etter at frontend ble bygget på nytt.
- Kodeendringene er ikke committet.

### Åpne punkter
Ingen.
