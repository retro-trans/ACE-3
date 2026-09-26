"""0.1.24: make the opening history crawl actually display in English. Dry-run unless --write.

0.1.12 kept the Japanese string pool of the crawl table (resource 4010, STUF, text 3) in place, appended an
English pool and redirected the 200 slot pointers to it. The user still sees the Japanese crawl on 0.1.19+,
at the end of Stage 1 and in the Movie Viewer, with a disc that holds both pools. The pointers are correct,
so the crawl renderer evidently does not go through them; the likeliest reading is that it walks the string
storage that starts right behind the pointer array. This build writes the English lines there, in slot order,
and drops the Japanese pool, so either way of reading the table finds English.
"""
import argparse
import hashlib
import json
import struct
from build_ui_patch import ROOT, inner_bnd, require, u32
from dialogue_corpus import archive, parse_table
from build_history_patch import chunks
import build_dialogue_patch as builder

VERSION = '0.1.24'
BASE = ROOT/'work/output/ACE3-English-0.1.23.iso'
OUTPUT = ROOT/'work/output/ACE3-English-0.1.24.iso'
KANJI = builder.re.compile('[぀-ヿ一-鿿]')


def compact(table):
    """Same header, ID ranges, slots and English rows; strings stored once, in slot order, from the pool start."""
    size, pointers, count, rows = parse_table(table)
    require(count == 200 and rows and not any(KANJI.search(r[3].decode('cp932')) for r in rows), 'Expected the English crawl table')
    output = bytearray(table[:pointers+count*4])
    for i in range(count): struct.pack_into('<I', output, pointers+i*4, 0)
    for slot, text_id, _, raw in sorted(rows):
        struct.pack_into('<I', output, pointers+slot*4, len(output)); output.extend(raw+b'\0')
    output.extend(bytes(builder.align(len(output), 32)-len(output)))
    struct.pack_into('<I', output, 4, len(output))
    after = parse_table(output)[3]
    require([(s, i, r) for s, i, _, r in after] == [(s, i, r) for s, i, _, r in rows], 'Crawl rows changed')
    require(not KANJI.search(bytes(output[pointers+count*4:]).decode('cp932', 'replace')), 'Japanese pool still present')
    return bytes(output), {'slots':count, 'english_lines':len(rows), 'old_table_size':size, 'new_table_size':len(output),
                           'first_pool_string':after[0][3].decode('cp932')}


def plan():
    with BASE.open('rb') as f:
        fi, entries = archive(f); _, size, off, _ = next(e for e in entries if e[3] == 4010)
        f.seek(fi['offset']+off); data = f.read(size)
    parts = chunks(data)
    (a, z), = [(lo, hi) for tag, lo, hi in parts if tag == b'STUF']
    bnd = data[a+16:z]; (key, ta, tz), = inner_bnd(bnd)
    require(key == 3, 'Unexpected crawl bundle')
    table, report = compact(bnd[ta:tz])
    replaced = builder.rebuild_bundle(bnd, {3:table})
    header = bytearray(data[a:a+16]); struct.pack_into('<I', header, 4, len(replaced)+16)
    output = data[:a]+bytes(header)+replaced+data[z:]
    after = chunks(output)
    require([t for t, _, _ in parts] == [t for t, _, _ in after], 'Scene chunk order changed')
    for (tag, lo, hi), (_, nlo, nhi) in zip(parts, after):
        if tag != b'STUF': require(data[lo:hi] == output[nlo:nhi], 'Unrelated scene data changed')
    report.update({'resource_id':4010, 'kind':'opening_history_pool_fix', 'old_resource_size':len(data),
                   'new_resource_size':len(output), 'japanese_crawl_left_in_resource':'熱血クーデター'.encode('cp932') in output})
    return {4010:output}, [report]


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    replacements, reports = plan()
    print('DRY RUN', json.dumps(reports, indent=1, ensure_ascii=True))
    if not a.write: return
    builder.VERSION, builder.BASE, builder.OUTPUT = VERSION, BASE, OUTPUT
    builder.build(replacements, reports)
    path = OUTPUT.with_suffix('.json'); doc = json.loads(path.read_text(encoding='utf-8'))
    doc['coverage'] = 'Opening history crawl table rebuilt with the English pool in the original pool position. Everything else inherited from 0.1.23.'
    doc['runtime_verified'] = False
    path.write_text(json.dumps(doc, indent=2)+'\n', encoding='utf-8')
    inputs = [ROOT/'tools/build_history_fix.py', ROOT/'tools/build_history_patch.py', ROOT/'tools/build_dialogue_patch.py']
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps({'version':VERSION, 'base':BASE.name,
        'base_sha256':'c8d41638731491c9398ac947a0d169536206b45053eb8d3e2c6d68f9ac778c87', 'sha256':doc['sha256'],
        'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
