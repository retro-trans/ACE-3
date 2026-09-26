"""Build the next dialogue wave on top of the previous build. Dry-run unless --write.

    python tools/build_wave_patch.py --version 0.1.31 --base 0.1.30 [--write]
Uses the 0.1.29 machinery (tools/build_029_patch.py): every reviewed+sealed window scene not yet on the disc is
inserted, repainted caption pictures are recognised, and every live in-mission scene (2002080..2002350) whose
timed rows are all reviewed is relocated with its HUD labels from work/translation/en/hud_labels.json.
"""
import argparse
import hashlib
import json
from build_ui_patch import ROOT
import build_dialogue_patch as builder
import build_029_patch as base
import hud_labels


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--version', required=True); ap.add_argument('--base', required=True)
    ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    base.VERSION = a.version; base.BASE = ROOT/('work/output/ACE3-English-%s.iso' % a.base)
    base.OUTPUT = output = ROOT/('work/output/ACE3-English-%s.iso' % a.version)
    base.AUXILIARY = hud_labels.labels()
    changes, reports, summary = base.plan()
    print('DRY RUN', json.dumps(summary))
    if not a.write: return
    builder.VERSION, builder.BASE, builder.OUTPUT = a.version, base.BASE, output
    builder.build(changes, reports)
    path = output.with_suffix('.json'); doc = json.loads(path.read_text(encoding='utf-8'))
    doc['coverage'] = summary; doc['runtime_verified'] = False
    path.write_text(json.dumps(doc, indent=2)+'\n', encoding='utf-8')
    inputs = [ROOT/'tools/build_wave_patch.py', ROOT/'tools/build_029_patch.py', ROOT/'tools/hud_labels.py', hud_labels.OUT]
    inputs += sorted(base.previous.SCENES.glob('[0-9]*.json'))+sorted((ROOT/'work/translation/en/dialogue').glob('batch_*.json'))
    output.with_suffix('.manifest.json').write_text(json.dumps({'version':a.version, 'base':base.BASE.name,
        'base_sha256':hashlib.sha256(base.BASE.read_bytes()).hexdigest() if False else json.loads(base.BASE.with_suffix('.json').read_text(encoding='utf-8'))['sha256'],
        'sha256':doc['sha256'], 'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
