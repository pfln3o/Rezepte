#!/usr/bin/env python3
"""Macht aus einem „Rezept eintragen“-Issue eine Rezeptdatei nach der Vorlage.

Aufruf:  rezept_aus_issue.py pruefen|anlegen  <event.json>  [ausgabe-ordner]
  pruefen  – schreibt nur eine Vorschau (kommentar.md), ändert nichts
  anlegen  – legt rezepte/<kategorie>/<name>.md (+ Foto) an und trägt es in die README ein

Der Issue-Text kommt von Fremden: er wird nur als Text verarbeitet, nie ausgeführt.
"""
import io
import json
import os
import re
import sys
import unicodedata
import urllib.request

FELDER = {
    "Name des Gerichts": "titel",
    "Kategorie": "kategorie",
    "Kurzbeschreibung": "beschreibung",
    "Portionen": "portionen",
    "Vorbereitungszeit": "vorbereitung",
    "Koch-, Back- oder Garzeit": "garzeit",
    "Gesamtzeit": "gesamt",
    "Schwierigkeit": "schwierigkeit",
    "Zutaten": "zutaten",
    "Zubereitung": "zubereitung",
    "Tipps & Varianten (optional)": "tipps",
    "Passt gut zu (optional)": "passt_zu",
    "Woher stammt das Rezept? (optional)": "quelle",
    "Foto (optional)": "foto",
}
KATEGORIEN = {
    "hauptgerichte": "hauptgerichte", "beilagen": "beilagen", "suppen": "suppen",
    "salate": "salate", "soßen": "saucen", "mehlspeisen": "mehlspeisen", "desserts": "desserts", "backen": "backen",
    "getränke": "getraenke",
}
KATEGORIE_TITEL = {v: k.capitalize() for k, v in KATEGORIEN.items()}
PFLICHT = ["titel", "kategorie", "beschreibung", "portionen", "gesamt", "schwierigkeit", "zutaten", "zubereitung"]
FOTO_HOSTS = ("https://github.com/user-attachments/", "https://user-images.githubusercontent.com/",
              "https://private-user-images.githubusercontent.com/")


def felder_lesen(body):
    werte = {}
    teile = re.split(r"^### (.+?)\s*$", body or "", flags=re.M)
    for i in range(1, len(teile) - 1, 2):
        schluessel = FELDER.get(teile[i].strip())
        if schluessel:
            wert = teile[i + 1].strip()
            werte[schluessel] = "" if wert == "_No response_" else wert
    return werte


def einzeilig(text, laenge=200):
    text = re.sub(r"\s+", " ", text or "").strip()
    text = text.replace("<", "‹").replace(">", "›")  # kein HTML aus fremden Einträgen
    text = text.replace("](", "] (")  # keine Links/Bilder aus fremden Einträgen
    return text[:laenge]


def mehrzeilig(text):
    zeilen = []
    for z in (text or "").splitlines():
        z = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", z).strip()
        if z:
            zeilen.append(einzeilig(z, 500))
    return zeilen


def slug(text):
    text = text.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:60] or "rezept"


def yaml_wert(text):
    return json.dumps(text, ensure_ascii=False)  # JSON-Strings sind gültiges YAML


def rezept_bauen(w, autor):
    fehler = [f for f in PFLICHT if not w.get(f)]
    kat = KATEGORIEN.get((w.get("kategorie") or "").strip().lower())
    if w.get("kategorie") and not kat:
        fehler.append("kategorie")
    if w.get("schwierigkeit") and w["schwierigkeit"].strip() not in ("einfach", "mittel", "anspruchsvoll"):
        fehler.append("schwierigkeit")
    if fehler:
        return None, fehler

    titel = einzeilig(w["titel"], 80)
    zeiten = {k: einzeilig(w.get(k, ""), 30) for k in ("portionen", "vorbereitung", "garzeit", "gesamt")}
    passt = [einzeilig(p, 60) for p in (w.get("passt_zu") or "").split(",") if p.strip()]
    quelle = einzeilig(w.get("quelle") or "", 120) or f"eingetragen von @{autor}"

    zutaten_md = []
    for z in mehrzeilig(w["zutaten"]):
        if z.endswith(":"):
            zutaten_md += ["", f"### {z[:-1].strip()}", ""]
        else:
            zutaten_md.append(f"- {z}")
    schritte = [f"{i}. {s}" for i, s in enumerate(mehrzeilig(w["zubereitung"]), 1)]
    tipps = [f"- {t}" for t in mehrzeilig(w.get("tipps", ""))]
    tipps_md = ("## Tipps & Varianten\n\n" + "\n".join(tipps) + "\n\n") if tipps else ""

    kopf = "| Portionen | Vorbereitung | Garzeit | Gesamt |\n|---|---|---|---|\n"
    kopf += "| " + " | ".join(zeiten[k] or "–" for k in ("portionen", "vorbereitung", "garzeit", "gesamt")) + " |"

    md = f"""---
titel: {yaml_wert(titel)}
kategorie: {kat}
portionen: {yaml_wert(zeiten['portionen'])}
vorbereitung: {yaml_wert(zeiten['vorbereitung'] or '0 min')}
garzeit: {yaml_wert(zeiten['garzeit'] or '0 min')}
gesamt: {yaml_wert(zeiten['gesamt'])}
schwierigkeit: {w['schwierigkeit'].strip()}
tags: []
quelle: {yaml_wert(quelle)}
passt_zu: [{', '.join(yaml_wert(p) for p in passt)}]
eingetragen_von: {yaml_wert('@' + autor)}
---

# {titel}

{einzeilig(w['beschreibung'], 600)}

{kopf}

## Zutaten

{chr(10).join(zutaten_md).strip()}

## Zubereitung

{chr(10).join(schritte)}

{tipps_md}## Notizen

- Über die Website eingetragen von @{autor}.
"""
    return {"titel": titel, "kategorie": kat, "md": md, "zeiten": zeiten,
            "schwierigkeit": w["schwierigkeit"].strip()}, []


def foto_url(text):
    for url in re.findall(r"https://[^\s)\"'>]+", text or ""):
        if url.startswith(FOTO_HOSTS):
            return url
    return None


def foto_speichern(url, ziel, token):
    from PIL import Image, ImageOps  # nur im Anlegen-Schritt nötig
    req = urllib.request.Request(url, headers={"User-Agent": "rezept-bot"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as r:
        daten = r.read(25 * 1024 * 1024)
    bild = ImageOps.exif_transpose(Image.open(io.BytesIO(daten))).convert("RGB")
    w, h = bild.size
    tw, th = (w, int(w * 3 / 4)) if w * 3 / 4 <= h else (int(h * 4 / 3), h)
    x, y = (w - tw) // 2, (h - th) // 2
    bild = bild.crop((x, y, x + tw, y + th)).resize((1200, 900), Image.LANCZOS)
    os.makedirs(os.path.dirname(ziel), exist_ok=True)
    bild.save(ziel, quality=80, optimize=True, progressive=True)


def readme_eintragen(pfad_readme, r, rel):
    if not os.path.exists(pfad_readme):
        return
    with open(pfad_readme, encoding="utf-8") as f:
        text = f.read()
    z = r["zeiten"]
    zeile = f"| [{r['titel']}]({rel}) | {z['portionen'] or '–'} | {z['gesamt'] or '–'} | {r['schwierigkeit']} |"
    titel = KATEGORIE_TITEL[r["kategorie"]]
    m = re.search(rf"^### {re.escape(titel)}\s*\n\s*\n\|.*\|\s*\n\|[-| ]+\|\s*\n((?:\|.*\|\s*\n?)*)", text, re.M)
    if m:
        text = text[:m.end(1)].rstrip("\n") + "\n" + zeile + "\n" + text[m.end(1):]
    else:
        block = f"### {titel}\n\n| Rezept | Portionen | Gesamtzeit | Schwierigkeit |\n|---|---|---|---|\n{zeile}\n\n"
        text = text.replace("## Menüvorschläge", block + "## Menüvorschläge", 1) if "## Menüvorschläge" in text else text + "\n" + block
    with open(pfad_readme, "w", encoding="utf-8") as f:
        f.write(text)


def ausgabe(**werte):
    pfad = os.environ.get("GITHUB_OUTPUT")
    if pfad:
        with open(pfad, "a", encoding="utf-8") as f:
            for k, v in werte.items():
                f.write(f"{k}={v}\n")


def main():
    modus, event_pfad = sys.argv[1], sys.argv[2]
    raus = sys.argv[3] if len(sys.argv) > 3 else "."
    with open(event_pfad, encoding="utf-8") as f:
        issue = json.load(f)["issue"]
    autor = re.sub(r"[^A-Za-z0-9-]", "", issue["user"]["login"])
    w = felder_lesen(issue.get("body", ""))
    rezept, fehler = rezept_bauen(w, autor)

    if not rezept:
        namen = {v: k for k, v in FELDER.items()}
        liste = "\n".join(f"- {namen.get(f, f)}" for f in fehler)
        text = f"Da fehlt noch etwas, bitte bearbeite den Eintrag und ergänze:\n\n{liste}\n"
        with open(os.path.join(raus, "kommentar.md"), "w", encoding="utf-8") as f:
            f.write(text)
        ausgabe(ok="false")
        return

    datei = slug(rezept["titel"])
    ordner = os.path.join("rezepte", rezept["kategorie"])
    rel_pfad = f"{rezept['kategorie']}/{datei}.md"
    n = 2
    while modus == "anlegen" and os.path.exists(os.path.join("rezepte", rel_pfad)):
        rel_pfad = f"{rezept['kategorie']}/{datei}-{n}.md"
        n += 1
    url_foto = foto_url(w.get("foto", ""))

    if modus == "pruefen":
        foto_hinweis = "Foto gefunden und wird übernommen." if url_foto else "Kein Foto, die Karte bekommt einen Platzhalter."
        text = (f"Danke! So wird das Rezept angelegt (`rezepte/{rel_pfad}`). {foto_hinweis}\n\n"
                f"Es erscheint auf der Website, sobald es freigegeben ist.\n\n"
                f"<details><summary>Vorschau der Rezeptdatei</summary>\n\n```markdown\n{rezept['md']}```\n</details>\n")
        with open(os.path.join(raus, "kommentar.md"), "w", encoding="utf-8") as f:
            f.write(text)
        ausgabe(ok="true", pfad=rel_pfad, titel=rezept["titel"])
        return

    os.makedirs(ordner, exist_ok=True)
    with open(os.path.join("rezepte", rel_pfad), "w", encoding="utf-8") as f:
        f.write(rezept["md"])
    foto_ok = "nein"
    if url_foto:
        try:
            foto_speichern(url_foto, os.path.join("rezepte", "bilder", rel_pfad[:-3] + ".jpg"),
                           os.environ.get("GITHUB_TOKEN"))
            foto_ok = "ja"
        except Exception as e:  # Rezept trotzdem anlegen
            print(f"Foto konnte nicht geladen werden: {e}", file=sys.stderr)
            foto_ok = "fehler"
    readme_eintragen(os.path.join("rezepte", "README.md"), rezept, rel_pfad)
    ausgabe(ok="true", pfad=rel_pfad, titel=rezept["titel"], foto=foto_ok)


if __name__ == "__main__":
    main()
