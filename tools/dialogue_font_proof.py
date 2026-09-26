"""Render an offline diagnostic from the actual patched font bitmaps."""
import argparse
import struct
from PIL import Image
from build_ui_patch import ROOT, inner_bnd, u32
from dialogue_corpus import archive
from dialogue_font import complete_font, texture_pixels
from ui_font import font_map


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    with next(ROOT.glob('*.iso')).open('rb') as stream:
        file, entries = archive(stream)
        def get(resource_id):
            entry = next(r for r in entries if r[3] == resource_id)
            stream.seek(file['offset'] + entry[2])
            return stream.read(entry[1])
        bundle = get(1200000)
        parts = {rid: bundle[start:end] for rid, start, end in inner_bnd(bundle)}
        font, texture, _ = complete_font(parts[2500], parts[2000], get(35), get(36))
    width, height, pixels = texture_pixels(texture)
    palette = texture[32 + u32(texture, 4):u32(texture, 0)]
    colors = [tuple(palette[i:i + 3]) + (min(255, palette[i + 3] * 2),) for i in range(0, 64, 4)]
    atlas = Image.frombytes('RGBA', (width, height), b''.join(bytes(colors[p]) for p in pixels))
    mapping, glyphs, _ = font_map(font)
    lines = ['Offline font proof - original game glyphs', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
             'abcdefghijklmnopqrstuvwxyz', "W-wait a second!", 'You mean I have to pilot this?',
             'Quickly jump back, Faye. Keep moving!', '0123456789 !?.,:; \'"()-+ /']
    proof = Image.new('RGBA', (540, len(lines) * 28 + 20), (7, 17, 32, 255))
    for line_index, line in enumerate(lines):
        x, y = 12, 10 + line_index * 28
        for char in line:
            record = struct.unpack_from('<4f4h', font, glyphs + mapping[ord(char)] * 24)
            left, top, right, bottom, offset, glyph_width, advance, zero = record
            crop = atlas.crop((round(left * width), round(top * height), round(right * width), round(bottom * height)))
            crop = crop.resize((max(1, glyph_width), u32(font, 8)), Image.BILINEAR)
            proof.alpha_composite(crop, (x + offset, y))
            x += advance
    path = ROOT / 'work/ui/assets/dialogue_font_0.1.6.png'
    print('Offline diagnostic:', path, 'size', proof.size, 'ASCII glyphs', sum(c in mapping for c in range(32, 127)))
    if args.write:
        path.parent.mkdir(parents=True, exist_ok=True)
        proof.resize((1080, proof.height * 2), Image.NEAREST).save(path)


if __name__ == '__main__':
    main()
