# Abbildung auf MerMEId MeLODy

Wie `scripts/export_melody.py` die Dateien aus `data/` auf das Modell von
[MerMEId MeLODy](https://music-metadata-tools.github.io/MerMEId-Website/latest/)
abbildet. Grundlage sind die SHACL-Shapes und die Vorlage mit Stand
3. November 2026 (Editor `a207350`, Vorlage `58783c5`, Version 0.9). Begründung
in `docs/entscheidungen.md`, Abschnitt 44.

## Entitäten

| Bei uns | In MeLODy | Datei |
| --- | --- | --- |
| Werk `work:90` | `melod:Work` | `works/90.ttl` |
| (ein Datensatz je Werk, nur im Export) | `melod:Expression` | `expressions/90.ttl` |
| Fassung `expression:74-IV` | `melod:Expression` | `expressions/74-IV.ttl` |
| Druck `print:1555-1` | `melod:Manifestation` | `manifestations/1555-1.ttl` |
| Handschrift (Sigel und Signatur) | `melod:Manifestation` und `melod:Item` | `manifestations/hs-….ttl`, `items/hs-….ttl` |
| Person | `melod:Person` | `persons/gnd-….ttl` |
| Ausgabe `edition:ga2` | `melod:Bibliography` (Reihe) | `bibliography/ga2.ttl` |
| Band `edition:ga2-xiv` | `melod:Bibliography` (Bandnummer) | `bibliography/ga2-xiv.ttl` |
| Bibliothek, Ort, Stimmenzahl | `Institution`, `Place`, `Instrumentation` | abgeleitet |

**IDs.** Der Editor bildet die IRI aus dem Dateipfad, `works/90.ttl` wird zu
`urn:uuid:works/90`. Unsere Nummern bleiben dadurch erkennbar (Abschnitt 7). Es
sind aber keine echten UUIDs; ob das auf Dauer trägt, ist mit dem Projekt zu
klären.

## Felder

| Bei uns | In MeLODy |
| --- | --- |
| `preferredTitle`, `variantTitles` | `melod:hasTitle` mit `MainTitle`, `OtherTitle` |
| `lv`, `lvAnh` | `melod:hasIdentifier` „LV“, „LV-Anhang“ |
| Komponist (Lasso) | `melod:hasContribution`, Rolle `Composer` |
| `textAuthors`, `uncertainTextAuthors` | `melod:hasContribution`, Rolle `Lyricist`, unsicher als `LowCertainty` |
| `isPartOf`, `hasPart` | `melod:isWorkPartOf`, `melod:hasWorkPart`, an der Expression entsprechend |
| `languages` | `melod:inLanguage` an der Expression; zugleich Sprach-Tag der Werktitel |
| eine Stimmenzahl | `melod:hasInstrumentation` an der Expression |
| `prints`, `printAppearances` | `lrmoo:R4_embodies` vom Druck zur Expression |
| `siglum`, `references` | `melod:hasIdentifier` je Verzeichnis |
| `rism`, `gnd`, `viaf`, `link` | `owl:sameAs` |
| `title`, `shortTitle` (Druck) | `melod:hasTitlePage`, `melod:hasTitle` |
| `year` | `schema:publication`, 1. Januar bis 31. Dezember wie in der Vorlage |
| `rismSiglum`, `library`, `place` | `melod:Institution` mit `melod:hasSiglum` und Ort |
| `shelfmark`, `shelfmarkAlt` | `melod:hasShelfmark`, `melod:hasFormerShelfmark` |
| `editionAppearances` | `schema:citation` zum Band |

## Lücken

Was MeLODy nicht als eigenes Feld kennt, geht nicht verloren, steht aber nur als
Text und ist nicht maschinell verknüpft.

| Lücke | Im Export | Mögliche Lösung |
| --- | --- | --- |
| **Stelle im Druck** (Stücknummer) | Zeile in `melod:hasContents` | Eigene Shape oder Lösung des Projekts |
| **Stelle in der Gesamtausgabe** (`number`, `page`, `appendix`) | Rohwert als Anmerkung „Gesamtausgabe“ | Dito |
| **Teilband** (`XIV,I`) | Verweis auf Band `XIV`, Teilband nur im Rohwert | Eigener Bibliography-Eintrag |
| **Handschrift enthält welches Stück** | Zeile in `melod:hasContents` mit Stimmen, Datierung, Bemerkung; nur das Stück selbst über `R4_embodies` | Dito |
| **Mehrere Stimmenzahlen** (544 Werke) | Anmerkung „Stimmenzahlen“, keine `Instrumentation` | Eigene Expression je Besetzung, fachlich offen (Abschnitt 17) |
| **Verlag** | Text im Label der Veröffentlichung, weil `schema:publishedBy` nur Personen erlaubt | Klärung mit dem Projekt |
| **Personennamen** | Ganzer Name in `schema:familyName`, Pflichtfeld; Zerlegen wäre eine Setzung (Abschnitt 8) | Redaktionelle Zerlegung |
| **Herausgeber-Normdaten** | Ohne GND/VIAF | Ergänzen in `gesamtausgaben.json` |
| **Textprovenienz, Bemerkung, Pars, Druckbeschreibung, Stimmbücher, Quellenart, Provenienz, Literatur** | Anmerkung mit Bezeichnung | Teils eigene Felder der Shapes prüfen |
| **Titelsprache** | Tag aus der Werksprache; bei 242 Werken (353 Titel) ohne Sprachangabe kein Tag. **Diese Werke dürfen im Editor noch nicht gespeichert werden**, das Formular schreibt sonst ungültiges Turtle (`"…"^^rdf:langString`), mit dem Tag `und` ebenso | Sprache redaktionell bestimmen; raten wäre eine Setzung |
| **Verlag, „ca.“** | Text im Label der Veröffentlichung; am Druck kennt die Shape kein Beschreibungsfeld, „ca. 1558“ ginge dort sonst beim Speichern verloren | Klärung mit dem Projekt |
| **Ungültige Links** | Zwei Links mit `[` als Anmerkung „Link“, weil sie die Index-Erzeugung abbrechen | Links in der Quelle korrigieren |

**Bewusst nicht exportiert.** `genres`, weil die Gattung derzeit fehlerhaft ist
(Abschnitt 42). Abgeleitete Angaben wie `entryCount`, `preferredTitleBasis` und
`normalizedTitleBasis`. Die Einträge aus `entries.json` werden nicht einzeln
abgebildet, ihre Titel stehen am Werk, ihre Bemerkungen in der Anmerkung.

## Praxistest

Durchgeführt am 4. November 2026 mit dem Editor-Stand `a207350`, automatisiert in
Chrome (ohne sichtbares Fenster), mit dem Browser-Speicher statt eines echten
Ordners. Geprüft wurde, ob das Formular dieselben Aussagen ausgibt wie die Datei;
der vom Formular ergänzte `dct:conformsTo` zählt nicht als Abweichung. Dazu kam
Speichern an drei Dateien.

| Prüfung | Ergebnis |
| --- | --- |
| Stichprobe `1555-1`, 118 Dateien | 118 ohne Abweichung |
| Gesamtbestand, 54 Dateien aus allen Typen | 54 ohne Abweichung |
| Sonderfälle im Gesamtbestand, 63 Dateien | 60 ohne Abweichung, 3 mit dem Titelfehler oben |
| Speichern von Werk, Druck und Band | ohne Verlust |
| Gültigkeitsprüfung des Formulars | keine Beanstandung |

**Gesamtbestand (8053 Dateien).** Die Messwerte schwanken stark und sind
Anhaltspunkte, nicht Laborwerte: Indizes erzeugen 27 bis 225 Sekunden, Ordner
aufklappen 2 bis 111 Sekunden, Formular öffnen im Mittel 4 bis 15 Sekunden gegenüber
0,6 Sekunden in der Stichprobe. Der JS-Speicher erreichte rund 3 GB; nach 60
Formularen blieben nach erzwungener Speicherbereinigung noch 848 MB.

**Nicht geprüft.** Eingaben von Hand, Klonen und Hochladen über GitHub, ein echter
lokaler Ordner, andere Browser und die MEI-Ausgabe.

## Befunde für das Projekt

- **Widerspruch in `manifestation.shacl`.** `melod:Contents` trägt laut Stand
  `sh:targetClass melod:Annotation`, offenbar kopiert. Dadurch gilt für jede
  Anmerkung sowohl `rdf:HTML` als auch `xsd:string`, sodass Anmerkungen an einer
  Manifestation die Validierung nie bestehen können. Der Export schreibt
  `rdf:HTML` wie die Annotation-Shape. Das Inhaltsverzeichnis speichert das
  Formular als `melod:Annotation`, der Export tut das deshalb auch.
- **Titel ohne Sprache.** Das Formular schreibt sie als `"…"^^rdf:langString`,
  was kein gültiges Turtle ist.
- **Leere `datasetBaseUrl`.** Ist sie nicht gesetzt, lädt der Editor ohne Warnung
  ein leeres Formular. Speichern würde die Datei überschreiben.
- **Fehlende Indizes.** Ohne Indizes verschwinden Verknüpfungen beim Serialisieren
  des Formulars, etwa zur Expression, zum Band oder zum Herausgeber.
- **Vorzeitig „ungespeichert“.** Ohne Indizes gilt ein Formular schon direkt nach
  dem Laden als geändert.
- **Möglicher Doppelbestand in unseren Daten.** `A-Wn SA.68.A.139` und
  `SA.68.A.139*` sowie `D-B Mus. ms. 40209` und `Mus.ms. 40209` ergeben denselben
  Dateinamen. Sie bleiben getrennt (Zählung `-2`), ob sie eine Quelle sind, ist
  fachlich zu prüfen.
- **Dateinamen ohne Groß- und Kleinschreibung.** Die Sigel `E-SC` (Santiago de
  Compostela) und `E-Sc` (Sevilla) sind verschiedene Bibliotheken, fielen unter
  Windows aber auf eine Datei. Der Export zählt sie deshalb hoch und bricht bei
  einer solchen Kollision ab. Für den Editor mit seinen Pfad-IDs ist das auf
  anderen Systemen ebenfalls zu beachten.
