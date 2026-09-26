"""Translate the two baked controller diagrams with the game's own glyphs.

Dry-run first. --preview writes review artwork; --write creates a new ISO.
Only indexed pixels inside reviewed caption rectangles can change. Controller
artwork, leader lines, icon, palettes, texture addresses and ISO extents remain.
"""
import argparse
from collections import Counter
import hashlib
import json
import shutil
import struct
from PIL import Image
from build_ui_patch import ROOT, inner_bnd, require, u32
from dialogue_corpus import archive
from dialogue_font import texture_pixels
from ui_font import font_map
from ui_textures import decode

VERSION='0.1.10'
BASE=ROOT/'work/output/ACE3-English-0.1.9.iso'
OUTPUT=ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
EXPECTED_BASE='f9fbb6079caff3f83df7d9db0a646af9f23de0ae4db5d21092113b3455cd4cff'
LAYOUT=ROOT/'work/ui/controller_diagrams.json'
TRANSLATION=ROOT/'work/translation/en/controller_diagrams.json'


def captions(tid):
    layout=json.loads(LAYOUT.read_text(encoding='utf-8'))
    translation=json.loads(TRANSLATION.read_text(encoding='utf-8'))
    require(translation['review']['status']=='meaning_reviewed','Unreviewed captions')
    terms={r['id']:r for r in translation['entries']}
    asset=next(a for a in layout['assets'] if a['texture_id']==tid)
    for row in layout['regions']:
        key=asset['overrides'].get(row['id'],row['id']);term=terms[key]
        yield key,term.get('display',term['target']),row['rectangle'],term['target']


class NativeGlyphs:
    def __init__(self,font,texture):
        self.font=font
        self.mapping,self.start,_=font_map(font)
        w,h,indices=texture_pixels(texture)
        raw=texture[32+u32(texture,4):u32(texture,0)]
        colors=[tuple(raw[i:i+3])+(min(255,raw[i+3]*2),) for i in range(0,64,4)]
        self.atlas=Image.frombytes('RGBA',(w,h),bytes(v for i in indices for v in colors[i]))

    def render(self,text):
        rows=[];width=0
        for c in text:
            require(ord(c) in self.mapping,'Missing native glyph: '+c)
            record=struct.unpack_from('<4f4h',self.font,self.start+24*self.mapping[ord(c)])
            w,h=self.atlas.size
            box=tuple(round(v*s) for v,s in zip(record[:4],(w,h,w,h)))
            rows.append((width+record[4],self.atlas.crop(box)))
            width+=record[6]
        result=Image.new('RGBA',(width+4,24))
        for x,glyph in rows:result.alpha_composite(glyph,(x,0))
        bounds=result.getbbox();require(bounds is not None,'Empty caption')
        return result.crop(bounds)


def translate_texture(original,tid,glyphs):
    require(tid in (50512,50513),'Not a controller diagram')
    require(u32(original,0)==66592 and u32(original,4)==65536 and u32(original,12)==0,
            'Unexpected diagram storage')
    tex=struct.unpack_from('<Q',original,16)[0]
    require((tex>>20)&63==19 and (tex>>26)&15==8 and (tex>>30)&15==8,'Expected 256x256 PSMT8')
    pixels=bytearray(original[32:32+65536]);before=bytes(pixels)
    palette=original[32+65536:66592]
    colors=[]
    for i in range(256):
        j=(i&~24)|((i&8)<<1)|((i&16)>>1)
        r,g,b,a=palette[j*4:j*4+4];colors.append((r,g,b,min(255,a*2)))
    allowed=set();report=[];cache={}
    for key,text,rect,full_meaning in captions(tid):
        x,y,w,h=rect
        require(0<=x<x+w<=256 and 0<=y<y+h<=256,'Caption outside texture')
        positions=[yy*256+xx for yy in range(y,y+h) for xx in range(x,x+w)]
        require(not allowed.intersection(positions),'Caption rectangles overlap')
        allowed.update(positions)
        bg=Counter(before[i] for i in positions).most_common(1)[0][0]
        label=glyphs.render(text)
        # Original art is stretched horizontally on screen. Keep consistent
        # 14-pixel ink height and fit the entire label in its original box.
        target_h=min(14,h-2)
        target_w=min(w,round(label.width*target_h/label.height))
        label=label.resize((target_w,target_h),Image.Resampling.LANCZOS)
        patch=Image.new('RGBA',(w,h),colors[bg])
        patch.alpha_composite(label,(0,(h-target_h)//2))
        for pos,color in zip(positions,patch.getdata()):
            if color not in cache:
                cache[color]=min(range(256),key=lambda j:sum((a-b)**2 for a,b in zip(color,colors[j])))
            pixels[pos]=cache[color]
        report.append({'id':key,'display_text':text,'rectangle':list(rect),
                       'ink_size':[target_w,target_h],'background_index':bg,
                       'full_meaning':full_meaning})
    changed={i for i,(a,b) in enumerate(zip(before,pixels)) if a!=b}
    require(changed<=allowed,'Artwork outside caption rectangles changed')
    result=original[:32]+bytes(pixels)+original[32+65536:]
    require(len(result)==len(original) and result[:32]==original[:32] and
            result[32+65536:]==original[32+65536:],'Texture metadata or palette changed')
    return result,{'texture_id':tid,'scheme':'Shift' if tid==50512 else 'Select',
                   'captions':report,'changed_pixels':len(changed),
                   'original_sha256':hashlib.sha256(original).hexdigest(),
                   'patched_sha256':hashlib.sha256(result).hexdigest()}


def plan():
    with BASE.open('rb') as f:
        fi,entries=archive(f)
        def bundle(rid):
            _,size,offset,_=next(e for e in entries if e[3]==rid)
            f.seek(fi['offset']+offset);d=f.read(size)
            return fi['offset']+offset,d,{r:(a,z) for r,a,z in inner_bnd(d)}
        _,donor,dr=bundle(4002050)
        glyphs=NativeGlyphs(donor[slice(*dr[2500])],donor[slice(*dr[2000])])
        base,data,resources=bundle(4002056)
        changes=[]
        for tid in (50512,50513):
            a,z=resources[tid];original=data[a:z]
            patched,report=translate_texture(original,tid,glyphs)
            changes.append({'offset':base+a,'before':original,'after':patched,'report':report})
        return changes


def verify_disc(changes):
    base_hash=hashlib.sha256();output_hash=hashlib.sha256();size=0
    with BASE.open('rb') as a,OUTPUT.open('rb') as b:
        while True:
            raw=a.read(8*1024*1024)
            if not raw:break
            expected=bytearray(raw);base_hash.update(raw)
            for c in changes:
                lo=max(size,c['offset']);hi=min(size+len(raw),c['offset']+len(c['after']))
                if lo<hi:expected[lo-size:hi-size]=c['after'][lo-c['offset']:hi-c['offset']]
            actual=b.read(len(raw));require(actual==expected,'Unexpected disc byte change')
            output_hash.update(actual);size+=len(raw)
        require(not b.read(1),'Disc size changed')
    require(base_hash.hexdigest()==EXPECTED_BASE,'Unexpected base ISO')
    return base_hash.hexdigest(),output_hash.hexdigest(),size


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--preview',action='store_true');ap.add_argument('--write',action='store_true')
    args=ap.parse_args();changes=plan()
    for c in changes:print(json.dumps({'iso_offset':c['offset'],**c['report']},indent=2))
    print('DRY RUN: 2 fixed-size textures; 22 caption occurrences; native game font; artwork outside text boxes unchanged')
    if args.preview:
        folder=ROOT/'work/ui/assets/translated/0.1.10';folder.mkdir(parents=True,exist_ok=True)
        for c in changes:
            img=decode(c['after']);tid=c['report']['texture_id']
            img.save(folder/('%d.png'%tid))
            img.resize((400,256),Image.Resampling.LANCZOS).save(folder/('%d_display.png'%tid))
    if not args.write:return
    require(not OUTPUT.exists(),'Output exists')
    shutil.copyfile(BASE,OUTPUT)
    with OUTPUT.open('r+b') as f:
        for c in changes:
            f.seek(c['offset']);require(f.read(len(c['before']))==c['before'],'Preimage mismatch')
            f.seek(c['offset']);f.write(c['after'])
    base_hash,output_hash,size=verify_disc(changes)
    report={'version':VERSION,'base':BASE.name,'base_sha256':base_hash,'output':OUTPUT.name,
            'sha256':output_hash,'size':size,'whole_disc_verified':True,'runtime_verified':False,
            'bundle_id':4002056,'native_font_source':[4002050,2500,2000],
            'meaning_review':'review_controller_010; 22 occurrences / 13 distinct captions',
            'unchanged_related_assets':[50514,50515,50516,50517],
            'changes':[{'iso_offset':c['offset'],**c['report']} for c in changes]}
    OUTPUT.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    manifest={'version':VERSION,'base_sha256':base_hash,'output_sha256':output_hash,
              'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in (LAYOUT,TRANSLATION,ROOT/'tools/build_controller_patch.py',ROOT/'tools/ui_textures.py',ROOT/'tools/dialogue_font.py')}}
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('BUILT',OUTPUT,output_hash)


if __name__=='__main__':main()
