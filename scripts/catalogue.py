"""Gemeinsames Laden eines Datenordners, fuer validate.py und export_melody.py."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTEXT_PATH = ROOT / "schema" / "context.jsonld"
SCHEMA_PATH = ROOT / "schema" / "catalogue.schema.json"
# Reihenfolge der Dateien; jede enthaelt die Datensaetze eines Typs.
COLLECTIONS = (
    "works",
    "expressions",
    "manifestations",
    "items",
    "persons",
    "institutions",
    "places",
    "instrumentations",
    "bibliography",
)


def read_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_context():
    return read_json(CONTEXT_PATH)["@context"]


def load_catalogue(folder):
    """Liefert den Katalogdatensatz und je Typ die Liste der Datensaetze."""
    folder = Path(folder)
    collections = {
        name: read_json(folder / (name + ".json"))["entries"] for name in COLLECTIONS
    }
    catalog = read_json(folder / "catalog.json")
    catalog.pop("@context", None)
    return catalog, collections
