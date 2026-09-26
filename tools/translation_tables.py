"""Standalone, standard-library readers for supported ACE3 text containers.

Only structural BND paths and active mission-table pointers are followed. Models,
packed resources, fixed parameter names, images and movies are outside this reader.
"""
import hashlib
import json
import re
import struct
from pathlib import Path
from build_ui_patch import ROOT, inner_bnd, iso_files, require, u32
from dialogue_corpus import archive

SCHEMA = 'ace3-text-v1'
JP = re.compile(r'[\u3040-\u30ff\u3400-\u9fff\uff66-\uff9f]')
TOKENS = re.compile(r'<[^<>]*>|#[a-z](?:\[[^\]]*\])?|%%|%(?:\d+\$)?[-+0 #]*\d*(?:\.\d+)?[sdiufxX]|[①-⑳○×△□㊤㊦㊧㊨㌀-㏿]')
SAVE_SLOT = re.compile(r'Ｎｏ．[0-9０-９]+')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_table(data):
    require(len(data) >= 40, 'Short text table')
    magic, size, _, ranges, count, pointers, _ = struct.unpack_from('<7I', data)
    require(magic in (0, 65536), 'Unknown text-table format')
    require(0 < ranges <= 4096 and 0 < count <= 65536, 'Invalid index count')
    require(28 + ranges*12 <= size <= len(data), 'Table outside container')
    compact = ranges == count == 1 and pointers == 24
    require(compact or pointers >= 28+ranges*12, 'Overlapping pointer array')
    require(pointers+count*4 <= size, 'Pointer array outside table')
    ids = []
    for n in range(ranges):
        base, first, last = struct.unpack_from('<3I', data, 28+n*12)
        require(base == len(ids) and first <= last and last-first < count, 'Invalid ID range')
        require(not ids or first > ids[-1], 'Unsorted or duplicate IDs')
        ids.extend(range(first, last+1))
    require(len(ids) == count, 'Slot count mismatch')
    start = max(28+ranges*12, pointers+count*4)
    rows = []
    for slot, tid in enumerate(ids):
        pointer = u32(data, pointers+slot*4)
        if not pointer:
            rows.append((slot, tid, 0, None)); continue
        require(start <= pointer < size, 'String pointer outside pool')
        end = data.find(b'\0', pointer, size)
        require(end >= 0, 'Unterminated text')
        raw = bytes(data[pointer:end]); raw.decode('cp932')
        rows.append((slot, tid, pointer, raw))
    return {'size': size, 'pointers': pointers, 'start': start, 'rows': rows}


def walk(data, path=(), offset=0, depth=0):
    require(depth < 12, 'Excessive BND nesting')
    if data[:4] == b'BND\0':
        require(len(data) >= 16 and 16 <= u32(data, 4) <= len(data), 'Invalid BND length')
        for tid, a, z in inner_bnd(data[:u32(data, 4)]):
            yield from walk(data[a:z], path+(str(tid),), offset+a, depth+1)
        return
    try:
        table = read_table(data)
    except (ValueError, UnicodeError, struct.error):
        return
    yield '/'.join(path), offset, table


def scan_iso(path, resources=None):
    """Return rows and table preimages, without retaining whole archive resources."""
    path = Path(path)
    require(path.suffix.lower() == '.iso', 'Use an unpacked .iso; CHD/BIN/CUE are not supported')
    tables = {}; counts = {'resources_examined': 0, 'resources_with_tables': 0, 'unsupported_containers': []}
    with path.open('rb') as f:
        require('/SLPS_257.84' in iso_files(f), 'Expected ACE3 Japanese SLPS-25784 disc')
        fi, entries = archive(f)
        entries = [e for e in entries if e[1] and e[3]]
        for _, size, off, rid in entries:
            if resources is not None and rid not in resources:
                continue
            counts['resources_examined'] += 1
            f.seek(fi['offset']+off); head = f.read(min(size, 24))
            mission = 6000 <= rid < 7000 or 2002000 <= rid < 2003000 or 3200000 <= rid < 3202000
            if head[:4] != b'BND\0' and not mission:
                continue
            require(size <= 32 << 20, 'Resource too large for supported text reader')
            f.seek(fi['offset']+off); data = f.read(size)
            if data[:4] == b'BND\0':
                try: found = list(walk(data))
                except (ValueError, UnicodeError, struct.error) as exc:
                    counts['unsupported_containers'].append({'resource': rid, 'reason': str(exc)}); continue
            elif mission and len(data) >= 24 and data[:4] == b'\0\1\0\0':
                at = u32(data, 20)
                try: table = read_table(data[at:])
                except (ValueError, UnicodeError, struct.error) as exc:
                    counts['unsupported_containers'].append({'resource': rid, 'reason': str(exc)}); continue
                found = [('active', at, table)]
            else:
                continue
            if found: counts['resources_with_tables'] += 1
            for locator, at, table in found:
                key = '%d:%s' % (rid, locator)
                require(key not in tables, 'Duplicate table locator')
                table.update(resource=rid, locator=locator, offset=fi['offset']+off+at,
                             digest=sha(data[at:at+table['size']]))
                tables[key] = table
    counts['tables'] = len(tables)
    counts['rows'] = sum(sum(r[3] is not None for r in t['rows']) for t in tables.values())
    return tables, counts


def row_key(table_key, tid):
    return table_key+':'+str(tid)


def export_document(path, resources=None):
    tables, counts = scan_iso(path, resources)
    rows = []
    for key, table in sorted(tables.items()):
        for _, tid, _, raw in table['rows']:
            if raw is None: continue
            text = raw.decode('cp932')
            rows.append({'id': row_key(key, tid), 'table': key, 'text_id': tid,
                         'before_sha256': sha(raw), 'text': None if JP.search(text) else text})
    return {'schema': SCHEMA, 'source_name': Path(path).name,
            'scope': 'BND text tables and active mission text tables; see docs/TRANSLATING.md for exclusions.',
            'resources': sorted(resources) if resources is not None else None,
            'tables': {key: t['digest'] for key, t in tables.items()}, 'rows': rows}, counts


def save_new(path, text):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f: f.write(text)


def json_text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=2)+'\n'


def rebuild_table(before, targets):
    table = read_table(before)
    out = bytearray(before[:table['start']]); pool = {}
    for slot, tid, _, raw in table['rows']:
        if raw is None: continue
        if tid in targets:
            text = targets[tid]
            require(isinstance(text, str) and '\0' not in text, 'Text must be a string without NUL')
            require(all(ord(c) >= 32 or c in '\n\r\t' for c in text), 'Unexpected control character')
            require(TOKENS.findall(text) == TOKENS.findall(raw.decode('cp932')), 'Control codes, links, placeholders or buttons changed')
            for match in SAVE_SLOT.finditer(raw.decode('cp932')):
                prefix = raw.decode('cp932')[:match.start()].encode('cp932')
                token = match.group().encode('cp932')
                require(text.encode('cp932')[len(prefix):len(prefix)+len(token)] == token, 'Runtime save-slot field moved or changed')
            raw = text.encode('cp932')
        if raw not in pool:
            pool[raw] = len(out); out.extend(raw+b'\0')
        struct.pack_into('<I', out, table['pointers']+slot*4, pool[raw])
    require(len(out) <= table['size'], 'Text pool needs %d bytes; table has %d. Use a format-specific relocation builder.' % (len(out), table['size']))
    out.extend(bytes(table['size']-len(out)))
    actual = read_table(out)['rows']
    expected = [(slot, tid, targets[tid].encode('cp932') if tid in targets else raw) for slot, tid, _, raw in table['rows']]
    require([(s, i, r) for s, i, _, r in actual] == expected, 'Table round-trip failed')
    return bytes(out)


def plan_edits(path, doc):
    require(doc.get('schema') == SCHEMA, 'Unsupported export schema')
    resources = doc.get('resources')
    require(resources is None or (isinstance(resources, list) and all(type(r) is int for r in resources)), 'Invalid resource filter')
    tables, _ = scan_iso(path, set(resources) if resources is not None else None)
    require({k: t['digest'] for k, t in tables.items()} == doc['tables'], 'Table preimages differ: export again from this ISO')
    current = {row_key(k, tid): (k, tid, raw) for k, t in tables.items() for _, tid, _, raw in t['rows'] if raw is not None}
    require(isinstance(doc.get('rows'), list), 'Invalid rows')
    require(len(doc['rows']) == len(current) and {r['id'] for r in doc['rows']} == set(current), 'Rows missing, duplicated or added')
    edits = {}
    for row in doc['rows']:
        key, tid, raw = current[row['id']]
        require(row['table'] == key and row['text_id'] == tid and row['before_sha256'] == sha(raw), 'Row identity/preimage changed')
        text = row['text']
        require(text is None or isinstance(text, str), 'text must be a string or null')
        if text is not None and text.encode('cp932') != raw:
            edits.setdefault(key, {})[tid] = text
    patches = []
    with Path(path).open('rb') as f:
        for key, targets in edits.items():
            table = tables[key]; f.seek(table['offset']); before = f.read(table['size'])
            after = rebuild_table(before, targets)
            patches.append({'table': key, 'offset': table['offset'], 'before': before, 'after': after, 'rows': targets})
    patches.sort(key=lambda p: p['offset'])
    require(all(a['offset']+len(a['before']) <= b['offset'] for a, b in zip(patches, patches[1:])), 'Overlapping edits')
    return patches


def write_copy(source, output, patches):
    """Copy once, substitute validated fixed extents, then verify every byte."""
    source, output = Path(source), Path(output)
    require(source.resolve() != output.resolve(), 'Never overwrite the source ISO')
    require(not output.exists() and not output.with_suffix('.json').exists(), 'Output or report already exists')
    output.parent.mkdir(parents=True, exist_ok=True)
    def copy_until(src, dst, end):
        while src.tell() < end:
            block = src.read(min(8 << 20, end-src.tell())); require(block, 'Short source read'); dst.write(block)
    size = source.stat().st_size
    with source.open('rb') as src, output.open('xb') as dst:
        for p in patches:
            copy_until(src, dst, p['offset'])
            require(src.read(len(p['before'])) == p['before'], 'Source changed during copy')
            dst.write(p['after'])
        copy_until(src, dst, size)
    h = hashlib.sha256(); cursor = 0
    with source.open('rb') as src, output.open('rb') as dst:
        for p in patches + [{'offset': size, 'before': b'', 'after': b''}]:
            while cursor < p['offset']:
                n = min(8 << 20, p['offset']-cursor); a, b = src.read(n), dst.read(n)
                require(len(a) == n and a == b, 'Unplanned output change'); h.update(b); cursor += n
            require(src.read(len(p['before'])) == p['before'], 'Source changed during verification')
            actual = dst.read(len(p['after'])); require(actual == p['after'], 'Output edit differs')
            h.update(actual); cursor += len(actual)
        require(dst.read(1) == b'' and output.stat().st_size == size, 'Output size changed')
    return {'size': size, 'sha256': h.hexdigest(), 'exact_delta_verified': True, 'runtime_verified': False}
