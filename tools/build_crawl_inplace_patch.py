"""0.1.27 (first built as 0.1.26 with a faulty packer): English history crawl that changes no size or offset anywhere. Dry-run unless --write.

0.1.25 and 0.1.26 froze the Stage 1 ending demo (PCSX2: TLB miss, load from 0x020226B0 at pc 0x0012AFF0).
The cause was the packer, not the scene: the game's decoder treats a reference's field as an absolute offset
while fewer than 4096 bytes are out, and packed_resource.py wrote the sliding form there, so the first bytes of
the scene (its chunk header) unpacked wrong. That is fixed in packed_resource.py and cross-checked by a
transcription of the game's decoder in the tests. Whether a larger scene would also have been a problem is
unknown, so this build still takes no chances with sizes: it keeps both copies of the scene (packed 701009, the one the demo loads, and plain 4010)
byte-for-byte the original size: the crawl table is rebuilt inside its original 2,304 bytes. To make room the
slot index is cut from 200 to the 81 IDs the Japanese crawl uses (IDs 82-200 were empty), and the English is a
tightened version laid out inside the original span, IDs 11-81, so the demo's scroll length is unchanged too.
"""
import argparse
import hashlib
import json
import struct
from build_ui_patch import ROOT, inner_bnd, require, u32
from dialogue_corpus import archive, parse_table
from build_history_patch import chunks
from build_scene_patch import wrap_words
from packed_resource import pack, unpack
from ui_font import measure_text
import build_dialogue_patch as builder

VERSION = '0.1.27'
BASE = ROOT/'work/output/ACE3-English-0.1.24.iso'          # 0.1.25 and 0.1.26 are withdrawn
OUTPUT = ROOT/'work/output/ACE3-English-0.1.27.iso'
TEXT = ROOT/'work/translation/en/opening_history_compact.json'
PACKED, PLAIN = 701009, 4010
SLOTS, WIDTH, LAST_SLOT = 81, 470, 80
KANJI = builder.re.compile('[぀-ヿ一-鿿]')


def layout(sections, font):
    """sections: [{'heading_slot', 'heading', 'paragraphs'}]. Returns {slot: line}; blank slots separate paragraphs."""
    rows = {}
    for n, section in enumerate(sections):
        slot = section['heading_slot']
        require(not rows or slot > max(rows)+1, 'Section %d starts inside the previous one' % n)
        rows[slot] = section['heading']; slot += 2
        for i, paragraph in enumerate(section['paragraphs']):
            for line in wrap_words(paragraph, font, WIDTH, 99).split('\n'):
                rows[slot] = line; slot += 1
            slot += 1
    require(max(rows) <= LAST_SLOT, 'Crawl runs past the original last line: slot %d' % max(rows))
    return rows


def build_table(stock, rows):
    size, pointers, count, source = parse_table(stock)
    require(count == 200 and size == 2304 and pointers == 40, 'Unexpected crawl table')
    require(struct.unpack_from('<3I', stock, 28) == (0, 1, 200), 'Unexpected ID range')
    require(max(r[0] for r in source) == LAST_SLOT, 'Stock crawl span changed')
    out = bytearray(stock[:pointers]); struct.pack_into('<3I', out, 28, 0, 1, SLOTS); struct.pack_into('<I', out, 16, SLOTS)
    out += bytes(SLOTS*4)
    for slot, line in sorted(rows.items()):
        raw = line.encode('cp932'); require(b'\0' not in raw, 'Embedded null')
        struct.pack_into('<I', out, pointers+slot*4, len(out)); out += raw+b'\0'
    require(len(out) <= size, 'English crawl needs %d bytes, the table has %d' % (len(out), size))
    used = len(out); out += bytes(size-len(out))
    parsed = parse_table(bytes(out))
    require(parsed[0] == size and {s:r.decode('cp932') for s, _, _, r in parsed[3]} == rows, 'Crawl table round trip failed')
    return bytes(out), used


def swap_table(scene, table):
    (a, z), = [(lo, hi) for tag, lo, hi in chunks(scene) if tag == b'STUF']
    bnd = scene[a+16:z]; (key, ta, tz), = inner_bnd(bnd)
    require(key == 3 and parse_table(bnd[ta:tz])[0] == len(table), 'Crawl table is not where it should be')
    start = a+16+ta
    out = scene[:start]+table+scene[start+len(table):]
    require(len(out) == len(scene), 'Scene size changed')
    return out, start


def plan():
    doc = json.loads(TEXT.read_text(encoding='utf-8'))
    require(doc['review']['status'] == 'meaning_reviewed', 'Unreviewed crawl text')
    with next(ROOT.glob('*.iso')).open('rb') as f:
        fi, entries = archive(f)
        def get(rid):
            _, size, off, _ = next(e for e in entries if e[3] == rid); f.seek(fi['offset']+off); return f.read(size)
        stock_plain, stock_packed = get(PLAIN), get(PACKED)
    with BASE.open('rb') as f:                                  # the stock gameplay font has no Latin glyphs
        fi, entries = archive(f)
        def current(rid):
            _, size, off, _ = next(e for e in entries if e[3] == rid); f.seek(fi['offset']+off); return f.read(size)
        game, base_plain, base_packed = current(1200000), current(PLAIN), current(PACKED)
    require(base_packed == stock_packed, 'Base build already changed the packed scene')
    for (tag, lo, hi), (_, nlo, nhi) in zip(chunks(stock_plain), chunks(base_plain)):
        if tag != b'STUF': require(stock_plain[lo:hi] == base_plain[nlo:nhi], 'Base build changed scene 4010 outside its text chunk')
    font = next(game[a:z] for k, a, z in inner_bnd(game) if k == 2500)
    rows = layout(doc['sections'], font)
    for line in rows.values():
        require(not KANJI.search(line) and measure_text(font, line)[0] <= WIDTH, 'Bad crawl line: %r' % line)
    scene, used = unpack(stock_packed)
    require(not any(stock_packed[used:]), 'Unexpected data after the packed stream')
    (a, z), = [(lo, hi) for tag, lo, hi in chunks(scene) if tag == b'STUF']
    stock_table = scene[a+16:z][inner_bnd(scene[a+16:z])[0][1]:][:2304]
    table, used_bytes = build_table(stock_table, rows)
    new_scene, at = swap_table(scene, table)
    new_plain, at_plain = swap_table(stock_plain, table)
    for old, new, where in ((scene, new_scene, at), (stock_plain, new_plain, at_plain)):
        require(old[:where] == new[:where] and old[where+2304:] == new[where+2304:], 'Bytes outside the crawl table changed')
    repacked = pack(new_scene)
    require(unpack(repacked)[0] == new_scene, 'Packed scene does not round-trip')
    require(len(repacked) <= len(stock_packed), 'Packed scene grew')
    repacked += bytes(len(stock_packed)-len(repacked))         # same packed size as stock, zero padded like stock
    report = {'kind':'history_crawl_in_place', 'lines':len(rows), 'last_slot':max(rows), 'table_bytes_used':used_bytes, 'table_size':2304,
              'scene_size':len(new_scene), 'packed_size':len(repacked), 'widest_line':max(measure_text(font, l)[0] for l in rows.values()),
              'rows':[{'slot':s, 'text':t} for s, t in sorted(rows.items())]}
    return {PACKED:repacked, PLAIN:new_plain}, [dict(report, resource_id=PACKED), {'resource_id':PLAIN, 'kind':'history_crawl_in_place_plain_twin', 'size':len(new_plain)}]


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    replacements, reports = plan()
    print('DRY RUN', json.dumps({k:v for k, v in reports[0].items() if k != 'rows'}))
    for row in reports[0]['rows']: print('%3d  %s' % (row['slot'], row['text']))
    if not a.write: return
    builder.VERSION, builder.BASE, builder.OUTPUT = VERSION, BASE, OUTPUT
    builder.build(replacements, reports)
    path = OUTPUT.with_suffix('.json'); doc = json.loads(path.read_text(encoding='utf-8'))
    doc['coverage'] = 'History crawl rebuilt inside its original table in packed scene 701009 and plain 4010; both scenes keep their original size.'
    doc['runtime_verified'] = False
    path.write_text(json.dumps(doc, indent=2)+'\n', encoding='utf-8')
    inputs = [TEXT, ROOT/'tools/build_crawl_inplace_patch.py', ROOT/'tools/packed_resource.py', ROOT/'tools/build_dialogue_patch.py']
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps({'version':VERSION, 'base':BASE.name,
        'base_sha256':'6566c3b9222c46f56d5e4763a1e7a3b4008686dad4922820006c3a1b2535331c', 'sha256':doc['sha256'],
        'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
