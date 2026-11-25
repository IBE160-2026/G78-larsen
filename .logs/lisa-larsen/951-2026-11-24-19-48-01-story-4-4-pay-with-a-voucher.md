# Story 4.4: Pay with a Voucher

## 2026-11-24 kl. 19:48 — Lisa Larsen

### Oppgave
`/bmad-build` for Story 4.4 (FR-28): gjesten skal kunne betale hele eller deler av en ny booking med en voucher. Lisa valgte «Godkjenn og stopp», så implementeringen gjøres i en ny `bmad-build`-økt.

### Plan
- Steg 1: `epic-4-context.md` var fortsatt gyldig, fordi ingen planleggingsdokumenter er nyere. 4.3-specen ble lastet for kontinuitet.
- Steg 2: gikk gjennom epics.md Story 4.4, AD-13/AD-30/AD-31, PRD FR-28 og koden: `services/booking.py`, `services/payment.py`, `services/voucher.py`, `db/vouchers.py`, `db/bookings.py`, `api/public.py`, `api/schemas.py`, `api/errors.py`, `Review.js`, `Confirmation.js`, `lib/copy.js`, `lib/draft.js` og testhjelperne i 4.3. Deretter skrev jeg specen og avklarte de åpne spørsmålene med Lisa.
- Spec: [spec-4-4-pay-with-a-voucher.md](../../.docs/implementation-artifacts/spec-4-4-pay-with-a-voucher.md), status `ready-for-dev`, rute `dispatch`, ca. 2 800 tokens.

### Resultat
- Ny spec som dekker:
  - `POST /api/vouchers/quote`
  - voucher på `POST /api/bookings`, med betinget UPDATE etter låsen og radene `charge`/`voucher` + `charge`/`card`
  - `paid` i bookingsvaret
  - voucher-feltet på Review, betalingsradene på Confirmation og i e-posten
  - testene `test_fr28_voucher.py` (API og e2e) og README

  Ingen migrasjon trengs.
- Lisas beslutninger, som også lukker EXPERIENCE.md Open Item 23:
  - Etiketten er «Voucher code», og lenken ved siden av feltet er «Apply voucher».
  - Når koden ikke kan brukes, gir alle årsaker samme melding: «This voucher code cannot be used. It may be mistyped, used up or expired. Check the code and try again.» Lisa spurte om meldingen kunne si at voucheren er utløpt. En egen utløpt-melding ville gått imot PRD FR-28 og AD-30, så hun valgte å nevne utløp som mulig årsak.
  - Teknisk feil: «The voucher could not be checked, please try again.»
  - På Review vises radene «Voucher −NOK …» og «To pay by card NOK …». Pay-knappen sier «Pay NOK {kortdel}», eller «Book with voucher» når voucheren dekker hele beløpet.
  - «Simulated payment: no money moves» vises bare når noe betales med kort.
  - På Confirmation og i e-posten: «Paid with voucher: NOK …» og «Paid by card: NOK …». En del på 0 tas ikke med.
  - Voucheren fjernes ved at gjesten endrer eller tømmer feltet. Det er ingen egen «fjern»-lenke.
- Mine egne valg, som står i specen:
  - Ukjent `window_id` i quote gir 404.
  - En voucherdel som er større enn totalen gir `voucher_invalid`.
  - Kortdelen regnes ut fra prisen før låsen og sjekkes på nytt etter at bookingen er satt inn.
  - `request_hash` er uendret for bookinger uten voucher.
- Lisa godtok størrelsen over 1 600 tokens (én PR, som i 4.3).
- Specen er ikke committet. Den hører til story-grenen.

### Åpne punkter
- Implementer Story 4.4 i en ny `bmad-build`-økt. Specen er `ready-for-dev`.
- EXPERIENCE.md: før inn Lisas voucher-felttekster og betalingsrader, og merk Open Item 23 som lukket.

## 2026-11-24 kl. 19:49 — Lisa Larsen

### Oppgave
Føre inn 4.4-tekstene i EXPERIENCE.md og lukke Open Item 23.

### Plan
- Ny tabell «Pay with a voucher wording» under «Give up seats wording» i Voice and Tone, i samme form som tabellene for 4.2 og 4.3.
- Oppdatere Voucher field i Component Patterns og If-time Plug-in Points, og lukke Open Item 23.
- Oppdatere epic-4-konteksten, slik at den er nyere enn planleggingsdokumentene når neste build starter.

### Resultat
- `EXPERIENCE.md` har fått tabellen «Pay with a voucher wording, accepted by Lisa (2026-11-24, Story 4.4, FR-28)». Den har feltet, lenken, de to feilmeldingene, radene på Review, Pay («Pay NOK {card}» / «Book with voucher»), betalingsnotatet og radene på Confirmation og i e-posten.
- `[ASSUMPTION]` er fjernet fra plasseringen av voucher-feltet, og Open Item 23 er merket «Closed by Lisa 2026-11-24».
- `epic-4-context.md`: linjen «Still for Lisa to decide» er erstattet med 4.4-beslutningene.
- Ikke committet. Endringene hører til story-grenen sammen med specen.

### Åpne punkter
Ingen nye.

## 2026-11-24 kl. 22:13 — Lisa Larsen

### Oppgave
Implementere Story 4.4 (FR-28, betale med voucher) med `bmad-build` fra specen som var `ready-for-dev`. Lisa ba om at jeg ikke skulle spørre noen underveis, så avgjørelsene i review-steget tok jeg selv.

### Plan
- Ny gren `story/4-4-pay-with-a-voucher` fra `main` (4a91e65). De ukommitterte endringene i specen og EXPERIENCE.md ble med på grenen.
- Steg 3: en implementeringsagent fulgte specen. Jeg gikk gjennom diffen og sjekket matrisen mot testene. Deretter kjørte jeg API- og e2e-suitene og frontend-bygget.
- Steg 4: tre review-agenter (Blind Hunter, Edge Case Hunter, Verification Gap). De stoppet på bruksgrensen og ble gjenopptatt etter at den ble nullstilt. Triage-loggen står i specen.
- Spec: [spec-4-4-pay-with-a-voucher.md](../../.docs/implementation-artifacts/spec-4-4-pay-with-a-voucher.md) (`done`).

### Resultat
- Commit `34d7c54` på `story/4-4-pay-with-a-voucher` (ikke pushet). Den inneholder:
  - `POST /api/vouchers/quote`
  - voucher på `POST /api/bookings`, trukket med én betinget UPDATE etter at Window er låst
  - `paid` i bookingsvaret
  - voucher-feltet på Review, med en ny quote når Review åpnes og etter at en nærmeste økt er valgt
  - radene «Paid with voucher»/«Paid by card» på Confirmation og i e-posten
  - `tests/test_fr28_voucher.py` (54) og `tests/e2e/test_fr28_voucher.py` (4)
  - README, sensorveiledningen (rad 3: 698 tester) og `sprint-status` (4-4: `review`)
- Før review-patchene: 518 API-tester, 179 e2e-tester og frontend-bygget var grønne. Alle radene i matrisen har en test som har kjørt.
- Review: 19 funn.
  - 6 ble patchet:
    - ny quote av lagret kode (ved reload og etter valg av nærmeste økt)
    - «could not be checked»-feilen
    - Confirmation når voucheren dekker hele beløpet
    - lange linjer
    - testtallet i sensorveiledningen
    - sprint-status
  - 1 ble utsatt: fornying av voucher ved å gi fra seg plasser. Den står i `deferred-work.md`.
  - 12 ble avvist med begrunnelse. Blant dem:
    - En kode som er skrevet inn men ikke brukt, ignoreres ved Pay. Pay-knappen viser da hele beløpet.
    - Ingen rate limit på quote. Det hører til Open Item 24.
- Etter patchene kjørte agenten `test_fr28` (API og e2e) grønt. Min fulle kjøring på nytt ble stoppet av Claude Code fordi maskinen hadde lite minne. Patchene endret i kildekoden bare kommentarer og docstrings.
- Agenten endret layoutsjekken i `tests/e2e/test_fr05_book_and_pay.py`, slik at den måler hele høyrekolonnen. Voucher-feltet ligger nå over vilkårene, slik specen bestemmer.
- Lukket i `issues.md`:
  - «implementer Story 4.4»
  - «sensorveiledningen sier fortsatt 536 tester»

### Åpne punkter
- Kjør full verifisering på nytt etter review-patchene. Kjøringen ble stoppet på grunn av lite minne.
- Lisa må bestemme om voucher-betalte plasser som gis fra seg skal få en ny voucher med ett års gyldighet, eller beholde utløpsdatoen til den brukte voucheren.
- Godta endringen i layoutsjekken i `test_fr05_book_and_pay.py`.
- Gå gjennom endringen (`bmad-walkthrough`), åpne PR og sett 4.4 til `done` etter godkjenning.

## 2026-11-24 kl. 22:31 — Lisa Larsen

### Oppgave
Lisa bestemte at en voucher fra «gi fra deg plasser» skal beholde utløpsdatoen til voucheren som betalte bookingen, så en voucher ikke kan fornyes i det uendelige.

### Plan
- Regelen ligger i SQL (`db/vouchers.next_last_valid_date`). Den tar den tidligste siste gyldige datoen til en voucher som betalte bookingen, og følger `booking_changes.new_booking_id` bakover, slik at en booking som er delt opp ved flytting arver datoen. Uten voucher gjelder fortsatt ett år.
- `services/change.voucher` bruker datoen når voucheren utstedes.
- Manage-lesingen (`booking_now`) får `voucher_last_valid_date`, og Give up seats-steget viser den i stedet for å regne «i dag + ett år» i nettleseren.

### Resultat
- Commit `892234b` på `story/4-4-pay-with-a-voucher` (ikke pushet).
- Nye tester i `tests/test_fr28_voucher.py`: datoen arves ved delvis voucherbetaling, arves gjennom oppdeling ved flytting, og bookinger betalt bare med kort gir fortsatt ett år. `test_fr25_manage_link.py` forventer det nye feltet.
- 521 API-tester grønne. Frontend-bygget er grønt. E2e for `test_fr27_voucher` og `test_fr28_voucher` er grønne (6).
- Dokumentasjon: README (FR-27-avsnittet), FR-27 i `epics.md`, `epic-4-context.md` og testtallet i sensorveiledningen (701).
- Lukket i `issues.md`: vouchers som kan fornyes i det uendelige, og «Valid until» som ble regnet ut i nettleseren.
- Merk: en booking som er betalt dels med voucher og dels med kort, får hele den nye voucheren med den kortere datoen.

### Åpne punkter
- Hele e2e-suiten er ikke kjørt etter review-patchene og denne endringen. Punktet om full verifisering står fortsatt åpent.

## 2026-11-24 kl. 22:46 — Lisa Larsen

### Oppgave
Vise voucher-flyten i nettleseren, slik at Lisa kunne teste den manuelt.

### Plan
- Bygge dev-stakken på nytt fra `story/4-4-pay-with-a-voucher` med `docker compose up --build --wait`, sjekke at `POST /api/vouchers/quote` svarer, og åpne `https://localhost:8443`.

### Resultat
- Stakken kjører koden fra grenen. Quote-ruten svarer `401 no_session` uten økt, som forventet.
- Lisa testet flyten og godkjente den. Story 4.4 er satt til `done` i `sprint-status.yaml` (`5ec9cbc`).
- Endringen i layoutsjekken i `test_fr05` regnes som godtatt.

### Åpne punkter
- PR for `story/4-4-pay-with-a-voucher` er ikke åpnet ennå.
- Hele e2e-suiten er ikke kjørt etter de siste endringene (punktet står fortsatt åpent).

## 2026-11-24 kl. 23:00 — Lisa Larsen

### Oppgave
Kjøre hele e2e-suiten etter review-patchene og endringen av voucherens utløpsdato.

### Plan
- To kjøringer i forgrunnen (8 + 9 testfiler), hver under 10 minutter. Forrige bakgrunnskjøring ble stoppet på grunn av lite minne.

### Resultat
- E2e: 98 + 82 = 180 tester grønne. Sammen med 521 API-tester og frontend-bygget fra forrige økt er hele verifiseringen grønn for koden i `892234b`.
- Lukket i `issues.md`: «kjør full verifisering på nytt».

### Åpne punkter
- PR for `story/4-4-pay-with-a-voucher` er ikke åpnet ennå.
