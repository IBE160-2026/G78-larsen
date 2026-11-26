# Booking-list-date-picker

## 2026-11-26 kl. 17:58 — Lisa Larsen

### Oppgave
Få en kalender-picker (pop-up) i Administrators bookingliste, så datoen kan velges uten å skrives inn. Denne økten: bare planlegging (spec), ikke implementering.

### Plan
- `bmad-build`, freeform-sti (ikke en epic-story). Spec: [`spec-booking-list-date-picker.md`](../../.docs/implementation-artifacts/spec-booking-list-date-picker.md).
- Før arbeidet: Story 5.3 del 1 ble committet på `feat/5-3-cancel-private-sauna`, og ny gren `feat/booking-list-date-picker` ble laget derfra (Lisas valg).

### Resultat
- Story 5.3 del 1 committet: `49b04632f9861d6385229b0aa4f84a24ba6501f2` (28 filer). `frontend/AGENTS.md`, som `next dev` skrev, ble holdt utenfor og er fortsatt utracket.
- Spec skrevet og godkjent (`ready-for-dev`, ukommittert på `feat/booking-list-date-picker`). Beslutning (Lisa): sidens egen pop-up-kalender, ikke nettleserens native datovelger. Knappen «Choose from calendar» ved datofeltet; alle dager valgbare, også bakover; valget går via `?date=` som en skrevet dato; ny komponent `DayPickerPopup.js`; ingen API-endring, ingen markering av dager med bookinger.
- Backend (8001) og frontend (3000) fra forrige del av økten kjører fortsatt i bakgrunnen.

### Åpne punkter
- Implementer kalender-pickeren etter `spec-booking-list-date-picker.md` i en ny `bmad-build`-økt.
- Avgjør om `frontend/AGENTS.md` (skrevet av `next dev`) skal committes.
