# Tilbakemelding på product brief

| | |
|---|---|
| **Gruppe** | G78 – G78-larsen |
| **Product brief** | `.docs/planning-artifacts/briefs/brief-booking-platform-2026-09-20/brief.md` (commit 5666cfd), lest sammen med `addendum.md` i samme mappe |
| **Tilbakemelding fra** | Faglærer i IBE160 (utarbeidet med KI-støtte) |
| **Dato** | 2026-10-06 |

## Samlet vurdering

- **Godt utgangspunkt med justeringer.** Gruppen kan gå videre og innarbeide punktene under.

**Det som er bra:**

1. Bookingreglene er usedvanlig presise: enkeltplasser fordeles på badstuer i en rekkefølge administrator bestemmer, hele badstuer kan bare bookes når ingen enkeltplasser er plassert der, og avbestillingsfristene er 12 og 72 timer. Det gjør domenet testbart, og dere skriver selv at styrken er at reglene kan testes.
2. Suksesskriterium 1–8 er konkrete scenarioer som nesten direkte kan bli automatiske tester («en gjest booker fire plasser … plassene trekkes fra kapasiteten»). Commit-historikken viser også at briefen er bearbeidet i mange små, beskrivende steg – akkurat den typen sporbarhet sensor ser etter.

**De viktigste endringene:**

1. V1 er svært stort for én person: to bookingtyper, priser med barnepris, gavekort, medlemskap, periodekort, avbestilling og verdikoder, dørkoder, fjernstyring av dører, styring av oppvarming, kalenderblokkering, justerbare regler, innlogging, sikkerhet og responsivt design. Flytt flere av disse til senere trinn.
2. Suksesskriterium 9 («beskyttet mot hacking») kan ikke testes slik det står. Erstatt det med konkrete tiltak, f.eks. hashede passord, rollebasert tilgang og validering av input, som hver kan testes.
3. Plattform og nettside skal holdes adskilt «så flere nettsider kan kobles til senere». Det er fornuftig, men ikke la forberedelser for fremtiden ta tid fra kjerneflyten i v1.

## Vanskelighetsgrad og gjennomførbarhet

### Vurdert vanskelighetsgrad

- **Vanskelig**

**Sammenlignbart med:** 3) KI-styrt simulering av prosjektledelse (vanskelig) – omfattende domenelogikk som må stemme (kapasitet, tidsvinduer, frister, priser og kombinasjon av to bookingtyper), fordelt på mange moduler som henger sammen. Appen har ingen KI-funksjon, men domenelogikken alene gjør den krevende.

**Begrunnelse:**

| Faktor | Nivå (lav / middels / høy) | Kommentar |
|---|---|---|
| Domenelogikk – hvor mange og hvor kompliserte regler og beregninger må stemme? | Høy | Fordeling av plasser på badstuer, konflikt mellom enkeltplasser og hele badstuer, frister, verdikoder, refusjon, medlemspris, periodekort og regler som bare gjelder nye bookinger. |
| Datamodell – antall entiteter og relasjoner mellom dem | Høy | Badstue, tidsvindu, booking, plass, gjest, gavekort, verdikode, medlemskap, periodekort, dørkode, blokkering og innstillinger. |
| Brukere, roller og innlogging | Middels | Administrator (påkrevd) og gjest (valgfri konto), pluss booking uten konto med referanse. |
| KI-funksjonalitet i appen, f.eks. kall til språkmodell, prompts i koden og håndtering av usikre svar | Lav | Ingen KI i appen. KI brukes i utviklingen, og det er i tråd med emnet. |
| Integrasjoner og eksterne tjenester, f.eks. API-er, betaling og e-post | Middels | Betaling, e-post, dørlåser og oppvarming er simulert – et godt valg. Simuleringene må likevel bygges og testes. |
| Sanntid, samtidighet eller flere brukere som påvirker hverandre | Høy | Flere gjester booker samme tidsvindu, plasser holdes i 10 minutter, og dobbeltbooking må hindres. |
| Filhåndtering, f.eks. opplasting, PDF-lesing og eksport | Lav | Ikke en del av v1. |
| Sikkerhet og personvern | Middels | Kontoer med navn, e-post og passord, og rollebasert tilgang. Addendumet har gode utgangspunkter. |

**Hva vanskelighetsgraden betyr for dere:**

- _Vanskelig:_ Et vanskelig prosjekt gir større mulighet for toppkarakter, men også større risiko. Definer en minimal versjon som sikkert kan bli ferdig, og legg resten i tydelige trinn etterpå. For dere er suksesskriterium 1–4 en naturlig minimal versjon: booke plasser, booke hel badstue, endre og avbestille – med administratorvisning.

### Gjennomførbarhet med BMAD og Claude Code

Dere skal planlegge med BMAD (product brief → PRD → arkitektur → epics og stories) og implementere med Claude Code. Vurderingen under tar hensyn til at det må være tid til hele denne flyten, og til testing, retting og README til slutt.

| Spørsmål | Vurdering (OK / risiko / stor risiko) | Kommentar |
|---|---|---|
| **Tid og omfang** – kan v1 realistisk bli ferdig og stabil i løpet av semesteret, med tid til flere iterasjoner? | Stor risiko | Tolv suksesskriterier og rundt ti funksjonsområder, med én person og BMAD-flyten i tillegg. Kjernen (1–4) er realistisk; alt er det neppe. |
| **BMAD-flyten** – er briefen konkret nok til at PRD, arkitektur og stories kan lages uten store hull, og blir det overkommelig mange stories? | OK | Svært konkret, med beslutninger og åpne spørsmål samlet i addendumet. Antallet stories blir høyt med dagens scope; færre funksjoner gir en mer overkommelig plan. |
| **Egnet for Claude Code** – bruker løsningen en vanlig, godt dokumentert teknologistakk som Claude Code håndterer godt, eller krever den nisjeteknologi, spesialmaskinvare eller mye manuell konfigurasjon? | OK | Python-backend og JavaScript-frontend med uv er vanlig og godt dokumentert. Hold separasjonen mellom plattform og nettside enkel (ett API). |
| **Kontroll på KI-ens arbeid** – kan gruppen selv avgjøre om koden gjør det riktige? Krever domenet kunnskap gruppen ikke har, f.eks. avanserte beregninger eller fagregler, så er det vanskelig å kvalitetssikre. | OK | Dere har selv definert reglene og kan avgjøre om koden følger dem. Det er en stor fordel. |
| **Testbarhet** – finnes det tydelige regler og forventede resultater som tester kan skrives mot? | OK | Svært godt testbart, og automatiske tester av kriterium 1–8 er allerede planlagt. Legg til tester for samtidighet (to gjester som booker siste plass samtidig). |
| **Kjørbar for sensor** – kan appen kjøres lokalt etter README, uten gruppens nøkler, betalte kontoer eller egen infrastruktur? | OK | Alle eksterne tjenester er simulert, så sensor trenger ingen nøkler. Husk testbrukere (administrator og gjest) og eksempeldata i README. |
| **Avhengigheter og kostnader** – krever løsningen betalte API-er, f.eks. språkmodeller, og finnes det en plan for kostnad, testmodus eller mock-data? | OK | Ingen betalte tjenester. |

**Konklusjon om gjennomførbarhet:**

- **Gjennomførbart med justert omfang.** Se forslagene under.

**Forslag til justering av omfang eller vanskelighetsgrad:**

1. V1: enkeltplasser og hele badstuer, priser, simulert betaling og e-post med bookingreferanse, endring og avbestilling med frister, og administratorverktøy for tidsvinduer, kapasitet, priser og blokkering. Det dekker suksesskriterium 1–4 og er fortsatt et vanskelig prosjekt.
2. Trinn 2 (når v1 er stabil og testet): gavekort og verdikoder, deretter dørkoder. Flytt medlemskap, periodekort, fjernstyring av dører og styring av oppvarming til visjonen.
3. Begrens de justerbare reglene til noen få innstillinger med standardverdier i v1, i stedet for at alle regler skal kunne endres.

## Hvorfor product brief er viktig for mappen

Product brief er utgangspunktet for PRD, arkitektur, stories og til slutt koden. Del 1 av mappen vurderes blant annet på om sensor kan følge en sporbar vei fra plan til ferdig app. Den vurderes også på om appen gjør det dere har beskrevet, om den er testet, om den er godt designet, og om den kan kjøres etter README. Et uklart, for stort eller for lite brief gjør alt dette vanskeligere senere. Det er mye enklere å rette nå enn sent i semesteret.

## 1. Gjennomgang av briefens deler

| Del av brief | Status | Kommentar |
|---|---|---|
| Executive Summary – er det klart hva appen er, og hvilket problem den løser? | OK | Klart og ærlig: et bookingsystem for et fiktivt badstueanlegg, med simulert betaling, som ikke later som det er en ekte tjeneste. |
| The Problem – er problemet konkret, med reelle situasjoner og brukere? | OK | Konflikten mellom enkeltplasser og private bookinger, dobbeltsalg og avbestillinger er et konkret og godt formulert problem. |
| The Solution – beskriver løsningen brukeropplevelsen, ikke bare teknologi? | Juster | Godt beskrevet funksjon for funksjon, men det mangler en kort beskrivelse av gjestens vei gjennom nettsiden (velg tid → velg plasser eller hel badstue → betal → få bekreftelse). |
| What Makes This Different – er vurderingen ærlig og realistisk? | OK | Ærlig om at markedsfordelen ikke er bevist, og at styrken nå er presise, testbare regler. |
| Who This Serves – er primærbrukerne tydelige, og vet vi hva de trenger? | OK | Gjester og administrator er tydelig beskrevet med behov. Sensor er ikke en bruker av appen og kan tas ut av denne listen. |
| Success Criteria – kan kriteriene faktisk sjekkes eller testes? | Juster | Kriterium 1–8 og 10 er gode. Kriterium 9 er for vagt, og 11–12 er krav til leveransen, ikke appen. Gjør 9 om til konkrete, testbare sikkerhetstiltak. |
| Scope – er det klart hva som er med i første versjon, og hva som ikke er det? | Endre | Tydelig inndeling, og det er bra at alt eksternt er simulert. Men «In» er for stort for én person. Del i v1 og trinn 2 (se forslagene). |
| Vision – henger visjonen sammen med resten uten å blåse opp omfanget? | OK | Realistisk og tydelig adskilt fra v1. |

## 2. Utgangspunkt for del 1 av mappen

Punktene følger kriteriene i sensorveiledningen for del 1. Vektene i parentes viser hvor mye hvert kriterium teller i del 1.

| Kriterium i del 1 | Hva briefen bør legge til rette for | Status | Kommentar |
|---|---|---|---|
| **1. Prosess og KI-styring** (30 %) | Brief som er presis nok til at PRD og stories kan bygges direkte på den, slik at krav kan spores fra brief til kode. | OK | Briefen er presis, og historikken viser mange små, beskrivende commits. Fortsett slik gjennom PRD, arkitektur og implementering. |
| **2. Funksjonalitet og omfang** (20 %) | Realistisk omfang for gruppen og semesteret: en tydelig kjerneflyt som kan bli ferdig og stabil, og nok innhold til å vise reell funksjonalitet. | Endre | Kjerneflyten er tydelig, men omfanget er for stort. En stabil v1 med kriterium 1–4 gir mye reell funksjonalitet. |
| **3. Kvalitetssikring og testing** (15 %) | Suksesskriterier og funksjoner som er konkrete nok til å bli testtilfeller. | OK | Svært godt grunnlag for automatiske tester. Legg til samtidighetstester og konkrete sikkerhetstester. |
| **4. Design og brukeropplevelse** (10 %) | Tydelige brukere og brukssituasjoner som designet kan bygges rundt, gjerne med de viktigste skjermbildene eller flytene skissert. | OK | Finsk-inspirert, rolig stil og responsivt design gir god retning. Skisser bookingflyten og administratorkalenderen tidlig. |
| **5. Kodekvalitet og arkitektur** (10 %) | Teknologivalg som er begrunnet og ikke mer komplekse enn appen trenger. | Juster | Python og JavaScript er greit. Hold skillet mellom plattform og nettside til ett enkelt API i v1, uten støtte for flere nettsider. |
| **6. README og kjørbarhet** (10 %) | Løsning som andre kan kjøre lokalt uten betalte kontoer, og uten tilgang til gruppens egne tjenester og nøkler. | OK | Alt eksternt er simulert, og README beskriver allerede uv. Legg til oppstart av frontend, testbrukere og eksempeldata. |
| **7. Ryddighet i repoet** (5 %) | En plan for hvor hemmeligheter, testdata og dokumentasjon skal ligge. | OK | Ryddig struktur med `.docs/`, `src/` og `.gitignore`. Kravet om «rene» ressurser (ingen lisensbelagt materiale) er også bra. |

## 3. Neste steg for gruppen

1. Del Scope i v1 (kriterium 1–4 med administratorverktøy) og trinn 2 (gavekort, dørkoder), og flytt medlemskap, periodekort, fjernstyring og oppvarming til visjonen.
2. Gjør suksesskriterium 9 om til 3–5 konkrete, testbare sikkerhetstiltak, og flytt 11–12 til en egen liste over leveransekrav.
3. Lukk de åpne spørsmålene i addendumet som gjelder v1 (enkeltplasser og booking uten konto), og gå videre til PRD.

Oppdater product brief i repoet når dere har gjort endringene, slik at historikken viser hvordan planen utviklet seg. Det er en del av prosessen sensor ser etter.
