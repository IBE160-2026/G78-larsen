# G78 — Saunalöyly Booking Platform

Gruppeprosjekt i **IBE160 Programmering med KI** ved Høgskolen i Molde, høsten 2026 (15 studiepoeng). Repoet inneholder applikasjonen og dokumentasjonen av hvordan den er planlagt, bygget og kvalitetssikret med KI (BMAD og Claude Code).

## Medlemmer

- Lisa Katarina Larsen

## Hva appen gjør

Saunalöyly er et fiktivt, finsk-inspirert badstuanlegg med fire badstuer. Gjester velger dag og antall plasser, ser hvilke økter som har ledige plasser og hva det koster, og betaler uten konto. Administrator logger inn og ser hvem som kommer til hver økt, og leser e-postene plattformen har sendt. Betaling og e-post er simulert.

Det vanskelige er kapasiteten: plattformen skal aldri selge samme plass to ganger, heller ikke når to gjester trykker «Pay» i samme sekund. Hele kravsettet står i [PRD-en](.docs/planning-artifacts/prds/prd-booking-platform-2026-10-29/prd.md).

## Status (2026-11-24)

Core er bygget (Epic 1 og 2, PRD §10.1): landingssiden, Book seats, Details, Review og Confirmation med simulert betaling og avvisninger uten belastning, vilkår og personvern, og for Administrator innlogging, bookinglisten og Outbox. Hele plattformen går over HTTPS (Epic 3, FR-24); vanlig HTTP blir bare sendt videre til HTTPS. Epic 4 er påbegynt: hver Seat-booking får en Manage-lenke i bekreftelses-e-posten, og lenken åpner bookingen uten konto (Story 4.1). Selve endringene (flytte plasser, Voucher) er ikke bygget ennå. Status per vurderingskriterium står i [sensorveiledningen](.docs/sensorveiledning-kravsporing.md).

### Ikke levert

Dette er ikke bygget per i dag (DR-2). Senere epics korter ned listen.

- **Suksesskriteriene SC2–SC8**: hel badstue (SC2, SC4), endre plasser eller ta Voucher (SC3), gavekort (SC5), dørkoder (SC6), medlemskap og klippekort (SC7, bare visjon) og justerbare regler (SC8).
- **FR-26 til FR-51**: endringer og Vouchere (Manage-lenken, FR-25, åpner bookingen, men tilbyr ingen endring ennå), hel badstue, holds, gjestekontoer, innstillinger, blokker, gavekort, dørkoder og mobiloppsett. Noen regler fra den første skiva (holds og blokker, FR-35, FR-36, FR-40, FR-41) finnes i databasen og har tester, men ingen side bruker dem ennå.
- **Mobildelen av SC10**. Core er laget for laptop.
- **WCAG 1.4.10 Reflow** (innhold i 320 CSS-piksler bredde uten rulling i to retninger) er ikke oppfylt før mobiloppsettet (FR-51) finnes. Det er det eneste avviket fra WCAG 2.2 AA som de automatiske testene kjenner, og tilgjengelighetsrapporten fra e2e-testene oppgir det. De manuelle testene og funnene deres står i [`tests/manual/core-accessibility.md`](tests/manual/core-accessibility.md).

## Forutsetninger

Tre verktøy må være installert:

- [uv](https://docs.astral.sh/uv/) (installerer selv Python 3.12, se `.python-version`)
- [Node.js](https://nodejs.org/) 24 LTS eller nyere (testene og utvikling av frontend)
- [Docker](https://www.docker.com/) med Docker Compose (kjører hele plattformen)

I tillegg trengs Git for å klone repoet.

## Kom i gang

```sh
git clone https://github.com/IBE160-2026/G78-larsen.git
cd G78-larsen
docker compose up --build --wait
```

Kommandoen bygger og starter de fire tjenestene (Caddy, FastAPI, Next.js og PostgreSQL) og venter til alle er friske. Første gang tar det noen minutter. Åpne så **`https://localhost:8443`**. Bruk `localhost`, ikke `127.0.0.1`: Caddy svarer bare for `localhost`.

Nettleseren advarer én gang om sertifikatet, fordi det er utstedt av Caddys egen lokale sertifikatutsteder (CA) og ikke av en offentlig. Godta advarselen (i Chrome: «Avansert» og «Fortsett til localhost»), så åpnes landingssiden. Det er ikke nødvendig å gjøre mer.

Vil du slippe advarselen, kan du kopiere Caddys rotsertifikat ut av containeren og importere det i nettleseren eller operativsystemet. Det er valgfritt. Fjern det igjen etter sensuren, for alle som har nøkkelen i `caddy_data`-volumet, kan utstede sertifikater maskinen din da stoler på:

```sh
docker compose cp proxy:/data/caddy/pki/authorities/local/root.crt .
```

Rotsertifikatet ligger i volumet `caddy_data` og overlever `docker compose down`. Etter `docker compose down -v` lager Caddy en ny rot, og da må den kopieres og importeres på nytt (og den gamle fjernes).

På Windows (Chrome og Edge bruker Windows' sertifikatlager) importerer og fjerner du den slik, for din egen bruker:

```powershell
certutil -addstore -user Root root.crt                                        # importer
certutil -delstore -user Root "Caddy Local Authority - 2026 ECC Root"         # fjern etter sensuren
```

Navnet er det Caddy gir roten (årstallet er året den ble laget; se `certutil -dump root.crt`). På macOS brukes Nøkkelring (Keychain Access), og Firefox har sin egen sertifikatbehandler (Innstillinger → Personvern og sikkerhet → Vis sertifikater → Autoriteter).

Vanlig HTTP på port 8000 svarer bare med en omdirigering til HTTPS (HT-1). Slik ser du det:

```sh
curl -i http://localhost:8000/
```

Svaret er `308 Permanent Redirect` med `Location: https://localhost:8443/` og ingen andre av nettstedets hoder. Ingen forespørsel over HTTP når backend eller frontend, og ingenting i databasen endres. I PowerShell skrives `curl.exe` i stedet for `curl`.

Caddy er eneste inngang og har de eneste publiserte webportene (`127.0.0.1:8443` for HTTPS og `127.0.0.1:8000`, som bare omdirigerer). Den sender `/api` og `/api/*` til FastAPI og resten til Next.js. Backend og frontend nås bare på det interne compose-nettverket. Databasen er i tillegg publisert på `127.0.0.1:55432`, for utvikling og API-testene.

## Utvikling uten Docker for backend og frontend

```sh
uv sync                              # installerer Python og avhengighetene i .venv
docker compose up -d --wait db       # starter bare PostgreSQL (port 55432)
uv run booking-platform dev          # API-et på http://127.0.0.1:8001, starter på nytt ved endringer
npm --prefix frontend ci             # én gang: frontendens avhengigheter
npm --prefix frontend run dev        # Next.js på http://127.0.0.1:3000; /api/* sendes videre til 127.0.0.1:8001
```

Kjør `uv run booking-platform dev` og `npm --prefix frontend run dev` i hvert sitt terminalvindu, og åpne **`http://127.0.0.1:3000`** (Administrator: `http://127.0.0.1:3000/admin/sign-in`). Backend svarer på `http://127.0.0.1:8001/api/health`. Compose-stakken kan kjøre samtidig: den bruker databasen `booking`, utviklingsoppsettet `booking_dev` i samme `db`-container.

`uv run booking-platform dev` oppretter databasen `booking_dev` første gang og kjører migrasjonene i `migrations/`. Ved hver oppstart legges badstuene, øktplanen, eksempelbookingene og Administrator fra `seeds/` inn der de mangler; seeden overskriver aldri noe som allerede står i databasen. Øktene genereres fra planen fram til slutten av bookinghorisonten (4 uker), så en fersk klone alltid har datoer å booke.

## Tester

To forberedelser, én gang:

```sh
npm --prefix frontend ci             # frontendens avhengigheter, også axe-core som e2e-testene bruker
uv run playwright install chromium   # nettleseren til e2e-testene
```

Deretter:

```sh
uv run pytest
```

Docker må kjøre. Testene har to lag:

- **API-testene** (`tests/`) starter `db`-tjenesten, oppretter databasen `booking_test` på nytt og sender ekte HTTP-forespørsler til en egen backend-prosess mot ekte PostgreSQL. Noen skriver også rett til databasen for å vise at reglene holder utenom API-et (FR-10).
- **E2e-testene** (`tests/e2e/`) starter hele stakken som et eget compose-prosjekt, `booking_e2e`, på ledige porter (så de aldri kolliderer med stakken på 8000 og 8443), kjører Playwright og axe-core mot den og fjerner den med `down -v` til slutt.

Hele settet (over 500 tester) tar 10–15 minutter, mer første gang imagene bygges. Skjermbildene fra 200 %-zoom-testen havner i `test-results/zoom/` (ikke i git). De manuelle tilgjengelighetstestene, med dato, nettleser, utfall og hvilken automatisk test som dekker hver av dem, står i [`tests/manual/core-accessibility.md`](tests/manual/core-accessibility.md).

`BP_TEST_MUTATE=<navn>` slår av én beskyttelse i databasen (se `MUTATIONS` i `tests/conftest.py`) for å vise at testene da feiler.

## Administrator og eksempelbookinger

Første gang backend starter, legger seeden inn én Administrator (`seeds/admin.json`); en omstart overskriver aldri passordet. Testinnloggingen gjelder bare lokalt:

| E-post | Passord |
|---|---|
| `admin@saunaloyly.example` | `badstue-admin-test-2026` |

Logg inn på `https://localhost:8443/admin/sign-in`. Etter innlogging åpnes **bookinglisten** på `https://localhost:8443/admin/bookings`, med gjestene per økt for valgt dato. Etter 5 feil på rad for én e-post er den sperret i 15 minutter.

Seeden legger også inn tolv eksempelbookinger (`seeds/bookings.json`), én gang, regnet i dager fra datoen backend startet første gang:

| Dag | Økt | Bookinger | Hvordan økten ser ut |
|---|---|---|---|
| I morgen | 14:30 | 1 (2 plasser) | Vanlig |
| Om 2 dager | 17:30 | 5 (42 av 44 plasser) | 2 plasser igjen |
| Om 3 dager | 19:00 | 5 (44 av 44 plasser) | Fullt |
| Om 5 dager | 10:00 | 1 (4 plasser) | Vanlig |

En omstart, også en senere dag, lager ingen kopier.

## Outbox

E-post sendes ikke ut. Hver e-post plattformen sender, legges i **Outbox**, en simulert postkasse: `https://localhost:8443/admin/outbox` (lenken «Outbox» i Administrator-linjen). Den viser hver e-post slik den ble sendt, også de gjesten aldri ser på en side. Bekreftelsen fra en ny booking dukker opp her og på Confirmation-siden. Alle lenker i e-postene er absolutte og begynner med `https://localhost:8443` (`BP_BASE_URL`).

**Eksempel på Manage-lenke:** hver eksempelbooking har en lenke i sin bekreftelses-e-post i Outbox (emne «Booking confirmed: …»), på linjen under «Manage your booking». Den ser slik ut: `https://localhost:8443/manage#t=…`. Åpne den i nettleseren, så vises bookingen på `/manage/<referanse>`, og tokenet er borte fra adresselinjen. En eksempelbooking som fantes før Manage-lenkene ble bygget, får i stedet sin egen e-post med emnet «Manage your booking: <referanse>». Lenken virker til bookingens badstueøkt er slutt (DR-2); etter det, og for en gjettet referanse, viser siden «This page is not available.». Tilgangen i nettleseren varer 30 minutter etter siste bruk; å åpne lenken på nytt gir den tilbake.

## Drift

### Ny Administrator eller nytt passord

```sh
docker compose exec backend booking-platform create-admin   # i compose-stakken
uv run booking-platform create-admin                         # mot booking_dev (utvikling)
```

I PowerShell er det de samme kommandoene. Mot en annen database settes URL-en først:

```powershell
$env:BP_DATABASE_URL = "postgresql://postgres:booking@127.0.0.1:55432/booking_dev"; uv run booking-platform create-admin
```

Kjør den i et vanlig terminalvindu (PowerShell, Terminal eller cmd), ikke gjennom en pipe: den spør etter e-post og to ganger etter passordet uten å vise det; passordet tas aldri som argument eller miljøvariabel. Den skriver e-posten og «created» eller «password changed». Passordet må ha minst 15 tegn, kan ikke stå på listen over vanlige passord og kan ikke være lik e-postadressen; et passord som bryter en regel, gir én linje og exit-kode 2 uten at noe lagres.

### Testbrytere

Testbryterne lar deg prøve en avvist betaling (`payment = "fail"`), en betaling som venter (`"hold"`) eller en tvunget databasekonflikt (`force_conflict = true`). Ingen av dem belaster noe eller lagrer en booking:

```sh
cp config/test-switches.example.toml config/test-switches.toml   # virker også i PowerShell
docker compose restart backend
```

Endre `config/test-switches.toml` mellom de to kommandoene. Backend leser filen bare ved oppstart, så kjør `docker compose restart backend` etter hver endring (`cp` trengs bare første gang; den overskriver endringene dine). Uten filen er alle brytere av: slett den og kjør `docker compose restart backend` igjen for å slå dem av. Filen committes ikke.

### Status, logger og stopp

```sh
docker compose ps                    # status og helsesjekker for de fire tjenestene
docker compose logs backend proxy    # logger fra backend og Caddy
docker compose down                  # stopper og fjerner containerne; dataene blir liggende
docker compose down -v               # fjerner også volumene: databasen og Caddys data (ny rot)
```

Etter `down -v` starter neste `docker compose up --build --wait` med en tom database, ny seed og eksempelbookinger regnet fra den dagen. `down -v` fjerner også `booking_dev` fra utviklingsoppsettet, som ligger i samme `db`-container.

## Konfigurasjon

Alt har en standardverdi som virker lokalt, og ingen `.env`-fil trengs. Backend leser bare `BP_*`-miljøvariabler:

| Variabel | Standard | Betydning |
|---|---|---|
| `BP_DATABASE_URL` | `postgresql://postgres:booking@127.0.0.1:55432/booking_dev` | Databasen (`booking_dev` opprettes bare når standard-URL-en brukes) |
| `BP_BASE_URL` | `http://127.0.0.1:3000` | Opprinnelsen nettleseren bruker; skrivende forespørsler må komme derfra (CSRF) |
| `BP_HTTPS` | `off` | Gjør øktkapselen `Secure`; krever at `BP_BASE_URL` begynner med `https://` |
| `BP_HOST`, `BP_PORT` | `127.0.0.1`, `8001` | Hvor backend lytter |
| `BP_ROOT` | repoets rot | Rot for `migrations/`, `seeds/`, `content/` og `config/` (imaget setter `/app`) |
| `BP_TEST_SWITCHES` | `config/test-switches.toml` | Testbryterfilen; mangler den, er alle brytere av |

Docker Compose og frontenden leser i tillegg disse:

| Variabel | Standard | Betydning |
|---|---|---|
| `HTTPS_PORT` | `8443` | HTTPS-porten Caddy lytter på og publiserer på `127.0.0.1`; også i `BP_BASE_URL` i compose og i omdirigeringen |
| `HTTP_PORT` | `8000` | HTTP-porten Caddy lytter på og publiserer på `127.0.0.1`; den svarer bare med omdirigering til HTTPS |
| `HSTS_MAX_AGE` | `3600` | `max-age` i `Strict-Transport-Security` (sekunder); settes bare når du vil overstyre |
| `DB_PORT` | `55432` | Databaseporten på `127.0.0.1` (en annen verdi krever en tilsvarende `BP_DATABASE_URL`) |
| `SWITCHES_DIR` | `./config` | Mappen som monteres skrivebeskyttet som `/app/config` i backend (testbryterne) |
| `API_INTERNAL_URL` | compose: `http://backend:8000`, ellers `http://127.0.0.1:8001` | Hvor frontendens server kaller backend (`frontend/lib/server-api.js`) |

## Sikkerhet

Slik beskyttes dataene i denne versjonen (FR-21). Det stemmer med personvernerklæringen på `https://localhost:8443/privacy` ([kilden](frontend/app/privacy/page.js)).

- **Passord** lagres bare som Argon2id-hash. Testpassordet over står i klartekst i `seeds/admin.json` fordi det bare gjelder lokalt.
- **Roller** sjekkes på serveren ved hver forespørsel. Alle Administrator-endepunkter ligger under `/api/admin/`, og uten en innlogget Administrator-økt svarer de `401`; en gjests bookingøkt gir ingen tilgang. Sidene under `/admin` sender en anonym besøkende til innloggingen (`tests/e2e/test_fr15_sign_in.py`).
- **Økter** er rader på serveren. Nettleseren får én informasjonskapsel med et tilfeldig token, og databasen lagrer bare en hash av det. Gjesten får kapselen på Book seats eller når en Manage-lenke åpnes; ved Administrator-innlogging får den samme kapselen et nytt token.
- **Ingen tredjepartsforespørsler**: fontene og bildene er selvhostet (se `ASSETS.md`), og API-dokumentasjonen (`/docs`, `/openapi.json`) er slått av (`tests/test_fr20_access.py`).
- **Ingen hemmeligheter i loggene** (AD-19): loggene har metode, sti, statuskode og feilkode, aldri forespørselskropper, hoder, informasjonskapsler, passord eller tokener. E2e-testene sjekker loggene for testpassordet, økttokenene og forespørselskroppene.
- **Skrivende forespørsler** må komme fra plattformens egen opprinnelse (CSRF, FR-18), og all inndata valideres på serveren.
- **HTTPS** (FR-24): alle sider og hele API-et går over HTTPS, og HTTPS ender i Caddy. Backend og frontend nås bare på det interne compose-nettverket, og Caddy publiserer bare på `127.0.0.1`. Vanlig HTTP får bare en omdirigering og returnerer eller endrer aldri data. Hvert HTTPS-svar har `Strict-Transport-Security: max-age=3600` (uten `includeSubDomains` og `preload`), og øktkapselen er `Secure`, `HttpOnly`, `SameSite=Strict` og `Path=/` (`tests/e2e/test_fr24_https.py`). Ingen forespørsel går til en tredjepart. En produksjonsinstallasjon ville brukt et offentlig sertifikat og HSTS i ett år; den korte verdien her hindrer at sensors `localhost` låses til HTTPS lenge.
- **Manage-lenker** (PRD §4.8, FR-25): tokenet har 256 tilfeldige biter og ligger bare i lenkens fragment (`#t=`), så det havner aldri i en sti, en spørring, en logg eller en referrer. Databasen lagrer bare en SHA-256-hash av det. Siden fjerner fragmentet fra adresselinjen og bytter tokenet mot en tilgang knyttet til nettleserens økt; tilgangen gjelder bare den ene bookingen, varer 30 minutter etter siste bruk og forsvinner ved utlogging. Ukjente, ugyldige, utløpte og andres lenker og referanser får det samme svaret, «This page is not available.» (`404`). Caddy legger `X-Robots-Tag: noindex` og `Referrer-Policy: no-referrer` på Manage-sidene og -API-et. Outbox, som er en simulert postkasse, viser lenkene slik de ble sendt, og er bare åpen for Administrator (`tests/test_fr25_manage_link.py`, `tests/e2e/test_fr25_manage.py`).

## Kjente begrensninger

- **`Secure`-kapsler til `http://localhost`**: nettlesere regner `localhost` som en sikker opprinnelse og sender derfor også `Secure`-kapsler til `http://localhost:8000`. Der svarer Caddy bare med omdirigeringen, så forespørselen når aldri backend, og økten endres ikke.
- **HSTS fra `localhost`**: Chrome og Firefox ser bort fra `Strict-Transport-Security` fra `localhost`. Hodet sendes likevel, og omdirigeringen i Caddy er det som sender HTTP over til HTTPS.
- **Sertifikatadvarselen**: sertifikatet er fra Caddys lokale CA, så nettleseren advarer én gang (se «Kom i gang»).

## Mappestruktur

```
src/booking_platform/   Python-pakke (backend): api/ → services/ → db/, config.py
migrations/             Nummererte SQL-migrasjoner; skjemaet endres bare her
seeds/                  Seed-data: badstuene (venue.json), eksempelbookingene (bookings.json), Administrator (admin.json)
content/                Tekst som deles av sider og e-post (bookingvilkår, resepsjonssetningen)
config/                 Eksempel på testbryterfil (den ekte filen committes ikke)
frontend/               Next.js (App Router, JavaScript): app/, components/, lib/, public/ (fonter og bilder)
tests/                  API-tester mot ekte backend og PostgreSQL
tests/e2e/              Nettlesertester med Playwright og axe-core mot hele stakken
tests/manual/           Sjekklisten og resultatene for de manuelle tilgjengelighetstestene (FR-23)
Caddyfile               Proxyen: eneste inngang, ruting og svarhoder
docker-compose.yml      De fire tjenestene (proxy, backend, frontend, db) med helsesjekker
Dockerfile              Backend-imaget (frontend/Dockerfile er frontend-imaget)
ASSETS.md               Register over fonter og bilder med kilde og lisens (DR-3)
.docs/                  Planlegging: brief, PRD, UX, arkitektur, epics og spesifikasjonene per story
.logs/<bruker>/         Sesjonslogger: oppgave, plan, resultat og åpne punkter per økt
_bmad/, .claude/skills/ BMad Method og prosjektets egne skills for Claude Code
pyproject.toml, uv.lock Avhengigheter (eneste kilde) og låste versjoner
```

## Plan- og prosessdokumentasjon

| Dokument | Innhold |
|---|---|
| [Product brief](.docs/planning-artifacts/briefs/brief-booking-platform-2026-09-20/brief.md) og [tilbakemelding](.docs/planning-artifacts/briefs/brief-booking-platform-2026-09-20/tilbakemelding-product-brief.md) | Hva som skal bygges, og lærerens vurdering av briefen |
| [PRD](.docs/planning-artifacts/prds/prd-booking-platform-2026-10-29/prd.md) og [addendum](.docs/planning-artifacts/prds/prd-booking-platform-2026-10-29/addendum.md) | Krav (FR-1 …), testbare konsekvenser, leveringskrav (DR-1 …) og åpne spørsmål |
| [Research](.docs/planning-artifacts/research/) | Samtidighet og plassreservasjon, kapasitetsmodell med 85 eksempler, dørkoder |
| [UX](.docs/planning-artifacts/ux-designs/ux-booking-platform-2026-11-05/EXPERIENCE.md) og [design](.docs/planning-artifacts/ux-designs/ux-booking-platform-2026-11-05/DESIGN.md) | Hvordan plattformen oppfører seg og ser ut |
| [Arkitektur](.docs/planning-artifacts/architecture/architecture-booking-platform-2026-11-03/ARCHITECTURE-SPINE.md) | FastAPI + PostgreSQL, Next.js og Caddy i Docker Compose |
| [Epics og stories](.docs/planning-artifacts/epics.md) | Arbeidet delt i stories, med akseptansekriterier |
| [Brainstorm: minste v1](.docs/brainstorming/brainstorm-minste-v1-mvp-2026-10-27/brainstorm-intent.md) | Hva som er kjerne og hva som er «hvis tid» |
| [Sesjonslogger](.logs/lisa-larsen/) | Hva som ble spurt om, planlagt og besluttet i hver KI-økt |
| [Åpne punkter](.logs/lisa-larsen/issues.md) | Avklaringer som gjenstår, med lenke til økta de oppstod i |
| [Sensorveiledning: kravsporing](.docs/sensorveiledning-kravsporing.md) | Status per vurderingskriterium og hva som gjenstår |

## Prosess

Planleggingen er gjort med BMAD-skills i Claude Code. Hver økt logges i `.logs/` med oppgave, plan og resultat, og beslutninger føres inn i PRD-en med dato. Under implementeringen arbeides det på én gren per story, med pull request som viser hvilke krav (FR-nummer) som er dekket, hvordan KI ble brukt, og hvilke tester og funn kvalitetssikringen ga. Se [PR-malen](.github/pull_request_template.md). Avhengigheter legges til med `uv` (`pyproject.toml` og `uv.lock`), aldri med pip eller `requirements.txt`.
