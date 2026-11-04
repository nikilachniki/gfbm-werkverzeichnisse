# Werkverzeichnis-Vorlage

Prototyp für die Daten eines musikalischen Werkverzeichnisses. Das Modell folgt
[MerMEId MeLODy](https://music-metadata-tools.github.io/MerMEId-Website/latest/), die
Daten liegen aber als JSON-LD vor, damit eine Website sie direkt lesen kann. Sie
entstand aus dem Lasso-Werkverzeichnis (Branch `main`).

**Stand:** Prototyp. Noch ohne Eingabeoberfläche und Website.

## Aufbau

| Ordner | Inhalt |
| --- | --- |
| `data/` | Die Daten eines Verzeichnisses, hier leer |
| `examples/beispiel/` | Erfundener Beispieldatensatz mit allen wichtigen Fällen |
| `examples/lasso-1555-1/` | Echter Auszug für den [Härtetest](docs/haertetest-1555-1.md) |
| `schema/` | JSON-LD-Kontext und JSON-Schema |
| `scripts/` | Prüfung und Export nach MeLODy |
| `docs/` | [Datenmodell](docs/modell.md) und [Entscheidungen](docs/entscheidungen.md) |

## Ein neues Verzeichnis beginnen

```bash
pip install -r scripts/requirements.txt
```

1. Name und Kürzel in `data/catalog.json` eintragen.
2. Datensätze in die Dateien unter `data/` schreiben, am besten nach dem Muster in
   `examples/beispiel/`.
3. Prüfen:

   ```bash
   python scripts/validate.py data
   ```

   Das findet unbekannte Felder, Verweise ohne Ziel, doppelte IDs und Felder ohne
   RDF-Abbildung.

## Export nach MeLODy

```bash
python scripts/export_melody.py --data data --out ZIELORDNER
```

Schreibt eine Turtle-Datei je Datensatz in der Ordnerstruktur von MeLODy. Der
Zielordner muss leer sein. Eigene Felder wie die Stücknummer im Druck werden dabei
zu Text, siehe [Datenmodell](docs/modell.md). Für den Editor braucht das Repository
zusätzlich `configuration/config.json` mit `datasetBaseUrl` und einen Ordner
`indexes/`, den der Editor füllt.

## Lizenz

Siehe `LICENSE`. Für ein neues Verzeichnis sind Daten- und Codelizenz neu festzulegen.
