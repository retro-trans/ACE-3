"""0.1.30: Mission 07 (Destroy Shin Dragon) in-mission dialogue, on top of 0.1.29. Dry-run unless --write.

Same machinery as 0.1.29 (tools/build_029_patch.py): newly reviewed window scenes are picked up if any exist, caption
pictures are already repainted and are recognised as such, and complete reviewed mission scenes are relocated.
"""
import argparse
import hashlib
import json
from build_ui_patch import ROOT
import build_dialogue_patch as builder
import build_029_patch as base

VERSION = '0.1.30'
base.VERSION = VERSION
base.BASE = ROOT/'work/output/ACE3-English-0.1.29.iso'
base.OUTPUT = OUTPUT = ROOT/'work/output/ACE3-English-0.1.30.iso'
SHIP = lambda name: {n:'Warning: %s at %d％ damage' % (name, n) for n in (40, 60, 80)}
NADESICO, TOWER, GEKKO = SHIP('Nadesico B'), SHIP('Tower'), SHIP('Gekko')
base.AUXILIARY = {
 2002070:{3:'Destroy the Eligor', 4:'Objective: Destroy the Eligor', 10:'Objective: Mothership reaches its goal',
          11:'Objective: Destroy all targets', 12:'Nav: Prioritize targets on the route', 13:'Info: Mothership advancing again',
          14:'Warning: Enemy reinforcements', 15:'Warning: Enemy advancing', 16:'Info: Mothership has arrived',
          17:'Info: Allied forces advancing', 18:'Info: Base captured', 19:'Info: Enemy speed reduced',
          20:NADESICO[40], 21:NADESICO[60], 22:NADESICO[80], 23:TOWER[40], 24:TOWER[60], 25:TOWER[80],
          26:GEKKO[40], 27:GEKKO[60], 28:GEKKO[80], 29:'Mission Failed: Nadesico B sunk', 30:'Mission Failed: Tower sunk',
          31:'Mission Failed: Gekko sunk', 32:'Warning: 5 minutes remaining', 33:'Mission Failed: Time Over'},
}


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    changes, reports, summary = base.plan()
    print('DRY RUN', json.dumps(summary))
    if not a.write: return
    builder.VERSION, builder.BASE, builder.OUTPUT = VERSION, base.BASE, OUTPUT
    builder.build(changes, reports)
    path = OUTPUT.with_suffix('.json'); doc = json.loads(path.read_text(encoding='utf-8'))
    doc['coverage'] = summary; doc['runtime_verified'] = False
    path.write_text(json.dumps(doc, indent=2)+'\n', encoding='utf-8')
    inputs = [ROOT/'tools/build_030_patch.py', ROOT/'tools/build_029_patch.py']+sorted((ROOT/'work/translation/en/dialogue').glob('batch_02[0-9]*.json'))
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps({'version':VERSION, 'base':base.BASE.name,
        'base_sha256':'34805721a1387bb07e6e31abe574c66d8909fc644377d2d1d01a5a1d49c71630', 'sha256':doc['sha256'],
        'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
