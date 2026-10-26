# CLAUDE.md

**Logg alltid sesjonen.** Claude skal alltid logge via `sesjonslogg`-skillen når en oppgave/økt avsluttes — før sluttoppsummeringen, uten at brukeren må be om det. Skillen logger Oppgave + Plan + Resultat + åpne punkter per bruker i `.logs/<bruker>/`, committer loggfila (kun den) og oppretter/lukker åpne punkter som `Agent`-merkede Issues via `book issues`.
