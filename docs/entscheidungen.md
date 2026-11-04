# Entscheidungen

Begründungen zur Vorlage. Die Entscheidungen zum Lasso-Verzeichnis, aus dem sie
hervorgeht, stehen im Branch `main` in derselben Datei.

## 1. Vorlage statt Lasso-Sonderfall

**Entscheidung.** Dieser Branch enthält nur ein allgemeines Modell, leere Datendateien,
einen erfundenen Beispieldatensatz und Werkzeuge. Lasso-Daten und Lasso-spezifische
Felder (LV-Nummern, LV-Anhang, Excel-Import, TeX-Auszug) sind entfernt.

**Begründung.** Das Lasso-Projekt soll Grundlage für weitere Werkverzeichnisse sein.

**Preis.** Lasso nutzt die Vorlage noch nicht und bleibt auf `main` beim eigenen
Modell; eine Migration wäre eine eigene Aufgabe.

## 2. JSON-LD mit den Begriffen von MeLODy

**Entscheidung.** Die Daten liegen als JSON-LD in Sammeldateien je Typ. Der Kontext
bildet sie auf die Begriffe von MerMEId MeLODy ab (`melod:`, `lrmoo:`, `schema:`).
Turtle in MeLODy-Form entsteht per Skript.

**Anlass.** Der MeLODy-Editor sagte dem Team bei einem Test mit Lasso-Daten nicht zu.
Der Anschluss an das Modell soll bleiben, die Bindung an den Editor nicht.

**Alternativen.** Turtle wie MeLODy als führendes Format: Der Editor funktionierte
direkt, eine Website bräuchte aber einen RDF-Parser oder einen Umwandlungsschritt, und
die Bindung an eine Beta-Version wäre enger. Ein eigenes Modell ohne Bezug zu MeLODy:
freier, aber der Anschluss bliebe eine dauerhaft gepflegte Abbildung.

**Begründung.** Turtle und JSON-LD sind zwei Schreibweisen für RDF. Mit denselben
Begriffen ist der Kern ohne eigene Abbildung umwandelbar, und eine Website kann die
Daten direkt lesen.

**Preis.** Ändert MeLODy seine Begriffe, ist der Kontext anzupassen. Das Modell bringt
den Umweg über die Expression auch dort mit, wo es nur eine Gestalt gibt. Ohne Editor
fehlt vorerst eine Eingabeoberfläche; die Dateien werden von Hand oder per Skript
gepflegt, ein eigener schlanker Editor ist spätere Aufgabe.

## 3. Stellenangaben als eigene Erweiterung

**Entscheidung.** `contents` und `citations` halten die Stelle in Quelle und Ausgabe
als Struktur, im Namensraum `wv:`.

**Anlass.** Beim Test mit Lasso war das die größte Lücke: MeLODy kennt keine Aussage
über die Verbindung von Stück und Quelle. Stücknummern, Fundstellen und die Angaben je
Handschriftenzeugnis wären nur Text gewesen.

**Preis.** Beim Export nach MeLODy werden sie zu Text. Eine eigene Shape dafür ist
noch nicht erprobt.

## 4. Keine ID-Registry, nur eine Beziehungsrichtung

**Entscheidung.** IDs stehen frei gewählt im Datensatz. Beziehungen werden nur in einer
Richtung gepflegt, die Gegenrichtung erzeugt der Export.

**Begründung.** Ohne Excel-Import fehlt der Anlass für eine Registry, und doppelt
gepflegte Beziehungen liefen auseinander.

**Preis.** Dass eine ID nicht neu vergeben wird, sichert nur die Redaktion ab, nicht
ein Werkzeug; `scripts/validate.py` findet nur Dubletten im aktuellen Bestand.

## 5. Die Vorlage legt keine Regel für Expressions fest

**Entscheidung.** Wann eine weitere Expression entsteht, entscheidet die Redaktion
eines Verzeichnisses. Das Modell erlaubt eine Expression je Fassung, schreibt aber keine
Regel vor.

**Anlass.** Der Härtetest legt je belegter Stimmenzahl eine Expression an. Das hielt
den Fakt fest, welche Besetzung wo steht, ergäbe bei Lasso aber rund 3300 Expressions
bei 2166 Werken und setzte jede abweichende Zählung mit einer Fassung gleich, auch wenn
eine Quelle nur Stimmen verloren hat.

**Alternative.** Die Stimmenzahl nur am Stück in der Quelle (`voices` in `contents`)
und je Werk eine Expression. Das hält die Daten klein und bleibt für den Regelfall der
einfachere Weg; `voices` steht dafür schon bereit.

**Preis.** Verzeichnisse können uneinheitlich arbeiten. Eine Empfehlung braucht die
Erfahrung eines echten Verzeichnisses.
