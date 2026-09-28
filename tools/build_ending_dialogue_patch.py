"""0.1.53: translate the separate mission-ending comm table. Dry-run by default."""
import argparse
import hashlib
import json
import struct

from build_ui_patch import ROOT, require, u32
from dialogue_corpus import archive, parse_table, INDEX
from build_flight_save_patch import parts
from ui_font import font_map, measure_text
import build_scene_patch as scene
import build_dialogue_patch as builder

VERSION = '0.1.53'
BASE = ROOT/'work/output/ACE3-English-0.1.52.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
INPUT = ROOT/'work/translation/en/dialogue/batch_ending_053.json'
COPIES = (6341, 2002341, 3200341, 3201341)
BASE_SHA256 = '99652863265618c436709256d49d5870e5062de3a47a3458cfb2d920e83ff96d'


def plan():
    doc = json.loads(INPUT.read_text(encoding='utf-8'))
    require(doc['status'] == 'meaning_reviewed', 'Meaning review required')
    indexed = {r['id']: r for r in json.loads(INDEX.read_text(encoding='utf-8'))['rows']}
    drafts = doc['rows']
    require(len(drafts) == 18 and len({r['id'] for r in drafts}) == 18, 'Incomplete ending table')
    translations = {indexed[r['id']]['source_sha256']: r for r in drafts}
    changes, reports = {}, []
    with BASE.open('rb') as f:
        fi, entries = archive(f)

        def get(rid):
            _, size, off, _ = next(e for e in entries if e[3] == rid)
            f.seek(fi['offset']+off)
            return f.read(size)

        font = parts(get(1200000))[2500]
        glyphs = font_map(font)[0]
        previous_wrap = scene.wrap
        scene.wrap = lambda text, ft: scene.wrap_words(text, ft, 400, 4)
        try:
            for rid in COPIES:
                data = get(rid)
                old = u32(data, 20)
                size, _, count, source_rows = parse_table(data, old)
                require(count == 18 and len(source_rows) == 18, 'Source table changed')
                require({hashlib.sha256(r[3]).hexdigest() for r in source_rows} == set(translations), 'Unexpected source rows')
                table, rows = scene.rebuild_table(data[old:old+size], translations, font, {})
                for row in rows:
                    visible = builder.TOKEN.sub('', row['target'])
                    require(not scene.KANJI.search(visible), 'Japanese remains in ending table')
                    require(all(ord(c) in glyphs for c in visible if c != '\n'), 'Missing glyph')
                    require(max(measure_text(font, visible)) <= 400, 'Comm line too wide')
                new = builder.align(len(data), 32)
                output = bytearray(data+b'\0'*(new-len(data))+table)
                struct.pack_into('<I', output, 20, new)
                require(output[:20] == data[:20] and output[24:len(data)] == data[24:], 'Original scene/script changed')
                require(parse_table(output, new)[0] == len(table), 'Relocation mismatch')
                changes[rid] = bytes(output)
                reports.append(dict(resource_id=rid, kind='relocated_dialogue_table', original_offset=old,
                                    relocated_offset=new, original_size=len(data), new_size=len(output), rows=rows))
        finally:
            scene.wrap = previous_wrap
    require(all(r['rows'] == reports[0]['rows'] for r in reports), 'Copies disagree')
    return changes, reports


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    changes, reports = plan()
    print('DRY RUN: 18 translated rows in each of four mission-ending copies', flush=True)
    print(json.dumps(reports[0]['rows'], indent=2), flush=True)
    if not args.write:
        return
    with BASE.open('rb') as f:
        require(builder.sha_region(f, 0, BASE.stat().st_size) == BASE_SHA256, 'Base disc mismatch')
    builder.VERSION, builder.BASE, builder.OUTPUT = VERSION, BASE, OUTPUT
    builder.build(changes, reports)
    with OUTPUT.open('rb') as f:
        fi, entries = archive(f)
        for rid, expected in changes.items():
            _, size, off, _ = next(e for e in entries if e[3] == rid)
            f.seek(fi['offset']+off)
            require(f.read(size) == expected, 'Finished-disc ending table mismatch')
    path = OUTPUT.with_suffix('.json')
    report = json.loads(path.read_text(encoding='utf-8'))
    report['coverage'] = 'Mission-ending scene 2002341 and its three copies: all 17 timed comm lines and the quit prompt. Other unclassified mission variants and battle shouts are not certified translated.'
    report['base_sha256'] = BASE_SHA256
    report['translation_input_sha256'] = hashlib.sha256(INPUT.read_bytes()).hexdigest()
    report['checks'] = dict(copies=4, rows_per_copy=18, all_controls_preserved=True,
                            original_scripts_preserved=True, finished_disc_tables_verified=True,
                            runtime_verified=False)
    path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('VERIFIED', OUTPUT, report['sha256'], flush=True)


if __name__ == '__main__':
    main()
