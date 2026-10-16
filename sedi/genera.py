#!/usr/bin/env python3
"""Genera le pagine delle sedi Gruppo Agila a partire da sedi.json.

Uso:  python3 sedi/genera.py

Per ogni sede produce in sedi/output/:
  - wordpress/<slug>.html   contenuto da incollare in un blocco "HTML personalizzato"
  - anteprima/<slug>.html   pagina completa da aprire nel browser per controllo
e inoltre la pagina indice "Le nostre sedi" e seo.md con titoli e meta description.
"""
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

BASE = Path(__file__).resolve().parent
OUT = BASE / "output"
SEGNAPOSTO = "[DA COMPILARE"

GIORNI = [("Mo", "Lunedì"), ("Tu", "Martedì"), ("We", "Mercoledì"), ("Th", "Giovedì"),
          ("Fr", "Venerdì"), ("Sa", "Sabato"), ("Su", "Domenica")]
GIORNI_SCHEMA = {"Mo": "Monday", "Tu": "Tuesday", "We": "Wednesday", "Th": "Thursday",
                 "Fr": "Friday", "Sa": "Saturday", "Su": "Sunday"}

SERVIZI = [
    ("👵", "Badanti a {citta}",
     "Assistenza ad anziani e persone non autosufficienti: badanti conviventi o a ore, "
     "scelte in base alle reali esigenze della persona da assistere e della famiglia."),
    ("🏠", "Colf a {citta}",
     "Collaboratrici domestiche per pulizie, stiro e gestione della casa, "
     "a tempo pieno o part-time."),
    ("🧸", "Babysitter a {citta}",
     "Babysitter affidabili per bambini di ogni età: tutti i giorni, "
     "dopo la scuola o quando ti serve."),
    ("📄", "Gestione contratti e buste paga",
     "Assunzione secondo il CCNL del lavoro domestico, buste paga, contributi INPS, "
     "TFR e cessazioni: pensiamo a tutto noi, senza pensieri per la famiglia."),
]

PASSI = [
    ("Contattaci", "Chiama, scrivi su WhatsApp o vieni nella sede di {citta}."),
    ("Analisi delle esigenze", "Ascoltiamo la famiglia e definiamo insieme il profilo ideale."),
    ("Selezione e colloqui", "Ti presentiamo candidati selezionati, con referenze verificate."),
    ("Inserimento e contratto", "Gestiamo assunzione e adempimenti e restiamo al tuo fianco."),
]


def compilato(valore):
    return bool(valore) and SEGNAPOSTO not in str(valore)


def e(testo):
    return html.escape(str(testo), quote=True)


def solo_cifre(numero):
    return re.sub(r"\D", "", numero or "")


def href_tel(numero):
    return "tel:+" + solo_cifre(numero) if compilato(numero) else "#contatti"


def href_whatsapp(numero, citta):
    if not compilato(numero):
        return "#contatti"
    testo = f"Buongiorno, vorrei informazioni sui vostri servizi a {citta}."
    return f"https://wa.me/{solo_cifre(numero)}?text={quote(testo)}"


def url_sede(az, sede):
    return az["sito"].rstrip("/") + az["percorso_sedi"] + sede["slug"] + "/"


def url_indice(az):
    return az["sito"].rstrip("/") + az["percorso_sedi"]


def indirizzo_completo(sede):
    return f'{sede["indirizzo"]}, {sede["cap"]} {sede["citta"]} ({sede["provincia"]})'


def orari_per_giorno(orari):
    """Restituisce [(nome giorno, "09:00–13:00, 14:30–18:30" | "Chiuso"), ...]."""
    righe = []
    for codice, nome in GIORNI:
        fasce = [f'{f["apre"]}–{f["chiude"]}' for f in orari if codice in f["giorni"]]
        righe.append((nome, ", ".join(fasce) if fasce else "Chiuso"))
    return righe


def faq(az, sede):
    citta = sede["citta"]
    zone = [z for z in sede["zone_servite"] if compilato(z)]
    dintorni = f" come {', '.join(zone)}" if zone else ""
    orari = "; ".join(f"{g} {o}" for g, o in orari_per_giorno(sede["orari"]) if o != "Chiuso")
    return [
        (f"Come posso trovare una badante a {citta}?",
         f"Contatta la sede {az['nome']} di {citta} per telefono, su WhatsApp o tramite il modulo "
         "di contatto: fissiamo un primo colloquio per capire le esigenze della persona da "
         "assistere e ti proponiamo profili selezionati e referenziati."),
        (f"Cercate anche colf e babysitter a {citta} e dintorni?",
         "Sì. Oltre alle badanti selezioniamo collaboratrici domestiche (colf) e babysitter "
         f"per le famiglie di {citta} e dei comuni vicini{dintorni}."),
        ("Vi occupate anche del contratto e delle buste paga?",
         "Sì: gestiamo l'assunzione nel rispetto del CCNL del lavoro domestico, le buste paga, "
         "i contributi INPS e le pratiche di fine rapporto, così la famiglia non deve pensare "
         "alla burocrazia."),
        (f"Serve un appuntamento per venire nella sede di {citta}?",
         "Ti consigliamo di chiamarci prima: così il referente può dedicarti tutto il tempo "
         f"necessario. Siamo aperti: {orari}."),
    ]


def json_ld(az, sede, domande):
    url = url_sede(az, sede)
    agenzia = {
        "@type": "EmploymentAgency",
        "@id": url + "#sede",
        "name": f'{az["nome"]} - {sede["citta"]}',
        "url": url,
        "parentOrganization": {"@type": "Organization", "name": az["nome"], "url": az["sito"]},
        "address": {
            "@type": "PostalAddress",
            "streetAddress": sede["indirizzo"],
            "postalCode": sede["cap"],
            "addressLocality": sede["citta"],
            "addressRegion": sede["provincia"],
            "addressCountry": "IT",
        },
        "openingHoursSpecification": [
            {"@type": "OpeningHoursSpecification",
             "dayOfWeek": [GIORNI_SCHEMA[g] for g in f["giorni"]],
             "opens": f["apre"], "closes": f["chiude"]}
            for f in sede["orari"]
        ],
        "areaServed": [{"@type": "City", "name": c}
                       for c in [sede["citta"], *sede["zone_servite"]] if compilato(c)],
        "knowsAbout": ["Badanti", "Colf", "Babysitter", "Lavoro domestico"],
    }
    if compilato(sede["telefono"]):
        agenzia["telephone"] = sede["telefono"]
    if compilato(sede["email"]):
        agenzia["email"] = sede["email"]
    if compilato(az["logo"]):
        agenzia["image"] = az["logo"]
        agenzia["logo"] = az["logo"]
    if compilato(sede["google_business_url"]):
        agenzia["sameAs"] = [sede["google_business_url"]]
    if sede["lat"] and sede["lng"]:
        agenzia["geo"] = {"@type": "GeoCoordinates",
                          "latitude": float(sede["lat"]), "longitude": float(sede["lng"])}
    # Indirizzo incompleto: meglio non dichiararlo a Google che dichiararlo sbagliato.
    if not all(compilato(agenzia["address"][k]) for k in ("streetAddress", "postalCode", "addressLocality")):
        del agenzia["address"]

    briciole = {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": az["sito"]},
            {"@type": "ListItem", "position": 2, "name": "Le nostre sedi", "item": url_indice(az)},
            {"@type": "ListItem", "position": 3, "name": sede["citta"], "item": url},
        ],
    }
    domande_ld = {
        "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": d,
                        "acceptedAnswer": {"@type": "Answer", "text": r}} for d, r in domande],
    }
    dati = {"@context": "https://schema.org", "@graph": [agenzia, briciole, domande_ld]}
    testo = json.dumps(dati, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return f'<script type="application/ld+json">\n{testo}\n</script>'


def blocco_form(az, sede):
    if az.get("form_shortcode"):
        return f'<div class="ga-form">{az["form_shortcode"]}</div>'
    link = f'{az["pagina_contatti"]}?sede={quote(sede["slug"])}'
    return (f'<p><a class="ga-btn ga-btn-accento" href="{e(link)}" data-evento="richiesta_preventivo" '
            f'data-sede="{e(sede["slug"])}">Richiedi un colloquio gratuito</a></p>')


def pulsanti(sede, chiaro=False):
    tel, wa = href_tel(sede["telefono"]), href_whatsapp(sede["whatsapp"], sede["citta"])
    stile_tel = "ga-btn-chiaro" if chiaro else "ga-btn-bordo"
    slug = e(sede["slug"])
    return f"""<div class="ga-cta-riga">
  <a class="ga-btn {stile_tel}" href="{e(tel)}" data-evento="chiamata" data-sede="{slug}">📞 Chiama {e(sede["telefono"]) if compilato(sede["telefono"]) else "la sede"}</a>
  <a class="ga-btn ga-btn-whatsapp" href="{e(wa)}" target="_blank" rel="noopener" data-evento="whatsapp" data-sede="{slug}">💬 Scrivici su WhatsApp</a>
  <a class="ga-btn ga-btn-accento" href="#contatti" data-evento="vai_contatti" data-sede="{slug}">Richiedi un colloquio gratuito</a>
</div>"""


def pagina_sede(az, sede, tutte):
    citta, slug = sede["citta"], sede["slug"]
    domande = faq(az, sede)
    forza = "\n".join(f"    <li>{e(p.format(citta=citta))}</li>" for p in az["punti_di_forza"])
    servizi = "\n".join(
        f'    <div class="ga-card"><span class="ga-icona" aria-hidden="true">{i}</span>'
        f"<h3>{e(t.format(citta=citta))}</h3><p>{e(d)}</p></div>"
        for i, t, d in SERVIZI)
    passi = "\n".join(f"    <li><h3>{e(t)}</h3><p>{e(d.format(citta=citta))}</p></li>" for t, d in PASSI)
    zone = "\n".join(f"    <li>{e(z)}</li>" for z in sede["zone_servite"])
    orari = "\n".join(f"        <tr><td>{g}</td><td>{e(o)}</td></tr>" for g, o in orari_per_giorno(sede["orari"]))
    domande_html = "\n".join(f"    <details><summary>{e(d)}</summary><p>{e(r)}</p></details>" for d, r in domande)
    altre = "\n".join(
        f'    <li><a href="{e(url_sede(az, s))}">{e(az["nome"])} {e(s["citta"])}</a></li>'
        for s in tutte if s is not sede)

    if compilato(sede["indirizzo"]) and compilato(sede["citta"]):
        mappa = (f'<iframe class="ga-mappa" title="Mappa sede {e(az["nome"])} {e(citta)}" loading="lazy" '
                 f'referrerpolicy="no-referrer-when-downgrade" '
                 f'src="https://www.google.com/maps?q={quote(az["nome"] + ", " + indirizzo_completo(sede))}&amp;output=embed"></iframe>')
    else:
        mappa = '<div class="ga-mappa ga-tenue" style="display:grid;place-items:center">Mappa: inserire l\'indirizzo in sedi.json</div>'

    referente = (f'\n        <dt>Referente</dt><dd>{e(sede["referente"])}</dd>'
                 if sede["referente"] else "")
    recensioni = (f'\n      <p><a href="{e(sede["google_business_url"])}" target="_blank" rel="noopener">'
                  f"Indicazioni stradali e recensioni su Google →</a></p>"
                  if compilato(sede["google_business_url"]) else "")

    return f"""<div class="ga-sede">
<div class="ga-wrap">

<nav class="ga-breadcrumb" aria-label="Percorso">
  <ol>
    <li><a href="{e(az["sito"])}">Home</a></li>
    <li><a href="{e(url_indice(az))}">Le nostre sedi</a></li>
    <li aria-current="page">{e(citta)}</li>
  </ol>
</nav>

<header class="ga-hero">
  <div class="ga-wrap">
    <h1>Badanti, Colf e Babysitter a {e(citta)}</h1>
    <p class="ga-sottotitolo">{e(az["nome"])} {e(citta)}: troviamo la persona giusta per la tua famiglia e gestiamo contratto e buste paga al posto tuo.</p>
    {pulsanti(sede, chiaro=True)}
    <ul class="ga-badge-lista">
{forza}
    </ul>
  </div>
</header>

<section>
  <h2>La sede {e(az["nome"])} di {e(citta)}</h2>
  <p>{e(sede["intro"])}</p>
  <p>{e(az["autorizzazione"])}.</p>
</section>

<section>
  <h2>I nostri servizi a {e(citta)}</h2>
  <div class="ga-griglia">
{servizi}
  </div>
</section>

<section class="ga-tenue">
  <div class="ga-wrap">
  <h2>Come funziona</h2>
  <ol class="ga-passi">
{passi}
  </ol>
  </div>
</section>

<section>
  <h2>Zone servite dalla sede di {e(citta)}</h2>
  <p>Aiutiamo le famiglie di {e(citta)} e dei comuni vicini:</p>
  <ul class="ga-zone">
    <li>{e(citta)}</li>
{zone}
  </ul>
</section>

<section id="contatti">
  <h2>Contatti e orari della sede di {e(citta)}</h2>
  <div class="ga-contatti">
    <div class="ga-card">
      <dl>
        <dt>Indirizzo</dt><dd>{e(indirizzo_completo(sede))}</dd>
        <dt>Telefono</dt><dd><a href="{e(href_tel(sede["telefono"]))}" data-evento="chiamata" data-sede="{e(slug)}">{e(sede["telefono"])}</a></dd>
        <dt>WhatsApp</dt><dd><a href="{e(href_whatsapp(sede["whatsapp"], citta))}" target="_blank" rel="noopener" data-evento="whatsapp" data-sede="{e(slug)}">{e(sede["whatsapp"])}</a></dd>
        <dt>Email</dt><dd><a href="mailto:{e(sede["email"])}" data-evento="email" data-sede="{e(slug)}">{e(sede["email"])}</a></dd>{referente}
        <dt>Come raggiungerci</dt><dd>{e(sede["come_raggiungerci"])}</dd>
      </dl>
      <h3 style="margin-top:20px">Orari di apertura</h3>
      <table class="ga-orari">
{orari}
      </table>
    </div>
    <div>
      {mappa}{recensioni}
      <h3 style="margin-top:20px">Preferisci essere ricontattato?</h3>
      {blocco_form(az, sede)}
    </div>
  </div>
</section>

<section class="ga-faq">
  <h2>Domande frequenti</h2>
{domande_html}
</section>

<section>
  <h2>Le altre sedi {e(az["nome"])}</h2>
  <ul>
{altre}
  </ul>
</section>

<div class="ga-cta-finale">
  <h2>Cerchi una badante, una colf o una babysitter a {e(citta)}?</h2>
  <p>Parlane con noi: il primo colloquio è senza impegno.</p>
  {pulsanti(sede, chiaro=True)}
</div>

</div>

<nav class="ga-barra-mobile" aria-label="Contatti rapidi">
  <a href="{e(href_tel(sede["telefono"]))}" data-evento="chiamata" data-sede="{e(slug)}">📞 Chiama</a>
  <a href="{e(href_whatsapp(sede["whatsapp"], citta))}" target="_blank" rel="noopener" data-evento="whatsapp" data-sede="{e(slug)}">💬 WhatsApp</a>
</nav>
</div>

{json_ld(az, sede, domande)}
"""


def pagina_indice(az, sedi):
    schede = "\n".join(f"""    <div class="ga-card">
      <h3>{e(az["nome"])} {e(s["citta"])}</h3>
      <p>{e(indirizzo_completo(s))}<br>
      <a href="{e(href_tel(s["telefono"]))}" data-evento="chiamata" data-sede="{e(s["slug"])}">{e(s["telefono"])}</a></p>
      <p><a class="ga-btn ga-btn-bordo" href="{e(url_sede(az, s))}">Scopri la sede di {e(s["citta"])}</a></p>
    </div>""" for s in sedi)
    citta = ", ".join(s["citta"] for s in sedi)
    return f"""<div class="ga-sede">
<div class="ga-wrap">

<header class="ga-hero">
  <div class="ga-wrap">
    <h1>Le sedi {e(az["nome"])}</h1>
    <p class="ga-sottotitolo">Badanti, colf e babysitter vicino a te: siamo presenti a {e(citta)}. Scegli la sede più comoda e contattaci per un primo colloquio senza impegno.</p>
  </div>
</header>

<section>
  <div class="ga-griglia">
{schede}
  </div>
</section>

</div>
</div>
"""


def anteprima(titolo, descrizione, contenuto, css):
    return f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titolo)}</title>
<meta name="description" content="{e(descrizione)}">
<style>body{{margin:0;background:#fff;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}</style>
<style>
{css}</style>
</head>
<body>
{contenuto}
</body>
</html>
"""


def seo(az, sede):
    c = sede["citta"]
    return (f'Badanti, Colf e Babysitter a {c} | {az["nome"]}',
            f'Cerchi una badante, una colf o una babysitter a {c}? {az["nome"]} seleziona personale '
            f'referenziato e gestisce contratto e buste paga. Chiamaci o scrivici su WhatsApp.')


def segnaposto_mancanti(dati):
    mancanti = []

    def visita(nodo, percorso):
        if isinstance(nodo, dict):
            for k, v in nodo.items():
                visita(v, f"{percorso}.{k}" if percorso else k)
        elif isinstance(nodo, list):
            for i, v in enumerate(nodo):
                visita(v, f"{percorso}[{i}]")
        elif isinstance(nodo, str) and SEGNAPOSTO in nodo:
            mancanti.append(percorso)

    visita(dati, "")
    return mancanti


def main():
    dati = json.loads((BASE / "sedi.json").read_text(encoding="utf-8"))
    az, sedi = dati["azienda"], dati["sedi"]
    css = (BASE / "stile.css").read_text(encoding="utf-8")
    (OUT / "wordpress").mkdir(parents=True, exist_ok=True)
    (OUT / "anteprima").mkdir(parents=True, exist_ok=True)

    righe_seo = ["# Impostazioni SEO (Yoast / Rank Math)", "",
                 f'Pagina madre: **Le nostre sedi** — slug `{az["percorso_sedi"].strip("/")}`', ""]
    pagine = [(s["slug"], pagina_sede(az, s, sedi), *seo(az, s), s) for s in sedi]
    titolo_indice = f'Le nostre sedi | {az["nome"]} - Badanti, Colf e Babysitter'
    descr_indice = (f'Le sedi {az["nome"]} a {", ".join(s["citta"] for s in sedi)}: '
                    "badanti, colf e babysitter selezionati vicino a te. Contatta la sede più comoda.")
    pagine.insert(0, ("le-nostre-sedi", pagina_indice(az, sedi), titolo_indice, descr_indice, None))

    for nome, contenuto, titolo, descr, sede in pagine:
        (OUT / "wordpress" / f"{nome}.html").write_text(f"<style>\n{css}</style>\n{contenuto}", encoding="utf-8")
        (OUT / "anteprima" / f"{nome}.html").write_text(anteprima(titolo, descr, contenuto, css), encoding="utf-8")
        righe_seo += [f"## {titolo}", "",
                      f'- Slug WordPress: `{sede["slug"] if sede else az["percorso_sedi"].strip("/")}`'
                      + (" (pagina figlia di *Le nostre sedi*)" if sede else ""),
                      f"- Titolo SEO: {titolo}",
                      f"- Meta description: {descr}"]
        if sede:
            righe_seo.append(f'- Parola chiave principale: badanti {sede["citta"]}')
        righe_seo.append("")
    (OUT / "seo.md").write_text("\n".join(righe_seo), encoding="utf-8")

    print(f"Generate {len(pagine)} pagine in {OUT.relative_to(BASE.parent)}/")
    mancanti = segnaposto_mancanti(dati)
    if mancanti:
        print(f"\nAttenzione: {len(mancanti)} campi ancora da compilare in sedi.json:", file=sys.stderr)
        for m in mancanti:
            print(f"  - {m}", file=sys.stderr)


if __name__ == "__main__":
    main()
