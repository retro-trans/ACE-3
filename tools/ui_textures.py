"""Decode selected original UI textures for inspection. Extraction is dry-run first."""
import argparse
from pathlib import Path
import struct
from PIL import Image
from build_ui_patch import iso_files, inner_bnd, u32, require, ROOT

IDS = (50011, 50012, 50711, 50712, 50713, 50714, 50715)


def decode(data):
    tex = struct.unpack_from('<Q', data, 16)[0]
    psm = (tex >> 20) & 63
    width, height = 1 << ((tex >> 26) & 15), 1 << ((tex >> 30) & 15)
    pixel_size = u32(data, 4)
    raw = data[32:32 + pixel_size]
    palette = data[32 + pixel_size:u32(data, 0)]
    require(psm in (19, 20, 27, 44) and len(palette) in (64, 1024), 'Unsupported indexed texture')
    if len(palette) == 64:
        indices = bytes(v for byte in raw for v in (byte & 15, byte >> 4))
    else:
        indices = raw
    require(len(indices) == width * height, 'Texture dimensions mismatch')
    colors = []
    for i in range(len(palette) // 4):
        j = ((i & ~24) | ((i & 8) << 1) | ((i & 16) >> 1)) if len(palette) == 1024 else i
        r, g, b, a = palette[j * 4:j * 4 + 4]
        colors.append(bytes((r, g, b, min(255, a * 2))))
    return Image.frombytes('RGBA', (width, height), b''.join(colors[i] for i in indices))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    with next(ROOT.glob('*.iso')).open('rb') as f:
        files = iso_files(f)
        base = files['/DATA.BIN']['offset']
        f.seek(base)
        header = f.read(32)
        rows = f.read(u32(header, 16) * 16)
        for i in range(u32(header, 16)):
            _, size, off, bid = struct.unpack_from('<IIII', rows, i * 16)
            if bid == 4002050:
                f.seek(base + off)
                bundle = f.read(size)
                break
        for tid, start, end in inner_bnd(bundle):
            if tid not in IDS:
                continue
            img = decode(bundle[start:end])
            path = ROOT / 'work/ui/assets/source' / (str(tid) + '.png')
            print(('WRITE' if args.write else 'DRY RUN'), tid, img.size, path)
            if args.write:
                path.parent.mkdir(parents=True, exist_ok=True)
                img.save(path)


if __name__ == '__main__':
    main()
