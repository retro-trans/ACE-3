"""0.1.54: replace the ending disclaimer texture. Dry-run unless --write."""
import argparse
import hashlib
import json
import sys
from PIL import Image, ImageDraw, ImageFont
from build_ui_patch import ROOT, require, u32
from dialogue_corpus import archive
from ui_textures import decode
import build_stats_panel_patch as writer

VERSION = '0.1.54'
BASE = ROOT/'work/output/ACE3-English-0.1.53.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_HASH = 'd323b46805dcbfbcbb8e688bb203db70b7b2dd46512546e16664876e96d002c3'
TEXTURE_HASH = 'f1a571d87a3fe5b8e23a5ed75de04cbb2750e834b7ceb750145a20b609608195'
INPUT = ROOT/'work/translation/en/ending_disclaimer_054.json'
FONT = 'C:/Windows/Fonts/georgia.ttf'
PREVIEW = ROOT/'work/ui/ending_disclaimer_054/preview'


def repaint(source, target, lines):
    require(hashlib.sha256(source).hexdigest() == TEXTURE_HASH, 'Unexpected disclaimer texture')
    require(u32(source, 0) == 16480 and u32(source, 4) == 16384, 'Texture format changed')
    require(decode(source).size == (256, 128), 'Texture dimensions changed')
    palette = source[-64:]
    colors = [tuple(palette[i:i+3])+(min(255, palette[i+3]*2),) for i in range(0, 64, 4)]
    require(colors[0] == (0, 0, 0, 255), 'Background palette changed')
    font = ImageFont.truetype(FONT, 14)
    require(' '.join(lines) == target and len(lines) <= 7, 'Incomplete disclaimer or too many lines')
    require(all(font.getlength(line) <= 244 for line in lines), 'Line too wide')
    image = Image.new('RGBA', (256, 128), colors[0])
    draw = ImageDraw.Draw(image)
    top = (128-len(lines)*16)//2
    for n, line in enumerate(lines):
        draw.text((6, top+n*16), line, font=font, fill=(180, 180, 180, 255), anchor='lt')
    cache = {}
    indices = []
    for pixel in image.getdata():
        if pixel not in cache:
            cache[pixel] = min(range(16), key=lambda j: sum((a-b)**2 for a, b in zip(pixel, colors[j])))
        indices.append(cache[pixel])
    pixels = bytes(indices[i] | (indices[i+1] << 4) for i in range(0, len(indices), 2))
    result = source[:32]+pixels+palette
    require(len(result) == len(source) and result[:32] == source[:32] and result[-64:] == source[-64:],
            'Texture metadata or palette changed')
    bounds = decode(result).convert('RGB').getbbox()
    require(bounds and 4 <= bounds[0] < bounds[2] <= 252 and 2 <= bounds[1] < bounds[3] <= 126,
            'Caption exceeds safe texture bounds')
    return result, dict(lines=lines, bounds=list(bounds), font='Georgia', font_pixels=14,
                        font_sha256=hashlib.sha256(open(FONT, 'rb').read()).hexdigest())


def plan():
    doc = json.loads(INPUT.read_text(encoding='utf-8'))
    require(doc['status'] == 'meaning_reviewed', 'Unreviewed disclaimer')
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        _, size, off, _ = next(e for e in entries if e[3] == 4350)
        f.seek(fi['offset']+off)
        data = f.read(size)
        before = data[0x2009e0:0x2009e0+16480]
        after, layout = repaint(before, doc['target'], doc['display_lines'])
        copies = []
        for _, length, offset, rid in entries:
            f.seek(fi['offset']+offset)
            chunk = f.read(length)
            at = chunk.find(before)
            if at >= 0:
                require(chunk.find(before, at+1) < 0, 'Unexpected duplicate in resource')
                copies.append((rid, at))
        require(copies == [(4350, 0x2009e0)], 'Disclaimer copy inventory changed')
    return [dict(offset=fi['offset']+off+0x2009e0, before=before, after=after)], dict(
        resource_id=4350, texture_offset=0x2009e0, dimensions=[256, 128], layout=layout,
        translation_sha256=hashlib.sha256(INPUT.read_bytes()).hexdigest(), runtime_verified=False), after


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--preview', action='store_true')
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    edits, summary, texture = plan()
    print('DRY RUN: one ending disclaimer texture', flush=True)
    print(json.dumps(summary, indent=2), flush=True)
    if args.preview:
        PREVIEW.mkdir(parents=True, exist_ok=True)
        for name, raw in [('before', edits[0]['before']), ('after', texture)]:
            decode(raw).resize((1024, 512), Image.Resampling.NEAREST).save(PREVIEW/(name+'.png'))
    if args.write:
        writer.VERSION, writer.BASE, writer.OUTPUT, writer.BASE_HASH = VERSION, BASE, OUTPUT, BASE_HASH
        writer.plan = lambda: (edits, summary, texture)
        sys.argv = [sys.argv[0], '--write']
        writer.main()


if __name__ == '__main__':
    main()
