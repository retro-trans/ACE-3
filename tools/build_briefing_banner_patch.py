"""0.1.67: translate the briefing banner using the game's font and indexed atlas.

Dry-run by default; --preview reconstructs the banner; --write verifies the
entire new disc. Original textures and previews remain local and untracked.
"""
import argparse
import hashlib
import json
import struct
import sys
from PIL import Image
from build_ui_patch import ROOT, require, u32, inner_bnd
from dialogue_corpus import archive
from build_flight_save_patch import parts
from build_controller_patch import NativeGlyphs
from ui_textures import decode
import build_stats_panel_patch as writer

VERSION = '0.1.67'
BASE = ROOT/'work/output/ACE3-English-0.1.66.iso'
BASE_HASH = 'eb84ee5b8a20f4891546ce4059209be838860a7ed128d4efa64cdd7cfdea1618'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
TEXTURE_HASH = 'baab7c2cd190e82979ec866db3243118ae6b6b5e68182341ea5980b5e2ee5f45'
LAYOUT_HASH = '6edac957365d899461e2c1a606b0d31b357a6dcc0b0181f696637aa0b4176549'
BUNDLES = [4002050, 4002054, 4002057]
# Each original kanji is a separate textured quad. Keep the four primitives,
# packing consecutive portions of the English line into their atlas cells.
CELLS = [(4,1,32,29), (32,1,60,29), (4,30,32,58), (32,30,60,58)]
VERTICES = [(9,16,17,15), (3,6,23,5), (8,2,10,4), (20,22,21,7)]


def paint(texture, glyphs, text):
    require(hashlib.sha256(texture).hexdigest() == TEXTURE_HASH, 'Texture preimage')
    require(len(texture) == 2144 and u32(texture,4) == 2048, '4-bit 64x64 atlas')
    palette = texture[2080:2144]
    colors = [tuple(palette[i:i+3])+(min(255,palette[i+3]*2),) for i in range(0,64,4)]
    pixels = bytearray(v for byte in texture[32:2080] for v in (byte&15,byte>>4))
    blank = min(range(16), key=lambda i: colors[i][3])
    require(colors[blank][3] == 0, 'No transparent palette entry')
    # Artwork at x>=60 or y>=59 supplies the animated bars and brackets.
    for y in range(59):
        for x in range(60): pixels[y*64+x] = blank
    line = Image.new('RGBA',(112,28))
    label = glyphs.render(text)
    # Quads double the horizontal resolution on screen; account for this
    # when fitting the native glyphs so the displayed letter proportions hold.
    h = min(24, round(232*label.height/label.width))
    w = min(108, round(label.width*h/label.height/2))
    label = label.resize((w,h),Image.Resampling.LANCZOS)
    line.alpha_composite(label,((112-w)//2,(28-h)//2))
    cache = {}
    for n,(x0,y0,x1,y1) in enumerate(CELLS):
        crop = line.crop((n*28,0,(n+1)*28,28))
        for j,c in enumerate(crop.getdata()):
            if c not in cache:
                # Palette is the original white antialias ramp; alpha matters
                # more than RGB in the transparent parts of the new glyphs.
                cache[c] = min(range(16),key=lambda i: abs(c[3]-colors[i][3]))
            pixels[(y0+j//28)*64+x0+j%28] = cache[c]
    raw = bytes(pixels[i]|(pixels[i+1]<<4) for i in range(0,4096,2))
    result = texture[:32]+raw+palette
    original = bytes(v for b in texture[32:2080] for v in (b&15,b>>4))
    require(all(a==b or (i%64<60 and i//64<59) for i,(a,b) in enumerate(zip(original,pixels))),
            'Border artwork changed')
    require(len(result)==len(texture) and result[:32]==texture[:32] and result[2080:]==texture[2080:],
            'Texture container or palette changed')
    return result


def fit_layout(layout):
    require(hashlib.sha256(layout).hexdigest()==LAYOUT_HASH,'Layout preimage')
    a = 80+173*112
    require(struct.unpack_from('<4I',layout,a+60)==(32,69568,20,70080),'Banner mesh changed')
    result=bytearray(layout);allowed=set()
    def put(at,v):
        struct.pack_into('<f',result,at,v);allowed.update(range(at,at+4))
    for n,indices in enumerate(VERTICES):
        left,right=-112+n*56,-112+(n+1)*56
        for idx,x,y in zip(indices,(left,right,left,right),(-14,-14,14,14)):
            put(69568+idx*16,x);put(69568+idx*16+4,y)
    # Shared UVs follow the original four-cell topology; border UVs 0..3
    # and 16..19 stay untouched. Edges map to texel boundaries.
    uv={4:(60,30),5:(32,30),6:(60,58),7:(32,58),
        8:(60,1),9:(32,1),10:(60,29),11:(32,29),
        12:(4,30),13:(4,58),14:(4,1),15:(4,29)}
    for idx,(u,v) in uv.items():
        put(70080+idx*8,u/64);put(70080+idx*8+4,v/64)
    require(all(x==y or i in allowed for i,(x,y) in enumerate(zip(layout,result))), 'Other mesh changed')
    require(-127 < -112 and 112 < 127, 'Banner overlaps brackets')
    return bytes(result)


def spans(data):
    return {k:(a,b) for k,a,b in inner_bnd(data[:u32(data,4)])}


def plan():
    text=json.loads((ROOT/'work/translation/en/briefing_banner_067.json').read_text(encoding='utf-8'))['target']
    edits=[];copies=[];preview=None
    with BASE.open('rb') as f:
        fi,entries=archive(f)
        for _,size,off,rid in entries:
            f.seek(fi['offset']+off)
            if f.read(4)!=b'BND\0':continue
            f.seek(fi['offset']+off);data=f.read(size)
            try:p=parts(data)
            except ValueError:continue
            if 50914 not in p:continue
            require(rid in BUNDLES,'Unexpected banner copy')
            require(hashlib.sha256(p[50914]).hexdigest()==TEXTURE_HASH,'Banner copy preimage')
            new=preview if preview is not None else paint(p[50914],NativeGlyphs(p[2500],p[2000]),text)
            layout=parts(p[14])[0];fixed=fit_layout(layout)
            s=spans(data);la=spans(p[14])[0][0]
            edits.extend([dict(offset=fi['offset']+off+s[50914][0],before=p[50914],after=new),
                          dict(offset=fi['offset']+off+s[14][0]+la,before=layout,after=fixed)])
            require(preview is None or preview==new,'Banner copies differ')
            preview=new;copies.append(rid)
    require(copies==BUNDLES,'Banner coverage changed')
    edits.sort(key=lambda e:e['offset'])
    require(all(a['offset']+len(a['after'])<=b['offset'] for a,b in zip(edits,edits[1:])), 'Overlapping edits')
    return edits,dict(text=text,bundles=copies,texture_id=50914,layout_id=14,node=173,
                      banner_bounds=[-112,-14,112,14],runtime_verified=False),preview


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--preview',action='store_true');ap.add_argument('--write',action='store_true')
    args=ap.parse_args();edits,report,texture=plan()
    print(json.dumps(report,indent=2),flush=True)
    if args.preview:
        out=ROOT/'work/ui/briefing_banner_067';out.mkdir(exist_ok=True)
        atlas=decode(texture);canvas=Image.new('RGBA',(280,60),(73,21,30,255))
        for n,cell in enumerate(CELLS):
            canvas.alpha_composite(atlas.crop(cell).resize((56,28),Image.Resampling.BILINEAR),(28+n*56,16))
        canvas.resize((840,180),Image.Resampling.NEAREST).save(out/'banner-preview.png')
        (out/'layout.json').write_text(json.dumps(dict(report,atlas_cells=CELLS,vertices=VERTICES),indent=2)+'\n')
    if args.write:
        writer.VERSION,writer.BASE,writer.OUTPUT,writer.BASE_HASH=VERSION,BASE,OUTPUT,BASE_HASH
        writer.plan=lambda:(edits,report,None)
        sys.argv=[sys.argv[0],'--write'];writer.main()


if __name__=='__main__':main()
