"""0.1.46: fit the missing Briefing victory/defeat headings.

Dry run by default. --write copies 0.1.45 and applies six fixed-size text
edits, then verifies the entire disc delta. No layout or script changes.
"""
import argparse
import hashlib
import json
import shutil
import struct
from build_ui_patch import ROOT, require, u32, inner_bnd
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts
from ui_font import measure_text

VERSION = '0.1.46'
BASE = ROOT/'work/output/ACE3-English-0.1.45.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
INPUT = ROOT/'work/translation/en/briefing_headers_046.json'
BASE_SHA = '879cd6a564669ce82966c26fd96099b0cbed4ee41e65b6c4aaff4ee435c0de7f'


def plan():
    doc = json.loads(INPUT.read_text(encoding='utf-8'))
    edits, checks = [], []
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        for rid in doc['bundles']:
            _, size, offset, _ = next(e for e in entries if e[3] == rid)
            origin = fi['offset']+offset
            f.seek(origin)
            data = f.read(size)
            p = parts(data)
            table_offset = next(a for k, a, b in inner_bnd(data) if k == doc['table_id'])
            table = p[doc['table_id']]
            rows = parse_table(table)[3]
            layout = parts(p[doc['layout_id']])[0]
            patched = bytearray(table)
            expected = {tid: raw for _, tid, _, raw in rows}
            for spec in doc['rows']:
                slot, tid, ptr, raw = next(r for r in rows if r[1] == spec['text_id'])
                require(raw.decode('cp932') == spec['before'], 'Heading preimage changed')
                a, b = 80+spec['node']*112, 80+spec['body_node']*112
                require(layout[a+85] == 10 and struct.unpack_from('<h', layout, a+86)[0] == tid, 'Heading binding')
                gap = struct.unpack_from('<f', layout, b)[0]-struct.unpack_from('<f', layout, a)[0]
                width = max(measure_text(p[2500], spec['target']))
                require(90 < gap < 100 and width <= gap-4, 'Heading exceeds available column')
                encoded = spec['target'].encode('cp932')
                require(len(encoded) <= len(raw), 'Replacement grows')
                # Refuse shared pointers or overlapping string slices rather
                # than accidentally modifying another label through an alias.
                require(all(s == slot or at+len(other)+1 <= ptr or at >= ptr+len(raw)+1
                            for s, _, at, other in rows), 'Aliased heading string')
                replacement = encoded+bytes(len(raw)+1-len(encoded))
                patched[ptr:ptr+len(raw)+1] = replacement
                edits.append(dict(offset=origin+table_offset+ptr, before=raw+b'\0', after=replacement))
                expected[tid] = encoded
                checks.append(dict(bundle=rid, text_id=tid, before=spec['before'], target=spec['target'],
                                   display_width=width, available_width=gap))
            require({tid: raw for _, tid, _, raw in parse_table(patched)[3]} == expected, 'Neighboring text changed')
    edits.sort(key=lambda e: e['offset'])
    require(len(edits) == 6 and all(a['offset']+len(a['after']) <= b['offset'] for a, b in zip(edits, edits[1:])),
            'Unexpected edit coverage')
    return edits, checks


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    edits, checks = plan()
    print('DRY RUN', json.dumps(checks, indent=2), flush=True)
    if not args.write:
        return
    require(not OUTPUT.exists(), 'Output already exists')
    shutil.copyfile(BASE, OUTPUT)
    with OUTPUT.open('r+b') as f:
        for e in edits:
            f.seek(e['offset'])
            require(f.read(len(e['before'])) == e['before'], 'Disc preimage mismatch')
            f.seek(e['offset'])
            f.write(e['after'])
    source_sha, output_sha = hashlib.sha256(), hashlib.sha256()
    position = 0
    with BASE.open('rb') as source, OUTPUT.open('rb') as output:
        while True:
            raw = source.read(8 << 20)
            if not raw:
                break
            expected = bytearray(raw)
            for e in edits:
                lo, hi = max(position, e['offset']), min(position+len(raw), e['offset']+len(e['after']))
                if lo < hi:
                    expected[lo-position:hi-position] = e['after'][lo-e['offset']:hi-e['offset']]
            actual = output.read(len(raw))
            require(actual == expected, 'Unexpected disc byte change')
            source_sha.update(raw)
            output_sha.update(actual)
            position += len(raw)
        require(not output.read(1), 'Output size changed')
    require(source_sha.hexdigest() == BASE_SHA, 'Wrong base image')
    report = dict(version=VERSION, base_sha256=source_sha.hexdigest(), sha256=output_sha.hexdigest(),
                  size=position, whole_disc_verified=True, runtime_verified=False, checks=checks)
    OUTPUT.with_suffix('.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('VERIFIED', OUTPUT, report['sha256'], flush=True)


if __name__ == '__main__':
    main()
