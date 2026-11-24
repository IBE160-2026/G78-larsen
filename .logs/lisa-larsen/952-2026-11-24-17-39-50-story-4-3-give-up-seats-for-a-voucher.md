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
