# Sensorveiledning-epic-5

## 2026-11-25 kl. 20:19 — Lisa Larsen

### Oppgave
Oppdatere `.docs/sensorveiledning-kravsporing.md` for Story 5.1 og 5.2.

### Plan
- Rad 2 (Funksjonalitet): legg til FR-29/FR-30 fra Story 5.1 og 5.2 med testfiler, og si hva som fortsatt ikke er levert.
- Rad 3 (Testing): oppdater testtallet.

### Resultat
- Rad 2: ny del «2026-11-25, Epic 5» med oppføringen (5.1), bookingen og betalingen (5.2), testfilene (`test_fr29_whole_sauna.py`, `test_fr29_whole_store.py`, `test_fr29_whole_booking.py`, e2e `test_fr30_private_sauna.py`), hva som ikke er levert (5.3–5.5, FR-31 og videre) og Back-lenken (PR #24).
- Rad 3: 812 tester (610 API + 202 e2e, talt med `pytest --collect-only`; alle har passert i dagens kjøringer).
- Commit `0cd9dc5` på `docs/sensor-guide-5-1-5-2`. Pushet, og PR #25 opprettet (https://github.com/IBE160-2026/G78-larsen/pull/25).
- Lukket i `issues.md`: punktet om at sensorveiledningen sa «FR-29 og videre er ikke levert».

### Åpne punkter
- Ingen.
