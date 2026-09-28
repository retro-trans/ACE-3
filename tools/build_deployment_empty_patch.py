"""0.1.66: translate all shared empty-unit placeholders. Dry-run before --write."""
import argparse
import json
import struct
import sys
from build_ui_patch import ROOT, require, u32, inner_bnd
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts
from ui_font import measure_text
import build_stats_panel_patch as writer

VERSION = '0.1.66'
# Exact published 0.1.65 image, mastered from the approved local 0.1.64 content.
BASE = ROOT/'work/release/ACE3-English-0.1.64-orig-layout.iso'
BASE_HASH = 'b8d7f75e714eb2a0575bf9b7d79030bdc7859a75552b4560bb13e166f633486a'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
INPUT = ROOT/'work/translation/en/deployment_empty_066.json'


def plan():
    doc = json.loads(INPUT.read_text(encoding='utf-8'))
    before, after = doc['source'].encode('cp932')+b'\0', doc['target'].encode('cp932')+b'\0'
    require(len(before) == len(after) == 5, 'Placeholder extent changed')
    edits, reports, inventory = [], [], []
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        for _,size,off,rid in entries:
            f.seek(fi['offset']+off)
            if f.read(4) != b'BND\0':continue
            f.seek(fi['offset']+off);data = f.read(size)
            if before not in data:continue
            try:subresources = parts(data)
            except ValueError:continue
            spans = {k:(a,b) for k,a,b in inner_bnd(data[:u32(data,4)])}
            for tid, table in subresources.items():
                try:rows = parse_table(table)[3]
                except (ValueError,UnicodeError,struct.error):continue
                for slot,text_id,pointer,raw in rows:
                    if raw != before[:-1]:continue
                    inventory.append((rid,tid,text_id))
                    require(tid == doc['table_id'] and text_id == doc['text_id'] and rid in doc['resources'],
                            'Unexpected empty-placeholder context')
                    require(slot == 1 and table[pointer:pointer+5] == before, 'Placeholder preimage')
                    width = max(measure_text(subresources[2500],doc['target']))
                    require(width <= 94, 'Placeholder does not fit narrow deployment caption width')
                    patched = table[:pointer]+after+table[pointer+5:]
                    expected = [(s,i,p,after[:-1] if i==text_id else r) for s,i,p,r in rows]
                    require(parse_table(patched)[3] == expected, 'Unrelated table row changed')
                    edits.append(dict(offset=fi['offset']+off+spans[tid][0]+pointer,before=before,after=after))
                    reports.append(dict(resource=rid,table=tid,text_id=text_id,target=doc['target'],font_width=width))
    require(sorted(inventory) == [(rid,doc['table_id'],doc['text_id']) for rid in doc['resources']],
            'Empty-unit copy coverage changed')
    edits.sort(key=lambda c:c['offset'])
    require(all(a['offset']+len(a['after']) <= b['offset'] for a,b in zip(edits,edits[1:])), 'Overlapping edits')
    return edits, dict(base_release='0.1.65',copies=reports,total_string_bytes=20,
                       source=doc['source'],target=doc['target'],runtime_verified=False), None


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true')
    args=ap.parse_args();edits,report,_=plan()
    print('DRY RUN: replace the four empty-unit strings; preserve all pointers and other rows',flush=True)
    print(json.dumps(report,indent=2,ensure_ascii=True),flush=True)
    if args.write:
        writer.VERSION,writer.BASE,writer.OUTPUT,writer.BASE_HASH=VERSION,BASE,OUTPUT,BASE_HASH
        writer.plan=lambda:(edits,report,None)
        sys.argv=[sys.argv[0],'--write'];writer.main()


if __name__=='__main__':main()
