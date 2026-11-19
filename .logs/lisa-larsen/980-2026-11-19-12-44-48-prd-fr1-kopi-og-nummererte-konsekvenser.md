# PRD: FR-1 uten kopitekst, nummererte konsekvenser

## 2026-11-19 kl. 12:44 — Lisa Larsen

### Oppgave
Tilbakemelding på PRD-en (medium): FR-1 blandet krav med ferdig tekst, og FR-39 og FR-40 hadde så mange konsekvenser at én story ble for stor og det var uklart når FR-en var ferdig. Forslaget var å gi konsekvensene egne ID-er eller dele FR-ene, og å flytte kopitekst til UX-dokumentet.

### Plan
- Nummerere konsekvensene (FR-40.1, FR-40.2 …) i stedet for å dele FR-ene i a/b/c, så FR-numrene som arkitekturen, addendum K og testene viser til, står stille.
- Flytte den ferdige landingsteksten fra FR-1 til `EXPERIENCE.md`, og la FR-1 bare si hva siden skal inneholde. Teksten ble hentet ordrett fra mocken `directions-3.html`, som Lisa har godkjent.

### Resultat
- `prd.md`, FR-1: Har nå åtte nummererte konsekvenser (FR-1.1–FR-1.8) som beskriver innholdet: kravet til beskrivelsen (ingen antall badstuer, ikke «shared»), hva «Before you come» skal dekke, og at kontaktdetaljene ikke kan nå noen. All ordrett tekst er fjernet, og FR-1 viser til `EXPERIENCE.md`.
- `prd.md`, §0: En linje om nummererte konsekvenser og om at ferdig sidetekst ligger i UX-dokumentene.
- `appendix-fr-34-51.md`: FR-39.1–FR-39.7 og FR-40.1–FR-40.11 er nummerert. Selve teksten er uendret.
- `EXPERIENCE.md`, Voice and Tone: Ny tabell «Landing copy, verbatim» med beskrivelsen, alle punktene i «Before you come» og adressen og kontaktinfoen. Den erstatter avsnittet som viste til FR-1.
- Committet i `9664b81`.

### Åpne punkter
Ingen.
