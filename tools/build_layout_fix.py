"""Build 0.1.9: increase real UI layout allocations; remove ineffective hooks."""
import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path
from build_ui_patch import ROOT, iso_files, require, u32
from dialogue_corpus import archive
from ui_capacity import SITES, replacement

VERSION='0.1.9'
BASE=ROOT/'work/output/ACE3-English-0.1.8.iso'
OUTPUT=ROOT/'work/output/ACE3-English-0.1.9.iso'
CAPACITY=128
TEXT_TYPES=(4,10,11,12)


def layout_changes(data, origin=0, path=()):
    """Walk bounded nested BNDs and validated version-0x202 UI records."""
    changes=[]
    if len(data)>=32 and data[:4]==b'BND\0':
        size,count=u32(data,4),u32(data,8)
        require(16+count*8<=size<=len(data),'Invalid nested BND')
        rows=[struct.unpack_from('<II',data,16+i*8) for i in range(count)]
        for i,(rid,start) in enumerate(rows):
            end=rows[i+1][1] if i+1<count else size
            require(16+count*8<=start<end<=size,'Invalid nested extent')
            changes.extend(layout_changes(data[start:end],origin+start,path+(rid,)))
    elif len(data)>=80 and u32(data,4)==0x202:
        size,count,start=u32(data,0),u32(data,8),u32(data,12)
        require(start==0x50 and start+count*112<=size<=len(data),'Unknown layout records')
        for i in range(count):
            at=start+i*112
            if data[at+0x55] not in TEXT_TYPES:continue
            old=struct.unpack_from('<H',data,at+0x62)[0]
            require(old<=255,'Capacity is not a byte-sized glyph allocation')
            if old>=CAPACITY:continue
            changes.append({'offset':origin+at+0x62,'before':struct.pack('<H',old),
                            'after':struct.pack('<H',CAPACITY),'kind':'layout_text_capacity',
                            'path':list(path),'widget':i,'binding':struct.unpack_from('<h',data,at+0x56)[0],
                            'old_capacity':old or 32,'capacity':CAPACITY})
    return changes


def plan():
    changes=[]
    with BASE.open('rb') as f:
        fi,entries=archive(f)
        for _,size,offset,rid in entries:
            if not (1200000<=rid<=1200011 or 4002050<=rid<=4002058):continue
            f.seek(fi['offset']+offset);data=f.read(size)
            changes.extend(layout_changes(data,fi['offset']+offset,(rid,)))
        exe=next(v for k,v in iso_files(f).items() if k.endswith('/SLPS_257.84'))
        f.seek(exe['offset']);elf=f.read(exe['size'])
        phoff=u32(elf,28);phsize,phcount=struct.unpack_from('<HH',elf,42)
        segments=[struct.unpack_from('<8I',elf,phoff+i*phsize) for i in range(phcount)]
        for site in SITES:
            seg=next(s for s in segments if s[0]==1 and s[2]<=site['va']<s[2]+s[4])
            off=seg[1]+site['va']-seg[2]
            require(elf[off:off+20]==replacement(),'Unexpected old capacity hook')
            changes.append({'offset':exe['offset']+off,'before':replacement(),
                            'after':struct.pack('<5I',*site['words']),
                            'kind':'restore_original_callback','virtual_address':site['va']})
    changes.sort(key=lambda c:c['offset'])
    require(all(a['offset']+len(a['after'])<=b['offset'] for a,b in zip(changes,changes[1:])),
            'Overlapping changes')
    return changes


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    changes=plan()
    print('DRY RUN:',len(changes),'fixed-size patches')
    counts={}
    for c in changes:
        if c['kind']=='layout_text_capacity':counts[c['path'][0]]=counts.get(c['path'][0],0)+1
    print('Widget counts by bundle:',json.dumps(counts))
    samples=[c for c in changes if c.get('path') in ([4002050,32,0],[1200000,5,0])][:14]
    for c in samples:print(json.dumps({k:v for k,v in c.items() if k not in ('before','after')}))
    if not args.write:return
    require(not OUTPUT.exists(),'Output exists')
    shutil.copyfile(BASE,OUTPUT)
    with OUTPUT.open('r+b') as f:
        for c in changes:
            f.seek(c['offset']);require(f.read(len(c['before']))==c['before'],'Preimage mismatch')
            f.seek(c['offset']);f.write(c['after'])
    # Verify the entire disc against the base plus exactly the planned edits.
    digest=hashlib.sha256();base_hash=hashlib.sha256();index=0
    with BASE.open('rb') as a,OUTPUT.open('rb') as b:
        pos=0
        while True:
            raw=a.read(8*1024*1024)
            if not raw:break
            expected=bytearray(raw);base_hash.update(raw)
            while index<len(changes) and changes[index]['offset']<pos+len(raw):
                c=changes[index];at=c['offset']-pos
                require(0<=at and at+len(c['after'])<=len(raw),'Patch straddles verification chunk')
                expected[at:at+len(c['after'])]=c['after'];index+=1
            actual=b.read(len(raw));require(actual==expected,'Disc verification failed');digest.update(actual);pos+=len(raw)
        require(not b.read(1),'Output size changed')
    report={'version':VERSION,'base':BASE.name,'output':OUTPUT.name,'sha256':digest.hexdigest(),
            'base_sha256':base_hash.hexdigest(),'size':OUTPUT.stat().st_size,
            'whole_disc_verified':True,'runtime_verified':False,'widget_counts':counts,
            'changes':[{k:(v.hex() if isinstance(v,bytes) else v) for k,v in c.items()} for c in changes]}
    OUTPUT.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='changes'},indent=2))


if __name__=='__main__':main()
