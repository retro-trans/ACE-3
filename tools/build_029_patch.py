"""0.1.29: English captions painted into the Global Meeting pictures, plus the next reviewed scenes.

On top of 0.1.28:
 1. every caption picture in the 4003xxx meeting/briefing/archive files is repainted (tools/meeting_captions.py);
    texture size, header and palette are unchanged, so the files keep their layout;
 2. newly reviewed window scenes from work/translation/en/scenes (scenes already inserted are recognised and skipped);
 3. newly reviewed complete in-mission scenes, relocated as before.
Dry-run unless --write.
"""
import argparse
import hashlib
import json
import re
import struct
from build_ui_patch import ROOT, require, u32
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts, controls
from build_intermission_patch import replace_rows
from ui_font import measure_text
import build_dialogue_patch as builder
import build_scene_patch as scene
import build_reviewed_scenes_patch as old_scenes
import build_028_patch as previous
import meeting_captions as captions

VERSION = '0.1.29'
BASE = ROOT/'work/output/ACE3-English-0.1.28.iso'
OUTPUT = ROOT/'work/output/ACE3-English-0.1.29.iso'
TAG = previous.TAG
TRAIN = {5:'Warning: Train at 5％ damage', 25:'Warning: Train at 25％ damage', 50:'Warning: Train at 50％ damage', 75:'Warning: Train at 75％ damage'}
AUXILIARY = {
 2002060:{3:'Destroy the Rushrod', 4:'Objective: Destroy the Rushrod', 10:'Objective: Train leaves the area',
          11:'Warning: Blockade force sighted', 12:'Info: Train moving again on Route A', 13:'Warning: Enemy reinforcements',
          14:'Info: Train has left the area', 15:'Warning: 5 minutes remaining', 16:'Mission Failed: Time Over',
          17:TRAIN[5], 18:TRAIN[25], 19:TRAIN[50], 20:TRAIN[75], 21:'Mission Failed: Train destroyed',
          22:'Info: Train moving again on Route B'},
}


def picture_edits(rid, p, seen):
    edits, report = {}, []
    for key, chunk in p.items():
        if key < 2 or len(chunk) != captions.SIZE: continue
        sha = hashlib.sha256(chunk).hexdigest()[:12]
        if sha not in captions.CAPTIONS: continue
        if sha not in seen: seen[sha] = captions.repaint(chunk, captions.CAPTIONS[sha])
        edits[key] = seen[sha][0]; report.append({'chunk':key, 'picture':sha, 'captions':[c['text'] for c in seen[sha][1]]})
    return edits, report


def text_edits(rid, p, doc, font):
    edits, tables = {}, []
    for tid in sorted({r['table'] for r in doc['rows']}):
        stock = parse_table(p[tid])[3]; targets = {r['slot']:r for r in doc['rows'] if r['table'] == tid}
        require(set(targets) == {s for s, _, _, _ in stock}, 'Incomplete scene table %s/%s' % (rid, tid))
        mappings, rows = {}, []
        for slot, text_id, _, raw in stock:
            source, row = raw.decode('cp932'), targets[slot]; en = row['en']
            require(row['text_id'] == text_id, 'Text ID mismatch %s/%s/%s' % (rid, tid, slot))
            require('\n' not in en and not re.search(r'[^\x20-\x7e]', TAG.sub('', en)), 'Non-ASCII or newline: %s/%s' % (rid, slot))
            title = rid//1000 == 4003 and '<operator(' not in en and '<speed(' not in en  # screen and list titles
            target = en if title else previous.wrap_window(en, font, rid//1000)
            if title: require(max(measure_text(font, target)) <= 420, 'Title too wide: '+target)
            if source == target: continue  # inserted by an earlier build
            require(hashlib.sha256(raw).hexdigest() == row['source_sha256'], 'Scene preimage changed %s/%s/%s' % (rid, tid, slot))
            require(controls(source) == controls(target), 'Scene commands changed %s/%s/%s' % (rid, tid, slot))
            mappings[slot] = (source, target)
            rows.append({'slot':slot, 'text_id':text_id, 'target':target, 'widths':measure_text(font, TAG.sub('', target))})
        if mappings: edits[tid] = replace_rows(p[tid], mappings); tables.append({'table_id':tid, 'rows':rows})
    return edits, tables


def mission_scenes(get, font):
    translations = previous.reviewed(); replacements, reports, skipped = {}, [], []
    keep, keep_width = scene.wrap, scene.WIDTH
    scene.wrap, scene.WIDTH = previous.Mission.wrap, 480
    try:
        for scene_id, auxiliary in AUXILIARY.items():
            for rid in old_scenes.copies(scene_id):
                data = get(rid); old = u32(data, 20); size = parse_table(data, old)[0]
                require(old+size <= len(data), 'Malformed scene: %s' % rid)
                missing = [i for _, i, _, raw in parse_table(data, old)[3] if b'<sp(' in raw and hashlib.sha256(raw).hexdigest() not in translations]
                if missing: skipped.append((rid, len(missing))); continue
                table, rows = scene.rebuild_table(data[old:old+size], translations, font, auxiliary)
                new = builder.align(len(data), 32)
                output = bytearray(data+b'\0'*(new-len(data))+table); struct.pack_into('<I', output, 20, new)
                require(output[24:len(data)] == data[24:] and output[:20] == data[:20], 'Original script modified')
                replacements[rid] = bytes(output)
                reports.append({'resource_id':rid, 'kind':'relocated_dialogue_table', 'original_offset':old, 'relocated_offset':new,
                                'original_size':len(data), 'new_size':len(output), 'rows':rows})
    finally:
        scene.wrap, scene.WIDTH = keep, keep_width
    return replacements, reports, skipped


def plan():
    docs, unreviewed = {}, []
    for path in sorted(previous.SCENES.glob('[0-9]*.json')):
        doc = json.loads(path.read_text(encoding='utf-8'))
        if doc.get('status') == 'meaning_reviewed' and all('source_sha256' in r for r in doc['rows']): docs[doc['resource_id']] = doc
        else: unreviewed.append(doc['resource_id'])
    changes, reports, seen = {}, [], {}
    with BASE.open('rb') as f:
        fi, es = archive(f)
        def get(rid):
            e = next(x for x in es if x[3] == rid); f.seek(fi['offset']+e[2]); return f.read(e[1])
        game_font, menu_font = parts(get(1200000))[2500], parts(get(4002050))[2500]
        for entry in es:
            rid = entry[3]
            if not 4003000 <= rid < 4005000: continue
            data = get(rid)
            try: p = parts(data)
            except ValueError: continue
            pictures, picture_report = picture_edits(rid, p, seen)
            texts, tables = text_edits(rid, p, docs[rid], menu_font) if rid in docs else ({}, [])
            if not pictures and not texts: continue
            require(all(len(pictures[k]) == len(p[k]) for k in pictures), 'Picture size changed')
            changes[rid] = previous.rebuild_scene_bundle(data, {**texts, **pictures})
            reports.append({'resource_id':rid, 'kind':'window_scene', 'old_size':len(data), 'new_size':len(changes[rid]),
                            'tables':tables, 'pictures':picture_report})
        mission, mission_reports, mission_skipped = mission_scenes(get, game_font)
    require(not set(changes) & set(mission), 'Resource planned twice')
    changes.update(mission); reports += mission_reports
    summary = {'resources':len(changes), 'pictures_repainted':len(seen), 'picture_instances':sum(len(r.get('pictures', [])) for r in reports),
               'captions':sum(len(v[1]) for v in seen.values()),
               'window_scenes_with_new_text':sorted(r['resource_id'] for r in reports if r.get('tables')),
               'window_rows':sum(len(t['rows']) for r in reports for t in r.get('tables', [])), 'window_unreviewed':unreviewed,
               'mission_scene_resources':sorted(mission), 'mission_rows':sum(len(r['rows']) for r in mission_reports),
               'mission_skipped_incomplete':mission_skipped}
    return changes, reports, summary


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    changes, reports, summary = plan()
    print('DRY RUN', json.dumps(summary))
    for r in reports:
        if r['kind'] == 'window_scene' and r['tables']:
            print(r['resource_id'], r['old_size'], '->', r['new_size'])
            for x in r['tables'][0]['rows'][:2]: print('    ', repr(x['target']), x['widths'])
    if not a.write: return
    builder.VERSION, builder.BASE, builder.OUTPUT = VERSION, BASE, OUTPUT
    builder.build(changes, reports)
    path = OUTPUT.with_suffix('.json'); doc = json.loads(path.read_text(encoding='utf-8'))
    doc['coverage'] = summary; doc['runtime_verified'] = False
    path.write_text(json.dumps(doc, indent=2)+'\n', encoding='utf-8')
    inputs = [ROOT/'tools/build_029_patch.py', ROOT/'tools/build_028_patch.py', ROOT/'tools/meeting_captions.py', ROOT/'tools/build_scene_patch.py']
    inputs += sorted(previous.SCENES.glob('[0-9]*.json'))+sorted((ROOT/'work/translation/en/dialogue').glob('batch_*.json'))
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps({'version':VERSION, 'base':BASE.name,
        'base_sha256':'a1e05e316a65d54dc2d66265ce9d7de682c5f2de2d70b313d9ca33c1eda4d6b7', 'sha256':doc['sha256'],
        'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
