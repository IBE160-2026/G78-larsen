# Story 5.1: A Guest sees which saunas can be booked whole

## 2026-11-25 kl. 01:05 — Lisa Larsen

### Oppgave
Bygge story 5-1 med `bmad-build`. Whole-sauna-prisene skulle settes ut fra snittprisen i Oslo-området og badstuenes størrelse, og Badstu 1 og 4 skulle kunne bookes hele. De to ventende Epic 5-avgjørelsene (feilmeldingen etter `sauna_unavailable` på Review i 5.2 og plasseringsvisningen i 5.4) skulle løses uten å spørre noen. Underveis ba Lisa om at arbeidet ble gjort med subagenter, så kontekstvinduet ikke ble for stort.

### Plan
- Kompilerte [epic-5-context.md](../../.docs/implementation-artifacts/epic-5-context.md) og skrev specen [spec-5-1](../../.docs/implementation-artifacts/spec-5-1-a-guest-sees-which-saunas-can-be-booked-whole.md) på branch `story/5-1-private-sauna-listing`.
- Én subagent implementerte, tre subagenter reviewet (Blind Hunter, Edge Case Hunter, Verification Gap), og deretter fulgte patcher og verifisering.

### Resultat
- **Avgjørelser** (EXPERIENCE.md, «Private sauna wording»; Open Item 27 lukket):
  - Rauha koster NOK 1850 og Lumo NOK 3950. Grunnlaget er Oslo-snittet, NOK 1 837 for omtrent 7 plasser, dvs. NOK 262 per plass, ganget med antall plasser og rundet til nærmeste 50.
  - Löyly og Kajo kan ikke bookes hele.
  - Etter `sauna_unavailable` (5.2) står det «This sauna can no longer be booked for this session. You have not been charged.», med lenken «Choose another sauna or session».
  - Plasseringen (5.4) vises som tabellen «Saunas» med kolonnene «Sauna» og «Seats counted», og cellene «7 of 7», «Booked whole · {ref}», «Blocked» og «Private sauna only».
- **Kode** (commit `b8afac8`):
  - Migrering `0013_whole_sauna_bookings.sql` legger til `kind` og `sauna_id`, paringen med `whole_pairing`, `whole_bookable()`, `cutoff_whole` og `whole_price_ore`.
  - Seed-prisene er lagt inn, og `GET /api/private-saunas` er nytt. Slice-endepunktet `/api/admin/whole-bookings` er fjernet, og testene bruker `raw_whole`.
  - Landing har fått Private sauna-lenken, prisene og gruppesetningen, og siden `/private-sauna` er ny.
  - De nye testene er `test_fr29_whole_sauna.py`, `test_fr29_whole_store.py` og `tests/e2e/test_fr30_private_sauna.py`.
- **Review:** 20 funn. 11 ble rettet, 5 avvist og 4 utsatt til `deferred-work.md`. Triageloggen står i specen.
- **Verifisering:**
  - API-laget: 561 passed.
  - Full e2e: 186 passed, 1 failed og 1 error, begge i `test_fr30`. Begge er rettet, og `test_fr30` alene gir 5 passed.
  - En ny full e2e-kjøring ble stoppet av Claude Code fordi maskinen hadde lite minne, så den er ikke bekreftet.
- **Lukket i issues.md:** `sauna_unavailable`-meldingen og plasseringsvisningen (5.4) er avgjort.
- Specen ble på omtrent 2500 tokens, over anbefalt 1600; den ble holdt samlet fordi storyen er definert slik i epics.
- Ikke pushet, og ingen PR er opprettet.

### Åpne punkter
- Kjør `uv run pytest tests/e2e` på nytt når det er nok minne. Hele e2e-laget er ikke bekreftet grønt etter rettingene i `test_fr30`.
- Story 5.2: e2e-flyten må booke Lumo, ikke Kajo, fordi Kajo ikke tilbys hel i seeden. epics.md sier fortsatt Kajo.
- Story 5.2: gjenopprett whole-dekningen i `test_fr14_retry`, `test_fr20_access` og `test_fr2_input` mot `POST /api/bookings` med `kind = 'whole'` (deferred-work).
- Story 5.3: `seat_guest_refund_forbidden` må begrenses til `kind = 'seats'`, og `whole_bookable(..., ignore_booking)` må se bort fra den ignorerte raden også i `room_ahead` (deferred-work).
- e2e-test der badstuene har ulike ledige sesjoner, for omgrupperingen på `/private-sauna` (deferred-work).

## 2026-11-25 kl. 01:15 — Lisa Larsen

### Oppgave
Endre punktet om at e2e-flyten i Story 5.2 må booke Lumo, siden epics.md fortsatt sa Kajo.

### Plan
- Rette e2e-kriteriet i Story 5.2 i epics.md og lukke punktet i issues.md.

### Resultat
- `.docs/planning-artifacts/epics.md` Story 5.2: «a Guest books Lumo for a session with the keyboard alone (Kajo is not offered whole in the seed, Lisa 2026-11-24)». De andre Kajo-eksemplene i Epic 5 er katalogtester som setter egne priser i testfixturen, og de er ikke endret.
- `epic-5-context.md` er oppdatert, og punktet i issues.md er lukket.

### Åpne punkter
Ingen.

## 2026-11-25 kl. 01:40 — Lisa Larsen

### Oppgave
Lisa presiserte at alle badstuer skal være åpne for både helbadstu-booking og enkeltseter, hvis ikke annet er markert. Det erstatter valget fra 2026-11-24 om at bare Badstu 1 og 4 kan bookes hele.

### Plan
- Rette dokumentene selv (EXPERIENCE.md, epics.md, epic-5-context.md og specens Decisions).
- La implementasjonsagenten rette seed, tester og README.

### Resultat
- Prisene er Oslo-snittet NOK 262 per plass ganget med antall plasser, rundet til nærmeste 50: Rauha NOK 1850, Löyly NOK 2600, Kajo NOK 3150 og Lumo NOK 3950.
- En badstue tilbys ikke hel bare når den har `bookable_whole = false` eller mangler pris.
- epics.md 5.2 booker Kajo i e2e igjen; endringen til Lumo fra forrige seksjon er tilbakeført.
- En eksisterende database får prisene for Löyly og Kajo ved neste oppstart, fordi seeden fyller felt som er NULL.
- Tester: API-laget 561 passed. e2e-filene `test_fr30_private_sauna.py` og `test_fr01_landing.py` ga 19 passed.

### Åpne punkter
- Hele e2e-laget må fortsatt kjøres, slik punktet i issues.md allerede sier.

## 2026-11-25 kl. 01:55 — Lisa Larsen

### Oppgave
Begrense regelen som forbyr refusjon ved gjestekansellering til setebookinger, så en privat badstu kan refunderes (FR-33, AD-31). Før var dette satt til Story 5.3.

### Plan
- Rette CHECK-en i migrering 0013, som ikke er merget ennå, i stedet for å vente til 5.3.

### Resultat
- `migrations/0013_whole_sauna_bookings.sql`: `seat_guest_refund_forbidden` er gjenopprettet med samme navn som `CHECK (kind <> 'seats' OR NOT (cancel_cause = 'guest' AND cancel_remedy = 'refund'))`.
- Ny test, `test_fr29_whole_store.py::test_a_whole_sauna_booking_may_be_cancelled_by_the_guest_with_a_refund`:
  - En helbadstu-booking som avbestilles med refusjon, går gjennom.
  - En setebooking med samme verdier avvises fortsatt.
- Tester: `test_fr29_whole_store`, `test_fr27_voucher_for_seats` og `test_dr4_migrations` ga 69 passed.
- Punktet er lukket i deferred-work.md og issues.md. Punktet om `ignore_booking` står fortsatt.

### Åpne punkter
Ingen nye.

## 2026-11-25 kl. 09:01 — Lisa Larsen

### Oppgave
Lisa ville at «Book seats» og «Book private sauna» på landingssiden skulle se like ut. Hun fikk fem forslag og deretter fem blå varianter av forslag E, og valgte E1 uten pil. Prisen «NOK 250 per seat, incl. VAT» blir stående i railen; Lisa trakk tilbake ønsket om å fjerne den.

### Plan
- Forslagene ble vist som artifact: https://claude.ai/artifact/TuGZHGyrs3fNAjUbk39XGf
- Bytte tekstlenken «Private sauna» med to like Booking choices, og rette UX-DR41 i dokumentene.

### Resultat
- Ny komponent `frontend/components/BookingChoice.js` og `LANDING_CHOICES` i `frontend/lib/copy.js`: «Book seats» / «Share a sauna with others» og «Book private sauna» / «A whole sauna for your group». Primærknappens blå fyll og kant, venstrestilt, uten pil.
- Lenkens navn er bare handlingen. Forklaringen er `aria-hidden` og leses som beskrivelse via `aria-describedby`. En første versjon med `aria-label` feilet axe (`label-content-name-mismatch`).
- `frontend/app/page.js` og `frontend/app/styles.css`: `.rail-private` er erstattet av `.booking-choices` og `.booking-choice`. Landingssiden har nå ingen `.button-primary`.
- Dokumenter rettet: UX-DR41 og akseptkriteriet for Story 5.1 i `epics.md`, `EXPERIENCE.md` (tekstabell og §4.9-raden), `DESIGN.md` (Private sauna entry), `epic-5-context.md` og en ny merknad i spec-5-1.
- Tester rettet: `test_fr01_landing.py` og `test_fr30_private_sauna.py`. De ga 19 passed etter at frontend ble bygget på nytt.
- Kodeendringene er ikke committet.

### Åpne punkter
Ingen.

## 2026-11-25 kl. 09:06 — Lisa Larsen

### Oppgave
Lisa syntes knappene på landingssiden fikk for lang tekst. De skulle bare si «Book seats» og «Book private sauna», og være like store.

### Plan
- Fjerne forklaringslinjene fra Booking choice og gi begge knappene samme bredde og høyde.

### Resultat
- `BookingChoice.js` har bare handlingsteksten. Forklaringene og `aria-describedby` er fjernet, og `seatsNote` og `privateNote` er tatt ut av `LANDING_CHOICES`.
- `.booking-choice` har full bredde i railen og samme høyde som primærknappen (minst 48 px). Teksten er venstrestilt. `.booking-choice-note` er fjernet.
- `test_fr01_landing.py` sjekker nå at knappene har samme bredde og høyde. `epics.md`, `EXPERIENCE.md`, `DESIGN.md` og spec-5-1 er rettet tilsvarende.
- Tester: `test_fr01_landing` og `test_fr30_private_sauna` ga 19 passed etter at frontend ble bygget på nytt.
- Kodeendringene er ikke committet.

### Åpne punkter
Ingen.

## 2026-11-25 kl. 09:09 — Lisa Larsen

### Oppgave
Midtstille teksten i Booking choice-knappene på landingssiden.

### Plan
- Midtstille teksten i `.booking-choice` og rette beskrivelsen i dokumentene.

### Resultat
- `.booking-choice` har nå `justify-content: center` og `text-align: center`, som primærknappen. Kommentaren i `BookingChoice.js`, `DESIGN.md`, `epics.md` og spec-5-1 er rettet.
- Tester: `test_fr01_landing` ga 14 passed etter at frontend ble bygget på nytt.
- Kodeendringene er ikke committet.

### Åpne punkter
Ingen.

## 2026-11-25 kl. 09:10 — Lisa Larsen

### Oppgave
Committe endringen av knappene på landingssiden.

### Plan
- Committe kode, tester og dokumenter på `story/5-1-private-sauna-listing`.

### Resultat
- Commit `7bdec8d` «FR-1, FR-30: Book seats and Book private sauna as two equal buttons on Landing» endret 11 filer. Den er ikke pushet.

### Åpne punkter
Ingen.

## 2026-11-25 kl. 09:17 — Lisa Larsen

### Oppgave
På Private sauna-siden skulle kolonnene i badstuvalgene få mer plass mellom prisen og «x free sessions», og mindre avstand mellom badstuas navn og «Holds x».

### Plan
- Endre kolonnene i `.session-row.sauna-option`, slik at den ledige plassen havner foran «x free sessions».

### Resultat
- `frontend/app/styles.css`: kolonnene er nå `32px minmax(64px, max-content) minmax(72px, max-content) max-content minmax(0, 1fr)`. Navnet har ikke lenger `padding-right`.
- Målt ved 1366 px: avstanden fra navn til «Holds» gikk fra ca. 60 px til ca. 26 px. Avstanden fra prisen til «free sessions» gikk fra ca. 60 px til ca. 90 px.
- Tester: `test_fr30_private_sauna` ga 5 passed.
- Ikke committet.

### Åpne punkter
Ingen.

## 2026-11-25 kl. 09:21 — Lisa Larsen

### Oppgave
I «3. Choose a sauna» (visningen «Show by session») skulle «x free sessions» fjernes, fordi tallet kan forvirre når økten alt er valgt. Tabellen skulle tilpasses.

### Plan
- Gi `SaunaOptions` en `showFree`-parameter, slå den av i steg 3 og gi radene der en egen kolonnemal.

### Resultat
- `frontend/components/PrivateSauna.js`: steg 3 har `showFree={false}`. Raden har klassen `no-free`, og `aria-label` er «Navn, Holds x, NOK y».
- `frontend/app/styles.css`: `.sauna-option.no-free` bruker kolonnene `32px minmax(64px, max-content) minmax(72px, max-content) minmax(0, 1fr)`. Navn, størrelse og pris står i samme kolonner som i steg 2.
- `EXPERIENCE.md` (Sauna option) og `test_fr30_private_sauna.py` er oppdatert. Tester: 5 passed.
- Ikke committet, sammen med kolonneendringen fra forrige seksjon.

### Åpne punkter
Ingen.

## 2026-11-25 kl. 09:30 — Lisa Larsen

### Oppgave
Lisa ba om fem designforslag for Private sauna-siden der hver badstu vises med bilde og en kort beskrivelse.

### Plan
- Lage forslagene som en artifact med de fire badstubildene som allerede ligger i `frontend/public/images` (oppført i `ASSETS.md`), i høyre kolonne på `/private-sauna` med ekte bredde (ca. 490 px).

### Resultat
- Artifact: https://claude.ai/artifact/7SL79i3ixvUVXiMw1i3BFE
- Forslagene er A rader med lite bilde, B 2×2-kort, C brede bildebannere, D dagens rader med forhåndsvisning av valgt badstu, og E stort bilde ved siden av teksten.
- Beskrivelsene er utkast og ikke bekreftet av Lisa. Ingen kode er endret.

### Åpne punkter
- Lisa må velge et forslag og godkjenne beskrivelsene før bildene bygges inn på Private sauna-siden.

## 2026-11-25 kl. 09:36 — Lisa Larsen

### Oppgave
Lisa ba om fem nye forslag der de ledige øktene står som knapper ved hver badstu, så steg 3 kanskje ikke trengs. Overskriften skal være «Choose a sauna and a session».

### Plan
- Lage en ny artifact med de samme bildene og beskrivelsene. Badstu og økt velges med ett klikk.

### Resultat
- Artifact: https://claude.ai/artifact/KRErnbSV2aYiQr6t1zC723
- Forslagene er F rader med lite bilde og øktknapper, G 2×2-kort med øktrutenett, H brede bannere med start–slutt-knapper, I stort bilde med øktrutenett, og J en tabell med badstuer mot økter.
- Overskriften er «2. Choose a sauna and a session». Opptatte økter er eksempeldata. Ingen kode er endret.

### Åpne punkter
- Lisa må velge forslag. Hun må også bestemme om «Show by session» skal beholdes når badstu og økt velges i ett steg.

## 2026-11-25 kl. 09:42 — Lisa Larsen

### Oppgave
Lisa valgte forslag H (brede bannere med øktknapper) for «Show by sauna». Hun ba om fem lignende forslag med bilder og tekst for «Show by session».

### Plan
- Lage en ny artifact der økta velges først og de ledige badstuene vises i H-stil.

### Resultat
- Artifact: https://claude.ai/artifact/Bhhi9wKNAk7Zfw31zEe8Pk
- Forslagene er K øktknapper og så badstukort, L gruppert per økt med små kort, M trekkspill per økt, N øktknapper og så badstuer med bilde ved siden av, og O tidslinje med bildeknapper og den valgte badstua stort under.
- Overskriften er «2. Choose a session and a sauna». Ingen kode er endret.

### Åpne punkter
- Lisa må velge et forslag for «Show by session». Deretter bygges H og det valgte forslaget inn, og beskrivelsene må godkjennes.

## 2026-11-25 kl. 09:55 — Lisa Larsen

### Oppgave
Lisa valgte forslag K for «Show by session». Forslag H skulle bygges for «Show by sauna» og K for «Show by session» på Private sauna-siden.

### Plan
- Skrive om `PrivateSauna.js` med badstukort (bilde, navn, størrelse, pris og beskrivelse) og øktknapper. Deretter rette tekster, CSS, tester og dokumenter.

### Resultat
- `frontend/components/PrivateSauna.js` har to nye deler:
  - `SaunaCards` (H): alle øktknappene ligger i én radiogruppe (`name=pair`), så ett klikk velger både badstu og økt. Steg 3 er borte.
  - `SessionThenSauna` (K): økter med «x saunas free», og så de ledige badstuene som valgbare kort.
- Bildene er dekorative på denne siden (`alt=""`). Beskrivelsen er kortets `aria-describedby`.
- `frontend/lib/copy.js`: `bySaunaQuestion`, `bySessionQuestion`, `sessionLegend`, `saunaLegend` og `saunasFree` er nye. `saunaQuestion`, `sessionQuestion` og `freeSessions` er fjernet fra `PRIVATE`.
- `frontend/lib/sauna-copy.js`: hver badstu har fått `description` (utkast).
- `frontend/app/styles.css`: `.private-card`, `.private-pick`, `.slot-grid`, `.cell.slot` og `.q-sub` er nye. De gamle `.sauna-option`-reglene er fjernet.
- `test_fr30_private_sauna.py` er skrevet om for H og K. `EXPERIENCE.md`, `DESIGN.md`, `epics.md` (UX-DR41 og akseptkriteriet), `epic-5-context.md` og spec-5-1 er oppdatert.
- Tester: `test_fr30` og `test_fr01` ga 19 passed. `test_fr02_book_seats` ga 18 passed.
- Ikke committet.

### Åpne punkter
- Beskrivelsene av badstuene i `sauna-copy.js` er utkast og må godkjennes av Lisa.
- Story 5.2 må bygge Continue og Review på det nye valget, der ett klikk gir badstu og økt i «Show by sauna».

## 2026-11-25 kl. 10:01 — Lisa Larsen

### Oppgave
Sjekke endringene mot product brief og PRD. Deretter skulle PRD §4.1 rettes, fordi beskrivelsen fortsatt sa «one main action», mens landingssiden nå har to like knapper.

### Plan
- Sammenligne endringene med brief, brief-addendumet, PRD FR-1, FR-30, UJ-5, §6, §7 og FR-22/23.
- Rette bare §4.1, som Lisa ba om.

### Resultat
- Sjekken: H og K samsvarer med FR-30, UJ-5 og §7 («Window → Sauna, or Sauna → Window»). De to like knappene samsvarer med brief («The guest first chooses Individual seats or Private sauna»). Fire avvik ble funnet: §4.1 «one main action», FR-1.5 «one image and one line», «löyly» uten engelsk forklaring i Kajo-beskrivelsen, og stockfoto-bildene, som nå er mer synlige.
- `prd.md` §4.1 sier nå at landingssiden tilbyr Book seats, og at Book private sauna står rett under som et likt valg når §4.9 er bygget, som i brief. FR-1.2 er uendret.
- Beslutningen er ført i addendum M.3 og i `.memlog.md`.
- Ikke committet.

### Åpne punkter
- FR-1.5 «one image and one line» mot de lengre beskrivelsene på Private sauna-siden: Lisa har ikke avgjort om beskrivelsene skal kortes ned eller om PRD-en skal utvides.
- Kajo-beskrivelsen bruker «löyly» uten engelsk forklaring (§6 Copy), og «A big stove gives soft, even heat» er ikke bekreftet.

## 2026-11-25 kl. 10:03 — Lisa Larsen

### Oppgave
FR-1.5 i PRD skulle endres, så kravet passer med de lengre beskrivelsene av badstuene på Private sauna-siden.

### Plan
- Utvide FR-1.5 og føre beslutningen i addendum M.3 og `.memlog.md`, som for §4.1.

### Resultat
- `prd.md` FR-1.5: «one image and one line» gjelder fortsatt landingssiden. På Private sauna-siden vises hver badstu med samme bilde og en beskrivelse på én eller to setninger, fordi gjesten der velger badstua (FR-30).
- Raden er lagt i addendum M.3, og linjen i `.memlog.md`. Punktet om FR-1.5 i `issues.md` er lukket.
- Ikke committet.

### Åpne punkter
Ingen nye.

## 2026-11-25 kl. 10:05 — Lisa Larsen

### Oppgave
Endre Kajo-beskrivelsen, så det ikke står «löyly» uten forklaring (PRD §6 Copy).

### Plan
- Bytte ut slutten av setningen i `sauna-copy.js`, `EXPERIENCE.md` og testen.

### Resultat
- Kajo-beskrivelsen er nå: «Kajo means a soft glow. Warm light, and a bucket and ladle for throwing water on the stones.»
- Endret i `frontend/lib/sauna-copy.js`, i `EXPERIENCE.md` (Private sauna wording) og i `test_fr30_private_sauna.py`. Testene ga 5 passed etter at frontend ble bygget på nytt.
- Ikke committet.

### Åpne punkter
- «A big stove gives soft, even heat» i Löyly-beskrivelsen er fortsatt ikke bekreftet.

## 2026-11-25 kl. 10:09 — Lisa Larsen

### Oppgave
Endre Löyly-beskrivelsen, så den ikke inneholder den ubekreftede påstanden «A big stove gives soft, even heat».

### Plan
- Bytte setningen i `sauna-copy.js`, `EXPERIENCE.md` og testen.

### Resultat
- Löyly-beskrivelsen er nå: «Löyly is the steam that rises when water meets the hot stones. A sauna for a mid-sized group.» Første setning forklarer ordet med samme formulering som beskrivelsen av anlegget på landingssiden.
- Testene ga 5 passed etter at frontend ble bygget på nytt. Punktet er lukket i `issues.md`.
- Ikke committet.

### Åpne punkter
Ingen nye.

## 2026-11-25 kl. 10:10 — Lisa Larsen

### Oppgave
Committe endringene i PRD-en og på Private sauna-siden.

### Plan
- To commits: én for PRD-endringene og én for Private sauna-siden med tilhørende dokumenter og tester.

### Resultat
- `e867ade` «PRD §4.1, FR-1.5: two equal booking choices and longer sauna descriptions» (prd.md, addendum.md og .memlog.md).
- `550e224` «FR-30: choose the Sauna and the session on photo cards (Story 5.1)» (10 filer: komponent, tekster, CSS, test og UX- og epic-dokumenter). Kolonneendringen fra tidligere i dag er erstattet av de nye kortene og er med her.
- Ikke pushet.

### Åpne punkter
Ingen nye.
