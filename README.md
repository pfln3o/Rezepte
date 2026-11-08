# Rezeptsammlung

Die Rezepte liegen als Markdown in [`rezepte/`](rezepte/) (Übersicht: [`rezepte/README.md`](rezepte/README.md)).
Bei jedem Push auf `main` baut GitHub Actions daraus mit MkDocs eine Website und veröffentlicht sie auf GitHub Pages.
Die Startseite listet alle Rezepte automatisch (siehe `hooks/startseite.py`), neue Rezepte erscheinen also ohne weitere Schritte.

Lokal ansehen: `pip install -r requirements.txt && mkdocs serve`
