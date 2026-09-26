"""Read-only ACE3 glossary lookup and integrity checks (Python standard library)."""

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = {"character", "organization", "location", "technology"}
FACT_STATUSES = {"sourced", "unknown", "not_found_in_reviewed_sources"}


def normalize(value):
    """Normalize width/case/spacing for lookup; do not change canonical data."""
    return "".join(unicodedata.normalize("NFKC", value).casefold().split())


def load_data(folder):
    values = []
    for filename in ("glossary.json", "sources.json", "research_queue.json"):
        with (folder / filename).open(encoding="utf-8-sig") as handle:
            values.append(json.load(handle))
    return values


def source_references(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "source_ids" or key.endswith("_source_ids"):
                yield from child
            else:
                yield from source_references(child)
    elif isinstance(value, list):
        for child in value:
            yield from source_references(child)


def validate(db, registry, queue):
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    def unique_ids(rows, label):
        ids = [row["id"] for row in rows]
        for value, count in Counter(ids).items():
            require(count == 1, f"Duplicate {label} id: {value}")
        return set(ids)

    source_ids = unique_ids(registry["sources"], "source")
    series_ids = unique_ids(db["series"], "series")
    entry_ids = unique_ids(db["entries"], "entry")
    require(bool(re.fullmatch(r"0\.\d+\.\d+", db["version"])), "Version must be 0.x.y")
    require(db["target_language"] == "en", "This release uses English target names")
    for label, data in (("glossary", db), ("sources", registry), ("queue", queue)):
        require(data["schema_version"] == "1.0", f"Unsupported schema in {label}")
        require(data["version"] == db["version"], f"Version mismatch in {label}")
        for source in source_references(data):
            require(source in source_ids, f"Unknown source in {label}: {source}")
    for source in registry["sources"]:
        url = urlsplit(source["url"])
        require(url.scheme in {"http", "https"} and bool(url.netloc), f"Bad URL: {source['id']}")
        require(bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", source["accessed_on"])), f"Missing access date: {source['id']}")

    names = defaultdict(list)
    for entry in db["entries"]:
        eid = entry["id"]
        require(entry["category"] in CATEGORIES, f"Bad category: {eid}")
        require(entry["series_id"] in series_ids, f"Unknown series: {eid}")
        require(bool(entry["continuity"]), f"Missing continuity: {eid}")
        name = entry["name"]
        require(isinstance(name["en"], str) and bool(name["en"].strip()), f"Missing English name: {eid}")
        require(name["decision"] in {"researched", "provisional"}, f"Bad name status: {eid}")
        require(bool(name["en_source_ids"]), f"Missing name evidence: {eid}")
        require(isinstance(name["ja"], list) and all(isinstance(s, str) and s for s in name["ja"]), f"Bad Japanese labels: {eid}")
        require(not name["ja"] or bool(name["ja_source_ids"]), f"Missing Japanese evidence: {eid}")
        require(bool(name["ja"]) or bool(entry["open_questions"]), f"Untracked missing Japanese label: {eid}")
        require(name["decision"] != "provisional" or bool(entry["open_questions"]), f"Untracked provisional name: {eid}")
        names[(entry["series_id"], normalize(name["en"]))].append(eid)
        presence = entry["game_presence"]
        require(presence["status"] in {"reference_confirmed", "franchise_context"}, f"Bad presence status: {eid}")
        require(presence["status"] != "reference_confirmed" or bool(presence["source_ids"]), f"Missing game evidence: {eid}")
        for alias in entry["aliases"]:
            require(bool(alias["text"]) and bool(alias["source_ids"]), f"Unsupported alias: {eid}")
            require(alias["language"] in {"en", "ja"}, f"Bad alias language: {eid}")
            require(alias["kind"] in {"spelling", "short_form", "name_order", "other_identity", "reference_label"}, f"Bad alias kind: {eid}")
        if entry["category"] == "character":
            profile = entry["profile"]
            require(set(profile) == {"gender", "nicknames", "personality", "role"}, f"Incomplete profile fields: {eid}")
            require(profile["gender"]["value"] in {None, "male", "female", "nonbinary", "other"}, f"Bad gender value: {eid}")
            require(profile["nicknames"]["value"] is None or isinstance(profile["nicknames"]["value"], list), f"Bad nickname list: {eid}")
            facts = profile.items()
        else:
            facts = [("description", entry["description"])]
        for key, fact in facts:
            require(fact["status"] in FACT_STATUSES, f"Bad fact status: {eid}.{key}")
            if fact["status"] == "sourced":
                require(fact["value"] is not None and fact["value"] != [] and bool(fact["source_ids"]), f"Empty sourced fact: {eid}.{key}")
            elif fact["status"] == "unknown":
                require(fact["value"] is None, f"Unknown fact has asserted value: {eid}.{key}")
            else:
                require(key == "nicknames" and fact["value"] == [] and bool(fact["source_ids"]), f"Invalid negative search result: {eid}.{key}")
    for key, ids in names.items():
        require(len(ids) == 1, f"Duplicate canonical name in series {key[0]}: {ids}")
    queued_ids = [row["entry_id"] for row in queue["entry_questions"]]
    require(len(queued_ids) == len(set(queued_ids)), "Duplicate research queue entry")
    for row in queue["entry_questions"]:
        require(row["entry_id"] in entry_ids, f"Unknown queued entry: {row['entry_id']}")
    queued = {row["entry_id"]: row["questions"] for row in queue["entry_questions"]}
    for entry in db["entries"]:
        require(queued.get(entry["id"], []) == entry["open_questions"], f"Stale research queue: {entry['id']}")
    for batch in queue["next_batches"]:
        for sid in batch.get("series_ids", []):
            require(sid in series_ids, f"Unknown queued series: {sid}")
    return errors


def lookup(entries, query, exact=False, category=None, series=None):
    needle = normalize(query)
    if not needle:
        return []
    found = []
    for entry in entries:
        if category and entry["category"] != category:
            continue
        if series and entry["series_id"] != series:
            continue
        terms = [entry["id"], entry["name"]["en"], *entry["name"]["ja"]]
        terms += [a["text"] for a in entry["aliases"]]
        terms += entry.get("profile", {}).get("nicknames", {}).get("value") or []
        if any((needle == normalize(term) if exact else needle in normalize(term)) for term in terms):
            found.append(entry)
    return found


def show_entry(entry, source_map):
    print(f"{entry['name']['en']} [{entry['id']}]")
    print(f"  Name: {entry['name']['decision']}; presence: {entry['game_presence']['status']}")
    print(f"  Continuity: {entry['continuity']}")
    print("  Japanese: " + (" / ".join(entry["name"]["ja"]) or "not established"))
    if entry["aliases"]:
        print("  Aliases: " + "; ".join(f"{a['text']} ({a['kind']})" for a in entry["aliases"]))
    facts = entry.get("profile", {"description": entry.get("description")})
    for key, fact in facts.items():
        value = fact["value"]
        text = ", ".join(value) if isinstance(value, list) else value
        print(f"  {key}: {text or fact['status']} [{', '.join(fact['source_ids'])}]")
        if fact.get("note"):
            print(f"    {fact['note']}")
    for note in entry["translation_notes"]:
        print(f"  Note: {note}")
    for question in entry["open_questions"]:
        print(f"  Research: {question}")
    for sid in sorted(set(source_references(entry))):
        print(f"  Source {sid}: {source_map[sid]['url']}")
    print()


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "work" / "glossary")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="Read-only validation; never changes files")
    query = commands.add_parser("lookup", help="Find names, nicknames, aliases, or IDs")
    query.add_argument("query")
    query.add_argument("--exact", action="store_true")
    query.add_argument("--category", choices=sorted(CATEGORIES))
    query.add_argument("--series", help="Series id from glossary.json")
    query.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        db, registry, queue = load_data(args.data_dir)
        errors = validate(db, registry, queue)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print(f"Cannot read valid glossary data: {error}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if args.command == "check":
        entries = db["entries"]
        print(f"PASS: glossary {db['version']}; {len(entries)} entries; {len(registry['sources'])} sources")
        print("Categories: " + ", ".join(f"{k}={v}" for k, v in sorted(Counter(e['category'] for e in entries).items())))
        print(f"Provisional names: {sum(e['name']['decision'] == 'provisional' for e in entries)}")
        print(f"Franchise-context-only entries: {sum(e['game_presence']['status'] == 'franchise_context' for e in entries)}")
        print(f"Unknown personality profiles: {sum(e.get('profile', {}).get('personality', {}).get('status') == 'unknown' for e in entries)}")
        print("Integrity passed. This is not an assessment of translation quality or complete roster coverage.")
        return 0
    found = lookup(db["entries"], args.query, args.exact, args.category, args.series)
    if not found:
        print("No match. Research the missing term before choosing a canonical spelling.", file=sys.stderr)
        return 2
    source_map = {s["id"]: s for s in registry["sources"]}
    if args.as_json:
        ids = set(source_references(found))
        print(json.dumps({"version": db["version"], "matches": found, "sources": [source_map[s] for s in sorted(ids)]}, ensure_ascii=False, indent=2))
    else:
        for entry in found:
            show_entry(entry, source_map)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
