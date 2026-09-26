"""Translate complete flight and save-related UI categories. Dry-run before --write."""
import argparse
import hashlib
import json
import re
import struct
from collections import Counter
from build_ui_patch import ROOT, inner_bnd, require, u32
from dialogue_corpus import archive, parse_table
from gameplay_font import supplement
from ui_font import patch_font, measure_text, font_map, codepoint
import build_dialogue_patch as builder

VERSION = '0.1.13'
BASE = ROOT/'work/output/ACE3-English-0.1.12.iso'
OUTPUT = ROOT/'work/output/ACE3-English-0.1.13.iso'
INPUTS = [ROOT/('work/translation/en/'+name+'.json') for name in
          ('flight_options', 'intermission_save', 'results_free_mission')]
COPY_IDS = (3041, 3043, 3084)
ICONS = '㍉㌢㌔㍍㌘㊤㊦㊧㊨○×△□①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯'
KANJI = re.compile('[\u3040-\u30ff\u4e00-\u9fff]')


def controls(text):
    return Counter(c for c in text if c in ICONS), re.findall(r'#[a-z](?:\[[^\]]*\])?|<[^>]*>', text)


def visible(text):
    return text.replace('#i', '')


def placeholders(text):
    # Save slot fields are overwritten by the game at runtime. Preserve the
    # fullwidth prefix and digit run as well as all-numeric/time placeholder rows.
    fields = re.findall(r'Ｎｏ．[0-9０-９]+',text)
    if re.fullmatch(r'[0-9０-９：:－―\-\s]+',text):
        fields.append(text)
    fields.extend(re.findall(r'[③⑦]×２',text))
    return Counter(fields)


def wrap(text, font, limit):
    lines = []
    for paragraph in text.split('\n'):
        line = ''
        for word in paragraph.split(' '):
            candidate = (line+' '+word).lstrip()
            if line and max(measure_text(font, visible(candidate))) > limit:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    result = '\n'.join(lines)
    require(result.split() == text.split(), 'Wrapping changed words')
    return result


def replace_table(table, category, font):
    size, pointers, count, source = parse_table(table)
    drafts = {r['slot']: r for r in category['rows']}
    require(len(drafts) == len(category['rows']) and set(drafts) == {r[0] for r in source},
            'Incomplete or duplicate category rows')
    # Append English strings; preserve original pool and every null/index slot.
    output = bytearray(table[:size])
    reports = []
    tid = category['table_id']
    for slot, text_id, pointer, raw in source:
        row = drafts[slot]
        require(raw.decode('cp932') == row['source'], 'Source mismatch: %s/%s' % (tid, slot))
        target = row['en']
        require(controls(target) == controls(row['source']), 'Control sequence changed')
        require(placeholders(target) == placeholders(row['source']), 'Runtime placeholder changed')
        if tid == 3092 and slot >= 50:
            widths = measure_text(font, target)
            require(max(widths[1:]) <= 350 and widths[0] <= 600, 'Flight help overlaps diagram')
            require(len(target.splitlines()) <= len(row['source'].splitlines()), 'Flight help too tall')
            require(len(target) <= 255, 'Flight help exceeds drawable allocation')
        else:
            if '\n' in target:
                target = wrap(target, font, 410)
                require(len(target.splitlines()) <= 6, 'Dialog too tall')
            capacity = 255 if tid == 3041 else 128
            require(len(visible(target)) <= capacity, 'Text exceeds inherited layout capacity: %s/%s' % (tid, slot))
            widths = measure_text(font, visible(target))
            require(max(widths) <= 620, 'UI text exceeds screen width: %s/%s' % (tid, slot))
        if tid == 3092 and slot in (40, 41, 42, 43):
            require(max(widths) <= {40:62, 41:70, 42:109, 43:120}[slot], 'Flight mode label too wide')
        require(not KANJI.search(target), 'Untranslated Japanese in target')
        encoded = target.encode('cp932')
        require(b'\0' not in encoded, 'Embedded null')
        if target != row['source']:
            struct.pack_into('<I', output, pointers+slot*4, len(output))
            output.extend(encoded+b'\0')
        reports.append({'slot':slot, 'text_id':text_id, 'target':target,
                        'changed':target != row['source'], 'characters':len(visible(target)), 'widths':widths})
    output.extend(bytes(builder.align(len(output),32)-len(output)))
    struct.pack_into('<I', output, 4, len(output))
    parsed = parse_table(output)
    require([(s,i,raw.decode('cp932')) for s,i,_,raw in parsed[3]] ==
            [(r['slot'],r['text_id'],r['target']) for r in reports], 'Table round trip failed')
    require(output[pointers+count*4:size] == table[pointers+count*4:size], 'Original string pool changed')
    return bytes(output), reports


def flight_capacity(data):
    output = bytearray(data)
    resources = inner_bnd(data[:u32(data,4)])
    a,z = next((a,z) for k,a,z in resources if k == 0)
    require(u32(data,a+4) == 0x202 and u32(data,a+8) == 24, 'Unexpected flight layout')
    at = a+80+17*112
    require(data[at+0x55] == 10 and struct.unpack_from('<h',data,at+0x56)[0] == 103,
            'Wrong flight help widget')
    require(struct.unpack_from('<H',data,at+0x62)[0] == 200, 'Unexpected flight help allocation')
    struct.pack_into('<H',output,at+0x62,255)
    return bytes(output)


def parts(data):
    return {k:data[a:z] for k,a,z in inner_bnd(data[:u32(data,4)])}


def plan():
    categories = []
    for path in INPUTS:
        doc = json.loads(path.read_text(encoding='utf-8'))
        require(doc['review']['status'] == 'meaning_reviewed', 'Unreviewed UI draft')
        categories.extend(doc['categories'])
    chosen_ids = {c['table_id'] for c in categories} | set(COPY_IDS)
    replacements, reports, discovered = {}, [], []
    with BASE.open('rb') as f, next(ROOT.glob('*.iso')).open('rb') as original:
        fi, entries = archive(f)
        ofi, old_entries = archive(original)
        def get(stream, info, rows, rid):
            _,size,off,_ = next(e for e in rows if e[3] == rid)
            stream.seek(info['offset']+off)
            return stream.read(size)
        canonical = parts(get(f,fi,entries,4002050))
        native_canonical = parts(get(original,ofi,old_entries,4002050))
        game = parts(get(f,fi,entries,1200000))
        donors = [('menu19',canonical[2500],canonical[2000]), ('game19',game[2500],game[2000]),
                  ('global12',get(original,ofi,old_entries,35),get(original,ofi,old_entries,36))]
        for _,size,off,rid in entries:
            f.seek(fi['offset']+off)
            header = f.read(16)
            if header[:4] != b'BND\0' or not 16 <= u32(header,4) <= size:
                continue
            data = get(f,fi,entries,rid)
            try:
                resources = parts(data)
            except ValueError:
                continue
            targets = []
            for tid in sorted(chosen_ids & resources.keys()):
                try:
                    parsed = parse_table(resources[tid])
                except ValueError:
                    continue
                discovered.append([rid,tid])
                if tid in COPY_IDS:
                    # Exact original index and source identity establish safe copy reuse.
                    native = parts(get(original,ofi,old_entries,rid))[tid]
                    ref = parse_table(native_canonical[tid])
                    require([(s,i,r) for s,i,_,r in parse_table(native)[3]] ==
                            [(s,i,r) for s,i,_,r in ref[3]], 'Different original save category')
                    ref_rows = parse_table(canonical[tid])[3]
                    require([(s,i) for s,i,_,r in parsed[3]] == [(s,i) for s,i,_,r in ref_rows], 'Copy indices differ')
                    cat = {'table_id':tid,'category':'Previously reviewed save/load and shared dialogs',
                           'rows':[{'slot':s,'source':r.decode('cp932'),'en':nr.decode('cp932')}
                                   for (s,_,_,r),(_,_,_,nr) in zip(parsed[3],ref_rows)]}
                else:
                    candidates = [c for c in categories if c['table_id'] == tid and
                                  ('bundle_ids' not in c or rid in c['bundle_ids'])]
                    require(len(candidates) == 1, 'Ambiguous category variant')
                    cat = candidates[0]
                if any(r['source'] != r['en'] for r in cat['rows']):
                    targets.append(cat)
            if not targets:
                continue
            # The legacy Free Mission overlay contains no font resource; it
            # uses the shared menu font. Do not invent a local font binding.
            local_font = resources.get(2500, canonical[2500])
            require(2500 in resources or rid == 4002055, 'Unknown shared font user')
            font, aliases = patch_font(local_font)
            used = ''.join(visible(r['en']) for c in targets for r in c['rows']).replace('\n','')
            mapping = font_map(font)[0]
            missing = set(c for c in used if codepoint(c) not in mapping)
            edits, font_report = {}, {'aliases':aliases,'missing_used_before':sorted(missing)}
            if missing:
                require(2500 in resources, 'Shared font lacks a required glyph')
                font, texture, font_report = supplement(resources[2500],resources[2000],donors,used)
                require(not any(r['character'] in used and r['source_height'] == 12 for r in font_report['additions']),
                        'New UI uses small fallback glyph')
                edits[2000] = texture
            if 2500 in resources and font != local_font[:u32(local_font,4)]:
                edits[2500] = font
            cat_reports = []
            for cat in targets:
                tid = cat['table_id']
                table, rows = replace_table(resources[tid],cat,font)
                edits[tid] = table
                cat_reports.append({'table_id':tid,'category':cat['category'],'rows':rows})
                if tid == 3092:
                    if 27 in resources:
                        edits[27] = flight_capacity(resources[27])
                    else:
                        require(rid == 4002054, 'Missing flight setup layout')
            result = builder.rebuild_bundle(data, edits)
            replacements[rid] = result
            reports.append({'resource_id':rid,'kind':'flight_and_save_categories','categories':cat_reports,
                            'font':font_report,'old_size':len(data),'new_size':len(result),
                            'changed_subresources':sorted(edits)})
    require({4002050,4002051,4002054,4002055,4002057} <= set(replacements), 'Missing UI bundle coverage')
    require(set(replacements) <= set(range(1200000,1200012)) | set(range(4002050,4002059)),
            'Unexpected UI bundle coverage: '+str(sorted(replacements)))
    require(Counter(tid for _,tid in discovered) == Counter({3001:1,3004:2,3010:3,3041:3,
            3043:3,3054:3,3068:3,3071:3,3084:5,3092:3}), 'Category-copy inventory changed')
    return replacements, reports, discovered


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true')
    args = ap.parse_args()
    replacements,reports,discovered = plan()
    summary = {'bundles':len(replacements),'category_copies':sum(len(r['categories']) for r in reports),
               'rows_examined':sum(len(c['rows']) for r in reports for c in r['categories']),
               'rows_changed':sum(x['changed'] for r in reports for c in r['categories'] for x in c['rows']),
               'discovered_category_copies':discovered}
    print('DRY RUN',json.dumps(summary))
    for r in reports:
        print(r['resource_id'],r['old_size'],'->',r['new_size'],'resources',r['changed_subresources'])
        for c in r['categories']:
            print(c['table_id'],json.dumps(c['rows'][:2]))
    if not args.write:
        return
    builder.VERSION,builder.BASE,builder.OUTPUT = VERSION,BASE,OUTPUT
    builder.build(replacements,reports)
    path = OUTPUT.with_suffix('.json')
    report = json.loads(path.read_text(encoding='utf-8'))
    report['coverage'] = summary
    report['runtime_verified'] = False
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    manifests = INPUTS+[ROOT/'work/glossary/flight_save_terms.json',ROOT/'tools/build_flight_save_patch.py',
                        ROOT/'tools/build_dialogue_patch.py',ROOT/'tools/gameplay_font.py',ROOT/'tools/repair_disc_layout.py']
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps({'version':VERSION,
        'base_sha256':'cf91a7007a100a44863d2fdfa4ee4f1e54c8b0b0b0cf870e0aaffbbbacb74f58',
        'sha256':report['sha256'], 'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in manifests}},indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()
