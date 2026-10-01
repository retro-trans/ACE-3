"""0.9.11: English staff roll and an embedded antialiased serif font.

Dry-run unless --write. Preserve every row/ID, logo command, timing track,
dialogue/lyric caption, disc extent and unrelated resource.
"""
import hashlib
import json
import math
import re
import struct
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from build_ui_patch import ROOT, require, u32
from dialogue_corpus import archive, parse_table
from build_history_patch import chunks
from build_flight_save_patch import parts
from build_dialogue_patch import rebuild_bundle
from dialogue_font import texture_pixels, encode_pixels
from ui_font import font_map, measure_text
from preview_hd_font import text_image, record, rect
from build_controller_patch import NativeGlyphs
from build_all_fonts_test_patch import place
import build_stats_panel_patch as writer

VERSION = '0.9.11'
BASE = ROOT/'work/output/ACE3-English-0.9.10.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_HASH = '417398c847d83b512f999a5bbdf820e23dacdbcf89ab499060ff3ac08466cc62'
FOLDER = ROOT/'work/ui/staff_credits_0911'
TRANSLATION = ROOT/'work/translation/en/staff_credits.json'
COLOR = re.compile(r'#c(?:\[[0-9A-Fa-f]{6}\])?')
ROLL_X, LINE_HEIGHT, CENTER = 90, 21, 320


def font_assets(source, texture):
    """Repack a complete ASCII font in the original 512-square allocation."""
    w, h, _ = texture_pixels(texture)
    require((w, h) == (512, 512), 'Staff atlas dimensions')
    require(u32(source, 8) == 20, 'Staff font height')
    pal = 32+u32(texture, 4)
    palette = texture[pal:pal+64]
    colors = [tuple(palette[i:i+3])+(min(255, palette[i+3]*2),) for i in range(0, 64, 4)]
    def premult(c): return tuple(v*c[3]/255 for v in c[:3])+(c[3],)
    color_vectors = [premult(c) for c in colors]
    blank = next(i for i, c in enumerate(colors) if not c[3])
    failures = []
    for scale in (4, 3, 2):
        vector = ImageFont.truetype('C:/Windows/Fonts/times.ttf', 21*scale)
        glyphs = []
        for code in range(32, 127):
            char = chr(code)
            advance = max(1, round(vector.getlength(char)/scale))
            bbox = vector.getbbox(char, anchor='ls')
            bearing = math.floor(bbox[0]/scale)-1
            draw_width = max(1, math.ceil(bbox[2]/scale)-bearing+1)
            mask = Image.new('L', (draw_width*scale, 20*scale))
            ImageDraw.Draw(mask).text((-bearing*scale, 16*scale), char, font=vector, fill=255, anchor='ls')
            # Half a native pixel of outline, sampled before palette conversion.
            outline = mask.filter(ImageFilter.MaxFilter(2*max(1, round(scale*.5))+1))
            tile = Image.new('RGBA', mask.size, (32, 32, 32, 0)); tile.putalpha(outline)
            white = Image.new('RGBA', mask.size, (245, 245, 245, 0)); white.putalpha(mask)
            tile.alpha_composite(white)
            glyphs.append(dict(old_index=code-32, w=tile.width, h=tile.height, pad=1,
                               tile=tile, metrics=(bearing, draw_width, advance, 0)))
        if sum((g['w']+2)*(g['h']+2) for g in glyphs) > w*h:
            failures.append([scale, 'pixel capacity']); continue
        try:
            place(glyphs, w, h)
        except ValueError:
            failures.append([scale, 'rectangle packing']); continue
        break
    else:
        raise ValueError('ASCII font does not fit')
    pixels = bytearray([blank])*(w*h); occupied = bytearray(w*h); quant = {}
    out = bytearray(source[:32])
    # Retain the whitespace-only original row without retaining unused kanji.
    ranges = [(32, 126, 0), (0x8140, 0x8140, 0)]
    for r in ranges: out.extend(struct.pack('<3I', *r))
    glyph_start = len(out)
    for g in glyphs:
        x, y, gw, gh = g['x'], g['y'], g['w'], g['h']
        require(0 <= x-1 and x+gw+1 <= w and 0 <= y-1 and y+gh+1 <= h, 'Glyph bounds')
        for yy in range(y-1, y+gh+1):
            require(not any(occupied[yy*w+x-1:yy*w+x+gw+1]), 'Glyph overlap')
            occupied[yy*w+x-1:yy*w+x+gw+1] = b'\1'*(gw+2)
        packed = []
        for c in g['tile'].getdata():
            if c not in quant:
                v = premult(c)
                quant[c] = min(range(16), key=lambda i: sum((a-b)**2*(3 if k == 3 else 1) for k, (a,b) in enumerate(zip(v, color_vectors[i]))))
            packed.append(quant[c])
        g['pixels'] = bytes(packed)
        for yy in range(gh): pixels[(y+yy)*w+x:(y+yy)*w+x+gw] = g['pixels'][yy*gw:(yy+1)*gw]
        out.extend(struct.pack('<4f4h', x/w, y/h, (x+gw)/w, (y+gh)/h, *g['metrics']))
    struct.pack_into('<I', out, 4, len(out))
    struct.pack_into('<HH', out, 16, len(ranges), len(glyphs))
    struct.pack_into('<I', out, 24, glyph_start)
    tx = encode_pixels(texture, pixels)
    require(tx[:32] == texture[:32] and tx[pal:] == texture[pal:] and len(tx) == len(texture), 'Texture header/palette/allocation changed')
    _, _, decoded = texture_pixels(tx)
    require(bytes(decoded) == bytes(pixels), 'Texture round trip')
    mapping, start, count = font_map(out)
    require(all(c in mapping for c in range(32, 127)) and count == 95, 'ASCII coverage')
    for g in glyphs:
        x,y,xx,yy = rect(record(out,start,g['old_index']), (w,h))
        require(b''.join(decoded[j*w+x:j*w+xx] for j in range(y,yy)) == g['pixels'], 'Glyph decode mismatch')
    return bytes(out), tx, dict(face='Times New Roman', sampling=scale, atlas=[w,h], ascii_glyphs=95,
                               font_height=20, palette_and_gpu_allocation_preserved=True,
                               texture_round_trip_verified=True, unavailable_larger_scales=failures)


def translated_table(source, font, doc):
    require(hashlib.sha256(source).hexdigest() == doc['source_table_sha256'], 'Source table hash')
    _, ptrs, count, rows = parse_table(source)
    by_id = {r['text_id']: r for r in doc['rows']}
    require(len(by_id) == 332, 'Meaningful row count')
    out = bytearray(source[:ptrs+count*4]); out[ptrs:] = bytes(count*4)
    pool = {}; report = []; seen = set()
    factor = LINE_HEIGHT/u32(font, 8)
    space = measure_text(font, ' ')[0]
    for slot, tid, _, raw in rows:
        original = raw.decode('cp932')
        target = raw
        if original.strip():
            row = by_id[tid]; seen.add(tid)
            require(hashlib.sha256(raw).hexdigest() == row['source_sha256'], 'Source row hash')
            require(row['target'] is not None, 'Unresolved row')
            if row['status'] != 'preserve_graphics_commands':
                text = row['target']
                require(text.isascii() and '\n' not in text, 'Target must be one ASCII line')
                width = measure_text(font, text)[0]
                indent = round(((CENTER-ROLL_X)/factor-width/2)/space)
                require(indent >= 0, 'Line cannot be centered inside roll')
                x = ROLL_X+indent*space*factor
                require(80 <= x and x+width*factor <= 560, 'Credits line outside safe area')
                prefix = ' '*indent
                tokens = COLOR.findall(original)
                require(not tokens or tokens == ['#c[FF0000]', '#c'], 'Unexpected color commands')
                # Original red empty prefix resets to white before the song title.
                target = ((tokens[0]+prefix+tokens[1]+text) if tokens else prefix+text).encode('ascii')
                require(COLOR.findall(target.decode('ascii')) == tokens, 'Color commands changed')
                require(len(target) < 256, 'Native text buffer bound')
                report.append(dict(text_id=tid, text=text, width=width*factor, x=x,
                                   center=x+width*factor/2, status=row['status']))
        if target not in pool:
            pool[target] = len(out); out.extend(target+b'\0')
        struct.pack_into('<I', out, ptrs+slot*4, pool[target])
    require(seen == set(by_id), 'Translation coverage')
    out.extend(b'\0'*(-len(out)%32)); struct.pack_into('<I',out,4,len(out))
    newrows = parse_table(out)[3]
    require([(s,t) for s,t,_,_ in newrows] == [(s,t) for s,t,_,_ in rows], 'Rows/null slots changed')
    for old,new in zip(rows,newrows):
        if not old[3].decode('cp932').strip() or old[3].startswith(b'<picture('):
            require(old[3] == new[3], 'Blank row or logo command changed')
    return bytes(out), report


def previews(font, texture, lines):
    native = NativeGlyphs(font, texture)
    native.atlas.save(FOLDER/'font-atlas.png')
    by_id = {r['text_id']:r for r in lines}
    pages = [('directors', range(29,61)), ('cast', range(486,501)), ('long-lines', (610,613,636,641,659,661,688)),
             ('provisional-names', (177,179,184,186,427,434))]
    # These decode the actual built font; they are not emulator screenshots.
    label_font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',20)
    for title, ids in pages:
        items = [by_id[t] for t in ids if t in by_id]
        image = Image.new('RGBA',(1280,90+len(items)*55),'#111a23'); d = ImageDraw.Draw(image)
        d.text((24,16),'Built credits font / '+title+' / reconstructed preview',font=label_font,fill='#a9bbc9')
        for i,row in enumerate(items):
            tile = text_image(native, native.atlas, row['text'], 3)
            tile = tile.resize((round(tile.width*.7),42),Image.Resampling.LANCZOS)
            image.alpha_composite(tile,(round(row['x']*2),65+i*55))
        image.convert('RGB').save(FOLDER/(title+'.png'))


def plan():
    FOLDER.mkdir(parents=True,exist_ok=True)
    doc = json.loads(TRANSLATION.read_text(encoding='utf-8'))
    with BASE.open('rb') as f:
        fi, entries = archive(f); _,size,off,_ = next(e for e in entries if e[3] == 4350)
        origin = fi['offset']+off; f.seek(origin); data=f.read(size)
        _,motion_size,motion_off,_ = next(e for e in entries if e[3] == 3823496)
        f.seek(fi['offset']+motion_off); motion = f.read(motion_size)
    _,ma,mz = next(c for c in chunks(motion) if c[0] == b'POLY')
    poly = motion[ma+16:mz]; clip_record = 0x50+6*32
    clip = poly[u32(poly,clip_record+12):][:u32(poly,clip_record+16)]
    channel = u32(clip,20); key = u32(clip,channel+16); payload = u32(clip,key+32)
    require(u32(clip,key+36) == 26 and struct.unpack_from('<4H',clip,payload) == (ROLL_X,1,LINE_HEIGHT,56), 'Roll geometry/font mode/speed preimage')
    _,a,z = next(c for c in chunks(data) if c[0] == b'STUF')
    source = data[a+16:z]; p = parts(source)
    font,texture,font_report = font_assets(p[2],p[1])
    table,lines = translated_table(p[3],font,doc)
    rebuilt = rebuild_bundle(source[:u32(source,4)],{1:texture,2:font,3:table})
    require(len(rebuilt) <= len(source), 'Translated credits exceed original allocation')
    after = rebuilt+bytes(len(source)-len(rebuilt))
    newparts = parts(after)
    require(set(newparts) == set(p), 'STUF resources changed')
    for rid in p:
        if rid not in (1,2,3): require(p[rid] == newparts[rid], 'Other credits asset changed')
    require(len(after) == len(source), 'Chunk extent changed')
    final = data[:a+16]+after+data[z:]
    require(chunks(final) == chunks(data), 'Chunk chain changed')
    font_map(newparts[2]); parse_table(newparts[3])
    require(newparts[1] == texture and newparts[2][:len(font)] == font and newparts[3][:len(table)] == table, 'Rebuilt font/text mismatch')
    previews(newparts[2],newparts[1],lines)
    summary = dict(font=font_report, translated_rows=len(lines), graphic_rows_preserved=9,
                   row_slots= parse_table(table)[2], english_target_rows=323,
                   provisional_names=[r for r in lines if r['status']=='provisional_romanization'],
                   original_chunk_bytes=len(source), rebuilt_bundle_bytes=len(rebuilt),
                   centering=dict(origin_x=ROLL_X, center_x=CENTER, line_height=LINE_HEIGHT, safe_x=[80,560]),
                   row_ids_and_blank_rows_preserved=True, logo_assets_and_commands_preserved=True,
                   timing_dialogue_lyrics_and_other_fonts_unchanged=True, texture_replacement_required=False,
                   runtime_verified=False)
    (FOLDER/'layout.json').write_text(json.dumps(dict(summary=summary,lines=lines),indent=2)+'\n',encoding='utf-8')
    return [dict(offset=origin+a+16,before=source,after=after)],summary,None


if __name__ == '__main__':
    writer.VERSION,writer.BASE,writer.OUTPUT,writer.BASE_HASH = VERSION,BASE,OUTPUT,BASE_HASH
    writer.plan = plan
    writer.main()
