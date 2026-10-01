"""0.9.13: draw the CAUTION badge with the existing native HD font atlas.

Replace only the old caption strip in the card panel mesh. Keep the frame
strips and use a second material for seven glyph quads; no text binding,
font replacement, new texture allocation or memory-card behavior change.
"""
import argparse
import hashlib
import json
import struct
from PIL import Image, ImageDraw, ImageFont
from build_ui_patch import ROOT, require, u32
from dialogue_corpus import archive
from build_flight_save_patch import parts
from packed_resource import is_packed
from ui_font import font_map, measure_text
from preview_hd_font import record, text_image
from build_controller_patch import NativeGlyphs
from ui_textures import decode
import build_dialogue_patch as builder

VERSION='0.9.13'
BASE=ROOT/'work/output/ACE3-English-0.9.12.iso'
OUTPUT=ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_HASH='1da2209c1e6a27662a785c45d0aed3307795a22ca999d7cab9d392f9ed1520df'
LAYOUT_HASH='af1338177f21d186c090b73c482a3afd8b4469ba39bc74a8af8fec85feba5278'
BUNDLES=(4002050,4002054,4002057)
FOLDER=ROOT/'work/ui/caution_0913'
TEXT='CAUTION'


def convert(data,font):
    require(hashlib.sha256(data).hexdigest()==LAYOUT_HASH,'Caution mesh preimage')
    node=80+2*112
    require(data[node+84:node+86]==b'\1\1','Expected 3D sprite mesh')
    mc,mp,vc,vp,uc,up,cc,cp=struct.unpack_from('<8I',data,node+52)
    require((mc,vc,uc,cc)==(1,24,19,3),'Caution topology changed')
    flags,texture,sc,sp=struct.unpack_from('<4I',data,mp)
    require((flags,texture,sc)==(0,50101,6),'Shared atlas binding')
    strips=[struct.unpack_from('<4I',data,sp+i*16) for i in range(sc)]
    require(all(s[1]==4 for s in strips),'Expected quad strips')
    removed=data[strips[3][2]:strips[3][2]+16]
    require(removed==bytes.fromhex('0d0b02000e0c02000c0d02000f0e0200'),'Caution strip indices')
    out=bytearray(data)
    def append(raw):
        out.extend(bytes(-len(out)%16));at=len(out);out.extend(raw);return at
    vertices=bytearray(data[vp:vp+vc*16]);uvs=bytearray(data[up:up+uc*8])
    mapping,start,_=font_map(font);scale=16/u32(font,8)
    cursor=-286.5;top,bottom=-60.5,-76.5;depth=struct.unpack_from('<f',data,vp+12*16+4)[0]
    glyph_strips=[];glyph_reports=[]
    for char in TEXT:
        r=record(font,start,mapping[ord(char)])
        left=cursor+r[4]*scale;right=left+r[5]*scale
        vi,ui=len(vertices)//16,len(uvs)//8
        require(vi+3<256 and ui+3<256,'Mesh index capacity')
        for x,z in ((right,bottom),(right,top),(left,bottom),(left,top)):
            vertices.extend(struct.pack('<4f',x,depth,z,1))
        for u,v in ((r[2],r[3]),(r[2],r[1]),(r[0],r[3]),(r[0],r[1])):
            uvs.extend(struct.pack('<2f',u,v))
        indices=b''.join(bytes((vi+i,ui+i,2,0)) for i in range(4))
        glyph_strips.append((0,4,append(indices),0))
        glyph_reports.append(dict(character=char,bounds=[left,-top,right,-bottom],uv=list(r[:4])))
        cursor+=r[6]*scale
    old_strips=[s for i,s in enumerate(strips) if i!=3]
    old_sp=append(b''.join(struct.pack('<4I',*s) for s in old_strips))
    new_sp=append(b''.join(struct.pack('<4I',*s) for s in glyph_strips))
    new_mp=append(struct.pack('<8I',0,50101,len(old_strips),old_sp,0,2000,len(glyph_strips),new_sp))
    new_vp=append(vertices);new_up=append(uvs)
    struct.pack_into('<6I',out,node+52,2,new_mp,len(vertices)//16,new_vp,len(uvs)//8,new_up)
    out.extend(bytes(-len(out)%32));struct.pack_into('<I',out,0,len(out))
    allowed=set(range(4))|set(range(node+52,node+76))
    require(all(a==b or i in allowed for i,(a,b) in enumerate(zip(data,out))),'Unrelated layout bytes changed')
    require(out[cp:cp+cc*4]==data[cp:cp+cc*4],'Mesh colors changed')
    require(cursor < -190,'Caution header exceeds safe area')
    # Read back every active material and its strip/vertex/UV/color indices.
    active=[]
    for m in range(2):
        _,tid,n,ptr=struct.unpack_from('<4I',out,new_mp+m*16)
        for i in range(n):
            _,count,ip,_=struct.unpack_from('<4I',out,ptr+i*16)
            raw=out[ip:ip+count*4]
            require(len(raw)==count*4,'Strip outside layout')
            for j in range(count):
                v,u,c,pad=raw[j*4:j*4+4]
                require(v<len(vertices)//16 and u<len(uvs)//8 and c<cc and pad==0,'Invalid mesh index')
            active.append((tid,bytes(raw)))
    require(len(active)==12 and not any(t==50101 and r==removed for t,r in active),'Old caption still active')
    require([r for t,r in active if t==50101]==[data[s[2]:s[2]+16] for s in old_strips],'Frame strips changed')
    return bytes(out),dict(node=2,original_material=50101,hd_glyph_material=2000,
        label=TEXT,font_height=16,old_cell_height=10.37854,glyphs=glyph_reports,
        old_caption_strip_removed=True,frame_strips_preserved=5,hd_glyph_strips=7,
        left=-286.5,right=cursor,atlas_bytes_changed=False,warning_text_changed=False)


def preview(p):
    old=decode(p[50101]).crop((50,74,93,83)).resize((207,42),Image.Resampling.BILINEAR)
    n=NativeGlyphs(p[2500],p[2000]);new=text_image(n,n.atlas,TEXT,4)
    new=new.resize((round(new.width*16/19),64),Image.Resampling.LANCZOS)
    canvas=Image.new('RGB',(850,290),'#080e13');d=ImageDraw.Draw(canvas)
    title=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',22)
    for y,label,tile in ((12,'Previous image label',old),(145,'HD letters from the existing game font',new)):
        d.text((20,y),label,font=title,fill='#becbd4')
        d.rectangle((25,y+42,38,y+103),fill='#b3b3b3');canvas.paste(tile,(49,y+43),tile)
        d.line((20,y+110,825,y+110),fill='#666666',width=2)
    canvas.save(FOLDER/'comparison.png')


def plan():
    FOLDER.mkdir(parents=True,exist_ok=True)
    changes={};reports=[];sizes=[]
    with BASE.open('rb') as f:
        fi,es=archive(f)
        for rid in BUNDLES:
            _,n,o,_=next(e for e in es if e[3]==rid);sizes.append(n);f.seek(fi['offset']+o);source=f.read(n)
            p=parts(source);layout=parts(p[35])[0];fixed,report=convert(layout,p[2500])
            nested=builder.rebuild_bundle(p[35][:u32(p[35],4)],{0:fixed})
            changed=builder.rebuild_bundle(source[:u32(source,4)],{35:nested})
            q=parts(changed)
            require(all(q[k]==v for k,v in p.items() if k!=35),'Unrelated UI/font/table/texture changed')
            require(parts(q[35])[0]==fixed,'Changed layout readback mismatch')
            changes[rid]=changed;reports.append(dict(bundle=rid,layout=35,**report))
            if rid==BUNDLES[0]:preview(p)
        twins=[]
        for _,n,o,rid in es:
            f.seek(fi['offset']+o);h=f.read(min(n,12))
            if is_packed(h) and struct.unpack_from('>I',h,4)[0] in sizes:twins.append(rid)
        require(not twins,'Packed UI copies require inspection')
    (FOLDER/'layout.json').write_text(json.dumps(dict(version=VERSION,copies=reports,
        matching_packed_bundle_sizes=twins,runtime_verified=False),indent=2)+'\n',encoding='utf-8')
    return changes,reports


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    replacements,reports=plan()
    print(json.dumps(dict(version=VERSION,bundles=list(replacements),label=TEXT,font_height=16,preview=str(FOLDER/'comparison.png')),indent=2),flush=True)
    if not args.write:return
    require(not OUTPUT.exists(),'Output already exists')
    with BASE.open('rb') as f:require(builder.sha_region(f,0,BASE.stat().st_size)==BASE_HASH,'Base ISO hash')
    builder.VERSION,builder.BASE,builder.OUTPUT=VERSION,BASE,OUTPUT
    builder.build(replacements,reports)
    path=OUTPUT.with_suffix('.json');doc=json.loads(path.read_text(encoding='utf-8'))
    doc.update(base_sha256=BASE_HASH,runtime_verified=False,
        coverage='CAUTION card-panel label uses existing native HD glyphs in all three menu copies; frame artwork, warnings and card operations unchanged.',
        limitations='Mesh/index, glyph coverage, resource preservation and disc checks passed. In-game rendering requires testing.')
    path.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
