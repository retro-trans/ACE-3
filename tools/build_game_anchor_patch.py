"""0.9.20: retain native Game widget anchors and bake spacing into meshes.

0.9.19 checked descriptor positions, but the displayed menu uses the native
anchors. This is the same failure previously corrected in Controls (0.1.52).
"""
import hashlib
import json
import struct
from build_game_column_patch import geometry, ranges, CHOICES, LABELS, VALUE_IDS
from build_game_spacing_patch import PANELS
from build_ui_patch import ROOT, require, u32
from build_flight_save_patch import parts
from dialogue_corpus import archive, parse_table
from ui_font import measure_text
import build_stats_panel_patch as writer

VERSION = '0.9.20'
BASE = ROOT/'work/output/ACE3-English-0.9.19.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
REFERENCE = ROOT/"Another Century's Episode 3 - The Final (Japan).iso"
BASE_HASH = '69d28cbaa58f205ae0bc0a03d98db83944160742a81096fc18c9535c54c27f61'
FOLDER = ROOT/'work/ui/game_anchors_0920'


def x_bounds(data, reference, node, indices=None):
    a, _, xs = geometry(data, node)
    x = struct.unpack_from('<f', reference, a)[0]
    selected = xs if indices is None else [xs[i] for i in indices]
    return x+min(selected), x+max(selected)


def clearances(data, anchors, rows, font):
    result = []
    for panel in PANELS:
        _, _, xs = geometry(data, panel)
        count = (len(xs)-12)//4+1
        boxes = []
        for node in range(panel+2, panel+2*count+1, 2):
            a, _, _ = geometry(data, node)
            binding = struct.unpack_from('<h', data, a+86)[0]
            text = rows[VALUE_IDS[binding]]
            width = max(measure_text(font, text))
            left, right = x_bounds(data, anchors, node)
            middle = (left+right)/2
            boxes.append(dict(node=node, text=text, left=middle-width/2, right=middle+width/2))
        arrow_groups = sorted((list(range(i, i+4)) for i in range(12, len(xs), 4)),
                              key=lambda ids: min(xs[j] for j in ids))
        gaps = []
        for i, indices in enumerate(arrow_groups):
            left, right = x_bounds(data, anchors, panel, indices)
            gaps.append(dict(after=boxes[i]['text'], before=boxes[i+1]['text'],
                             left_gap=left-boxes[i]['right'], right_gap=boxes[i+1]['left']-right))
        caption = 3 if panel == 74 else panel-1
        a, _, _ = geometry(data, caption)
        binding = struct.unpack_from('<h', data, a+86)[0]
        text = rows[binding-98]
        text_right = x_bounds(data, anchors, caption)[0]+max(measure_text(font, text))
        dash_left = x_bounds(data, anchors, panel, range(8, 12))[0]
        result.append(dict(panel=panel, text_bounds=boxes, arrow_gaps=gaps,
                           caption=text, connector_gap=dash_left-text_right))
    return result


def correct(before, reference, rows, font):
    require(u32(before, 8) == u32(reference, 8) == 89, 'Game node inventory changed')
    after = bytearray(before)
    allowed, vertex_fields, moves = set(), set(), []
    for node in CHOICES:
        a, ptr, xs = geometry(before, node)
        require(before[a+85] == reference[a+85], 'Native widget type mismatch')
        require(before[a+86:a+88] == reference[a+86:a+88], 'Native widget binding mismatch')
        require(struct.unpack_from('<4f', before, a+32) == (1, 1, 1, 1), 'Unexpected widget scale')
        old_x = struct.unpack_from('<f', before, a)[0]
        native_x = struct.unpack_from('<f', reference, a)[0]
        delta = old_x-native_x
        require(0 < delta < 24, 'Unexpected inherited origin adjustment')
        struct.pack_into('<f', after, a, native_x)
        allowed.update(range(a, a+4))
        for i, x in enumerate(xs):
            at = ptr+i*16
            require(at not in vertex_fields, 'Shared mesh needs separate handling')
            vertex_fields.add(at)
            struct.pack_into('<f', after, at, x+delta)
            allowed.update(range(at, at+4))
            actual = native_x+struct.unpack_from('<f', after, at)[0]
            require(abs(actual-(old_x+x)) < .0001, 'Spacing changed during anchor correction')
        moves.append(dict(node=node, descriptor_x=old_x, native_x=native_x,
                          mesh_shift=delta, vertex_count=len(xs)))
    require(all(a == b or i in allowed for i, (a, b) in enumerate(zip(before, after))),
            'Unrelated bytes changed')
    for node in range(89):
        a = 80+node*112
        require(before[a+4:a+112] == after[a+4:a+112], 'Non-X widget attribute changed')
    old_checks = clearances(before, reference, rows, font)
    checks = clearances(after, reference, rows, font)
    # Replay native anchoring instead of trusting modified descriptor positions.
    # This must reproduce a failing old case, then pass for all corrected rows.
    old_min = min(min(g['left_gap'], g['right_gap']) for p in old_checks for g in p['arrow_gaps'])
    require(old_min < 0, 'Regression no longer reproduces with native anchors')
    for p in checks:
        require(p['connector_gap'] >= 28, 'Caption still touches connector with native anchor')
        for gap in p['arrow_gaps']:
            require(min(gap['left_gap'], gap['right_gap']) >= 6, 'Arrow still overlaps native-anchored text')
        for box in p['text_bounds']:
            require(-320 < box['left'] < box['right'] < 306, 'Choice outside visible menu')
        for box in p['text_bounds']:
            node = box['node']
            require(all(abs(x-y) < .001 for x, y in zip(x_bounds(after, reference, node),
                                                        x_bounds(after, reference, node-1))),
                    'Highlight and text-cell alignment differs at native anchor')
    return bytes(after), dict(native_layout_sha256=hashlib.sha256(reference).hexdigest(),
                             corrected_widgets=moves, old_native_clearances=old_checks,
                             corrected_native_clearances=checks,
                             old_minimum_arrow_gap=old_min, runtime_verified=False)


def plan():
    edits, reports = [], []
    with BASE.open('rb') as f, REFERENCE.open('rb') as ref:
        fi, es = archive(f)
        ri, rs = archive(ref)
        for rid in (4002050, 4002054, 4002057):
            _, size, off, _ = next(e for e in es if e[3] == rid)
            origin = fi['offset']+off
            f.seek(origin)
            bundle = f.read(size)
            p = parts(bundle)
            _, size, off, _ = next(e for e in rs if e[3] == rid)
            ref.seek(ri['offset']+off)
            reference = parts(parts(ref.read(size))[42])[0]
            rows = {tid: raw.decode('cp932') for _, tid, _, raw in parse_table(p[3070])[3]}
            before = parts(p[42])[0]
            after, report = correct(before, reference, rows, p[2500])
            edits.append(dict(offset=origin+ranges(bundle)[42][0]+ranges(p[42])[0][0],
                              before=before, after=after))
            reports.append(dict(bundle=rid, **report))
    edits.sort(key=lambda e: e['offset'])
    require(all(len(e['before']) == len(e['after']) for e in edits), 'Layout extent changed')
    require(all(a['offset']+len(a['after']) <= b['offset'] for a, b in zip(edits, edits[1:])),
            'Overlapping edits')
    summary = dict(version=VERSION, menus=reports, runtime_verified=False,
                   diagnosis='0.9.19 retained shifted descriptors from 0.1.50, but screenshot placement matches native anchors. Restore those anchors and bake the offset into vertices, as in the existing Controls fix.')
    FOLDER.mkdir(parents=True, exist_ok=True)
    (FOLDER/'layout.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    return edits, summary, None


if __name__ == '__main__':
    writer.VERSION, writer.BASE, writer.OUTPUT, writer.BASE_HASH = VERSION, BASE, OUTPUT, BASE_HASH
    writer.plan = plan
    writer.main()
