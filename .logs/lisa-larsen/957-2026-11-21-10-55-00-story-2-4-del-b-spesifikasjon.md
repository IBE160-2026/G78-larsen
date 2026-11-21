# Story 2.4 del B: Core done — README, fersk klone og manuelle sjekker

## 2026-11-21 kl. 10:55 — Lisa Larsen

### Oppgave
Lisa ba om å starte del B av Story 2.4: README-en, kjøring fra en fersk klone, de manuelle tilgjengelighetssjekkene og «Core done» i loggen. Økten endte etter planleggingen, fordi Lisa valgte «Godkjenn og stopp».

### Plan
- `bmad-build`, steg 1 og 2. Del A står i [story-2-4-core-done-automated-checks](958-2026-11-21-10-32-49-story-2-4-core-done-automated-checks.md).
- En subagent bygde `epic-2-context.md` på nytt, fordi `DESIGN.md` var nyere. En annen subagent undersøkte:
  - PRD-kravene DR-1, DR-2, DR-5, NFR-1, SM-4 og §10.1
  - suksesskriteriene SC1–SC10
  - AD-14, AD-18, AD-19 og AD-27
  - personvernerklæringen, seed-dataene og loggingen
- Spesifikasjon: [spec-2-4-core-done-readme-clean-clone-manual-passes.md](../../.docs/implementation-artifacts/spec-2-4-core-done-readme-clean-clone-manual-passes.md)

### Resultat
- Spesifikasjonen er skrevet og godkjent, med status `ready-for-dev`. Den er ikke implementert.
- Lisas beslutninger, som står i den låste delen av spesifikasjonen:
  - README-en er fortsatt på norsk.
  - Lisa kjører de manuelle sjekkene (tastatur, 200 % zoom, tabulatorrekkefølge, NVDA med Chrome) mens agenten venter. Agenten fører inn resultatene hun rapporterer.
  - Agenten kjører sjekken fra en fersk klone på laptopen, i en ny mappe. Først stopper den stakken `g78-larsen` med `docker compose down` uten `-v`, og etterpå starter den den igjen.
- `epic-2-context.md` er bygget på nytt med nesten samme innhold. Endringer: `POST /api/admin/sign-in` er lagt til, og formen på feilsvarene og fargene i Administrator-linjen er tatt med.
- Lisa ba om commit. Spesifikasjonen og `epic-2-context.md` er committet som `55b07d0` på den nye grenen `story/2-4-core-done-part-b`, som implementeringen fortsetter på. Ingenting er pushet.

### Åpne punkter
- Implementeringen av del B gjenstår og startes i en ny `bmad-build`-økt fra spesifikasjonen. Punktet var allerede åpent i `issues.md`.
- Også `epics.md`, Story 2.2, sier fortsatt `heading-md` for økttiden og har tallene og «No bookings» som egne punkter. Dette er lagt til i det åpne DESIGN.md-punktet.
