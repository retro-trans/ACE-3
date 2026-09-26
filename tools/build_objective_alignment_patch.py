"""0.1.37: stack pause objectives below their headings; fixed-size edits only.

Dry run first. Inherits 0.1.36 including the English prologue movie.
"""
import argparse
import hashlib
import json
import shutil
import struct
from build_ui_patch import ROOT, require, u32, inner_bnd
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts
from ui_font import measure_text

VERSION='0.1.37'
BASE=ROOT/'work/output/ACE3-English-0.1.36-movie-test.iso'
OUTPUT=ROOT/'work/output/ACE3-English-0.1.37.iso'
INPUT=ROOT/'work/translation/en/objective_fit_037.json'
LEFT=-61.458778381347656
OLD_X=6.661476135253906
OLD_Y=(-157.59591674804688,-157.59591674804688,-135.93191528320312,-115.28092193603516,-77.99185180664062,-77.99185180664062,-56.327850341796875)
SHIFT=(0,24,24,24,24,48,48)
BODY=(1,2,3,5,6)
WIDTH=355


def layout_edits(data,origin,path,rid):
    edits=[]
    if data[:4]==b'BND\0':
        for k,a,b in inner_bnd(data[:u32(data,4)]):
            edits+=layout_edits(data[a:b],origin+a,path+[k],rid)
        return edits
    if len(data)<80 or u32(data,4)!=0x202:return edits
    size,count,start=struct.unpack_from('<I4xII',data)
    require(start==80 and start+count*112<=size<=len(data),'Layout extent')
    bindings=[struct.unpack_from('<h',data,start+i*112+86)[0] for i in range(count)]
    for first in range(count-6):
        if bindings[first:first+7]!=list(range(112,119)):continue
        records=[start+(first+j)*112 for j in range(7)]
        require(all(data[a+85]==4 for a in records),'Objective widget types')
        require(tuple(struct.unpack_from('<f',data,a+4)[0] for a in records)==OLD_Y,'Unexpected objective Y preimage')
        def setf(at,new,kind,**extra):
            old=data[at:at+4];after=struct.pack('<f',new)
            if old!=after:edits.append(dict(offset=origin+at,before=old,after=after,kind=kind,resource_id=rid,path=path,**extra))
        for j,a in enumerate(records):
            require(struct.unpack_from('<f',data,a)[0]==(OLD_X if j in BODY else LEFT),'Unexpected X preimage')
            if j in BODY:setf(a,LEFT,'objective_x',widget=first+j)
            if SHIFT[j]:setf(a+4,OLD_Y[j]+SHIFT[j],'objective_y',widget=first+j)
        # The preceding shape holds the two complete panels, 11 vertices apiece.
        a=start+(first-1)*112
        require(data[a+85]==1,'Expected panel shape')
        n,vertices=struct.unpack_from('<II',data,a+60)
        require(n==22 and vertices+16*n<=size,'Unexpected panel mesh')
        for v in range(n):
            delta=24 if v in (6,7,10) or v>=11 else 0
            if v in (17,18,21):delta+=24
            y=struct.unpack_from('<f',data,vertices+v*16+4)[0]
            require(50<y<184,'Unexpected panel Y preimage')
            if delta:setf(vertices+v*16+4,y+delta,'panel_y',widget=first-1,vertex=v)
    return edits


def plan():
    doc=json.loads(INPUT.read_text(encoding='utf-8'))
    require(doc['review']['status']=='meaning_reviewed','Unreviewed objective fit')
    lookup={r['old']:r['en'] for r in doc['rows']}
    changes={};layouts=[];checked=[];hits={s:0 for s in lookup}
    def add(c):
        at=c['offset']
        if at in changes:require(changes[at]['after']==c['after'],'Conflicting shared string')
        else:changes[at]=c
    with BASE.open('rb') as f:
        fi,es=archive(f)
        def get(e):f.seek(fi['offset']+e[2]);return f.read(e[1])
        fonts=[parts(get(next(e for e in es if e[3]==rid)))[2500] for rid in range(1200000,1200008)]
        def strings(data,at,origin,rid,kind,limited=False):
            for slot,tid,pointer,raw in parse_table(data,at)[3]:
                if limited and tid not in (1,2):continue
                old=raw.decode('cp932');new=lookup.get(old,old)
                if old.isascii() and '<' not in old:
                    width=max(max(measure_text(font,new)) for font in fonts)
                    require(width<=WIDTH,'Objective exceeds panel: '+new)
                    checked.append({'resource_id':rid,'text_id':tid,'text':new,'max_width':width})
                if old not in lookup:continue
                encoded=new.encode('cp932');require(len(encoded)<=len(raw),'Text extent grows')
                require(old.count(' / ')==new.count(' / '),'Condition separator changes')
                add(dict(offset=origin+at+pointer,before=raw+b'\0',after=encoded+bytes(len(raw)+1-len(encoded)),
                         kind=kind,resource_id=rid,text_id=tid,old=old,new=new))
                hits[old]+=1
        def walk(data,origin,rid,path=()):
            if data[:4]!=b'BND\0':return
            for k,a,b in inner_bnd(data[:u32(data,4)]):
                if k==3056:strings(data,a,origin,rid,'catalog_objective')
                elif data[a:a+4]==b'BND\0':walk(data[a:b],origin+a,rid,path+(k,))
        for e in es:
            rid=e[3];origin=fi['offset']+e[2]
            if 1200000<=rid<=1200011 or 4002050<=rid<=4002058:
                d=get(e);walk(d,origin,rid)
                if rid<2000000:
                    found=layout_edits(d,origin,[],rid)
                    if found:layouts.append(rid)
                    for c in found:add(c)
            elif 6000<=rid<=6999 or 2002000<=rid<=2002999 or 3200000<=rid<=3201999:
                d=get(e)
                try:parse_table(d,u32(d,20))
                except (ValueError,struct.error):continue
                strings(d,u32(d,20),origin,rid,'scene_objective',True)
    require(layouts==[1200000,1200001,1200002,1200003,1200005,1200006,1200007],'Missing pause layout variant')
    require(all(hits.values()),'Unused objective fit input')
    ordered=sorted(changes.values(),key=lambda c:c['offset'])
    require(all(a['offset']+len(a['before'])<=b['offset'] for a,b in zip(ordered,ordered[1:])),'Overlapping edits')
    require(all(len(c['before'])==len(c['after']) for c in ordered),'Non-fixed edit')
    return ordered,{'layout_bundles':layouts,'objective_occurrences':hits,'width_checks':checked}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    changes,summary=plan()
    print('DRY RUN',len(changes),'fixed-size edits;',len(summary['layout_bundles']),'layouts;',len(summary['width_checks']),'objective width checks',flush=True)
    print(json.dumps(summary['objective_occurrences'],indent=2),flush=True)
    for c in changes[:5]:print(json.dumps({k:v.hex() if isinstance(v,bytes) else v for k,v in c.items()}),flush=True)
    if not a.write:return
    require(not OUTPUT.exists(),'Output exists');shutil.copyfile(BASE,OUTPUT)
    with OUTPUT.open('r+b') as f:
        for c in changes:
            f.seek(c['offset']);require(f.read(len(c['before']))==c['before'],'Preimage mismatch')
            f.seek(c['offset']);f.write(c['after'])
    digest=hashlib.sha256();index=0;pos=0
    with BASE.open('rb') as src,OUTPUT.open('rb') as dst:
        while True:
            raw=src.read(8<<20)
            if not raw:break
            expected=bytearray(raw)
            while index<len(changes) and changes[index]['offset']<pos+len(raw):
                c=changes[index];at=c['offset']-pos
                require(0<=at and at+len(c['after'])<=len(raw),'Verification chunk boundary')
                expected[at:at+len(c['after'])]=c['after'];index+=1
            actual=dst.read(len(raw));require(actual==expected,'Unexpected disc change')
            digest.update(actual);pos+=len(raw)
        require(not dst.read(1) and index==len(changes),'Size/patch count mismatch')
    report=dict(version=VERSION,base=BASE.name,output=OUTPUT.name,sha256=digest.hexdigest(),size=pos,
                whole_disc_verified=True,runtime_verified=False,inherits_english_prologue_movie=True,summary=summary,
                changes=[{k:v.hex() if isinstance(v,bytes) else v for k,v in c.items()} for c in changes])
    OUTPUT.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('summary','changes')},indent=2),flush=True)


if __name__=='__main__':main()
