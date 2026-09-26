"""Repaint the Japanese captions baked into the Global Meeting pictures (256x256 indexed textures in 4003xxx).

Each caption sits on a flat translucent bar. The Japanese glyphs are found as bright pixels inside the bar, removed
by interpolating the bar colour along each row, and the English is drawn in their place and mapped back to the
picture's own 256-colour palette, so the texture keeps its size, format and palette.
    python tools/meeting_captions.py --proof <dir>    write before/after proof sheets (nothing else)
The builder imports repaint() and CAPTIONS. Pictures are identified by the SHA-256 of the stock texture.
"""
import argparse
import hashlib
import struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from build_ui_patch import ROOT, u32, require
from dialogue_corpus import archive
from build_flight_save_patch import parts

SIZE = 66592  # 32-byte header, 256x256 indices, 256-colour palette
FONT = 'C:/Windows/Fonts/georgia.ttf'
TOP, BOTTOM = (4, 28), (230, 254)
# sha256[:12] of the stock texture -> [(band, [English captions left to right])]. Spellings are the locked ones.
CAPTIONS = {
 'ecda632f9789':[(TOP, [(32, 103, 'Ra Cailum')]), (BOTTOM, [(163, 233, 'Bright Noa')])],
 '72c3ea5798e4':[(TOP, [(39, 97, 'Ixbrau')]), (BOTTOM, [(130, 160, 'Barrel'), (204, 231, 'Faye')])],
 '22680e583eef':[(TOP, [(41, 94, 'Nadesico B')]), (BOTTOM, [(167, 229, 'Ruri Hoshino')])],
 '756a22aefc75':[(TOP, [(51, 84, 'Gekko')]), (BOTTOM, [(152, 243, 'Holland Novak')])],
 '6d2bf4578fec':[(TOP, [(15, 151, 'Nirvash typeZERO')]), (BOTTOM, [(183, 218, 'Eureka')])],
 'bf0594d7f689':[(BOTTOM, [(134, 218, 'Gain Bijou')])],
 'dd53bf661457':[(TOP, [(37, 102, 'Siberian Railway')])],
 'db2a3825b676':[(BOTTOM, [(64, 114, 'Shin Dragon'), (184, 238, 'Dr. Saotome')])],
 '5a74ac963365':[(TOP, [(34, 104, 'Blood Ark')]), (BOTTOM, [(157, 196, 'Berkt')])],
 '180d49129dbb':[(TOP, [(21, 112, 'Shin Getter-1 (Go)')]), (BOTTOM, [(86, 134, 'Go'), (145, 193, 'Kei'), (205, 253, 'Gai')])],
 '0692176ca420':[(TOP, [(48, 87, 'Macross')])],
 '36f153c04d26':[(TOP, [(9, 126, 'Aestivalis (Ryoko)')]), (BOTTOM, [(157, 229, 'Ryoko Subaru')])],
 'ac7cd5506cec':[(TOP, [(36, 99, 'Emperanza')]), (BOTTOM, [(156, 234, 'Gain Bijou')])],
 '9beb2aa56d96':[(TOP, [(166, 245, 'Neo Zeon')]), ((112, 136), [(17, 70, 'Giganos'), (175, 245, 'Martian Succ.')])],
 '2d51a1ac928c':[(TOP, [(10, 119, 'Aestivalis (Izumi)'), (134, 245, 'Aestivalis (Hikaru)')]), (BOTTOM, [(137, 158, 'Izumi'), (204, 233, 'Hikaru')])],
 '3d893573eec1':[(TOP, [(6, 69, 'VF-1A Hikaru'), (81, 158, 'VF-1A Max'), (170, 245, 'VF-1S Fokker')]),
                 (BOTTOM, [(100, 113, 'Hikaru'), (144, 181, 'Max'), (200, 248, 'Fokker')])],
 '892770db324b':[(BOTTOM, [(178, 218, 'Berkt')])],
 '3ac3ec88bce9':[(TOP, [(179, 238, 'New Fed. Main Force')]), ((66, 90), [(15, 50, 'Intelligence')]), (BOTTOM, [(174, 238, 'Siberian Railway')])],
 '00c1fc8b454a':[(TOP, [(30, 108, 'Neo Zeon')]), (BOTTOM, [(127, 226, 'Char Aznable')])],
 '67cdd2ead223':[(TOP, [(38, 100, 'Hojo Army')]), (BOTTOM, [(123, 230, 'Shinjiro Sakomizu')])],
 '7a1455a465a2':[(TOP, [(53, 87, 'Nanajin')]), (BOTTOM, [(153, 243, 'Asap Suzuki')])],
 '374f3f4f4fcf':[(TOP, [(196, 225, 'Deins')]), (BOTTOM, [(29, 60, 'Gewei')])],
 '6f97e8fe2b4d':[(TOP, [(13, 122, 'Nirvash spec2')]), (BOTTOM, [(127, 162, 'Renton'), (198, 238, 'Eureka')])],
 '66d032e098b7':[(TOP, [(46, 80, 'New Federation')]), (BOTTOM, [(130, 223, 'Dewey Novak')])],
 '27128b41f677':[(BOTTOM, [(63, 128, 'Invaders'), (184, 238, 'Dr. Saotome')])],
 '86577c81a2ec':[(BOTTOM, [(155, 196, 'Eureka')])],
 '4c6bb973ed5b':[(BOTTOM, [(128, 224, 'Barrel Orland')])],
 '94430cdcaca5':[(BOTTOM, [(161, 191, 'Norb')])],
 '8bbaf42b0f8d':[(TOP, [(11, 114, 'Terminus typeB303')]), (BOTTOM, [(152, 243, 'Holland Novak')])],
 '4a9ec061cb3a':[(BOTTOM, [(177, 218, 'Eureka')])],
 '29ae67d74e91':[(BOTTOM, [(125, 227, 'Renton Thurston')])],
 'ed9ec53a930b':[(TOP, [(30, 108, 'Neo Zeon')]), (BOTTOM, [(127, 226, 'Char Aznable')])],
 'b4181b60982a':[(TOP, [(8, 143, 'Grave Ark Phantom')]), (BOTTOM, [(157, 196, 'Berkt')])],
 'c6229e7c4628':[(TOP, [(52, 87, 'New Federation')])],
 '5452d8acd3fa':[(BOTTOM, [(29, 66, 'Jamil'), (112, 141, 'Gain'), (200, 221, 'Hayato')])],
 '5664a9669e76':[(TOP, [(52, 87, 'New Federation')]), (BOTTOM, [(121, 232, 'Fixx Bloodman')])],
 'ab3ca105a870':[(TOP, [(14, 112, 'Gundam Virsago'), (137, 242, 'Gundam Ashtaron')]), (BOTTOM, [(114, 155, 'Shagia'), (197, 229, 'Olba')])],
}


def unswizzle(i):
    return (i & ~24) | ((i & 8) << 1) | ((i & 16) >> 1)


def decode(data):
    require(len(data) == SIZE and u32(data, 4) == 65536, 'Not a 256x256 indexed picture')
    indices = data[32:32+65536]; palette = data[32+65536:SIZE]
    colors = [tuple(palette[unswizzle(i)*4:unswizzle(i)*4+3]) for i in range(256)]
    return indices, colors


def luminance(c):
    return (c[0]*299+c[1]*587+c[2]*114)//1000


def clusters(indices, colors, band, gap=9):
    """Columns holding caption glyphs: bright pixels in columns whose band edges are the dark bar."""
    y0, y1 = band
    lum = lambda x, y: luminance(colors[indices[y*256+x]])
    columns = []
    for x in range(256):
        if lum(x, y0) < 100 and lum(x, y1-1) < 100 and any(lum(x, y) > 140 for y in range(y0+2, y1-2)): columns.append(x)
    groups = []
    for x in columns:
        if groups and x-groups[-1][1] <= gap: groups[-1][1] = x
        else: groups.append([x, x])
    return [(a, b) for a, b in groups if b-a >= 6]


def bar_extent(image, band, a, b):
    """How far the flat bar runs left and right of the glyph columns, judged on the band's edge rows."""
    y0, y1 = band
    def flat(x, ref):
        return all(luminance(image.getpixel((x, y))) < 115 and sum(abs(p-q) for p, q in zip(image.getpixel((x, y)), ref[n])) < 70
                   for n, y in enumerate((y0+1, y1-2)))
    left_ref = [image.getpixel((max(a-3, 0), y)) for y in (y0+1, y1-2)]; right_ref = [image.getpixel((min(b+3, 255), y)) for y in (y0+1, y1-2)]
    left, right = a, b
    while left > 0 and flat(left-1, left_ref): left -= 1
    while right < 255 and flat(right+1, right_ref): right += 1
    return left, right


def repaint(data, plan):
    indices, colors = decode(data); pixels = [colors[i] for i in indices]
    image = Image.new('RGB', (256, 256)); image.putdata(pixels)
    report, pending = [], []
    for band, captions in plan:
        y0, y1 = band
        for a, b, text in captions:
            lum = lambda x, y: luminance(image.getpixel((x, y)))
            span = range(a, b+1)
            # Glyph rows: bright pixels between the given columns on rows that are mostly dark bar.
            rows = [y for y in range(max(y0-6, 1), min(y1+6, 255)) if any(lum(x, y) > 140 for x in span)
                    and sum(lum(x, y) < 100 for x in span)*10 >= len(span)*3]
            require(rows, 'No glyphs where expected: %s' % text)
            top, bottom = min(rows), max(rows)
            # Grow the columns a little over strokes the given range missed, never into a neighbouring caption.
            def grow(x, step, limit=12):
                gap, start = 0, x
                while 0 < x+step < 255 and gap < 5 and abs(x+step-start) <= limit:
                    x += step
                    if any(lum(x, y) > 140 for y in range(top, bottom+1)): gap = 0
                    else: gap += 1
                return x-step*gap
            a, b = max(grow(a, -1)-2, 0), min(grow(b, 1)+2, 255)
            # Erase: every pixel brighter than the bar takes the colour of the last bar pixel on its row.
            for y in range(top-1, bottom+2):
                bar = sorted(lum(x, y) for x in range(a, b+1) if lum(x, y) < 110)
                if len(bar) < 3: continue
                limit = bar[len(bar)//2]+22
                last = next(image.getpixel((x, y)) for x in range(a, b+1) if lum(x, y) <= limit)
                for x in range(a, b+1):
                    if lum(x, y) <= limit: last = image.getpixel((x, y))
                    else: image.putpixel((x, y), last)
            fitted = (top-3, bottom+4)  # this caption's own rows; the plan's band stays as given for the next caption
            bar_left, bar_right = bar_extent(image, fitted, a, b)
            centre = (a+b)//2; anchored = False
            if top < 40:  # unit and faction labels are centred on a bar that starts at the picture's edge
                room = 2*min(centre, 255-centre)-10
            else:
                room = max(2*min(centre-bar_left, bar_right-centre)-8, b-a+12)
            pending.append((text, a, b, fitted[0], fitted[1], centre, room, bar_left))
    for text, a, b, y0, y1, centre, room, bar_left in pending:  # draw after every caption is erased
        size = 15
        while True:
            font = ImageFont.truetype(FONT, size); box = font.getbbox(text); width = box[2]-box[0]
            if width <= room or size == 11: break
            size -= 1
        if width > room+4: print('   NOTE tight bar (%d > %d): %s' % (width, room, text))
        x = min(max(centre-width//2, 2), 253-width)-box[0]; y = (y0+y1)//2-(box[3]+box[1])//2
        ImageDraw.Draw(image).text((x, y), text, font=font, fill=(226, 230, 236))
        report.append({'text':text, 'columns':[a, b], 'font_size':size, 'width':width})
    # Back to the stock palette: nearest colour, palette untouched.
    cache = {}
    def nearest(c):
        if c not in cache: cache[c] = min(range(256), key=lambda i: sum((p-q)**2 for p, q in zip(colors[i], c)))
        return cache[c]
    new = bytes(nearest(c) if c != colors[old] else old for c, old in zip(image.getdata(), indices))
    output = data[:32]+new+data[32+65536:]
    require(len(output) == SIZE and output[:32] == data[:32] and output[32+65536:] == data[32+65536:], 'Picture container changed')
    return output, report


def pictures(stream):
    info, entries = archive(stream); seen = {}
    for entry in entries:
        if not 4003000 <= entry[3] < 4004000: continue
        stream.seek(info['offset']+entry[2])
        for key, chunk in parts(stream.read(entry[1])).items():
            if key >= 2 and len(chunk) == SIZE: seen.setdefault(hashlib.sha256(chunk).hexdigest()[:12], [chunk, []])[1].append((entry[3], key))
    return seen


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--proof'); ap.add_argument('--detect', action='store_true'); a = ap.parse_args()
    with next(ROOT.glob('*.iso')).open('rb') as f: seen = pictures(f)
    if a.detect:
        for n, (sha, (chunk, uses)) in enumerate(seen.items()):
            indices, colors = decode(chunk)
            print(n, sha, 'top', clusters(indices, colors, TOP), 'bottom', clusters(indices, colors, BOTTOM))
        return
    done = []
    for sha, plan in CAPTIONS.items():
        output, report = repaint(seen[sha][0], plan); done.append((sha, seen[sha][0], output))
        print(sha, len(seen[sha][1]), 'uses', [(r['text'], r['font_size']) for r in report])
    if a.proof:
        out = Path(a.proof)
        for start in range(0, len(done), 10):
            sheet = Image.new('RGB', (2560, 512))
            for n, (sha, before, after) in enumerate(done[start:start+10]):
                for row, chunk in enumerate((before, after)):
                    indices, colors = decode(chunk); tile = Image.new('RGB', (256, 256)); tile.putdata([colors[i] for i in indices])
                    sheet.paste(tile, (n*256, row*256))
            sheet.save(out/('captions_proof_%d.png' % (start//10)))


if __name__ == '__main__': main()
