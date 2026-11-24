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
