"""Pack original glyph bitmaps plus native-size Latin supplements into the font slot."""
import struct
from build_ui_patch import u32, require
from dialogue_font import texture_pixels, encode_pixels
from ui_font import font_map, patch_font, codepoint


def supplement(font, texture, donors, extra_chars=''):
    """Donors are ordered by visual match. Keep every original glyph bitmap.

    Repacking, instead of growing the 1024x512 atlas, stays below the fixed
    palette address in GS memory. Smaller 512-wide fonts use the same proven
    1024-wide slot. Existing UVs are remapped with their exact pixel rectangles.
    """
    original, _ = patch_font(font)
    mapping, start, count = font_map(original)
    ow, oh, pixels = texture_pixels(texture)
    require(oh == 512 and ow in (512,1024), 'Unexpected game font dimensions')
    palette = texture[32 + u32(texture,4):u32(texture,0)]
    colors = [tuple(palette[i:i+4]) for i in range(0,64,4)]
    glyphs = []

    def extract(ft, tx, code=None, index=None):
        fm, fs, _ = font_map(ft)
        if index is None:
            index = fm[code]
        w,h,px = texture_pixels(tx)
        record = struct.unpack_from('<4f4h',ft,fs+index*24)
        x,y,x1,y1 = [round(v*s) for v,s in zip(record[:4],(w,h,w,h))]
        return record[4:], x1-x, y1-y, b''.join(px[j*w+x:j*w+x1] for j in range(y,y1))

    # Decode each atlas once. The helper below uses cached pixel planes.
    def unpack_glyph(ft, mp, gs, txdata, index):
        w,h,px = txdata
        row = struct.unpack_from('<4f4h',ft,gs+index*24)
        x,y,x1,y1 = [round(v*s) for v,s in zip(row[:4],(w,h,w,h))]
        require(0<=x<x1<=w and 0<=y<y1<=h, 'Invalid glyph rectangle')
        return {'metrics':row[4:], 'w':x1-x, 'h':y1-y,
                'pixels':b''.join(px[j*w+x:j*w+x1] for j in range(y,y1))}

    for i in range(count):
        glyphs.append(unpack_glyph(original,mapping,start,(ow,oh,pixels),i))
    prepared=[]
    for label,ft,tx in donors:
        ft=patch_font(ft)[0]
        mp,gs,_=font_map(ft)
        donor_palette=tx[32+u32(tx,4):u32(tx,0)]
        remap=[]
        for i in range(16):
            color=tuple(donor_palette[i*4:i*4+4])
            remap.append(min(range(16),key=lambda j:sum((a-b)**2 for a,b in zip(color,colors[j]))))
        prepared.append((label,ft,mp,gs,texture_pixels(tx),remap))
    additions=[]
    for code in sorted(set(range(32,127)) | {codepoint(c) for c in extra_chars if c!='\n'}):
        if code in mapping:
            continue
        label,ft,mp,gs,txdata,remap=next(d for d in prepared if code in d[2])
        glyph=unpack_glyph(ft,mp,gs,txdata,mp[code])
        glyph['pixels']=bytes(remap[x] for x in glyph['pixels'])
        scale=u32(original,8)/u32(ft,8)
        glyph['metrics']=tuple(round(x*scale) for x in glyph['metrics'][:3])+(glyph['metrics'][3],)
        mapping[code]=len(glyphs)
        glyphs.append(glyph)
        char=bytes([code]).decode('cp932') if code<256 else code.to_bytes(2,'big').decode('cp932')
        additions.append({'character':char,'donor':label,'source_height':u32(ft,8),'glyph':len(glyphs)-1})
    # Height grouping with best-fit decreasing width gives deterministic shelves.
    shelves=[]
    for i in sorted(range(len(glyphs)),key=lambda i:(-glyphs[i]['h'],-glyphs[i]['w'],i)):
        g=glyphs[i]
        possible=[s for s in shelves if s['h']>=g['h'] and s['x']+g['w']<=1024]
        if possible:
            shelf=min(possible,key=lambda s:(s['h']-g['h'],1024-s['x']-g['w']))
        else:
            shelf={'x':0,'h':g['h'],'items':[]};shelves.append(shelf)
        g['x']=shelf['x'];shelf['items'].append(i);shelf['x']+=g['w']
    used_height=sum(s['h'] for s in shelves)
    require(used_height<=512,'Repacked font exceeds fixed GS font slot: '+str(used_height))
    packed=bytearray(1024*512)
    y=0
    for shelf in shelves:
        for i in shelf['items']:
            g=glyphs[i];g['y']=y
            for row in range(g['h']):
                at=(y+row)*1024+g['x']
                packed[at:at+g['w']]=g['pixels'][row*g['w']:(row+1)*g['w']]
        y+=shelf['h']
    ranges=[]
    for code,index in sorted(mapping.items()):
        if ranges and code==ranges[-1][1]+1 and index==ranges[-1][2]+code-ranges[-1][0]:
            ranges[-1][1]=code
        else:ranges.append([code,code,index])
    output=bytearray(original[:32])
    for row in ranges:output.extend(struct.pack('<3I',*row))
    glyph_start=len(output)
    for g in glyphs:
        output.extend(struct.pack('<4f4h',g['x']/1024,g['y']/512,(g['x']+g['w'])/1024,
                                  (g['y']+g['h'])/512,*g['metrics']))
    struct.pack_into('<I',output,4,len(output))
    struct.pack_into('<HH',output,16,len(ranges),len(glyphs))
    struct.pack_into('<I',output,24,glyph_start)
    header=bytearray(texture[:32])
    tex0=struct.unpack_from('<Q',header,16)[0]
    tex0=(tex0 & ~((63<<14)|(15<<26))) | (16<<14) | (10<<26)
    struct.pack_into('<Q',header,16,tex0)
    struct.pack_into('<II',header,0,32+1024*512//2+64,1024*512//2)
    blank=bytes(header)+bytes(1024*512//2)+palette
    result_texture=encode_pixels(blank,packed)
    require(texture_pixels(result_texture)[2]==packed,'Repacked atlas round-trip failed')
    result_map,new_start,_=font_map(output)
    for i,g in enumerate(glyphs):
        actual=unpack_glyph(output,result_map,new_start,(1024,512,packed),i)
        require(actual['pixels']==g['pixels'] and actual['metrics']==g['metrics'], 'Glyph changed during packing')
    require(all(result_map[c]==i for c,i in mapping.items()),'Mapping changed')
    return bytes(output),result_texture,{'original_glyphs_preserved':count,'atlas_size':[1024,512],
                                      'used_height':used_height,'additions':additions}
