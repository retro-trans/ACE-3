"""0.9.19: separate Game option captions, values and separator arrows."""
import json
import struct
from build_game_column_patch import geometry, ranges, LABELS, VALUE_IDS
from build_ui_patch import ROOT, require, u32
from build_flight_save_patch import parts
from dialogue_corpus import archive, parse_table
from ui_font import measure_text
import build_stats_panel_patch as writer

VERSION = '0.9.19'
BASE = ROOT/'work/output/ACE3-English-0.9.18.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_HASH = '8d50f482879a460e8c2a5344f40693394cb53c75a5fd475a575165c487245314'
FOLDER = ROOT/'work/ui/game_spacing_0919'
PANELS = (4, 14, 22, 34, 42, 50, 58, 66, 74)
GROW = 10.0
GAP = 20.0


def space_layout(before, rows, font):
    require(u32(before, 4) == 514 and u32(before, 8) == 89, 'Unexpected Game layout')
    after = bytearray(before)
    allowed = set()

    def put(at, value):
        struct.pack_into('<f', after, at, value)
        allowed.update(range(at, at+4))

    def bounds(node):
        a, ptr, xs = geometry(after, node)
        origin = struct.unpack_from('<f', after, a)[0]
        return min(xs)+origin, max(xs)+origin

    def remap(node, indices, left, right):
        a, ptr, xs = geometry(before, node)
        origin = struct.unpack_from('<f', before, a)[0]
        lo, hi = min(xs[i] for i in indices), max(xs[i] for i in indices)
        require(hi > lo, 'Degenerate mesh strip')
        for i in indices:
            put(ptr+i*16, left-origin+(xs[i]-lo)*(right-left)/(hi-lo))

    # Widen the caption frames, including their selected variants. Retain
    # caption position, full-size glyphs and all interaction/animation fields.
    for node in [0]+[n for label in LABELS for n in (label-2, label-1)]:
        a, ptr, xs = geometry(before, node)
        require(before[a+85] == 1, 'Expected caption frame')
        midpoint = (min(xs)+max(xs))/2
        for i, x in enumerate(xs):
            if x > midpoint:
                put(ptr+i*16, x+GROW)

    reports = []
    for panel in PANELS:
        a, ptr, xs = geometry(before, panel)
        origin = struct.unpack_from('<f', before, a)[0]
        require(len(xs) in (16, 20, 24), 'Unexpected separator mesh')
        count = (len(xs)-12)//4+1
        # Vertices 0..7 are the panel border; 8..11 the connector dash;
        # remaining groups of four are separator arrows, sometimes unordered.
        for i in (0, 1, 2, 3, 8, 9, 10, 11):
            put(ptr+i*16, xs[i]+GROW)
        left = origin+min(xs[:4])+GROW+3.5
        right = origin+max(xs[4:8])-3.5
        text_nodes = [panel+2+2*i for i in range(count)]
        widths, texts = [], []
        for node in text_nodes:
            ta, tp, tx = geometry(before, node)
            require(before[ta+85] == 10 and len(tx) == 4, 'Expected choice text quad')
            require(struct.unpack_from('<f', before, ta+32)[0] == 1, 'Scaled choice text')
            binding = struct.unpack_from('<h', before, ta+86)[0]
            text = rows[VALUE_IDS[binding]]
            texts.append(text)
            widths.append(max(measure_text(font, text)))
        padding = (right-left-GAP*(count-1)-sum(widths))/count
        require(padding >= 5, 'Insufficient full-size choice padding')
        cells, cursor = [], left
        for node, width in zip(text_nodes, widths):
            end = cursor+width+padding
            remap(node, range(4), cursor, end)
            remap(node-1, range(4), cursor, end)
            cells.append((cursor, end))
            cursor = end+GAP
        require(abs(cells[-1][1]-right) < .001, 'Choice right edge moved')
        arrows = sorted((list(range(i, i+4)) for i in range(12, len(xs), 4)),
                        key=lambda ids: min(xs[i] for i in ids))
        arrow_reports = []
        for i, ids in enumerate(arrows):
            width = max(xs[j] for j in ids)-min(xs[j] for j in ids)
            require(width < GAP, 'Arrow wider than separator space')
            start = cells[i][1]+(GAP-width)/2
            remap(panel, ids, start, start+width)
            gap = (GAP-width+padding)/2
            require(gap >= 6, 'Text touches separator arrow')
            arrow_reports.append(dict(left=start, right=start+width, text_gap=gap))
        for node, cell in zip(text_nodes, cells):
            actual = bounds(node)
            require(all(abs(x-y) < .001 for x, y in zip(actual, cell)), 'Serialized choice bounds')
            require(all(abs(x-y) < .001 for x, y in zip(bounds(node-1), cell)), 'Highlight mismatch')
        reports.append(dict(panel=panel, texts=texts, widths=widths, cells=cells,
                            cell_padding=padding, arrows=arrow_reports))
    # The longest caption ends well before the relocated connector dash.
    caption_reports = []
    for node, panel in zip(LABELS[:8], PANELS[:8]):
        a, _, _ = geometry(before, node)
        binding = struct.unpack_from('<h', before, a+86)[0]
        text = rows[binding-98]
        text_right = bounds(node)[0]+max(measure_text(font, text))
        pa, pp, px = geometry(after, panel)
        dash_left = struct.unpack_from('<f', after, pa)[0]+min(px[8:12])
        require(dash_left-text_right >= 28, 'Caption touches connector')
        caption_reports.append(dict(text=text, connector_gap=dash_left-text_right))
    require(len(after) == len(before), 'Layout size changed')
    require(all(x == y or i in allowed for i, (x, y) in enumerate(zip(before, after))),
            'Non-coordinate data changed')
    for node in range(89):
        a = 80+node*112
        require(after[a:a+112] == before[a:a+112], 'Widget attributes changed')
    return bytes(after), dict(column_growth=GROW, captions=caption_reports, panels=reports,
                             fonts_and_strings_unchanged=True, runtime_verified=False)


def plan():
    edits, reports = [], []
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        for rid in (4002050, 4002054, 4002057):
            _, size, off, _ = next(e for e in entries if e[3] == rid)
            origin = fi['offset']+off
            f.seek(origin)
            bundle = f.read(size)
            p = parts(bundle)
            rows = {tid: raw.decode('cp932') for _, tid, _, raw in parse_table(p[3070])[3]}
            before = parts(p[42])[0]
            after, report = space_layout(before, rows, p[2500])
            edits.append(dict(offset=origin+ranges(bundle)[42][0]+ranges(p[42])[0][0],
                              before=before, after=after))
            reports.append(dict(bundle=rid, layout=42, **report))
    edits.sort(key=lambda e: e['offset'])
    require(all(a['offset']+len(a['after']) <= b['offset'] for a, b in zip(edits, edits[1:])),
            'Overlapping edits')
    summary = dict(version=VERSION, menus=reports, runtime_verified=False)
    FOLDER.mkdir(parents=True, exist_ok=True)
    (FOLDER/'layout.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    return edits, summary, None


if __name__ == '__main__':
    writer.VERSION, writer.BASE, writer.OUTPUT, writer.BASE_HASH = VERSION, BASE, OUTPUT, BASE_HASH
    writer.plan = plan
    writer.main()
