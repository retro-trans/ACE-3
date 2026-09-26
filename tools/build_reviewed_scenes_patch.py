"""0.1.21: insert five scenes whose dialogue was already translated and reviewed in 0.1.6 but never inserted.

Scenes 2002011, 2002020, 2002021, 2002030 and 2002031 with their 60xx/3200xxx/3201xxx copies: the
training follow-up and the Mission 02/03 in-mission chatter, alerts and nav messages.
"""
import argparse
import hashlib
import json
import struct
from build_ui_patch import ROOT, inner_bnd, require, u32
from dialogue_corpus import archive, parse_table, INDEX
import build_dialogue_patch as builder
import build_scene_patch as scene

VERSION = '0.1.21'
BASE = ROOT/'work/output/ACE3-English-0.1.20.iso'
OUTPUT = ROOT/'work/output/ACE3-English-0.1.21.iso'
NADESICO = {25:'Warning: Nadesico B at 25％ damage', 50:'Warning: Nadesico B at 50％ damage', 75:'Warning: Nadesico B at 75％ damage'}
ALLY50, ALLY0 = 'Warning: Allied forces at 50％ damage', 'Warning: Allied forces wiped out'
# HUD labels stored beside the dialogue. Wording follows released labels: Objective:, Warning:,
# "5 minutes remaining", "Mission Failed: Time Over", Destroy/Capture, Gun Ark, Giganos, Nadesico B.
AUXILIARY = {
 2002011:{1:'Destroy the training units', 3:'Destroy the Gun Ark'},
 2002020:{10:'Objective: Destroy all targets', 11:ALLY50, 12:ALLY0, 13:NADESICO[25], 14:NADESICO[50], 15:NADESICO[75],
          16:'Mission Failed: Nadesico B sunk', 17:'Warning: 5 minutes remaining', 18:'Mission Failed: Time Over',
          28:'Warning: Enemy reinforcements', 29:'Mission Complete: All targets destroyed', 30:'Warning: Enemy advancing',
          31:"Nav: Watch the Nadesico B's damage", 32:'Nav: Watch for allied losses', 33:'Info: Allied forces advancing'},
 2002021:{1:'Destroy all Giganos bases'},
 2002030:{10:'Target: Capture all target bases', 11:ALLY50, 12:ALLY0, 13:ALLY50, 14:ALLY0, 15:NADESICO[25], 16:NADESICO[50],
          17:NADESICO[75], 18:'Warning: 5 minutes remaining', 19:'Info: Base captured', 20:'Info: Base captured',
          21:'Info: Base captured', 22:'Info: Base captured', 23:'Warning: Enemy advancing', 24:'Warning: Enemy reinforcements',
          25:'Warning: Enemy reinforcements', 26:'Warning: Enemy reinforcements', 28:'Info: All target bases captured',
          29:'Mission Failed: Nadesico B sunk', 30:'Mission Failed: Time Over', 31:'Left stick (flick): Evade',
          32:'⑤ button ×2: Evade up', 33:'⑦ button ×2: Evade down'},
 2002031:{1:'Destroy UNKNOWN', 10:'Objective: Destroy UNKNOWN'},
}


def copies(scene_id):
    n = scene_id-2002000
    return (6000+n, scene_id, 3200000+n, 3201000+n)


def reviewed():
    indexed = {r['id']:r for r in json.loads(INDEX.read_text(encoding='utf-8'))['rows']}
    out = {}
    for path in sorted((ROOT/'work/translation/en/dialogue').glob('batch_*.json')):
        rows = json.loads(path.read_text(encoding='utf-8')).get('rows', [])
        for row in rows if isinstance(rows, list) else []:
            if row.get('status') == 'meaning_reviewed': out[indexed[row['id']]['source_sha256']] = row
    return out


class InMission:
    """Portrait-window chatter uses the tutorial's measured budget: 460 units, at most four lines."""
    reflowed = []

    @staticmethod
    def wrap(text, font):
        try:
            return scene.wrap_words(text, font, 460, 4)
        except ValueError:
            # A reviewed row whose hand-placed breaks plus wrapping pass four lines is reflowed as one
            # paragraph. Words and commands are unchanged; only the break positions move.
            flat = text.replace('\n', ' ')
            require(flat.split() == text.split(), 'Reflow changed words')
            InMission.reflowed.append(text)
            return scene.wrap_words(flat, font, 460, 4)


def plan():
    translations = reviewed(); replacements, reports = {}, []
    with BASE.open('rb') as stream:
        file, entries = archive(stream)
        def get(rid):
            entry = next(e for e in entries if e[3] == rid); stream.seek(file['offset']+entry[2]); return stream.read(entry[1])
        bundle = get(1200000); font = {k:bundle[a:z] for k, a, z in inner_bnd(bundle)}[2500]
        keep = scene.wrap; scene.wrap = InMission.wrap
        try:
            for scene_id, labels in AUXILIARY.items():
                for rid in copies(scene_id):
                    data = get(rid); old = u32(data, 20); size = parse_table(data, old)[0]
                    require(old < len(data) and old+size <= len(data), 'Scene already relocated or malformed: %s' % rid)
                    table, rows = scene.rebuild_table(data[old:old+size], translations, font, labels)
                    new = builder.align(len(data), 32)
                    output = bytearray(data+b'\0'*(new-len(data))+table); struct.pack_into('<I', output, 20, new)
                    require(output[24:len(data)] == data[24:] and output[:20] == data[:20], 'Original script modified')
                    replacements[rid] = bytes(output)
                    reports.append({'resource_id':rid, 'kind':'relocated_dialogue_table', 'original_offset':old,
                                    'relocated_offset':new, 'original_size':len(data), 'new_size':len(output), 'rows':rows})
        finally:
            scene.wrap = keep
    return replacements, reports


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    replacements, reports = plan()
    summary = {'resources':len(replacements), 'rows':sum(len(r['rows']) for r in reports),
               'dialogue_rows':sum(x['id'].startswith('dialogue_') for r in reports for x in r['rows']),
               'max_width':max(max(x['widths']) for r in reports for x in r['rows']),
               'max_lines':max(x['lines'] for r in reports for x in r['rows'])}
    print('DRY RUN', json.dumps(summary))
    for r in reports:
        if r['resource_id'] == 2002020:
            for x in r['rows']:
                if x['text_id'] in (13, 31) or x['lines'] >= 3: print(json.dumps({k:x[k] for k in ('text_id', 'target', 'widths')}))
    if not a.write: return
    builder.VERSION, builder.BASE, builder.OUTPUT = VERSION, BASE, OUTPUT
    builder.build(replacements, reports)
    path = OUTPUT.with_suffix('.json'); doc = json.loads(path.read_text(encoding='utf-8'))
    doc['coverage'] = 'Scenes 2002010, 2002011, 2002020, 2002021, 2002030, 2002031 and 2002410 complete in all four copies. Other dialogue remains outstanding.'
    doc['scenes'] = summary; doc['runtime_verified'] = False
    path.write_text(json.dumps(doc, indent=2)+'\n', encoding='utf-8')
    inputs = sorted((ROOT/'work/translation/en/dialogue').glob('batch_0*.json'))+[ROOT/'tools/build_reviewed_scenes_patch.py',
              ROOT/'tools/build_scene_patch.py', ROOT/'tools/build_dialogue_patch.py', ROOT/'tools/repair_disc_layout.py']
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps({'version':VERSION, 'base':BASE.name,
        'base_sha256':'da8a36e5717032afff5e9f5d0a407ebf7291c7e7aa8be7b509170a1e2494c821', 'sha256':doc['sha256'],
        'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
