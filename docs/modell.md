# Datenmodell

Das Modell folgt [MerMEId MeLODy](https://music-metadata-tools.github.io/MerMEId-Website/latest/):
dieselben Entitäten und über `schema/context.jsonld` dieselben Begriffe. Geprüft
gegen den Editor-Stand `a207350`, Version 0.9. Die Daten sind aber JSON-LD, das eine
Website direkt lesen kann.

## Entitäten

| Datei | Typ | Inhalt |
| --- | --- | --- |
| `catalog.json` | `Catalogue` | Name des Verzeichnisses, Komponist*in, Kürzel |
| `works.json` | `Work` | Das abstrakte Werk |
| `expressions.json` | `Expression` | Eine Gestalt des Werks, etwa eine Besetzung |
| `manifestations.json` | `Manifestation` | Ein Druck oder eine Handschrift |
| `items.json` | `Item` | Ein Exemplar mit Bibliothek und Signatur |
| `persons.json` | `Person` | Komponist*innen, Textdichter*innen, Herausgeber*innen |
| `institutions.json` | `Institution` | Bibliotheken, Verlage |
| `places.json` | `Place` | Orte |
| `instrumentations.json` | `Instrumentation` | Besetzungen |
| `bibliography.json` | `Bibliography` | Literatur, Ausgaben und ihre Bände |

Jede Datei hat die Form `{ "@context": …, "entries": [ … ] }`. Einen Einblick in
alle Felder gibt `examples/beispiel/`, die Regeln stehen in
`schema/catalogue.schema.json`.

## Regeln

**IDs.** Eine ID besteht aus Präfix und frei gewähltem Namen, etwa `works:90`. Sie
wird einmal vergeben und nie neu verwendet. In RDF wird daraus `urn:uuid:works/90`,
die Form, die der Editor aus dem Dateipfad bildet.

**Beziehungen stehen in einer Richtung.** Ein Teil verweist mit `partOfWork` auf sein
Gesamtwerk, ein Werk mit `realisedIn` auf seine Expressions, ein Exemplar mit
`exemplifies` auf die Quelle. Die Gegenrichtung ist ableitbar und wird nicht gepflegt.

**Jedes Werk braucht eine Expression,** wenn es in einer Quelle stehen soll, denn eine
Quelle verweist auf die Expression. Weicht ein Stück ab, etwa in der Besetzung,
bekommt es eine weitere Expression.

**Begriffe aus MeLODy-Listen** stehen als `terms:…`, etwa `terms:Lyricist` oder
`terms:Print`. Die vollständigen Listen führt das MeLODy-Vokabular. Für das Land
eines Orts erwartet es einen GeoNames-Link.

**Titel tragen ihre Sprache als Schlüssel,** etwa `{ "it": "Fiera stella" }`, ohne
Text oder bekannte Sprache `{ "@none": "Sonate" }`.

**`notes[].html`** ist HTML, `&` und `<` sind also als Entität zu schreiben.

## Eigene Erweiterungen

Diese Felder kennt MeLODy nicht. Sie stehen im Namensraum `wv:`, dessen Adresse
`https://example.org/werkverzeichnis/ns#` noch ein Platzhalter ist.

| Feld | Zweck | Beim Export nach MeLODy |
| --- | --- | --- |
| `contents` an der Manifestation | Welches Stück wo in der Quelle steht (`position`, `part`), mit Titel, Stimmen, Datierung und Bemerkung dieser Quelle | `lrmoo:R4_embodies` und eine Textzeile in `melod:hasContents` |
| `citations` an Werk und Expression | Verweis auf den Band samt Nummer, Seite und Abschnitt | `schema:citation` und eine Anmerkung „Fundstelle“ |
| `genres` am Werk | Gattung als freier Text, das MeLODy-Vokabular kennt etwa keine Motette | Anmerkung „Gattung“ |
| `textSources` an Werk und Expression | Herkunft des vertonten Texts, etwa eine Bibelstelle | Anmerkung „Textprovenienz“ |
| `sourceType`, `partbooks`, `literature` an der Manifestation | Art der Quelle, vorhandene Stimmbücher, Literatur als Text | je eine Anmerkung |
| `publisherName` | Verlag als Text, `schema:publishedBy` erlaubt nur Personen | Text im Label der Veröffentlichung |
| `composer`, `catalogueAbbreviation` am Katalog | Angaben zum Verzeichnis | entfallen |

Die Stelle im Druck und die Fundstelle gehen beim Export also als Struktur verloren,
als Text bleiben sie erhalten. Im JSON-LD selbst sind sie vollwertig.

## Bekannte Grenzen des Editors

- **Titel ohne Sprache.** Das Formular schreibt sie als `"…"^^rdf:langString`, was kein
  gültiges Turtle ist. Solche Werke und Expressions nicht im Editor speichern. Der
  Export meldet sie.
- **Anmerkungen an der Manifestation** bestehen die Shape-Prüfung nie, weil
  `melod:Contents` versehentlich `sh:targetClass melod:Annotation` trägt.
- **Indizes und `datasetBaseUrl`** müssen vorhanden sein. Ohne Indizes verschwinden
  Verknüpfungen aus der Formularausgabe, ohne `datasetBaseUrl` lädt das Formular leer.
- **Automatische Rückführung.** Der Export ist einseitig. Änderungen im Editor kommen
  nicht zurück in das JSON-LD.
