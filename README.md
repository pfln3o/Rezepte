# Rezeptsammlung

Die Rezepte liegen als Markdown in [`rezepte/`](rezepte/) (Übersicht: [`rezepte/README.md`](rezepte/README.md)).
Bei jedem Push auf `main` baut GitHub Actions daraus mit MkDocs eine Website und veröffentlicht sie auf GitHub Pages.
Die Startseite listet alle Rezepte automatisch (siehe `hooks/startseite.py`), neue Rezepte erscheinen also ohne weitere Schritte.

Lokal ansehen: `pip install -r requirements.txt && mkdocs serve`

## Rezepte über die Website eintragen

Der Knopf „Rezept eintragen“ öffnet ein GitHub-Formular (`.github/ISSUE_TEMPLATE/rezept.yml`).
Die Aktion `.github/workflows/rezept.yml` kommentiert eine Vorschau. Setzt der Besitzer das Label **freigegeben**,
wird `rezepte/<kategorie>/<name>.md` (plus Foto) angelegt, in die README eingetragen, veröffentlicht und der Eintrag geschlossen.
Ohne Freigabe sofort veröffentlichen: Repo-Variable `SOFORT_ONLINE` auf `true` setzen.
