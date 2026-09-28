"""0.1.48: repair the incomplete Lock-On Priority text quad.

Dry run by default; --write creates a local test image and verifies every byte.
The previous builder compared float coordinates exactly and widened only the
bottom-right vertex. The top-right vertex remained narrower than the text.
"""
import argparse
import hashlib
import json
import shutil
import struct
from build_ui_patch import ROOT, require, u32, inner_bnd
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts
from ui_font import measure_text

VERSION = '0.1.48'
BASE = ROOT/'work/output/ACE3-English-0.1.47.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_SHA = '77fa368be1d5e287ebf6a560c363bdadc85f4d2a3c8672ca23b91ce22b8c12df'
BUNDLES = (4002050, 4002054, 4002057)


def edge_widths(data, ptr):
    vertices = [struct.unpack_from('<2f', data, ptr+i*16) for i in range(4)]
    left, right = vertices[:2], vertices[2:]
    require(abs(left[0][0]-left[1][0]) < .001, 'Unexpected left edge')
    require(all(abs(a[1]-b[1]) < .001 for a, b in zip(left, right)), 'Unexpected vertex order')
    return [b[0]-a[0] for a, b in zip(left, right)]


def repair_quad(data, ptr, text_width):
    widths = edge_widths(data, ptr)
    require(widths[0] < text_width and abs(widths[1]-(text_width+8)) < .001,
            'Expected the partially widened 0.1.44 quad')
    out = bytearray(data)
    # Copy the widened bottom-right X to the top-right X. Other coordinates,
    # text binding, capacity, scale and all neighboring nodes remain intact.
    out[ptr+32:ptr+36] = data[ptr+48:ptr+52]
    require(min(edge_widths(out, ptr)) >= text_width+7.99, 'Incomplete text box')
    return bytes(out)


def plan():
    edits, checks = [], []
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        for rid in BUNDLES:
            _, size, off, _ = next(e for e in entries if e[3] == rid)
            origin = fi['offset']+off
            f.seek(origin)
            bundle = f.read(size)
            p = parts(bundle)
            label = next(raw.decode('cp932') for _, tid, _, raw in parse_table(p[3070])[3] if tid == 7)
            require(label == 'Lock-On Priority', 'Label preimage changed')
            width = max(measure_text(p[2500], label))
            d = parts(p[42])[0]
            a = 80+21*112
            require(u32(d, 4) == 514 and u32(d, 12) == 80 and d[a+85] == 10, 'Layout format')
            require(struct.unpack_from('<h', d, a+86)[0] == 105, 'Wrong text binding')
            n, ptr = struct.unpack_from('<II', d, a+60)
            require(n == 4 and ptr+64 <= len(d), 'Text quad bounds')
            scale = struct.unpack_from('<f', d, a+32)[0]
            require(abs(scale-140/(width+8)) < .00001, 'Unexpected label scale')
            fixed = repair_quad(d, ptr, width)
            require(max(edge_widths(fixed, ptr))*scale <= 140.001, 'Text box exceeds row')
            layout_start = next(start for k, start, _ in inner_bnd(bundle[:u32(bundle, 4)]) if k == 42)
            part_start = next(start for k, start, _ in inner_bnd(p[42][:u32(p[42], 4)]) if k == 0)
            start = ptr+32
            require(fixed[:start] == d[:start] and fixed[start+4:] == d[start+4:], 'Unrelated bytes changed')
            edits.append(dict(offset=origin+layout_start+part_start+start,
                              before=d[start:start+4], after=fixed[start:start+4]))
            checks.append(dict(bundle=rid, layout=42, node=21, label=label, text_width=width,
                               edge_widths_before=edge_widths(d, ptr), edge_widths_after=edge_widths(fixed, ptr),
                               scale_x=scale, displayed_text_width=width*scale))
    require(len(edits) == 3, 'Missing menu copies')
    return edits, checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    edits, checks = plan()
    print('DRY RUN', json.dumps(checks, indent=2), flush=True)
    if not args.write:
        return
    require(not OUTPUT.exists(), 'Output already exists')
    shutil.copyfile(BASE, OUTPUT)
    with OUTPUT.open('r+b') as f:
        for edit in edits:
            f.seek(edit['offset'])
            require(f.read(4) == edit['before'], 'Disc preimage mismatch')
            f.seek(edit['offset'])
            f.write(edit['after'])
    source_sha, output_sha = hashlib.sha256(), hashlib.sha256()
    position = 0
    with BASE.open('rb') as source, OUTPUT.open('rb') as output:
        while True:
            raw = source.read(8 << 20)
            if not raw:
                break
            expected = bytearray(raw)
            for edit in edits:
                lo, hi = max(position, edit['offset']), min(position+len(raw), edit['offset']+4)
                if lo < hi:
                    expected[lo-position:hi-position] = edit['after'][lo-edit['offset']:hi-edit['offset']]
            actual = output.read(len(raw))
            require(actual == expected, 'Unexpected disc byte change')
            source_sha.update(raw)
            output_sha.update(actual)
            position += len(raw)
        require(not output.read(1), 'Output size changed')
    require(source_sha.hexdigest() == BASE_SHA, 'Wrong base image')
    report = dict(version=VERSION, base_sha256=source_sha.hexdigest(), sha256=output_sha.hexdigest(),
                  size=position, whole_disc_verified=True, runtime_verified=False, checks=checks)
    OUTPUT.with_suffix('.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('VERIFIED', OUTPUT, report['sha256'], flush=True)


if __name__ == '__main__':
    main()
