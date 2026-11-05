# Härtetests mit Lasso-Daten

Am 4. November 2026 wurden echte Auszüge aus dem Lasso-Stand (Branch `lasso`) in die Vorlage
übertragen. `examples/lasso_konvertieren.py` ist wiederholbar, aber kein Teil der
Vorlage; `luecken.json` im jeweiligen Ordner listet die Fundstücke.

| Test | Auswahl | Was er prüft |
| --- | --- | --- |
| `examples/lasso-1555-1/` | Druck 1555-1 mit allem, was dazugehört | Der Normalfall |
| `examples/lasso-schwierig/` | LV 74, 90, 193, 327 mit Teilen und LV-Anhang 1 | Fassungen, mehrere Stimmenzahlen, Textprovenienz, Titel ohne Sprache, Werk ohne Druck |

## Ergebnis

| Prüfung | 1555-1 | Schwierig |
| --- | --- | --- |
| Werke, Expressions | 31, 31 | 27, 32 |
| Quellen, Exemplare | 27, 7 | 101, 45 |
| `scripts/validate.py` | keine Fehler | keine Fehler |
| Stellen in Drucken mit Nummer | 315 von 315 | 59 von 59 |
| Handschriftenzeugnisse der Werke | 27 von 27 | 149 von 149 |
| Fundstellen in der Gesamtausgabe | 31 von 31 | 14 von 14 |
| Fassungen | keine | 5 von 5 |
| Export nach MeLODy, zwei Läufe | identisch, 121 Dateien | identisch, 275 Dateien |
| Shapes | 83 Meldungen | 357 Meldungen |
| Formular im Editor ohne Abweichung | 118 von 118 | 75 von 75 in der Stichprobe; davor 290 von 291 |
| Speichern ohne Verlust | Werk, Druck, Band | Werk, Druck, Fassung |

Alle Shape-Meldungen haben zwei Ursachen: den Widerspruch bei Anmerkungen an
Manifestationen und die Titel des Anhang-Werks ohne Sprache. Dieses Werk war auch die
eine Abweichung im Editor (`"…"^^rdf:langString`). Nach dem Wechsel auf eine Expression
je Werk wurde nur noch eine Stichprobe von 10 Dateien je Typ im Editor geprüft, das
Anhang-Werk war nicht darunter.

Stimmenzahlen funktionieren: LV 90 steht fünfstimmig in 1560-4 und zweistimmig in
1560-8, mit `voices` und Nummer am Stück in der Quelle.

## Inhaltliche Befunde

**Eine Expression je Werk.** Eine frühere Fassung dieses Tests legte je Stimmenzahl eine
Expression an (50 statt der jetzigen 32 Expressions). Das wurde verworfen, siehe
`docs/entscheidungen.md`, Abschnitt 5. Die Tabelle oben zeigt den aktuellen Stand; die
Laufzeit weiter unten stammt noch von der früheren Fassung.

**Viele Nachdrucke belegen keine Stimmenzahl.** Bei Werken mit mehreren Stimmenzahlen
sagt die Quelle in 35 von 59 Druckstellen nicht, welche gemeint ist. Dort fehlt `voices`.
Das ist eine Lücke der Quelle, das Modell gibt sie richtig wieder.

**Fassung und Registernummer finden nicht zueinander.** In 1558-1 steht Nr. 12 mit der
Bemerkung „nur IV.“ am Gesamtwerk LV 74, die Fassung `74 (IV)` steht im selben Druck
ohne Nummer. Vermutlich ist beides dasselbe Stück, automatisch zusammengelegt wurde es
nicht. Alle 5 Fassungen stehen deshalb ohne Stücknummer im Druck.

## Ergänzt nach dem ersten Test

`partbooks`, `sourceType` und `literature` an der Manifestation, `textSources` an Werk
und Expression, `part` im Inhalt. `literature` ist Freitext, nicht `citations`, weil
Literaturangaben in Lasso nicht als Bibliographie-Einträge vorliegen.

## Noch ohne Platz

| Angabe | Häufigkeit | Bisher |
| --- | --- | --- |
| Pars einer Fassung | 5 | Anmerkung |
| Provenienz | je nach Quelle | Anmerkung; MeLODy hat dafür Ereignisse am Exemplar |
| Vor- und Nachname | 3 Namen | ganzer Name in `familyName` |

## Was nicht geprüft ist

- **Stücke außerhalb der Auswahl.** Die Handschriften enthalten viele weitere Stücke
  (1325 im schwierigen Test). Sie stehen als Stücke ohne Werk in `contents`, mit ihrer
  Nummer in `note`. Stücke mit Nummer wären im Gesamtbestand normal zugeordnet.
- **Datenmenge.** Der Editor wird schon bei 291 Dateien spürbar langsamer: Der Test
  dauerte gut zehn Minuten, Chrome belegte bis zu 2,8 GB. Die Vorlage selbst ist nicht
  mit großen Datenmengen getestet.
- **Eingaben von Hand** im Editor. Gespeichert wurde nur per Skript, ohne Änderungen.
- **Bemerkungen zu Einträgen und unsichere Textdichter** waren in diesen Auszügen
  nicht oder kaum vertreten.
- **Die Gattung** ist ungeprüft übernommen, obwohl sie in Lasso als fehlerhaft gilt.
- **Der Weg zurück** vom Editor in das JSON-LD fehlt.
- **Shapes und Editor nach dem Verschieben der Datierung.** `dating` steht seit
  `docs/entscheidungen.md`, Abschnitt 8, an der Handschrift und wird beim Export zu einer
  Anmerkung. Prüfung und Export liefen erneut, Shapes und Editor nicht. Die Zahlen oben
  stammen also von davor.
