"""0.1.16: replace blanket text capacities with corpus-derived bounds."""
import argparse
import hashlib
import json
import shutil
import struct
from collections import Counter
from build_ui_patch import ROOT, iso_files, require, u32
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts

VERSION = '0.1.16'
BASE = ROOT/'work/output/ACE3-English-0.1.15.iso'
OUTPUT = ROOT/'work/output/ACE3-English-0.1.16.iso'
ORIGINAL = next(ROOT.glob('*.iso'))
TEXT_TYPES = (4, 10, 11, 12)


def capacity_bound(original, pairs):
    """Cover every translated string which fitted the original glyph budget.

    Includes spaces, controls and newlines conservatively, plus one spare
    glyph. Keep at least the engine's default 32; never shrink a stock bound.
    Existing independently enlarged 200/255-char dialogs are not candidates.
    """
    original = original or 32
    targets = [len(target)+1 for source, target in pairs if len(source) <= original]
    return max([32, original] + targets)


def layouts(data, origin=0, path=()):
    if data[:4] == b'BND\0':
        count, size = u32(data, 8), u32(data, 4)
        require(16+count*8 <= size <= len(data), 'Invalid BND')
        rows = [struct.unpack_from('<II', data, 16+i*8) for i in range(count)]
        for j, (rid, start) in enumerate(rows):
            end = rows[j+1][1] if j+1 < count else size
            require(16+count*8 <= start < end <= size, 'Invalid child extent')
            yield from layouts(data[start:end], origin+start, path+(rid,))
    elif len(data) >= 80 and u32(data, 4) == 0x202:
        size, count, start = u32(data, 0), u32(data, 8), u32(data, 12)
        require(start == 80 and start+count*112 <= size <= len(data), 'Bad layout')
        for i in range(count):
            at = start+i*112
            if data[at+0x55] in TEXT_TYPES:
                yield path+(i,), origin+at+0x62, struct.unpack_from('<H',data,at+0x62)[0]


def plan():
    pairs, bundles = set(), []
    with BASE.open('rb') as f, ORIGINAL.open('rb') as o:
        fi, es = archive(f)
        oi, oe = archive(o)
        old = {rid:(size, off) for _, size, off, rid in oe}
        for _, size, off, rid in es:
            if not (1200000 <= rid <= 1200011 or 4002050 <= rid <= 4002058): continue
            f.seek(fi['offset']+off); current = f.read(size)
            sz, pos = old[rid]; o.seek(oi['offset']+pos); original = o.read(sz)
            bundles.append((rid, fi['offset']+off, current, original))
            p, q = parts(current), parts(original)
            for tid, table in p.items():
                if table[:4] != b'\0\0\1\0' or tid not in q: continue
                # Fonts share the magic but not the text-table header.
                try:
                    old_rows, new_rows = parse_table(q[tid])[3], parse_table(table)[3]
                except ValueError:
                    continue
                before = {i:r.decode('cp932') for _,i,_,r in old_rows}
                after = {i:r.decode('cp932') for _,i,_,r in new_rows}
                pairs.update((before[i], text) for i,text in after.items()
                             if i in before and text != before[i])
    changes = []
    for rid, disc, current, original in bundles:
        old = {path:cap for path,_,cap in layouts(original)}
        for path, at, cap in layouts(current):
            require(path in old, 'Layout topology changed')
            stock = old[path] or 32
            if cap != 128 or stock >= 128: continue
            bound = capacity_bound(stock, pairs)
            require(bound <= cap, 'Translation needs larger bound: '+str(path))
            if bound == cap: continue
            changes.append({'offset':disc+at, 'before':128, 'after':bound,
                            'bundle':rid, 'path':list(path), 'stock_capacity':stock})
    changes.sort(key=lambda c:c['offset'])
    require(all(a['offset']+2 <= b['offset'] for a,b in zip(changes,changes[1:])), 'Overlap')
    return changes, len(pairs)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    changes, pairs = plan()
    print('DRY RUN:',len(changes),'capacity fields;',pairs,'distinct translation pairs')
    print('Capacity distribution:',dict(sorted(Counter(c['after'] for c in changes).items())))
    print('Samples:',json.dumps(changes[:8],indent=2))
    if not args.write: return
    require(not OUTPUT.exists(), 'Output already exists')
    shutil.copyfile(BASE, OUTPUT)
    with OUTPUT.open('r+b') as f:
        for c in changes:
            f.seek(c['offset']); require(f.read(2)==struct.pack('<H',c['before']), 'Preimage mismatch')
            f.seek(c['offset']); f.write(struct.pack('<H',c['after']))
    digest, base_digest = hashlib.sha256(), hashlib.sha256()
    index, pos = 0, 0
    with BASE.open('rb') as a, OUTPUT.open('rb') as b:
        while True:
            raw = a.read(8*1024*1024)
            if not raw: break
            expected = bytearray(raw); base_digest.update(raw)
            while index < len(changes) and changes[index]['offset'] < pos+len(raw):
                c = changes[index]; at = c['offset']-pos
                require(0 <= at <= len(raw)-2, 'Chunk boundary')
                struct.pack_into('<H', expected, at, c['after']); index += 1
            actual = b.read(len(raw)); require(actual == expected, 'Unexpected ISO change')
            digest.update(actual); pos += len(raw)
        require(not b.read(1) and index==len(changes), 'Size/patch count mismatch')
    report = {'version':VERSION,'base':BASE.name,'output':OUTPUT.name,
              'sha256':digest.hexdigest(),'base_sha256':base_digest.hexdigest(),
              'size':OUTPUT.stat().st_size,'translation_pairs':pairs,
              'whole_disc_verified':True,'runtime_verified':False,'changes':changes}
    OUTPUT.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='changes'},indent=2))


if __name__ == '__main__': main()
