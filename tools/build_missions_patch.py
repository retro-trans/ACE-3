"""0.1.19: ACE3 mission titles and secret goals. Reuses the 0.1.18 text-only builder."""
import argparse
import hashlib
import json
from build_ui_patch import ROOT
import build_dialogs_patch as dialogs
import build_dialogue_patch as builder

VERSION = '0.1.19'
BASE = ROOT/'work/output/ACE3-English-0.1.18.iso'
OUTPUT = ROOT/'work/output/ACE3-English-0.1.19.iso'
INPUT = ROOT/'work/translation/en/missions_019.json'


def plan():
    return dialogs.plan(BASE, INPUT)


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    changes, reports, inventory = plan()
    summary = {'resources':len(changes), 'tables':inventory, 'text_instances':sum(n for _, _, n in inventory),
               'allocation_adjustments':sum(len(r['allocations']) for r in reports)}
    print('DRY RUN', json.dumps(summary))
    for r in reports:
        print(r['resource_id'], r['old_size'], '->', r['new_size'], 'changed', r['changed_subresources'],
              'missing glyphs', r['font'].get('missing_used_before'))
        if r['resource_id'] == 4002050:
            for t in r['tables']:
                for row in t['rows']:
                    if row['text_id'] in (10, 170, 424): print(t['table_id'], json.dumps(row, ensure_ascii=True))
    if not a.write: return
    builder.VERSION, builder.BASE, builder.OUTPUT = VERSION, BASE, OUTPUT
    builder.build(changes, reports)
    path = OUTPUT.with_suffix('.json'); doc = json.loads(path.read_text(encoding='utf-8'))
    doc['coverage'] = summary; doc['runtime_verified'] = False
    doc['limitations'] = ('Offline verified only. Legacy ACE2 mission tables in bundle 4002055, song titles, story movie titles, '
                          'encyclopedia text, pilot names and ability descriptions remain Japanese.')
    path.write_text(json.dumps(doc, indent=2)+'\n', encoding='utf-8')
    inputs = [INPUT, ROOT/'work/glossary/mission_terms_019.json', ROOT/'tools/build_missions_patch.py',
              ROOT/'tools/build_dialogs_patch.py', ROOT/'tools/build_dialogue_patch.py', ROOT/'tools/repair_disc_layout.py']
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps({'version':VERSION, 'base':BASE.name,
        'base_sha256':'a19bd7038cfe7204e2ac6fe5aa990e54c487e8e10fc8da84d2cc2e6b4d9c5ddf', 'sha256':doc['sha256'],
        'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
