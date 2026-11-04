# Härtetest mit dem Lasso-Druck 1555-1

Am 4. November 2026 wurde der Druck 1555-1 samt seinen Werken, Nachdrucken und
Handschriften aus dem Lasso-Stand (`main`) in die Vorlage übertragen.
`examples/lasso-1555-1/konvertieren.py` ist wiederholbar, `luecken.json` im selben
Ordner listet alle Fundstücke. Die Daten sind echt, aber ein Auszug; das Werkzeug
gehört nicht zur Vorlage.

## Ergebnis

| Prüfung | Ergebnis |
| --- | --- |
| Datenmenge | 31 Werke, 31 Expressions, 27 Quellen (20 Drucke, 7 Handschriften), 7 Exemplare |
| `scripts/validate.py` | keine Fehler, 3320 RDF-Aussagen |
| Stellen in Drucken | 315 von 315, mit Nummer und Expression |
| Handschriftenzeugnisse der Werke | 27 von 27, mit Titel, Stimmen, Datierung und Bemerkung |
| Fundstellen in der Gesamtausgabe | 31 von 31, mit Band, Abschnitt und Nummer |
| Variantentitel, Textdichter | 28 von 28, 18 von 18 |
| Export nach MeLODy | 121 Dateien, zwei Läufe identisch |
| Shapes | nur der bekannte Widerspruch bei Anmerkungen an Manifestationen (83 Meldungen) |
| Formular im Editor | 118 von 118 ohne Abweichung, Speichern von Werk, Druck und Band ohne Verlust |

Damit stehen Stücknummern, Fundstellen und Zeugnisse hier als Struktur, die beim
Lasso-Export nur Text waren. Im MeLODy-Export bleiben sie weiterhin Text.

## Was im Modell fehlt

| Angabe | Häufigkeit | Bisher | Vorschlag |
| --- | --- | --- | --- |
| Stimmbücher | 20 Drucke | Anmerkung | Eigenes Feld `partbooks` |
| Quellenart | 7 Handschriften | Anmerkung | Eigenes Feld `sourceType` |
| Literatur zu einer Quelle | 2 | Anmerkung | `citations` auch an der Manifestation |
| Quellenbemerkung | 1 | Anmerkung | passt |
| Teil innerhalb eines Stücks | 9 | Text in `position` („1, Teil 2“) | Eigenes Feld prüfen |
| Vor- und Nachname | 3 Namen | ganzer Name in `familyName` | Redaktionell zerlegen |

Textprovenienz hat ebenfalls kein eigenes Feld. Sie kommt in diesem Druck zwar nicht
vor, in Lasso aber häufig.

## Was nicht geprüft ist

**Der Druck ist einfacher als der Gesamtbestand.** Er enthält keine Werke mit mehreren
Stimmenzahlen, keine Textprovenienz, keine Fassungen, keine Bemerkungen zu Einträgen,
keine Titel ohne Sprache und keine Werke aus dem LV-Anhang. Die schwierigsten Fälle
stehen also noch aus; das Skript ist für mehrere Stimmenzahlen vorbereitet, aber nicht
erprobt.

**Die Quelle begrenzt die Tiefe.** Für Nachdrucke liegt keine Stimmenzahl und kein
Titel des Drucks vor, nur die Stücknummer. Außerdem nennen die Handschriften 174
weitere Stücke außerhalb der Auswahl; sie stehen nur als Anmerkung „Weitere Stücke“.

**Weiteres.** Größere Datenmengen, Eingaben von Hand im Editor und die Gattung, die in
Lasso als fehlerhaft gilt und hier ungeprüft übernommen ist.
