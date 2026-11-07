#!/usr/bin/env python3
"""Haertetest: uebertraegt Lasso-Daten aus dem Branch lasso in die Vorlage.

Aufruf (im Wurzelordner):
  python examples/lasso_konvertieren.py --out examples/lasso-1555-1 --print 1555-1
  python examples/lasso_konvertieren.py --out examples/lasso-schwierig --lv 74 90 193 327 --anh 1

Einmaliges Werkzeug fuer die Tests, kein Teil der Vorlage. Liest den Git-Stand von
lasso, schreibt die Datensaetze in den Zielordner und fuehrt in luecken.json auf, was
keinen passenden Platz gefunden hat. Am Ende zaehlt es gegen die Quelle nach.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

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
        ["git", "show", "lasso:data/{0}.json".format(name)],
        capture_output=True, encoding="utf-8", check=True,
    ).stdout
    return json.loads(text)["items"]


def gap(kind, example):
    gaps[kind] += 1
    if len(examples[kind]) < 3:
        examples[kind].append(str(example)[:120])


def slug(text):
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-")


def local(identifier):
    return slug(identifier.split(":", 1)[1])


def note(label, text):
    return {"label": label, "html": html.escape(str(text), quote=False)}


def key_of(row):
    return row["rismSiglum"], row["shelfmark"]


def expression_for(work):
    """Eine Expression je Werk, siehe docs/entscheidungen.md, Abschnitt 5. Die
    Stimmenzahl steht am Stueck in der jeweiligen Quelle."""
    return "expressions:" + local(work["@id"])


def contributor_list(item):
    result = []
    for person in item["textAuthors"]:
        entry = {"agent": "persons:" + local(person), "role": "terms:Lyricist"}
        if person in item["uncertainTextAuthors"]:
            entry["certainty"] = "terms:LowCertainty"
        result.append(entry)
    return result


class Converter:
    def __init__(self, selected, all_works, entries, manuscripts, prints, persons, editions, fassungen):
        self.selected = selected
        self.by_id = {work["@id"]: work for work in all_works}
        self.entries = entries
        self.manuscripts = manuscripts
        self.prints = prints
        self.persons = persons
        self.editions = editions
        self.fassungen = fassungen
        self.counts = set()
        self.used_persons = set()
        self.used_volumes = set()
        self.places = {}
        self.contents = defaultdict(list)
        self.volume_of = {}
        self.part_label = {}
        for edition in editions:
            for volume in edition["volumes"]:
                self.volume_of[volume["@id"]] = volume["@id"]
                for part in volume["parts"]:
                    self.volume_of[part["@id"]] = volume["@id"]
                    self.part_label[part["@id"]] = part["volume"].split(",")[-1]
        self.out = {name: [] for name in (
            "works", "expressions", "manifestations", "items", "persons",
            "institutions", "places", "instrumentations", "bibliography",
        )}

    def language(self, work):
        """Eigene Sprache, sonst die von Gesamtwerk und Teilen."""
        base = self.by_id[work["isPartOf"]] if work["isPartOf"] else work
        family = [work, base] + [self.by_id[p] for p in base["hasPart"]]
        names = {name for member in family for name in member["languages"]}
        return names.pop() if len(names) == 1 else None

    def citations(self, item):
        result = []
        for appearance in item["editionAppearances"]:
            volume = self.volume_of[appearance["inVolume"]]
            self.used_volumes.add(volume)
            citation = {"inBibliography": "bibliography:" + local(volume)}
            section = [self.part_label.get(appearance["inVolume"]), appearance.get("appendix")]
            section = ", ".join(part for part in section if part)
            if section:
                citation["section"] = section
            for field in ("number", "page", "note"):
                if field in appearance:
                    citation[field] = appearance[field]
            result.append(citation)
        return result

    def expression(self, identifier, label, languages, voices=None, parent=None):
        item = {"@id": identifier, "@type": "Expression", "label": label}
        if languages:
            item["languages"] = languages
        if voices:
            self.counts.add(voices)
            item["instrumentation"] = "instrumentations:{0}-stimmen".format(voices)
        if parent:
            item["partOfExpression"] = parent
        return item

    def work(self, work):
        name = self.language(work)
        tag = LANGUAGES[name][0] if name else "@none"
        if not name:
            gap("Titel ohne Sprache", work["@id"])
        record = {
            "@id": "works:" + local(work["@id"]),
            "@type": "Work",
            "titles": [{"text": {tag: work["preferredTitle"]}, "type": "terms:MainTitle"}]
            + [{"text": {tag: t}, "type": "terms:OtherTitle"} for t in work["variantTitles"]],
            "identifiers": [
                {"list": "LV", "value": work["lv"]} if work["lv"]
                else {"list": "LV-Anhang", "value": str(work["lvAnh"])}
            ],
            "contributors": [{"agent": LASSO, "role": "terms:Composer"}] + contributor_list(work),
        }
        self.used_persons.update(work["textAuthors"])
        counts = work["voiceCounts"]
        realised = [expression_for(work)]
        if len(counts) > 1:
            gap("Werk mit mehreren Stimmenzahlen", work["@id"])
        realised += ["expressions:" + local(x) for x in work["expressions"]]
        record["realisedIn"] = realised
        if work["isPartOf"]:
            record["partOfWork"] = "works:" + local(work["isPartOf"])
        citations = self.citations(work)
        if citations:
            record["citations"] = citations
        if work["textSources"]:
            record["textSources"] = work["textSources"]
        if work["genres"]:
            record["genres"] = work["genres"]
        self.out["works"].append(record)

        languages = [LANGUAGES[name][1]] if name else []
        parent = self.by_id.get(work["isPartOf"])
        # Die Besetzung nur, wenn sie eindeutig ist; sonst steht sie je Quelle in voices.
        self.out["expressions"].append(self.expression(
            expression_for(work), work["preferredTitle"], languages,
            counts[0] if len(counts) == 1 else None,
            expression_for(parent) if parent else None,
        ))
        self.work_contents(work)

    def work_contents(self, work):
        by_print = defaultdict(list)
        for entry_id in work["entries"]:
            by_print[self.entries[entry_id]["firstPrint"]].append(self.entries[entry_id])
        appeared = set()
        for appearance in work["printAppearances"]:
            siglum = appearance["inPrint"].split(":", 1)[1]
            appeared.add(siglum)
            first = by_print.get(siglum, [])
            voices = first[0]["voices"] if first else None
            if len(work["voiceCounts"]) > 1 and voices is None:
                gap("Stimmenzahl im Druck nicht belegt", "{0} in {1}".format(work["lv"], siglum))
            content = {"position": appearance["piece"], "embodies": expression_for(work)}
            self.source_details(content, first, appearance.get("note"))
            self.contents[siglum].append(content)
        # Teile und Eintraege ohne Registerangabe stehen nur als Eintrag im Erstdruck.
        for siglum, group in by_print.items():
            if not siglum or siglum in appeared:
                continue
            content = {"embodies": expression_for(work)}
            if work["isPartOf"]:
                piece = [
                    a["piece"] for a in self.by_id[work["isPartOf"]]["printAppearances"]
                    if a["inPrint"] == "print:" + siglum
                ]
                if piece:
                    content["position"] = piece[0]
                else:
                    gap("Teil ohne Stücknummer im Druck", "{0} in {1}".format(work["lv"], siglum))
                content["part"] = str(work["lvPart"])
            else:
                gap("Eintrag ohne Registerangabe, ohne Stücknummer", "{0} in {1}".format(work["lv"], siglum))
            self.source_details(content, group, None)
            self.contents[siglum].append(content)

    @staticmethod
    def source_details(content, entries, extra_note):
        if entries:
            if entries[0]["title"]:
                content["titleInSource"] = entries[0]["title"]
            if entries[0]["voices"]:
                content["voices"] = entries[0]["voices"]
        notes = [e["note"] for e in entries if e.get("note")] + ([extra_note] if extra_note else [])
        if notes:
            content["note"] = "; ".join(notes)

    def fassung(self, item):
        """Die gekennzeichneten Fassungen aus lasso sind echte Expressions."""
        name = item["languages"][0] if item["languages"] else None
        languages = [LANGUAGES[name][1]] if name else []
        tag = LANGUAGES[name][0] if name else "@none"
        voices = item["voiceCounts"][0] if len(item["voiceCounts"]) == 1 else None
        record = self.expression(
            "expressions:" + local(item["@id"]), item["preferredTitle"], languages, voices,
        )
        record["identifiers"] = [{"list": "LV", "value": item["lv"]}]
        if item["variantTitles"]:
            record["titles"] = [{"text": {tag: t}} for t in item["variantTitles"]]
        contributors = contributor_list(item)
        if contributors:
            record["contributors"] = contributors
        self.used_persons.update(item["textAuthors"])
        citations = self.citations(item)
        if citations:
            record["citations"] = citations
        if item["textSources"]:
            record["textSources"] = item["textSources"]
        record["notes"] = [note("Pars", item["pars"])]
        gap("Pars einer Fassung nur als Anmerkung", item["lv"])
        self.out["expressions"].append(record)
        for entry_id in item["entries"]:
            entry = self.entries[entry_id]
            gap("Fassung im Druck ohne Stücknummer", "{0} in {1}".format(item["lv"], entry["firstPrint"]))
            content = {"embodies": record["@id"]}
            self.source_details(content, [entry], None)
            self.contents[entry["firstPrint"]].append(content)

    def print_records(self):
        def sort_key(content):
            numbers = re.findall(r"\d+", content.get("position") or "")
            return [int(n) for n in numbers] + [int(content.get("part") or 0)] if numbers else [10 ** 6]

        for item in self.prints:
            siglum = item["siglum"]
            if siglum not in self.contents:
                continue
            record = {
                "@id": "manifestations:" + slug(siglum),
                "@type": "Manifestation",
                "titles": [{"text": {"@none": item["shortTitle"] or item["title"] or siglum}}],
                "classifications": ["terms:Print"],
                "identifiers": [{"list": "Sigle", "value": siglum}]
                + [{"list": k, "value": v} for k, v in item["references"].items()],
                "contents": sorted(self.contents[siglum], key=sort_key),
            }
            if item["partbooks"]:
                record["partbooks"] = item["partbooks"]
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
            if item["description"]:
                record["notes"] = [note("Beschreibung", item["description"])]
            self.out["manifestations"].append(record)
        missing = set(self.contents) - {p["siglum"] for p in self.prints}
        for siglum in missing:
            gap("Druck ohne Datensatz", siglum)

    def place(self, name):
        identifier = "places:" + slug(name)
        self.places.setdefault(identifier, {"@id": identifier, "@type": "Place", "name": name})
        return identifier

    def manuscript_records(self):
        wanted = {
            key_of(row) for row in self.manuscripts
            if any(row["@id"] in w["manuscripts"] for w in self.selected)
        }
        by_source = defaultdict(list)
        for row in self.manuscripts:
            if key_of(row) in wanted:
                by_source[key_of(row)].append(row)
        by_lv = {w["lv"]: w for w in self.selected if w["lv"]}
        by_anh = {w["lvAnh"]: w for w in self.selected if w["lvAnh"] is not None}
        institutions = {}
        institution_ids = {}
        used_names = set()
        self.others = 0
        self.structured = 0
        for key in sorted(by_source, key=lambda k: tuple(p or "" for p in k)):
            rows = by_source[key]
            name = " ".join(part for part in key if part) or "Ohne Angabe"
            base = "hs-" + slug(name)[:60]
            while base.casefold() in used_names:
                gap("Quellenname nur durch Zählung eindeutig", name)
                base += "-2"
            used_names.add(base.casefold())
            contents = []
            for row in rows:
                work = by_lv.get(row["lv"]) if row["lv"] else by_anh.get(row["lvAnh"])
                content = {"embodies": expression_for(work)} if work else {}
                if work and len(work["voiceCounts"]) > 1 and row["voices"] is None:
                    gap("Stimmenzahl in Handschrift nicht belegt", "{0} in {1}".format(work["lv"], name))
                for source_field, target in (
                    ("title", "titleInSource"), ("voices", "voices"), ("note", "note"),
                ):
                    if row[source_field]:
                        content[target] = row[source_field]
                if work:
                    self.structured += 1
                else:
                    # Ohne Werk im Auszug; die Nummer bleibt als Hinweis erhalten.
                    self.others += 1
                    number = row["lv"] or ("LVanh {0}".format(row["lvAnh"]) if row["lvAnh"] is not None else None)
                    if number:
                        label = "LV {0}".format(number) if row["lv"] else number
                        content["note"] = "; ".join(filter(None, (label, content.get("note"))))
                    else:
                        gap("Stück in Handschrift ohne Nummer", row["title"])
                contents.append(content)
            record = {
                "@id": "manifestations:" + base,
                "@type": "Manifestation",
                "titles": [{"text": {"@none": name}}],
                "classifications": ["terms:Manuscript"],
                "contents": contents,
            }
            datings = sorted({r["dating"] for r in rows if r["dating"]})
            if datings:
                record["dating"] = "; ".join(datings)
                if len(datings) > 1:
                    gap("Mehrere Datierungen für eine Quelle", "{0}: {1}".format(name, datings))
            types = sorted({r["sourceType"] for r in rows if r["sourceType"]})
            if types:
                record["sourceType"] = types[0]
                if len(types) > 1:
                    gap("Mehrere Quellenarten für eine Quelle", types)
            literature = sorted({r["literature"] for r in rows if r["literature"]})
            if literature:
                record["literature"] = literature
            notes = []
            for field, label in (("provenance", "Provenienz"), ("sourceNote", "Bemerkung")):
                notes += [note(label, v) for v in sorted({r[field] for r in rows if r[field]})]
            if notes:
                record["notes"] = notes
            self.out["manifestations"].append(record)

            first = rows[0]
            item = {
                "@id": "items:" + base, "@type": "Item", "label": name,
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
            label = first["rismSiglum"] or first["library"]
            if label:
                # Das Sigel als ID; dieselbe Schreibung kann verschiedene Bibliotheken meinen.
                pair = (first["rismSiglum"], first["library"])
                if pair not in institution_ids:
                    number = 1
                    identifier = "institutions:" + slug(label)[:50]
                    while identifier.casefold() in {v.casefold() for v in institution_ids.values()}:
                        number += 1
                        identifier = "institutions:{0}-{1}".format(slug(label)[:50], number)
                    institution_ids[pair] = identifier
                identifier = institution_ids[pair]
                if identifier not in institutions:
                    institution = {
                        "@id": identifier, "@type": "Institution",
                        "name": first["library"] or first["rismSiglum"],
                    }
                    if first["rismSiglum"]:
                        institution["siglum"] = first["rismSiglum"]
                    if first["place"]:
                        institution["place"] = self.place(first["place"])
                    institutions[identifier] = institution
                item["keeper"] = identifier
            self.out["items"].append(item)
        self.out["institutions"] = sorted(institutions.values(), key=lambda r: r["@id"])
        self.source_count = sum(len(rows) for rows in by_source.values())

    def rest(self):
        for count in sorted(self.counts):
            self.out["instrumentations"].append({
                "@id": "instrumentations:{0}-stimmen".format(count),
                "@type": "Instrumentation",
                "label": "{0} {1}".format(count, "Stimme" if count == 1 else "Stimmen"),
                "details": [{"position": 1, "medium": "terms:Voices", "description": "Stimmen", "quantity": count}],
            })
        self.out["persons"].append({
            "@id": LASSO, "@type": "Person", "familyName": "Lasso", "givenName": "Orlando di",
        })
        for person in self.persons:
            if person["@id"] not in self.used_persons:
                continue
            gap("Name nicht in Vor- und Nachname zerlegt", person["preferredName"])
            record = {
                "@id": "persons:" + local(person["@id"]),
                "@type": "Person",
                "familyName": person["preferredName"],
            }
            if person["variantNames"]:
                record["alternateNames"] = person["variantNames"]
            links = [link for link in (person["gnd"], person["viaf"]) if link]
            if links:
                record["sameAs"] = links
            self.out["persons"].append(record)

        editors = {}
        for edition in self.editions:
            volumes = [v for v in edition["volumes"] if v["@id"] in self.used_volumes]
            if not volumes:
                continue
            series = "bibliography:" + local(edition["@id"])
            self.out["bibliography"].append({
                "@id": series, "@type": "Bibliography", "abbreviation": edition["siglum"],
                "genre": "terms:Book", "titles": [{"text": {"@none": edition["title"]}}],
            })
            for volume in volumes:
                record = {
                    "@id": "bibliography:" + local(volume["@id"]),
                    "@type": "Bibliography",
                    "abbreviation": "{0} {1}".format(edition["siglum"], volume["volume"]),
                    "genre": "terms:Book",
                    "titles": [{"text": {"@none": volume["title"]}}],
                    "series": series,
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
                    publication["place"] = self.place(volume["place"])
                if publication:
                    record["publication"] = publication
                self.out["bibliography"].append(record)
        for identifier, name in sorted(editors.items()):
            gap("Name nicht in Vor- und Nachname zerlegt", name)
            self.out["persons"].append({"@id": identifier, "@type": "Person", "familyName": name})
        self.out["places"] = sorted(self.places.values(), key=lambda r: r["@id"])


def choose(works, args):
    """Die gewuenschten Werke samt Gesamtwerken und deren Teilen."""
    by_id = {work["@id"]: work for work in works}
    chosen = set()
    if args.siglum:
        chosen = {
            work["@id"] for work in works
            if args.siglum in work["prints"]
            or any(a["inPrint"] == "print:" + args.siglum for a in work["printAppearances"])
        }
    chosen.update("work:" + lv for lv in args.lv)
    chosen.update("work:anh-" + anh for anh in args.anh)
    for work_id in list(chosen):
        if by_id[work_id]["isPartOf"]:
            chosen.add(by_id[work_id]["isPartOf"])
    for work_id in list(chosen):
        chosen.update(by_id[work_id]["hasPart"])
    return [work for work in works if work["@id"] in chosen]


def write(folder, name, payload):
    with (folder / (name + ".json")).open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--print", dest="siglum")
    parser.add_argument("--lv", nargs="*", default=[])
    parser.add_argument("--anh", nargs="*", default=[])
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    works = source("works")
    entries = {entry["@id"]: entry for entry in source("entries")}
    selected = choose(works, args)
    ids = {work["@id"] for work in selected}
    fassungen = [x for x in source("expressions") if x["realizationOf"] in ids]
    converter = Converter(
        selected, works, entries, source("manuscripts"), source("prints"),
        source("persons"), source("editions"), fassungen,
    )
    for work in selected:
        converter.work(work)
    for item in fassungen:
        converter.fassung(item)
    converter.print_records()
    converter.manuscript_records()
    converter.rest()

    context = "../../schema/context.jsonld"
    for name, records in converter.out.items():
        write(args.out, name, {"@context": context, "entries": records})
    # Der Name erscheint im Kopf der Website, daher ohne Hinweis auf den Auszug.
    label = "Werkverzeichnis Orlando di Lasso"
    write(args.out, "catalog", {
        "@context": context, "@id": "urn:uuid:dataCatalogs/catalog", "@type": "Catalogue",
        "label": label, "composer": LASSO, "catalogueAbbreviation": "LV",
    })
    write(args.out, "luecken", {
        kind: {"Anzahl": gaps[kind], "Beispiele": examples[kind]} for kind in sorted(gaps)
    })

    # Nachzaehlen gegen die Quelle
    out = converter.out
    prints = [m for m in out["manifestations"] if m["classifications"] == ["terms:Print"]]
    appearances = sum(len(w["printAppearances"]) for w in selected)
    with_position = sum(1 for m in prints for c in m["contents"] if "position" in c and "part" not in c)
    print("Werke {0}, Expressions {1}, Quellen {2}, Exemplare {3}".format(
        len(out["works"]), len(out["expressions"]), len(out["manifestations"]), len(out["items"])
    ))
    print("Drucknachweise: Quelle {0}, mit Nummer {1}".format(appearances, with_position))
    print("Fassungen: {0}".format(len(fassungen)))
    print("Handschriftenzeilen der Quellen: {0} = {1} mit Struktur + {2} außerhalb".format(
        converter.source_count, converter.structured, converter.others
    ))
    print("Fundstellen: Quelle {0}, Ausgabe {1}".format(
        sum(len(i["editionAppearances"]) for i in selected + fassungen),
        sum(len(r.get("citations", [])) for name in ("works", "expressions") for r in out[name]),
    ))
    for kind in sorted(gaps):
        print("  {0:<50}{1}".format(kind, gaps[kind]))


if __name__ == "__main__":
    main()
