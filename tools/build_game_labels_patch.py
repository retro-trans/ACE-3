"""0.1.44: user-requested Game option names and complete local label boxes.

Default dry run; --write builds and verifies a new ISO from 0.1.43.
"""
import argparse
import json
import struct
from build_ui_patch import ROOT, require, u32, inner_bnd
from build_flight_save_patch import parts
from build_intermission_patch import replace_rows
from dialogue_corpus import archive, parse_table
from ui_font import measure_text
import build_dialogue_patch as builder

VERSION = '0.1.44'
BASE = ROOT/'work/output/ACE3-English-0.1.43.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
INPUT = ROOT/'work/translation/en/game_labels_044.json'


def fit_labels(layout, specs, font, limit):
    d = parts(layout)[0]
    require(u32(d, 4) == 514 and u32(d, 12) == 80, 'Unexpected Game layout')
    out = bytearray(d)
    allowed, reports, meshes = set(), [], set()
    for row in specs:
        node, tid = row['node'], row['text_id']
        a = 80 + node*112
        require(node < u32(d, 8) and d[a+85] == 10, 'Wrong label widget')
        require(struct.unpack_from('<h', d, a+86)[0] == tid+98, 'Label binding mismatch')
        x, y = struct.unpack_from('<2f', d, a)
        require(-293 < x < -290 and abs(y-(-160.080154+30*(tid-5))) < .01, 'Label position changed')
        require(struct.unpack_from('<3f', d, a+36) == (1, 1, 1), 'Vertical scale changed')
        old_width = max(measure_text(font, row['before']))
        old_scale = struct.unpack_from('<f', d, a+32)[0]
        require(abs(old_scale-min(1, limit/old_width)) < .00001, 'Unexpected previous label fit')
        require(struct.unpack_from('<H', d, a+98)[0] >= len(row['target'])+1, 'Glyph capacity exceeded')
        n, ptr = struct.unpack_from('<II', d, a+60)
        require(n == 4 and ptr+n*16 <= len(d) and ptr not in meshes, 'Unexpected/shared text quad')
        meshes.add(ptr)
        xs = [struct.unpack_from('<f', d, ptr+i*16)[0] for i in range(n)]
        left, right = min(xs), max(xs)
        width = max(measure_text(font, row['target']))
        # Keep enough local space for one complete line before scaling its
        # rendered width. Retain the left edge, row height and control binding.
        box_width = max(right-left, width+8)
        scale = min(1, limit/box_width)
        def set_float(offset, value):
            struct.pack_into('<f', out, offset, value)
            allowed.update(range(offset, offset+4))
        for i, value in enumerate(xs):
            if value == right:
                set_float(ptr+i*16, left+box_width)
        set_float(a+32, scale)
        set_float(a, x+left*(old_scale-scale))
        # Validate serialized geometry, including float32 rounding.
        actual_x = [struct.unpack_from('<f', out, ptr+i*16)[0] for i in range(n)]
        actual_scale = struct.unpack_from('<f', out, a+32)[0]
        require(max(actual_x)-min(actual_x) >= width+7.99, 'Local line too narrow')
        require((max(actual_x)-min(actual_x))*actual_scale <= limit+.001, 'Display box too wide')
        require(out[a+84:a+112] == d[a+84:a+112], 'Binding or capacity changed')
        reports.append(dict(text_id=tid, node=node, before=row['before'], target=row['target'],
                            width=width, box_width=box_width, scale_x=scale, display_width=width*scale))
    require(all(i in allowed or a == b for i, (a, b) in enumerate(zip(d, out))), 'Unrelated layout bytes changed')
    start, end = next((a, b) for k, a, b in inner_bnd(layout[:u32(layout, 4)]) if k == 0)
    return layout[:start]+bytes(out)+layout[end:], reports


def plan():
    spec = json.loads(INPUT.read_text(encoding='utf-8'))
    changes, reports = {}, []
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        for rid in spec['bundles']:
            _, size, off, _ = next(e for e in entries if e[3] == rid)
            f.seek(fi['offset']+off)
            before = f.read(size)
            p = parts(before)
            rows = parse_table(p[spec['table_id']])[3]
            by_id = {r['text_id']: r for r in spec['rows']}
            mappings = {slot: (by_id[tid]['before'], by_id[tid]['target'])
                        for slot, tid, _, raw in rows if tid in by_id}
            require(len(mappings) == len(by_id), 'Missing option labels')
            table = replace_rows(p[spec['table_id']], mappings)
            updated_layout, rr = fit_labels(p[spec['layout_id']], spec['rows'], p[2500], spec['display_width'])
            edits = {spec['table_id']: table, spec['layout_id']: updated_layout}
            after = builder.rebuild_bundle(before, edits)
            resources = parts(after)
            require(all(v == resources[k] for k, v in p.items() if k not in edits), 'Unrelated resource changed')
            expected = [(s, tid, by_id[tid]['target'].encode('cp932') if tid in by_id else raw)
                        for s, tid, _, raw in rows]
            require([(s, tid, raw) for s, tid, _, raw in parse_table(resources[spec['table_id']])[3]] == expected,
                    'Unselected text changed')
            changes[rid] = after
            reports.append(dict(resource_id=rid, table_id=spec['table_id'], layout_id=spec['layout_id'], labels=rr))
    return changes, reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    changes, reports = plan()
    print('DRY RUN', json.dumps(reports, indent=2), flush=True)
    if not args.write:
        return
    builder.VERSION, builder.BASE, builder.OUTPUT = VERSION, BASE, OUTPUT
    builder.build(changes, reports)
    with OUTPUT.open('rb') as f:
        fi, entries = archive(f)
        for rid, expected in changes.items():
            _, size, off, _ = next(e for e in entries if e[3] == rid)
            f.seek(fi['offset']+off)
            require(f.read(size) == expected, 'Finished-disc bundle differs')
    path = OUTPUT.with_suffix('.json')
    report = json.loads(path.read_text(encoding='utf-8'))
    report['coverage'] = 'Lock-On Info, Lock-On Priority and Ingame Comm in three Game menu copies, with fitted local text boxes.'
    report['checks'] = dict(label_copies=9, finished_disc_bundles_match=True, runtime_verified=False)
    path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('VERIFIED', OUTPUT, report['sha256'], flush=True)


if __name__ == '__main__':
    main()
