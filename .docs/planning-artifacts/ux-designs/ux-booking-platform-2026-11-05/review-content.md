# Innholdsreview: DESIGN.md og EXPERIENCE.md

Dato: 2026-11-06. Omfang: DESIGN.md, EXPERIENCE.md, .memlog.md og mockups/ (key-details, key-review, key-confirmation, key-booking-list, directions-3), holdt mot PRD, PRD-addendum, arkitekturspine, brief og brief-addendum. `.working/` er ikke brukt som kilde.

Linjehenvisninger: `EXP` = EXPERIENCE.md, `DES` = DESIGN.md, `PRD` = prd.md, `ADD` = PRD-addendum, `ARCH` = ARCHITECTURE-SPINE.md. Sitater fra `EXP` og mockups står som i filene.

## Samlet vurdering

Dokumentparet stemmer godt med kildene på tall, regler, fast tekst og eksempeldata, og alle de 15 punktene i PRD impact står faktisk i PRD-en eller spinen. Svakheten ligger i det gjesten trenger for å handle trygt: vilkår og personvernerklæring finnes ikke, bekreftelsen sier ikke hvor gjesten skal, e-posten kan ikke sjekkes før et kjøp som ikke kan endres, og setningen om ingen refusjon har ikke noe unntak. Ingen funn stopper bygging i dag, så ingen er satt til critical, men de fem som er high bør avgjøres før bekreftelse, vilkår og Review bygges.

| Alvorlighetsgrad | Antall |
|---|---|
| Critical | 0 |
| High | 5 |
| Medium | 13 |
| Low | 12 |

## Funn

### High

**H-1. Setningen om ingen refusjon har ikke noe unntak når Saunalöyly selv avlyser**
- **Plassering:** EXP L158, Required statements; `key-review.html` L95; `key-confirmation.html` L87 og L103.
- **Sitat:** "A booking cannot be changed or refunded."
- **Problem:** Setningen er absolutt, men PRD-en sier noe annet for det tilfellet at stedet ikke kan levere. Gjesten blir fortalt at pengene er tapt uansett årsak, også ved stengt anlegg. Det stemmer ikke med produktets egen posisjon og kan villede om gjestens rettigheter. Core har heller ingen vei for dette: Booking list er skrivebeskyttet (EXP L552, PRD Q7) og ingen annen rute tilbys (PRD L233).
- **Kilde:** PRD §9 L933: "When Saunalöyly cancels, the Guest chooses between a refund and a Voucher." ADD D L176: "Keeping the money when the trader cancels may be unfair". FR-5 L233 pålegger setningen, så PRD-en er selvmotsigende her.
- **Forslag:** Endre til det som faktisk menes: "You cannot change or cancel a booking, and there is no refund if you do not come." Legg til i Terms: "If Saunalöyly has to cancel, you get your money back." Oppdater FR-5 L233, og gjenåpne Open Items 11 (EXP L547). Si også i Terms hvordan gjesten da hører fra stedet.

**H-2. Bekreftelsen sier ikke hvem eller hvor**
- **Plassering:** `key-confirmation.html` L90–109 (e-post), L85 (side); EXP L116, L252, L426.
- **Sitat:** "Keep your booking reference and give it at reception when you arrive."
- **Problem:** E-posten nevner ikke Saunalöyly i det hele tatt: ordet forekommer ikke i brødteksten, og den har heller ikke adresse eller kontakt. Bekreftelsessiden har Wordmark, men ingen adresse eller kontakt, fordi Booking summary bare har Venue-radene på Review (EXP L252). Gjesten får beskjed om å gå til en resepsjon, uten å få vite hvor den er i det eneste varige dokumentet. Har gjesten et spørsmål, står det ingen kontaktvei der.
- **Kilde:** PRD §7 L879 og FR-8 L259–266 ramser ikke opp Venue-opplysninger, så mangelen starter i PRD-en. ADD D L168 krever bekreftelse på varig medium, og FR-5 L231 krever Venue-identitet før betaling. Malen følger mocken gjennom antakelsen i EXP L426.
- **Forslag:** Legg til rader for Venue og Contact på Confirmation, som på Review, og en blokk øverst i e-posten: "Saunalöyly", adresse, kontakt. Oppdater FR-8 og tabellen i §7.

**H-3. Gjesten får ikke sjekket navn og e-post før betaling**
- **Plassering:** EXP L45, L170, L252; `key-review.html` L93; Flow 1 EXP L463.
- **Sitat:** "Check everything, accept the terms, pay" (L45). Booking summary: "On Review it also holds Venue identity and contact details" (L252).
- **Problem:** Review viser verken navn eller e-post, selv om siden lover "Check everything". E-posten er den eneste kanalen for bekreftelsen, og en skrivefeil oppdages først på Confirmation, etter et kjøp som ikke kan endres. Da har bekreftelsen med personopplysninger gått til en fremmed, og resepsjonens reserveløsning (navn og e-post) treffer dårligere.
- **Kilde:** ADD E L249: "use a check-answers page". ADD D L173: forklare "how to correct mistakes" før bestilling. FR-5 L229–232 krever ikke feltene, men forbyr dem heller ikke.
- **Forslag:** Legg til radene Name og Email i Booking summary på Review, med Back som rettevei. Kontroller at Pay fortsatt er i første visning ved 1366 × 768 (Lisa, EXP L396). Legg til en linje på Details om at bekreftelsen sendes til denne adressen.

**H-4. Antakelsen for tapt nettleserøkt kan gi dobbel Booking og dobbel betaling**
- **Plassering:** EXP L342.
- **Sitat:** "The SPA makes a new browser session and a new key without comment, entered values stay, and the Guest sees \"please try again\"."
- **Problem:** Etter AD-9 lagres bare suksess, så `409 invalid_key` betyr at nøkkelen allerede har gitt en Booking i en annen økt. Da er det feil svar å lage ny nøkkel og be gjesten prøve igjen: neste trykk på Pay gir en ny Booking og en ny betaling. Gjesten ser ikke den første, og kjøpet kan ikke endres eller refunderes. Tilfellet krever at svaret gikk tapt og at økten utløp, så det er smalt, men følgen er alvorlig. `401 no_session` har samme risiko hvis økten er slettet, for da forsvinner også nøkkelraden (AD-8: `CASCADE`).
- **Kilde:** ARCH AD-9 L134–138: "It reuses the same key for every retry of that review", "only a success is stored". FR-6 L246. ARCH AD-8 L123, L126.
- **Forslag:** Skill de to kodene. Ved `invalid_key`: ingen ny nøkkel og ingen Pay, men en Notice som ber gjesten kontrollere bekreftelsen før nytt forsøk. Ved `no_session`: la arkitekturen avgjøre om nøkkelraden skal overleve økten til Window er slutt. Dette er en antakelse som må bekreftes før Review bygges.

**H-5. Gjesten godtar en tekst som ikke finnes**
- **Plassering:** `key-review.html` L95; `key-confirmation.html` L87, L104; EXP L538–539.
- **Sitat:** "[Rest of the booking terms]"
- **Problem:** Terms og Privacy notice er ikke skrevet. Dermed er det uavklart hva "I accept the booking terms" binder gjesten til. Det er ført i Open Items, men ingen av punktene har eier eller frist, og flere funn i denne rapporten må løses i disse tekstene. Tekstene trengs i `content/` for både side og e-post (AD-12). §10.1 krever endelig tekst før Core er ferdig.
- **Kilde:** PRD §10.1 L955, FR-5, FR-21, ADD D. EXP L532.
- **Forslag:** Skriv Terms og Privacy notice før Review og Confirmation regnes som ferdige. Bruk listen under "Manglende innhold" som innholdsliste.

### Medium

**M-1. Uklart hvilke vilkår gjesten godtar og får med seg**
- **Plassering:** EXP L169, L181, L538, L425; `key-review.html` L94–97; `key-confirmation.html` L86–88, L101–104.
- **Sitat:** "I accept the booking terms". "The part shown on Review must stay short, about six lines at most ... The rest belongs on the Terms page."
- **Problem:** Heading sier "Booking terms", lenken sier "Terms", og avkrysningen sier ikke om den gjelder de seks linjene eller hele siden. Confirmation og e-post har bare kortdelen og ingen lenke til Terms, så gjesten har ikke vilkårene hun godtok i det varige dokumentet.
- **Kilde:** FR-5 L232–234, FR-8 L265, ADD D L168, ARCH AD-12 L169.
- **Forslag:** Bruk "I accept the booking terms" sammen med lenketeksten "Full booking terms", og vis samme lenke på Confirmation og i e-posten. Avklar om e-posten skal ha hele teksten (se Vilkår, kjøp og personvern).

**M-2. "cannot be withdrawn" sier ikke det loven krever at gjesten får vite**
- **Plassering:** EXP L157; `key-review.html` L95; `key-confirmation.html` L87, L102.
- **Sitat:** "A booking for a fixed date cannot be withdrawn."
- **Problem:** Ordet "withdrawn" er en juridisk term uten kontekst, og setningen nevner ikke retten som faller bort. Rett etter følger "cannot be changed", så den leses lett som en gjentakelse og ikke som opplysning om angrerett.
- **Kilde:** FR-5 L232: "has no right of withdrawal". ADD D L164–165.
- **Forslag:** "This booking is for a fixed date and time, so there is no right of withdrawal." Endelig ordlyd må sjekkes av jurist ved ekte drift.

**M-3. Egen bekreftelse møter gjesten som "not available", uten forklaring**
- **Plassering:** EXP L194, L329, L341.
- **Sitat:** "This page is not available."
- **Problem:** Økten varer i 24 timer (AD-8). Åpner gjesten bekreftelsen dagen etter, eller på en annen enhet, står det bare at siden ikke er tilgjengelig, og det kan leses som at bookingen er borte. Reglen om at svaret skal være likt er riktig, men teksten kan likevel forklare.
- **Kilde:** FR-8 L269, FR-20 L401, ARCH AD-8 L125, FR-22 L432.
- **Forslag:** På `/confirmation/:reference`, likt for alle referanser: "This page is not available. A confirmation can only be opened in the browser you booked in. Your booking is not affected: find the confirmation in your email." Avklar sammen med M-7.

**M-4. Reserveløsningen ved tapt referanse når aldri gjesten**
- **Plassering:** EXP L490, L549; PRD §3 L134.
- **Sitat:** "A Guest who has lost the reference gives their name and email instead, and Katja finds the Booking the same way (Lisa)."
- **Problem:** Reglen finnes bare i Flow 3 og i PRD-en. Ingen gjestetekst nevner den, så en gjest uten referanse har ingen grunn til å tro at hun slipper inn.
- **Kilde:** PRD §3 L134, FR-22 L432.
- **Forslag:** Legg setningen i Terms og i "Before you come", Practical: "Lost your booking reference? Give your name and email at reception."

**M-5. "please try again" er et fragment, og Pay kan være borte**
- **Plassering:** EXP L144, L284, L292, L321–322, L342–343.
- **Sitat:** "Notice with \"please try again\", different from \"No seat free\"." "Pay, the payment note and the Terms checkbox are removed for the refused Session".
- **Problem:** Alle andre meldinger på Review sier "You have not been charged.", men denne, som kommer rett etter et trykk på Pay, gjør det ikke. Fire tilstander deler fragmentet, og ingen full setning er skrevet. Raden "After a refusal" skiller heller ikke `try_again` fra de andre, så leser man den bokstavelig fjernes Pay, og gjesten blir bedt om å prøve igjen uten en knapp å prøve med.
- **Kilde:** FR-14 L319–320, FR-22 L432, ARCH Conventions L290 (503 `try_again`), AD-9 L138.
- **Forslag:** Review: "Something went wrong on our side. You have not been charged. Please try again." Skriv i L322 at Pay, merknaden og avkrysningen står igjen ved `try_again`.

**M-6. Ingen plass i hele horisonten gir ingen neste steg**
- **Plassering:** EXP L189, L299; motsier L130.
- **Sitat:** "There is no room for 2 seats in the next 4 weeks." og "Say so plainly, with no alternatives".
- **Problem:** Gjesten står uten neste steg, som Voice-tabellen selv avviser ("A message with no next step"). Hun kan faktisk gjøre noe: velge færre seter, eller komme tilbake senere.
- **Kilde:** FR-22 L432.
- **Forslag:** "There is no room for 2 seats in the next 4 weeks. You can try fewer seats, or come back later: booking opens 4 weeks ahead."

**M-7. Teksten sier ikke at e-posten er simulert og stedet fiktivt**
- **Plassering:** EXP L172, L254, L422; `key-confirmation.html` L90; `directions-3.html` L143.
- **Sitat:** "Sent by email:"
- **Problem:** Ingen e-post sendes. Merknaden "Simulated payment: no money moves" gjelder bare betalingen, og ingen gjestetekst sier at Saunalöyly er fiktivt. En ekte bruker venter på en e-post som aldri kommer, og hvis fanen lukkes, er referansen tapt. M-3 og M-4 lener seg på den samme e-posten.
- **Kilde:** PRD §1 L35: "it does not pretend to be one". PRD §3 L119. FR-6 L243.
- **Forslag:** Bruk "Sent by email (simulated):" over e-posten, og legg til i Find us og Terms: "Saunalöyly is a fictional venue in a student project." Da må "Keep your booking reference" stå som den viktigste handlingen.

**M-8. "never alone" er ikke sant for alle gjester, og begrunnelsen holder ikke**
- **Plassering:** `directions-3.html` L140; EXP L548; FR-1 L179.
- **Sitat:** "Bathe with caution, and never alone." og "The saunas are shared, so a Guest with 1 seat is not alone."
- **Problem:** En sikkerhetsregel må kunne følges. Alle kan bestille 1 sete, også i en økt uten andre gjester (`key-booking-list.html` L83 viser "Seats booked 0"), og systemet håndhever ingenting (PRD §9 L938). Med fire badstuer og fri bevegelse kan gjesten også være alene i et rom selv om økten er delt. Begrunnelsen for å lukke punktet stemmer derfor ikke.
- **Kilde:** FR-2, FR-1 L179, PRD §9 L938, EXP L131.
- **Forslag:** Gjenåpne Open Items 12 og erstatt regelen med noe gjesten kan gjøre, for eksempel: "Bathe with caution and look out for each other. If you are on your own, tell reception." Det siste krever en beslutning om hva resepsjonen gjør. Oppdater FR-1 hvis teksten endres.

**M-9. Sikkerhetsteksten dekker ikke den største risikoen kildene nevner, og sier ikke hva gjesten gjør ved ubehag**
- **Plassering:** `directions-3.html` L140, Safety.
- **Sitat:** "Alcohol is not allowed at the venue." og "leave the sauna if you feel unwell."
- **Problem:** Alkoholregelen gjelder bare på stedet. Kilden begrunner den med påvirkning, og det gjelder også den som har drukket før ankomst. "Leave the sauna" stopper der: ingenting sier hvem gjesten skal si fra til, verken om seg selv eller om andre. Hjerteproblemer, graviditet og lignende nevnes ikke, men det har heller ingen av kildene. Hele innholdet er merket som antakelse i PRD-en.
- **Kilde:** ADD F L285: "about 80 % of Finland's 30–40 yearly sauna heat deaths involved intoxication". ADD F L289. FR-1 L177.
- **Forslag:** "Do not use the sauna after drinking alcohol." og "Leave the sauna if you feel unwell, and tell reception." Legg til en linje som ber gjester med helseplager spørre lege først. Ordlyden i ADD F L289 er valgt av Lisa, så endringen må bekreftes.

**M-10. Gjesten får ikke vite at barn trenger sete og koster det samme**
- **Plassering:** `directions-3.html` L136, L140; EXP L84, L224.
- **Sitat:** "Children must be supervised by an adult."
- **Problem:** Regelen sier at barn kan komme, men ikke at hvert barn trenger et sete og koster fullt. PRD-en har bestemt dette, men det står ikke i noen gjestetekst. En familie kan bestille feil og oppdage det i resepsjonen, uten rett til å endre. Ingen tekst sier heller om det finnes en aldersgrense for å bestille.
- **Kilde:** PRD §9 L937: "every Seat costs the same". PRD §3 L124.
- **Forslag:** Legg til i "Before you come", Practical: "Everyone needs a seat. Adults and children pay the same." Avklar aldersgrense for å bestille (se juridisk del).

**M-11. Tilbake fra Confirmation er ikke beskrevet og kan gi ny Booking**
- **Plassering:** EXP L316, L368.
- **Sitat:** "Back in the browser and the Back link do the same thing, and neither loses input (FR-5)."
- **Problem:** Regelen dekker ikke Confirmation. Etter AD-9 lages nøkkelen "when the Guest reaches the review page", så en bokstavelig bygging gir Review med ny nøkkel etter nettleserens tilbake-knapp, og Pay kan da gi en andre Booking. L316 gjelder bare dobbeltklikk, reload og retry.
- **Kilde:** FR-6 L246, ARCH AD-9 L134.
- **Forslag:** Legg til en tilstand: "After payment, Back to Review shows Confirmation." Da kan ikke samme gjennomgang betales to ganger.

**M-12. Samtykkebanner er forbudt mens spørsmålet fortsatt er åpent**
- **Plassering:** EXP L371 mot L539.
- **Sitat:** "consent banner (FR-21)" under **Banned**, og "Check the \"no consent banner\" claim against the session cookie".
- **Problem:** Spinen sier at banner er forbudt og at påstanden må sjekkes. AD-8 setter cookie for hver besøkende når SPA-en lastes, også for dem som bare leser Landing. Om det er strengt nødvendig for en tjeneste brukeren har bedt om, er ikke opplagt. Punktet har ingen eier, og Privacy notice kan ikke skrives ferdig uten svaret.
- **Kilde:** FR-21 L416, ARCH AD-8 L124, ADD D L194.
- **Forslag:** Opprett økten først når gjesten går inn på Book seats, så forsvinner spørsmålet for Landing. Dette krever endring i AD-8. Ved ekte drift må jurist sjekke vurderingen.

**M-13. FR-21 gir ikke grunnlag for en fullstendig personvernerklæring**
- **Plassering:** EXP L539; FR-21 L409–414; PRD §3 L134.
- **Sitat:** "Privacy notice text. Required contents are in FR-21."
- **Problem:** Tre hull: (1) FR-21 nevner ikke hvem behandlingsansvarlig er og hvordan hen kontaktes, og det er påkrevd etter GDPR art. 13. Her trengs et ærlig svar, siden stedet er fiktivt. (2) Sletting etter 12 måneder er en antakelse og står mot ADD D L192 om 5 års oppbevaring av regnskapsmateriale. (3) "Who sees it" må dekke resepsjonen, som etter antakelsen bruker Administrator-listen med alle gjesters navn og e-post.
- **Kilde:** FR-21 L414, ADD D L190–192, ARCH AD-4 L88, AD-12 L173.
- **Forslag:** Utvid FR-21 med behandlingsansvarlig, og bekreft oppbevaringstiden før teksten skrives. I studentprosjektet kan erklæringen si at data bare ligger lokalt.

### Low

**L-1. Tre setninger i EXPERIENCE.md er utdatert etter PRD-oppdateringen**
- **Plassering:** EXP L50, L342, L446.
- **Sitat:** "PRD §7 lists them as one, and FR-5 allows either." "Not in the PRD's §7 list." "The Book action in FR-35 and FR-37 is the Continue action on Book seats."
- **Problem:** PRD-en sier nå det motsatte eller noe mer presist: FR-5 L229 og §7 L860 har to sider, §7 L873 har tilstanden, og FR-35 L598 og FR-37 L631 sier "Continue booking".
- **Forslag:** Stryk de tre setningene, og marker i L580–592 at punktene er gjennomført.

**L-2. Henvisninger til forkastet materiale**
- **Plassering:** EXP L452, L539, L551, L586.
- **Sitat:** "Times are seed times (extract §14, C1)."
- **Problem:** "extract" er `.working/source-extract.md`. Den er forkastet og står ikke blant kildene i front matter, så sporene brytes.
- **Forslag:** Vis direkte til PRD §12 Q3, FR-21 og AD-8, og ADD E L248.

**L-3. Knappen heter to ting**
- **Plassering:** EXP L44–45, L102, L114, L190, L232, L439–440 mot L166.
- **Sitat:** "Continue" og "Continue booking".
- **Problem:** Etiketten er "Continue booking", og PRD-en bruker den. Spinen sier "Continue" i flere rader, også der den beskriver når en Hold starter.
- **Forslag:** Bruk "Continue booking" i rader som beskriver knappen.

**L-4. "Only" ligger nær det Voice-tabellen avviser**
- **Plassering:** EXP L183 mot L128.
- **Sitat:** "Only 1 seat left in this session. You have not been charged."
- **Problem:** Tallet er sant, men "Only" er ordet i eksempelet på det som ikke skal brukes, og setningen sier ikke hvorfor gjesten ble avvist.
- **Kilde:** FR-3 L205, NFR-9.
- **Forslag:** "1 seat left in this session, too few for this booking. You have not been charged."

**L-5. Siste dag i horisonten kan ha økter som mangler uten forklaring**
- **Plassering:** EXP L225, L298.
- **Sitat:** "All Sessions for the date in time order, including unavailable ones".
- **Problem:** Horisonten telles "from the moment of booking" (PRD §3 L145), så den siste dagen kan ha økter utenfor. Spinen beskriver ikke dem, og `horizon_end` er bare en dato (AD-16 L215).
- **Forslag:** Bestem at slike økter ikke vises, og la linjen "Booking opens 4 weeks ahead." forklare dem.

**L-6. Avvisning på Review uten noen ledige økter**
- **Plassering:** EXP L171, L322.
- **Sitat:** "The nearest sessions with room:"
- **Problem:** Finnes det ingen økter å foreslå, står etiketten over en tom liste, og Pay er borte.
- **Forslag:** Bruk teksten fra M-6 i stedet for etiketten, og la Back være neste steg.

**L-7. Grensen på 10 seter forklares ikke**
- **Plassering:** EXP L224; `directions-3.html` L146.
- **Sitat:** "Ten choices, 1 to 10 (FR-2)."
- **Problem:** En gruppe på 12 ser at valgene stopper, uten å få vite at de kan lage to bookinger (FR-9). Private sauna finnes ikke i Core.
- **Forslag:** Hint under spørsmål 2: "Up to 10 seats per booking. For more, make another booking." Sjekk mot plassbudsjettet på siden (DES L379).

**L-8. "Already started" følger ikke med til Review**
- **Plassering:** EXP L176, L295; `key-review.html` L93.
- **Sitat:** "Already started"
- **Problem:** Gjesten betaler full pris for en økt som er i gang, og Review, der kjøpet skjer, sier det ikke. Ingen kilde sier hva som gjelder ved sen ankomst eller om gjesten ikke møter.
- **Kilde:** PRD §3 L146; FR-5.
- **Forslag:** Vis "Already started" ved Session-raden på Review, og ta sen ankomst og uteblivelse inn i Terms.

**L-9. Begrunnelsen for feil på Landing holder ikke**
- **Plassering:** EXP L284.
- **Sitat:** "the Notice says \"please try again\", because Book seats still works without them"
- **Problem:** Book seats henter øktene fra det samme API-et, så feilen vil trolig ramme begge. Prisen, åpningstidene og adressen mangler da også.
- **Kilde:** ARCH AD-16 L220.
- **Forslag:** Fjern begrunnelsen og si hva gjesten ser i tomme felt.

**L-10. Format for beløp over 1000 er ikke bestemt**
- **Plassering:** `key-booking-list.html` L83; EXP L141.
- **Sitat:** "NOK 1000"
- **Problem:** Mocken bruker "NOK 1000" og addendumet "NOK 1,360". Pay for 10 seter viser "Pay NOK 2500".
- **Kilde:** ARCH Conventions L289.
- **Forslag:** Velg én form, gjerne "NOK 2,500" på engelsk, og før den inn i Conventions.

**L-11. Sign-in mangler lenke til Privacy notice**
- **Plassering:** EXP L48, L118.
- **Sitat:** "Text link wherever data is collected"
- **Problem:** Sign-in samler inn e-post og passord, men sideoppskriften har ingen lenke. Det får betydning når gjestekonto kommer, fordi EXP L444 gjenbruker skjemaet.
- **Kilde:** FR-21 L409.
- **Forslag:** Legg lenken til i L118.

**L-12. Følgesvenner vet ikke om referansen**
- **Plassering:** EXP L159; `key-confirmation.html` L84.
- **Sitat:** "Keep your booking reference and give it at reception when you arrive."
- **Problem:** Bare den som bestiller har referansen, og navnet er bestillerens. En venn som kommer først, har ingenting å oppgi.
- **Forslag:** Legg til i "Before you come", Practical: "Coming separately? Share the booking reference with your group."

## Kontroll av PRD impact (EXP L576–592)

Påstanden i EXP L576 stemmer. Alle punktene er kontrollert mot filene:

| Punkt | Finnes i | Resultat |
|---|---|---|
| 1 Q2 | PRD L1022 | Står |
| 2 Reception | PRD §3 L134, FR-8 L267 | Står |
| 3 Session | PRD §3 L123, §6 L850, FR-1 L180 | Står |
| 4 Én total | FR-3 L206 | Står |
| 5 Endringssetningen | FR-5 L233 | Står, men se H-1 |
| 6 To sider | FR-5 L229, §7 L860 | Står. EXP L50 er utdatert (L-1) |
| 7 Plassering av timeplanen | Ingen endring trengs | Riktig |
| 8 Book-handlingen | §4.11 L593, FR-35 L598, FR-37 L631 | Står. EXP L446 er utdatert (L-1) |
| 9 Tider | UJ-1, UJ-2, UJ-3 | Står |
| 10 Administrator-adresse | UJ-3 L85 | Står |
| 11 Saunanavn | UJ-5 L101 | Står |
| 12 Økt som utløper | §7 L873 | Står. EXP L342 er utdatert (L-1) |
| 13 Serverstøtte | AD-16 L214–215 | Står |
| 14 UI-ordet | AD-12 L170 | Står |
| 15 Q7 | PRD L1037 | Står |

Tall og eksempeldata stemmer også mellom dokumentene: Saunaer og kapasitet, åpningstider, åtte økter, NOK 250, 8 tegn i referansen, alle summene i `key-booking-list.html` og ukedagene i mockene. Fast tekst (EXP L136–147) stemmer med FR-6, FR-8, FR-14 og FR-22.

## Vilkår, kjøp og personvern

**Lovkrav jeg er sikker på**
- Gjesten skal få vite før kjøpet at angreretten ikke gjelder. Unntaket for fritidstjenester på en bestemt dato finnes i direktiv 2011/83/EU art. 16 bokstav l, og opplysningsplikten i art. 6 nr. 1 bokstav k. Prosjektet følger dette i FR-5, men ordlyden er svak (M-2).
- Bestillingsknappen må vise betalingsplikten (samme direktiv art. 8 nr. 2). "Pay NOK 500" ser ut til å oppfylle dette, så her er det ikke noe funn.
- Personvernerklæringen må oppgi hvem som er behandlingsansvarlig og hvordan hen kontaktes (GDPR art. 13 nr. 1 bokstav a). Dette mangler i FR-21 (M-13).

**Må sjekkes av jurist ved ekte drift**
- Om "cannot be changed or refunded" kan stå uten unntak, og hvilke rettigheter gjesten har hvis stedet avlyser eller ikke leverer (H-1).
- Om kortdelen av vilkårene er nok i bekreftelsen, eller om hele vilkårene må stå i e-posten (M-1, ADD D L168).
- Ordlyden om angrerett (M-2).
- Om økt-cookie ved første lasting er strengt nødvendig (M-12).
- Oppbevaringstid mot bokføringskravet (M-13).
- Aldersgrense for å inngå avtale, og ansvar for barn (M-10).
- Ansvar ved skade eller ubehag, og om sikkerhetsreglene skal være en del av vilkårene, for eksempel om stedet kan nekte adgang.
- Offentlige krav til drift av badstu. Her oppgir jeg ingen henvisning, fordi jeg ikke er sikker.

**Ekte drift krever i tillegg**
- Reell juridisk enhet, organisasjonsnummer og MVA-opplysninger (PRD §12 Q12, ADD D L172).
- Opplysninger på norsk hvis tjenesten markedsføres til norske forbrukere (ADD D L169).
- Ekte betaling og e-post, og en faktisk kontakt- og avlysningsrutine.
- Egen tilgang for resepsjonen i stedet for delt Administrator-konto (PRD §3 L133–134).
- Nødinformasjon med adresse og nødnummer, og en fagkontroll av sikkerhetsteksten.

## Manglende innhold

**Allerede ført i Open Items (EXP L534–542), blokkerer Core done (PRD §10.1)**

| Innhold | Plassholder |
|---|---|
| Stedsbeskrivelse | `directions-3.html` L139 |
| Én linje per Sauna, fire stykker. Finske ord må ha engelsk forklaring (PRD §6) | L141 |
| Badetøyregelen. Krever en beslutning, ikke bare tekst | L140 |
| Adresse, telefon, e-post. Ikke bruk `admin@saunaloyly.example`, som også er innloggingsnavn | L143, `key-review.html` L93 |
| Terms | H-5 |
| Privacy notice | H-5, M-13 |
| Ekte bilder, og alt-tekst for hvert bilde | L138–142 |
| Logo og favicon | EXP L542 |

**Ikke ført i Open Items**

| Innhold | Hvor | Kilde |
|---|---|---|
| Emne og avsender for Booking confirmation | Outbox, e-post | FR-17 L359 krever emne |
| Base URL i e-post | `key-confirmation.html` L107 | EXP L426 |
| Feiltekst når vilkår ikke er godtatt | Review | EXP L216, L314 |
| Feiltekst for feilskrevet dato og dato som ikke kan bestilles | Book seats | EXP L300–301 |
| Feiltekst for manglende dato og antall. Bare "Choose a session" finnes | Book seats | EXP L190, L232 |
| Notice når valgt økt fjernes fordi antallet ikke passer | Book seats | EXP L226 |
| Notice når datoen er utsolgt før antall er valgt. "No room for 2 seats" har da ikke noe tall | Book seats | EXP L187, L225 |
| Full tekst for "please try again" på Landing, Book seats, Review og ved tapt økt | M-5 | FR-14 |
| Overskrifter på Terms, Privacy notice, Sign-in og Outbox, og feltetiketter på Sign-in | EXP L117–120 | |
| Sidetitler (`<title>`) for alle sider | Alle | FR-23 |
| Tekst uten JavaScript og med cookies blokkert. Uten cookie går gjesten i ring på "please try again" | Alle | EXP L551, AD-8 L124 |
| Rad for anonymisert gjest i Booking list | Booking list | AD-4 L88 |
| Vilkårspunkter: avlysning fra stedet, sen ankomst, uteblivelse, tapt referanse, barn | Terms | H-1, L-8, M-4, M-10 |
| Gjestetekst som bare står i mock: spørsmål 1–3, faktaene i rail, "NOK 250 per seat in every session", "Booking reference", "Name", "Email", "Next month" | EXP L162–196 | EXP L16 |
| Ny vilkårstekst når §4.8 og §4.9 bygges. "A booking cannot be changed or refunded." blir da feil | Review, Confirmation, e-post | FR-5 L232–233 |

**Tilstander der gjesten står uten forklaring eller neste steg**

| Tilstand | Vurdering |
|---|---|
| Utsolgt økt eller dato | Dekket, unntatt hele horisonten (M-6) |
| Frist passert før betaling | Dekket (EXP L185, L320) |
| Betaling avvist | Dekket (EXP L186, L317) |
| Tapte seter og siste sete | Dekket. Mangler tilfellet uten ledige økter (L-6) |
| Konflikt, forsøk brukt opp | Ikke dekket godt nok (M-5) |
| Tapt referanse | Ikke dekket for gjesten (M-4) |
| Bekreftelse åpnet senere eller et annet sted | Ikke dekket godt nok (M-3) |
| Tapt nettleserøkt | Feil behandling (H-4) |
| Tilbake etter betaling | Ikke beskrevet (M-11) |
| Feil e-post oppdaget etter kjøp | Ingen vei, og hindres ikke (H-3) |

## Merkevare og tone

Feilmeldingene og sikkerhetsreglene er rolige og saklige, og Do/Don't-listene følger PRD §6. Bare ett konkret forhold bør nevnes: den lovede følelsen av avkobling hviler i dag på innhold som ikke finnes. Beskrivelsen, de fire linjene og alle bilder er plassholdere (`directions-3.html` L138–142), så DES L281 ("through imagery and quiet space") kan ikke vurderes ennå. Der tone og klarhet står mot hverandre, er det klarheten som må vinne: M-2, M-8 og M-9 viser steder der knapp ordlyd går ut over forståelsen.

## Triage av antakelser

Det er 40 `[ASSUMPTION]`-merker i EXPERIENCE.md (L528 er bare en omtale av merkene) og 10 i DESIGN.md.

**Binder innhold eller oppførsel, må bekreftes før bygging (8)**

| Sted | Antakelse | Hvorfor |
|---|---|---|
| EXP L61, L490 | Resepsjonen bruker Booking list | Bærer Confirmation-teksten, og forutsetter delt Administrator-konto |
| EXP L342 | Ny økt og ny nøkkel | H-4 |
| EXP L284 | Landing ved lesefeil | M-5, L-9 |
| EXP L292 | Book seats ved lesefeil | M-5. Full tekst mangler |
| EXP L341 | Én felles "not available"-side | M-3 |
| EXP L426 | E-postoppsett følger mocken | H-2 |
| EXP L110 | Rekkefølge på Terms, Privacy notice, Sign-in og Outbox | Ikke gjennomgått. Bør avgjøres sammen med tekstene (H-5, L-11) |

**Tilsvarende i kildene, må bekreftes**

| Sted | Antakelse | Hvorfor |
|---|---|---|
| PRD FR-1 L177 | Innholdet i "Before you come" utover håndklær og badereglene | Sikkerhetstekst (M-8, M-9) |
| PRD FR-21 L414 | 12 måneders oppbevaring | Må stå i Privacy notice (M-13) |
| PRD FR-8 L269 | Bekreftelsen er bundet til økten | M-3 |
| EXP L538 | Vilkårene på Review maks seks linjer | Avgjør hva som må stå hvor (M-1) |

**Kan stå til den aktuelle If-time-delen planlegges (6)**

EXP L436 (to merker, plassering av Private sauna og pris), L438 (Voucher-felt), L440 (Cancel), L441 (My booking), L444 (gjestekonto).

**Trygge arbeidsvalg (26 i EXPERIENCE.md, 10 i DESIGN.md)**

- **EXPERIENCE.md:** L22, L36, L75, L223, L230, L232, L234, L262, L263, L265, L291, L343, L353, L356, L357, L366, L369, L370, L397, L398, L404–407, L422, L471. L357 og L422 er trygge som valg, men L357 trenger full tekst, og L422 må ses sammen med M-7.
- **DESIGN.md:** L287, L299, L350, L354, L358, L360, L385, L387 (to merker), L421. Ingen av dem binder innhold.
