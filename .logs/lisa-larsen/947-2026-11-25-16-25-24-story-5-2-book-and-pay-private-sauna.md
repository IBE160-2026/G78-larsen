# Story 5.2: Book and pay for a private sauna

## 2026-11-25 kl. 16:25 — Lisa Larsen

### Oppgave
Starte Story 5.2 (bestille og betale en privat badstue) med `bmad-build`. Økten stoppet etter godkjent spec ("Godkjenn og stopp"); implementeringen tas i en ny `bmad-build`-økt.

### Plan
- `bmad-build` steg 1–2: lastet `epic-5-context.md`, spec 5.1 og Story 5.2 i epics.md, undersøkte Seat-flyten (`services/booking.py`, `db/__init__.py:run`, `api/schemas.py`, `services/voucher.py`, `services/manage.py`, `db/booking_list.py`, frontend `Review`/`Details`/`draft.js`).
- Spec: [spec-5-2-book-and-pay-for-a-private-sauna.md](../../.docs/implementation-artifacts/spec-5-2-book-and-pay-for-a-private-sauna.md)

### Resultat
- Ny branch `story/5-2-book-and-pay-private-sauna` fra `f64b83c` (tar med loggcommiten for 5.1).
- Spec skrevet og godkjent, status `ready-for-dev`, route `dispatch` (ukommittert i arbeidskopien).
- Lisas beslutninger (i specens frosne blokk):
  - `content/terms-whole.json` får endelig FR-33-tekst nå: "A booking for a fixed date cannot be withdrawn." / "Up to 72 hours before the session starts, you can cancel for a refund or a voucher, or move the booking to another session." / "If Saunalöyly cancels your session, you choose a refund or a voucher."
  - Før 5.3 viser Manage-siden en hel-badstue-booking uten handlinger; Seat-endepunktene for flytt/voucher avviser den med `404 not_found`.
  - Specen beholdes hel (ca. 3000 tokens).
  - Subagenter godkjent for implementering og review.
- Valgt i specen: `sauna_unavailable` mappes per handling via en overstyring i `db.run` (globalt `MAP` uendret); nye ruter `/private-sauna/details` og `/private-sauna/review` med de eksisterende komponentene; `BookingIn` diskriminert på `kind` med `'seats'` som standard.

### Åpne punkter
- Implementere Story 5.2 etter specen (ny `bmad-build`-økt starter på steg 3).
- Føre terms-whole-teksten inn i EXPERIENCE.md ("Private sauna wording") under implementeringen.

## 2026-11-25 kl. 17:19 — Lisa Larsen

### Oppgave
Implementere Story 5.2 etter den godkjente specen (subagent i `bmad-build`, steg 3): booke og betale en Private sauna.

### Plan
- Spec: [spec-5-2-book-and-pay-for-a-private-sauna.md](../../.docs/implementation-artifacts/spec-5-2-book-and-pay-for-a-private-sauna.md); kontekst `epic-5-context.md`, Story 5.2 i `epics.md`, ARCHITECTURE-SPINE (AD-9, 12, 13, 16, 23, 24, 25, 30).
- Backend først (db, services, api), så tester, så frontend, så e2e og docs.

### Resultat
- **Backend:** `services.whole.create` (samme rekkefølge som Seat-flyten: hash med `kind`/`sauna_id`, kortdel fra ulåst pris, `charge()`, `lock_windows`, nøkkel, `outside_horizon`, `deadline_passed`, pris på nytt, Booking via `services.reference`, `whole_bookings`-rad, Voucher og `payments`, Manage-token, e-post, nøkkel). `db.run(..., refusals=...)` mapper `whole_bookable`, `booked_within_capacity` og `(window_id, sauna_id)`-nøkkelen til `409 sauna_unavailable` bare for denne handlingen; globalt `MAP` uendret. `BookingIn` og `VoucherQuoteIn` er diskriminerte unioner på `kind` (tag `kind=…` filtreres bort fra `fields`). Én serializer med `kind`/`sauna`; e-post med «Sauna: {navn}» og `content/terms-whole.json`; Voucher-quote mot `whole_price_ore`; bookinglisten og Manage-lesingen har `kind`/`sauna`; Seat-endringene svarer `404 not_found` for en hel booking. Seed-eposten leser tidssonen fra riktig felt.
- **Frontend:** `lib/draft.js` med slot, ny `lib/flows.js`, rutene `/private-sauna/details` og `/private-sauna/review`, Details/Review/Confirmation per flyt/kind, Continue i Private sauna-railen (åpner sesjon, leser `?date=`), Notice for `sauna_unavailable` med «Choose another sauna or session», Manage uten handlinger for hel booking, badstuenavn i Seats-kolonnen i bookinglisten, `sauna_unavailable` i `lib/api.js`.
- **Tester:** ny `tests/test_fr29_whole_booking.py` (happy, e-post, ingen Hold, B7, tatt/blokkert/fyller ikke/uten pris, rekkefølge, C1 ×100, gjentak/`invalid_key`, input-tabell, Voucher delvis/hel, bookingliste, Manage). AD-25-walk utvidet; slice-oppføringer gjenopprettet i `test_fr14_retry.py`, `test_fr20_access.py`, `test_fr2_input.py`. e2e: Kajo med tastatur + axe, `sauna_unavailable` på Review, Continue uten valg (`test_fr30`), og personvern-sider for den nye flyten (`test_fr21`).
- **Docs:** `content/terms-whole.json`, EXPERIENCE.md «Private sauna wording», README.
- **Verifisert:** `uv run pytest -x -q tests --ignore=tests/e2e` → 610 passert. `npm --prefix frontend run build` → ok. e2e: stoppet av Claude Code ved ca. 88 % pga. lite minne (172 passert, 0 feil før stopp); `booking_e2e`-stacken ble tatt ned etterpå.
- Ingenting committet.
- Review-runde: Sauna-cellen i bookinglisten uten `num`-klasse, README-statusdato 2026-11-25, og tre nye e2e-tester i `test_fr30_private_sauna.py` (Manage-side og bookingliste for hel booking, flytt/gi opp er ikke tilgjengelig, Voucher på Private sauna-Review). `uv run pytest tests/e2e/test_fr30_private_sauna.py` → 10 passert.

### Åpne punkter
- Hele e2e-laget er ikke kjørt i ett etter endringene (bare `test_fr30` alene, 10 passert); `test_fr21`-tilleggene er kjørt før stoppet.
- Kodereview av Story 5.2 er ikke kjørt.

## 2026-11-25 kl. 18:04 — Lisa Larsen

### Oppgave
Fullføre Story 5.2 med `bmad-build` fra specen som lå ukommittert på `story/5-2-book-and-pay-private-sauna`: implementering (steg 3), review (steg 4) og avslutning (steg 5).

### Plan
- Spec: [spec-5-2-book-and-pay-for-a-private-sauna.md](../../.docs/implementation-artifacts/spec-5-2-book-and-pay-for-a-private-sauna.md) (`ready-for-dev` → `done`); Review Triage Log står i specen.
- Implementering i subagent; selv lest hele diffen mot oppgavene og I/O-matrisen, så tre review-lag (blind, edge case, verification gap), triage, rettelser i samme subagent, full verifisering.

### Resultat
- Selv rettet: e2e-testen for tatt badstue brukte `label[for=terms]` (finnes ikke; avkrysningsboksen ligger inne i labelen) → `label.terms-check`. README fikk «Prøv å booke en Private sauna».
- Review: 23 funn. 5 rettet (badstuenavn uten `num`-klasse i bookinglisten, README-statusdato, tre e2e-tester: bookinglistecelle, Manage-side og flytt/gi opp for hel booking, Voucher i Private sauna-Review), 1 utsatt til `deferred-work.md` (gjenoppretting av valgt par ved Back), 17 avvist med begrunnelse i specens Review Triage Log.
- Verifisert: `uv run pytest -x -q tests --ignore=tests/e2e` → 610 passert; `npm --prefix frontend run build` → ok; `uv run pytest -q tests/e2e` → **196 passert** i én kjøring; `booking_e2e`-stacken var nede etterpå.
- Spec `done`, `sprint-status.yaml` 5-2 → `review`. Commit `7da6447` (feat: book and pay for a Private sauna (Story 5.2)). Ikke pushet, ingen PR.
- Lukket i `issues.md`: hele e2e-laget og kodereview for Story 5.2.
- Senere samme kveld: Lisa testet i nettleseren (ok); grenen pushet og PR #22 opprettet (https://github.com/IBE160-2026/G78-larsen/pull/22). `feat/terms-privacy-back` ligger oppå denne grenen og merges etter.

### Åpne punkter
- `.docs/sensorveiledning-kravsporing.md` rad 2 sier fortsatt «FR-29 og videre er ikke levert»; før inn FR-29/FR-30 (Story 5.1 og 5.2) med testfilene.
- Utsatt fra review: positiv e2e-sjekk av at Back fra Private sauna-Details velger samme badstue og økt igjen (`deferred-work.md`).
