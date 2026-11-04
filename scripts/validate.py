#!/usr/bin/env python3
"""Prueft einen Datenordner.

Aufruf:  python scripts/validate.py [ORDNER]   (Standard: data)

Prueft das Schema, eindeutige IDs, ob jeder Verweis ein Ziel hat, ob jedes Feld
im JSON-LD-Kontext abgebildet ist und ob die Daten als RDF lesbar sind.
"""

from __future__ import annotations

import json
import re
import sys

import jsonschema
import rdflib

from catalogue import COLLECTIONS, SCHEMA_PATH, load_catalogue, load_context, read_json

MAX_ID_LENGTH = 80
RE_REFERENCE = re.compile(r"^(?:" + "|".join(COLLECTIONS) + r"):[A-Za-z0-9-]+$")
# Schluessel, deren Wert kein Verweis ist, auch wenn er so aussieht.
TEXT_KEYS = {"value", "number", "note", "html", "description", "label", "@none"}


def walk(value, key=None):
    """Liefert alle Paare aus Feldname und Wert, auch verschachtelt."""
    if isinstance(value, dict):
        for child_key, child in value.items():
            yield child_key, child
            yield from walk(child, child_key)
    elif isinstance(value, list):
        for child in value:
            yield key, child
            yield from walk(child, key)


def check_schema(catalog, collections, errors):
    schema = read_json(SCHEMA_PATH)
    for name, records in [("catalog", [catalog])] + list(collections.items()):
        definition = "catalogue" if name == "catalog" else name
        validator = jsonschema.Draft202012Validator(
            {"$ref": "#/$defs/" + definition, "$defs": schema["$defs"]}
        )
        for record in records:
            for error in validator.iter_errors(record):
                where = "/".join(str(part) for part in error.path) or "(Datensatz)"
                errors.append("{0}, {1}: {2}".format(record.get("@id"), where, error.message))


def check_ids(collections, errors):
    """Eine ID wird im Export zum Dateinamen: Windows unterscheidet nicht zwischen
    E-SC und E-Sc, und lange Pfade scheitern dort."""
    known = set()
    folded = set()
    for records in collections.values():
        for record in records:
            identifier = record["@id"]
            if identifier.casefold() in folded:
                errors.append("ID doppelt vergeben (ohne Groß- und Kleinschreibung): {0}".format(identifier))
            if len(identifier) > MAX_ID_LENGTH:
                errors.append("ID länger als {0} Zeichen: {1}".format(MAX_ID_LENGTH, identifier))
            known.add(identifier)
            folded.add(identifier.casefold())
    return known


def check_references(records, known, errors):
    for record in records:
        for key, value in walk(record):
            if key not in TEXT_KEYS and key != "@id" and isinstance(value, str):
                if RE_REFERENCE.match(value) and value not in known:
                    errors.append("{0}: Verweis ohne Ziel: {1}".format(record["@id"], value))


def check_titles(collections, errors):
    for record in collections["works"]:
        main = [t for t in record["titles"] if t.get("type") == "terms:MainTitle"]
        if len(main) != 1:
            errors.append("{0}: braucht genau einen MainTitle".format(record["@id"]))


def check_context(records, context, errors):
    """Ein Feld ohne Abbildung wuerde JSON-LD stillschweigend verwerfen."""
    missing = set()
    for record in records:
        for key, value in walk(record):
            if isinstance(key, str) and not key.startswith("@") and key not in context:
                # Schluessel eines Sprach-Objekts sind Sprach-Tags, keine Felder.
                if not re.fullmatch(r"[a-z]{2,3}", key):
                    missing.add(key)
    errors.extend("Feld fehlt im Kontext: {0}".format(key) for key in sorted(missing))


def check_rdf(catalog, collections, context, errors):
    entries = [catalog] + [r for records in collections.values() for r in records]
    document = json.dumps({"@context": context, "entries": entries}, ensure_ascii=False)
    try:
        graph = rdflib.Graph().parse(data=document, format="json-ld")
    except Exception as error:  # rdflib meldet verschiedene Parserfehler
        errors.append("Nicht als JSON-LD lesbar: {0}".format(error))
        return 0
    return len(graph)


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "data"
    catalog, collections = load_catalogue(folder)
    context = load_context()
    errors = []
    check_schema(catalog, collections, errors)
    known = check_ids(collections, errors)
    records = [r for items in collections.values() for r in items]
    check_references(records, known, errors)
    check_titles(collections, errors)
    check_context(records + [catalog], context, errors)
    triples = check_rdf(catalog, collections, context, errors)

    counts = ", ".join("{0} {1}".format(len(v), k) for k, v in collections.items() if v)
    print("{0}: {1}".format(folder, counts or "keine Datensaetze"))
    if errors:
        print("{0} Fehler:".format(len(errors)))
        for error in errors:
            print("  " + error)
        raise SystemExit(1)
    print("Keine Fehler, {0} RDF-Aussagen.".format(triples))


if __name__ == "__main__":
    main()
