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
- Kl. 18:03: Lisa valgte å committe `frontend/AGENTS.md` (Next.js-agentregler; `next dev` lager den på nytt om den slettes) sammen med specen: commit `12cbb65`. Åpent punkt om AGENTS.md lukket i `issues.md`.

### Åpne punkter
- Implementer kalender-pickeren etter `spec-booking-list-date-picker.md` i en ny `bmad-build`-økt.

## 2026-11-26 kl. 18:28 — Lisa Larsen

### Oppgave
Lage selve kalendervelgeren til admin-siden (bookinglisten) etter specen.

### Plan
- `bmad-build` fra steg 3 (specen var `ready-for-dev`): implementert direkte ut fra [`spec-booking-list-date-picker.md`](../../.docs/implementation-artifacts/spec-booking-list-date-picker.md), uten implementeringssubagent.
- Review-steget med tre reviewer-subagenter (Blind Hunter, Edge Case Hunter, Verification Gap), godkjent av Lisa. Funnene er triagert i specens «Review Triage Log».

### Resultat
- Ny `frontend/components/DayPickerPopup.js`: knappen «Choose from calendar» ved datofeltet åpner en månedskalender med ubegrensede «Previous month»/«Next month». Alle dager er knapper med fullt datonavn, og den viste dagen har `aria-current="date"`. Ved åpning får den viste dagen fokus. Escape (uansett hvor fokus er) lukker og gir fokus tilbake til knappen, og det samme gjør klikk utenfor og Tab ut av kalenderen. Månedslinjen er en `aria-live`-region.
- `BookingList.js`: `pickDay` fjerner feltfeil, setter teksten og kjører `router.replace(?date=…)` bare når dagen er en annen. Ellers er copy (`chooseFromCalendar`), CSS (`.date-bar-control`, `.date-pop`, `.cal-pick`), EXPERIENCE.md (antakelsen er erstattet med vedtatt oppførsel), DESIGN.md (ny komponentbullet) og README oppdatert.
- Review: 21 funn. 14 er rettet som patcher: Tab ut, Safari-Escape, fokus når et skrevet dato-blur endrer datoen, live region, wrapping, DESIGN.md, kommentar og testhull. 7 er avvist med begrunnelse. Ingenting er utsatt.
- Verifisert: `npm --prefix frontend run build` går gjennom, og `uv run pytest tests/e2e/test_fr16_booking_list.py tests/e2e/test_fr23_accessibility.py` gir 35 passed. Det inkluderer 10 nye tester: I/O-matrisen, tastatur, axe, 200 % zoom og ukedagkolonner.
- Commit: `753d09070c7f18cac6b02e840ad871e7c88e0804` på `feat/booking-list-date-picker` (ikke pushet). Specen har status `done`.

### Åpne punkter
- Ingen.

## 2026-11-26 kl. 18:40 — Lisa Larsen

### Oppgave
Vise kalenderen i nettleseren, og deretter rette den trange månedslinjen i pop-upen («November 2026» og «Previous month» brøt over to linjer).

### Plan
- Startet dev-stacken etter README og sjekket med Playwright (skjermbilde) før siden ble åpnet i Lisas nettleser.
- I pop-upen står månedsnavnet nå på egen linje og månedsknappene under det, uten linjebrudd. Fikk en ny test.

### Resultat
- `docker compose up` feilet fordi Windows har reservert port 55432 (portområdet 55394–55493). Stacken ble startet med `DB_PORT=56432`, uten endringer i filer. Den kjører på https://localhost:8443.
- `frontend/app/styles.css`: `.date-pop .cal-head` er en kolonne, og `.cal-month` og månedsknappene har `white-space: nowrap`. Verifisert visuelt med skjermbilde på 1366 px.
- `tests/e2e/test_fr16_booking_list.py`: `assert_on_one_line` (teller linjene i tekstens client rects) brukes for månedsnavnet og begge månedsknappene. `npm --prefix frontend run build` går gjennom, og fr16 + fr23 gir 35 passed.
- Kodeendringen er ikke committet (Lisa har ikke bedt om det).

### Åpne punkter
- Port 55432 er reservert av Windows på denne maskinen. Stacken må startes med `$env:DB_PORT=56432`, eller README/compose-standarden bør endres.
