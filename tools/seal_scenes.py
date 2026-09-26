"""Bind reviewed window-scene translations (work/translation/en/scenes) to their source rows. Dry-run unless --write.

Adds each row's source_sha256 from the 0.1.27 disc so the builder can refuse a changed preimage, after checking that
every row of every table is present, text IDs match and the command sequence is unchanged. No Japanese is stored.
"""
import argparse
import hashlib
import json
from build_ui_patch import ROOT, require
from dialogue_corpus import archive
from build_flight_save_patch import controls
from scene_source import scene_tables

BASE = ROOT/'work/output/ACE3-English-0.1.27.iso'
SCENES = ROOT/'work/translation/en/scenes'


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    with BASE.open('rb') as f:
        info, entries = archive(f)
        for path in sorted(SCENES.glob('[0-9]*.json')):
            doc = json.loads(path.read_text(encoding='utf-8')); rid = doc['resource_id']
            if doc.get('status') != 'meaning_reviewed': print('SKIP (unreviewed)', rid); continue
            entry = next(e for e in entries if e[3] == rid); f.seek(info['offset']+entry[2]); tables = scene_tables(f.read(entry[1]))
            stock = {(tid, slot):(text_id, raw) for tid, rows in tables.items() for slot, text_id, _, raw in rows}
            require({(r['table'], r['slot']) for r in doc['rows']} == set(stock), 'Row set differs from scene %s' % rid)
            for row in doc['rows']:
                text_id, raw = stock[(row['table'], row['slot'])]
                require(row['text_id'] == text_id, 'Text ID mismatch %s %s' % (rid, row['slot']))
                require(controls(raw.decode('cp932')) == controls(row['en']), 'Commands changed %s table %s slot %s' % (rid, row['table'], row['slot']))
                row['source_sha256'] = hashlib.sha256(raw).hexdigest()
            print(('SEAL' if a.write else 'DRY RUN'), rid, doc.get('status'), len(doc['rows']), 'rows')
            if a.write: path.write_text(json.dumps(doc, ensure_ascii=False, indent=1)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
