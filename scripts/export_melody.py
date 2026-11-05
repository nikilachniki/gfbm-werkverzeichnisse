#!/usr/bin/env python3
"""Exportiert einen Datenordner als Turtle-Dateien fuer MerMEId MeLODy.

Aufruf:  python scripts/export_melody.py --out ZIELORDNER [--data ORDNER]

Der Kontext verwendet die Begriffe von MeLODy, die meisten Felder ergeben also
direkt dieselben Aussagen. Eigene Erweiterungen kennt MeLODy nicht: Sie werden
hier in dessen Form gebracht, Stellenangaben dabei zu Text, siehe docs/modell.md.
"""

from __future__ import annotations

import argparse
import copy
import html
import json
from collections import defaultdict
from pathlib import Path

import rdflib
from rdflib.compare import to_canonical_graph

from catalogue import load_catalogue, load_context

# Verschachtelte Objekte brauchen in MeLODy einen Typ, im JSON sind sie ueberfluessig.
NESTED_TYPES = {
    "titles": "melod:Title",
    "identifiers": "melod:Identifier",
    "contributors": "melod:Contribution",
    "notes": "melod:Annotation",
    "titlePages": "melod:TitlePage",
    "publication": "schema:PublicationEvent",
    "key": "melod:Key",
    "meter": "melod:Meter",
    "incipit": "melod:MusicIncipit",
    "dateCreated": "melod:ExactDate",
    "birthDate": "melod:ExactDate",
    "deathDate": "melod:ExactDate",
    "details": "melod:InstrumentationDetail",
}
PREFIXES = ("melod", "lrmoo", "cidoc", "mus", "schema", "owl", "rdf", "rdfs", "xsd")
CONFORMS_TO = {"Work", "Expression", "Manifestation", "Institution", "Instrumentation"}
DCT_CONFORMS = "http://purl.org/dc/terms/conformsTo"


def add_nested_types(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in NESTED_TYPES:
                for member in child if isinstance(child, list) else [child]:
                    member["@type"] = NESTED_TYPES[key]
            add_nested_types(child)
    elif isinstance(value, list):
        for child in value:
            add_nested_types(child)


def note(label, text):
    return {"label": label, "html": html.escape(text, quote=False)}


def citation_text(citation, abbreviations):
    parts = [abbreviations[citation["inBibliography"]]]
    if citation.get("section"):
        parts.append(citation["section"])
    if citation.get("number"):
        parts.append("Nr. " + citation["number"])
    if citation.get("page"):
        parts.append("S. {0}".format(citation["page"]))
    if citation.get("note"):
        parts.append(citation["note"])
    return ", ".join(parts)


def flatten_citations(record, abbreviations):
    """Der Verweis bleibt, die Stelle wird zur Anmerkung."""
    citations = record.pop("citations", None)
    if not citations:
        return
    record["schema:citation"] = [
        {"@id": ref}
        for ref in sorted({citation["inBibliography"] for citation in citations})
    ]
    text = "; ".join(citation_text(citation, abbreviations) for citation in citations)
    record.setdefault("notes", []).append(note("Fundstelle", text))


def content_line(content, labels):
    # Ein Stueck ohne Werk hat nur seinen Titel in der Quelle.
    assigned = "embodies" in content
    line = labels.get(content["embodies"], content["embodies"]) if assigned else content["titleInSource"]
    if content.get("position"):
        place = content["position"]
        if content.get("part"):
            place = "{0}, Teil {1}".format(place, content["part"])
        line = "Nr. {0}: {1}".format(place, line)
    elif content.get("part"):
        line = "Teil {0}: {1}".format(content["part"], line)
    details = [content.get("titleInSource")] if assigned else []
    if content.get("voices"):
        details.append("{0} Stimmen".format(content["voices"]))
    details.append(content.get("note"))
    details = [detail for detail in details if detail]
    return "{0} ({1})".format(line, "; ".join(details)) if details else line


def flatten_contents(record, labels):
    """Jedes Stueck wird zu lrmoo:R4_embodies, die Angaben dazu zu einer Textzeile."""
    contents = record.pop("contents", None)
    if not contents:
        return
    embodied = sorted({content["embodies"] for content in contents if "embodies" in content})
    if embodied:
        record["lrmoo:R4_embodies"] = [{"@id": ref} for ref in embodied]
    # melod:Annotation, denn so speichert es der Editor (Shape melod:Contents).
    record["melod:hasContents"] = {
        "@type": "melod:Annotation",
        "rdfs:label": "Inhalt",
        "melod:paragraph": "\n".join(content_line(c, labels) for c in contents),
    }


def fields_to_notes(record, fields):
    """Eigene Textfelder werden zu Anmerkungen, Listen je eine."""
    for field, label in fields:
        value = record.pop(field, None)
        if not value:
            continue
        for text in value if isinstance(value, list) else [value]:
            record.setdefault("notes", []).append(note(label, text))


def merge_publisher(record):
    publication = record.get("publication")
    if publication and publication.get("publisherName"):
        parts = [publication.pop("publisherName"), publication.get("label")]
        publication["label"] = ", ".join(part for part in parts if part)


def add_inverse(records, field, inverse):
    """MeLODy speichert Teil-Beziehungen in beiden Richtungen, wir nur in einer."""
    parts = defaultdict(list)
    for record in records:
        if field in record:
            parts[record[field]].append({"@id": record["@id"]})
    for record in records:
        if record["@id"] in parts:
            record[inverse] = parts[record["@id"]]


def add_bookkeeping(record):
    if record["@type"] in CONFORMS_TO:
        record[DCT_CONFORMS] = {"@id": "melod:" + record["@type"]}
    if record["@type"] in ("Work", "Manifestation"):
        collection = "works" if record["@type"] == "Work" else "manifestations"
        record["melod:memberOfDataCollection"] = {
            "@id": "urn:uuid:dataCollections/" + collection
        }


def to_melody(catalog, collections):
    """Bringt die Datensaetze in die Form, die MeLODy erwartet."""
    collections = copy.deepcopy(collections)
    catalog = copy.deepcopy(catalog)
    labels = {record["@id"]: record["label"] for record in collections["expressions"]}
    abbreviations = {r["@id"]: r["abbreviation"] for r in collections["bibliography"]}

    for name in ("works", "expressions"):
        for record in collections[name]:
            flatten_citations(record, abbreviations)
    for work in collections["works"]:
        genres = work.pop("genres", None)
        if genres:
            work.setdefault("notes", []).append(note("Gattung", "; ".join(genres)))
    for name in ("works", "expressions"):
        for record in collections[name]:
            fields_to_notes(record, (("textSources", "Textprovenienz"),))
    for record in collections["manifestations"]:
        flatten_contents(record, labels)
        fields_to_notes(record, (
            ("sourceType", "Quellenart"),
            ("partbooks", "Stimmbücher"),
            ("dating", "Datierung"),
            ("literature", "Literatur"),
        ))
    for name in ("manifestations", "bibliography"):
        for record in collections[name]:
            merge_publisher(record)
    for record in collections["bibliography"]:
        # schema:publication ist hier Pflicht, auch wenn sie leer bleibt.
        record.setdefault("publication", {})

    add_inverse(collections["works"], "partOfWork", "melod:hasWorkPart")
    add_inverse(collections["expressions"], "partOfExpression", "melod:hasExpressionPart")
    add_inverse(collections["manifestations"], "partOfManifestation", "melod:hasManifestationPart")

    records = [record for items in collections.values() for record in items]
    for record in records:
        add_bookkeeping(record)
    add_nested_types(records)

    catalog.pop("composer", None)
    catalog.pop("catalogueAbbreviation", None)
    catalog["melod:usesApplication"] = "MerMEId MeLODy"
    catalog[DCT_CONFORMS] = {"@id": "melod:DataCatalog"}
    collection_records = [
        {
            "@id": "urn:uuid:dataCollections/" + name,
            "@type": "melod:DataCollection",
            "rdfs:label": label,
            "melod:hasClassification": kind,
            "schema:includedInDataCatalog": {"@id": catalog["@id"]},
        }
        for name, label, kind in (
            ("works", "All works", "work catalog"),
            ("manifestations", "All manifestations", "source catalog"),
        )
    ]
    return records + [catalog] + collection_records


def closure(graph, subject):
    """Die Aussagen eines Datensatzes samt seinen verschachtelten Objekten."""
    result = rdflib.Graph()
    stack = [subject]
    while stack:
        current = stack.pop()
        for triple in graph.triples((current, None, None)):
            result.add(triple)
            if isinstance(triple[2], rdflib.BNode):
                stack.append(triple[2])
    return result


def write_turtle(graph, context, out):
    written = defaultdict(int)
    for subject in sorted(set(graph.subjects())):
        if not isinstance(subject, rdflib.URIRef) or not str(subject).startswith("urn:uuid:"):
            continue
        path = str(subject)[len("urn:uuid:"):]
        # Kanonische Blankoknoten, sonst wechselt die Reihenfolge von Lauf zu Lauf.
        part = rdflib.Graph()
        for triple in to_canonical_graph(closure(graph, subject)):
            part.add(triple)
        for prefix in PREFIXES:
            part.bind(prefix, context[prefix])
        part.bind("melodTerms", context["terms"])
        part.bind("dct", "http://purl.org/dc/terms/")
        target = out / (path + ".ttl")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(part.serialize(format="turtle"), encoding="utf-8", newline="\n")
        written[path.split("/")[0]] += 1
    return written


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data", help="Datenordner")
    parser.add_argument("--out", required=True, type=Path, help="leerer Zielordner")
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        raise SystemExit("Zielordner ist nicht leer: {0}".format(args.out))

    catalog, collections = load_catalogue(args.data)
    context = load_context()
    untagged = [
        record["@id"]
        for name in ("works", "expressions")
        for record in collections[name]
        if any("@none" in t["text"] for t in record.get("titles", []))
    ]
    if untagged:
        print("Hinweis: Titel ohne Sprache, im MeLODy-Editor nicht speichern: {0}".format(
            ", ".join(untagged)
        ))
    records = to_melody(catalog, collections)
    document = json.dumps({"@context": context, "entries": records}, ensure_ascii=False)
    graph = rdflib.Graph().parse(data=document, format="json-ld")
    written = write_turtle(graph, context, args.out)
    for folder, count in sorted(written.items()):
        print("{0:<18}{1}".format(folder, count))
    print("Geschrieben nach {0}".format(args.out))


if __name__ == "__main__":
    main()
