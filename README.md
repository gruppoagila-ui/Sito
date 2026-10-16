# Sito Gruppo Agila – Pagine delle sedi

Pagine locali per le 3 sedi di **Gruppo Agila** (Udine, Pordenone, Trieste), pensate per
WordPress. Servono come pagine di destinazione delle campagne **Google Ads** e sono ottimizzate
per la **SEO locale**.

| Pagina | URL | Telefono |
|---|---|---|
| Le nostre sedi | https://www.gruppoagila.it/sedi/ | – |
| Udine | https://www.gruppoagila.it/sedi/udine/ | 0432 681739 |
| Pordenone | https://www.gruppoagila.it/sedi/pordenone/ | 0434 1754524 |
| Trieste | https://www.gruppoagila.it/sedi/trieste/ | 040 2034844 |

## Cosa contiene

| File | A cosa serve |
|---|---|
| `sedi/sedi.json` | Dati e testi di ogni sede: indirizzi, telefoni, orari, zone servite |
| `sedi/genera.py` | Rigenera tutte le pagine da `sedi.json` (`python3 sedi/genera.py`) |
| `sedi/stile.css` | Grafica delle pagine (colori modificabili in cima al file) |
| `sedi/output/wordpress/` | **Codice da incollare in WordPress** (1 file per pagina) |
| `sedi/output/anteprima/` | Le stesse pagine da aprire nel browser per un controllo |
| `sedi/output/seo.md` | Slug, titolo SEO, meta description e parole chiave |

## Struttura di ogni pagina sede

1. **Intestazione**: titolo con la parola chiave ("Agenzia Badanti, Colf e Babysitter a *Città*"),
   punti di forza e riquadro **Consulenza gratuita** con chiamata, WhatsApp ed email, visibile
   senza scorrere la pagina.
2. Numeri chiave (dal 1987, oltre 2.000 famiglie, 24–48 ore nei casi urgenti, consulenza gratuita).
3. Testo unico sulla sede, servizi, box **urgenze** (dimissione ospedaliera), come funziona.
4. **Zone servite**: comuni e quartieri vicini, per comparire nelle ricerche "badante + paese".
5. Contributi regionali FVG, contatti con orari e mappa, 6 domande frequenti, link alle altre sedi.
6. Su smartphone: barra fissa in basso con **Chiama** e **WhatsApp**.
7. Dati strutturati schema.org (`EmploymentAgency`, `BreadcrumbList`, `FAQPage`) per Google.

## Pubblicare su WordPress

1. **Pagine → Aggiungi nuova**, titolo *Le nostre sedi*, slug `sedi`. Aggiungere un blocco
   **HTML personalizzato** e incollare `sedi/output/wordpress/le-nostre-sedi.html`. Pubblicare.
2. Per ogni sede: nuova pagina, **Genitore = Le nostre sedi**, slug `udine` / `pordenone` /
   `trieste`, blocco **HTML personalizzato** con il file corrispondente.
3. In Yoast / Rank Math copiare titolo SEO e meta description da `sedi/output/seo.md`.
4. Se il tema lo consente, scegliere un modello di pagina **a larghezza piena**.
5. Aggiungere *Le nostre sedi* al menu e al footer, e collegare le pagine già esistenti
   (`/badanti-udine/`, `/badanti-pordenone-servizi/`…) alla pagina della sede corrispondente.

## Google Ads

- **Una campagna (o un gruppo di annunci) per sede**, con URL finale alla pagina della sede e
  targeting geografico sul raggio servito da quella sede.
- Parole chiave suggerite per ogni città in `seo.md` (es. *agenzia badanti udine*,
  *badante convivente trieste*, *colf pordenone*).
- Estensioni: **località** (collegando il profilo Google Business), **chiamata** con il numero
  della sede e sitelink verso le altre pagine sede.

### Misurare le conversioni

Ogni clic su telefono, WhatsApp, email, indicazioni e richiesta di contatto invia l'evento
`contatto_sede` con due parametri:

- `tipo_contatto`: `chiamata`, `chiamata_urgente`, `whatsapp`, `email`, `indicazioni`, `richiesta_contatto`
- `sede`: `udine`, `pordenone`, `trieste`

L'evento arriva sia a **Google Tag Manager** (`dataLayer`) sia a **gtag.js**, se presente.

- **Con gtag.js / Site Kit**: in GA4 segnare `contatto_sede` come *evento chiave* e importarlo
  in Google Ads come conversione.
- **Con Tag Manager**: creare un attivatore *Evento personalizzato* `contatto_sede` e un tag
  GA4 o Google Ads collegato. In questo caso non creare anche la conversione da gtag, per non
  contare due volte lo stesso contatto.

## Dati da verificare

- Il **WhatsApp** è il numero di Udine (0432 681739) su tutte le sedi, come indicato sul sito.
- **Sabato** 9–13 "su appuntamento": sul sito alcune pagine lo indicano senza appuntamento.
- Il **modulo contatti**: se esiste uno shortcode (Contact Form 7, WPForms…), inserirlo in
  `form_shortcode` di `sedi.json` e rigenerare: comparirà nel riquadro in alto.
- Aggiungere in `sedi.json` il link alla scheda **Google Business** di ogni sede
  (`google_business_url`) e il logo (`logo`).
