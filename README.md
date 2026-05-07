# Finn-scraping test

En minimal test som henter 3 prosjektsider fra Finn.no og rapporterer hva som faktisk finnes i HTML-en. Formålet er å avgjøre om automatisert scraping av Finn er gjennomførbart fra GitHub Actions før vi bygger en full løsning.

## Mulige utfall

**Suksess (3/3):** Finn returnerer normal HTML, parser finner enheter med pris og BRA. Trygt å bygge full løsning.

**Delvis (1-2/3):** Variabel struktur eller blokkering på enkelte sider. Kan løses, men trenger mer arbeid.

**Feilet (0/3):** Finn blokkerer, returnerer Cloudflare-utfordring, eller har endret struktur. Vi må enten gi opp Finn-scraping eller bruke avansert anti-bot-omgåelse (Playwright med stealth, residential proxies — som bryter ToS).

## Kjøring

Kun manuell — gå til Actions-fanen → "Finn-scraping test" → "Run workflow".

## Tolkning

Loggen viser HTTP-status, sidestørrelse, sidetittel, og første 3 enheter fra hver side. Hvis det står "BOT-VEGG" et sted, er det dårlige nyheter.
