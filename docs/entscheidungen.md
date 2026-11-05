# Entscheidungen

Begründungen zur Vorlage. Die Entscheidungen zum Lasso-Verzeichnis, aus dem sie
hervorgeht, stehen im Branch `lasso` in derselben Datei.

## 1. Vorlage statt Lasso-Sonderfall

**Entscheidung.** `main` enthält nur ein allgemeines Modell, leere Datendateien, einen
erfundenen Beispieldatensatz, die Lasso-Testauszüge und Werkzeuge. Lasso-Daten und
Lasso-spezifische Felder (LV-Nummern, LV-Anhang, Excel-Import, TeX-Auszug) sind entfernt.

**Begründung.** Das Lasso-Projekt soll Grundlage für weitere Werkverzeichnisse sein.

**Preis.** Lasso nutzt die Vorlage noch nicht und bleibt im Branch `lasso` beim eigenen
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

## 5. Eine Expression je Werk

**Entscheidung.** Ein Werk hat eine Expression. Die Stimmenzahl steht am Stück in der
jeweiligen Quelle (`voices` in `contents`), die Besetzung an der Expression nur dann,
wenn sie eindeutig ist.

**Anlass.** Ein erster Härtetest legte je belegter Stimmenzahl eine Expression an. Das
ergäbe bei Lasso rund 3300 Expressions bei 2166 Werken und setzte jede abweichende
Zählung mit einer Fassung gleich, auch wenn eine Quelle nur Stimmen verloren hat.

**Alternative.** Je Stimmenzahl eine Expression: näher an der Idee von LRM, aber mit
vielen Datensätzen und einer stillschweigenden fachlichen Setzung.

**Preis.** Welche Stimmen ein Werk in welcher Gestalt hat, ist nur je Quelle ablesbar,
nicht als eigene Gestalt des Werks. Die in Lasso ausdrücklich als Fassung
gekennzeichneten Stücke, etwa `74 (IV)`, bleiben im Härtetest vorerst eigene
Expressions, damit die Kennzeichnung nicht verloren geht.

## 6. Stücke ohne Werk in einer Quelle

**Entscheidung.** `embodies` ist in `contents` optional, wenn `titleInSource` angegeben
ist. So kann eine Quelle ein Stück nennen, das keinem Werk zugeordnet ist.

**Anlass.** Bei Lasso sind 311 Handschriftenzeugnisse keinem Werk zugeordnet (siehe
`lasso`, Abschnitt 14). Ohne dieses Feld standen sie nur als Textblock in einer Anmerkung.

**Alternative.** Für jedes solche Stück ein Werk anlegen: Das unterstellte eine
Zuordnung, die noch nicht feststeht.

**Preis.** Solche Stücke sind nicht über ein Werk auffindbar, sondern nur über die Quelle.
In MeLODy erscheinen sie als Textzeile im Inhaltsverzeichnis, weil `lrmoo:R4_embodies`
ein Ziel braucht. Ob zwei gleich lautende Stücke dasselbe sind, bleibt offen.

## 7. Frühester Druck aus dem Datum statt eigenes Feld

**Entscheidung.** Ob ein Druck der früheste eines Werks ist, steht nicht in den Daten.
Die Oberfläche leitet es aus dem Datum ab, innerhalb eines Jahres aus der laufenden
Nummer der Sigle, und nennt es „Frühester Druck“. Ohne solche Nummer bleiben alle
Drucke des Jahres markiert.

**Alternative.** Ein Feld in `contents`: Es wäre redundant und könnte dem Datum
widersprechen.

**Begründung.** Gegen die 1977 Lasso-Werke mit angegebenem Erstdruck geprüft: Das
früheste Jahr trifft 1820-mal genau, die laufende Nummer entscheidet weitere 150. Bei
7 Werken weicht es ab, in den 6 angesehenen Fällen, weil ein Teil oder eine Fassung
früher erschien als das Werk als Ganzes. Deshalb „Frühester Druck“ statt „Erstdruck“.

**Preis.** Ein zweiter Erstdruck in anderer Besetzung ist nicht mehr gekennzeichnet (bei
Lasso 30 Werke), und das Datum „ca. 1558“ zählt als 1558. Eine redaktionelle Korrektur
der Ableitung ist nicht vorgesehen, bis ein echter Fall sie verlangt.

## 8. Datierung an der Handschrift

**Entscheidung.** `dating` steht an der Manifestation, nicht am Stück in `contents`. Es
ist Text wie in der Literatur. Drucke tragen ihr Datum weiter in `publication`.

**Anlass.** Die Lasso-Tabelle hat eine Zeile je Stück und wiederholt dort die Datierung
der Handschrift. Der erste Härtetest übernahm sie je Stück, und die Oberfläche zeigte
sie dadurch wie eine Eigenschaft des Stücks.

**Alternative.** `publication` auch für Handschriften: Das Feld hätte schon Platz für
Text und Datum, eine Handschrift ist aber nicht veröffentlicht.

**Begründung.** Die Datierung beschreibt die Quelle. Von den 1410 Lasso-Handschriften
im Branch `lasso` haben 1403 genau einen Wert, 3 keinen und 4 mehrere: D-Rp A.R. 233-238,
D-Rp Pr-M Lasso III/24, D-Po Lasso 5 und A-Wn Mus.Hs.19428.

**Preis.** Entstand eine Handschrift nachweislich in Abschnitten, lässt sich das nur als
Text ausdrücken. Die 4 Handschriften mit mehreren Werten sind fachlich nicht geklärt. Die
Konvertierung behält ihre Werte als Text, etwa „um 1585; um 1590“, und meldet sie in
`luecken.json`. In den beiden Testauszügen kommen sie nicht vor.
