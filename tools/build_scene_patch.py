"""0.1.20: insert the reviewed prologue cutscene (scene 2002410 and its three copies).

Same relocation as the tutorial: a complete new table is appended to each scene
resource and the header pointer redirected; original table and script stay intact.
"""
import argparse
import hashlib
import json
import struct
from build_ui_patch import ROOT, inner_bnd, require, u32
from dialogue_corpus import archive, parse_table, INDEX
from ui_font import measure_text
import build_dialogue_patch as builder
from build_flight_save_patch import controls

KANJI = builder.re.compile('[぀-ヿ一-鿿]')

VERSION = '0.1.20'
BASE = ROOT/'work/output/ACE3-English-0.1.19.iso'
OUTPUT = ROOT/'work/output/ACE3-English-0.1.20.iso'
BATCH = ROOT/'work/translation/en/dialogue/batch_scene_2002410.json'
COPIES = (6410, 2002410, 3200410, 3201410)
# Objective labels stored in the same table; wording follows the released tutorial labels.
AUXILIARY = {1:'Destroy all enemies attacking the city', 3:'Destroy all enemies', 4:'Objective: Destroy all enemies'}
# The stock letterbox subtitle runs to 28 full-width glyphs (about 530 units) on one line and never
# exceeds two lines; English is wrapped a little inside that and held to the same two lines.
WIDTH, LINES = 500, 2


def wrap_words(text, font, width, lines):
    """Wrap on spaces only. Tags are zero-width and stay glued to the word they touch; a
    <book>/<color> span is kept on one line so a link or highlight is never split."""
    out = []
    for paragraph in text.split('\n'):
        words, span = [], None
        for word in paragraph.split(' '):
            if span is not None:
                span += ' '+word
                if '<endbook()>' in word or '<ce()>' in word: words.append(span); span = None
            elif (word.count('<book(') > word.count('<endbook()>')) or (word.count('<color(') > word.count('<ce()>')):
                span = word
            else:
                words.append(word)
        if span is not None: words.append(span)
        line, used = [], 0
        for word in words:
            w = measure_text(font, builder.TOKEN.sub('', word))[0]
            require(w <= width, 'One word or span exceeds subtitle width: %r' % word)
            space = measure_text(font, ' ')[0] if line else 0
            if line and used+space+w > width:
                out.append(' '.join(line)); line, used, space = [], 0, 0
            line.append(word); used += space+w
        out.append(' '.join(line))
    result = '\n'.join(out)
    require(builder.TOKEN.findall(result) == builder.TOKEN.findall(text), 'Control sequence changed while wrapping')
    require(result.split() == text.split(), 'Wrapping changed words')
    require(len(out) <= lines, 'Subtitle exceeds %d lines: %r' % (lines, text))
    return result


def wrap(text, font):
    return wrap_words(text, font, WIDTH, LINES)


def rebuild_table(table, translations, font, auxiliary=None):
    auxiliary = AUXILIARY if auxiliary is None else auxiliary
    size, pointers, count, rows = parse_table(table)
    result, reports, pool = bytearray(table[:pointers+count*4]), [], {}
    for slot, text_id, pointer, raw in rows:
        source = raw.decode('cp932')
        if b'<sp(' in raw:
            digest = hashlib.sha256(raw).hexdigest()
            require(digest in translations, 'Incomplete scene, missing text ID %s' % text_id)
            draft = translations[digest]
            require(builder.TOKEN.findall(source) == builder.TOKEN.findall(draft['target']), 'Commands changed: '+draft['id'])
            target, row_id = wrap(draft['target'], font), draft['id']
        else:
            # Bare commands, dashes and labels already in English pass through unchanged.
            require(text_id in auxiliary or not KANJI.search(source), 'Untranslated auxiliary text ID %s' % text_id)
            target, row_id = auxiliary.get(text_id, source), 'scene_ui_%s' % text_id
            require(controls(source) == controls(target), 'Auxiliary icons or commands changed: %s' % text_id)
            require(max(measure_text(font, target)) <= WIDTH, 'Auxiliary line too wide')
        encoded = target.encode('cp932'); require(b'\0' not in encoded, 'Embedded null')
        if encoded not in pool:
            pool[encoded] = len(result); result.extend(encoded+b'\0')
        struct.pack_into('<I', result, pointers+slot*4, pool[encoded])
        reports.append({'id':row_id, 'slot':slot, 'text_id':text_id, 'target':target, 'lines':len(target.split('\n')),
                        'widths':measure_text(font, builder.TOKEN.sub('', target))})
    result.extend(b'\0'*(builder.align(len(result), 32)-len(result)))
    struct.pack_into('<I', result, 4, len(result))
    parsed = parse_table(result)[3]
    require([(s, i) for s, i, _, _ in parsed] == [(s, i) for s, i, _, _ in rows], 'Slots or IDs changed')
    require([r[3].decode('cp932') for r in parsed] == [r['target'] for r in reports], 'Table round-trip failed')
    return bytes(result), reports


def plan():
    indexed = {r['id']:r for r in json.loads(INDEX.read_text(encoding='utf-8'))['rows']}
    batch = json.loads(BATCH.read_text(encoding='utf-8'))
    require(all(r['status'] == 'meaning_reviewed' for r in batch['rows']), 'Unreviewed scene rows')
    translations = {indexed[r['id']]['source_sha256']:r for r in batch['rows']}
    replacements, reports = {}, []
    with BASE.open('rb') as stream:
        file, entries = archive(stream)
        def get(rid):
            entry = next(e for e in entries if e[3] == rid); stream.seek(file['offset']+entry[2]); return stream.read(entry[1])
        bundle = get(1200000)
        font = {k:bundle[a:z] for k, a, z in inner_bnd(bundle)}[2500]
        for rid in COPIES:
            data = get(rid); old = u32(data, 20); size = parse_table(data, old)[0]
            table, rows = rebuild_table(data[old:old+size], translations, font)
            new = builder.align(len(data), 32)
            output = bytearray(data+b'\0'*(new-len(data))+table)
            struct.pack_into('<I', output, 20, new)
            require(output[24:len(data)] == data[24:] and output[:20] == data[:20], 'Original script modified')
            require(parse_table(output, new)[0] == len(table), 'Relocated table invalid')
            replacements[rid] = bytes(output)
            reports.append({'resource_id':rid, 'kind':'relocated_dialogue_table', 'original_offset':old, 'relocated_offset':new,
                            'original_size':len(data), 'new_size':len(output), 'rows':rows})
    return replacements, reports


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    replacements, reports = plan()
    rows = reports[1]['rows']
    summary = {'resources':len(replacements), 'rows_per_copy':len(rows), 'dialogue_rows':sum(r['id'].startswith('dialogue_') for r in rows),
               'max_width':max(max(r['widths']) for r in rows), 'max_lines':max(r['lines'] for r in rows)}
    print('DRY RUN', json.dumps(summary))
    for r in rows:
        if r['text_id'] in (303, 305, 309, 327, 343): print(json.dumps({k:r[k] for k in ('text_id', 'target', 'widths')}))
    if not a.write: return
    builder.VERSION, builder.BASE, builder.OUTPUT = VERSION, BASE, OUTPUT
    builder.build(replacements, reports)
    path = OUTPUT.with_suffix('.json'); doc = json.loads(path.read_text(encoding='utf-8'))
    doc['coverage'] = 'Prologue cutscene 2002410: all 62 timed strings and 3 objective labels in all four copies. Tutorial inherited. Other dialogue remains outstanding.'
    doc['scene'] = summary; doc['runtime_verified'] = False
    path.write_text(json.dumps(doc, indent=2)+'\n', encoding='utf-8')
    inputs = [BATCH, ROOT/'work/translation/en/dialogue/review_scene_2002410.json', ROOT/'tools/build_scene_patch.py',
              ROOT/'tools/build_dialogue_patch.py', ROOT/'tools/repair_disc_layout.py']
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps({'version':VERSION, 'base':BASE.name,
        'base_sha256':'93d980a938ecd71af03d95d9e1a752dfddf5fe703d6e8863ad01326d2aeb2d36', 'sha256':doc['sha256'],
        'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__': main()
