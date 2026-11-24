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
