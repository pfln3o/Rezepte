"""Baut die Startseite der Website automatisch aus allen Rezeptdateien.

Jede .md-Datei in einem Kategorie-Ordner mit Frontmatter (titel, portionen,
gesamt, schwierigkeit) landet in der Tabelle ihrer Kategorie. Neue Rezepte
erscheinen also ohne weiteres Zutun. Die Menüvorschläge kommen aus der README.
"""
import os
import re

import yaml

REIHENFOLGE = ["hauptgerichte", "suppen", "salate", "beilagen", "saucen", "desserts", "backen", "getraenke"]
SCHOENE_NAMEN = {"getraenke": "Getränke", "saucen": "Soßen"}


def _frontmatter(pfad):
    with open(pfad, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    meta = yaml.safe_load(m.group(1)) if m else {}
    if not meta.get("titel"):
        h1 = re.search(r"^# (.+)$", text, re.M)
        meta["titel"] = h1.group(1).strip() if h1 else os.path.basename(pfad)
    return meta


def _kategorie_name(ordner):
    return SCHOENE_NAMEN.get(ordner, ordner.replace("-", " ").capitalize())


def _zelle(wert):
    return "–" if wert in (None, "", "0 min") else str(wert).replace("|", "/")


def on_page_markdown(markdown, page, config, files):
    if page.file.src_uri != "index.md":
        return markdown
    docs = config["docs_dir"]
    kategorien = {}
    for eintrag in sorted(os.listdir(docs)):
        ordner = os.path.join(docs, eintrag)
        if not os.path.isdir(ordner) or eintrag.startswith((".", "_")) or eintrag == "assets":
            continue
        rezepte = []
        for datei in sorted(os.listdir(ordner)):
            if datei.endswith(".md") and not datei.startswith("_"):
                meta = _frontmatter(os.path.join(ordner, datei))
                rezepte.append((str(meta["titel"]), f"{eintrag}/{datei}", meta))
        if rezepte:
            kategorien[eintrag] = sorted(rezepte, key=lambda r: r[0].lower())

    rang = {k: i for i, k in enumerate(REIHENFOLGE)}
    teile = []
    for kat in sorted(kategorien, key=lambda k: (rang.get(k, 99), k)):
        teile.append(f"## {_kategorie_name(kat)}\n")
        teile.append("| Rezept | Portionen | Zeit | Schwierigkeit |\n|---|---|---|---|")
        for titel, link, meta in kategorien[kat]:
            teile.append(
                f"| [{titel}]({link}) | {_zelle(meta.get('portionen'))} | "
                f"{_zelle(meta.get('gesamt'))} | {_zelle(meta.get('schwierigkeit'))} |"
            )
        teile.append("")

    readme = os.path.join(docs, "README.md")
    if os.path.exists(readme):
        with open(readme, encoding="utf-8") as f:
            m = re.search(r"^## Menüvorschläge\s*\n(.*?)(?=^## |\Z)", f.read(), re.S | re.M)
        if m and m.group(1).strip():
            teile.append("## Menüvorschläge\n\n" + m.group(1).strip() + "\n")

    return markdown.replace("<!-- REZEPTE -->", "\n".join(teile))
