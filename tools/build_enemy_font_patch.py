"""0.9.2: complete the separate lock-on HUD font in eight gameplay bundles.

Dry run by default; --preview writes a font proof; --write builds a test ISO.
"""
import argparse
import hashlib
import json
import struct
from PIL import Image, ImageDraw
from build_ui_patch import ROOT, require, u32
from build_flight_save_patch import parts
from dialogue_corpus import archive
from dialogue_font import complete_font
from ui_font import font_map, patch_font, measure_text
from ui_textures import decode
import build_dialogue_patch as builder

VERSION = '0.9.2'
BASE = ROOT/'work/output/ACE3-English-0.9.1.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_HASH = '33d39e60222049b212e0f346aca02d48e26892df36718947caf39775bf9514b0'
BUNDLES = tuple(range(1200000, 1200008))
PROOF = ROOT/'work/ui/enemy_font_092'


def repair(font, texture, donor_font, donor_texture):
    tex0 = struct.unpack_from('<Q', texture, 16)[0]
    require((tex0 >> 20) & 63 == 44, 'Expected HUD PSMT4HH texture')
    require(u32(texture, 12) == 0 and u32(texture, 4) == 32768, 'Expected linear HUD atlas')
    require((1 << ((tex0 >> 26) & 15), 1 << ((tex0 >> 30) & 15)) == (256, 256), 'HUD dimensions')
    mapping, start, count = font_map(font)
    simulated = ''.join(c if ord(c) in mapping else '?' for c in 'Monsuno type10')
    require(simulated == '???s??? ????10', 'Reported missing-letter signature changed')
    # Both linear formats store two palette indices per byte. The helper's
    # PSMT4 view is only for CPU packing; restore the original GPU header.
    view = bytearray(texture)
    struct.pack_into('<Q', view, 16, (tex0 & ~(63 << 20)) | (20 << 20))
    new_font, packed, report = complete_font(font, bytes(view), patch_font(donor_font)[0], donor_texture)
    new_texture = texture[:32]+packed[32:]
    require(len(new_texture) == len(texture) and new_texture[-64:] == texture[-64:], 'HUD atlas/palette changed size')
    result, new_start, new_count = font_map(new_font)
    require(all(c in result for c in range(32, 127)), 'ASCII coverage incomplete')
    require(all(result[c] == i for c, i in mapping.items()), 'Existing lookup changed')
    require(new_font[new_start:new_start+count*24] == font[start:start+count*24], 'Existing glyph UVs/metrics changed')
    before, after = decode(texture), decode(new_texture)
    for index in range(count):
        box = tuple(round(v*256) for v in struct.unpack_from('<4f', font, start+index*24))
        require(before.crop(box).tobytes() == after.crop(box).tobytes(), 'Existing glyph image changed')
    report.update(original_glyphs=count, resulting_glyphs=new_count, ascii_complete=True,
                  atlas_dimensions=[256, 256], gpu_header_preserved=True,
                  example='Monsuno type10', previous_render=simulated,
                  example_width=measure_text(new_font, 'Monsuno type10')[0])
    return new_font, new_texture, report


def plan():
    changes, reports, cache = {}, [], {}
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        def get(rid):
            e = next(e for e in entries if e[3] == rid)
            f.seek(fi['offset']+e[2])
            return f.read(e[1])
        donor_font, donor_texture = get(35), get(36)
        for rid in BUNDLES:
            data = get(rid)
            p = parts(data)
            key = hashlib.sha256(p[2501]+p[2001]).hexdigest()
            if key not in cache:
                cache[key] = repair(p[2501], p[2001], donor_font, donor_texture)
            font, texture, report = cache[key]
            changes[rid] = builder.rebuild_bundle(data, {2501: font, 2001: texture})
            reports.append(dict(resource_id=rid, kind='lock_on_hud_font', font_id=2501,
                                texture_id=2001, before_sha256=key, font=report))
        require(len(cache) == 1, 'Unexpected HUD font variants')
    return changes, reports, (p[2501], p[2001], font, texture)


def preview(old_font, old_texture, font, texture):
    canvas = Image.new('RGBA', (660, 184), (65, 77, 90, 255))
    draw = ImageDraw.Draw(canvas)
    for y, title, ft, tx, text in [
        (4, 'Before', old_font, old_texture, 'Monsuno type10'),
        (48, 'After', font, texture, 'Monsuno type10'),
        (92, 'Other target names', font, texture, 'Gundam Virsago / Jagd Doga (Quess)'),
        (136, 'Letter coverage', font, texture, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz')]:
        draw.text((8, y), title, fill='white')
        atlas = decode(tx)
        mapping, start, _ = font_map(ft)
        x = 8
        for char in text:
            index = mapping.get(ord(char), mapping.get(0x8148))
            record = struct.unpack_from('<4f4h', ft, start+index*24)
            box = tuple(round(v*256) for v in record[:4])
            glyph = atlas.crop(box).resize((max(1, record[5]), u32(ft, 8)), Image.Resampling.NEAREST)
            canvas.alpha_composite(glyph, (x+record[4], y+16))
            x += record[6]
    PROOF.mkdir(parents=True, exist_ok=True)
    canvas.convert('RGB').save(PROOF/'font-proof.png')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--preview', action='store_true')
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    changes, reports, proof = plan()
    print(json.dumps(dict(version=VERSION, bundles=list(BUNDLES),
                         aliases=len(reports[0]['font']['aliases']),
                         copied_glyphs=len(reports[0]['font']['copied_glyphs']),
                         original_glyphs_preserved=reports[0]['font']['original_glyphs'],
                         ascii_complete=True), indent=2), flush=True)
    if args.preview:
        preview(*proof)
    if not args.write:
        return
    with BASE.open('rb') as f:
        require(builder.sha_region(f, 0, BASE.stat().st_size) == BASE_HASH, 'Base ISO identity changed')
    builder.VERSION, builder.BASE, builder.OUTPUT = VERSION, BASE, OUTPUT
    builder.build(changes, reports)
    path = OUTPUT.with_suffix('.json')
    report = json.loads(path.read_text(encoding='utf-8'))
    report.update(base_sha256=BASE_HASH,
                  coverage='Complete printable ASCII in the eight lock-on HUD fonts; preserve all original glyphs, texture dimensions, GPU headers and palettes.',
                  limitations='Offline font and full-disc checks only. In-game lock-on rendering needs a fresh-boot check. MOVIE003/MOVIE006 remain unintegrated.')
    path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
