"""0.9.4: fit the Comm badge and apply the user's Jamil wording correction.

Dry-run by default. --write builds and verifies a new local test ISO.
"""
import argparse
import hashlib
import json
import struct

from build_ui_patch import ROOT, require, u32
from dialogue_corpus import archive, parse_table, INDEX
from build_flight_save_patch import parts
from build_communication_fit_patch import relocate
from build_scene_patch import wrap_words
from build_stats_panel_patch import ranges
from ui_font import measure_text
import build_dialogue_patch as builder

VERSION = '0.9.4'
BASE = ROOT/'work/release/ACE3-English-0.9.3-orig-layout.iso'
BASE_HASH = 'e8a5173150f3c44017adb652aee4798696d3e6ab1ebf86d4bc611b800d53b02b'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
SPEC = ROOT/'work/ui/comm_094/layout.json'
TRANSLATION = ROOT/'work/translation/en/dialogue/batch_04478.json'
ROW = 'dialogue_04529'
OLD = '<on()><sp(20)>Thanks to your hard fighting, we were able to handle it fast.'
NEW = '<on()><sp(20)>Thanks to your hard work fighting, we were able to handle it fast.'


def fit_badge(data, fonts, spec):
    require(hashlib.sha256(data).hexdigest() == spec['layout_sha256'], 'Badge layout changed')
    require(u32(data, 4) == 514 and u32(data, 12) == 80, 'Unknown layout format')
    frame, text = [80+spec[k]*112 for k in ('frame_node', 'text_node')]
    require(data[frame+85] == 1 and data[text+85] == 4, 'Badge widget types changed')
    require(struct.unpack_from('<h', data, text+86)[0] == spec['binding'], 'Badge binding changed')
    require(struct.unpack_from('<H', data, text+98)[0] >= len(spec['text'])+1, 'Badge capacity')
    fc, fp = struct.unpack_from('<II', data, frame+60)
    tc, tp = struct.unpack_from('<II', data, text+60)
    require((fc, tc) == (8, 4), 'Badge topology changed')
    frame_x = struct.unpack_from('<f', data, frame)[0]
    text_x = struct.unpack_from('<f', data, text)[0]
    fxs = [frame_x+struct.unpack_from('<f', data, fp+i*16)[0] for i in range(fc)]
    xs = [struct.unpack_from('<f', data, tp+i*16)[0] for i in range(tc)]
    widths = [measure_text(font, spec['text'])[0] for font in fonts]
    require(set(widths) == {62, 66}, 'Communication font variants changed')
    width, scale = max(widths), spec['scale_x']
    left, right = min(fxs), max(fxs)
    new_left = (left+right-width*scale)/2
    shift = (new_left-text_x)/scale-min(xs)
    out, allowed = bytearray(data), set()
    def put(at, value):
        struct.pack_into('<f', out, at, value)
        allowed.update(range(at, at+4))
    # Keep native origins: animation may update them at runtime.
    for i, x in enumerate(xs):
        put(tp+i*16, x+shift)
    put(text+32, scale)
    after_xs = [struct.unpack_from('<f', out, tp+i*16)[0] for i in range(tc)]
    actual_left = text_x+min(after_xs)*scale
    actual_right = actual_left+width*scale
    padding = [actual_left-left, right-actual_right]
    require(min(padding) >= spec['minimum_horizontal_padding'], 'Comm exceeds frame')
    require(abs((max(after_xs)-min(after_xs))-(max(xs)-min(xs))) < .001, 'Local line width changed')
    require(max(after_xs)-min(after_xs) > width+8, 'Local line too narrow')
    require(all(a == b or i in allowed for i, (a, b) in enumerate(zip(data, out))), 'Unrelated layout changed')
    require(len(out) == len(data), 'Layout size changed')
    return bytes(out), dict(frame_bounds=[left, right], text_bounds=[actual_left, actual_right],
        text_width=width, padding=padding, local_vertex_shift=shift,
        old_scale_x=struct.unpack_from('<f', data, text+32)[0], scale_x=scale)


def plan():
    spec = json.loads(SPEC.read_text(encoding='utf-8'))
    draft = next(r for r in json.loads(TRANSLATION.read_text(encoding='utf-8'))['rows'] if r['id'] == ROW)
    require(draft['target'] == NEW, 'Unexpected corrected wording')
    indexed = next(r for r in json.loads(INDEX.read_text(encoding='utf-8'))['rows'] if r['id'] == ROW)
    require({o['resource_id'] for o in indexed['occurrences']} == {6140, 2002140, 3200140, 3201140}, 'Scene coverage changed')
    changes, reports = {}, []
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        def get(rid):
            e = next(e for e in entries if e[3] == rid)
            f.seek(fi['offset']+e[2])
            return f.read(e[1])
        fonts = []
        for rid in range(1200000, 1200008):
            p = parts(get(rid))
            texts = {i: raw.decode('cp932') for _, i, _, raw in parse_table(p[spec['text_table']])[3]}
            require(texts[spec['text_id']] == spec['text'], 'Comm table text changed')
            fonts.append(p[2500])
        fonts.append(parts(get(1200011))[2500])
        bundle = get(spec['bundle'])
        p = parts(bundle)
        after, badge = fit_badge(p[spec['layout']], fonts, spec)
        start, end = ranges(bundle)[spec['layout']]
        changed_bundle = bytearray(bundle)
        changed_bundle[start:end] = after
        changes[spec['bundle']] = bytes(changed_bundle)
        require(all(parts(changes[spec['bundle']])[k] == v for k, v in p.items() if k != spec['layout']), 'Unrelated badge resource changed')
        reports.append(dict(resource_id=spec['bundle'], kind='comm_badge_fit', layout=spec['layout'], checks=badge))
        target = wrap_words(NEW, fonts[0], 460, 3)
        widths = [measure_text(font, builder.TOKEN.sub('', target)) for font in fonts]
        require(max(max(ws) for ws in widths) <= 460 and len(target.split('\n')) <= 3, 'Dialogue does not fit')
        for occurrence in indexed['occurrences']:
            rid = occurrence['resource_id']
            data = get(rid)
            rows = parse_table(data, u32(data, 20))[3]
            slot, tid, _, raw = next(r for r in rows if r[1] == occurrence['text_id'])
            source = raw.decode('cp932')
            require(slot == occurrence['slot'] and source.split() == OLD.split(), 'Dialogue preimage changed')
            after, at = relocate(data, {slot: (source, target)})
            expected = [(s, i, target.encode('cp932') if s == slot else raw) for s, i, _, raw in rows]
            require([(s, i, raw) for s, i, _, raw in parse_table(after, at)[3]] == expected, 'Other scene text changed')
            changes[rid] = after
            reports.append(dict(resource_id=rid, kind='jamil_wording', row=ROW, text_id=tid,
                target=target, line_widths=widths[0], table_offset=at))
    return changes, reports


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    changes, reports = plan()
    print(json.dumps(dict(version=VERSION, changes=reports), indent=2), flush=True)
    if not args.write:
        return
    require(not OUTPUT.exists(), 'Output already exists')
    with BASE.open('rb') as f:
        require(builder.sha_region(f, 0, BASE.stat().st_size) == BASE_HASH, 'Base ISO mismatch')
    builder.VERSION, builder.BASE, builder.OUTPUT = VERSION, BASE, OUTPUT
    builder.build(changes, reports)
    path = OUTPUT.with_suffix('.json')
    report = json.loads(path.read_text(encoding='utf-8'))
    report.update(base_sha256=BASE_HASH, runtime_verified=False,
        coverage='Shared Comm badge geometry and Jamil wording in all four scene copies.',
        limitations='Geometry, text fit and full-disc checks passed; fresh-boot in-game confirmation remains pending.')
    path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
