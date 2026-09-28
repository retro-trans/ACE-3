"""0.1.49: separate stat captions from gauges without text scaling.

Preview by default; --write produces and verifies a new local test ISO.
"""
import json
import struct
from build_ui_patch import ROOT, require, u32, inner_bnd
from build_flight_save_patch import parts
from dialogue_corpus import archive, parse_table
from ui_font import measure_text
import build_stats_panel_patch as writer

VERSION = '0.1.49'
BASE = ROOT/'work/output/ACE3-English-0.1.48.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_SHA = '904ad87a1dc019992e31869c1fc3e3b19fab528cf4ba1acd41da879b5721c8e0'
INPUT = ROOT/'work/translation/en/stat_columns_049.json'
BAR_SHIFT = 28.0
LABEL_WIDTH = 88.0
PANELS = [
    (4002053, 21, 12, 13, [14, 17, 20, 23, 26, 29], 2, [0, 28, 48, 68, 88, 108]),
    (4002053, 23, 54, 55, [56, 60, 64, 68, 72, 76], 3, [4, 24, 44, 64, 84, 104]),
    (4002050, 30, 45, 46, [47, 49, 51, 53, 55, 57], 1, [0, 28, 48, 68, 88, 108]),
    (4002057, 30, 45, 46, [47, 49, 51, 53, 55, 57], 1, [0, 28, 48, 68, 88, 108]),
]


def ranges(data):
    return {k: (a, b) for k, a, b in inner_bnd(data[:u32(data, 4)])}


def quad(data, node, kind):
    a = 80+node*112
    require(data[a+85] == kind, 'Unexpected widget type')
    n, ptr = struct.unpack_from('<II', data, a+60)
    require(n == 4 and ptr+64 <= len(data), 'Unexpected quad')
    xs = [struct.unpack_from('<f', data, ptr+i*16)[0] for i in range(4)]
    return a, ptr, xs


def fit_panel(data, heading, labels, layers, frame, frame_groups, texts, font):
    require(u32(data, 4) == 514 and u32(data, 12) == 80, 'Layout format')
    out = bytearray(data)
    allowed = set()
    report = []

    def put(at, value):
        struct.pack_into('<f', out, at, value)
        allowed.update(range(at, at+4))

    for node in [heading]+labels:
        a, ptr, xs = quad(data, node, 10)
        tid = struct.unpack_from('<h', data, a+86)[0]
        text = texts[tid]
        width = max(measure_text(font, text))
        left = min(xs)
        box = 112 if node == heading else LABEL_WIDTH
        require(width+4 <= box and struct.unpack_from('<H', data, a+98)[0] > len(text), 'Text does not fit')
        # Preserve the former unscaled anchor, then use an actual full-width
        # column. No assumption that scale X changes the text renderer's pen.
        x, old_scale = struct.unpack_from('<f', data, a)[0], struct.unpack_from('<f', data, a+32)[0]
        put(a, x+left*(old_scale-1))
        put(a+32, 1)
        require(abs(xs[2]-xs[3]) < .001, 'Malformed right edge')
        for i in (2, 3):
            put(ptr+i*16, left+box)
        if node == heading:
            continue
        for bar in range(node+1, node+1+layers):
            ba, bp, bx = quad(data, bar, 3)
            require(abs(min(bx)) < .001 and 91 < max(bx) < 92, 'Unexpected gauge width')
            old_x = struct.unpack_from('<f', data, ba)[0]
            put(ba, old_x+BAR_SHIFT)
            ratio = (max(bx)-BAR_SHIFT)/max(bx)
            for i, value in enumerate(bx):
                put(bp+i*16, value*ratio)
            after_x = struct.unpack_from('<f', out, ba)[0]
            after_right = max(struct.unpack_from('<f', out, bp+i*16)[0] for i in range(4))
            require(abs(after_x+after_right-old_x-max(bx)) < .001, 'Gauge right edge moved')
            require(out[ba+84:ba+112] == data[ba+84:ba+112], 'Gauge binding changed')
        label_right = struct.unpack_from('<f', out, a)[0]+left+box
        bar_left = struct.unpack_from('<f', out, 80+(node+1)*112)[0]
        require(bar_left-label_right >= 6, 'Caption overlaps gauge')
        report.append(dict(node=node, text=text, text_width=width, box_width=box,
                           gap=bar_left-label_right, gauge_layers=layers))

    # Each gauge frame has 16 vertices (three ticks plus its baseline).
    # Compress those only; row separators, heading and panel border stay put.
    a = 80+frame*112
    require(data[a+85] == 1, 'Unexpected gauge frame widget')
    count, ptr = struct.unpack_from('<II', data, a+60)
    for start in frame_groups:
        require(start+16 <= count, 'Frame group out of bounds')
        offsets = [ptr+i*16 for i in range(start, start+16)]
        xs = [struct.unpack_from('<f', data, at)[0] for at in offsets]
        left, right = min(xs), max(xs)
        require(91 < right-left < 92, 'Unexpected frame width')
        for at, x in zip(offsets, xs):
            put(at, left+BAR_SHIFT+(x-left)*(right-left-BAR_SHIFT)/(right-left))
        require(abs(max(struct.unpack_from('<f', out, at)[0] for at in offsets)-right) < .001,
                'Frame right edge moved')

    require(all(i in allowed or x == y for i, (x, y) in enumerate(zip(data, out))), 'Unselected layout bytes changed')
    return bytes(out), report


def fit_counter(data):
    out = bytearray(data)
    a, ptr, _ = quad(data, 8, 10)
    donor, dp, xs = quad(data, 10, 10)
    require(struct.unpack_from('<h', data, a+86)[0] == 73, 'Wrong consecutive-sortie binding')
    # Reuse the unchanged Mood caption's horizontal cell geometry.
    out[a:a+4] = data[donor:donor+4]
    struct.pack_into('<f', out, a+32, 1)
    for i in range(4):
        out[ptr+i*16:ptr+i*16+4] = data[dp+i*16:dp+i*16+4]
    right = struct.unpack_from('<f', out, a)[0]+max(xs)
    require(right < 220 and right < struct.unpack_from('<f', data, 80+9*112)[0]-10, 'Counter collision')
    return bytes(out)


def plan():
    doc = json.loads(INPUT.read_text(encoding='utf-8'))
    edits, reports = [], []
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        for rid in (4002050, 4002053, 4002057):
            _, size, off, _ = next(e for e in entries if e[3] == rid)
            origin = fi['offset']+off
            f.seek(origin)
            bundle = f.read(size)
            p, locations = parts(bundle), ranges(bundle)
            rows = parse_table(p[3013])[3]
            texts = {tid: raw.decode('cp932') for _, tid, _, raw in rows}
            slot, tid, ptr, raw = next(row for row in rows if row[1] == 73)
            require(texts[73] == doc['counter']['before'], 'Counter text preimage')
            target = doc['counter']['target'].encode('cp932')
            require(len(target) <= len(raw) and max(measure_text(p[2500], doc['counter']['target'])) <= 65,
                    'Counter caption too long')
            require(all(s == slot or at+len(other)+1 <= ptr or at >= ptr+len(raw)+1
                        for s, _, at, other in rows), 'Aliased counter text')
            edits.append(dict(offset=origin+locations[3013][0]+ptr,
                              before=raw+b'\0', after=target+bytes(len(raw)+1-len(target))))
            for panel_rid, lid, frame, heading, nodes, layers, groups in PANELS:
                if panel_rid != rid:
                    continue
                start = locations[lid][0]+ranges(p[lid])[0][0]
                before = parts(p[lid])[0]
                after, rr = fit_panel(before, heading, nodes, layers, frame, groups, texts, p[2500])
                if rid == 4002053 and lid == 21:
                    after = fit_counter(after)
                edits.append(dict(offset=origin+start, before=before, after=after))
                reports.append(dict(bundle=rid, layout=lid, rows=rr))
    edits.sort(key=lambda e: e['offset'])
    require(len(edits) == 7 and all(len(e['before']) == len(e['after']) for e in edits), 'Edit coverage or extent')
    require(all(a['offset']+len(a['after']) <= b['offset'] for a, b in zip(edits, edits[1:])), 'Overlapping edits')
    return edits, dict(counter=doc['counter'], panels=reports, runtime_verified=False), None


if __name__ == '__main__':
    writer.VERSION, writer.BASE, writer.OUTPUT, writer.BASE_HASH = VERSION, BASE, OUTPUT, BASE_SHA
    writer.plan = plan
    writer.main()
