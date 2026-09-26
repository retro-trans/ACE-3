"""0.1.25: put the English history crawl into the resource the game really loads. Dry-run unless --write.

The Stage 1 ending demo never reads resource 4010. PCSX2's read log shows it loading resource 701009, an
LZSS-compressed variant of the same scene (see packed_resource.py); that copy still held the Japanese crawl
table. This build unpacks 701009, swaps its STUF text table for the English one already built for 4010 in
0.1.24, repacks it and replaces the resource. Nothing else inside the scene changes.
"""
import argparse
import hashlib
import json
import struct
from build_ui_patch import ROOT, inner_bnd, require, u32
from dialogue_corpus import archive, parse_table
from build_history_patch import chunks
from packed_resource import pack, unpack
import build_dialogue_patch as builder

VERSION = '0.1.25'
BASE = ROOT/'work/output/ACE3-English-0.1.24.iso'
OUTPUT = ROOT/'work/output/ACE3-English-0.1.25.iso'
PACKED, PLAIN = 701009, 4010
KANJI = builder.re.compile('[぀-ヿ一-鿿]')


def stuf_table(scene):
    (a, z), = [(lo, hi) for tag, lo, hi in chunks(scene) if tag == b'STUF']
    bnd = scene[a+16:z]; (key, ta, tz), = inner_bnd(bnd)
    require(key == 3, 'Unexpected crawl bundle')
    return a, z, bnd, bnd[ta:tz]


def plan():
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        def get(rid):
            _, size, off, _ = next(e for e in entries if e[3] == rid); f.seek(fi['offset']+off); return f.read(size)
        packed, plain = get(PACKED), get(PLAIN)
    scene, used = unpack(packed)
    require(not any(packed[used:]), 'Unexpected data after the packed stream')
    a, z, bnd, japanese = stuf_table(scene)
    _, _, _, english = stuf_table(plain)
    rows = parse_table(japanese)[3]
    require(len(rows) == 39 and all(KANJI.search(r[3].decode('cp932')) for r in rows), 'Packed scene does not hold the stock crawl')
    english = english[:parse_table(english)[0]]
    require(not KANJI.search(english[parse_table(english)[1]:].decode('cp932', 'replace')), 'English table still holds Japanese')
    replaced = builder.rebuild_bundle(bnd, {3:english})
    header = bytearray(scene[a:a+16]); struct.pack_into('<I', header, 4, len(replaced)+16)
    new_scene = scene[:a]+bytes(header)+replaced+scene[z:]
    before, after = chunks(scene), chunks(new_scene)
    require([t for t, _, _ in before] == [t for t, _, _ in after], 'Scene chunk order changed')
    for (tag, lo, hi), (_, nlo, nhi) in zip(before, after):
        if tag != b'STUF': require(scene[lo:hi] == new_scene[nlo:nhi], 'Unrelated scene data changed')
    repacked = pack(new_scene)
    require(unpack(repacked)[0] == new_scene, 'Packed scene does not round-trip')
    report = {'resource_id':PACKED, 'kind':'packed_scene_crawl', 'old_packed_size':len(packed), 'new_packed_size':len(repacked),
              'old_unpacked_size':len(scene), 'new_unpacked_size':len(new_scene), 'english_lines':len(parse_table(english)[3]),
              'japanese_crawl_left':'熱血クーデター'.encode('cp932') in new_scene,
              'unpacked_sha256':hashlib.sha256(new_scene).hexdigest()}
    return {PACKED:repacked}, [report]


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    replacements, reports = plan()
    print('DRY RUN', json.dumps(reports, indent=1))
    if not a.write: return
    builder.VERSION, builder.BASE, builder.OUTPUT = VERSION, BASE, OUTPUT
    builder.build(replacements, reports)
    path = OUTPUT.with_suffix('.json'); doc = json.loads(path.read_text(encoding='utf-8'))
    doc['coverage'] = 'History crawl in packed scene 701009 (the copy the Stage 1 ending demo loads). Everything else inherited from 0.1.24.'
    doc['runtime_verified'] = False
    path.write_text(json.dumps(doc, indent=2)+'\n', encoding='utf-8')
    inputs = [ROOT/'tools/build_crawl_packed_patch.py', ROOT/'tools/packed_resource.py', ROOT/'tools/build_dialogue_patch.py']
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps({'version':VERSION, 'base':BASE.name,
        'base_sha256':'6566c3b9222c46f56d5e4763a1e7a3b4008686dad4922820006c3a1b2535331c', 'sha256':doc['sha256'],
        'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
