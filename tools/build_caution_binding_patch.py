"""0.9.15: split CAUTION glyphs from the frame's single-texture UI object."""
import argparse
import hashlib
import json
import struct
from build_ui_patch import ROOT, require, u32
from dialogue_corpus import archive
from build_flight_save_patch import parts
import build_dialogue_patch as builder

VERSION = '0.9.15'
BASE = ROOT/'work/output/ACE3-English-0.9.14.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_HASH = '9c7c7cd44ad0e01fa01303ab0049bdfea36b3e1e379e5625ca89a845e33caba6'
BUNDLES = (4002050, 4002054, 4002057)
FOLDER = ROOT/'work/ui/caution_0915'


def split_layout(data):
    require(u32(data, 0) == len(data) and u32(data, 4) == 514, 'Layout format')
    require((u32(data, 8), u32(data, 12)) == (8, 80), 'Node table preimage')
    nodes = bytearray(data[80:80+8*112])
    a = 2*112
    require(nodes[a+84:a+86] == b'\1\1', 'Frame mesh type')
    mc, mp = struct.unpack_from('<2I', nodes, a+52)
    require(mc == 2, 'Expected 0.9.13 two-material frame')
    require(struct.unpack_from('<3I', data, mp) == (0, 50101, 5), 'Frame material')
    require(struct.unpack_from('<3I', data, mp+16) == (0, 2000, 7), 'Font material')
    label = bytearray(nodes[a:a+112])
    # Keep the seven glyph strips and five frame strips in independent objects.
    struct.pack_into('<I', nodes, a+52, 1)
    struct.pack_into('<3I', label, 48, 8, 1, mp+16)
    nodes.extend(label)
    out = bytearray(data)
    new_table = len(out)
    out.extend(nodes)
    out.extend(bytes(-len(out) % 32))
    struct.pack_into('<I', out, 0, len(out))
    struct.pack_into('<2I', out, 8, 9, new_table)
    # Geometry is shared, not moved; all old pointers and index arrays stay valid.
    for i in range(8):
        before, after = data[80+i*112:80+(i+1)*112], nodes[i*112:(i+1)*112]
        allowed = set(range(52, 56)) if i == 2 else set()
        require(all(x == y or j in allowed for j, (x, y) in enumerate(zip(before, after))),
                'Unrelated node changed')
    require(out[16:len(data)] == data[16:], 'Original geometry changed')
    require(u32(out, new_table+8*112+56) == mp+16, 'Label first texture binding')
    return bytes(out)


def split_animation(data):
    require((u32(data, 0), u32(data, 4), u32(data, 8), u32(data, 12)) ==
            (len(data), 256, 7, 32), 'Animation preimage')
    require(struct.unpack_from('<6h', data, 64) == (0, 2, 1, 2, 3, 1), 'Frame animation record')
    require(u32(data, 64+12) == 96 and u32(data, 64+16) == 0, 'Frame graph links')
    table = bytearray(data[32:256])
    new_start = len(data)
    def relocate(ptr):
        if not ptr:
            return 0
        require(32 <= ptr < 256 and (ptr-32) % 32 == 0, 'Animation graph pointer')
        return new_start+ptr-32
    for i in range(7):
        for offset in (12, 16):
            struct.pack_into('<I', table, i*32+offset, relocate(u32(table, i*32+offset)))
    label = bytearray(table[32:64])
    struct.pack_into('<2h', label, 2, 8, 7)
    struct.pack_into('<2I', label, 12, 0, 0)
    # Same parent and motion data as the frame, preserving fade/entrance timing.
    struct.pack_into('<I', table, 32+16, new_start+7*32)
    table.extend(label)
    out = bytearray(data)
    out.extend(table)
    struct.pack_into('<I', out, 0, len(out))
    struct.pack_into('<2I', out, 8, 8, new_start)
    require(out[16:len(data)] == data[16:], 'Original animation data changed')
    require(u32(out, new_start+32+20) == u32(out, new_start+7*32+20), 'Motion data differs')
    seen = set()
    def visit(ptr):
        if not ptr:
            return
        require(ptr not in seen and new_start <= ptr < len(out) and (ptr-new_start) % 32 == 0,
                'Animation graph cycle/bad reference')
        seen.add(ptr)
        visit(u32(out, ptr+12))
        visit(u32(out, ptr+16))
    visit(new_start)
    require(len(seen) == 8, 'Unreachable animation object')
    return bytes(out)


def plan():
    changes, reports = {}, []
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        for rid in BUNDLES:
            _, size, offset, _ = next(e for e in entries if e[3] == rid)
            f.seek(fi['offset']+offset)
            source = f.read(size)
            p = parts(source)
            q = parts(p[35])
            layout, animation = split_layout(q[0]), split_animation(q[1])
            nested = builder.rebuild_bundle(p[35][:u32(p[35], 4)], {0: layout, 1: animation})
            result = builder.rebuild_bundle(source[:u32(source, 4)], {35: nested})
            rebuilt = parts(result)
            require(set(rebuilt) == set(p), 'Resource IDs changed')
            require(all(rebuilt[k] == v for k, v in p.items() if k != 35), 'Unrelated resource changed')
            check = parts(rebuilt[35])
            require(check[0] == layout and check[1] == animation, 'Layout/animation readback')
            require(all(check[k] == v for k, v in q.items() if k not in (0, 1)), 'Other animation changed')
            changes[rid] = result
            reports.append(dict(bundle=rid, layout=35, frame_node=2, label_node=8,
                                frame_texture=50101, label_texture=2000,
                                frame_strips=5, glyph_strips=7, animation_records=8,
                                original_layout_sha256=hashlib.sha256(q[0]).hexdigest(),
                                layout_sha256=hashlib.sha256(layout).hexdigest(),
                                geometry_and_font_unchanged=True))
    FOLDER.mkdir(parents=True, exist_ok=True)
    (FOLDER/'layout.json').write_text(json.dumps(dict(version=VERSION, changes=reports,
        runtime_verified=False), indent=2)+'\n', encoding='utf-8')
    return changes, reports


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    changes, reports = plan()
    print(json.dumps(dict(version=VERSION, bundles=list(changes), separate_label_node=8), indent=2), flush=True)
    if not args.write:
        return
    require(not OUTPUT.exists(), 'Output already exists')
    with BASE.open('rb') as f:
        require(builder.sha_region(f, 0, BASE.stat().st_size) == BASE_HASH, 'Base ISO hash')
    builder.VERSION, builder.BASE, builder.OUTPUT = VERSION, BASE, OUTPUT
    builder.build(changes, reports)
    path = OUTPUT.with_suffix('.json')
    report = json.loads(path.read_text(encoding='utf-8'))
    report.update(base_sha256=BASE_HASH,
        coverage='Separate CAUTION glyph object in all three memory-card panels. Preserve 0.9.14 cinematic alignment and prior fixes.',
        limitations='Resource/graph/disc verification passed; fresh-boot in-game label rendering and panel animation still need confirmation.')
    path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
