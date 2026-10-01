"""Audit native font capacity and create an HD serif atlas/preview, without patching.

The output atlas is a local PCSX2 replacement experiment, not an installable pack:
runtime dump identities and renderer behavior have not yet been verified.
"""
import hashlib
import json
import struct
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageFilter
from build_controller_patch import NativeGlyphs
from build_flight_save_patch import parts
from dialogue_corpus import archive
from ui_font import font_map

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'work/ui/font_preview/hd'
BASE = ROOT / 'work/output/ACE3-English-0.9.6.iso'
SCALE = 4
BUNDLES = (4002050, 4002053, 4002057, 1200000, 1200011)


def record(font, start, index):
    return struct.unpack_from('<4f4h', font, start + index * 24)


def rect(row, size):
    w, h = size
    return tuple(round(v * s) for v, s in zip(row[:4], (w, h, w, h)))


def audit(font, texture):
    mapping, start, count = font_map(font)
    tex0 = struct.unpack_from('<Q', texture, 16)[0]
    w, h = 1 << ((tex0 >> 26) & 15), 1 << ((tex0 >> 30) & 15)
    latin = {mapping[c] for c in range(33, 127)}
    candidates = []
    for scale in (1, 2, 4):
        dims = []
        for i in range(count):
            x, y, xx, yy = rect(record(font, start, i), (w, h))
            factor = scale if i in latin else 1
            dims.append(((xx - x) * factor, (yy - y) * factor))
        shelves = []
        for gw, gh in sorted(dims, key=lambda d: (-d[1], -d[0])):
            fits = [s for s in shelves if s[1] >= gh and s[0] + gw <= w]
            if fits:
                shelf = min(fits, key=lambda s: (s[1] - gh, w - s[0] - gw))
                shelf[0] += gw
            else:
                shelves.append([gw, gh])
        candidates.append(dict(latin_scale=scale, required_pixel_area=sum(a*b for a,b in dims),
                               area_exceeds_atlas=sum(a*b for a,b in dims) > w*h,
                               shelf_packed_height=sum(s[1] for s in shelves)))
    return dict(dimensions=[w, h], glyph_count=count, latin_glyphs=len(latin),
                texture_base_bytes=(tex0 & 16383)*256,
                palette_base_bytes=((tex0 >> 37) & 16383)*256,
                atlas_pixel_bytes=w*h//2, candidates=candidates)


def make_hd(native):
    """Fresh vector rasterization; old bitmap enlargement is only for other glyphs."""
    font = ImageFont.truetype('C:/Windows/Fonts/times.ttf', 21 * SCALE)
    reference = native.atlas.resize((native.atlas.width*SCALE, native.atlas.height*SCALE),
                                    Image.Resampling.NEAREST)
    atlas = reference.copy()
    allowed = Image.new('L', atlas.size)
    mask_draw = ImageDraw.Draw(allowed)
    touched = set()
    for code in range(33, 127):
        index = native.mapping[code]
        if index in touched:
            continue
        touched.add(index)
        row = record(native.font, native.start, index)
        box = rect(row, atlas.size)
        w, h = box[2]-box[0], box[3]-box[1]
        # Use a common baseline for capitals, lowercase and descenders. Render
        # outside the cell first so narrow native slots cannot clip the glyph.
        scratch = Image.new('L', (160, h+32))
        draw = ImageDraw.Draw(scratch)
        draw.text((16, 15*SCALE), chr(code), font=font, anchor='ls', fill=255)
        bbox = scratch.getbbox()
        assert bbox is not None, chr(code)
        glyph = scratch.crop(bbox)
        original = native.atlas.crop(rect(row, native.atlas.size))
        ink_bounds = original.getchannel('R').point(lambda v: 255 if v > 80 else 0).getbbox()
        assert ink_bounds is not None, chr(code)
        left, top, right, bottom = [v*SCALE for v in ink_bounds]
        # Match the original visible letter bounds, not just its font-cell size;
        # otherwise larger new capitals would unfairly favor the HD sample.
        glyph = glyph.resize((right-left,bottom-top), Image.Resampling.LANCZOS)
        ink = Image.new('L', (w, h))
        ink.paste(glyph, (left, top))
        # Half-native-pixel outline improves contrast on brighter backgrounds.
        outline = ink.filter(ImageFilter.MaxFilter(5))
        tile = Image.new('RGBA', (w,h), (10,15,23,0))
        tile.putalpha(outline)
        white = Image.new('RGBA', (w,h), (245,245,245,0))
        white.putalpha(ink)
        tile.alpha_composite(white)
        atlas.paste(tile, box)
        mask_draw.rectangle((box[0],box[1],box[2]-1,box[3]-1),fill=255)
    changed = ImageChops.difference(atlas, reference)
    for channel in changed.split():
        assert ImageChops.multiply(channel, ImageChops.invert(allowed)).getbbox() is None
    _, _, count = font_map(native.font)
    for index in range(count):
        if index not in touched:
            box = rect(record(native.font,native.start,index),atlas.size)
            assert atlas.crop(box).tobytes() == reference.crop(box).tobytes(), index
    # Original data and metrics are used for all placement; no font-table edits.
    return atlas, len(touched)


def text_image(native, atlas, text, display_scale=2):
    width = sum(record(native.font,native.start,native.mapping[ord(c)])[6] for c in text)
    height = struct.unpack_from('<I',native.font,8)[0]
    out = Image.new('RGBA', ((width+4)*display_scale, height*display_scale))
    x = 0
    for char in text:
        row = record(native.font,native.start,native.mapping[ord(char)])
        glyph = atlas.crop(rect(row,atlas.size))
        glyph = glyph.resize((max(1,row[5])*display_scale,height*display_scale),
                             Image.Resampling.BILINEAR)
        out.alpha_composite(glyph, ((x+row[4])*display_scale,0))
        x += row[6]
    return out


def panel(native, atlas):
    image = Image.new('RGBA', (1280, 328), '#071526')
    draw = ImageDraw.Draw(image)
    for y in range(0,328,8):
        draw.line((0,y,1280,y),fill='#0a192b')
    def text(s,x,y):
        im = text_image(native,atlas,s)
        assert x+im.width <= image.width, s
        image.alpha_composite(im,(x,y))
    draw.rectangle((24,22,485,80),outline='#657483',width=2)
    text('Combat Records',36,32)
    draw.rectangle((24,92,485,150),outline='#657483',width=2)
    text('Unit Upgrades',36,102)
    draw.rectangle((24,176,1254,306),fill='#080e20',outline='#46566b',width=2)
    text('Renton',42,182)
    text("They were fun days, but Eureka wasn't there.",42,222)
    text('I kept feeling like something was missing.',42,262)
    return image.convert('RGB')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    reports = []
    with BASE.open('rb') as stream:
        fi, entries = archive(stream)
        for rid in BUNDLES:
            entry = next(e for e in entries if e[3] == rid)
            stream.seek(fi['offset']+entry[2])
            p = parts(stream.read(entry[1]))
            reports.append(dict(bundle=rid,**audit(p[2500],p[2000])))
            if rid == 4002050:
                native = NativeGlyphs(p[2500],p[2000])
                source_hash = hashlib.sha256(p[2500]+p[2000]).hexdigest()
    hd, touched = make_hd(native)
    hd.save(OUT/'menu-atlas-4x-prototype.png')
    levels=[round(20+235*max(0,min(1,(v-55)/125))) for v in range(256)]
    r,g,b,a=native.atlas.split()
    contrast=Image.merge('RGBA',(r.point(levels),g.point(levels),b.point(levels),a))
    label = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',25)
    title = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',32)
    canvas=Image.new('RGB',(1320,1390),'#101824')
    draw=ImageDraw.Draw(canvas)
    draw.text((22,14),'HD font experiment',font=title,fill='white')
    draw.text((22,57),'Matched letter bounds and spacing. All samples shown at 2x game coordinates.',font=label,fill='#bacbdf')
    for i,(name,atlas,filename) in enumerate([
            ('1 / Current bitmap font',native.atlas,'current-2x.png'),
            ('2 / Contrast adjustment only',contrast,'contrast-2x.png'),
            ('3 / Fresh 4x lettering with AA (similar serif typeface)',hd,'hd-2x.png')]):
        y=106+i*402
        draw.text((22,y),name,font=label,fill='#91cbea')
        specimen=panel(native,atlas)
        specimen.save(OUT/filename)
        canvas.paste(specimen,(20,y+42))
    draw.text((22,1320),'Local visual prototype; not installed or tested in-game.',font=label,fill='#bacbdf')
    canvas.save(OUT/'hd-font-comparison.png')
    report=dict(status='offline_prototype_not_installed',base_version='0.9.6',
                font_source_sha256=source_hash,capacity_audit=reports,
                prototype=dict(scale=SCALE,dimensions=list(hd.size),replaced_ascii_glyphs=touched,
                               typeface='Times New Roman, locally installed font; TTF not copied',
                               alpha='grayscale coverage with a half-native-pixel outline',
                               font_table_unchanged=True,other_atlas_pixels_preserved_at_nearest_4x=True),
                limitations=['Prototype uses a similar serif, not a vector reconstruction of the original',
                             'Only one menu atlas redrawn; other font atlases still need handling',
                             'Requires PCSX2 texture dump/hash matching and an in-game trial',
                             'Does not improve PS2 native framebuffer resolution',
                             'Not an ISO patch and not verified for ARMSX2'],
                reference='https://pcsx2.net/blog/2024/pcsx2-2-release/')
    (OUT/'feasibility.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(OUT/'hd-font-comparison.png')


if __name__ == '__main__':
    main()
