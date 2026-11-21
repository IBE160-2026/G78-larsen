# Story 2.4 del A: Core done — de automatiske sjekkene

## 2026-11-21 kl. 10:32 — Lisa Larsen

### Oppgave
Fortsette med Story 2.4 («Core done: the examiner can run, sign in and check everything») gjennom `bmad-build`.

### Plan
- Storyen var for stor for én spec. Lisa valgte å splitte den:
  - **del A** er de automatiske sjekkene, som bygges nå;
  - **del B** er README, fersk klone, manuelle tilgjengelighetssjekker og Core done-loggen. Den er ført i `.docs/implementation-artifacts/deferred-work.md`.
- Spec: [spec-2-4-core-done-automated-checks.md](../../.docs/implementation-artifacts/spec-2-4-core-done-automated-checks.md). Den er ca. 1900 tokens; Lisa valgte å beholde den hel og godkjente den.
- Implementert direkte. Gjennomgang med tre reviewer-subagenter (blind hunter, edge case hunter og verification gap), etter Lisas ja.

### Resultat
- Ny `tests/e2e/test_fr23_accessibility.py`: axe og ingen horisontal rulling (1024/1366/1920) på hver Core-side i 16 tilstander, blant annet:
  - feiloppsummeringer;
  - avvisningsmelding på Review;
  - utsolgt økt på Book seats og Booking list;
  - siden som ikke finnes.

  1.4.10 Reflow er låst som eneste kjente avvik.
- Ny `tests/e2e/test_fr23_keyboard_and_zoom.py`:
  - tabulatorrekkefølgen på Book seats: dato, kalender, plasser og økt før «Continue booking»;
  - ariaSnapshot av øktlisten («1 seat left, not enough for 2», «Sold out»);
  - bookingflyten med bare tastatur i 200 % zoom (1366×768 og 1920×1080), med seks skjermbilder i `test-results/zoom/` (git-ignorert).
- `tests/e2e/test_fr21_privacy.py`:
  - anonyme besøk på `/admin`, `/admin/bookings` og `/admin/outbox` går til Sign-in;
  - Sign-in, Booking list og Outbox har én informasjonskapsel, bare egen opprinnelse og ett stilark;
  - logg-test: etter en booking, en avvist booking, en avvist og en godkjent innlogging og en utlogging finnes verken passord, tokener, engangsnøkler eller forespørselsinnhold i compose-loggene.
- `tests/test_dr3_assets.py`: hver bilde- og fontrad i `ASSETS.md` peker på en fil som finnes (med eksakt store og små bokstaver) og har en kildelenke.
- Ingen produktkode endret: ingen sjekk avdekket feil.
- Gjennomgangen ga 9 rettinger og 9 avviste funn (se Review Triage Log i spec-en). Blant rettingene var en ustabil zoom-test: fokus forsvant når øktene ble hentet på nytt. Den venter nå på svaret fra `/api/windows`.
- `uv run pytest -q`: 536 passerte (etter rettingene). `npm --prefix frontend run build`: ok.
- Commit `d3fde60` (lokalt, ikke pushet). Sprint-status: Story 2.4 står fortsatt som `in-progress` til del B er gjort.
- Lukket: «tastaturrekkefølge på Book seats må testes mot WCAG 2.4.3». Den er nå automatisert; del B ser den i tillegg manuelt.

### Åpne punkter
- Story 2.4 del B gjenstår:
  - README i storyens rekkefølge, med sikkerhetsseksjon og «Not delivered»;
  - fersk klone fulgt ord for ord;
  - `tests/manual/core-accessibility.md` med de manuelle kontrollene (tastatur, 200 % zoom, tabulatorrekkefølge, NVDA);
  - «Core done» i sesjonsloggen.
- Til den manuelle zoom-sjekken: i 200 % zoom (683 px bredt) brytes e-postadressen på Review midt i ordet («zoom@example.c / om»), og venstre kolonne er stort sett tom. Vurder det mot WCAG 1.4.4 og 1.4.10.
- Mulig samme ustabilitet i `test_fr02_book_seats.py:139` og `test_fr05_book_and_pay.py:57`: de venter på `networkidle` etter at antall plasser endres. Ført i `deferred-work.md`.
