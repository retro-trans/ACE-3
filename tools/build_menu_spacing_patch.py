"""0.1.52: separate Controls choices and widen Intermission buttons.

Dry run by default; --write builds and byte-verifies a local test ISO.
"""
import struct
from build_game_column_patch import ROOT, ranges, geometry, parts, archive, parse_table, require, measure_text
import build_stats_panel_patch as writer

VERSION = '0.1.52'
BASE = ROOT/'work/output/ACE3-English-0.1.51.iso'
REFERENCE = ROOT/'work/output/ACE3-English-0.1.50.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_SHA = '3660248c74beed04f64e1dcffd5e70f7ddffdcee42ec146931a6a31b2bb3cb19'
LEFT, RIGHT, ARROW_GAP = -84.0, 316.0, 14.0
ROWS = [
    (4, [(5, 6, 14), (7, 8, 15)]),
    (12, [(13, 14, 17), (15, 16, 18), (17, 18, 19), (19, 20, 20)]),
    (24, [(25, 26, 22), (27, 28, 23)]),
    (32, [(33, 34, 25), (35, 36, 26), (37, 38, 27)]),
    (42, [(43, 44, 29), (45, 46, 30)]),
]


def controls(data, reference, texts, font):
    out = bytearray(data)
    allowed = set()
    reports = []

    def put(at, value):
        struct.pack_into('<f', out, at, value)
        allowed.update(range(at, at+4))

    def original_anchor(node):
        a, ptr, xs = geometry(data, node)
        origin = struct.unpack_from('<f', reference, a)[0]
        # The screenshot shows the old origins surviving in-game. Bake the
        # desired placement into vertices and keep original widget origins.
        put(a, origin)
        return a, ptr, xs, origin

    def place_vertices(ptr, indices, origin, lo, hi):
        xs = [struct.unpack_from('<f', data, ptr+i*16)[0] for i in indices]
        x0, x1 = min(xs), max(xs)
        require(x1 > x0, 'Degenerate rectangle')
        for i, x in zip(indices, xs):
            put(ptr+i*16, lo+(x-x0)*(hi-lo)/(x1-x0)-origin)

    def place_quad(node, lo, hi, kind):
        a, ptr, xs, origin = original_anchor(node)
        require(data[a+85] == kind and len(xs) == 4, 'Choice widget shape')
        place_vertices(ptr, range(4), origin, lo, hi)
        return a, ptr, origin

    for frame, choices in ROWS:
        widths = [max(measure_text(font, texts[tid])) for _, _, tid in choices]
        minimum = sum(w+6 for w in widths)+ARROW_GAP*(len(choices)-1)
        spare = RIGHT-LEFT-4-minimum
        require(spare >= -.001, 'Choices exceed the screen width')
        extra = max(0, spare)/len(choices)
        slots, cursor, gaps = [], LEFT+2, []
        for i, ((highlight, label, tid), width) in enumerate(zip(choices, widths)):
            end = cursor+width+6+extra
            place_quad(highlight, cursor+1, end-1, 1)
            a, ptr, origin = place_quad(label, cursor, end, 10)
            xs = [struct.unpack_from('<f', out, ptr+j*16)[0]+origin for j in range(4)]
            require(min(xs) >= LEFT and max(xs) <= RIGHT and max(xs)-min(xs) >= width+5.99,
                    'Choice text does not fit')
            slots.append(dict(text=texts[tid], node=label, text_width=width, left=cursor, right=end))
            if i < len(choices)-1:
                gaps.append((end, end+ARROW_GAP))
            cursor = end+ARROW_GAP
        require(abs(slots[-1]['right']-(RIGHT-2)) < .001, 'Row extent mismatch')
        a, ptr, xs, origin = original_anchor(frame)
        require(data[a+85] == 1 and len(xs) == 12+4*len(gaps), 'Unexpected frame/arrows')
        place_vertices(ptr, range(0, 4), origin, LEFT, LEFT+3)
        place_vertices(ptr, range(4, 8), origin, RIGHT-3, RIGHT)
        # Horizontal connector ends at the widened caption button.
        label_node = frame-1
        ba, bp, bx = geometry(data, label_node-2)
        button_right = struct.unpack_from('<f', data, ba)[0]+max(bx)
        require(LEFT-button_right >= 10, 'Columns touch')
        place_vertices(ptr, range(8, 12), origin, button_right, LEFT+1)
        # Arrow meshes are not stored in visual left-to-right order.
        groups = sorted(range(12, len(xs), 4), key=lambda s: min(xs[s:s+4]))
        for start, (lo, hi) in zip(groups, gaps):
            place_vertices(ptr, range(start, start+4), origin, lo, hi)
        reports.append(dict(frame=frame, column_gap=LEFT-button_right, slots=slots, arrow_gaps=gaps))
    require(all(i in allowed or a == b for i, (a, b) in enumerate(zip(data, out))), 'Unrelated Controls bytes changed')
    for node in range(struct.unpack_from('<I', data, 8)[0]):
        a = 80+node*112
        require(out[a+84:a+112] == data[a+84:a+112], 'Controls binding/flags changed')
    return bytes(out), reports


def intermission(data, font, texts):
    out = bytearray(data)
    require(struct.unpack_from('<I', data, 8)[0] == 36, 'Intermission layout changed')
    allowed = set()
    for node in [0]+[n for label in range(3, 28, 3) for n in (label-2, label-1)]:
        a, ptr, xs = geometry(data, node)
        require(data[a+85] == 1, 'Intermission border type')
        middle = (min(xs)+max(xs))/2
        for i, x in enumerate(xs):
            if x > middle:
                struct.pack_into('<f', out, ptr+i*16, x+32)
                allowed.update(range(ptr+i*16, ptr+i*16+4))
    # Check the complete Combat Records text against both button states,
    # retaining room for the selected-row marker near the right edge.
    label = 15
    a, ptr, xs = geometry(data, label)
    require(struct.unpack_from('<h', data, a+86)[0] == 114 and texts[24] == 'Combat Records', 'Combat Records binding')
    text_right = struct.unpack_from('<f', data, a)[0]+min(xs)+max(measure_text(font, texts[24]))
    clearances = []
    for node in (13, 14):
        ba, bp, bx = geometry(out, node)
        gap = struct.unpack_from('<f', out, ba)[0]+max(bx)-text_right
        require(gap > 20, 'Combat Records lacks marker space')
        clearances.append(gap)
    require(all(i in allowed or a == b for i, (a, b) in enumerate(zip(data, out))), 'Unrelated Intermission bytes changed')
    return bytes(out), dict(button_growth=32, rows=9, combat_records_clearance=clearances)


def plan():
    edits, reports = [], []
    with BASE.open('rb') as f, REFERENCE.open('rb') as ref:
        fi, entries = archive(f)
        rfi, res = archive(ref)
        for rid in (4002050, 4002054, 4002057):
            _, size, off, _ = next(e for e in entries if e[3] == rid)
            f.seek(fi['offset']+off)
            bundle = f.read(size)
            p = parts(bundle)
            _, rsize, roff, _ = next(e for e in res if e[3] == rid)
            ref.seek(rfi['offset']+roff)
            rp = parts(ref.read(rsize))
            for lid, tid in [(43, 3071)]+([(13, 3004)] if rid != 4002054 else []):
                texts = {i: raw.decode('cp932') for _, i, _, raw in parse_table(p[tid])[3]}
                before = parts(p[lid])[0]
                if lid == 43:
                    after, report = controls(before, parts(rp[lid])[0], texts, p[2500])
                else:
                    after, report = intermission(before, p[2500], texts)
                require(len(before) == len(after), 'Layout extent changed')
                edits.append(dict(offset=fi['offset']+off+ranges(bundle)[lid][0]+ranges(p[lid])[0][0],
                                  before=before, after=after))
                reports.append(dict(bundle=rid, layout=lid, details=report))
    edits.sort(key=lambda e: e['offset'])
    require(len(edits) == 5 and all(a['offset']+len(a['after']) <= b['offset'] for a, b in zip(edits, edits[1:])),
            'Layout coverage/overlap')
    return edits, dict(panels=reports, runtime_verified=False), None


if __name__ == '__main__':
    writer.VERSION, writer.BASE, writer.OUTPUT, writer.BASE_HASH = VERSION, BASE, OUTPUT, BASE_SHA
    writer.plan = plan
    writer.main()
