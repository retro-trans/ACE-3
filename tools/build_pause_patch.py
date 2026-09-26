"""Build 0.1.8 pause-menu translations and native-size gameplay glyph repairs."""
import argparse
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path
import build_dialogue_patch as builder
from build_ui_patch import ROOT, inner_bnd, text_table, require, u32
from dialogue_corpus import archive
from gameplay_font import supplement
from ui_font import measure_text

VERSION='0.1.8'
BASE=ROOT/'work/output/ACE3-English-0.1.7.iso'
MANIFEST=ROOT/'work/translation/en/pause_menu.json'
ICONS='㍉㊤㊦㊧㊨⑪○×△□'


def replace_slots(table, draft, font):
    _, start, rows=text_table(table)
    targets=list(rows)
    report=[]
    for row in draft['rows']:
        require(row['status']=='meaning_reviewed','Unreviewed translation')
        slot=row['slot']
        require(rows[slot].decode('cp932')==row['source'],'UI source preimage mismatch')
        require(Counter(c for c in row['source'] if c in ICONS)==Counter(c for c in row['target'] if c in ICONS),'Control glyph changed')
        target=row['target']
        if '\n' in target:
            target=builder.wrap_text(target,font,width=410)
        widths=measure_text(font,target)
        require(max(widths)<=620,'Pause UI line too wide: '+row['id'])
        if slot in range(19,28):
            require(max(widths)<=174,'Pause label exceeds screenshot width: '+row['id'])
        targets[slot]=target.encode('cp932')
        report.append({'id':row['id'],'slot':slot,'target':target,'widths':widths})
    output=bytearray(table[:start])
    pool={}
    for slot,raw in enumerate(targets):
        if raw is None:continue
        if raw not in pool:
            pool[raw]=len(output);output.extend(raw+b'\0')
        struct.pack_into('<I',output,40+slot*4,pool[raw])
    output.extend(bytes(builder.align(len(output),32)-len(output)))
    struct.pack_into('<I',output,4,len(output))
    require(text_table(output)[2]==targets,'Pause table round-trip failed')
    return bytes(output),report


def plan():
    draft=json.loads(MANIFEST.read_text(encoding='utf-8'))
    require(draft['status']=='meaning_reviewed','Pause meaning review incomplete')
    replacements,reports={},[]
    with next(ROOT.glob('*.iso')).open('rb') as original,BASE.open('rb') as patched:
        source_file,source_entries=archive(original)
        base_file,base_entries=archive(patched)
        def get(stream,file,entries,rid):
            entry=next(e for e in entries if e[3]==rid)
            stream.seek(file['offset']+entry[2]);return stream.read(entry[1])
        def original_bundle(rid):
            data=get(original,source_file,source_entries,rid)
            return {k:data[a:b] for k,a,b in inner_bnd(data)}
        native19,native20=original_bundle(4002050),original_bundle(1200002)
        game19=original_bundle(1200000)
        donors=[('menu19',native19[2500],native19[2000]),('game19',game19[2500],game19[2000]),('game20',native20[2500],native20[2000]),
                ('global12',get(original,source_file,source_entries,35),get(original,source_file,source_entries,36))]
        cache={}
        for rid in draft['bundle_ids']:
            native=original_bundle(rid)
            key=hashlib.sha256(native[2500]+native[2000]).hexdigest()
            if key not in cache:
                cache[key]=supplement(native[2500],native[2000],donors,ICONS)
            font,texture,font_report=cache[key]
            data=get(patched,base_file,base_entries,rid)
            parts={k:data[a:b] for k,a,b in inner_bnd(data)}
            require(hashlib.sha256(parts[3013]).hexdigest()==draft['source_table_sha256'],'Different pause category copy')
            table,rows=replace_slots(parts[3013],draft,font)
            used=set(''.join(row['target'] for row in rows))
            require(not any(a['character'] in used and a['source_height']==12 for a in font_report['additions']),
                    'Pause category still relies on small fallback glyphs')
            replacements[rid]=builder.rebuild_bundle(data,{3013:table,2500:font,2000:texture})
            reports.append({'resource_id':rid,'kind':'pause_menu_and_font','rows':rows,
                            'font':font_report,'old_size':len(data),'new_size':len(replacements[rid])})
    return replacements,reports


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    replacements,reports=plan()
    print('DRY RUN:',len(replacements),'gameplay bundles;',sum(len(r['rows']) for r in reports),'translated instances')
    for r in reports:
        print(r['resource_id'],r['old_size'],'->',r['new_size'],'font packed height',r['font']['used_height'])
    for row in reports[0]['rows']:
        if row['slot'] in list(range(19,28))+[36,37,72]:print(json.dumps(row))
    if not args.write:return
    builder.VERSION=VERSION
    builder.BASE=BASE
    builder.OUTPUT=ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
    builder.build(replacements,reports)
    path=builder.OUTPUT.with_suffix('.json')
    report=json.loads(path.read_text(encoding='utf-8'))
    report['coverage']='103 pause-category slots in eight gameplay bundles (824 instances). Inherited tutorial and startup UI translations retained.'
    report['font_limitations']='Reported b/l/v/w and other available native-size glyphs repaired. Lowercase j/q and uncommon punctuation without a native-size donor still use the prior small-font fallback outside this pause category.'
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    manifest['base_sha256']='2465b48f453b1ec20c3d0b05649a01bb93adf46b2aae6250bde9d40d8d1b747e'
    manifest['output_sha256']=report['sha256']
    manifest['tools_sha256']={name:hashlib.sha256((ROOT/'tools'/name).read_bytes()).hexdigest()
                             for name in ['build_pause_patch.py','gameplay_font.py','build_dialogue_patch.py','repair_disc_layout.py']}
    builder.OUTPUT.with_suffix('.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
