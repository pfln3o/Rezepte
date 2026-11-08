"""MkDocs-Hook für die Rezeptsammlung.

* Startseite: baut aus allen Rezeptdateien automatisch Rezeptkarten je Kategorie
  (neue Rezepte erscheinen ohne weiteres Zutun) plus die Menüvorschläge aus der README.
* Rezeptseiten: macht aus der Eckdaten-Tabelle Infokacheln, rahmt Zutaten und
  Zubereitung ein und zeigt „Passt zu“ aus dem Frontmatter als Links an.
"""
import html
import os
import posixpath
import re

import yaml

REIHENFOLGE = ["hauptgerichte", "suppen", "salate", "beilagen", "saucen", "desserts", "backen", "getraenke"]
NAMEN = {"getraenke": "Getränke", "saucen": "Soßen"}
EMOJI = {
    "hauptgerichte": "🍲", "suppen": "🥣", "salate": "🥗", "beilagen": "🥔",
    "saucen": "🫙", "desserts": "🍰", "backen": "🥨", "getraenke": "🍹",
}
INFO_EMOJI = {
    "portionen": "🍽️", "vorbereitung": "🔪", "ruhezeit": "⏳", "garzeit": "🔥",
    "backzeit": "🔥", "kochzeit": "🔥", "gesamt": "⏱️", "schwierigkeit": "📊",
}
SCHWIERIGKEIT_EMOJI = {"einfach": "●○○", "mittel": "●●○", "anspruchsvoll": "●●●"}

FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def _lesen(pfad):
    with open(pfad, encoding="utf-8") as f:
        text = f.read()
    m = FRONTMATTER.match(text)
    meta = (yaml.safe_load(m.group(1)) or {}) if m else {}
    body = text[m.end():] if m else text
    h1 = re.search(r"^# (.+)$", body, re.M)
    meta.setdefault("titel", h1.group(1).strip() if h1 else os.path.basename(pfad))
    # erster normaler Absatz nach der Überschrift = Kurzbeschreibung
    nach_h1 = body[h1.end():] if h1 else body
    for absatz in re.split(r"\n\s*\n", nach_h1):
        absatz = absatz.strip()
        if absatz and not absatz.startswith(("|", "#", "-", "<", "1.")):
            meta["_beschreibung"] = re.sub(r"\s+", " ", absatz)
            break
    return meta


def _kurz(text, laenge=150):
    if len(text) <= laenge:
        return text
    return text[:laenge].rsplit(" ", 1)[0] + " …"


def _kategorie(ordner):
    return NAMEN.get(ordner, ordner.replace("-", " ").capitalize())


def _leer(wert):
    return wert in (None, "", "0 min", [])


# ---------------------------------------------------------------- Startseite

def _startseite(markdown, config):
    docs = config["docs_dir"]
    kategorien = {}
    for eintrag in sorted(os.listdir(docs)):
        ordner = os.path.join(docs, eintrag)
        if not os.path.isdir(ordner) or eintrag.startswith((".", "_")) or eintrag == "assets":
            continue
        rezepte = []
        for datei in sorted(os.listdir(ordner)):
            if datei.endswith(".md") and not datei.startswith("_"):
                meta = _lesen(os.path.join(ordner, datei))
                url = f"{eintrag}/{datei[:-3]}/"
                rezepte.append((str(meta["titel"]), url, meta))
        if rezepte:
            kategorien[eintrag] = sorted(rezepte, key=lambda r: r[0].lower())

    rang = {k: i for i, k in enumerate(REIHENFOLGE)}
    anzahl = sum(len(r) for r in kategorien.values())
    teile = [f'<p class="rezept-zaehler">{anzahl} Rezepte in {len(kategorien)} Kategorien</p>\n']
    for kat in sorted(kategorien, key=lambda k: (rang.get(k, 99), k)):
        emoji = EMOJI.get(kat, "🍴")
        teile.append(f'<h2 id="{kat}" class="kategorie-titel"><span aria-hidden="true">{emoji}</span> {_kategorie(kat)}</h2>\n')
        karten = []
        for titel, url, meta in kategorien[kat]:
            chips = []
            if not _leer(meta.get("gesamt")):
                chips.append(f"⏱️ {html.escape(str(meta['gesamt']))}")
            if not _leer(meta.get("portionen")):
                chips.append(f"🍽️ {html.escape(str(meta['portionen']))}")
            if not _leer(meta.get("schwierigkeit")):
                chips.append(html.escape(str(meta["schwierigkeit"])).capitalize())
            chip_html = "".join(f"<span>{c}</span>" for c in chips)
            beschreibung = html.escape(_kurz(meta.get("_beschreibung", "")))
            karten.append(
                f'<a class="rezept-karte" href="{url}">'
                f'<span class="rezept-karte__emoji" aria-hidden="true">{emoji}</span>'
                f'<span class="rezept-karte__titel">{html.escape(titel)}</span>'
                f'<span class="rezept-karte__text">{beschreibung}</span>'
                f'<span class="rezept-karte__chips">{chip_html}</span></a>'
            )
        teile.append('<div class="rezept-karten">' + "".join(karten) + "</div>\n")

    readme = os.path.join(docs, "README.md")
    if os.path.exists(readme):
        with open(readme, encoding="utf-8") as f:
            m = re.search(r"^## Menüvorschläge\s*\n(.*?)(?=^## |\Z)", f.read(), re.S | re.M)
        if m and m.group(1).strip():
            teile.append('<div class="menues" markdown>\n\n## 🍷 Menüvorschläge\n\n' + m.group(1).strip() + "\n\n</div>\n")

    return markdown.replace("<!-- REZEPTE -->", "\n".join(teile))


# ---------------------------------------------------------------- Rezeptseite

def _infokacheln(body, meta):
    """Ersetzt die erste Tabelle nach der Überschrift durch Infokacheln."""
    m = re.search(r"^\|(.+)\|\s*\n\|[-| :]+\|\s*\n\|(.+)\|\s*$", body, re.M)
    paare = []
    if m:
        koepfe = [k.strip() for k in m.group(1).split("|")]
        werte = [w.strip() for w in m.group(2).split("|")]
        paare = list(zip(koepfe, werte))
        body = body[:m.start()] + "<!-- INFO -->" + body[m.end():]
    else:
        for feld in ("portionen", "vorbereitung", "ruhezeit", "garzeit", "gesamt"):
            if not _leer(meta.get(feld)):
                paare.append((feld.capitalize(), str(meta[feld])))
        body = re.sub(r"^(# .+\n)", r"\1\n<!-- INFO -->\n", body, count=1, flags=re.M)
    if not _leer(meta.get("schwierigkeit")):
        paare.append(("Schwierigkeit", str(meta["schwierigkeit"]).capitalize()))

    kacheln = "".join(
        f'<div class="info-kachel"><span class="info-kachel__icon" aria-hidden="true">'
        f'{INFO_EMOJI.get(k.lower(), "•")}</span><span class="info-kachel__wert">{html.escape(w)}</span>'
        f'<span class="info-kachel__name">{html.escape(k)}</span></div>'
        for k, w in paare if w and w != "–"
    )
    return body.replace("<!-- INFO -->", f'<div class="rezept-info">{kacheln}</div>', 1)


def _abschnitt_einrahmen(body, ueberschrift, klasse):
    muster = re.compile(rf"^(## {re.escape(ueberschrift)}\s*\n)(.*?)(?=^## |\Z)", re.S | re.M)
    return muster.sub(lambda m: f'<div class="{klasse}" markdown>\n\n{m.group(1)}{m.group(2).rstrip()}\n\n</div>\n\n', body, count=1)


def _passt_zu(meta, page):
    eintraege = meta.get("passt_zu") or []
    if not eintraege:
        return ""
    basis = posixpath.dirname(page.file.src_uri)
    teile = []
    for e in eintraege:
        e = str(e)
        if e.endswith(".md"):
            ziel = posixpath.relpath(e, basis or ".")
            name = os.path.splitext(os.path.basename(e))[0].replace("-", " ").capitalize()
            teile.append(f"[{name}]({ziel})")
        else:
            teile.append(e)
    return "\n\n## Passt dazu\n\n" + " · ".join(teile) + "\n"


def _rezeptseite(markdown, page):
    meta = page.meta or {}
    md = _infokacheln(markdown, meta)
    md = _abschnitt_einrahmen(md, "Zutaten", "zutaten")
    md = _abschnitt_einrahmen(md, "Zubereitung", "schritte")
    return md + _passt_zu(meta, page)


def on_page_markdown(markdown, page, config, files):
    if page.file.src_uri == "index.md":
        return _startseite(markdown, config)
    if "/" in page.file.src_uri and page.meta.get("kategorie"):
        md = _rezeptseite(markdown, page)
        # Linknamen für „Passt dazu“ durch echte Rezepttitel ersetzen
        def titel(m):
            ziel = posixpath.normpath(posixpath.join(posixpath.dirname(page.file.src_uri), m.group(2)))
            pfad = os.path.join(config["docs_dir"], ziel)
            return f"[{_lesen(pfad)['titel']}]({m.group(2)})" if os.path.exists(pfad) else m.group(0)
        kopf, sep, passt = md.rpartition("## Passt dazu")
        if sep:
            md = kopf + sep + re.sub(r"\[([^\]]+)\]\(([^)]+\.md)\)", titel, passt)
        return md
    return markdown
