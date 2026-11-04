#!/usr/bin/env python3
"""Haertetest: uebertraegt den Lasso-Druck 1555-1 aus main in die Vorlage.

Aufruf (im Wurzelordner):  python examples/lasso-1555-1/konvertieren.py

Einmaliges Werkzeug fuer den Test, kein Teil der Vorlage. Liest die Lasso-Daten aus
dem Git-Stand von main, schreibt die Datensaetze in diesen Ordner und fuehrt in
luecken.json auf, was keinen passenden Platz gefunden hat.
"""

from __future__ import annotations

import html
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SIGLUM = "1555-1"
LANGUAGES = {
    "Latein": ("la", "terms:Latin"),
    "Italienisch": ("it", "terms:Italian"),
    "Französisch": ("fr", "terms:French"),
    "Deutsch": ("de", "terms:German"),
}
RE_LINK = re.compile(r"^https?://[^\s/<>\"{}|\\^`\[\]]+/[^\s<>\"{}|\\^`\[\]]+$")
LASSO = "persons:lasso"
gaps = Counter()
examples = defaultdict(list)


def source(name):
    text = subprocess.run(
        ["git", "show", "main:data/{0}.json".format(name)],
        capture_output=True, encoding="utf-8", check=True,
    ).stdout
    return json.loads(text)["items"]


def gap(kind, example):
    gaps[kind] += 1
    if len(examples[kind]) < 3:
        examples[kind].append(str(example)[:120])


def slug(text):
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")


def note(label, text):
    return {"label": label, "html": html.escape(str(text), quote=False)}


def key_of(row):
    return row["rismSiglum"], row["shelfmark"]


def main():
    works = source("works")
    entries = {entry["@id"]: entry for entry in source("entries")}
    manuscripts = source("manuscripts")
    prints = source("prints")
    persons = source("persons")
    editions = source("editions")
    by_id = {work["@id"]: work for work in works}

    # Die Werke des Drucks samt Gesamtwerken und Teilen.
    chosen = {
        work["@id"] for work in works
        if SIGLUM in work["prints"]
        or any(a["inPrint"] == "print:" + SIGLUM for a in work["printAppearances"])
    }
    for work_id in list(chosen):
        if by_id[work_id]["isPartOf"]:
            chosen.add(by_id[work_id]["isPartOf"])
    for work_id in list(chosen):
        chosen.update(by_id[work_id]["hasPart"])
    selected = [work for work in works if work["@id"] in chosen]
    manuscript_by_id = {row["@id"]: row for row in manuscripts}

    # Sprache: eigene, sonst die des Gesamtwerks.
    def language(work):
        base = by_id[work["isPartOf"]] if work["isPartOf"] else work
        family = [work, base] + [by_id[p] for p in base["hasPart"]]
        names = {name for member in family for name in member["languages"]}
        return names.pop() if len(names) == 1 else None

    # Eine Expression je belegter Stimmenzahl. Hat ein Werk mehrere, gibt es
    # zusaetzlich eine ohne Besetzung fuer Quellen, die keine Stimmenzahl belegen.
    def expression_for(work, voices=None):
        base = slug(work["lv"])
        counts = work["voiceCounts"]
        if len(counts) <= 1:
            return "expressions:" + base
        if voices in counts:
            return "expressions:{0}-{1}st".format(base, voices)
        return "expressions:" + base

    out = {name: [] for name in (
        "works", "expressions", "manifestations", "items", "persons",
        "institutions", "places", "instrumentations", "bibliography",
    )}
    used_counts = set()
    used_persons = set()
    used_volumes = set()
    volume_of = {}
    for edition in editions:
        for volume in edition["volumes"]:
            volume_of[volume["@id"]] = volume["@id"]
            for part in volume["parts"]:
                volume_of[part["@id"]] = volume["@id"]
    part_label = {
        part["@id"]: part["volume"].split(",")[-1]
        for edition in editions for volume in edition["volumes"] for part in volume["parts"]
    }

    def bib(edition_id):
        return "bibliography:" + slug(edition_id.split(":", 1)[1])

    for work in selected:
        name = language(work)
        tag = LANGUAGES[name][0] if name else "@none"
        if not name:
            gap("Titel ohne Sprache", work["@id"])
        record = {
            "@id": "works:" + slug(work["lv"]),
            "@type": "Work",
            "titles": [{"text": {tag: work["preferredTitle"]}, "type": "terms:MainTitle"}]
            + [{"text": {tag: t}, "type": "terms:OtherTitle"} for t in work["variantTitles"]],
            "identifiers": [{"list": "LV", "value": work["lv"]}],
            "contributors": [{"agent": LASSO, "role": "terms:Composer"}],
        }
        for person in work["textAuthors"]:
            used_persons.add(person)
            contributor = {"agent": "persons:" + slug(person.split(":", 1)[1]), "role": "terms:Lyricist"}
            if person in work["uncertainTextAuthors"]:
                contributor["certainty"] = "terms:LowCertainty"
            record["contributors"].append(contributor)
        counts = work["voiceCounts"]
        expression_ids = [expression_for(work)] if len(counts) <= 1 else (
            [expression_for(work)] + [expression_for(work, n) for n in counts]
        )
        record["realisedIn"] = expression_ids
        if work["isPartOf"]:
            record["partOfWork"] = "works:" + slug(by_id[work["isPartOf"]]["lv"])
        citations = []
        for appearance in work["editionAppearances"]:
            volume = volume_of[appearance["inVolume"]]
            used_volumes.add(volume)
            citation = {"inBibliography": bib(volume)}
            section = [part_label.get(appearance["inVolume"]), appearance.get("appendix")]
            section = ", ".join(part for part in section if part)
            if section:
                citation["section"] = section
            if "number" in appearance:
                citation["number"] = appearance["number"]
            if "page" in appearance:
                citation["page"] = appearance["page"]
            if "note" in appearance:
                citation["note"] = appearance["note"]
            citations.append(citation)
        if citations:
            record["citations"] = citations
        notes = []
        if work["textSources"]:
            gap("Textprovenienz nur als Anmerkung", work["textSources"][0])
            notes.append(note("Textprovenienz", "; ".join(work["textSources"])))
        for entry_id in work["entries"]:
            if entries[entry_id]["note"]:
                gap("Bemerkung zum Eintrag ohne Bezug zur Quelle", entries[entry_id]["note"])
                notes.append(note("Bemerkung", entries[entry_id]["note"]))
        if notes:
            record["notes"] = notes
        if work["genres"]:
            record["genres"] = work["genres"]
        out["works"].append(record)

        # Expressions
        parent = by_id.get(work["isPartOf"]) if work["isPartOf"] else None
        languages = [LANGUAGES[name][1]] if name else []

        def expression(identifier, label, voices=None):
            item = {"@id": identifier, "@type": "Expression", "label": label}
            if languages:
                item["languages"] = languages
            if voices:
                used_counts.add(voices)
                item["instrumentation"] = "instrumentations:{0}-stimmen".format(voices)
            if parent:
                item["partOfExpression"] = expression_for(parent, voices)
            return item

        if len(counts) <= 1:
            out["expressions"].append(expression(
                expression_for(work), work["preferredTitle"], counts[0] if counts else None
            ))
        else:
            gap("Werk mit mehreren Stimmenzahlen", work["lv"])
            out["expressions"].append(expression(expression_for(work), work["preferredTitle"]))
            for count in counts:
                out["expressions"].append(expression(
                    expression_for(work, count),
                    "{0} ({1} Stimmen)".format(work["preferredTitle"], count), count,
                ))

    # Inhalte der Drucke
    print_contents = defaultdict(list)
    for work in selected:
        for appearance in work["printAppearances"]:
            siglum = appearance["inPrint"].split(":", 1)[1]
            first = [
                entries[e] for e in work["entries"] if entries[e]["firstPrint"] == siglum
            ]
            voices = first[0]["voices"] if first else None
            if len(work["voiceCounts"]) > 1 and voices is None:
                gap("Stimmenzahl im Druck nicht belegt", "{0} in {1}".format(work["lv"], siglum))
            content = {"position": appearance["piece"], "embodies": expression_for(work, voices)}
            if first and first[0]["title"]:
                content["titleInSource"] = first[0]["title"]
            if voices:
                content["voices"] = voices
            if appearance.get("note"):
                content["note"] = appearance["note"]
            print_contents[siglum].append(content)
        # Das Register nennt Teile nicht einzeln, sie stehen nur als Eintrag im Erstdruck.
        for entry_id in work["entries"]:
            entry = entries[entry_id]
            siglum = entry["firstPrint"]
            if work["isPartOf"] and siglum:
                parent_piece = [
                    a["piece"] for a in by_id[work["isPartOf"]]["printAppearances"]
                    if a["inPrint"] == "print:" + siglum
                ]
                content = {"embodies": expression_for(work, entry["voices"])}
                if parent_piece:
                    content["position"] = "{0}, Teil {1}".format(parent_piece[0], work["lvPart"])
                if entry["title"]:
                    content["titleInSource"] = entry["title"]
                if entry["voices"]:
                    content["voices"] = entry["voices"]
                print_contents[siglum].append(content)

    def sort_key(content):
        numbers = re.findall(r"\d+", content.get("position") or "")
        return [int(n) for n in numbers] or [10 ** 6]

    for item in prints:
        siglum = item["siglum"]
        if siglum not in print_contents:
            continue
        record = {
            "@id": "manifestations:" + slug(siglum),
            "@type": "Manifestation",
            "titles": [{"text": {"@none": item["shortTitle"] or item["title"] or siglum}}],
            "classifications": ["terms:Print"],
            "identifiers": [{"list": "Sigle", "value": siglum}]
            + [{"list": k, "value": v} for k, v in item["references"].items()],
            "contents": sorted(print_contents[siglum], key=sort_key),
        }
        if item["title"]:
            record["titlePages"] = [{"html": html.escape(item["title"], quote=False)}]
        if item["year"]:
            record["publication"] = {
                "startDate": "{0}-01-01".format(item["year"]),
                "endDate": "{0}-12-31".format(item["year"]),
            }
            if item["dateApproximate"]:
                record["publication"]["label"] = "ca. {0}".format(item["year"])
        if item["rism"] and RE_LINK.match(item["rism"]):
            record["sameAs"] = [item["rism"]]
        notes = []
        if item["description"]:
            notes.append(note("Beschreibung", item["description"]))
        if item["partbooks"]:
            gap("Stimmbücher nur als Anmerkung", item["partbooks"])
            notes.append(note("Stimmbücher", item["partbooks"]))
        if notes:
            record["notes"] = notes
        out["manifestations"].append(record)

    # Handschriften: Eine Quelle ist Manifestation und Exemplar.
    source_keys = {key_of(manuscript_by_id[m]) for w in selected for m in w["manuscripts"]}
    by_source = defaultdict(list)
    for row in manuscripts:
        if key_of(row) in source_keys:
            by_source[key_of(row)].append(row)
    by_lv = {work["lv"]: work for work in selected}
    institutions = {}
    places = {}

    def place(name):
        identifier = "places:" + slug(name)
        places.setdefault(identifier, {"@id": identifier, "@type": "Place", "name": name})
        return identifier

    for key in sorted(by_source, key=lambda k: tuple(p or "" for p in k)):
        rows = by_source[key]
        name = " ".join(part for part in key if part) or "Ohne Angabe"
        base = "hs-" + slug(name)
        contents = []
        for row in rows:
            work = by_lv.get(row["lv"])
            if not work:
                gap("Stück außerhalb der Auswahl nur als Bemerkung", row["lv"] or row["title"])
                continue
            content = {"embodies": expression_for(work, row["voices"])}
            if row["title"]:
                content["titleInSource"] = row["title"]
            if row["voices"]:
                content["voices"] = row["voices"]
            if row["dating"]:
                content["dating"] = row["dating"]
            if row["note"]:
                content["note"] = row["note"]
            contents.append(content)
        others = [r for r in rows if not by_lv.get(r["lv"])]
        notes = []
        for field, label in (
            ("sourceType", "Quellenart"), ("provenance", "Provenienz"),
            ("sourceNote", "Bemerkung"), ("literature", "Literatur"),
        ):
            for value in sorted({r[field] for r in rows if r[field]}):
                gap(label + " nur als Anmerkung", value)
                notes.append(note(label, value))
        if others:
            notes.append(note("Weitere Stücke", "; ".join(
                "{0}: {1}".format(r["lv"] or r["lvAnh"] or "ohne LV", r["title"]) for r in others
            )))
        record = {
            "@id": "manifestations:" + base,
            "@type": "Manifestation",
            "titles": [{"text": {"@none": name}}],
            "classifications": ["terms:Manuscript"],
            "contents": contents,
        }
        if notes:
            record["notes"] = notes
        out["manifestations"].append(record)

        first = rows[0]
        item = {
            "@id": "items:" + base,
            "@type": "Item",
            "label": name,
            "exemplifies": "manifestations:" + base,
        }
        if key[1]:
            item["shelfmark"] = key[1]
        former = sorted({r["shelfmarkAlt"] for r in rows if r["shelfmarkAlt"]})
        if former:
            item["formerShelfmark"] = former[0]
            if len(former) > 1:
                gap("Mehrere frühere Signaturen", former)
        links = sorted({r["link"] for r in rows if r["link"]})
        valid = [link for link in links if RE_LINK.match(link)]
        if valid:
            item["sameAs"] = valid
        if len(valid) != len(links):
            gap("Ungültiger Link", links)
        if first["library"] or first["rismSiglum"]:
            identifier = "institutions:" + slug(first["rismSiglum"] or first["library"])
            if identifier not in institutions:
                institution = {
                    "@id": identifier,
                    "@type": "Institution",
                    "name": first["library"] or first["rismSiglum"],
                }
                if first["rismSiglum"]:
                    institution["siglum"] = first["rismSiglum"]
                if first["place"]:
                    institution["place"] = place(first["place"])
                institutions[identifier] = institution
            item["keeper"] = identifier
        out["items"].append(item)

    # Besetzungen
    for count in sorted(used_counts):
        out["instrumentations"].append({
            "@id": "instrumentations:{0}-stimmen".format(count),
            "@type": "Instrumentation",
            "label": "{0} {1}".format(count, "Stimme" if count == 1 else "Stimmen"),
            "details": [{"position": 1, "medium": "terms:Voices", "description": "Stimmen", "quantity": count}],
        })

    # Personen
    out["persons"].append({
        "@id": LASSO, "@type": "Person", "familyName": "Lasso", "givenName": "Orlando di",
    })
    for person in persons:
        if person["@id"] not in used_persons:
            continue
        gap("Name nicht in Vor- und Nachname zerlegt", person["preferredName"])
        record = {
            "@id": "persons:" + slug(person["@id"].split(":", 1)[1]),
            "@type": "Person",
            "familyName": person["preferredName"],
        }
        if person["variantNames"]:
            record["alternateNames"] = person["variantNames"]
        links = [link for link in (person["gnd"], person["viaf"]) if link]
        if links:
            record["sameAs"] = links
        out["persons"].append(record)

    # Ausgaben und Baende
    editors = {}
    for edition in editions:
        volumes = [v for v in edition["volumes"] if v["@id"] in used_volumes]
        if not volumes:
            continue
        out["bibliography"].append({
            "@id": bib(edition["@id"]),
            "@type": "Bibliography",
            "abbreviation": edition["siglum"],
            "genre": "terms:Book",
            "titles": [{"text": {"@none": edition["title"]}}],
        })
        for volume in volumes:
            record = {
                "@id": bib(volume["@id"]),
                "@type": "Bibliography",
                "abbreviation": "{0} {1}".format(edition["siglum"], volume["volume"]),
                "genre": "terms:Book",
                "titles": [{"text": {"@none": volume["title"]}}],
                "series": bib(edition["@id"]),
                "volumeNumber": volume["volume"],
            }
            names = []
            for editor in volume["editors"]:
                identifier = "persons:" + slug(editor)
                editors[identifier] = editor
                names.append(identifier)
            if names:
                record["editors"] = names
            publication = {}
            if volume["year"]:
                publication["startDate"] = "{0}-01-01".format(volume["year"])
                publication["endDate"] = "{0}-12-31".format(volume["year"])
            if volume["dateApproximate"]:
                publication["label"] = "ca. {0}".format(volume["year"])
            if volume["publisher"]:
                publication["publisherName"] = volume["publisher"]
            if volume["place"]:
                publication["place"] = place(volume["place"])
            if publication:
                record["publication"] = publication
            out["bibliography"].append(record)
    for identifier, name in sorted(editors.items()):
        gap("Name nicht in Vor- und Nachname zerlegt", name)
        out["persons"].append({"@id": identifier, "@type": "Person", "familyName": name})

    out["institutions"] = sorted(institutions.values(), key=lambda r: r["@id"])
    out["places"] = sorted(places.values(), key=lambda r: r["@id"])

    context = "../../schema/context.jsonld"
    for name, records in out.items():
        write(name, {"@context": context, "entries": records})
    write("catalog", {
        "@context": context,
        "@id": "urn:uuid:dataCatalogs/catalog",
        "@type": "Catalogue",
        "label": "Werkverzeichnis Orlando di Lasso, Auszug zum Druck 1555-1",
        "composer": LASSO,
        "catalogueAbbreviation": "LV",
    })
    write("luecken", {
        kind: {"Anzahl": gaps[kind], "Beispiele": examples[kind]} for kind in sorted(gaps)
    })

    # Vollstaendigkeit gegen die Quelle
    wanted = sum(len(w["printAppearances"]) for w in selected)
    rows_wanted = sum(len(rows) for rows in by_source.values())
    embedded = sum(len(r["contents"]) for r in out["manifestations"] if "Manuscript" in r["classifications"][0])
    others = sum(len([r for r in rows if not by_lv.get(r["lv"])]) for rows in by_source.values())
    print("Werke {0}, Expressions {1}, Quellen {2}, Exemplare {3}".format(
        len(out["works"]), len(out["expressions"]), len(out["manifestations"]), len(out["items"])
    ))
    print("Drucknachweise der Auswahl: {0}".format(wanted))
    print("Handschriftenzeilen: {0} = {1} mit Struktur + {2} Stücke außerhalb".format(
        rows_wanted, embedded, others
    ))
    for kind in sorted(gaps):
        print("  {0:<50}{1}".format(kind, gaps[kind]))


def write(name, payload):
    with (HERE / (name + ".json")).open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
