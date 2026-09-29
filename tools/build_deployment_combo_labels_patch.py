"""0.9.1: give Deployment combo captions a full, separate text column.

Dry run by default; --write creates a new local ISO and checks every byte.
"""
import hashlib
import json
import struct
from build_ui_patch import ROOT, require, u32
from build_flight_save_patch import parts
from build_stats_panel_patch import ranges
from dialogue_corpus import archive, parse_table
from ui_font import measure_text
import build_stats_panel_patch as writer

VERSION = '0.9.1'
BASE = ROOT/'work/release/ACE3-English-0.9.0-orig-layout.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_HASH = '68b7fc22f7cde93b453223af0d45ca4e040be40f0edb263acc128f354e1e37d1'
LAYOUT_HASH = '2f70fd7103d9e6727413f112ff02faff1a28bf552c722da7c8f03cbb0a547afb'
SPEC = ROOT/'work/ui/deployment_combo_091/layout.json'


def repair(data, font, texts, spec):
    require(hashlib.sha256(data).hexdigest() == LAYOUT_HASH, 'Layout preimage changed')
    require(u32(data, 4) == 514 and u32(data, 12) == 80, 'Layout format')
    out = bytearray(data)
    allowed, rows = set(), []

    def put(at, value):
        struct.pack_into('<f', out, at, value)
        allowed.update(range(at, at+4))

    def quad(node, kind, binding):
        a = 80+node*112
        require(node < u32(data, 8) and data[a+85] == kind, 'Widget type')
        require(struct.unpack_from('<h', data, a+86)[0] == binding, 'Widget binding')
        require(struct.unpack_from('<4f', data, a+32) == (1, 1, 1, 1), 'Widget scale')
        count, ptr = struct.unpack_from('<II', data, a+60)
        require(count == 4 and ptr+64 <= len(data), 'Widget quad')
        xs = [struct.unpack_from('<f', data, ptr+i*16)[0] for i in range(4)]
        return a, ptr, xs

    shift = spec['column_shift']
    frame = 80+spec['divider_node']*112
    require(data[frame+85] == 1, 'Divider type')
    count, ptr = struct.unpack_from('<II', data, frame+60)
    require(count == 20 and ptr+count*16 <= len(data), 'Divider mesh')
    # Move only the two vertical separators. Leave row baselines and borders.
    separator_indices = []
    for i in range(count):
        x = struct.unpack_from('<f', data, ptr+i*16)[0]
        if 89 < x < 92:
            put(ptr+i*16, x+shift)
            separator_indices.append(i)
    require(separator_indices == [4, 5, 6, 7, 14, 15, 16, 17], 'Divider topology')
    divider_left = struct.unpack_from('<f', data, frame)[0]+89.61295318603516+shift

    for row in spec['rows']:
        text = texts[row['text_id']]
        require(text == row['text'], 'Caption text changed')
        a, p, xs = quad(row['node'], 10, row['text_id'])
        width = max(measure_text(font, text))
        require(struct.unpack_from('<H', data, a+98)[0] >= len(text)+1, 'Caption capacity')
        # Widen the local line itself. Do not rely on a scale/origin override.
        left, right = min(xs), max(xs)
        box_width = width+8
        for i, x in enumerate(xs):
            if abs(x-right) < .001:
                put(p+i*16, left+box_width)
        caption_left = struct.unpack_from('<f', data, a)[0]+left
        require(divider_left-caption_left-box_width >= 6, 'Caption touches separator')

        va, vp, vxs = quad(row['value_node'], row['value_type'], row['value_binding'])
        # Bake the new value position into its vertices, retaining native origins.
        # For the long level text box retain its right edge inside the panel.
        for i, x in enumerate(vxs):
            delta = shift if row['value_type'] == 11 or abs(x-min(vxs)) < .001 else 0
            put(vp+i*16, x+delta)
        new_xs = [struct.unpack_from('<f', out, vp+i*16)[0] for i in range(4)]
        value_left = struct.unpack_from('<f', data, va)[0]+min(new_xs)
        require(value_left-divider_left >= 4, 'Value touches separator')
        require(max(new_xs)-min(new_xs) >= 95, 'Value box too narrow')
        rows.append(dict(text=text, node=row['node'], text_width=width,
                         old_box_width=right-left, new_box_width=box_width,
                         separator_clearance=divider_left-caption_left-box_width,
                         value_node=row['value_node'], value_width=max(new_xs)-min(new_xs)))

    require(all(x == y or i in allowed for i, (x, y) in enumerate(zip(data, out))),
            'Unrelated layout bytes changed')
    require(len(out) == len(data), 'Layout extent changed')
    return bytes(out), rows


def plan():
    spec = json.loads(SPEC.read_text(encoding='utf-8'))
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        e = next(e for e in entries if e[3] == spec['bundle'])
        origin = fi['offset']+e[2]
        f.seek(origin)
        bundle = f.read(e[1])
        p = parts(bundle)
        texts = {i: raw.decode('cp932') for _, i, _, raw in parse_table(p[3013])[3]}
        before = parts(p[spec['layout']])[0]
        after, rows = repair(before, p[2500], texts, spec)
        offset = origin+ranges(bundle)[spec['layout']][0]+ranges(p[spec['layout']])[0][0]
    return [dict(offset=offset, before=before, after=after)], dict(
        bundle=spec['bundle'], layout=spec['layout'], labels=rows,
        column_shift=spec['column_shift'], runtime_verified=False), None


if __name__ == '__main__':
    writer.VERSION, writer.BASE, writer.OUTPUT, writer.BASE_HASH = VERSION, BASE, OUTPUT, BASE_HASH
    writer.plan = plan
    writer.main()
