"""Translate the complete opening history crawl; dry-run before --write."""
import argparse
import hashlib
import json
import struct
from build_ui_patch import ROOT, inner_bnd, require, u32
from dialogue_corpus import archive, parse_table
from ui_font import measure_text
import build_dialogue_patch as builder

VERSION = '0.1.12'
BASE = ROOT/'work/output/ACE3-English-0.1.11.iso'
OUTPUT = ROOT/'work/output/ACE3-English-0.1.12.iso'
TRANSLATION = ROOT/'work/translation/en/opening_history.json'
GLOSSARY = ROOT/'work/glossary/opening_history_terms.json'
WIDTH = 430


def chunks(data):
    rows, at = [], 0
    while at < len(data):
        require(at+16 <= len(data), 'Truncated scene chunk')
        size = u32(data, at+4)
        require(size >= 16 and size % 16 == 0 and at+size <= len(data), 'Invalid scene chunk')
        rows.append((data[at:at+4], at, at+size))
        at += size
    require(rows[-1][0] == b'END\0', 'Missing scene terminator')
    return rows


def wrap(text, font):
    lines = ['']
    for word in text.split():
        require(max(measure_text(font, word)) <= WIDTH, 'Unbreakable word exceeds crawl width')
        candidate = (lines[-1]+' '+word).strip()
        if max(measure_text(font, candidate)) > WIDTH:
            lines.append(word)
        else:
            lines[-1] = candidate
    require(' '.join(lines) == ' '.join(text.split()), 'Wrapping lost words')
    return lines


def rebuild_history(table, draft, font):
    size, pointers, count, source = parse_table(table)
    require(count == 200 and draft['review']['status'] == 'meaning_reviewed', 'Unreviewed or unexpected crawl')
    source_by_slot = {r[0]: r for r in source}
    examined, rows, groups, slot = [], {}, [], 10
    for index, group in enumerate(draft['groups']):
        for row in group['source_rows']:
            current = source_by_slot[row['slot']]
            require(current[1] == row['text_id'] and hashlib.sha256(current[3]).hexdigest() == row['source_sha256'],
                    'Crawl source hash/ID mismatch')
            examined.append(row['slot'])
        if index and group['kind'] == 'heading':
            slot += 2
        lines = wrap(group['en'], font)
        start = slot
        for line in lines:
            require(slot < count, 'Crawl exceeds available line IDs')
            rows[slot] = line.encode('cp932')
            slot += 1
        groups.append({'id': group['id'], 'start_slot': start, 'lines': lines,
                       'widths': [max(measure_text(font, line)) for line in lines]})
        slot += 1
    require(sorted(examined) == sorted(source_by_slot), 'Crawl coverage is incomplete or duplicated')
    # Keep original source storage intact; append a new English pool and redirect
    # all 200 slots. No individual source row imposes a byte/character budget.
    output = bytearray(table[:size])
    for i in range(count):
        struct.pack_into('<I', output, pointers+i*4, 0)
    for i, raw in rows.items():
        struct.pack_into('<I', output, pointers+i*4, len(output))
        output.extend(raw+b'\0')
    output.extend(bytes(builder.align(len(output), 32)-len(output)))
    struct.pack_into('<I', output, 4, len(output))
    result = parse_table(output)
    require({s:r for s,_,_,r in result[3]} == rows, 'Reflowed crawl failed round trip')
    require(output[pointers+count*4:size] == table[pointers+count*4:size], 'Original string storage changed')
    return bytes(output), {'source_rows':len(source), 'english_lines':len(rows), 'last_text_slot':max(rows),
                           'width_limit':WIDTH, 'source_size':size, 'new_size':len(output), 'groups':groups}


def plan():
    draft = json.loads(TRANSLATION.read_text(encoding='utf-8'))
    terms = json.loads(GLOSSARY.read_text(encoding='utf-8'))
    full = ' '.join(g['en'] for g in draft['groups'])
    for row in terms['entries']:
        require(row.get('short_display',row['en']) in full, 'Glossary spelling missing from crawl: '+row['id'])
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        def get(rid):
            _,size,off,_ = next(e for e in entries if e[3] == rid)
            f.seek(fi['offset']+off)
            return f.read(size)
        game = get(1200000)
        font = next(game[a:z] for k,a,z in inner_bnd(game) if k == 2500)
        data = get(4010)
        parts = chunks(data)
        stuf = [(a,z) for tag,a,z in parts if tag == b'STUF']
        require(len(stuf) == 1, 'Ambiguous scene text container')
        a,z = stuf[0]
        bnd = data[a+16:z]
        resources = inner_bnd(bnd)
        require(len(resources) == 1 and resources[0][0] == 3, 'Unexpected crawl bundle')
        _,ta,tz = resources[0]
        table, report = rebuild_history(bnd[ta:tz], draft, font)
        replaced = builder.rebuild_bundle(bnd, {3:table})
        header = bytearray(data[a:a+16])
        struct.pack_into('<I',header,4,len(replaced)+16)
        output = data[:a]+bytes(header)+replaced+data[z:]
        after_parts = chunks(output)
        require(len(parts) == len(after_parts), 'Scene chunk count changed')
        for (tag,lo,hi),(newtag,nlo,nhi) in zip(parts,after_parts):
            require(tag == newtag, 'Scene chunk order changed')
            if tag != b'STUF':
                require(data[lo:hi] == output[nlo:nhi], 'Unrelated scene data changed')
        report.update({'resource_id':4010, 'kind':'opening_history', 'old_resource_size':len(data),
                       'new_resource_size':len(output), 'old_stuf_offset':a,
                       'source_resource_sha256':hashlib.sha256(data).hexdigest(),
                       'runtime_verified':False})
    return {4010:output}, [report]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true')
    args = ap.parse_args()
    replacements,reports = plan()
    print('DRY RUN',json.dumps(reports,indent=2))
    if not args.write:return
    builder.VERSION,builder.BASE,builder.OUTPUT = VERSION,BASE,OUTPUT
    builder.build(replacements,reports)
    path = OUTPUT.with_suffix('.json')
    report = json.loads(path.read_text(encoding='utf-8'))
    report['coverage'] = 'Complete opening history crawl: all 39 source rows across 20 groups. Existing UI, tutorial and speaker translations inherited.'
    report['runtime_verified'] = False
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    manifest = {'version':VERSION, 'base_sha256':'40267948aa2d3c011caf50751425bf0dd486c5c8baaca8dfaa1a9060de8b5279',
                'output_sha256':report['sha256'], 'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [TRANSLATION,GLOSSARY,ROOT/'tools/build_history_patch.py',ROOT/'tools/build_dialogue_patch.py',ROOT/'tools/repair_disc_layout.py']}}
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':main()
