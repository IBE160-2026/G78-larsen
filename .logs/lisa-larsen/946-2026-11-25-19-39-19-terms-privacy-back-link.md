# Terms-privacy-back-link

## 2026-11-25 kl. 19:39 — Lisa Larsen

### Oppgave
Lisa spurte om Terms og Privacy notice burde ha en tilbakeknapp, siden de nås fra ulike steg. Anbefalingen var en «Back»-lenke som går tilbake i historikken fra en side på nettstedet, og ellers til landingssiden. Lisa ba om å sette den i gang.

### Plan
- Egen gren `feat/terms-privacy-back` fra `main` (Story 5.2 ligger ikke på main ennå).
- `bmad-build`, oneshot-rute: [spec-terms-privacy-back-link.md](../../.docs/implementation-artifacts/spec-terms-privacy-back-link.md) (med Review Triage Log).

### Resultat
- Ny `frontend/components/BackLink.js` (Text link til `/`; fra en side på nettstedet kalles `router.back()`), `frontend/lib/nav.js` (reserve uten Navigation API, notert av `FocusMover`), Back under h1 på `/terms` og `/privacy`, `LEGAL_PAGE.back` i `lib/copy.js`.
- EXPERIENCE.md («Back»-raden og Terms/Privacy-oppsettet) og mockupene `key-terms.html`/`key-privacy.html` oppdatert.
- Tester i `tests/e2e/test_fr22_terms_privacy_a11y.py`: tabulatorrekkefølge, direkte åpning → landingssiden, Review → Terms → Privacy → Back → Back til Review med alt bevart og fokus på h1, uten JavaScript, og reserven uten Navigation API. `test_fr22` 33 passert; fr01, fr05, fr21, fr23 ×2 og stack routing 79 passert; frontend bygger.
- Review (Blind Hunter): 10 funn, 6 rettet, 4 avvist.
- Commit `6bbd7e8` på `feat/terms-privacy-back`. Ikke pushet.
- Etterpå flyttet (rebase) oppå `story/5-2-book-and-pay-private-sauna`, slik at Back og Private sauna-bookingen kan prøves sammen; ny commit `6cd99b4`. Konflikt bare i `issues.md` (begge linjene beholdt). `test_fr22` + `test_fr30` 43 passert; stacken bygd på nytt. Lisa testet i nettleseren: ok. Grenen må merges etter Story 5.2.

### Åpne punkter
- Kjent begrensning i nettlesere uten Navigation API (eldre Firefox/Safari): etter at gjesten har navigert inne på nettstedet, går Back tilbake i historikken også når siden ble nådd med nettleserens egen tilbake- eller fremknapp.
