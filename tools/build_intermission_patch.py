"""Complete intermission update notices and unit-name UI. Dry-run before --write."""
import argparse
import hashlib
import json
import re
import struct
from collections import Counter
from build_flight_save_patch import parts, controls, placeholders
from build_ui_patch import ROOT, require, u32
from dialogue_corpus import archive, parse_table
from ui_font import patch_font, measure_text, codepoint, font_map
from gameplay_font import supplement
import build_dialogue_patch as builder

VERSION = '0.1.14'
BASE = ROOT/'work/output/ACE3-English-0.1.13.iso'
OUTPUT = ROOT/'work/output/ACE3-English-0.1.14.iso'
FILES = [ROOT/('work/translation/en/'+name+'.json') for name in
         ('intermission_notices','unit_names_014_a','unit_names_014_b','unit_name_variants_014')]
NAME_TABLES = (3000,3025,3077)
FORMAT = re.compile(r'%(?:[-+0 #]*\d*(?:\.\d+)?)?[sdiuf%]')


def load_translations():
    docs = [json.loads(p.read_text(encoding='utf-8')) for p in FILES]
    for d in docs:
        require(d['review']['status'] == 'meaning_reviewed','Unreviewed category')
    notices = docs[0]['categories'][0]
    names = {}
    for d in docs[1:]:
        for row in d['rows']:
            source,target = row['source'],row['en']
            require(source not in names or names[source] == target,'Conflicting unit name: '+source)
            names[source] = target
    require(len(docs[1]['rows']) == 80 and len(docs[2]['rows']) == 26,'Incomplete roster slices')
    glossary = {}
    for filename in ('unit_names_014_a.json','unit_names_014_b.json'):
        for row in json.loads((ROOT/'work/glossary'/filename).read_text(encoding='utf-8'))['entries']:
            glossary[row.get('ja',row.get('source'))] = row['en']
    require(all(glossary.get(source) == target for source,target in names.items()),'Unit spelling differs from locked glossary')
    return notices,names


def replace_rows(table, mappings):
    size,ptr,count,rows = parse_table(table)
    require(set(mappings) <= {s for s,_,_,_ in rows},'Invalid target slot')
    output = bytearray(table[:size])
    expected = []
    for slot,tid,at,raw in rows:
        if slot in mappings:
            source,target = mappings[slot]
            require(raw.decode('cp932') == source,'Source preimage mismatch')
            require(controls(source) == controls(target),'Control code changed')
            require(placeholders(source) == placeholders(target),'Placeholder changed')
            require(FORMAT.findall(source) == FORMAT.findall(target),'Printf arguments changed')
            raw = target.encode('cp932')
            require(b'\0' not in raw,'Embedded null')
            struct.pack_into('<I',output,ptr+slot*4,len(output))
            output.extend(raw+b'\0')
        expected.append((slot,tid,raw))
    output.extend(bytes(builder.align(len(output),32)-len(output)))
    struct.pack_into('<I',output,4,len(output))
    require([(s,i,r) for s,i,_,r in parse_table(output)[3]] == expected,'Name table round trip failed')
    require(output[ptr+count*4:size] == table[ptr+count*4:size],'Original pool changed')
    return bytes(output)


def notice_fit(notices, names, font):
    expansions = []
    for row in notices['rows']:
        texts = [row['en'] % name for name in names] if '%s' in row['en'] else [row['en']]
        if row['en'] in ('－',):
            continue
        for target in texts:
            require(len(target.encode('cp932')) <= 63,'Notice exceeds 64-byte record: '+target)
            widths = measure_text(font,target)
            require(max(widths) <= 410,'Expanded notice too wide: '+target)
            require(len(target) <= 41,'Six-notice allocation can overflow: '+target)
            require('\n' not in target,'Notice unexpectedly consumes two rows: '+target)
            expansions.append({'template_slot':row['slot'],'target':target,'width':max(widths),'characters':len(target),'bytes':len(target.encode('cp932'))})
    # Six maximum-length notices plus newline separators remain within the
    # existing 255-character shared dialog widget. No allocator hooks required.
    return {'expansions_checked':len(expansions),'max_width':max(r['width'] for r in expansions),
            'max_encoded_bytes':max(r['bytes'] for r in expansions),
            'max_characters':max(r['characters'] for r in expansions),
            'six_line_capacity_bound':6*max(r['characters'] for r in expansions)+5}


def plan():
    notices,names = load_translations()
    changes,reports,inventory = {},[],[]
    with BASE.open('rb') as f, next(ROOT.glob('*.iso')).open('rb') as original:
        fi,entries = archive(f)
        oi,oe = archive(original)
        def get(stream,info,es,rid):
            _,size,off,_ = next(e for e in es if e[3] == rid)
            stream.seek(info['offset']+off)
            return stream.read(size)
        menu = parts(get(f,fi,entries,4002050))
        game = parts(get(f,fi,entries,1200000))
        roster = parse_table(menu[3000])[3]
        require(all(raw.decode('cp932') in names for _,_,_,raw in roster),'Incomplete primary unit roster')
        roster_data = get(f,fi,entries,100204)
        roster_count = struct.unpack_from('<H',roster_data)[0]
        require(roster_count == 103,'Runtime notification roster changed')
        runtime_ids = [struct.unpack_from('<h',roster_data,8+i*64)[0] for i in range(roster_count)]
        donors = [('menu19',menu[2500],menu[2000]),('game19',game[2500],game[2000]),
                  ('global12',get(original,oi,oe,35),get(original,oi,oe,36))]
        for _,size,off,rid in entries:
            f.seek(fi['offset']+off)
            h = f.read(16)
            if h[:4] != b'BND\0' or not 16 <= u32(h,4) <= size:continue
            data = get(f,fi,entries,rid)
            try:p = parts(data)
            except ValueError:continue
            selected = {}
            for tid in (*NAME_TABLES,3069):
                if tid not in p:continue
                try:rows = parse_table(p[tid])[3]
                except ValueError:continue
                if tid == 3069:
                    require({r['slot']:r['source'] for r in notices['rows']} ==
                            {s:raw.decode('cp932') for s,_,_,raw in rows},'Notice category copy differs')
                    mappings = {r['slot']:(r['source'],r['en']) for r in notices['rows'] if r['source'] != r['en']}
                else:
                    mappings = {s:(raw.decode('cp932'),names[raw.decode('cp932')]) for s,_,_,raw in rows if raw.decode('cp932') in names}
                if mappings:
                    selected[tid] = mappings
                    inventory.append([rid,tid,len(mappings)])
            if not selected:continue
            require(2500 in p and 2000 in p,'Unknown unit-name font binding')
            used = ''.join(target for m in selected.values() for _,target in m.values()).replace('\n','')
            font,aliases = patch_font(p[2500])
            mp = font_map(font)[0]
            missing = {c for c in used if codepoint(c) not in mp}
            edits,fr = {},{'aliases':aliases}
            if missing:
                font,texture,fr = supplement(p[2500],p[2000],donors,used)
                require(not any(a['character'] in used and a['source_height'] == 12 for a in fr['additions']),
                        'Unit name uses small fallback glyph')
                edits[2000] = texture
            if font != p[2500][:u32(p[2500],4)]:edits[2500] = font
            fr['known_small_glyphs'] = ['j'] if 'j' in used else []
            fr['small_glyph_note'] = 'The existing gameplay j is a 12px fallback; exhaustive original-font scan found no native19/20px lowercase j.'
            fit = None
            if 3069 in selected:
                lookup = {tid:{i:r.decode('cp932') for _,i,_,r in parse_table(p[tid])[3]} for tid in (3025,3077)}
                runtime_names = [names[lookup[3025 if 19010 <= i <= 19012 else 3077][i]] for i in runtime_ids]
                fit = notice_fit(notices,runtime_names,font)
                fit['runtime_roster_count'] = roster_count
                fit['name_source'] = '100204 roster IDs; 3077 names except 19010-19012 from 3025'
            table_reports = []
            for tid,mappings in selected.items():
                row_reports = []
                for slot,(source,target) in sorted(mappings.items()):
                    widths = measure_text(font,target)
                    # Other menus include long original transformed-unit labels;
                    # keep those no wider than their original rendered label.
                    width_limit = 410 if tid == 3069 else max(320,max(measure_text(font,source)))
                    require(max(widths) <= width_limit and len(target) <= 128,
                            'Unit label exceeds UI capacity: '+target)
                    row_reports.append({'slot':slot,'target':target,'widths':widths,'width_limit':width_limit})
                edits[tid] = replace_rows(p[tid],mappings)
                table_reports.append({'table_id':tid,'rows':row_reports})
            changes[rid] = builder.rebuild_bundle(data,edits)
            reports.append({'resource_id':rid,'kind':'intermission_notices_and_unit_names',
                            'tables':table_reports,'font':fr,'notice_fit':fit,
                            'changed_subresources':sorted(edits),'old_size':len(data),'new_size':len(changes[rid])})
        # Inherited menu/help translations are checked against the actual latest ISO.
        require(dict((s,r.decode('cp932')) for s,_,_,r in parse_table(menu[3004])[3])[9] == 'Intermission',
                'Inherited Intermission title missing')
    require(Counter(tid for _,tid,_ in inventory) == Counter({3000:4,3025:5,3077:5,3069:3}),
            'Unexpected category-copy inventory')
    return changes,reports,inventory


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true')
    args = ap.parse_args()
    changes,reports,inventory = plan()
    summary = {'bundles':len(changes),'tables':len(inventory),'entries':sum(x[2] for x in inventory),'inventory':inventory}
    print('DRY RUN',json.dumps(summary))
    for r in reports:
        print(r['resource_id'],r['old_size'],'->',r['new_size'],'fit',r['notice_fit'])
        for t in r['tables']:print(t['table_id'],json.dumps(t['rows'][:2]))
    if not args.write:return
    builder.VERSION,builder.BASE,builder.OUTPUT = VERSION,BASE,OUTPUT
    builder.build(changes,reports)
    path = OUTPUT.with_suffix('.json')
    result = json.loads(path.read_text(encoding='utf-8'))
    result['coverage'] = summary
    result['font_limitations'] = 'Nanajin uses the existing smaller lowercase j fallback. All larger original game fonts lack lowercase j; runtime appearance remains unverified.'
    path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    inputs = FILES+[ROOT/'work/glossary/unit_names_014_a.json',ROOT/'work/glossary/unit_names_014_b.json',
                   ROOT/'tools/build_intermission_patch.py',ROOT/'tools/build_dialogue_patch.py',
                   ROOT/'tools/gameplay_font.py',ROOT/'tools/repair_disc_layout.py']
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps({'version':VERSION,'base':BASE.name,
        'base_sha256':'c6e8539a46f196b5cb715737f45d917b538d8971c54d89811eebb4811c8d2be6',
        'sha256':result['sha256'],'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}},indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':main()
