"""0.1.50: give full Game option captions an unscaled menu column.

Dry run by default. --write builds and verifies a new local test ISO.
"""
import struct
from build_ui_patch import ROOT, require, u32, inner_bnd
from build_flight_save_patch import parts
from dialogue_corpus import archive, parse_table
from ui_font import measure_text
import build_stats_panel_patch as writer

VERSION = '0.1.50'
BASE = ROOT/'work/output/ACE3-English-0.1.49.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_SHA = 'b9caa1cd0cef5e350d7393226ef3a26f1617cce05d61324f9ec90df103cfe15c'
LABELS = (3, 13, 21, 33, 41, 49, 57, 65, 73)
CHOICES = tuple(n for lo, hi in ((4, 11), (14, 19), (22, 31), (34, 39),
                               (42, 47), (50, 55), (58, 63), (66, 71), (74, 83))
                for n in range(lo, hi))
GROW = 24.0
VALUE_IDS = {120: 14, 121: 15, 122: 16, 140: 17,
             125: 21, 126: 22, 127: 23, 128: 24}
VALUE_IDS.update({binding: 18+(binding % 2 == 0)
                  for binding in (123, 124, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138)})


def ranges(data):
    return {k: (a, b) for k, a, b in inner_bnd(data[:u32(data, 4)])}


def geometry(data, node):
    a = 80+node*112
    count, ptr = struct.unpack_from('<II', data, a+60)
    require(count > 0 and ptr+count*16 <= len(data), 'Widget mesh bounds')
    return a, ptr, [struct.unpack_from('<f', data, ptr+i*16)[0] for i in range(count)]


def widen(data, rows, font, config=None):
    config = config or {}
    labels = config.get('labels', LABELS)
    choices = config.get('choices', CHOICES)
    grow = config.get('grow', GROW)
    box_width = config.get('box_width', 180)
    panel_node = config.get('panel_node', 22)
    value_ids = config.get('value_ids', VALUE_IDS)
    require(u32(data, 4) == 514 and u32(data, 12) == 80 and
            u32(data, 8) == config.get('count', 89), 'Options layout preimage')
    result = bytearray(data)
    touched, meshes = set(), set()

    def put(at, value):
        struct.pack_into('<f', result, at, value)
        touched.update(range(at, at+4))

    def mesh(node):
        a, ptr, xs = geometry(data, node)
        require(ptr not in meshes, 'Shared mesh needs explicit handling')
        meshes.add(ptr)
        return a, ptr, xs

    # Expand both the outer left panel and its nine normal/selected buttons.
    for node in [0]+[n for label in labels for n in (label-2, label-1)]:
        a, ptr, xs = mesh(node)
        require(data[a+85] == 1, 'Expected menu border/highlight')
        midpoint = (min(xs)+max(xs))/2
        for i, x in enumerate(xs):
            if x > midpoint:
                put(ptr+i*16, x+grow)

    label_reports = []
    for node in labels:
        a, ptr, xs = mesh(node)
        binding = struct.unpack_from('<h', data, a+86)[0]
        require(data[a+85] == 10 and binding in range(103, 112) and len(xs) == 4, 'Caption binding')
        text = rows[binding-98]
        width = max(measure_text(font, text))
        require(width+8 <= box_width, 'Caption exceeds new column')
        old_scale = struct.unpack_from('<f', data, a+32)[0]
        left = min(xs)
        x = struct.unpack_from('<f', data, a)[0]+left*(old_scale-1)
        put(a, x)
        put(a+32, 1)
        require(abs(xs[2]-xs[3]) < .001, 'Malformed caption quad')
        for i in (2, 3):
            put(ptr+i*16, left+box_width)
        ba, bp, bx = geometry(result, node-2)
        button_right = struct.unpack_from('<f', result, ba)[0]+max(bx)
        require(button_right-(x+left+box_width) > 4, 'Caption crosses button border')
        label_reports.append(dict(node=node, text=text, text_width=width,
                                  box_width=box_width, scale_x=1, border_gap=button_right-(x+left+box_width)))

    # Shorten the value area from its left edge, preserving its right edge.
    # Geometry changes directly; native text uses scale 1 and keeps its full
    # glyph size. Include alternate four-choice difficulty widgets.
    a, ptr, xs = geometry(data, panel_node)
    origin = struct.unpack_from('<f', data, a)[0]
    left, right = origin+min(xs), origin+max(xs)
    ratio = (right-left-grow)/(right-left)
    value_reports = []
    for node in choices:
        a, ptr, xs = mesh(node)
        old_x = struct.unpack_from('<f', data, a)[0]
        new_x = left+grow+(old_x-left)*ratio
        put(a, new_x)
        for i, x in enumerate(xs):
            put(ptr+i*16, x*ratio)
        if data[a+85] == 10:
            require(struct.unpack_from('<f', data, a+32)[0] == 1, 'Value text was scaled')
            binding = struct.unpack_from('<h', data, a+86)[0]
            text = rows[value_ids[binding]]
            width = max(measure_text(font, text))
            available = (max(xs)-min(xs))*ratio
            if config.get('expand_value_boxes') and available < width+8:
                # Keep the field's right edge fixed and provide full glyph
                # space on its left. Backgrounds and choice bindings stay put.
                require(len(xs) == 4 and abs(xs[0]-xs[1]) < .001, 'Value quad order')
                new_left = max(xs)*ratio-(width+8)
                for i in (0, 1):
                    put(ptr+i*16, new_left)
                available = width+8
            require(new_x+max(xs)*ratio <= right+.01, 'Value field crosses screen edge')
            require(width+4 <= available, 'Value text does not fit after column shift')
            value_reports.append(dict(node=node, text=text, text_width=width, available_width=available))
    require(all(i in touched or old == new for i, (old, new) in enumerate(zip(data, result))),
            'Unselected fields changed')
    # Verify serialized limits, including both quad edges and float rounding.
    for node in labels:
        a, ptr, xs = geometry(result, node)
        require(min(xs[2:])-max(xs[:2]) >= box_width-.01, 'Narrow caption edge')
        require(struct.unpack_from('<f', result, a+32)[0] == 1, 'Caption scaling remains')
        require(data[a+84:a+112] == result[a+84:a+112], 'Caption binding or capacity changed')
    a, ptr, xs = geometry(result, panel_node)
    new_x = struct.unpack_from('<f', result, a)[0]
    require(abs(new_x+max(xs)-right) < .001, 'Choice panel right edge moved')
    require(abs(new_x+min(xs)-left-grow) < .001, 'Choice panel left edge wrong')
    return bytes(result), dict(captions=label_reports, values=value_reports,
                              column_growth=grow, value_width_ratio=ratio)


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
            require(rows[7] == 'Lock-On Priority', 'Missing requested English caption')
            before = parts(p[42])[0]
            after, report = widen(before, rows, p[2500])
            offset = origin+ranges(bundle)[42][0]+ranges(p[42])[0][0]
            edits.append(dict(offset=offset, before=before, after=after))
            reports.append(dict(bundle=rid, layout=42, **report))
    require(all(len(e['before']) == len(e['after']) for e in edits), 'Layout extent changed')
    return edits, dict(panels=reports, runtime_verified=False), None


if __name__ == '__main__':
    writer.VERSION, writer.BASE, writer.OUTPUT, writer.BASE_HASH = VERSION, BASE, OUTPUT, BASE_SHA
    writer.plan = plan
    writer.main()
