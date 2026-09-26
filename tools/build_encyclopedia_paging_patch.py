"""0.1.41: word-preserving Encyclopedia pagination within the 190-glyph renderer.

Dry-run by default. Only the three menu body tables change. The in-mission
glossary uses shorter windows and does not share the eight-line page stride.
"""
import argparse
import json
import re
import struct
from build_ui_patch import ROOT, require, iso_files
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts
from build_intermission_patch import replace_rows
from ui_font import measure_text
import build_dialogue_patch as builder

VERSION = '0.1.41'
BASE = ROOT/'work/output/ACE3-English-0.1.40.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BUNDLES = (4002050, 4002054, 4002057)
PAGE_LINES, GLYPHS = 8, 180
TAG = re.compile(r'<[^<>]*>')
LINK = re.compile(r'<book\((\d+)\)>(.*?)<endbook\(\)>', re.S)


def visible(text):
    return TAG.sub('', text)


def pages(text):
    lines = text.split('\n')
    return ['\n'.join(lines[i:i+PAGE_LINES]) for i in range(0, len(lines), PAGE_LINES)]


def fits(lines):
    return len(lines) <= PAGE_LINES and sum(len(visible(x)) for x in lines) <= GLYPHS


def paginate(text):
    if all(fits(page.split('\n')) for page in pages(text)):
        return text
    completed, current = [], []

    def flush():
        if current:
            while current and not current[-1]:
                current.pop()
            completed.append(current[:])
            current.clear()

    for paragraph in text.split('\n\n'):
        block = paragraph.split('\n')
        require(all(line.count('<book(') == line.count('<endbook()>') for line in block),
                'A linked span crosses lines; needs separate handling')
        if fits(block):
            candidate = current + ([''] if current else []) + block
            if not fits(candidate):
                flush()
            if current:
                current.append('')
            current.extend(block)
        else:
            if current:
                current.append('')
            for line in block:
                require(fits([line]), 'Single line exceeds page capacity')
                if not fits(current+[line]):
                    flush()
                current.append(line)
    flush()
    result = '\n'.join('\n'.join(page+['']*(PAGE_LINES-len(page)))
                       if i < len(completed)-1 else '\n'.join(page)
                       for i, page in enumerate(completed))
    require(result.split() == text.split(), 'Pagination changed words')
    require(LINK.findall(result) == LINK.findall(text), 'Pagination changed links')
    require(all(fits(p.split('\n')) and len(visible(p)) < 190 for p in pages(result)),
            'Page exceeds drawing capacity')
    require(len(result.split('\n')) < 255, 'Line counter overflow')
    return result


def verify_renderer(stream):
    item = next(v for k, v in iso_files(stream).items() if 'SLPS' in k)
    stream.seek(item['offset']); elf = stream.read(item['size'])
    ph = struct.unpack_from('<I', elf, 28)[0]
    size, count = struct.unpack_from('<HH', elf, 42)
    segments = [struct.unpack_from('<8I', elf, ph+i*size) for i in range(count)]
    def at(va, n):
        for kind, off, start, _, sz, _, _, _ in segments:
            if kind == 1 and start <= va and va+n <= start+sz:
                return elf[off+va-start:off+va-start+n]
        raise ValueError('Address outside ELF')
    require(at(0x2f47c4, 8) == struct.pack('<II', 0x0c0adbec, 0x240500be),
            '190-glyph callback changed')
    require(at(0x369a20, 4) == struct.pack('<I', 0x2f4760), 'Callback pointer changed')


def plan():
    changes, reports = {}, []
    with BASE.open('rb') as f:
        verify_renderer(f)
        fi, entries = archive(f)
        for rid in BUNDLES:
            _, size, off, _ = next(e for e in entries if e[3] == rid)
            f.seek(fi['offset']+off); old = f.read(size); resources = parts(old)
            rows = parse_table(resources[3019])[3]
            require(len(rows) == 88, 'Incomplete Encyclopedia')
            mappings, audit = {}, []
            for slot, tid, _, raw in rows:
                source = raw.decode('cp932'); target = paginate(source)
                require(max(measure_text(resources[2500], visible(target))) <= 443, 'Line too wide')
                if source != target:
                    mappings[slot] = (source, target)
                audit.append({'text_id': tid, 'before': source, 'target': target,
                              'changed': source != target, 'pages': len(pages(target)),
                              'page_glyphs': [len(visible(p).replace('\n', '')) for p in pages(target)]})
            table = replace_rows(resources[3019], mappings)
            changes[rid] = builder.rebuild_bundle(old, {3019: table})
            require(all(v == parts(changes[rid])[k] for k, v in resources.items() if k != 3019),
                    'Unrelated resource changed')
            reports.append({'resource_id': rid, 'kind': 'encyclopedia_pagination', 'rows': audit})
    return changes, reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true'); args = parser.parse_args()
    changes, reports = plan()
    summary = {'entries_audited_per_copy': 88, 'menu_copies': len(reports),
               'distinct_entries_changed': sum(r['changed'] for r in reports[0]['rows']),
               'text_instances_changed': sum(r['changed'] for report in reports for r in report['rows']),
               'max_page_glyphs': max(max(r['page_glyphs']) for report in reports for r in report['rows']),
               'max_pages': max(r['pages'] for report in reports for r in report['rows'])}
    print('DRY RUN', json.dumps(summary), flush=True)
    sample = next(r for r in reports[0]['rows'] if r['text_id'] == 35)
    for i, page in enumerate(pages(sample['target'])):
        print('Zentradi page', i+1, repr(page), flush=True)
    if not args.write:
        return
    builder.VERSION, builder.BASE, builder.OUTPUT = VERSION, BASE, OUTPUT
    builder.build(changes, reports)
    path = OUTPUT.with_suffix('.json'); report = json.loads(path.read_text(encoding='utf-8'))
    report['coverage'] = summary
    report['runtime_note'] = 'Eight-line paging is grounded in the supplied captures; fresh-boot runtime verification pending.'
    path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    target = ROOT/'work/translation/en/encyclopedia_paging_041.json'
    target.write_text(json.dumps({'version': VERSION, 'method': 'Whitespace only; preserve all words and links',
                                  'summary': summary, 'rows': reports[0]['rows']}, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
