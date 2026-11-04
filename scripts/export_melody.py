#!/usr/bin/env python3
"""Exportiert data/ als Turtle-Dateien fuer MerMEId MeLODy.

Aufruf:  python scripts/export_melody.py --out ORDNER [--print SIGLE]

Ohne --print wird alles exportiert, mit --print nur die Werke dieses Drucks
samt den Drucken, Handschriften, Personen und Baenden, die zu ihnen gehoeren.
Das Skript liest nur data/ und schreibt nur in den leeren Zielordner. Die
Abbildung und ihre Luecken beschreibt docs/melody-abbildung.md.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

PREFIXES = {
    "cidoc": "http://www.cidoc-crm.org/cidoc-crm/",
    "dct": "http://purl.org/dc/terms/",
    "lrmoo": "http://iflastandards.info/ns/lrm/lrmoo/",
    "melod": "https://lod.academy/melod/vocab/ontology#",
    "melodTerms": "https://lod.academy/melod/vocab/terms#",
    "mus": "http://data.doremus.org/ontology#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "schema": "https://schema.org/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}
LANGUAGES = {
    "Latein": "melodTerms:Latin",
    "Italienisch": "melodTerms:Italian",
    "Französisch": "melodTerms:French",
    "Deutsch": "melodTerms:German",
}
LANGUAGE_TAGS = {"Latein": "la", "Italienisch": "it", "Französisch": "fr", "Deutsch": "de"}
UNKNOWN_LANGUAGE = "und"  # BCP 47: unbestimmt, fuer Werke ohne Sprachangabe
LASSO = "persons/lasso"
RE_LINK = re.compile(r"^https?://.+?/.+")


class Term(str):
    """Ein Begriff mit Praefix, in Turtle ohne Anfuehrungszeichen."""


class Typed:
    """Ein Literal mit Datentyp."""

    def __init__(self, value, datatype):
        self.value = value
        self.datatype = datatype


class Tagged:
    """Ein Literal mit Sprach-Tag."""

    def __init__(self, value, language):
        self.value = value
        self.language = language


def slug(text):
    """Macht aus einer Kennung einen Dateinamen; die Kennung bleibt erkennbar."""
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")


def iri(path):
    """Der Editor bildet die IRI aus dem Dateipfad (urn:uuid:works/90)."""
    return "<urn:uuid:{0}>".format(path)


def ref(path):
    return Term(iri(path))


def literal(value):
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    text = text.replace("\r", "").replace("\n", "\\n").replace("\t", "\\t")
    return '"{0}"'.format(text)


def render(value, indent):
    if isinstance(value, Term):
        return str(value)
    if isinstance(value, Typed):
        return "{0}^^{1}".format(literal(value.value), value.datatype)
    if isinstance(value, Tagged):
        return "{0}@{1}".format(literal(value.value), value.language)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):  # Blankoknoten als Liste von Paaren
        return "[\n{0}\n{1}]".format(render_pairs(value, indent + 4), " " * indent)
    return literal(value)


def render_pairs(pairs, indent):
    lines = []
    for predicate, value in pairs:
        lines.append("{0}{1} {2}".format(" " * indent, predicate, render(value, indent)))
    return " ;\n".join(lines)


def annotation(label, text):
    return ("melod:hasAnnotation", [
        ("a", Term("melod:Annotation")),
        ("rdfs:label", label),
        ("melod:paragraph", Typed(html.escape(str(text), quote=False), "rdf:HTML")),
    ])


def identifier(label, value):
    return ("melod:hasIdentifier", [
        ("a", Term("melod:Identifier")),
        ("rdfs:label", label),
        ("owl:hasValue", str(value)),
    ])


def title_language(item):
    """Werke und Fassungen verlangen Titel mit Sprach-Tag."""
    languages = item["languages"]
    return LANGUAGE_TAGS[languages[0]] if languages else UNKNOWN_LANGUAGE


def title(label, title_type=None, language=None):
    text = Tagged(label, language) if language else label
    pairs = [("a", Term("melod:Title")), ("rdfs:label", text)]
    if title_type:
        pairs.append(("melod:hasTitleType", Term("melodTerms:" + title_type)))
    return ("melod:hasTitle", pairs)


def contribution(person, role, uncertain=False):
    pairs = [
        ("a", Term("melod:Contribution")),
        ("melod:hasAgent", ref(person)),
        ("melod:hasRole", Term("melodTerms:" + role)),
    ]
    if uncertain:
        pairs.append(("melod:hasCertainty", Term("melodTerms:LowCertainty")))
    return ("melod:hasContribution", pairs)


def publication(year=None, approximate=False, place=None, publisher=None):
    """Ein Jahr wird wie in der MeLODy-Vorlage zum Zeitraum eines Jahres."""
    pairs = [("a", Term("schema:PublicationEvent"))]
    if publisher:  # schema:publishedBy erlaubt nur Personen, siehe Abbildung
        pairs.append(("rdfs:label", publisher))
    if year:
        pairs.append(("schema:startDate", Typed("{0}-01-01".format(year), "xsd:date")))
        pairs.append(("schema:endDate", Typed("{0}-12-31".format(year), "xsd:date")))
        if approximate:
            pairs.append(("schema:description", "ca. {0}".format(year)))
    if place:
        pairs.append(("schema:location", ref(place)))
    return ("schema:publication", pairs)


class Export:
    """Sammelt die Entitaeten; jede wird zu einer Datei folder/id.ttl."""

    def __init__(self):
        self.entities = {}
        self.folded = set()

    def add(self, path, pairs):
        # Ohne Gross- und Kleinschreibung, sonst ueberschreibt unter Windows
        # etwa E-Sc.ttl (Sevilla) die Datei E-SC.ttl (Santiago).
        if path.casefold() in self.folded:
            raise SystemExit("Zwei Entitaeten ergeben dieselbe Datei: " + path)
        self.folded.add(path.casefold())
        self.entities[path] = pairs

    def place(self, name):
        path = "places/" + slug(name)
        if path not in self.entities:
            self.add(path, [("a", Term("melod:Place")), ("schema:name", name)])
        return path

    def person(self, name):
        """Herausgeber: Der Name wird nicht zerlegt, das waere eine Setzung."""
        path = "persons/" + slug(name)
        if path not in self.entities:
            self.add(path, [("a", Term("melod:Person")), ("schema:familyName", name)])
        return path

    def instrumentation(self, voices):
        path = "instrumentations/{0}-stimmen".format(voices)
        if path not in self.entities:
            self.add(path, [
                ("a", Term("melod:Instrumentation")),
                ("rdfs:label", "{0} {1}".format(voices, "Stimme" if voices == 1 else "Stimmen")),
                ("melod:hasInstrumentationDetail", [
                    ("a", Term("melod:InstrumentationDetail")),
                    ("schema:position", 1),
                    ("mus:U2_foresees_use_of_medium_of_performance", Term("melodTerms:Voices")),
                    ("schema:description", "Stimmen"),
                    ("mus:U30_foresees_quantity_of_medium_of_performance", voices),
                ]),
                ("dct:conformsTo", Term("melod:Instrumentation")),
            ])
        return path

    def write(self, out):
        for path, pairs in self.entities.items():
            target = out / (path + ".ttl")
            target.parent.mkdir(parents=True, exist_ok=True)
            head = "".join(
                "@prefix {0}: <{1}> .\n".format(k, v) for k, v in PREFIXES.items()
            )
            body = "{0}\n{1} .\n".format(iri(path), render_pairs(pairs, 4))
            target.write_text(head + "\n" + body, encoding="utf-8", newline="\n")


def load(name):
    with (DATA_DIR / (name + ".json")).open(encoding="utf-8") as handle:
        return json.load(handle)["items"]


def work_path(work):
    return "works/" + slug(work["@id"].split(":", 1)[1])


def expression_of_work(work):
    """Die Expression gibt es nur im Export, siehe Abbildung."""
    return "expressions/" + slug(work["@id"].split(":", 1)[1])


def expression_path(expression):
    return "expressions/" + slug(expression["@id"].split(":", 1)[1])


def print_path(siglum):
    return "manifestations/" + slug(siglum)


def source_key(manuscript):
    return manuscript["rismSiglum"], manuscript["shelfmark"]


def source_slugs(keys):
    """Dateinamen je Quelle. Schreibvarianten wie "Mus. ms. 40209" und
    "Mus.ms. 40209" bleiben getrennt; ob sie eine Quelle sind, ist fachlich
    zu pruefen. Die Sortierung haelt die Zaehlung stabil."""
    result = {}
    used = set()
    for key in sorted(keys, key=lambda k: tuple(part or "" for part in k)):
        base = slug(" ".join(part for part in key if part)) or "ohne-angabe"
        name = base
        counter = 2
        while name.casefold() in used:
            name = "{0}-{1}".format(base, counter)
            counter += 1
        used.add(name.casefold())
        result[key] = name
    return result


def text_authors(item, persons):
    return [
        contribution(
            persons[person], "Lyricist", person in item["uncertainTextAuthors"]
        )
        for person in item["textAuthors"]
    ]


def shared_expression_fields(export, item):
    """Stimmen und Sprache; mehrere Stimmenzahlen passen nur in eine Anmerkung."""
    pairs = [("melod:inLanguage", Term(LANGUAGES[lang])) for lang in item["languages"]]
    if len(item["voiceCounts"]) == 1:
        path = export.instrumentation(item["voiceCounts"][0])
        pairs.append(("melod:hasInstrumentation", ref(path)))
    elif item["voiceCounts"]:
        counts = ", ".join(str(v) for v in item["voiceCounts"])
        pairs.append(annotation("Stimmenzahlen", counts))
    return pairs


def citation_notes(item, volume_of):
    pairs = []
    for volume in sorted({volume_of[a["inVolume"]] for a in item["editionAppearances"]}):
        pairs.append(("schema:citation", ref(volume)))
    if item["completeEditions"]:
        # Die Verknuepfung kennt keine Stelle im Band; sie bleibt hier erhalten.
        pairs.append(annotation("Gesamtausgabe", "; ".join(item["completeEditions"])))
    return pairs


def export_works(export, works, entry_by_id, persons, volume_of, selected_expressions):
    for work in works:
        pairs = [
            ("a", Term("melod:Work")),
            title(work["preferredTitle"], "MainTitle", title_language(work)),
        ]
        pairs += [title(t, "OtherTitle", title_language(work)) for t in work["variantTitles"]]
        if work["lv"]:
            pairs.append(identifier("LV", work["lv"]))
        if work["lvAnh"] is not None:
            pairs.append(identifier("LV-Anhang", work["lvAnh"]))
        pairs.append(contribution(LASSO, "Composer"))
        pairs += text_authors(work, persons)
        pairs.append(("lrmoo:R3_is_realised_in", ref(expression_of_work(work))))
        for expression in work["expressions"]:
            if expression in selected_expressions:
                pairs.append(("lrmoo:R3_is_realised_in", ref(selected_expressions[expression])))
        if work["isPartOf"]:
            pairs.append(("melod:isWorkPartOf", ref(slug_work(work["isPartOf"]))))
        for part in work["hasPart"]:
            pairs.append(("melod:hasWorkPart", ref(slug_work(part))))
        pairs += citation_notes(work, volume_of)
        if work["textSources"]:
            pairs.append(annotation("Textprovenienz", "; ".join(work["textSources"])))
        notes = [entry_by_id[e]["note"] for e in work["entries"] if entry_by_id[e]["note"]]
        if notes:
            pairs.append(annotation("Bemerkung", "; ".join(notes)))
        pairs.append(("melod:memberOfDataCollection", ref("dataCollections/works")))
        pairs.append(("dct:conformsTo", Term("melod:Work")))
        export.add(work_path(work), pairs)

        expression = [("a", Term("melod:Expression")), ("rdfs:label", work["preferredTitle"])]
        expression += shared_expression_fields(export, work)
        if work["isPartOf"]:
            expression.append(("melod:isExpressionPartOf", ref(slug_expression(work["isPartOf"]))))
        for part in work["hasPart"]:
            expression.append(("melod:hasExpressionPart", ref(slug_expression(part))))
        expression.append(("dct:conformsTo", Term("melod:Expression")))
        export.add(expression_of_work(work), expression)


def slug_work(work_id):
    return "works/" + slug(work_id.split(":", 1)[1])


def slug_expression(work_id):
    return "expressions/" + slug(work_id.split(":", 1)[1])


def export_fassungen(export, expressions, persons, volume_of):
    for item in expressions:
        pairs = [
            ("a", Term("melod:Expression")),
            ("rdfs:label", item["preferredTitle"]),
            identifier("LV", item["lv"]),
        ]
        pairs += [title(t, None, title_language(item)) for t in item["variantTitles"]]
        pairs += shared_expression_fields(export, item)
        pairs += text_authors(item, persons)
        pairs += citation_notes(item, volume_of)
        if item["textSources"]:
            pairs.append(annotation("Textprovenienz", "; ".join(item["textSources"])))
        pairs.append(annotation("Pars", item["pars"]))
        pairs.append(("dct:conformsTo", Term("melod:Expression")))
        export.add(expression_path(item), pairs)


def export_prints(export, prints, contents, embodied, known_sigla):
    for item in prints:
        siglum = item["siglum"]
        pairs = [
            ("a", Term("melod:Manifestation")),
            title(item["shortTitle"] or item["title"] or siglum),
            ("melod:hasClassification", Term("melodTerms:Print")),
            identifier("Sigle", siglum),
        ]
        pairs += [identifier(k, v) for k, v in item["references"].items()]
        if item["rism"] and RE_LINK.match(item["rism"]):
            pairs.append(("owl:sameAs", Term("<{0}>".format(item["rism"]))))
        if item["title"]:
            pairs.append(("melod:hasTitlePage", [
                ("a", Term("melod:TitlePage")),
                ("melod:paragraph", Typed(html.escape(item["title"], quote=False), "rdf:HTML")),
            ]))
        pairs.append(publication(item["year"], item["dateApproximate"]))
        if item["description"]:
            pairs.append(annotation("Beschreibung", item["description"]))
        if item["partbooks"]:
            pairs.append(annotation("Stimmbücher", item["partbooks"]))
        pairs += contents_field(contents.get(item["@id"]))
        pairs += [("lrmoo:R4_embodies", ref(p)) for p in sorted(embodied.get(item["@id"], ()))]
        if item["part"]:
            base = siglum.split("/")[0]
            if base in known_sigla:
                pairs.append(("melod:isManifestationPartOf", ref(print_path(base))))
        for other in sorted(known_sigla):
            if other.startswith(siglum + "/"):
                pairs.append(("melod:hasManifestationPart", ref(print_path(other))))
        pairs.append(("melod:memberOfDataCollection", ref("dataCollections/manifestations")))
        pairs.append(("dct:conformsTo", Term("melod:Manifestation")))
        export.add(print_path(siglum), pairs)


def contents_field(lines):
    """Die Stelle im Druck hat keine eigene Verknuepfung, siehe Abbildung."""
    if not lines:
        return []
    return [("melod:hasContents", [
        ("a", Term("melod:Contents")),
        ("rdfs:label", "Inhalt"),
        ("melod:paragraph", "\n".join(lines)),
    ])]


def print_contents(works, expressions):
    """Sammelt je Druck die Inhaltszeilen und die verkoerperten Expressions."""
    contents = defaultdict(list)
    embodied = defaultdict(set)
    for work in works:
        target = expression_of_work(work)
        label = "LV {0}".format(work["lv"]) if work["lv"] else "LVanh {0}".format(work["lvAnh"])
        for appearance in work["printAppearances"]:
            embodied[appearance["inPrint"]].add(target)
            line = "Nr. {0}: {1}, {2}".format(appearance["piece"], label, work["preferredTitle"])
            if appearance.get("note"):
                line += " ({0})".format(appearance["note"])
            contents[appearance["inPrint"]].append(line)
        for siglum in work["prints"]:
            embodied["print:" + siglum].add(target)
    for item in expressions:
        for siglum in item["prints"]:
            embodied["print:" + siglum].add(expression_path(item))
    for lines in contents.values():
        lines.sort(key=piece_sort_key)
    return contents, embodied


def piece_sort_key(line):
    return [int(p) if p.isdigit() else p for p in re.split(r"(\d+)", line)][1:2], line


def distinct(rows, field):
    values = []
    for row in rows:
        if row[field] and row[field] not in values:
            values.append(row[field])
    return values


def export_manuscripts(export, sources, selected_works, by_lv, by_anh):
    libraries = defaultdict(set)
    for rows in sources.values():
        for row in rows:
            libraries[row["rismSiglum"]].add(row["library"])

    # Dateinamen vorab festlegen, damit die Zaehlung nicht von der Reihenfolge abhaengt.
    def institution_key(row):
        siglum, library = row["rismSiglum"], row["library"]
        if siglum and len(libraries[siglum]) == 1:
            return (siglum, None)
        return (siglum, library)

    institution_slugs = source_slugs(
        {institution_key(row) for rows in sources.values() for row in rows}
    )
    institutions = set()

    def institution(row):
        siglum, library = row["rismSiglum"], row["library"]
        name = library or siglum
        if not name:
            return None
        path = "institutions/" + institution_slugs[institution_key(row)]
        if path not in institutions:
            institutions.add(path)
            pairs = [("a", Term("melod:Institution")), ("schema:name", name)]
            if siglum:
                pairs.append(("melod:hasSiglum", siglum))
            if row["place"]:
                pairs.append(("schema:location", ref(export.place(row["place"]))))
            pairs.append(("dct:conformsTo", Term("melod:Institution")))
            export.add(path, pairs)
        return path

    slugs = source_slugs(sources)
    for key, rows in sources.items():
        name = " ".join(part for part in key if part) or "Ohne Angabe"
        path = slugs[key]
        lines = []
        expressions = set()
        for row in rows:
            label = "LV {0}".format(row["lv"]) if row["lv"] else (
                "LVanh {0}".format(row["lvAnh"]) if row["lvAnh"] is not None else "ohne LV"
            )
            details = [str(v) for v in (row["voices"], row["dating"], row["note"]) if v]
            line = "{0}: {1}".format(label, row["title"])
            if details:
                line += " ({0})".format("; ".join(details))
            lines.append(line)
            work = by_lv.get(row["lv"]) if row["lv"] else by_anh.get(row["lvAnh"])
            if work and work["@id"] in selected_works:
                expressions.add(expression_of_work(work))

        manifestation = "manifestations/hs-" + path
        pairs = [
            ("a", Term("melod:Manifestation")),
            title(name),
            ("melod:hasClassification", Term("melodTerms:Manuscript")),
        ]
        for field, label in (
            ("sourceType", "Quellenart"),
            ("provenance", "Provenienz"),
            ("sourceNote", "Bemerkung"),
            ("literature", "Literatur"),
        ):
            pairs += [annotation(label, value) for value in distinct(rows, field)]
        pairs += contents_field(lines)
        pairs += [("lrmoo:R4_embodies", ref(p)) for p in sorted(expressions)]
        pairs.append(("melod:memberOfDataCollection", ref("dataCollections/manifestations")))
        pairs.append(("dct:conformsTo", Term("melod:Manifestation")))
        export.add(manifestation, pairs)

        item = [("a", Term("melod:Item")), ("rdfs:label", name)]
        keeper = institution(rows[0])
        if keeper:
            item.append(("cidoc:P50_has_current_keeper", ref(keeper)))
        if key[1]:
            item.append(("melod:hasShelfmark", key[1]))
        former = distinct(rows, "shelfmarkAlt")
        if former:
            item.append(("melod:hasFormerShelfmark", former[0]))
        item += [
            ("owl:sameAs", Term("<{0}>".format(link)))
            for link in distinct(rows, "link")
            if RE_LINK.match(link) and " " not in link
        ]
        item.append(("lrmoo:R7_exemplifies", ref(manifestation)))
        export.add("items/hs-" + path, item)


def export_persons(export, persons, used):
    export.add(LASSO, [
        ("a", Term("melod:Person")),
        ("schema:familyName", "Lasso"),
        ("schema:givenName", "Orlando di"),
    ])
    for person in persons:
        if person["@id"] not in used:
            continue
        pairs = [("a", Term("melod:Person")), ("schema:familyName", person["preferredName"])]
        pairs += [("schema:alternateName", name) for name in person["variantNames"]]
        pairs += [
            ("owl:sameAs", Term("<{0}>".format(link)))
            for link in (person["gnd"], person["viaf"])
            if link
        ]
        export.add(person_path(person["@id"]), pairs)


def person_path(person_id):
    return "persons/" + slug(person_id.split(":", 1)[1])


def volume_path(volume_id):
    return "bibliography/" + slug(volume_id.split(":", 1)[1])


def export_editions(export, editions, used_volumes):
    """Die Ausgabe wird zur Reihe, der Band zum Eintrag mit Bandnummer."""
    for edition in editions:
        volumes = [v for v in edition["volumes"] if volume_path(v["@id"]) in used_volumes]
        if not volumes:
            continue
        series = volume_path(edition["@id"])
        export.add(series, [
            ("a", Term("melod:Bibliography")),
            ("schema:genre", Term("melodTerms:Book")),
            ("melod:hasAbbreviation", edition["siglum"]),
            ("melod:hasTitle", [("a", Term("melod:Title")), ("rdfs:label", edition["title"])]),
            publication(),
            ("schema:description", edition["shortTitle"]),
        ])
        for volume in volumes:
            pairs = [
                ("a", Term("melod:Bibliography")),
                ("schema:genre", Term("melodTerms:Book")),
                ("melod:hasAbbreviation", "{0} {1}".format(edition["siglum"], volume["volume"])),
                ("melod:hasTitle", [("a", Term("melod:Title")), ("rdfs:label", volume["title"])]),
            ]
            pairs += [("melod:hasEditor", ref(export.person(name))) for name in volume["editors"]]
            place = export.place(volume["place"]) if volume["place"] else None
            pairs.append(publication(
                volume["year"], volume["dateApproximate"], place, volume["publisher"]
            ))
            pairs.append(("schema:isPartOf", ref(series)))
            pairs.append(("schema:position", volume["volume"]))
            export.add(volume_path(volume["@id"]), pairs)


def export_catalog(export):
    export.add("dataCatalogs/catalog", [
        ("a", Term("melod:DataCatalog")),
        ("rdfs:label", "Werkverzeichnis Orlando di Lasso"),
        ("melod:usesApplication", "MerMEId MeLODy"),
        ("dct:conformsTo", Term("melod:DataCatalog")),
    ])
    for name, label, kind in (
        ("works", "All works", "work catalog"),
        ("manifestations", "All manifestations", "source catalog"),
    ):
        export.add("dataCollections/" + name, [
            ("a", Term("melod:DataCollection")),
            ("rdfs:label", label),
            ("melod:hasClassification", kind),
            ("schema:includedInDataCatalog", ref("dataCatalogs/catalog")),
        ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="leerer Zielordner")
    parser.add_argument("--print", dest="siglum", help="nur die Werke dieses Drucks")
    args = parser.parse_args()

    if args.out.exists() and any(args.out.iterdir()):
        raise SystemExit("Zielordner ist nicht leer: {0}".format(args.out))

    works = load("works")
    expressions = load("expressions")
    manuscripts = load("manuscripts")
    prints = load("prints")
    persons = load("persons")
    editions = load("editions")
    entry_by_id = {e["@id"]: e for e in load("entries")}

    if args.siglum:
        if not any(p["siglum"] == args.siglum for p in prints):
            raise SystemExit("Druck nicht gefunden: {0}".format(args.siglum))
        chosen = {
            w["@id"]
            for w in works
            if args.siglum in w["prints"]
            or any(a["inPrint"] == "print:" + args.siglum for a in w["printAppearances"])
        }
        by_id = {w["@id"]: w for w in works}
        for work_id in list(chosen):  # ein Teil kommt nicht ohne sein Gesamtwerk
            work = by_id[work_id]
            if work["isPartOf"]:
                chosen.add(work["isPartOf"])
            chosen.update(work["hasPart"])
        for work_id in list(chosen):
            chosen.update(by_id[work_id]["hasPart"])
        works = [w for w in works if w["@id"] in chosen]
        expressions = [x for x in expressions if x["realizationOf"] in chosen]
        ids = {m for w in works for m in w["manuscripts"]}
        keys = {source_key(m) for m in manuscripts if m["@id"] in ids}
        manuscripts = [m for m in manuscripts if source_key(m) in keys]
        sigla = {a["inPrint"] for w in works for a in w["printAppearances"]}
        sigla |= {"print:" + s for item in works + expressions for s in item["prints"]}
        prints = [p for p in prints if p["@id"] in sigla]

    all_volumes = {}
    for edition in editions:
        for volume in edition["volumes"]:
            path = volume_path(volume["@id"])
            all_volumes[volume["@id"]] = path
            for part in volume["parts"]:
                all_volumes[part["@id"]] = path

    selected = {w["@id"] for w in works}
    selected_expressions = {x["@id"]: expression_path(x) for x in expressions}
    person_paths = {p["@id"]: person_path(p["@id"]) for p in persons}
    used_persons = {p for item in works + expressions for p in item["textAuthors"]}
    used_volumes = {
        all_volumes[a["inVolume"]]
        for item in works + expressions
        for a in item["editionAppearances"]
    }
    # Im Gesamtexport gehoeren auch die nicht zitierten Baende dazu.
    if not args.siglum:
        used_volumes = set(all_volumes.values())
    by_lv = {w["lv"]: w for w in works if w["lv"]}
    by_anh = {w["lvAnh"]: w for w in works if w["lvAnh"] is not None}
    sources = defaultdict(list)
    for manuscript in manuscripts:
        sources[source_key(manuscript)].append(manuscript)

    export = Export()
    export_catalog(export)
    export_persons(export, persons, used_persons)
    export_editions(export, editions, used_volumes)
    export_works(export, works, entry_by_id, person_paths, all_volumes, selected_expressions)
    export_fassungen(export, expressions, person_paths, all_volumes)
    contents, embodied = print_contents(works, expressions)
    export_prints(export, prints, contents, embodied, {p["siglum"] for p in prints})
    export_manuscripts(export, sources, selected, by_lv, by_anh)
    export.write(args.out)

    counts = defaultdict(int)
    for path in export.entities:
        counts[path.split("/")[0]] += 1
    for folder, count in sorted(counts.items()):
        print("{0:<18}{1}".format(folder, count))
    print("{0:<18}{1}".format("insgesamt", len(export.entities)))
    print("Geschrieben nach {0}".format(args.out))


if __name__ == "__main__":
    main()
