"""0.1.34/0.1.35: pilot battle shouts and per-unit name labels in the unit VMD resources, the in-mission series-name
table, and the on-disc "Kizz Munt" -> "Kids Munt" fix in the Encyclopedia. Dry-run unless --write.

Unit resources 28xxxxx are VMD chunk containers; three chunks hold text tables: FNM (unit name shown as the
target label), PPN1 (pilot short name shown above battle shouts) and PMS (the shouts). 120 of them have a packed
twin 48xxxxx that unpacks byte-for-byte to the plain one; it is unknown which twin the game loads, so both get
the same bytes (the twin is repacked with tools/packed_resource.py, the codec proven in 0.1.27). Every table is
rebuilt IN PLACE inside its original chunk: the slot index is cut to the IDs the unit uses and the English pool
must fit the freed space; units whose English does not fit are reported and left Japanese.
    python tools/build_shouts_patch.py --version 0.1.34 --base 0.1.33 [--write]
"""
import argparse
import hashlib
import json
import re
import struct
from build_ui_patch import ROOT, require, u32
from dialogue_corpus import archive, parse_table, INDEX
from build_flight_save_patch import parts
from build_intermission_patch import replace_rows
from packed_resource import is_packed, unpack, pack
from ui_font import measure_text, patch_font
import build_dialogue_patch as builder
import build_dialogs_patch as dialogs
import build_scene_patch as scene

UI = ROOT/'work/translation/en/ui_034.json'
JP = re.compile('[぀-ヿ一-鿿]')
TAG = re.compile(r'<[^>]*>')
GAMEPLAY = list(range(1200000, 1200012))
MENU = list(range(4002050, 4002059))
SHOUT_WIDTH, SHOUT_LINES = 400, 4
LITERALS = {'え': 'Eh?'}  # bare one-character stub rows not covered by the dialogue index


def reviewed():
    indexed = {r['id']:r for r in json.loads(INDEX.read_text(encoding='utf-8'))['rows']}
    out = {}
    for path in sorted((ROOT/'work/translation/en/dialogue').glob('batch_*.json')):
        doc = json.loads(path.read_text(encoding='utf-8')); rows = doc.get('rows', []) if isinstance(doc, dict) else []
        for row in rows if isinstance(rows, list) else []:
            if row.get('status') == 'meaning_reviewed': out[indexed[row['id']]['source_sha256']] = row
    return out


def name_lookups():
    units = {}
    for fn in ('unit_names_014_a.json', 'unit_names_014_b.json', 'unit_name_variants_014.json'):
        for r in json.loads((ROOT/'work/translation/en'/fn).read_text(encoding='utf-8'))['rows']: units[r['source']] = r['en']
    pilots = {}
    for cat in json.loads((ROOT/'work/translation/en/names_023.json').read_text(encoding='utf-8'))['categories']:
        for r in cat['rows']: pilots.setdefault(r['source'], r['en'])
    extra = json.loads((ROOT/'work/translation/en/names_034.json').read_text(encoding='utf-8'))
    for r in extra['unit_rows']: units.setdefault(r['source'], r['en'])
    for r in extra['pilot_rows']: pilots.setdefault(r['source'], r['en'])
    return units, pilots


def rebuild_in_place(table, texts):
    """Rebuild a text table inside its own byte length: single ID range over the used IDs, English pool."""
    size, pointers, count, rows = parse_table(table)  # table may carry chunk padding after it
    ids = sorted(text_id for _, text_id, _, _ in rows); first, last = ids[0], ids[-1]
    header = bytearray(table[:28]); struct.pack_into('<I', header, 12, 1); struct.pack_into('<I', header, 16, last-first+1)
    struct.pack_into('<I', header, 20, 40)
    out = header+struct.pack('<3I', 0, first, last)+bytearray(4*(last-first+1))
    pool = {}
    for _, text_id, _, raw in rows:
        target = texts[text_id]; encoded = target.encode('cp932'); require(b'\0' not in encoded, 'Embedded null')
        if encoded not in pool: pool[encoded] = len(out); out += encoded+b'\0'
        struct.pack_into('<I', out, 40+4*(text_id-first), pool[encoded])
    require(len(out) <= len(table), 'Table does not fit: needs %d of %d bytes' % (len(out), len(table)))
    used = len(out.rstrip(bytes(1)))
    out += bytes(len(table)-len(out)); struct.pack_into('<I', out, 4, size if used <= size else len(table))
    got = parse_table(bytes(out))[3]
    require([(i, r) for _, i, _, r in got] == [(i, texts[i].encode('cp932')) for _, i, _, _ in rows], 'In-place table round-trip failed')
    return bytes(out), len(table)


def game_lookup(table, text_id):
    """Mirror of the game's string lookup (SLPS_257.84 at 0x1b60c0): binary search of the range index at +28 by
    (first, last), slot = base + id - first, pointer array at the offset stored in header word +20. The header words
    +4 (size), +8, +16 (count) and +24 are never read by it."""
    ranges, pointers = u32(table, 12), u32(table, 20); lo, hi = 0, ranges-1
    while lo <= hi:
        mid = (lo+hi) >> 1; base, first, last = struct.unpack_from('<3I', table, 28+mid*12)
        if last < text_id: lo = mid+1
        elif text_id < first: hi = mid-1
        else:
            pointer = u32(table, pointers+4*(base+text_id-first))
            return None if not pointer else table[pointer:table.index(b'\0', pointer)]
    return None


def rebuild_compact(table, texts):
    """Single-row table whose English does not fit the standard layout: the pointer array is moved into the unread
    header word +24, which frees the 8 bytes from +40 for the string (48-byte PPN1 tables: 'Hikaru')."""
    size, pointers, count, rows = parse_table(table); require(len(rows) == 1, 'Compact layout is for one-row tables')
    _, text_id, _, _ = rows[0]; encoded = texts[text_id].encode('cp932')+b'\0'
    require(len(encoded) <= len(table)-40, 'Table does not fit even compacted: needs %d of %d bytes' % (40+len(encoded), len(table)))
    out = bytearray(table[:28]); struct.pack_into('<4I', out, 12, 1, 1, 24, 40); out += struct.pack('<3I', 0, text_id, text_id)+encoded
    out += bytes(len(table)-len(out)); struct.pack_into('<I', out, 4, len(table)); out = bytes(out)
    require(game_lookup(out, text_id) == encoded[:-1] and game_lookup(table, text_id) == rows[0][3], 'Compact table lookup failed')
    return out, len(table)


def chunk_table(data, tag):
    at = data.find(tag)
    if at < 0: return None
    tab = at+16
    try: size = parse_table(data, tab)[0]
    except ValueError: return None
    avail = u32(data, at+4)-16; require(avail >= size, 'Chunk smaller than its table')
    return tab, avail  # the whole chunk payload (table plus any padding) is usable


def unit_resources(get, entries, font, translations, units, pilots):
    changes, reports, skipped = {}, [], []
    ids = {e[3] for e in entries}
    for rid in sorted(r for r in ids if 2800000 <= r < 2900000):
        data = get(rid); edits = {}; report = {'resource_id':rid, 'kind':'unit_vmd', 'tables':{}}
        # FNM / PPN1: one-row name tables
        for tag, lookup, what in ((b'FNM\0', units, 'unit'), (b'PPN1', pilots, 'pilot')):
            found = chunk_table(data, tag)
            if not found: continue
            tab, size = found; rows = parse_table(data, tab)[3]
            if not rows or not JP.search(rows[0][3].decode('cp932')): continue
            source = rows[0][3].decode('cp932'); en = lookup.get(source)
            if en is None: skipped.append((rid, what, 'no spelling for '+source)); continue
            layout = 'standard'
            try: new, _ = rebuild_in_place(data[tab:tab+size], {rows[0][1]:en})
            except ValueError:
                try: new, _ = rebuild_compact(data[tab:tab+size], {rows[0][1]:en}); layout = 'compact'
                except ValueError as ex: skipped.append((rid, what, str(ex))); continue
            require(game_lookup(new, rows[0][1]) == en.encode('cp932'), 'Game lookup mismatch')
            edits[tab] = new; report['tables'][what] = {'source':source, 'en':en, 'width':measure_text(font, en)[0], 'layout':layout}
        # PMS: the shouts
        found = chunk_table(data, b'PMS\0')
        if found:
            tab, size = found; rows = parse_table(data, tab)[3]; texts = {}; missing = 0
            for _, text_id, _, raw in rows:
                h = hashlib.sha256(raw).hexdigest()
                if b'<sp(' not in raw and not JP.search(raw.decode('cp932')): texts[text_id] = raw.decode('cp932'); continue
                if raw.decode('cp932') in LITERALS: texts[text_id] = LITERALS[raw.decode('cp932')]; continue
                if h not in translations: missing += 1; continue
                target = translations[h]['target']
                require(builder.TOKEN.findall(raw.decode('cp932')) == builder.TOKEN.findall(target), 'Commands changed: '+translations[h]['id'])
                try: target = scene.wrap_words(target, font, SHOUT_WIDTH, SHOUT_LINES)
                except ValueError: target = scene.wrap_words(target.replace('\n', ' '), font, SHOUT_WIDTH, SHOUT_LINES)
                texts[text_id] = target
            if missing: skipped.append((rid, 'shouts', '%d rows untranslated' % missing))
            else:
                try:
                    new, _ = rebuild_in_place(data[tab:tab+size], texts); edits[tab] = new
                    report['tables']['shouts'] = {'rows':len(rows), 'bytes_used':len(new.rstrip(b'\0')), 'bytes_available':size}
                except ValueError as ex: skipped.append((rid, 'shouts', str(ex)))
        if not edits: continue
        out = bytearray(data)
        for tab, new in edits.items(): out[tab:tab+len(new)] = new
        out = bytes(out); require(len(out) == len(data), 'VMD size changed')
        changes[rid] = out; report['size'] = len(out)
        twin = rid+2000000
        if twin in ids:
            packed = get(twin); require(is_packed(packed), 'Twin is not packed'); plain, used = unpack(packed)
            require(plain == data, 'Packed twin differs from the plain resource: %s' % twin)
            repacked = pack(out); require(unpack(repacked)[0] == out, 'Repacked twin does not round-trip')
            if len(repacked) < len(packed): repacked += bytes(len(packed)-len(repacked))
            changes[twin] = repacked; report['twin'] = {'resource_id':twin, 'old_packed':len(packed), 'new_packed':len(repacked)}
        reports.append(report)
    return changes, reports, skipped


def encyclopedia_fix(get, entries):
    """Rows of the Encyclopedia page tables that still say Kizz Munt (inserted in 0.1.22 before the ruling)."""
    changes, reports = {}, []
    for rid in MENU:
        if rid not in {e[3] for e in entries}: continue
        data = get(rid)
        try: p = parts(data)
        except ValueError: continue
        edits = {}
        for tid, chunk in p.items():
            try: rows = parse_table(chunk)[3]
            except ValueError: continue
            mappings = {s:(r.decode('cp932'), r.decode('cp932').replace('Kizz Munt', 'Kids Munt')) for s, i, _, r in rows if b'Kizz Munt' in r}
            if mappings: edits[tid] = dialogs.append_rows(chunk, mappings); reports.append({'resource_id':rid, 'table_id':tid, 'rows':sorted(mappings)})
        if edits: changes[rid] = builder.rebuild_bundle(data, edits)
    return changes, reports


def plan(base):
    changes, reports, inventory = dialogs.plan(base, UI, GAMEPLAY)
    with base.open('rb') as f:
        fi, es = archive(f)
        def get(rid):
            e = next(x for x in es if x[3] == rid); f.seek(fi['offset']+e[2]); return f.read(e[1])
        font = parts(get(1200000))[2500]
        units, pilots = name_lookups()
        vmd, vmd_reports, skipped = unit_resources(get, es, font, reviewed(), units, pilots)
        enc, enc_reports = encyclopedia_fix(get, es)
    require(not (set(changes) & set(vmd)) and not (set(changes) & set(enc)), 'Resource planned twice')
    changes.update(vmd); changes.update(enc); reports += vmd_reports+enc_reports
    summary = {'resources':len(changes), 'ui_tables':inventory, 'allocation_adjustments':sum(len(r.get('allocations', [])) for r in reports),
               'units_changed':len(vmd_reports), 'units_with_shouts':sum('shouts' in r['tables'] for r in vmd_reports),
               'unit_names':sum('unit' in r['tables'] for r in vmd_reports), 'pilot_names':sum('pilot' in r['tables'] for r in vmd_reports),
               'twins_repacked':sum('twin' in r for r in vmd_reports), 'skipped':skipped, 'encyclopedia_rows':enc_reports}
    return changes, reports, summary


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--version', required=True); ap.add_argument('--base', required=True)
    ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    base = ROOT/('work/output/ACE3-English-%s.iso' % a.base); output = ROOT/('work/output/ACE3-English-%s.iso' % a.version)
    changes, reports, summary = plan(base)
    print('DRY RUN', json.dumps({k:v for k, v in summary.items() if k != 'skipped'}))
    print('skipped', len(summary['skipped']), json.dumps(summary['skipped'][:12]))
    if not a.write: return
    builder.VERSION, builder.BASE, builder.OUTPUT = a.version, base, output
    builder.build(changes, reports)
    path = output.with_suffix('.json'); doc = json.loads(path.read_text(encoding='utf-8'))
    doc['coverage'] = summary; doc['runtime_verified'] = False
    path.write_text(json.dumps(doc, indent=2)+'\n', encoding='utf-8')
    inputs = [ROOT/'tools/build_shouts_patch.py', UI, ROOT/'work/translation/en/names_034.json']+sorted((ROOT/'work/translation/en/dialogue').glob('batch_1[2-6]*.json'))
    output.with_suffix('.manifest.json').write_text(json.dumps({'version':a.version, 'base':base.name,
        'base_sha256':json.loads(base.with_suffix('.json').read_text(encoding='utf-8'))['sha256'], 'sha256':doc['sha256'],
        'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
