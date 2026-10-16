# Sito Gruppo Agila – Pagine delle sedi

Pagine locali per le 3 sedi di **Gruppo Agila** (badanti, colf, babysitter, gestione contratti),
pensate per WordPress e ottimizzate per portare contatti: chiamate, WhatsApp e richieste di colloquio.

## Cosa contiene

| File | A cosa serve |
|---|---|
| `sedi/sedi.json` | **Unico file da compilare**: indirizzi, telefoni, orari, zone servite, testi di ogni sede |
| `sedi/genera.py` | Rigenera tutte le pagine da `sedi.json` |
| `sedi/stile.css` | Grafica delle pagine (colori modificabili in cima al file) |
| `sedi/output/wordpress/` | Codice da incollare in WordPress (1 file per pagina) |
| `sedi/output/anteprima/` | Le stesse pagine da aprire nel browser per un controllo |
| `sedi/output/seo.md` | Slug, titolo SEO e meta description per Yoast / Rank Math |

Ogni pagina sede contiene: titolo locale ("Badanti, Colf e Babysitter a *Città*"), pulsanti
Chiama / WhatsApp / Colloquio gratuito, servizi, come funziona, zone servite, contatti con orari
e mappa Google, domande frequenti, link alle altre sedi e una barra contatti fissa su smartphone.
In fondo c'è il codice di dati strutturati (schema.org `EmploymentAgency`, `BreadcrumbList`,
`FAQPage`) che aiuta Google a mostrare la sede nelle ricerche locali.

## 1. Compilare i dati

Aprire `sedi/sedi.json` e sostituire ogni testo `[DA COMPILARE: ...]`. Consigli:

- `slug`: il nome della pagina nell'indirizzo, es. `varese` → `gruppoagila.it/sedi/varese/`.
- `intro`: scrivere un testo **diverso per ogni sede** (Google penalizza pagine quasi identiche).
- `zone_servite`: elencare i comuni vicini: le persone cercano "badante + nome del paese".
- Indirizzo e telefono devono essere **identici** a quelli della scheda Google Business della sede.
- `form_shortcode` (facoltativo): incollare lo shortcode del modulo contatti, es.
  `[contact-form-7 id="123" title="Contatti"]`. Se vuoto, il pulsante porta a `pagina_contatti`.

Poi rigenerare le pagine:

```bash
python3 sedi/genera.py
```

Lo script elenca i campi ancora da compilare.

## 2. Pubblicare su WordPress

1. **Pagine → Aggiungi nuova**, titolo *Le nostre sedi*, slug `sedi`.
   Aggiungere un blocco **HTML personalizzato** e incollare il contenuto di
   `sedi/output/wordpress/le-nostre-sedi.html`. Pubblicare.
2. Per ogni sede: nuova pagina, impostare **Genitore = Le nostre sedi** e lo slug indicato in
   `seo.md`, blocco **HTML personalizzato**, incollare il file `sedi/output/wordpress/<slug>.html`.
3. In Yoast / Rank Math copiare titolo SEO e meta description da `seo.md`.
4. Aggiungere *Le nostre sedi* al menu principale e al footer.
5. Nella scheda Google Business di ogni sede inserire come sito web il link alla pagina della sede.

## Misurare i contatti

Tutti i pulsanti hanno gli attributi `data-evento` (`chiamata`, `whatsapp`, `email`,
`richiesta_preventivo`) e `data-sede`. In Google Tag Manager si può creare un attivatore
"Clic – Tutti gli elementi" su questi attributi per contare in GA4 quanti contatti arrivano
da ciascuna sede.
