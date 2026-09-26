"""0.1.38: shared confirmation buttons and model parameter display names.

Default is a read-only plan. --write repacks verified twins and builds the ISO.
"""
import argparse
import json
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from build_ui_patch import ROOT, require
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts, controls
from build_history_patch import chunks
from build_combat_ui_patch import compact
from build_shouts_patch import game_lookup
from packed_resource import is_packed, pack, unpack
from ui_font import measure_text
import build_dialogue_patch as builder

VERSION='0.1.38'
BASE=ROOT/'work/output/ACE3-English-0.1.37.iso'
OUTPUT=ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
INPUT=ROOT/'work/translation/en'
PROMPTS={90202:96,101032:96,103000:925792,4000000:96}


def patch_names(data, rows):
    fields=[(a,b) for tag,a,b in chunks(data) if tag==b'PRM\0']
    require(len(fields)==len(rows),'PRM field count changed')
    out=bytearray(data); edits=[]
    for (a,b),row in zip(fields,rows):
        require(b-a==2176,'Unexpected PRM extent')
        raw=data[a+16:a+48]
        require(raw.split(b'\0')[0].decode('cp932')==row['source'],'PRM source mismatch')
        target=row['en'].encode('cp932')
        require(len(target)<=31 and b'\0' not in target,'PRM name exceeds fixed field')
        new=target+b'\0'+b' '*(31-len(target))
        if raw!=new:
            out[a+16:a+48]=new
            edits.append({'offset':a+16,'size':32,'source':row['source'],'en':row['en']})
    # Explicitly prove that stats, scripts and every non-name byte are untouched.
    cursor=0
    for e in edits:
        require(out[cursor:e['offset']]==data[cursor:e['offset']],'Non-name byte changed')
        cursor=e['offset']+32
    require(out[cursor:]==data[cursor:] and chunks(out)==chunks(data),'Model structure changed')
    return bytes(out),edits


def packed_copy(data):
    result=pack(data)
    require(unpack(result)[0]==data,'Packed twin round trip failed')
    return result


def plan():
    prompts=json.loads((INPUT/'shared_prompts_038.json').read_text(encoding='utf-8'))
    names=json.loads((INPUT/'parameter_names_038.json').read_text(encoding='utf-8'))
    require(prompts['review']['status']=='meaning_reviewed','Unreviewed prompts')
    require(names['review']['complete'] and names['review']['rows_examined']==177,'Incomplete name review')
    groups=defaultdict(list)
    for row in names['rows']:groups[row['resource_id']].append(row)
    require(len(groups)==110 and sum(map(len,groups.values()))==177,'Unexpected name coverage')
    changes={};reports=[];twins={};checks={}
    with BASE.open('rb') as f:
        fi,es=archive(f);entries={rid:(sz,off) for _,sz,off,rid in es}
        def get(rid):
            sz,off=entries[rid];f.seek(fi['offset']+off);return f.read(sz)
        fonts=[parts(get(rid))[2500] for rid in range(1200000,1200008)]
        fonts.append(parts(get(4002053))[2500])
        for row in names['rows']:
            require(max(max(measure_text(font,row['en'])) for font in fonts)<=355,'Name width exceeded')
        targets={r['text_id']:r['en'] for r in prompts['rows']}
        for row in prompts['rows']:
            require(controls(row['source'])==controls(row['en']),'Prompt controls changed')
            require(len(row['en'].split('\n'))<=4,'Prompt line limit')
            require(max(max(measure_text(font,row['en'])) for font in fonts[:8])<=400,'Prompt width')
        for rid,at in PROMPTS.items():
            data=get(rid);table=data[at:at+416]
            rs=parse_table(table)[3]
            require({i:r.decode('cp932') for _,i,_,r in rs}=={r['text_id']:r['source'] for r in prompts['rows']},'Prompt preimage')
            new=compact(table,targets)
            require(all(game_lookup(new,i)==s.encode('cp932') for i,s in targets.items()),'Prompt runtime lookup')
            changes[rid]=data[:at]+new+data[at+416:]
            require(len(changes[rid])==len(data),'Prompt resource grew')
            reports.append({'resource_id':rid,'kind':'shared_prompts','offset':at,'size':416,'rows':8})
        for live,rows in sorted(groups.items()):
            rows.sort(key=lambda r:r['chunk_offset'])
            for rid,twin in ((live,live+2000000),(live-2300000,live+1500000)):
                data=get(rid);new,edits=patch_names(data,rows)
                if new==data:continue
                changes[rid]=new
                require(twin in entries,'Missing packed model twin')
                encoded=get(twin)
                require(is_packed(encoded) and unpack(encoded)[0]==data,'Packed model preimage differs')
                twins[twin]=rid
                reports.append({'resource_id':rid,'kind':'parameter_names','packed_twin':twin,'edits':edits})
        abilities=json.loads((INPUT/'abilities_036.json').read_text(encoding='utf-8'))['rows']
        expected={r['text_id']:r['en'] for r in abilities}
        for rid in (4002050,4002053,4002054,4002057):
            table=parts(get(rid))[3079]
            actual={i:r.decode('cp932') for _,i,_,r in parse_table(table)[3]}
            require(actual==expected,'Inherited ability translations differ')
        checks={'ability_rows_per_copy':len(expected),'ability_copies':4,
                'highlighted_abilities':{i:s for i,s in expected.items() if s in ('Mood','Vital Jump','Organic Energy')},
                'model_rows_per_generation':177,'model_generations':2,'packed_twins':len(twins),
                'changed_model_fields':sum(len(r['edits']) for r in reports if r['kind']=='parameter_names'),
                'shared_prompt_copies':4,'shared_prompt_rows_per_copy':8,
                'uncertain_source_rows':len(names['review']['uncertain_rows'])}
    return changes,reports,twins,checks


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    changes,reports,twins,checks=plan()
    print('DRY RUN',json.dumps(checks),flush=True)
    sample=[r for r in reports if r['resource_id'] in (90202,2801040,501040)]
    print(json.dumps(sample,ensure_ascii=True,indent=2),flush=True)
    if not args.write:return
    require(not OUTPUT.exists(),'Versioned output already exists')
    with ProcessPoolExecutor(max_workers=3) as pool:
        jobs={pool.submit(packed_copy,changes[rid]):twin for twin,rid in twins.items()}
        for n,job in enumerate(as_completed(jobs),1):
            changes[jobs[job]]=job.result()
            if n%10==0:print('Packed and verified',n,'/',len(twins),flush=True)
    builder.VERSION,builder.BASE,builder.OUTPUT=VERSION,BASE,OUTPUT
    builder.build(changes,reports)
    path=OUTPUT.with_suffix('.json');report=json.loads(path.read_text(encoding='utf-8'))
    report['coverage']='Shared confirmation table in all four copies; all 177 playable model parameter names in both model generations and their packed twins.'
    report['checks']=checks
    report['limitations']='Runtime verification pending. Ability labels already English in all four active tables; old save-state or source of screenshot not yet confirmed. Truncated legacy name qualifiers documented in translation review.'
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
