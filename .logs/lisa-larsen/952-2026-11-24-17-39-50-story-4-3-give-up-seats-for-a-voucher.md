# Story 4.3: Give up Seats for a Voucher

## 2026-11-24 kl. 17:39 — Lisa Larsen

### Oppgave
`/bmad-build story 4-3-give-up-seats-for-a-voucher`: planlegge story 4.3 (FR-27). Gjesten skal kunne gi fra seg noen eller alle plassene for en voucher verdt det hen betalte. Lisa valgte «Godkjenn og stopp», så implementeringen tas i en ny `bmad-build`-sesjon.

### Plan
- Steg 1: epic-4-konteksten var eldre enn EXPERIENCE.md og backcastingen og ble kompilert på nytt med en subagent. 4.2-specen ble lastet for kontinuitet.
- Steg 2: undersøkte kodebasen (`services/change.py`, `db/changes.py`, migrasjonene `0006`/`0009`/`0011`, Manage-frontend, Booking list, testhjelpere) og AD-29/30/31. Skrev specen, avklarte fire åpne spørsmål med Lisa og satte status `ready-for-dev`.
- Spec: [spec-4-3-give-up-seats-for-a-voucher.md](../../.docs/implementation-artifacts/spec-4-3-give-up-seats-for-a-voucher.md)

### Resultat
- `.docs/implementation-artifacts/epic-4-context.md` er kompilert på nytt og tar med 4.2-tekstene og backcast-sjekkpunktet (Epic 4 merget innen fre 27. nov).
- Ny spec med status `ready-for-dev` og rute `dispatch`, ca. 3 600 tokens. Lisa godtok å holde den samlet som én PR.
- Lisas beslutninger (står ordrett i den låste intent-blokken):
  - Voucherverdien er alltid plassene som gis fra seg × prisen per plass som er lagret på bookingen.
  - Manage-siden for en kansellert booking åpner fortsatt. Den viser bookingen som kansellert, linjen «This booking was cancelled on … You gave up all seats for a voucher, which was sent by email.» og ingen endringslenker. Dette avgjør EXPERIENCE.md Open Item 19.
  - Gjestetekstene er godtatt som foreslått: «Give up seats for a voucher», «Give up seats», «What will happen» med «Voucher value» og «Valid until», «No money is paid back. …», og resultatsiden «Seats given up».
  - E-posten er «Booking changed: {ref}» når noen plasser gis fra seg og «Booking cancelled: {ref}» når alle gis fra seg, begge med voucher-blokken (kode, verdi, Valid until, «never paid out in money»).
  - I bookinglisten: historikklinjen «Gave up N seats on … for a voucher of NOK {verdi}» og statuscellen «Cancelled dd.mm.yyyy HH:MM · Guest · Voucher».
- Mine egne valg, som står i specen:
  - `seat_guest_refund_forbidden` er skrevet uten `kind`-kolonne, fordi alle `bookings`-rader er plassbookinger fram til Epic 5.
  - Ny migrasjon `0012`.
  - Endepunktet `POST /api/manage/{ref}/seats/voucher`.
  - En felles låse- og nøkkeldel som brukes av både `move` og `voucher`.
  - Pris 0 gir ingen voucher (CHECK-en `value_ore > 0`), og den saken håndteres ikke videre i v1.
- Specen og den nye epic-konteksten er ikke committet; de hører til story-branchen.

### Åpne punkter
- Implementer story 4.3 i en ny `bmad-build`-sesjon. Specen er `ready-for-dev`.
- EXPERIENCE.md Open Item 19: før inn Lisas beslutning (Manage-siden viser en kansellert booking med teksten, uten endringslenker), og før inn voucher-tekstene for gjesten.

## 2026-11-24 kl. 17:43 — Lisa Larsen

### Oppgave
Føre inn beslutningen om den kansellerte Manage-siden (Open Item 19) og voucher-tekstene i EXPERIENCE.md.

### Plan
- Ny tabell «Give up seats wording» under «Move seats wording» i Voice and Tone, i samme form som tabellen for 4.2.
- Merke Open Item 19 som lukket.
- Føre beslutningen inn i epic-4-konteksten også, så den fortsatt er gyldig (nyere enn planleggingsdokumentene) når neste build starter.

### Resultat
- `EXPERIENCE.md`: ny tabell «Give up seats wording, accepted by Lisa (2026-11-24, Story 4.3, FR-27)». Den har regelen for voucherverdien og alle tekstene: lenke, steg, oppsummering, knapp, resultat, refusals, den kansellerte Manage-siden, e-posten, historikklinjen og statuscellen i bookinglisten. Open Item 19 er merket «Closed by Lisa 2026-11-24».
- `epic-4-context.md`: linjen om det som gjenstår å avgjøre har fått inn 4.3-beslutningen. Konteksten er nyere enn alle planleggingsdokumentene igjen.
- Ikke committet. Endringene hører til story-branchen sammen med specen.

### Åpne punkter
Ingen nye.

## 2026-11-24 kl. 18:40 — Lisa Larsen

### Oppgave
Implementere story 4.3 etter specen (`.docs/implementation-artifacts/spec-4-3-give-up-seats-for-a-voucher.md`), som er eneste sannhetskilde. Kjørt som subagent fra en `bmad-build`-økt.

### Plan
- Migrasjon `0012` (vouchers, kanselleringskolonner og trigger, `voucher_id` i historikk og betalinger, ny `retention_due`).
- `db/vouchers.py` + `services/voucher.py`, så `services.change.voucher` med felles prolog `_locked` (som `move` også bruker), endepunkt `POST /api/manage/{ref}/seats/voucher`.
- Manage-lesingen og bookinglisten får kanselleringsfeltene; frontend: `GiveUpSeats.js`, `/manage/[reference]/voucher`, Manage-siden (lenke og kansellert tilstand), bookinglisten.
- Tester: `test_fr27_voucher_for_seats.py`, e2e `test_fr27_voucher.py`, og bare nødvendige utvidelser i eksisterende tester.

### Resultat
- Nye filer: `migrations/0012_vouchers_cancellation.sql`, `src/booking_platform/db/vouchers.py`, `src/booking_platform/services/voucher.py`, `frontend/components/GiveUpSeats.js`, `frontend/app/manage/[reference]/voucher/page.js`, `tests/test_fr27_voucher_for_seats.py`, `tests/e2e/test_fr27_voucher.py`.
- Endret: `db/changes.py`, `db/bookings.py`, `db/manage.py`, `db/booking_list.py`, `services/change.py` (felles `_locked`, `voucher`, Voucher-e-post), `services/history.py` (`voucher_value_ore`), `services/manage.py` (`cancelled_at`), `services/booking_list.py`, `api/manage.py`, `api/schemas.py` (`VoucherIn`), `lib/copy.js`, `ManageBooking.js`, `ManageBookingSummary.js`, `BookingList.js`, `styles.css`, README og sensorveiledningen.
- Eksisterende tester utvidet bare for nye kolonner: `conftest.clear` (vouchers), `test_dr4_migrations.py` (ny trigger, 0011-testen migrerer bare til 0011, ny 0012-test), `test_fr16_booking_list.py`, `test_fr25_manage_link.py`, `test_fr26_move.py` (direkte kansellering må nå sette kanselleringskolonnene).
- `uv run pytest tests --ignore=tests/e2e`: 464 passert. `npm --prefix frontend run build`: ok, `/manage/[reference]/voucher` bygges. E2e: 174 passert; den nye e2e-testen feilet først på et Tab-trykk før Manage-siden var lastet (testfeil, rettet med venting), og passerer nå alene (1 passert).
- Valgt selv: siste gyldige dag vises i steget ut fra API-ets `today` (`GET /api/windows`) + ett år i nettleseren (ingen klokke leses); gamle kansellerte rader i dev-databaser får `cancelled_at = entry_time`, `cancel_cause = 'block'` i 0012; en ekstra CHECK `vouchers_expires_after_issue`.
- Ikke committet (hører til story-branchen).

### Åpne punkter
Ingen nye. (Punktet «implementer story 4.3» er lukket.)

## 2026-11-24 kl. 19:13 — Lisa Larsen

### Oppgave
Implementere Story 4.3 (Voucher for plasser) i en ny `bmad-build`-økt, fra spec-en som sto `ready-for-dev`.

### Plan
- Spec: [`spec-4-3-give-up-seats-for-a-voucher.md`](../../.docs/implementation-artifacts/spec-4-3-give-up-seats-for-a-voucher.md) (nå `done`, med `## Review Triage Log`).
- Plan-endringene committet først (`f2de491`) som baseline; spec og `sprint-status.yaml` satt `in-progress`.
- Implementering ved en subagent (se seksjonen kl. 18:40), deretter diff-sjekk mot oppgaver og I/O-matrise.
- Review med tre parallelle lag (Blind Hunter, Edge Case Hunter, Verification Gap), triage, rettinger via samme subagent, full verifisering.

### Resultat
- Commit `831d576` på ny gren `story/4-3-give-up-seats-for-a-voucher` (ikke pushet, ingen PR). Story 4.3 står `review` i `sprint-status.yaml`.
- Første testkjøring ble stoppet av Claude Code pga. lite minne; Docker-containerne brukte bare ~380 MB (tømte page cache i Docker-VM-en, liten gevinst). Ny kjøring etter rettingene: 464 API-tester og 176 e2e-tester grønne, `npm --prefix frontend run build` rent.
- Walkthrough (`bmad-walkthrough`): compose-stakken bygget på nytt med 4.3 (migrasjon 0012 kjørt), Lisa prøvde voucher-flyten på eksempelbookingen G6VPY356. Etter ønske fra Lisa er «Move seats» og «Give up seats for a voucher» nå valgknapper side om side (plassvelgerens utseende, blå ved hover/trykk), commit `076208c`; deretter endret til blå primærknapper (som «Book seats») fordi hover-farge ikke synes ved Tab; e2e `test_fr25_manage.py`, `test_fr26_move.py`, `test_fr27_voucher.py` 12 passed.
- Review: 19 funn — 6 rettet (voucher-siden viser kansellert booking med forklaring; `booking_cancelled` leser bookingen på nytt; ny e2e-test for avvisninger og kansellert tilstand; docstring i `services/voucher.py`, kommentar i migrasjon 0012 og ordlyd i sensorveiledningen), 1 utsatt til `deferred-work.md` (29. feb-regelen i `GiveUpSeats.js` `lastValidDate` er ikke testet), 12 avvist med begrunnelse i spec-ens triage-logg.

### Åpne punkter
- Kansellert Manage-side sier alltid «You gave up all seats for a voucher …» og «Seats given up»; når kanselleringer fra stedet kommer (FR-42, block/overbooking), må teksten avhenge av `cancel_cause` (som da må med i Manage-lesingen).
- «Valid until» i voucher-steget regnes i nettleseren (29. feb → 28. feb) og er ikke testet; vurder å hente `last_valid_date` fra API-et (`deferred-work.md`).
- `.docs/sensorveiledning-kravsporing.md` rad 3 sier fortsatt «536 tester» (2026-11-21); nå 464 API + 176 e2e.
- Manuell gjennomgang av voucher-flyten i nettleseren (`bmad-walkthrough`) før Story 4.3 settes `done`.
