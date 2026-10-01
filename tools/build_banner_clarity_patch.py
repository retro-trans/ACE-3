"""0.9.8: larger, cleaner briefing banner with a native 128x128 atlas.

Preview/dry-run by default. --write builds and verifies a new local test ISO.
"""
import argparse
import hashlib
import json
import struct
from PIL import Image, ImageDraw, ImageFont
from build_ui_patch import ROOT, require, u32
from dialogue_corpus import archive
from build_flight_save_patch import parts
from build_briefing_banner_patch import CELLS, VERTICES, spans
from ui_textures import decode
import build_dialogue_patch as builder

VERSION='0.9.8'
BASE=ROOT/'work/output/ACE3-English-0.9.7.iso'
OUTPUT=ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_HASH='170671076e253c8a46b8f87fe7abf15a26f843fb639342bab9ebd89f18abaeec'
TEXTURE_HASH='1b276cf1c06152e8e0f8e9eba58fda2889003550db24013a3ceb107535be98e6'
LAYOUT_HASH='0b726e04794ea77915eaa24c9f0a57e751745f33deb0c51c4a332ee61a3e1f18'
BUNDLES=(4002050,4002054,4002057)
FOLDER=ROOT/'work/ui/banner_098'


def paint(texture):
    require(hashlib.sha256(texture).hexdigest()==TEXTURE_HASH,'Banner preimage changed')
    tex0=struct.unpack_from('<Q',texture,16)[0]
    require((tex0>>20)&63==20 and u32(texture,12)==0,'Expected linear PSMT4')
    require((tex0&16383,(tex0>>14)&63)==(13088,2),'Expected texture base/stride')
    require(len(texture)==2144 and u32(texture,4)==2048,'Expected 64x64 atlas')
    source=Image.frombytes('L',(64,64),bytes(v for b in texture[32:2080] for v in (b&15,b>>4)))
    pixels=bytearray(source.resize((128,128),Image.Resampling.NEAREST).tobytes())
    palette=texture[2080:2144]
    alphas=[min(255,palette[i*4+3]*2) for i in range(16)]
    blank=min(range(16),key=lambda i:alphas[i])
    require(alphas[blank]==0,'Transparent palette entry missing')
    for y in range(118):
        for x in range(120):pixels[y*128+x]=blank
    # Render from outlines; the old version accidentally treated the native
    # font's opaque dark outline as white when mapping to this alpha palette.
    font=ImageFont.truetype('C:/Windows/Fonts/ARIALNB.TTF',180)
    mask=Image.new('L',(2200,260));d=ImageDraw.Draw(mask)
    text='BATTLE STATIONS';d.text((8,0),text,font=font,fill=255)
    ink=mask.crop(mask.getbbox()).resize((216,46),Image.Resampling.LANCZOS)
    line=Image.new('L',(224,56));line.paste(ink,(4,5))
    lut=[min(range(16),key=lambda i:abs(alphas[i]-a)) for a in range(256)]
    for n,cell in enumerate(CELLS):
        x0,y0,x1,y1=[v*2 for v in cell]
        crop=line.crop((n*56,0,(n+1)*56,56))
        for j,a in enumerate(crop.tobytes()):pixels[(y0+j//56)*128+x0+j%56]=lut[a]
    old_scaled=source.resize((128,128),Image.Resampling.NEAREST).tobytes()
    require(all(a==b or (i%128<120 and i//128<118) for i,(a,b) in enumerate(zip(old_scaled,pixels))),
            'Bars/brackets artwork changed')
    header=bytearray(texture[:32])
    struct.pack_into('<II',header,0,32+8192+64,8192)
    struct.pack_into('<Q',header,16,(tex0&~((15<<26)|(15<<30)))|(7<<26)|(7<<30))
    raw=bytes(pixels[i]|(pixels[i+1]<<4) for i in range(0,len(pixels),2))
    out=bytes(header)+raw+palette
    require(decode(out).size==(128,128),'Texture dimensions invalid')
    require(out[-64:]==texture[-64:],'Palette changed')
    # TBP 13088..13119 occupies 8192 bytes: ends at the next atlas base 13120.
    require((tex0&16383)*256+8192==13120*256,'Texture memory footprint changed')
    return out


def layout_patch(layout):
    require(hashlib.sha256(layout).hexdigest()==LAYOUT_HASH,'Banner layout preimage')
    a=80+173*112
    require(struct.unpack_from('<4I',layout,a+60)==(32,69568,20,70080),'Banner mesh changed')
    out=bytearray(layout);allowed=set()
    for n,indices in enumerate(VERTICES):
        old=(-112+n*56,-112+(n+1)*56)
        new=(-118+n*59,-118+(n+1)*59)
        for index,x,y,ox,oy in zip(indices,(new[0],new[1],new[0],new[1]),(-20,-20,20,20),
                                   (old[0],old[1],old[0],old[1]),(-14,-14,14,14)):
            at=69568+index*16
            require(struct.unpack_from('<2f',layout,at)==(ox,oy),'Unexpected current banner vertex')
            struct.pack_into('<2f',out,at,x,y);allowed.update(range(at,at+8))
    require(all(a==b or i in allowed for i,(a,b) in enumerate(zip(layout,out))),'Unrelated layout changed')
    require(118<127,'Text overlaps bracket edges')
    return bytes(out)


def preview(before,after):
    canvas=Image.new('RGB',(1000,540),'#111b29');d=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',24)
    for i,(title,texture,scale,width,height) in enumerate([
            ('Current',before,1,224,28),('Larger, cleaner banner',after,2,236,40)]):
        y=20+i*250;d.text((22,y),title,font=font,fill='white')
        bg=Image.new('RGBA',(320,64),(70,20,29,255));bd=ImageDraw.Draw(bg)
        bd.line((0,32,25,32),fill='#c0bac0',width=2);bd.line((295,32,320,32),fill='#c0bac0',width=2)
        for x in [33,287]:bd.line((x,10,x,54),fill='#c0bac0')
        atlas=decode(texture)
        for n,cell in enumerate(CELLS):
            tile=atlas.crop(tuple(v*scale for v in cell)).resize((width//4,height),Image.Resampling.BILINEAR)
            bg.alpha_composite(tile,((320-width)//2+n*(width//4),(64-height)//2))
        canvas.paste(bg.convert('RGB').resize((960,192),Image.Resampling.BILINEAR),(20,y+40))
    canvas.save(FOLDER/'comparison.png')


def plan():
    changes={};reports=[];new=None
    with BASE.open('rb') as f:
        fi,entries=archive(f)
        for rid in BUNDLES:
            _,size,offset,_=next(e for e in entries if e[3]==rid)
            f.seek(fi['offset']+offset);data=f.read(size);p=parts(data)
            require(hashlib.sha256(p[50914]).hexdigest()==TEXTURE_HASH,'Banner copy differs')
            if new is None:new=paint(p[50914]);old=p[50914]
            fixed=layout_patch(parts(p[14])[0])
            # Confirm the neighboring texture boundary in each loading bundle.
            neighbor_id=50611 if rid==4002054 else 50195
            neighbor=struct.unpack_from('<Q',p[neighbor_id],16)[0]&16383
            require(neighbor==(13344 if rid==4002054 else 13120),'Next texture address differs')
            require(13088+8192//256<=neighbor,'Expanded banner exceeds available memory')
            changed_layout=bytearray(p[14]);start,end=spans(p[14])[0]
            require(len(fixed)==end-start,'Layout allocation changed')
            changed_layout[start:end]=fixed
            changes[rid]=builder.rebuild_bundle(data[:u32(data,4)],{14:bytes(changed_layout),50914:new})
            after=parts(changes[rid])
            require(all(after[k]==v for k,v in p.items() if k not in (14,50914)),'Other bundle resource changed')
            reports.append(dict(resource_id=rid,texture_id=50914,layout_id=14,node=173,
                                texture_size=[128,128],text_quad=[-118,-20,118,20],
                                original_text_quad=[-112,-14,112,14],bracket_padding=9,
                                graphics_memory_bytes=8192,graphics_base=13088,
                                next_texture_base=neighbor,main_hd_fonts_preserved=True))
    return changes,reports,old,new


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    FOLDER.mkdir(parents=True,exist_ok=True)
    changes,reports,old,new=plan();preview(old,new)
    (FOLDER/'layout.json').write_text(json.dumps(dict(version=VERSION,copies=reports,runtime_verified=False),indent=2)+'\n')
    print(json.dumps(dict(version=VERSION,bundles=list(changes),preview=str(FOLDER/'comparison.png')),indent=2),flush=True)
    if not args.write:return
    with BASE.open('rb') as f:require(builder.sha_region(f,0,BASE.stat().st_size)==BASE_HASH,'Base ISO mismatch')
    builder.VERSION,builder.BASE,builder.OUTPUT=VERSION,BASE,OUTPUT
    builder.build(changes,reports)
    path=OUTPUT.with_suffix('.json');report=json.loads(path.read_text(encoding='utf-8'))
    report.update(base_sha256=BASE_HASH,coverage='Larger clean Battle Stations banner in all three briefing copies; retains 0.9.7 native HD fonts and earlier fixes.',
                  limitations='Offline atlas/layout and full-disc payload checks passed. In-game banner animation, filtering and graphics-memory behavior remain unverified.')
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
