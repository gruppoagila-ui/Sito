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
     "Badanti conviventi H24 o a ore per anziani e persone non autosufficienti, "
     "scelte in base alle reali necessità della persona da assistere e della famiglia."),
    ("🏠", "Colf a {citta}",
     "Collaboratrici domestiche conviventi o a ore per pulizie, stiro e gestione della casa, "
     "a tempo pieno o part-time."),
    ("🧸", "Babysitter a {citta}",
     "Babysitter affidabili per bambini di ogni età: tutti i giorni, "
     "dopo la scuola o quando ti serve."),
    ("📄", "Contratto e pratiche",
     "Ti seguiamo nell'assunzione secondo il CCNL del lavoro domestico: contratto, "
     "buste paga, contributi INPS e pratiche di fine rapporto."),
]

PASSI = [
    ("Contattaci", "Chiama, scrivi su WhatsApp o vieni nella sede di {citta}: la prima consulenza è gratuita."),
    ("Analisi delle esigenze", "Ascoltiamo la famiglia e definiamo insieme il profilo ideale."),
    ("Selezione e colloqui", "Ti presentiamo candidati selezionati, con referenze verificate."),
    ("Inserimento e contratto", "Ci occupiamo delle pratiche di assunzione e restiamo al tuo fianco."),
]

# Invia ogni clic su telefono, WhatsApp, email e modulo a Google Tag Manager (dataLayer)
# e, se presente, a gtag.js: serve per misurare le conversioni di Google Ads per sede.
SCRIPT_TRACCIAMENTO = """<script>
(function () {
  if (window.gaSedeTracciamento) return;
  window.gaSedeTracciamento = true;
  document.addEventListener('click', function (ev) {
    var a = ev.target.closest && ev.target.closest('.ga-sede [data-evento]');
    if (!a) return;
    var dati = { tipo_contatto: a.getAttribute('data-evento'), sede: a.getAttribute('data-sede') };
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push(Object.assign({ event: 'contatto_sede' }, dati));
    if (typeof window.gtag === 'function') window.gtag('event', 'contatto_sede', dati);
  });
})();
</script>"""


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
        fasce = [f'{f["apre"]}–{f["chiude"]}' + (f' ({f["nota"]})' if f.get("nota") else "")
                 for f in sede_orari_giorno(orari, codice)]
        righe.append((nome, ", ".join(fasce) if fasce else "Chiuso"))
    return righe


def sede_orari_giorno(orari, codice):
    return [f for f in orari if codice in f["giorni"]]


def orari_brevi(orari):
    """Riassunto per l'intestazione, es. "Lun–Ven 09:00–13:00 e 14:30–18:30"."""
    feriali = [f'{f["apre"]}–{f["chiude"]}' for f in sede_orari_giorno(orari, "Mo") if not f.get("nota")]
    return "Lun–Ven " + " e ".join(feriali) if feriali else ""


def faq(az, sede):
    citta = sede["citta"]
    zone = [z for z in sede["zone_servite"] if compilato(z)][:6]
    dintorni = f", ad esempio {', '.join(zone)}" if zone else ""
    orari = "; ".join(f"{g} {o}" for g, o in orari_per_giorno(sede["orari"]) if o != "Chiuso")
    return [
        (f"Come posso trovare una badante a {citta}?",
         f"Contatta la sede {az['nome']} di {citta} per telefono, su WhatsApp o via email: la prima "
         "consulenza è gratuita. Valutiamo insieme le necessità della persona da assistere e ti "
         "proponiamo profili selezionati e referenziati."),
        ("Cosa succede in caso di urgenza, ad esempio una dimissione ospedaliera improvvisa?",
         "Attiviamo una ricerca prioritaria per trovare una soluzione temporanea in 24–48 ore. "
         "Nei casi urgenti puoi contattarci anche fuori dagli orari d'ufficio al numero principale."),
        (f"Seguite anche le famiglie fuori {citta}?",
         f"Sì: dalla sede di {citta} seguiamo anche le famiglie dei comuni e delle zone vicine{dintorni}."),
        ("Chi è il datore di lavoro della badante o della colf?",
         "Il contratto viene firmato direttamente tra la famiglia e la lavoratrice, nel rispetto del "
         "CCNL del lavoro domestico. Noi ti seguiamo in tutte le pratiche, così non devi pensare "
         "alla burocrazia."),
        ("Esistono contributi regionali per pagare la badante?",
         "In Friuli Venezia Giulia sono previsti contributi regionali per le famiglie che assumono "
         "un assistente familiare. Ti aiutiamo a capire quali puoi richiedere."),
        (f"Serve un appuntamento per venire nella sede di {citta}?",
         f"Ti consigliamo di chiamarci prima: così possiamo dedicarti tutto il tempo necessario. "
         f"Orari: {orari}."),
    ]


def json_ld(az, sede, domande):
    url = url_sede(az, sede)
    agenzia = {
        "@type": "EmploymentAgency",
        "@id": url + "#sede",
        "name": f'{az["nome"]} {sede["citta"]} - Badanti, Colf e Babysitter',
        "url": url,
        "telephone": sede["telefono"],
        "email": sede["email"],
        "parentOrganization": {"@type": "Organization", "name": az["nome"], "url": az["sito"]},
        "address": {
            "@type": "PostalAddress",
            "streetAddress": sede["indirizzo"],
            "postalCode": sede["cap"],
            "addressLocality": sede["citta"],
            "addressRegion": sede["provincia"],
            "addressCountry": "IT",
        },
        # Gli orari "su appuntamento" non sono orari di apertura effettivi: restano fuori dallo schema.
        "openingHoursSpecification": [
            {"@type": "OpeningHoursSpecification",
             "dayOfWeek": [GIORNI_SCHEMA[g] for g in f["giorni"]],
             "opens": f["apre"], "closes": f["chiude"]}
            for f in sede["orari"] if not f.get("nota")
        ],
        "areaServed": [sede["citta"], *[z for z in sede["zone_servite"] if compilato(z)]],
        "knowsAbout": ["Badanti", "Badante convivente", "Colf", "Babysitter", "Lavoro domestico"],
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": f"Servizi a {sede['citta']}",
            "itemListElement": [
                {"@type": "Offer", "itemOffered": {"@type": "Service", "name": t.format(citta=sede["citta"])}}
                for _, t, _ in SERVIZI
            ],
        },
    }
    if compilato(az["logo"]):
        agenzia["image"] = az["logo"]
        agenzia["logo"] = az["logo"]
    if compilato(sede["google_business_url"]):
        agenzia["sameAs"] = [sede["google_business_url"]]
    if sede["lat"] and sede["lng"]:
        agenzia["geo"] = {"@type": "GeoCoordinates",
                          "latitude": float(sede["lat"]), "longitude": float(sede["lng"])}

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


def link_contatti(az, sede, etichetta, classe="ga-btn ga-btn-accento"):
    link = f'{az["pagina_contatti"]}?sede={quote(sede["slug"])}'
    return (f'<a class="{classe}" href="{e(link)}" data-evento="richiesta_contatto" '
            f'data-sede="{e(sede["slug"])}">{etichetta}</a>')


def box_contatto(az, sede):
    """Riquadro nell'intestazione: modulo se configurato, altrimenti contatti diretti."""
    slug, citta = e(sede["slug"]), sede["citta"]
    if az.get("form_shortcode"):
        corpo = f'<div class="ga-form">{az["form_shortcode"]}</div>'
    else:
        corpo = f"""<a class="ga-btn ga-btn-accento ga-btn-pieno" href="{e(href_tel(sede["telefono"]))}" data-evento="chiamata" data-sede="{slug}">📞 {e(sede["telefono"])}</a>
      <a class="ga-btn ga-btn-whatsapp ga-btn-pieno" href="{e(href_whatsapp(sede["whatsapp"], citta))}" target="_blank" rel="noopener" data-evento="whatsapp" data-sede="{slug}">💬 Scrivici su WhatsApp</a>
      <a class="ga-btn ga-btn-bordo ga-btn-pieno" href="mailto:{e(sede["email"])}?subject={quote("Richiesta informazioni - sede di " + citta)}" data-evento="email" data-sede="{slug}">✉️ {e(sede["email"])}</a>"""
    return f"""<aside class="ga-box-contatto" aria-label="Richiedi una consulenza gratuita">
      <p class="ga-box-titolo">Consulenza gratuita</p>
      <p class="ga-box-sottotitolo">Parla subito con la sede di {e(citta)}</p>
      {corpo}
      <p class="ga-box-nota">{e(orari_brevi(sede["orari"]))}<br>{e(indirizzo_completo(sede))}</p>
    </aside>"""


def pulsanti(sede):
    tel, wa = href_tel(sede["telefono"]), href_whatsapp(sede["whatsapp"], sede["citta"])
    slug = e(sede["slug"])
    return f"""<div class="ga-cta-riga">
    <a class="ga-btn ga-btn-chiaro" href="{e(tel)}" data-evento="chiamata" data-sede="{slug}">📞 Chiama {e(sede["telefono"])}</a>
    <a class="ga-btn ga-btn-whatsapp" href="{e(wa)}" target="_blank" rel="noopener" data-evento="whatsapp" data-sede="{slug}">💬 Scrivici su WhatsApp</a>
  </div>"""


def pagina_sede(az, sede, tutte):
    citta, slug = sede["citta"], sede["slug"]
    domande = faq(az, sede)
    forza = "\n".join(f"      <li>{e(p.format(citta=citta))}</li>" for p in az["punti_di_forza"])
    numeri = "\n".join(f'    <div class="ga-numero"><strong>{e(n)}</strong><span>{e(t)}</span></div>'
                       for n, t in az["numeri"])
    intro = "\n".join(f"  <p>{e(p)}</p>" for p in sede["intro"])
    servizi = "\n".join(
        f'    <div class="ga-card"><span class="ga-icona" aria-hidden="true">{i}</span>'
        f"<h3>{e(t.format(citta=citta))}</h3><p>{e(d)}</p></div>"
        for i, t, d in SERVIZI)
    passi = "\n".join(f"    <li><h3>{e(t)}</h3><p>{e(d.format(citta=citta))}</p></li>" for t, d in PASSI)
    zone = "\n".join(f"    <li>{e(z)}</li>" for z in sede["zone_servite"])
    orari = "\n".join(f"        <tr><td>{g}</td><td>{e(o)}</td></tr>" for g, o in orari_per_giorno(sede["orari"]))
    domande_html = "\n".join(f"  <details><summary>{e(d)}</summary><p>{e(r)}</p></details>" for d, r in domande)
    altre = "\n".join(
        f'    <li><a href="{e(url_sede(az, s))}">Badanti e colf a {e(s["citta"])}</a> – {e(indirizzo_completo(s))}</li>'
        for s in tutte if s is not sede)

    mappa = (f'<iframe class="ga-mappa" title="Mappa della sede {e(az["nome"])} di {e(citta)}" loading="lazy" '
             f'referrerpolicy="no-referrer-when-downgrade" '
             f'src="https://www.google.com/maps?q={quote(az["nome"] + ", " + indirizzo_completo(sede))}&amp;output=embed"></iframe>')
    indicazioni = sede["google_business_url"] if compilato(sede["google_business_url"]) else \
        f'https://www.google.com/maps/search/?api=1&query={quote(az["nome"] + " " + indirizzo_completo(sede))}'

    extra = ""
    if sede["referente"]:
        extra += f'\n        <dt>Referente</dt><dd>{e(sede["referente"])}</dd>'
    if sede["come_raggiungerci"]:
        extra += f'\n        <dt>Come raggiungerci</dt><dd>{e(sede["come_raggiungerci"])}</dd>'

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
  <div class="ga-hero-testo">
    <p class="ga-occhiello">{e(az["nome"])} · Sede di {e(citta)}</p>
    <h1>Agenzia Badanti, Colf e Babysitter a {e(citta)}</h1>
    <p class="ga-sottotitolo">Troviamo la persona giusta per assistere i tuoi cari a {e(citta)} e provincia e ti seguiamo in tutte le pratiche di assunzione. Prima consulenza gratuita.</p>
    <ul class="ga-badge-lista">
{forza}
    </ul>
  </div>
  {box_contatto(az, sede)}
</header>

<div class="ga-numeri">
{numeri}
</div>

<section>
  <h2>La sede {e(az["nome"])} di {e(citta)}</h2>
{intro}
  <p class="ga-tenue-testo">{e(az["autorizzazione"])}.</p>
</section>

<section>
  <h2>I nostri servizi a {e(citta)}</h2>
  <div class="ga-griglia">
{servizi}
  </div>
</section>

<div class="ga-urgenza">
  <div>
    <h2>Dimissione ospedaliera improvvisa o badante da sostituire?</h2>
    <p>Attiviamo una ricerca prioritaria per trovare una soluzione temporanea in 24–48 ore.</p>
  </div>
  <a class="ga-btn ga-btn-chiaro" href="{e(href_tel(sede["telefono"]))}" data-evento="chiamata_urgente" data-sede="{e(slug)}">📞 Chiama ora</a>
</div>

<section class="ga-tenue">
  <h2>Come funziona</h2>
  <ol class="ga-passi">
{passi}
  </ol>
</section>

<section>
  <h2>Zone servite dalla sede di {e(citta)}</h2>
  <p>Aiutiamo le famiglie di {e(citta)} e di queste zone:</p>
  <ul class="ga-zone">
{zone}
  </ul>
</section>

<section class="ga-tenue ga-contributi">
  <h2>Contributi regionali per l'assistenza in FVG</h2>
  <p>In Friuli Venezia Giulia le famiglie che assumono un assistente familiare possono accedere a contributi regionali. Ti aiutiamo a capire quali puoi richiedere.</p>
  <p><a class="ga-btn ga-btn-bordo" href="{e(az["pagina_contributi"])}">Scopri i contributi regionali</a></p>
</section>

<section id="contatti">
  <h2>Contatti e orari della sede di {e(citta)}</h2>
  <div class="ga-contatti">
    <div class="ga-card">
      <dl>
        <dt>Indirizzo</dt><dd>{e(az["nome"])}<br>{e(indirizzo_completo(sede))}</dd>
        <dt>Telefono</dt><dd><a href="{e(href_tel(sede["telefono"]))}" data-evento="chiamata" data-sede="{e(slug)}">{e(sede["telefono"])}</a></dd>
        <dt>WhatsApp</dt><dd><a href="{e(href_whatsapp(sede["whatsapp"], citta))}" target="_blank" rel="noopener" data-evento="whatsapp" data-sede="{e(slug)}">{e(sede["whatsapp"])}</a></dd>
        <dt>Email</dt><dd><a href="mailto:{e(sede["email"])}" data-evento="email" data-sede="{e(slug)}">{e(sede["email"])}</a></dd>{extra}
      </dl>
      <h3 class="ga-spazio-sopra">Orari di apertura</h3>
      <table class="ga-orari">
{orari}
      </table>
    </div>
    <div>
      {mappa}
      <p><a href="{e(indicazioni)}" target="_blank" rel="noopener" data-evento="indicazioni" data-sede="{e(slug)}">Indicazioni stradali e recensioni su Google →</a></p>
      <p>{link_contatti(az, sede, "Richiedi di essere ricontattato")}</p>
    </div>
  </div>
</section>

<section class="ga-faq">
  <h2>Domande frequenti sulla sede di {e(citta)}</h2>
{domande_html}
</section>

<section>
  <h2>Le altre sedi {e(az["nome"])} in Friuli Venezia Giulia</h2>
  <ul>
{altre}
  </ul>
</section>

<div class="ga-cta-finale">
  <h2>Cerchi una badante, una colf o una babysitter a {e(citta)}?</h2>
  <p>Parlane con noi: la prima consulenza è gratuita e senza impegno.</p>
  {pulsanti(sede)}
</div>

</div>

<nav class="ga-barra-mobile" aria-label="Contatti rapidi">
  <a href="{e(href_tel(sede["telefono"]))}" data-evento="chiamata" data-sede="{e(slug)}">📞 Chiama</a>
  <a href="{e(href_whatsapp(sede["whatsapp"], citta))}" target="_blank" rel="noopener" data-evento="whatsapp" data-sede="{e(slug)}">💬 WhatsApp</a>
</nav>
</div>

{json_ld(az, sede, domande)}
{SCRIPT_TRACCIAMENTO}
"""


def pagina_indice(az, sedi):
    schede = "\n".join(f"""    <div class="ga-card">
      <h2>{e(az["nome"])} {e(s["citta"])}</h2>
      <p>{e(indirizzo_completo(s))}<br>
      <a href="{e(href_tel(s["telefono"]))}" data-evento="chiamata" data-sede="{e(s["slug"])}">{e(s["telefono"])}</a><br>
      {e(orari_brevi(s["orari"]))}</p>
      <p><a class="ga-btn ga-btn-bordo" href="{e(url_sede(az, s))}">Badanti e colf a {e(s["citta"])}</a></p>
    </div>""" for s in sedi)
    citta = ", ".join(s["citta"] for s in sedi[:-1]) + " e " + sedi[-1]["citta"]
    numeri = "\n".join(f'    <div class="ga-numero"><strong>{e(n)}</strong><span>{e(t)}</span></div>'
                       for n, t in az["numeri"])
    return f"""<div class="ga-sede">
<div class="ga-wrap">

<header class="ga-hero ga-hero-singolo">
  <div class="ga-hero-testo">
    <h1>Le sedi {e(az["nome"])} in Friuli Venezia Giulia</h1>
    <p class="ga-sottotitolo">Badanti, colf e babysitter vicino a te: siamo presenti a {e(citta)} e seguiamo le famiglie delle province di Udine, Pordenone, Trieste e Gorizia. Scegli la sede più comoda e contattaci per una consulenza gratuita.</p>
  </div>
</header>

<div class="ga-numeri">
{numeri}
</div>

<section>
  <div class="ga-griglia">
{schede}
  </div>
</section>

</div>
</div>
{SCRIPT_TRACCIAMENTO}
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
    return (f'Agenzia Badanti {c} – Colf e Babysitter | {az["nome"]}',
            f'Cerchi una badante, una colf o una babysitter a {c}? {az["nome"]}, agenzia autorizzata '
            f'dal 1987: personale selezionato e pratiche gestite. Consulenza gratuita.')


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

    righe_seo = ["# Impostazioni SEO (Yoast / Rank Math) e Google Ads", ""]
    pagine = [(s["slug"], pagina_sede(az, s, sedi), *seo(az, s), s) for s in sedi]
    titolo_indice = f'Le nostre sedi in FVG: Udine, Pordenone, Trieste | {az["nome"]}'
    descr_indice = (f'Le sedi {az["nome"]} a {", ".join(s["citta"] for s in sedi)}: '
                    "badanti, colf e babysitter selezionati vicino a te. Consulenza gratuita.")
    pagine.insert(0, ("le-nostre-sedi", pagina_indice(az, sedi), titolo_indice, descr_indice, None))

    for nome, contenuto, titolo, descr, sede in pagine:
        (OUT / "wordpress" / f"{nome}.html").write_text(f"<style>\n{css}</style>\n{contenuto}", encoding="utf-8")
        (OUT / "anteprima" / f"{nome}.html").write_text(anteprima(titolo, descr, contenuto, css), encoding="utf-8")
        url = url_sede(az, sede) if sede else url_indice(az)
        righe_seo += [f"## {sede['citta'] if sede else 'Le nostre sedi'}", "",
                      f"- URL: {url}",
                      f'- Slug WordPress: `{sede["slug"] if sede else az["percorso_sedi"].strip("/")}`'
                      + (" (pagina figlia di *Le nostre sedi*)" if sede else ""),
                      f"- Titolo SEO: {titolo}",
                      f"- Meta description: {descr}"]
        if sede:
            c = sede["citta"].lower()
            righe_seo += [f"- Parola chiave principale: agenzia badanti {c}",
                          f"- Parole chiave correlate: badante {c}, badante convivente {c}, colf {c}, babysitter {c}"]
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
