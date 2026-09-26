"""Verify supported ACE3 table structure, optionally against an edited export. Read-only."""
import argparse
import json
from pathlib import Path
from translation_tables import SCHEMA, json_text, require, row_key, scan_iso, sha


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('iso', type=Path); ap.add_argument('--script', type=Path); a = ap.parse_args()
    doc = json.loads(a.script.read_text(encoding='utf-8')) if a.script else None
    if doc: require(doc.get('schema') == SCHEMA, 'Unsupported export schema')
    resources = set(doc['resources']) if doc and doc['resources'] is not None else None
    tables, counts = scan_iso(a.iso, resources)
    require(tables, 'No supported text tables found')
    if doc:
        actual = {row_key(k, tid): raw for k, t in tables.items() for _, tid, _, raw in t['rows'] if raw is not None}
        require(len(doc['rows']) == len(actual) and {r['id'] for r in doc['rows']} == set(actual), 'Row inventory differs')
        for row in doc['rows']:
            raw = actual[row['id']]
            require(sha(raw) == row['before_sha256'] if row['text'] is None else raw == row['text'].encode('cp932'), 'Text differs at '+row['id'])
    print(json_text({k: len(v) if isinstance(v, list) else v for k, v in counts.items()}))
    print('Supported tables verified. Excluded formats and in-game layout are not certified by this check.')


if __name__ == '__main__': main()
