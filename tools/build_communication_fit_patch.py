"""0.1.39: keep communication dialogue in three visible lines; Purchasable notices.

Default dry-run. The <on()> bottom window has three body lines, unlike <op()>
HUD chatter. Never remove a glossary link to hide overflowing linked text.
"""
import argparse
import hashlib
import json
import struct
from collections import Counter
from build_ui_patch import ROOT,require,u32
from dialogue_corpus import archive,parse_table,INDEX
from build_flight_save_patch import parts
from build_intermission_patch import replace_rows
from build_scene_patch import wrap_words
from ui_font import measure_text
import build_dialogue_patch as builder

VERSION='0.1.39'
BASE=ROOT/'work/output/ACE3-English-0.1.38.iso'
OUTPUT=ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
INPUT=ROOT/'work/translation/en/dialogue_fit_039.json'
WIDTH,LINES=460,3


def communication(text):
    return '<on()>' in text and '<sp(' in text


def links(text):
    return builder.re.findall(r'<book\((\d+)\)>(.*?)<endbook\(\)>',text,flags=builder.re.S)


def reflow(text,font):
    out=wrap_words(text.replace('\n',' '),font,WIDTH,LINES)
    require(out.split()==text.split(),'Reflow changed words')
    return out


def relocate(data,mappings):
    old=u32(data,20);size=parse_table(data,old)[0]
    table=replace_rows(data[old:old+size],mappings)
    at=builder.align(len(data),32)
    out=bytearray(data+bytes(at-len(data))+table)
    struct.pack_into('<I',out,20,at)
    require(out[:20]==data[:20] and out[24:len(data)]==data[24:],'Scene script changed')
    return bytes(out),at


def plan():
    doc=json.loads(INPUT.read_text(encoding='utf-8'))
    require(doc['review']['rows_reviewed']==doc['review']['rows_in_scope']==15 and len(doc['rows'])==15,'Incomplete meaning review')
    edits={r['id']:r for r in doc['rows']}
    require(all(r['status']=='meaning_reviewed' for r in edits.values()),'Unreviewed wording')
    idx=json.loads(INDEX.read_text(encoding='utf-8'))['rows']
    lookup={(o['resource_id'],o['text_id']):r['id'] for r in idx for o in r['occurrences']}
    changes={};reports=[];review_used=set();audit=Counter();outrows=[];notice=[]
    with BASE.open('rb') as f:
        fi,es=archive(f);entries={rid:(sz,off) for _,sz,off,rid in es}
        def get(rid):
            size,off=entries[rid];f.seek(fi['offset']+off);return f.read(size)
        fonts=[parts(get(rid))[2500] for rid in range(1200000,1200008)]
        for rid in sorted(r for r in entries if 2002000<=r<2003000):
            data=get(rid)
            try:rows=parse_table(data,u32(data,20))[3]
            except ValueError:continue
            targets={}
            for slot,tid,_,raw in rows:
                text=raw.decode('cp932')
                if not communication(text):continue
                audit['communication_rows']+=1
                if len(text.split('\n'))<=LINES:continue
                rowid=lookup[(rid,tid)]
                if rowid in edits:
                    draft=edits[rowid]['target'];review_used.add(rowid)
                    target=wrap_words(draft,font=fonts[0],width=WIDTH,lines=LINES)
                    kind='meaning_reviewed_fit'
                else:
                    target=reflow(text,fonts[0]);kind='line_breaks_only'
                require(builder.TOKEN.findall(target)==builder.TOKEN.findall(text),'Control sequence changed: '+rowid)
                require(links(target)==links(text),'Glossary link ID or label changed: '+rowid)
                widths=[max(measure_text(font,builder.TOKEN.sub('',target))) for font in fonts]
                require(max(widths)<=WIDTH,'Dialogue width exceeded: '+rowid)
                require(len(target.split('\n'))<=LINES,'Hidden dialogue line')
                targets[tid]=(slot,text,target)
                audit[kind]+=1
                outrows.append({'id':rowid,'resource_id':rid,'text_id':tid,'before':text,'target':target,'kind':kind,'max_width':max(widths)})
            if not targets:continue
            n=rid-2002000
            for copy in (6000+n,rid,3200000+n,3201000+n):
                before=get(copy);current={i:(s,r.decode('cp932')) for s,i,_,r in parse_table(before,u32(before,20))[3]}
                mappings={}
                for tid,(_,old,new) in targets.items():
                    slot,actual=current[tid];require(actual==old,'Scene copy differs: '+str((copy,tid)))
                    mappings[slot]=(actual,new)
                after,at=relocate(before,mappings);changes[copy]=after
                for _,_,_,raw in parse_table(after,at)[3]:
                    text=raw.decode('cp932')
                    require(not communication(text) or len(text.split('\n'))<=LINES,'Remaining hidden line in copy')
                reports.append({'resource_id':copy,'kind':'communication_fit','original_size':len(before),'old_table_offset':u32(before,20),
                    'new_table_offset':at,'text_ids':sorted(targets),'rows':len(targets)})
        require(review_used==set(edits),'Unused reviewed row')
        require(audit['line_breaks_only']==99 and audit['meaning_reviewed_fit']==15,'Unexpected overflow inventory')
        roster=get(100204);n=struct.unpack_from('<H',roster)[0]
        ids=[struct.unpack_from('<h',roster,8+i*64)[0] for i in range(n)]
        for rid in list(range(4002050,4002059))+list(range(1200000,1200012)):
            if rid not in entries:continue
            data=get(rid);p=parts(data)
            if 3069 not in p:continue
            mappings={s:(r.decode('cp932'),'Purchasable: %s') for s,_,_,r in parse_table(p[3069])[3] if r==b'Can add: %s'}
            require(len(mappings)==1,'Unexpected purchase notice template')
            names={i:r.decode('cp932') for _,i,_,r in parse_table(p[3000])[3]}
            expanded=['Purchasable: '+names[i] for i in ids]
            widths=[max(measure_text(p[2500],s)) for s in expanded]
            require(max(widths)<=410 and max(map(len,expanded))<=41,'Purchasable notice does not fit')
            require(max(len(s.encode('cp932')) for s in expanded)<=63,'Notice record overflow')
            newtable=replace_rows(p[3069],mappings)
            changes[rid]=builder.rebuild_bundle(data,{3069:newtable})
            require(all(v==parts(changes[rid])[k] for k,v in p.items() if k!=3069),'Unrelated menu changed')
            notice.append({'resource_id':rid,'expansions_checked':len(expanded),'max_width':max(widths),'max_chars':max(map(len,expanded))})
            reports.append({'resource_id':rid,'kind':'purchasable_notice','table_id':3069,'rows':1})
        require(len(notice)==3,'Unexpected notice copies')
    summary={'dialogue_audit':dict(audit),'changed_scene_copies':sum(r['kind']=='communication_fit' for r in reports),
        'dialogue_instances':sum(r['rows'] for r in reports if r['kind']=='communication_fit'),'notice_checks':notice,
        'body_lines':LINES,'body_width':WIDTH}
    return changes,reports,summary,outrows


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    changes,reports,summary,rows=plan()
    print('DRY RUN',json.dumps(summary),flush=True)
    for r in rows:
        if r['id'] in ('dialogue_00823','dialogue_00833'):print(json.dumps(r,indent=2),flush=True)
    if not a.write:return
    require(not OUTPUT.exists(),'Output already exists')
    record=ROOT/'work/translation/en/communication_reflow_039.json'
    record.write_text(json.dumps({'version':VERSION,'rows':rows,'summary':summary},indent=2)+'\n',encoding='utf-8')
    builder.VERSION,builder.BASE,builder.OUTPUT=VERSION,BASE,OUTPUT
    builder.build(changes,reports)
    path=OUTPUT.with_suffix('.json');doc=json.loads(path.read_text(encoding='utf-8'))
    doc['coverage']='Fix all 114 four-line communication-window rows in all four scene copies; three Purchasable notice templates.'
    doc['checks']=summary
    doc['inputs']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (INPUT,record)}
    path.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
