# Story 5.3 — kansellere en Private sauna

## 2026-11-26 kl. 14:20 — Lisa Larsen

### Oppgave
Starte neste story i Epic 5: 5.3 «Cancel or move a Private sauna». Lisa valgte å dele storyen og ta kanselleringen først, og å godkjenne specen og stoppe før implementering.

### Plan
- `bmad-build` steg 1–2 (avklaring og plan), sjekkpunkt 1, og så «Godkjenn og stopp».
- Epic-5-konteksten var utdatert (planleggingsdokumentene var nyere) og ble kompilert på nytt av en subagent.
- Scope-sjekk: kansellere og flytte kan leveres hver for seg. Lisa valgte å dele dem: kansellering nå, flytting som egen spec under samme story.
- Spec: [`spec-5-3-cancel-a-private-sauna.md`](../../.docs/implementation-artifacts/spec-5-3-cancel-a-private-sauna.md).

### Resultat
- Ny gren `feat/5-3-cancel-private-sauna`, laget fra `main` (`9681d30`).
- `.docs/implementation-artifacts/epic-5-context.md` er kompilert på nytt med detaljer for FR-33: Cutoff, refund og voucher, flytting, refusal-rekkefølge og e-poster.
- `.docs/implementation-artifacts/spec-5-3-cancel-a-private-sauna.md` har status `ready-for-dev` og rute `dispatch`, omtrent 2600 tokens. Lisa valgte å beholde den samlet. Den dekker:
  - `POST /api/manage/{ref}/whole/cancel` og `services.payment.refund()` (AD-31);
  - migrasjon 0014 (history-action `cancel`) og cancel-steget på Manage;
  - siden for en kansellert booking og historikklinjen i Booking list;
  - testfilene `test_fr33_whole_change.py` og e2e-testen `test_fr33_whole_cancel.py`.
- Ordlyden for kansellering av en Private sauna ble godkjent som foreslått (Lisa 2026-11-26). Den står i specens Decisions og skal føres inn i EXPERIENCE.md under implementeringen.
- `deferred-work.md` har fått en ny oppføring for Story 5.3 del 2 (flytting).
- Specen, epic-konteksten og `deferred-work.md` er ukommittert på grenen.

### Åpne punkter
- Implementer Story 5.3 del 1 (kansellering) etter den godkjente specen `spec-5-3-cancel-a-private-sauna.md` (`ready-for-dev`) i en ny `bmad-build`-økt.
- Story 5.3 del 2: flytting av en Private sauna (`…/whole/move`, `price_differs`, flytteliste med `ignore_booking`) trenger egen spec. Den står i `deferred-work.md`.
