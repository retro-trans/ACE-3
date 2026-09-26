"""Translate the complete deployment UI while retaining bounded allocations."""
import argparse
import hashlib
import json
import re
import struct
from collections import Counter
from build_ui_patch import ROOT, require, u32
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts, controls, wrap
from build_intermission_patch import replace_rows, FORMAT
from build_hangar_fix import layouts, capacity_bound
from ui_font import measure_text, font_map, codepoint
import build_dialogue_patch as builder

VERSION='0.1.17'
BASE=ROOT/'work/output/ACE3-English-0.1.16.iso'
OUTPUT=ROOT/'work/output/ACE3-English-0.1.17.iso'
INPUT=ROOT/'work/translation/en/deployment_017.json'


def fit(target, source, tid, text_id, font, names):
    require(controls(source)==controls(target),'Control code changed')
    require(source.count('㍻')==target.count('㍻'),'Discount icon changed')
    require(FORMAT.findall(source)==FORMAT.findall(target),'Format arguments changed')
    dialog=tid==3013 and (160<=text_id<=228 or text_id in (390,425))
    if dialog:target=wrap(target,font,410)
    samples=[target]
    if '%' in target and FORMAT.search(target):
        # All strings substitute unit names or shorter restriction messages.
        # Use the widest and longest roster names, plus 10 decimal digits.
        samples=[]
        for name in names:
            sample=FORMAT.sub(lambda m:name if m.group()=='%s' else ('2147483647' if m.group()=='%d' else '%'),target)
            samples.append(sample)
    widths=[max(measure_text(font,s)) for s in samples]
    lines=max(len(s.split('\n')) for s in samples)
    bound=255 if dialog else 128
    require(max(map(len,samples))<=bound,'Capacity exceeded %s/%s: %s'%(tid,text_id,max(map(len,samples))))
    limit=410 if dialog else 620
    if tid in (3022,3072,3093):limit=440
    if tid==3013 and text_id in (9,10,11,12,13,14):limit=94
    if tid==3013 and text_id in (3,4,5,6,7):limit=120
    if tid==3013 and (100<=text_id<=105 or 111<=text_id<=116):limit=92
    require(max(widths)<=limit,'Width exceeded %s/%s: %s > %s: %r'%(tid,text_id,max(widths),limit,target))
    require(not dialog or lines<=9,'Dialog exceeds nine lines: '+str(text_id))
    return target,{'text_id':text_id,'target':target,'max_width':max(widths),'max_expanded_characters':max(map(len,samples)),'lines':lines,'limit':limit}


def plan():
    doc=json.loads(INPUT.read_text(encoding='utf-8'))
    require(doc['review']['status']=='meaning_reviewed','Unreviewed deployment draft')
    drafts={r['text_id']:r for r in doc['rows']}
    series={r['source']:r['en'] for r in doc['series']}
    names_map={r['source']:r['en'] for r in doc['names']}
    pairs=set(); inventory=[]; reports=[]; changes={}
    with BASE.open('rb') as f, next(ROOT.glob('*.iso')).open('rb') as o:
        fi,es=archive(f); oi,oe=archive(o)
        old={rid:(sz,off) for _,sz,off,rid in oe}
        def get(rid):
            _,sz,off,_=next(e for e in es if e[3]==rid);f.seek(fi['offset']+off);return f.read(sz)
        canonical=parts(get(4002050))
        roster=[r.decode('cp932') for _,_,_,r in parse_table(canonical[3000])[3]]
        # Both character count and font width extremes; all names are cheap to check.
        bundles=[]
        for _,size,off,rid in es:
            f.seek(fi['offset']+off);h=f.read(16)
            if h[:4]!=b'BND\0' or not 16<=u32(h,4)<=size:continue
            f.seek(fi['offset']+off);data=f.read(size)
            try:p=parts(data)
            except ValueError:continue
            edits={};tables=[]
            for tid in (3013,3014,3022,3072,3093):
                if tid not in p:continue
                try:rows=parse_table(p[tid])[3]
                except ValueError:continue
                selected={}
                if tid==3013:
                    if rid not in (4002050,4002053,4002057):continue
                    require({i for _,i,_,_ in rows}==set(drafts),'Deployment copy has different IDs')
                    selected={s:(r.decode('cp932'),drafts[i]['en'],i) for s,i,_,r in rows}
                    require(all(source==drafts[i]['source'] for source,_,i in selected.values()),'Different deployment source')
                else:
                    lookup=names_map if tid==3014 else series
                    selected={s:(r.decode('cp932'),lookup[r.decode('cp932')],i) for s,i,_,r in rows if r.decode('cp932') in lookup}
                if not selected:continue
                require(2500 in p,'Missing font for target bundle')
                font=p[2500];mappings={};rr=[]
                for s,(source,target,i) in selected.items():
                    target,record=fit(target,source,tid,i,font,roster)
                    pairs.add((source,target));record['slot']=s;rr.append(record)
                    if source!=target:mappings[s]=(source,target)
                if mappings:edits[tid]=replace_rows(p[tid],mappings)
                tables.append({'table_id':tid,'rows':rr});inventory.append([rid,tid,len(selected)])
            bundles.append((rid,data,p,edits,tables))
        # Recompute only bounds that the NEW translated pairs exceed. Preserve
        # all 0.1.16 reductions and the stock large dialog allocations.
        for rid,data,p,edits,tables in bundles:
            alloc=[]
            if 1200000<=rid<=1200011 or 4002050<=rid<=4002058:
                sz,off=old[rid];o.seek(oi['offset']+off);original=o.read(sz)
                stock={path:cap for path,_,cap in layouts(original)}
                for path,at,cap in layouts(data):
                    bound=capacity_bound(stock[path],pairs)
                    # Stock >=128 dialogs already cover dynamic text. The
                    # corpus envelope applies only to previously repaired labels.
                    if (stock[path] or 32)>=128 or bound<=cap:continue
                    require(bound<=128,'New static label exceeds bounded plan')
                    top=path[0]
                    # Locate the containing top-level resource without depending
                    # on its position after table relocation.
                    from build_ui_patch import inner_bnd
                    start=next(a for k,a,z in inner_bnd(data[:u32(data,4)]) if k==top)
                    chunk=bytearray(edits.get(top,p[top]));struct.pack_into('<H',chunk,at-start,bound);edits[top]=bytes(chunk)
                    alloc.append({'path':list(path),'before':cap,'after':bound})
            if edits:
                changes[rid]=builder.rebuild_bundle(data,edits)
                reports.append({'resource_id':rid,'kind':'deployment_ui','tables':tables,'allocations':alloc,'changed_subresources':sorted(edits)})
    require(sum(tid==3013 for _,tid,_ in inventory)>=3,'Missing shared deployment copies')
    return changes,reports,inventory


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    changes,reports,inventory=plan()
    summary={'resources':len(changes),'tables':inventory,'text_instances':sum(n for _,_,n in inventory),
             'allocation_adjustments':sum(len(r['allocations']) for r in reports)}
    print('DRY RUN',json.dumps(summary))
    for r in reports:
        if r['resource_id']==4002050:
            for table in r['tables']:
                if table['table_id']==3013:
                    for row in table['rows']:
                        if row['text_id'] in (12,14,57,160,175,192):print(json.dumps(row,ensure_ascii=True))
    if not a.write:return
    builder.VERSION,builder.BASE,builder.OUTPUT=VERSION,BASE,OUTPUT
    builder.build(changes,reports)
    path=OUTPUT.with_suffix('.json');doc=json.loads(path.read_text(encoding='utf-8'))
    doc['coverage']=summary
    doc['limitations']='Offline verified. User controls runtime testing. Other pilot names and ability descriptions remain untranslated.'
    path.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
