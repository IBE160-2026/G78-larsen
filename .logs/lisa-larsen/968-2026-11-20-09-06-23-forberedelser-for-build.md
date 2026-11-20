# Forberedelser for build

## 2026-11-20 kl. 09:06 — Lisa Larsen

### Oppgave
Lisa kjørte `bmad-help` og spurte hva hun kan forberede før `bmad-build` på Story 1.1, for eksempel apper eller datainnstillinger, så bygget går raskere. Deretter ba hun om å hente Docker-bildene, sette opp minne for WSL og kjøre `/fewer-permission-prompts`.

### Plan
- `bmad-help`: lese `sprint-status.yaml`, de siste loggene og `issues.md` for å finne neste steg. Svaret: planleggingen er ferdig, og neste påkrevde steg er `bmad-build` på Story 1.1.
- Sjekke verktøyene på maskinen mot stacken i spinen og epics (Docker, uv, Python, Node, gh, Playwright, NVDA).
- Gjøre forberedelsene Lisa valgte.

### Resultat
- **Verktøy:**
  - uv 0.12.6, Python 3.12.14, Node 26.7.0, npm 11.19.0, git 2.55 og gh 2.103.3 er installert. gh er innlogget.
  - Spinen godtar Node 24 eller 26 LTS, og frontend-bildet er `node:24-alpine`.
  - Caddy og psql trengs ikke lokalt.
- **Docker-bilder hentet:** `postgres:18`, `caddy:2.11`, `node:24-alpine`, `python:3.12-slim`.
- **WSL-minne:**
  - Ny fil `C:\Users\lisak\.wslconfig` med `memory=8GB` og `swap=8GB`. Den ligger utenfor repoet.
  - `wsl --shutdown` er kjørt, og Docker Desktop er startet på nytt.
  - En container viser `MemTotal` 8 129 684 kB og `SwapTotal` 8 388 608 kB.
  - Docker-motoren er nå 29.9.3. Før omstarten var den 29.8.0, så Docker Desktop tok trolig inn en ventende oppdatering.
- **Allowlist:**
  - Ny fil `.claude/settings.json` med `Bash(uv run _bmad/scripts/resolve_customization.py *)` (20 kall) og `Bash(uv run _bmad/scripts/resolve_config.py *)` (12 kall).
  - Begge skriptene er kontrollert: de leser bare og skriver kun til stdout.
  - Grunnlaget er 46 transkripsjoner.
  - Utelatt:
    - `git commit`/`add`/`push`, `curl` og `memlog.py`: skriver eller endrer.
    - `python` og `uv run pytest`: kjører vilkårlig kode, og testene skriver til testdatabasen.
    - `lint_spine.py`: kan skrive med `--output`.
    - grep, sed, head, git status/show/log og ls: allerede tillatt automatisk.
    - PowerShell-cmdlets: for få kall, og regelformatet er usikkert.
  - Filen er committet i `7c04774` og pushet til `origin/main` sammen med loggcommiten `47eb665` (Lisa ba om det).
- **Antall tester:** `uv run pytest --collect-only -q` samler 42 tester, med parametrisering. Tallet i `epics.md` stemmer. Punktet i `issues.md` er lukket.

### Åpne punkter
- Ingen nye. Før Story 1.1 bør Lisa avgjøre noen antakelser som allerede står i `issues.md`:
  - `GET /api/venue` og `GET /api/windows?date=&seats=` (1.3 og 1.4)
  - dummy-hash ved ukjent e-post (2.1)
  - navn på grenene og hvordan PR-er merges

## 2026-11-20 kl. 09:17 — Lisa Larsen

### Oppgave
Lisa avgjorde de tre valgene før Story 1.1 og fikk forklart hva merge og en åpen PR betyr. Hun presiserte at alt foreløpig bare kjøres lokalt, med lokal database og lokal fillagring, og at ingenting skal deployes nå.

### Plan
- Føre valgene inn i `epics.md` (byggeprosessen og storyene 1.3 og 1.4), oppdatere `issues.md`, committe og pushe.

### Resultat
- **Endepunktene** `GET /api/venue` og `GET /api/windows?date=&seats=` er bekreftet. «Or the path chosen in the story» er fjernet fra Story 1.3 og 1.4.
- **Dummy-hash** ved ukjent e-post (2.1) var allerede godtatt 2026-11-19. Ingen endring.
- **Grener og merge** står i `epics.md` under *Traceability*:
  - Grenene heter `story/<epic>-<story>-<kort-navn>`, for eksempel `story/1-1-backend-structure`.
  - Lisa merger selv når testene er grønne og hun har gjennomgått endringen.
  - Vanlig merge, ikke squash, slik at commitene med FR-nummer blir stående i `main`.
  - Neste story lager gren fra oppdatert `main`.
- **Deploy:** gren, PR og merge er bare historikk på GitHub. Appen kjøres fortsatt bare lokalt.
- **Commits:**
  - `31f4405`: `epics.md`.
  - `106dce5`: forrige logg-oppdatering. Den er pushet nå sammen med `31f4405`.
- **`issues.md`:** punktet om endepunktene er oppdatert. På punktet om gren og PR (kriterium 1) står valgene nå, men punktet er fortsatt åpent til det er tatt i bruk fra Story 1.1.

### Åpne punkter
- Ingen nye.
