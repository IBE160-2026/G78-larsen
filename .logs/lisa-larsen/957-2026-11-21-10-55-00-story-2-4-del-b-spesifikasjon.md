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

## 2026-11-21 kl. 12:44 — Lisa Larsen

### Oppgave
Lisa ba om å bygge del B av Story 2.4 fra spesifikasjonen med `bmad-build`. Det gjaldt to ting: README-en skulle skrives om til sensors kjøreguide med en sikkerhetsseksjon og en «Ikke levert»-liste, og en fersk klone av `main` i en ny mappe skulle kjøres, med retting av alt som feilet.

### Plan
- `bmad-build`, steg 3–5, fra [spesifikasjonen](../../.docs/implementation-artifacts/spec-2-4-core-done-readme-clean-clone-manual-passes.md).
- Agenten implementerte selv, uten subagent, fordi spesifikasjonen venter på Lisa og stopper og starter stakken hennes.
- Rekkefølge: skrive README-en, kjøre den ferske klonen, rette README-en, kjøre testene i repoet og gjennomgå med tre subagenter (Lisa godkjente dem).

### Resultat
- **README.md** er skrevet om i storyens rekkefølge, med disse delene:
  - status og «Ikke levert»: HTTPS/SC9, SC2–SC8, FR-25–51 (FR-35/36/40/41 finnes bare i databasen), mobildelen av SC10 og WCAG 1.4.10
  - tre verktøy, `docker compose up --build --wait` og utviklingskommandoene
  - de to forberedelsene, `uv run pytest` og `BP_TEST_MUTATE`
  - testinnloggingen for Administrator og en tabell over eksempelbookingene, bookinglisten og Outbox
  - drift: `create-admin`, testbrytere (slå på og av), `ps`, `logs`, `down` og `down -v`
  - konfigurasjon og sikkerhet, med testene hver påstand bygger på
  - mappestrukturen
- **Den ferske klonen** ble kjørt av agenten på laptopen:
  - Først `docker compose down` av `g78-larsen`, uten `-v`.
  - `git clone https://github.com/IBE160-2026/G78-larsen.git g78-fresh-clone` i scratchpad, på `7aa4e14` (= `origin/main`). Mappenavnet er et annet, så compose får egne volumer.
  - `docker compose up --build --wait`: alle fire tjenestene var friske etter 33 s.
  - Playwright med klikk på `http://localhost:8000`:
    - Landing viste «Before you come».
    - En booking av 2 plasser gikk gjennom Details, Review og betaling til Confirmation `7JVM8BCA`.
    - Anonym `/admin/bookings` sendte videre til Sign-in.
    - Innlogging virket, og bookinglisten og Outbox viste bookingen og e-posten.
    - Eksempelbookingen i morgen (Ingrid Berg) sto i bookinglisten.
  - `docker compose ps` viste fire friske tjenester. `docker compose logs backend proxy` inneholdt verken testpassordet eller gjestens e-post.
  - Testbrytere: `cp` (også i PowerShell), `payment = "fail"` og `docker compose restart backend` ga `409 payment_failed`. Filen ble fjernet igjen. Den er git-ignorert.
  - `docker compose exec -T backend booking-platform create-admin` med svarene sendt inn i en pipe ga «created», exit 0. Uten TTY ga den «cancelled, nothing written».
  - Utviklingsoppsettet: `docker compose down`, `uv sync`, `docker compose up -d --wait db`, `uv run booking-platform dev` (`/api/health` ok), `npm --prefix frontend ci` og `npm --prefix frontend run dev` (`/`, `/book-seats` og `/api/venue` ga 200 på 3000).
  - `uv run playwright install chromium` og så `uv run pytest -q`: **536 passed** på 12 min 34 s.
  - `docker compose down -v` fjernet bare klonens prosjekt.
- **Rettet i README-en etter kjøringen:**
  - Compose bruker databasen `booking` og utviklingsoppsettet `booking_dev`, så de kan kjøre samtidig. Det ble kjørt og bekreftet.
  - `cp` virker også i PowerShell.
  - Testene tar 10–15 minutter.
  - Loggene inneholder metode, sti, statuskode og feilkode.
  - `"hold"` betyr at betalingen venter.
- **I repoet:**
  - `uv run pytest -q`: 536 passed.
  - `npm --prefix frontend run build`: ok.
  - Stakken `g78-larsen` er startet igjen, og alle fire tjenestene er friske.
- **`tests/manual/core-accessibility.md`** er sjekklisten med fire rader og dekkende tester. Alle radene står som *Pending*.
- **`.docs/sensorveiledning-kravsporing.md`**: rad 3 (status og lenke til sjekklisten) og rad 6 (kjøreguide og fersk klone) er oppdatert.
- **Gjennomgang** (Blind Hunter, Edge Case Hunter, Verification Gap): 17 funn. 13 ble rettet i README-en, sjekklisten og kravsporingen, 3 ble avvist, og 1 var uten funn. Alt står i Review Triage Log i spesifikasjonen. Ingenting er utsatt.
- Committet lokalt som `9632a10`. Ingenting er pushet. Spesifikasjonen står som `in-review`, og storyen står fortsatt som `in-progress` i sprint-status.

### Åpne punkter
- Lisa kjører de fire manuelle tilgjengelighetstestene i `tests/manual/core-accessibility.md` og rapporterer dato, nettleser og utfall. Agenten fører dem inn. Zoom-raden avgjør punktet om e-posten på Review.
- Lisa kjører `create-admin` interaktivt i en ekte terminal: `docker compose exec backend booking-platform create-admin`, `uv run booking-platform create-admin` og PowerShell-linjen med `$env:BP_DATABASE_URL`. Kravet er at hver kommando i README-en er kjørt.
- Etter det skal «Core done» (eller hva som mangler) stå i loggen. Deretter settes spesifikasjonen til `done` og storyen til `done` i sprint-status, og PR-en lages.

## 2026-11-24 kl. 09:18 — Lisa Larsen

### Oppgave
Kjøre de fire manuelle tilgjengelighetstestene i `tests/manual/core-accessibility.md` (Lisa tester, agenten forbereder, retter og fører inn). Lisa ba om at avvikene fra zoom- og NVDA-testen ble rettet med en gang.

### Plan
- Starte Docker Desktop og stakken (`docker compose up --build --wait`), åpne `localhost:8000` i Edge, sette vindusstørrelser for zoom-testen og installere NVDA (`winget install NVAccess.NVDA`, versjon 2026.3).
- Føre inn hvert resultat i sjekklisten, rette avvik i samme story med en dekkende automatisk test, og bygge stakken på nytt så Lisa kunne teste igjen.
- Spesifikasjon: [`spec-2-4-core-done-readme-clean-clone-manual-passes.md`](../../.docs/implementation-artifacts/spec-2-4-core-done-readme-clean-clone-manual-passes.md).

### Resultat
- **Alle fire testene er bestått** 2026-11-24 i Edge 158.0.4370.33 (test 4 med NVDA 2026.3). Ingen rad står som *Pending*. Sjekklisten sier nå «NVDA with Chrome or Edge».
  1. Tastatur: Pass. Enter gjør ingenting i datofeltet og Seat picker, men verdien beholdes ved Tab. Det er forventet.
  2. 200 % zoom: 1366×768 viste venstre kolonne som klemte innholdet, og e-posten på Review brøt midt i ordet. Rettet, deretter Pass i både 1366×768 og 1920×1080 (vinduet satt til ca. 960 × 540 CSS-piksler).
  3. Tabulatorrekkefølgen på Book seats: Pass.
  4. NVDA: to avvik rettet, deretter Pass.
- **Rettinger:**
  - `frontend/app/styles.css`: under 1024 px er skallet én kolonne. Venstre kolonne tegnes over main; på Book seats under øktlisten (`.shell:has(.rail-book)`). «Find us» stables også. Over 1024 px er ingenting endret. Dette er den enkle stablingen EXPERIENCE.md (Zoom) tillater; det fulle mobiloppsettet er fortsatt FR-51, og WCAG 1.4.10 står fortsatt under «Ikke levert».
  - `frontend/components/BookingSummary.js`: en e-postadresse kan bare brytes foran `@` (`<wbr>`).
  - `frontend/components/SessionList.js`: den synlige teksten i øktradene er `aria-hidden`, så NVDA i lesemodus leser hver rad én gang (radioknappens navn har alt). Deaktiverte rader hoppes over med piltastene i fokusmodus, som for alle deaktiverte radioknapper, og leses som «unavailable» med årsak i lesemodus.
  - `frontend/lib/confirmation.js` (ny), `Review.js`, `Confirmation.js`: etter Pay leste NVDA bare «Saunalöyly», fordi Confirmation ikke hadde h1 mens bookingen ble lest. Review leser nå bekreftelsen før den navigerer, så «Booking confirmed» finnes fra første tegning og får fokus. Feiler lesingen, eller lastes siden på nytt, leser Confirmation selv som før.
  - `tests/e2e/test_fr23_keyboard_and_zoom.py`: zoom-testen sjekker at Review og Confirmation er én kolonne og at e-posten står på én linje (og tar skjermbilde av Confirmation); øktlistetesten sjekker at bare de åtte radioknappene eksponeres; ny test `test_after_pay_confirmation_has_its_heading_at_once_and_focused`. Den feilet mot den gamle koden og består med rettingen.
- **Tester:** de berørte e2e-filene består (fr01, fr02, fr05, fr11, fr22, fr23). Hele `uv run pytest -q` ble startet til slutt; resultatet står i sluttoppsummeringen.
- **Databasen på `localhost:8000`:** de to fyllbookingene for NVDA-testen (30.11 kl. 10:00 og 11:30) og agentens prøvebooking «Probe Guest» er slettet med betalinger, e-poster og nøkler.
- Ingenting av koden er committet ennå.
- Lukket i `issues.md`: punktet om e-posten på Review i 200 % zoom.

### Åpne punkter
- Lisa kjører `create-admin` interaktivt i en ekte terminal (compose, `uv run` og PowerShell-linjen) — fortsatt åpent.
- Etter det: «Core done» i loggen, spesifikasjonen og storyen til `done` i sprint-status, og PR.
- `EXPERIENCE.md` (Responsive, «Below 1024 px») sier fortsatt bare `[ASSUMPTION]`: før inn at en enkel stabling er bygget for Core (Wordmark og venstre kolonne over main, på Book seats under øktlisten).
