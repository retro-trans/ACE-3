"""Build 0.1.15 meeting/briefing translations. Dry-run before --write."""
import argparse,hashlib,json,re,struct
from collections import Counter
from build_ui_patch import ROOT,require,u32
from dialogue_corpus import archive,parse_table
from build_flight_save_patch import parts,controls
from build_intermission_patch import replace_rows
from ui_font import measure_text
import build_dialogue_patch as builder

VERSION='0.1.15'
BASE=ROOT/'work/output/ACE3-English-0.1.14.iso'
OUTPUT=ROOT/'work/output/ACE3-English-0.1.15.iso'
INPUT=ROOT/'work/translation/en/meeting_briefing_015.json'
TAG=re.compile(r'<[^>]*>')
SPEAKERS={'アムロ・レイ':'Amuro Ray','フェイ・ロシュナンテ':'Faye Rochenante','ミスマル・コウイチロウ':'Kouichiro Misumaru'}

def visible(s):return TAG.sub('',s)

def wrap(s,font,width=460):
    # Commands remain attached to their text. Only whitespace is reflowed.
    output='';line=0
    for word in s.split():
        w=measure_text(font,visible(word))[0]
        require(w<=width,'Single word too wide')
        gap=' ' if output else ''
        if line and line+measure_text(font,gap)[0]+w>width:gap='\n';line=0
        output+=gap+word
        line+=(measure_text(font,gap)[0] if gap==' ' else 0)+w
    require(TAG.findall(output)==TAG.findall(s),'Wrapping changed commands')
    require(visible(output).split()==visible(s).split(),'Wrapping changed visible words')
    require(len(output.splitlines())<=3,'Meeting window exceeds three body lines: '+visible(output))
    require(len(visible(output))<=128,'Meeting window exceeds inherited allocation: '+visible(output))
    return output

def relocate_scene(data,table,offset):
    at=builder.align(len(data),32)
    output=bytearray(data+bytes(at-len(data))+table)
    struct.pack_into('<I',output,20,at)
    require(output[:20]==data[:20] and output[24:len(data)]==data[24:],'Scene script modified')
    require(parse_table(output,at)[0]==len(table),'Invalid scene relocation')
    return bytes(output)

def plan():
    doc=json.loads(INPUT.read_text(encoding='utf-8'))
    require(doc['review']['status']=='meaning_reviewed','Unreviewed draft')
    drafts={rid:[r for r in doc['rows'] if r['resource_id']==rid] for rid in {r['resource_id'] for r in doc['rows']}}
    conditions={r['source']:r['en'] for r in doc['conditions']}
    changes,reports={},[]
    with BASE.open('rb') as f:
        fi,es=archive(f)
        def get(e):f.seek(fi['offset']+e[2]);return f.read(e[1])
        menu=parts(get(next(e for e in es if e[3]==4002050)))
        game=parts(get(next(e for e in es if e[3]==1200000)))
        for entry in es:
            rid=entry[3];data=get(entry)
            if data[:4]==b'BND\0':
                try:p=parts(data)
                except ValueError:continue
                edits={};tables=[]
                if rid in drafts:
                    rs=parse_table(p[1])[3];targets={r['slot']:r for r in drafts[rid]}
                    require(set(targets)=={s for s,_,_,_ in rs},'Incomplete scene category')
                    mappings={};rr=[]
                    for s,i,_,raw in rs:
                        r=targets[s];require(hashlib.sha256(raw).hexdigest()==r['source_sha256'],'Scene preimage changed')
                        target=wrap(r['en'],menu[2500]) if s else r['en']
                        require(controls(raw.decode('cp932'))==controls(target),'Scene controls changed')
                        mappings[s]=(raw.decode('cp932'),target)
                        rr.append({'slot':s,'text_id':i,'target':target,'widths':measure_text(menu[2500],visible(target))})
                    edits[1]=replace_rows(p[1],mappings);tables.append({'table_id':1,'rows':rr})
                for tid in (3056,3014):
                    # 4002055 contains the inherited ACE2 campaign tables.
                    if rid not in (4002050,4002052,4002053,4002054,4002057):continue
                    if tid not in p:continue
                    try:rs=parse_table(p[tid])[3]
                    except ValueError:continue
                    lookup=conditions if tid==3056 else SPEAKERS
                    mappings={s:(raw.decode('cp932'),lookup[raw.decode('cp932')]) for s,i,_,raw in rs if raw.decode('cp932') in lookup}
                    if tid==3056:require(len(mappings)==len(rs),'Untranslated objective category member '+str(rid)+': '+repr([r.decode('cp932') for _,_,_,r in rs if r.decode('cp932') not in lookup]))
                    if not mappings:continue
                    rr=[]
                    for s,(source,target) in mappings.items():
                        widths=measure_text(p[2500],target)
                        require(max(widths)<=480 and len(target)<=128,'Shared label exceeds bounds')
                        rr.append({'slot':s,'target':target,'widths':widths})
                    edits[tid]=replace_rows(p[tid],mappings);tables.append({'table_id':tid,'rows':rr})
                if edits:
                    changes[rid]=builder.rebuild_bundle(data,edits)
                    reports.append({'resource_id':rid,'kind':'meeting_briefing_bundle','changed_subresources':sorted(edits),'tables':tables})
            elif len(data)>=48 and u32(data,0)==0x100:
                # Scene victory/defeat labels are IDs 1/2 in the active table.
                at=u32(data,20)
                try:size,_,_,rs=parse_table(data,at)
                except (ValueError,UnicodeError,struct.error):continue
                mappings={s:(r.decode('cp932'),conditions[r.decode('cp932')]) for s,i,_,r in rs if i in (1,2) and r.decode('cp932') in conditions}
                if not mappings:continue
                for _,target in mappings.values():require(max(measure_text(game[2500],target))<=480,'Scene condition too wide')
                table=replace_rows(data[at:at+size],mappings)
                changes[rid]=relocate_scene(data,table,at)
                reports.append({'resource_id':rid,'kind':'scene_conditions','original_table_offset':at,'new_table_offset':u32(changes[rid],20),'rows':[{'slot':s,'target':t} for s,(_,t) in mappings.items()]})
    counts=Counter(t['table_id'] for r in reports for t in r.get('tables',[]))
    require(counts[1]==2 and counts[3056]==3 and counts[3014]==5,'Category copy count changed')
    return changes,reports

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    changes,reports=plan()
    summary={'resources':len(changes),'scene_conditions':sum(r['kind']=='scene_conditions' for r in reports),'bundle_tables':sum(len(r.get('tables',[])) for r in reports),'translated_instances':sum(len(r.get('rows',[]))+sum(len(t['rows']) for t in r.get('tables',[])) for r in reports)}
    print('DRY RUN',json.dumps(summary))
    for r in reports:
        if r['resource_id'] in (4003020,4003481):
            for row in r['tables'][0]['rows']:print(r['resource_id'],row['slot'],repr(visible(row['target'])),row['widths'])
    if not a.write:return
    builder.VERSION,builder.BASE,builder.OUTPUT=VERSION,BASE,OUTPUT
    builder.build(changes,reports)
    path=OUTPUT.with_suffix('.json');doc=json.loads(path.read_text(encoding='utf-8'));doc['coverage']=summary
    doc['limitations']='Other meeting/briefing dialogue, glossary popups and baked thumbnail labels remain Japanese. Runtime not verified. Existing smaller j glyph retained.'
    path.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
    inputs=[INPUT,ROOT/'tools/build_briefing_patch.py',ROOT/'tools/build_intermission_patch.py',ROOT/'tools/build_dialogue_patch.py',ROOT/'work/glossary/meeting_terms_015.json']
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps({'version':VERSION,'base_sha256':'3fbde2017dfa51ba72d1ba7c3bb94362c344f6d197f0c00c1c4457af3c0a66ca','sha256':doc['sha256'],'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}},indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
