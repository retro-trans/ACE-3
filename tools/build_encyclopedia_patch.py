"""0.1.22: every Encyclopedia entry - 88 term names and 88 pages, in the menu and gameplay bundles."""
import argparse
import hashlib
import json
from build_ui_patch import ROOT
import build_dialogs_patch as dialogs
import build_dialogue_patch as builder

VERSION = '0.1.22'
BASE = ROOT/'work/output/ACE3-English-0.1.21.iso'
OUTPUT = ROOT/'work/output/ACE3-English-0.1.22.iso'
INPUT = ROOT/'work/translation/en/encyclopedia_022.json'
BUNDLES = list(range(4002050, 4002059))+list(range(1200000, 1200012))


def plan():
    return dialogs.plan(BASE, INPUT, BUNDLES)


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    changes, reports, inventory = plan()
    summary = {'resources':len(changes), 'tables':inventory, 'text_instances':sum(n for _, _, n in inventory),
               'allocation_adjustments':sum(len(r['allocations']) for r in reports)}
    print('DRY RUN', json.dumps(summary))
    for r in reports:
        print(r['resource_id'], r['old_size'], '->', r['new_size'], 'changed', r['changed_subresources'],
              'missing glyphs', r['font'].get('missing_used_before'))
    for t in reports[0]['tables']:
        for row in t['rows']:
            if row['text_id'] == 4: print(t['table_id'], json.dumps(row, ensure_ascii=True))
    if not a.write: return
    builder.VERSION, builder.BASE, builder.OUTPUT = VERSION, BASE, OUTPUT
    builder.build(changes, reports)
    path = OUTPUT.with_suffix('.json'); doc = json.loads(path.read_text(encoding='utf-8'))
    doc['coverage'] = summary; doc['runtime_verified'] = False
    doc['longest_pages'] = json.loads(INPUT.read_text(encoding='utf-8'))['longest_pages']
    doc['limitations'] = ('Offline verified only. English pages stay inside the stock line count, line width and byte size, but '
                          'hold up to twice the stock maximum of 237 visible characters; test the longest pages first.')
    path.write_text(json.dumps(doc, indent=2)+'\n', encoding='utf-8')
    inputs = [INPUT, ROOT/'work/translation/en/encyclopedia_021_a.json', ROOT/'work/translation/en/encyclopedia_021_b.json',
              ROOT/'tools/build_encyclopedia_patch.py', ROOT/'tools/build_dialogs_patch.py',
              ROOT/'tools/build_dialogue_patch.py', ROOT/'tools/repair_disc_layout.py']
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps({'version':VERSION, 'base':BASE.name,
        'base_sha256':'913972cfb4f46d544dd4c90ed0c6cfdc296ec45730dc31af32b9a8b1e0c2dc7e', 'sha256':doc['sha256'],
        'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
