# Research: samtidighet ved booking

## 2026-10-27 kl. 15:08 — Lisa Larsen

### Oppgave
Kjøre `bmad-deep-recon` som «technical», kort, for å hjelpe PRD-en: hvordan hindre dobbeltsalg av siste plass, holde plasser i 10 minutter, og flytte plasser mellom badstuer uten at hele badstuen kan bookes midt i flyttingen. Målet er realistiske krav til ytelse og konsistens. Samtidig ble effort satt til `high` med `/effort` (lagret som standard for nye økter).

### Plan
- Plan godkjent av Lisa før kjøring: preset `quick` (2 assistenter, 5 kilder per runde, dybde 1), validation `normal`, red team av.
- Tre dimensjoner: D1 dobbeltsalg, D2 hold på 10 minutter, D3 flytting mellom badstuer.
- Assistent 1 tok D1 og ytelsestall, assistent 2 tok D2 og D3. Begge fikk bare oppgavebeskrivelsen, ingen prosjektfiler.

### Resultat
- Rapport: `.docs/planning-artifacts/research/technical-booking-concurrency-seat-holds-2026-10-27/research.md` (engelsk, status `complete`). Digester i `digests/`, prosessminne i `.memlog.md`.
- Hovedfunn: konsistenskrav kan stilles hardt og testbart (atomisk betinget UPDATE under Read Committed, Serializable med retry på 40001 som sikkerhetsnett, faste låsrekkefølger for flytting). Ytelsestall lot seg ikke kilde. PRD bør ikke ha TPS- eller latenstall, bare et lasttestmål målt på eget utstyr.
- Verifisering: sitatsjekk (mekanisk) OK, 10 av 10 markører løser seg. Lead hentet PostgreSQL-dokumentasjonen på nytt for tre sentrale sitater. Tally: 1 verifisert, 4 uverifisert. De fleste PostgreSQL-påstander er primærkilder lest av assistentene, ikke hentet på nytt av meg.
- Hoppet over fordi Lisa ba om kort: semantisk sitatsjekk med eget subagent og `doc_standards`-polering (`bmad-review` structure/prose).
- Ingenting er committet av research-mappen (ligger ukommittert under `.docs/planning-artifacts/research/`).

### Åpne punkter
- Databasemotor er ikke valgt; funnene gjelder bare PostgreSQL. SQLite (én skriver) og MySQL/InnoDB er ikke undersøkt.
- Ingen kildebelagt tall for rader per sekund ved hot-row-konflikt. Må måles i en liten spike på eget oppsett før PRD setter et lasttestmål.
- Flyten «betaling etter utløpt hold» og reelt avvik på utløpstid har ingen primærkilde. Avgjøres i arkitekturen og bevises med de parallelle testene.
- Semantisk sitatsjekk og polering av rapporten ble hoppet over; kjør ved behov.
