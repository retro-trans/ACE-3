"""0.1.43: fit deployment/upgrade stats and translate the baked sortie label.

Read-only dry run by default. --preview writes local artwork; --write creates
a new test ISO and verifies its entire byte delta. No executable edits.
"""
import argparse
from collections import Counter
import hashlib
import json
import shutil
import struct
from PIL import Image
from build_ui_patch import ROOT, require, u32, inner_bnd
from build_flight_save_patch import parts
from build_controller_patch import NativeGlyphs
from dialogue_corpus import archive, parse_table
from ui_font import measure_text
from ui_textures import decode

VERSION = '0.1.43'
BASE = ROOT / 'work/output/ACE3-English-0.1.42.iso'
OUTPUT = ROOT / ('work/output/ACE3-English-' + VERSION + '.iso')
BASE_HASH = '0ccdd0680135bb3138c1248f81fcad35450af892c9f1b09b8a4e486637572f5e'
TEXTURE_HASH = 'd5e853c9da2f7c37885d812b1ed7c47a6a07d8eeb9c343d35647d25f56a4568e'
LAYOUT = ROOT / 'work/ui/stats_043/layout.json'
TRANSLATION = ROOT / 'work/translation/en/stats_043.json'


def ranges(data):
    return {k: (a, b) for k, a, b in inner_bnd(data[:u32(data, 4)])}


def paint_label(original, glyphs, text, rect):
    require(hashlib.sha256(original).hexdigest() == TEXTURE_HASH, 'Texture preimage')
    require(u32(original, 4) == 128 * 128, 'Expected linear 128x128 indexed texture')
    palette = original[32 + 128 * 128:]
    require(len(palette) == 1024, 'Unexpected palette')
    colors = []
    for i in range(256):
        j = (i & ~24) | ((i & 8) << 1) | ((i & 16) >> 1)
        r, g, b, a = palette[j * 4:j * 4 + 4]
        colors.append((r, g, b, min(255, a * 2)))
    x, y, w, h = rect
    require(0 <= x < x+w <= 128 and 0 <= y < y+h <= 128, 'Caption bounds')
    positions = [yy * 128 + xx for yy in range(y, y+h) for xx in range(x, x+w)]
    pixels = bytearray(original[32:32 + 128 * 128])
    bg = Counter(pixels[i] for i in positions).most_common(1)[0][0]
    label = glyphs.render(text)
    height = min(14, h-2)
    width = min(w-2, round(label.width * height / label.height))
    label = label.resize((width, height), Image.Resampling.LANCZOS)
    patch = Image.new('RGBA', (w, h), colors[bg])
    patch.alpha_composite(label, ((w-width)//2, (h-height)//2))
    cache = {}
    for pos, color in zip(positions, patch.getdata()):
        if color not in cache:
            cache[color] = min(range(256), key=lambda j: sum((a-b)**2 for a, b in zip(color, colors[j])))
        pixels[pos] = cache[color]
    allowed = set(positions)
    require(all(i in allowed or a == b for i, (a, b) in enumerate(zip(original[32:32+16384], pixels))),
            'Pixels outside label changed')
    result = original[:32] + bytes(pixels) + palette
    require(len(result) == len(original), 'Texture size changed')
    return result


def fit_layout(data, specs, texts, font):
    require(u32(data, 4) == 0x202 and u32(data, 12) == 80, 'Layout format')
    result = bytearray(data)
    report = []
    touched = set()
    for spec in specs:
        node, tid, limit = spec['node'], spec['text_id'], spec['width']
        a = 80 + node * 112
        require(node < u32(data, 8) and data[a+85] == 10, 'Text widget type')
        require(struct.unpack_from('<h', data, a+86)[0] == tid, 'Text widget binding')
        require(struct.unpack_from('<4f', data, a+32) == (1, 1, 1, 1), 'Scale preimage')
        text = texts[tid]
        require(struct.unpack_from('<H', data, a+98)[0] >= len(text)+1, 'Glyph capacity')
        width = max(measure_text(font, text))
        count, ptr = struct.unpack_from('<II', data, a+60)
        require(count == 4 and ptr + count*16 <= len(data), 'Text quad')
        xs = [struct.unpack_from('<f', data, ptr+i*16)[0] for i in range(count)]
        left, right = min(xs), max(xs)
        # Give the unscaled text a complete local line before fitting its
        # displayed quad. Scaling alone may leave the old wrap width intact.
        local_width = max(right-left, width+4)
        scale = min(1.0, limit/local_width)
        def put(offset, value):
            struct.pack_into('<f', result, offset, value)
            touched.update(range(offset, offset+4))
        for i, x in enumerate(xs):
            if x == right:
                put(ptr+i*16, left+local_width)
        put(a+32, scale)
        x, y = struct.unpack_from('<2f', data, a)
        put(a, x + left*(1-scale))
        put(a+4, y + spec.get('dy', 0))
        require(width*scale <= limit + .001, 'Text exceeds display width')
        report.append(dict(node=node, text_id=tid, text=text, unscaled_width=width,
                           local_width=local_width, scale_x=scale, display_limit=limit,
                           y_shift=spec.get('dy', 0)))
    require(all(i in touched or a == b for i, (a, b) in enumerate(zip(data, result))), 'Unrelated layout bytes')
    return bytes(result), report


def plan():
    layout = json.loads(LAYOUT.read_text(encoding='utf-8'))
    translation = json.loads(TRANSLATION.read_text(encoding='utf-8'))
    changes, reports = [], []
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        bundles = {}
        for e in entries:
            if 4002050 <= e[3] <= 4002058:
                origin = fi['offset'] + e[2]
                f.seek(origin)
                bundles[e[3]] = (origin, f.read(e[1]))
        donor = parts(bundles[4002053][1])
        glyphs = NativeGlyphs(donor[2500], donor[2000])
        patched_texture = paint_label(donor[50101], glyphs, translation['player_sorties']['target'], layout['texture_rectangle'])
        texture_copies = []
        for rid, (origin, data) in bundles.items():
            resources = ranges(data)
            if 50101 not in resources:
                continue
            a, b = resources[50101]
            if hashlib.sha256(data[a:b]).hexdigest() == TEXTURE_HASH:
                changes.append(dict(offset=origin+a, before=data[a:b], after=patched_texture))
                texture_copies.append(rid)
        require(texture_copies == layout['texture_bundles'], 'Texture coverage changed')
        for panel in layout['panels']:
            rid, lid = panel['bundle'], panel['layout']
            origin, data = bundles[rid]
            p = parts(data)
            texts = {tid: raw.decode('cp932') for _, tid, _, raw in parse_table(p[3013])[3]}
            for spec in panel['labels']:
                require(texts[spec['text_id']] == translation['existing_labels'][str(spec['text_id'])], 'English text preimage')
            a, b = ranges(data)[lid]
            start, end = ranges(data[a:b])[0]
            before = data[a+start:a+end]
            after, report = fit_layout(before, panel['labels'], texts, p[2500])
            changes.append(dict(offset=origin+a+start, before=before, after=after))
            reports.append(dict(bundle=rid, layout=lid, labels=report))
    changes.sort(key=lambda c: c['offset'])
    require(all(len(c['before']) == len(c['after']) for c in changes), 'Extent change')
    require(all(a['offset']+len(a['after']) <= b['offset'] for a, b in zip(changes, changes[1:])), 'Overlapping edits')
    return changes, dict(texture_bundles=texture_copies, panels=reports), patched_texture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    changes, summary, texture = plan()
    print('DRY RUN:', len(changes), 'fixed-size resources', flush=True)
    print(json.dumps(summary, indent=2), flush=True)
    if args.preview:
        folder = ROOT/'work/ui/stats_043/preview'
        folder.mkdir(parents=True, exist_ok=True)
        im = decode(texture)
        bg = Image.new('RGBA', im.size, (15, 25, 38, 255))
        bg.alpha_composite(im)
        bg.resize((512, 512), Image.Resampling.NEAREST).save(folder/'sorties.png')
    if not args.write:
        return
    require(not OUTPUT.exists(), 'Output already exists')
    shutil.copyfile(BASE, OUTPUT)
    with OUTPUT.open('r+b') as f:
        for c in changes:
            f.seek(c['offset'])
            require(f.read(len(c['before'])) == c['before'], 'Patch preimage')
            f.seek(c['offset'])
            f.write(c['after'])
    src_hash, dst_hash = hashlib.sha256(), hashlib.sha256()
    pos = 0
    with BASE.open('rb') as src, OUTPUT.open('rb') as dst:
        while True:
            raw = src.read(8 << 20)
            if not raw:
                break
            expected = bytearray(raw)
            for c in changes:
                lo, hi = max(pos, c['offset']), min(pos+len(raw), c['offset']+len(c['after']))
                if lo < hi:
                    expected[lo-pos:hi-pos] = c['after'][lo-c['offset']:hi-c['offset']]
            actual = dst.read(len(raw))
            require(actual == expected, 'Unexpected disc byte change')
            src_hash.update(raw)
            dst_hash.update(actual)
            pos += len(raw)
        require(not dst.read(1), 'Disc size changed')
    require(src_hash.hexdigest() == BASE_HASH, 'Unexpected base ISO hash')
    report = dict(version=VERSION, base_sha256=src_hash.hexdigest(), sha256=dst_hash.hexdigest(),
                  size=pos, whole_disc_verified=True, runtime_verified=False, summary=summary)
    OUTPUT.with_suffix('.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('BUILT', OUTPUT, dst_hash.hexdigest(), flush=True)


if __name__ == '__main__':
    main()
