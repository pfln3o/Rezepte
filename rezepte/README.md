# Rezeptsammlung

Jedes Rezept ist eine eigene Markdown-Datei im Ordner seiner Kategorie. Neue Rezepte entstehen als Kopie von [`_vorlage.md`](_vorlage.md).

## Aufbau

```
rezepte/
├── README.md          ← diese Übersicht
├── _vorlage.md        ← Vorlage für neue Rezepte
├── hauptgerichte/
├── beilagen/
└── …                  ← weitere Kategorien bei Bedarf (suppen, desserts, backen …)
```

- **Dateinamen:** klein, ohne Umlaute, Bindestriche statt Leerzeichen (`semmelknoedel.md`, `gulasch-ungarisch.md`).
- **Kopfbereich (Frontmatter):** Portionen, Zeiten, Schwierigkeit, Tags und „passt zu“, damit die Sammlung später durchsuchbar oder in eine App übertragbar ist.
- **Abschnitte:** Zutaten (optional in Gruppen), Zubereitung (nummerierte Schritte), Tipps & Varianten, Notizen.

## Rezepte

### Hauptgerichte

| Rezept | Portionen | Gesamtzeit | Schwierigkeit |
|---|---|---|---|
| [Rinderbraten (Schmorbraten)](hauptgerichte/rinderbraten.md) | 4–6 | ca. 3 h 30 min | mittel |
| [Rindergulasch](hauptgerichte/gulasch.md) | 4–6 | ca. 3 h | einfach |

### Beilagen

| Rezept | Portionen | Gesamtzeit | Schwierigkeit |
|---|---|---|---|
| [Semmelknödel](beilagen/semmelknoedel.md) | 4 (ca. 8 Stück) | ca. 1 h | einfach |

### Suppen

| Rezept | Portionen | Gesamtzeit | Schwierigkeit |
|---|---|---|---|
| [Testrezept (bitte ignorieren)](suppen/testrezept-bitte-ignorieren.md) | 4 | 50 min | einfach |

## Menüvorschläge

- **Sonntagsbraten:** Rinderbraten + Semmelknödel (+ Rotkohl)
- **Deftiger Eintopftag:** Rindergulasch + Semmelknödel oder Spätzle
