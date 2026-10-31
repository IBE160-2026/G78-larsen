# Tilpass sensorveiledning

## 2026-10-31 kl. 21:09 — Lisa Larsen

### Oppgave
Lisa ba om å tilpasse bookingplattformen til sensorveiledning del 1 for IBE160 (sju kriterier, 70 % av karakteren): prosess og KI-styring, funksjonalitet, testing, design, kodekvalitet, README og ryddighet.

### Plan
- Kartlegge repoet (filer, historikk, grener, issues/PR-er, `.gitignore`, hemmeligheter) mot de sju kriteriene.
- Rette det som kan rettes nå uten å bestemme arkitektur: README, PR-mal, kravsporing.
- Ikke bygge app eller velge teknologi; det hører til arkitekturfasen.

### Resultat
- Funn: ingen app (`src/booking_platform/__init__.py` skriver én linje), ingen tester, ingen grener, issues eller PR-er. Planlegging er sterk: brief, PRD (utkast, 1059 linjer), tre research-rapporter, sju sesjonslogger. 111 commits fordelt over september–oktober. Ingen hemmeligheter i kode eller historikk (søkt); `.venv` og `__pycache__` er ikke sporet. PRD §8.1 kobler allerede kriteriene til krav.
- `README.md` skrevet om: ærlig status-tabell, forutsetninger, kjørbare kommandoer (`uv sync`, `uv run booking-platform` verifisert), mappestruktur, lenker til plan- og prosessdokumenter. Skrev ikke ned tester, testbrukere eller miljøvariabler som ikke finnes.
- `.github/pull_request_template.md` lagt til: krav (FR/story), KI-bruk, kvalitetssikring, funn i KI-kode.
- `.docs/sensorveiledning-kravsporing.md` lagt til: status, gjenstående og tidspunkt per kriterium, varseltegn, ventende beslutninger.
- Endringene er ikke committet (ikke bedt om).
- Rettelse: jeg trodde først at Bård Pettersen manglet i medlemslisten. Lisa er eneste student, og Bård er sensor; hans 5 commits er repo-oppsett, tilbakemelding på briefen og sesjonslogg-skillen. README er riktig.

### Åpne punkter
- Arkitektur, UX (`bmad-ux`), epics og stories er ikke startet; de må på plass før første story og før frontend (kriterium 1, 4, 5).
- Ta i bruk gren + PR per story og issues for store punkter, med FR-nummer i commit-meldinger (kriterium 1).
- README må oppdateres og verifiseres på en ren klone når appen finnes (kriterium 6).
