# Werkverzeichnis-Vorlage

Prototyp für die Daten eines musikalischen Werkverzeichnisses. Das Modell folgt
[MerMEId MeLODy](https://music-metadata-tools.github.io/MerMEId-Website/latest/), die
Daten liegen aber als JSON-LD vor, damit eine Website sie direkt lesen kann. Sie
entstand aus dem Lasso-Werkverzeichnis (Branch `lasso`).

**Stand:** Prototyp. Die Website samt Verwaltung liegt in
[gfbm-werkverzeichnisse-frontend](https://github.com/nikilachniki/gfbm-werkverzeichnisse-frontend) und wird für jedes Verzeichnis aus
demselben Code gebaut.

## Aufbau

| Ordner | Inhalt |
| --- | --- |
| `data/` | Die Daten eines Verzeichnisses, hier leer |
| `examples/beispiel/` | Erfundener Beispieldatensatz mit allen wichtigen Fällen |
| `examples/lasso-1555-1/`, `examples/lasso-schwierig/` | Echte Auszüge für die [Härtetests](docs/haertetest-1555-1.md) |
| `schema/` | JSON-LD-Kontext und JSON-Schema |
| `scripts/` | Prüfung und Export nach MeLODy |
| `docs/` | [Datenmodell](docs/modell.md) und [Entscheidungen](docs/entscheidungen.md) |

## Ein neues Verzeichnis beginnen

Jedes Werkverzeichnis bekommt ein eigenes Daten-Repo. Die Website kommt nicht als Kopie
dazu: Sie wird aus dem gemeinsamen Code im Frontend-Repo mit den Daten dieses Repos gebaut.

1. **Repo anlegen.** Auf GitHub bei diesem Repo „Use this template“ → „Create a new
   repository“, etwa `lebeau-werkverzeichnis`. Das ergibt ein eigenständiges Repo ohne
   Verbindung zur Vorlage (kein Fork). Am besten in der Organisation, in der auch die
   Redaktion Mitglied ist.
2. **Website einschalten.** Im neuen Repo Settings → Pages → Source: „GitHub Actions“.
   Danach Actions → „Daten prüfen und veröffentlichen“ → „Run workflow“. Die Seite
   erscheint unter `https://<owner>.github.io/<repo>/`.
3. **Einrichten.** `https://<owner>.github.io/<repo>/#/admin` öffnen, mit einem GitHub-Token
   anmelden (Anleitung auf der Seite), unter „Ausprobieren“ → „Aus dem Repo öffnen“. Dann
   in den Schritten Vorlage, Bausteine und Felder Name, Komponist*in, Kürzel und die
   gewünschten Felder wählen und speichern. Die Auswahl liegt danach als
   `data/baukasten.json` im Repo und gilt für alle, die das Verzeichnis bearbeiten.
4. **Erfassen und veröffentlichen.** Werke, Quellen usw. in der Verwaltung anlegen,
   speichern (Zweig `redaktion/<login>`), veröffentlichen (Pull Request) und nach grüner
   Prüfung zusammenführen. Jeder Push auf `main` baut die Seite neu.

Die Ordner `examples/` und `texDateien/` stammen aus der Vorlage und können im neuen Repo
gelöscht werden.

Von Hand geht es auch ohne Verwaltung:

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
