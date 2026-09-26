"""0.1.23: pilot full names and short speaker labels in every name-table copy."""
import argparse
import hashlib
import json
from build_ui_patch import ROOT
import build_dialogs_patch as dialogs
import build_dialogue_patch as builder

VERSION = '0.1.23'
BASE = ROOT/'work/output/ACE3-English-0.1.22.iso'
OUTPUT = ROOT/'work/output/ACE3-English-0.1.23.iso'
INPUT = ROOT/'work/translation/en/names_023.json'
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
              'missing glyphs', r['font'].get('missing_used_before'), 'small glyphs',
              [x['character'] for x in r['font'].get('additions', []) if x.get('source_height') == 12])
    if not a.write: return
    builder.VERSION, builder.BASE, builder.OUTPUT = VERSION, BASE, OUTPUT
    builder.build(changes, reports)
    path = OUTPUT.with_suffix('.json'); doc = json.loads(path.read_text(encoding='utf-8'))
    doc['coverage'] = summary; doc['runtime_verified'] = False
    doc['limitations'] = 'Offline verified only. Scene-specific actor labels outside the shared tables are not covered.'
    path.write_text(json.dumps(doc, indent=2)+'\n', encoding='utf-8')
    inputs = [INPUT, ROOT/'work/glossary/character_names_021.json',
              ROOT/'tools/build_names_patch.py', ROOT/'tools/build_dialogs_patch.py', ROOT/'tools/build_dialogue_patch.py']
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps({'version':VERSION, 'base':BASE.name,
        'base_sha256':'e98daceab6473d09c2f57f49d6572a49c110de00778f4652df6eabe8c8cbf600', 'sha256':doc['sha256'],
        'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
