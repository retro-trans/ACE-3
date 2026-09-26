"""0.1.18: remaining Help/confirmation dialogs, option screens and Free Mission label fixes."""
import argparse
import hashlib
import json
import re
import struct
from build_ui_patch import ROOT, inner_bnd, require, u32
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts, controls, wrap
from build_intermission_patch import replace_rows, FORMAT
from build_hangar_fix import layouts, capacity_bound
from gameplay_font import supplement
from ui_font import patch_font, measure_text, font_map, codepoint
import build_dialogue_patch as builder

VERSION = '0.1.18'
BASE = ROOT/'work/output/ACE3-English-0.1.17.iso'
OUTPUT = ROOT/'work/output/ACE3-English-0.1.18.iso'
INPUT = ROOT/'work/translation/en/dialogs_options_018.json'
KANJI = re.compile('[぀-ヿ一-鿿]')
MENU_BUNDLES = range(4002050, 4002059)
DIALOG_LINES = 10  # the stock by-series help fills ten lines in the user's capture
SAMPLE = 'W'*16    # stands in for a runtime %s name that is still Japanese


def fit(row, original, font):
    """Check one English row against the stock Japanese it replaces."""
    target = row['en']
    require(not KANJI.search(target), 'Untranslated Japanese in target')
    icons, tags = controls(original); new_icons, new_tags = controls(target)
    # Encyclopedia link tags may move with English word order; everything else keeps its order.
    if row.get('page_text'): tags, new_tags = sorted(tags), sorted(new_tags)
    require((icons, tags) == (new_icons, new_tags), 'Control code changed: %r' % target)
    require(original.count('㍻') == target.count('㍻'), 'Ace mark changed')
    require(FORMAT.findall(original) == FORMAT.findall(target), 'Format arguments changed')
    # A bare ASCII percent in a printf-style message is an invalid conversion.
    require('%' not in FORMAT.sub('', target), 'Stray percent sign: %r' % target)
    if row['dialog']:
        target = wrap(target, font, 410)
        shown = target.replace('%s', SAMPLE)
        require(len(shown.split('\n')) <= DIALOG_LINES, 'Dialog too tall: %r' % target)
        require(len(shown) <= 255, 'Dialog exceeds its 255-character widget')
        require(max(measure_text(font, shown)) <= 410, 'Dialog too wide: %r' % target)
    else:
        # Secret goals are centred two-line labels; everything else is one line.
        require(len(target.split('\n')) <= row.get('max_lines', 1), 'Label has too many lines: %r' % target)
        require(len(target) <= row.get('max_chars', 128), 'Label exceeds bounded allocation')
        # Link tags take no room on the page.
        shown = re.sub(r'<[^<>]*>', '', target) if row.get('page_text') else target
        require(max(measure_text(font, shown)) <= row['limit'],
                'Width exceeded %s > %s: %r' % (max(measure_text(font, shown)), row['limit'], target))
    return target


def append_rows(table, mappings):
    """replace_rows for page text: fit() has already compared the tags without regard to order."""
    size, ptr, count, rows = parse_table(table)
    require(set(mappings) <= {s for s, _, _, _ in rows}, 'Invalid target slot')
    output, expected = bytearray(table[:size]), []
    for slot, tid, at, raw in rows:
        if slot in mappings:
            source, target = mappings[slot]
            require(raw.decode('cp932') == source, 'Source preimage mismatch')
            raw = target.encode('cp932'); require(b'\0' not in raw, 'Embedded null')
            struct.pack_into('<I', output, ptr+slot*4, len(output)); output.extend(raw+b'\0')
        expected.append((slot, tid, raw))
    output.extend(bytes(builder.align(len(output), 32)-len(output)))
    struct.pack_into('<I', output, 4, len(output))
    require([(s, i, r) for s, i, _, r in parse_table(output)[3]] == expected, 'Page table round trip failed')
    require(output[ptr+count*4:size] == table[ptr+count*4:size], 'Original pool changed')
    return bytes(output)


def plan(base=None, source=None, bundles=MENU_BUNDLES):
    base, source = base or BASE, source or INPUT
    doc = json.loads(source.read_text(encoding='utf-8'))
    require(doc['review']['status'] == 'meaning_reviewed', 'Unreviewed draft')
    changes, reports, inventory, pairs, planned = {}, [], [], set(), []
    with base.open('rb') as f, next(ROOT.glob('*.iso')).open('rb') as o:
        fi, es = archive(f); oi, oe = archive(o)
        old = {rid:(sz, off) for _, sz, off, rid in oe}
        def get(stream, info, size, off):
            stream.seek(info['offset']+off); return stream.read(size)
        canonical = parts(get(f, fi, *next((sz, off) for _, sz, off, rid in es if rid == 4002050)))
        game = parts(get(f, fi, *next((sz, off) for _, sz, off, rid in es if rid == 1200000)))
        donors = [('menu19', canonical[2500], canonical[2000]), ('game19', game[2500], game[2000]),
                  ('global12', get(o, oi, *old[35]), get(o, oi, *old[36]))]
        for _, size, off, rid in es:
            if rid not in bundles: continue
            data = get(f, fi, size, off); p = parts(data)
            stock = parts(get(o, oi, *old[rid]))
            selected = []
            for cat in doc['categories']:
                tid = cat['table_id']
                if tid not in p: continue
                try: rows = {i:(s, r.decode('cp932')) for s, i, _, r in parse_table(p[tid])[3]}
                except ValueError: continue
                # The same table ID can hold another category; identify copies by preimage.
                if not all(r['text_id'] in rows and rows[r['text_id']] == (r['slot'], r['source']) for r in cat['rows']):
                    continue
                if cat['complete']:
                    left = [i for i, (_, t) in rows.items() if KANJI.search(t) and i not in {r['text_id'] for r in cat['rows']}]
                    require(not left, 'Incomplete category copy %s/%s' % (rid, tid))
                selected.append((cat, {i:r.decode('cp932') for _, i, _, r in parse_table(stock[tid])[3]}))
            if not selected: continue
            require(2500 in p or rid == 4002055, 'Unknown shared font user')
            font, aliases = patch_font(p.get(2500, canonical[2500]))
            used = ''.join(r['en'] for cat, _ in selected for r in cat['rows']).replace('\n', '')
            missing = sorted({c for c in used if codepoint(c) not in font_map(font)[0]})
            edits, font_report = {}, {'aliases':aliases, 'missing_used_before':missing}
            if missing:
                require(2500 in p, 'Shared font lacks a required glyph: '+''.join(missing))
                font, texture, font_report = supplement(p[2500], p[2000], donors, used)
                require(not any(x['character'] in used and x['source_height'] == 12 for x in font_report['additions']),
                        'New text uses a small fallback glyph')
                edits[2000] = texture
            if 2500 in p and font != p[2500][:u32(p[2500], 4)]: edits[2500] = font
            tables = []
            for cat, original in selected:
                tid, mappings, rr = cat['table_id'], {}, []
                for r in cat['rows']:
                    target = fit(r, original[r['text_id']], font)
                    # Page text is not drawn by the bounded label widgets, so it must not size them.
                    if not r.get('page_text'): pairs.add((original[r['text_id']], target))
                    if target != r['source']: mappings[r['slot']] = (r['source'], target)
                    rr.append({'slot':r['slot'], 'text_id':r['text_id'], 'target':target, 'changed':target != r['source'],
                               'width':max(measure_text(font, target.replace('%s', SAMPLE))), 'limit':r['limit']})
                if mappings: edits[tid] = (append_rows if cat.get('page_text') else replace_rows)(p[tid], mappings)
                tables.append({'table_id':tid, 'category':cat['category'], 'rows':rr})
                inventory.append([rid, tid, len(mappings)])
            planned.append((rid, data, p, edits, tables, font_report))
        # Raise only the bounded 0.1.16 label allocations that the new pairs exceed;
        # stock allocations of 128 and above already cover their text.
        for rid, data, p, edits, tables, font_report in planned:
            alloc = []
            limits = {path:cap for path, _, cap in layouts(get(o, oi, *old[rid]))}
            for path, at, cap in layouts(data):
                bound = capacity_bound(limits[path], pairs)
                if (limits[path] or 32) >= 128 or bound <= cap: continue
                require(bound <= 128, 'New static label exceeds bounded plan')
                top = path[0]
                start = next(a for k, a, z in inner_bnd(data[:u32(data, 4)]) if k == top)
                chunk = bytearray(edits.get(top, p[top])); struct.pack_into('<H', chunk, at-start, bound); edits[top] = bytes(chunk)
                alloc.append({'path':list(path), 'before':cap, 'after':bound})
            if edits:
                changes[rid] = builder.rebuild_bundle(data, edits)
                reports.append({'resource_id':rid, 'kind':'dialogs_and_options', 'tables':tables, 'font':font_report,
                                'allocations':alloc, 'changed_subresources':sorted(edits),
                                'old_size':len(data), 'new_size':len(changes[rid])})
    return changes, reports, inventory


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    changes, reports, inventory = plan()
    summary = {'resources':len(changes), 'tables':inventory, 'text_instances':sum(n for _, _, n in inventory),
               'allocation_adjustments':sum(len(r['allocations']) for r in reports),
               'allocation_bytes_added':sum(x['after']-x['before'] for r in reports for x in r['allocations'])}
    print('DRY RUN', json.dumps(summary))
    for r in reports:
        print(r['resource_id'], r['old_size'], '->', r['new_size'], 'changed', r['changed_subresources'],
              'missing glyphs', r['font'].get('missing_used_before'), 'allocations', len(r['allocations']))
        if r['resource_id'] == 4002050:
            for t in r['tables']:
                for row in t['rows']:
                    if (t['table_id'], row['text_id']) in ((3091, 12), (3091, 5), (3021, 27), (3054, 72), (3076, 108), (3013, 192)):
                        print(t['table_id'], json.dumps(row, ensure_ascii=True))
    if not a.write: return
    builder.VERSION, builder.BASE, builder.OUTPUT = VERSION, BASE, OUTPUT
    builder.build(changes, reports)
    path = OUTPUT.with_suffix('.json'); doc = json.loads(path.read_text(encoding='utf-8'))
    doc['coverage'] = summary; doc['runtime_verified'] = False
    doc['limitations'] = ('Offline verified only. Song titles, story movie titles, mission titles, secret conditions, '
                          'encyclopedia terms, pilot names and ability descriptions remain Japanese.')
    path.write_text(json.dumps(doc, indent=2)+'\n', encoding='utf-8')
    inputs = [INPUT, ROOT/'tools/build_dialogs_patch.py', ROOT/'tools/build_dialogue_patch.py', ROOT/'tools/repair_disc_layout.py']
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps({'version':VERSION, 'base':BASE.name,
        'base_sha256':'9194ff8b9d41728aeebce03c9e57a2cf9ccb789e1188f634006939e79e6f5663', 'sha256':doc['sha256'],
        'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
