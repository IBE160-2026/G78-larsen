# Private-sauna-back-restores-pair

## 2026-11-25 kl. 20:29 — Lisa Larsen

### Oppgave
Skrive den utsatte e2e-testen fra review av Story 5.2: at Back fra Details i Private sauna-flyten velger samme badstue og økt igjen.

### Plan
- Ny gren `test/private-sauna-back-restores-pair` fra `main`.
- Én test i `tests/e2e/test_fr30_private_sauna.py`, og en mutasjonssjekk for å vise at den fanger feilen.

### Resultat
- `test_back_from_details_chooses_the_same_sauna_and_session_again`: velg Kajo 13:00–14:30, Continue til Details, Back til `/private-sauna?date=…`. Testen sjekker at samme par og dato er valgt, og at Continue går rett til Details uten feiloppsummering. Ingenting bookes.
- Mutasjonssjekk: med `setPending(...)` fjernet i `PrivateSauna.js` feiler testen; koden er satt tilbake.
- `test_fr30_private_sauna.py`: 11 passert.
- `deferred-work.md`: punktet merket som løst. Lukket i `issues.md`.
- Commit `34f7918`. Ikke pushet.
- (Fra forrige økt: PR #25 med sensorveiledningen er merget, `751bbf1`.)

### Åpne punkter
- Ingen.
