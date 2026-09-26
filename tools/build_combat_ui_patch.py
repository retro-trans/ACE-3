"""0.1.36: ability/support details, complete command lists, and map unit labels.

Dry run by default. Preserve live scene script offsets and VMD chunk boundaries.
The command-name tables use magic 0 but the same indexed string layout.
"""
import argparse
import hashlib
import json
import re
import struct
from collections import Counter
from build_ui_patch import ROOT, require, u32
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts, controls
from build_history_patch import chunks
from build_intermission_patch import replace_rows
from build_shouts_patch import name_lookups, rebuild_compact, game_lookup
from find_in_resources import tables
from packed_resource import pack, unpack, is_packed
from ui_font import measure_text
import build_dialogue_patch as builder

VERSION = '0.1.36'
BASE = ROOT/'work/output/ACE3-English-0.1.35.iso'
OUTPUT = ROOT/('work/output/ACE3-English-%s.iso' % VERSION)
INPUT = ROOT/'work/translation/en'
BUNDLES = list(range(4002050,4002059))+list(range(1200000,1200012))
JP = re.compile('[\u3040-\u30ff\u4e00-\u9fff]')


def normal(table):
    require(u32(table,0) in (0,65536),'Unexpected table version')
    return b'\0\0\1\0'+table[4:]


def parsed(table):
    return parse_table(normal(table))


def fit(source,target,font,limit=410,max_chars=64):
    require(not JP.search(target),'Japanese target: '+target)
    require(controls(source)==controls(target),'Button/control loss: '+repr((source,target)))
    require('\0' not in target,'Embedded null')
    require(len(target)<=max_chars,'Character capacity: '+target)
    require('\n' not in target,'Multiline label: '+target)
    require(max(measure_text(font,target))<=limit,'Width exceeded: '+target)
    return target


def append(table,mappings):
    result=replace_rows(normal(table),mappings)
    return table[:4]+result[4:]


def compact(table,targets):
    """Pack a table inside its existing extent; coalesce consecutive ID ranges.

    Null slots remain null and IDs are checked against the actual game lookup.
    No executable changes and no moving later VMD/scene data.
    """
    size,ptr,count,rows=parsed(table)
    ids=[]
    for r in range(u32(table,12)):
        _,first,last=struct.unpack_from('<3I',table,28+r*12)
        ids.extend(range(first,last+1))
    ranges=[]
    for slot,tid in enumerate(ids):
        if ranges and tid==ranges[-1][2]+1:ranges[-1][2]=tid
        else:ranges.append([slot,tid,tid])
    newptr=28+12*len(ranges)
    out=bytearray(table[:28]);struct.pack_into('<3I',out,12,len(ranges),count,newptr)
    out+=b''.join(struct.pack('<3I',*r) for r in ranges)+bytes(count*4)
    pool={}
    for slot,tid,_,raw in rows:
        raw=targets.get(tid,raw.decode('cp932')).encode('cp932')
        require(b'\0' not in raw,'Embedded null')
        if raw not in pool:pool[raw]=len(out);out+=raw+b'\0'
        struct.pack_into('<I',out,newptr+slot*4,pool[raw])
    if len(out)>len(table) and len(rows)==1 and count==1:
        out,_=rebuild_compact(normal(table),{rows[0][1]:targets.get(rows[0][1],rows[0][3].decode('cp932'))})
        out=bytearray(table[:4]+out[4:])
    require(len(out)<=len(table),'Fixed table needs %d of %d bytes: %r'%(len(out),len(table),list(targets.values())))
    out+=bytes(len(table)-len(out));struct.pack_into('<I',out,4,len(table));out=bytes(out)
    for tid in ids:
        expected=targets[tid].encode('cp932') if tid in targets else game_lookup(table,tid)
        require(game_lookup(out,tid)==expected,'Runtime lookup mismatch')
    return out


def load_inputs(allow_draft=False):
    docs={n:json.loads((INPUT/(n+'_036.json')).read_text(encoding='utf-8')) for n in ('abilities','commands','map_names')}
    for n,d in docs.items():require(allow_draft or d['review']['status']=='meaning_reviewed','Unreviewed '+n)
    return docs


def plan(allow_draft=False,repack=True):
    docs=load_inputs(allow_draft)
    abilities={r['source']:r['en'] for r in docs['abilities']['rows']}
    commands={r['source']:r['en'] for r in docs['commands']['rows']}
    inputs={r['source']:r['en'] for r in docs['commands']['input_rows']}
    names={r['source']:r['en'] for c in docs['map_names']['categories'] for r in c['rows']}
    names.update({r['source']:r['en'] for r in docs['map_names']['scene_labels']})
    names.update({r['source']:r['en'] for r in docs['map_names'].get('model_variants',[])})
    names['？？？']='???'
    unitnames,pilots=name_lookups()
    allnames=dict(unitnames);allnames.update(pilots);allnames.update(names)
    changes={};reports=[];coverage=Counter();unknown=[]
    with BASE.open('rb') as f:
        fi,es=archive(f);entries={rid:(sz,off) for _,sz,off,rid in es}
        def get(rid):
            sz,off=entries[rid];f.seek(fi['offset']+off);return f.read(sz)
        menu=parts(get(4002053))[2500];game=parts(get(1200000))[2500]

        def walk(data,rid,path=()):
            if data[:4]==b'BND\0':
                edits={}
                for k,v in parts(data).items():
                    new=walk(v,rid,path+(k,))
                    if new!=v:edits[k]=new
                return builder.rebuild_bundle(data[:u32(data,4)],edits) if edits else data
            try:rs=parsed(data)[3]
            except (ValueError,struct.error):return data
            lookup=None;kind=None;limit=410
            if path==(3079,):lookup=abilities;kind='abilities';limit=280
            elif path in ((3023,),(3020,)) and any('押しながら' in r.decode('cp932') for _,_,_,r in rs):lookup=inputs;kind='command_inputs'
            elif len(path)==2 and path[0]==3049:lookup=commands;kind='commands'
            elif len(path)==1 and path[0] in (3061,3062,3063):lookup=allnames;kind='map_indexes';limit=280
            if lookup is None:return data
            mappings={}
            for s,i,_,raw in rs:
                source=raw.decode('cp932')
                if source not in lookup:
                    if JP.search(source):unknown.append((rid,path,i,source))
                    continue
                target=lookup[source]
                # Placeholder descriptions are stock developer stubs, not active field labels.
                cap=128 if kind=='abilities' and 51<=i<=75 else 64
                width=620 if kind=='abilities' and 51<=i<=75 else limit
                fit(source,target,game if rid<2000000 else menu,width,cap)
                if target!=source:mappings[s]=(source,target)
            if not mappings:return data
            coverage[kind]+=len(mappings)
            reports.append({'resource_id':rid,'path':list(path),'kind':kind,'rows':len(mappings)})
            return append(data,mappings)

        for rid in BUNDLES:
            if rid not in entries:continue
            before=get(rid);after=walk(before,rid)
            if after!=before:changes[rid]=after

        # Mission singleton name tables remain at exactly the same script offsets.
        # Four live resource copies: 60xx, 20020xx, 32000xx, 32010xx.
        for rid in entries:
            scene_id=rid if 2002000<=rid<=2002999 else rid+1996000 if 6000<=rid<=6999 else rid-1198000 if 3200000<=rid<=3200999 else rid-1199000 if 3201000<=rid<=3201999 else None
            if scene_id is None or not (2002010<=scene_id<=2002359 or 2002420<=scene_id<=2002469):continue
            before=get(rid);after=bytearray(before);edits=[]
            for at,size,rs in tables(before):
                if len(rs)!=1 or rs[0][1]!=1 or size>80:continue
                source=rs[0][3].decode('cp932')
                if not JP.search(source) and source!='？？？':continue
                if source not in allnames:unknown.append((rid,[at],1,source));continue
                target=allnames[source];fit(source,target,game,280,64)
                new=compact(before[at:at+size],{1:target})
                after[at:at+size]=new;edits.append({'offset':at,'size':size,'source':source,'target':target})
            if edits:
                changes[rid]=bytes(after);coverage['scene_labels']+=len(edits)
                reports.append({'resource_id':rid,'kind':'scene_labels','edits':edits})

        # Original per-unit CLM command lists and titles, including their packed twins.
        # These are older model copies; live 28xxxxx models use the shared UI lists.
        for rid in sorted(r for r in entries if 500000<=r<600000):
            before=get(rid)
            if before[:4]!=b'VMD\0':continue
            try:cs=chunks(before)
            except ValueError:continue
            after=bytearray(before);edits=[]
            for tag,a,b in cs:
                if tag not in (b'CLM\0',b'FNM\0'):continue
                table=before[a+16:b]
                try:rs=parsed(table)[3]
                except ValueError:continue
                lookup=commands if tag==b'CLM\0' else allnames
                targets={}
                for _,i,_,raw in rs:
                    source=raw.decode('cp932')
                    if source not in lookup:
                        if JP.search(source):unknown.append((rid,[tag.decode('ascii')],i,source))
                        continue
                    target=lookup[source];fit(source,target,game,410,64)
                    if target!=source:targets[i]=target
                if targets:
                    new=compact(table,targets);after[a+16:b]=new
                    edits.append({'tag':tag.decode('ascii').rstrip('\0'),'offset':a+16,'size':b-a-16,'rows':len(targets)})
                    coverage['model_commands' if tag==b'CLM\0' else 'model_titles']+=len(targets)
            if not edits:continue
            after=bytes(after);require(len(after)==len(before),'VMD length changed');changes[rid]=after
            report={'resource_id':rid,'kind':'model_labels','edits':edits}
            twin=rid+3800000
            if twin in entries:
                packed=get(twin);require(is_packed(packed),'Twin not packed')
                require(unpack(packed)[0]==before,'Packed twin preimage differs')
                if repack:
                    encoded=pack(after);require(unpack(encoded)[0]==after,'Packed twin round trip')
                    changes[twin]=encoded
                report['twin']=twin;coverage['packed_twins']+=1
            reports.append(report)
            if coverage['packed_twins'] and coverage['packed_twins']%20==0:
                print('Checked model command copies:',coverage['packed_twins'],flush=True)
    require(not unknown,'Uncovered category members: '+repr(unknown[:30]))
    return changes,reports,dict(coverage)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');ap.add_argument('--inspect-draft',action='store_true');a=ap.parse_args()
    require(not(a.write and a.inspect_draft),'Cannot build drafts')
    changes,reports,coverage=plan(a.inspect_draft,not a.inspect_draft);print('DRY RUN',len(changes),'resources',json.dumps(coverage),flush=True)
    for r in reports[:8]:print(json.dumps(r),flush=True)
    if not a.write:return
    builder.VERSION,builder.BASE,builder.OUTPUT=VERSION,BASE,OUTPUT
    builder.build(changes,reports)
    path=OUTPUT.with_suffix('.json');d=json.loads(path.read_text(encoding='utf-8'))
    d['coverage']=coverage;d['runtime_verified']=False
    d['limitations']='Offline verified. User controls runtime testing. Baked Japanese sprite labels are not changed.'
    path.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
    sources=[INPUT/(n+'_036.json') for n in ('abilities','commands','map_names')]+[ROOT/'tools/build_combat_ui_patch.py']
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps({'version':VERSION,'base':BASE.name,'sha256':d['sha256'],
        'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}},indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
