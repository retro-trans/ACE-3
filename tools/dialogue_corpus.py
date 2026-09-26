"""Index dialogue by source offsets; never export a Japanese script to disk."""
import argparse
import hashlib
import json
import re
import struct
import sys
from pathlib import Path
from build_ui_patch import iso_files, u32, require

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'work/translation/en/dialogue_index.json'
COMMAND = re.compile(rb'<[A-Za-z]+\([^<>\x00]*?\)>')


def archive(stream):
    file = iso_files(stream)['/DATA.BIN']
    stream.seek(file['offset'])
    header = stream.read(32)
    require(header[:4] == b'BND3', 'Unexpected archive')
    rows = [struct.unpack('<4I', stream.read(16)) for _ in range(u32(header, 16))]
    return file, rows


def parse_table(data, at=0):
    require(at + 40 <= len(data), 'Short table')
    magic, size, zero, ranges, count, pointers, reserved = struct.unpack_from('<7I', data, at)
    require(magic == 65536 and zero == reserved == 0, 'Not a text table')
    require(0 < ranges < 4096 and pointers == 28 + ranges * 12, 'Invalid range index')
    require(pointers + count * 4 <= size <= len(data) - at, 'Invalid table extent')
    ids = []
    for i in range(ranges):
        base, first, last = struct.unpack_from('<3I', data, at + 28 + i * 12)
        require(base == len(ids) and first <= last and last - first < count, 'Invalid ID range')
        ids.extend(range(first, last + 1))
    require(len(ids) == count and len(set(ids)) == count, 'Invalid slot count')
    rows = []
    for slot, text_id in enumerate(ids):
        pointer = u32(data, at + pointers + slot * 4)
        if not pointer:
            continue
        require(pointers + count * 4 <= pointer < size, 'Invalid string pointer')
        end = data.find(b'\0', at + pointer, at + size)
        require(end >= 0, 'Missing string terminator')
        raw = data[at + pointer:end]
        raw.decode('cp932')
        rows.append((slot, text_id, pointer, raw))
    return size, pointers, count, rows


def scan(path):
    unique, tables, uncovered = {}, [], []
    with path.open('rb') as stream:
        file, entries = archive(stream)
        for flags, length, offset, resource_id in entries:
            stream.seek(file['offset'] + offset)
            data = stream.read(length)
            if b'<sp(' not in data:
                continue
            covered = set()
            at = 0
            while True:
                at = data.find(b'\0\0\1\0', at)
                if at < 0:
                    break
                try:
                    size, pointers, count, rows = parse_table(data, at)
                except (ValueError, UnicodeError, struct.error):
                    at += 4
                    continue
                if any(b'<sp(' in row[3] for row in rows):
                    table = {'resource_id': resource_id, 'resource_offset': offset,
                             'resource_size': length, 'table_offset': at,
                             'table_size': size, 'pointer_array': pointers,
                             'slot_count': count, 'rows': []}
                    for slot, text_id, pointer, raw in rows:
                        for match in re.finditer(rb'<sp\(', raw):
                            covered.add(at + pointer + match.start())
                        if not b'<sp(' in raw:
                            continue
                        digest = hashlib.sha256(raw).hexdigest()
                        if digest not in unique:
                            unique[digest] = {'id': 'dialogue_%05d' % (len(unique) + 1),
                                             'source_sha256': digest, 'source_bytes': len(raw),
                                             'commands': [m.decode('ascii') for m in COMMAND.findall(raw)],
                                             'occurrences': []}
                        record = unique[digest]
                        occurrence = {'resource_id': resource_id, 'table_offset': at,
                                      'slot': slot, 'text_id': text_id,
                                      'iso_offset': file['offset'] + offset + at + pointer}
                        record['occurrences'].append(occurrence)
                        table['rows'].append({'id': record['id'], 'slot': slot, 'text_id': text_id})
                    tables.append(table)
                at += size
            missed = sorted(set(m.start() for m in re.finditer(rb'<sp\(', data)) - covered)
            if missed:
                uncovered.append({'resource_id': resource_id, 'offsets': missed})
    return {'schema_version': 1, 'version': '0.1.6', 'source_iso': path.name,
            'scope': 'All DATA.BIN text tables containing the dialogue speed command; other formats are not certified absent.',
            'rows': list(unique.values()), 'tables': tables, 'unmapped_speed_commands': uncovered}


def read_source(stream, row):
    stream.seek(row['occurrences'][0]['iso_offset'])
    raw = stream.read(row['source_bytes'])
    require(hashlib.sha256(raw).hexdigest() == row['source_sha256'], 'Source hash mismatch')
    return raw.decode('cp932')


def add_other_tagged_text(result, path):
    """Append window/book text without changing any existing speed-dialogue IDs."""
    unique = {r['source_sha256']: r for r in result['rows']}
    tables = {(t['resource_id'], t['table_offset']): t for t in result['tables']}
    markers = (b'<op()>', b'<on()>', b'<book(', b'<selectwindow(')
    with path.open('rb') as stream:
        file, entries = archive(stream)
        for flags, length, offset, resource_id in entries:
            stream.seek(file['offset'] + offset)
            data = stream.read(length)
            if not any(marker in data for marker in markers):
                continue
            at = 0
            while True:
                at = data.find(b'\0\0\1\0', at)
                if at < 0:
                    break
                try:
                    size, pointers, count, rows = parse_table(data, at)
                except (ValueError, UnicodeError, struct.error):
                    at += 4
                    continue
                for slot, text_id, pointer, raw in rows:
                    if b'<sp(' in raw or not any(marker in raw for marker in markers):
                        continue
                    if not COMMAND.sub(b'', raw).strip():
                        continue
                    digest = hashlib.sha256(raw).hexdigest()
                    if digest not in unique:
                        record = {'id': 'dialogue_%05d' % (len(result['rows']) + 1),
                                  'kind': 'window_or_book_text', 'source_sha256': digest,
                                  'source_bytes': len(raw), 'commands': [m.decode('ascii') for m in COMMAND.findall(raw)],
                                  'occurrences': []}
                        result['rows'].append(record)
                        unique[digest] = record
                    record = unique[digest]
                    record['occurrences'].append({'resource_id': resource_id, 'table_offset': at,
                                                  'slot': slot, 'text_id': text_id,
                                                  'iso_offset': file['offset'] + offset + at + pointer})
                    key = resource_id, at
                    if key not in tables:
                        tables[key] = {'resource_id': resource_id, 'resource_offset': offset, 'resource_size': length,
                                       'table_offset': at, 'table_size': size, 'pointer_array': pointers,
                                       'slot_count': count, 'rows': []}
                        result['tables'].append(tables[key])
                    tables[key]['rows'].append({'id': record['id'], 'slot': slot, 'text_id': text_id})
                at += size
    for table in result['tables']:
        table['rows'].sort(key=lambda row: row['slot'])
    result['scope'] = 'Referenced DATA.BIN text with dialogue speed, window-open, or book commands. Includes legacy content and help/book text; untagged and image-based dialogue is not certified absent.'
    return result


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['scan', 'slice'])
    parser.add_argument('start', type=int, nargs='?', default=1)
    parser.add_argument('count', type=int, nargs='?', default=80)
    parser.add_argument('--context', type=int, default=8)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    path = next(ROOT.glob('*.iso'))
    if args.action == 'scan':
        result = add_other_tagged_text(scan(path), path)
        print(json.dumps({'rows': len(result['rows']), 'tables': len(result['tables']),
                          'instances': sum(len(r['occurrences']) for r in result['rows']),
                          'unmapped_resources': len(result['unmapped_speed_commands']),
                          'samples': result['rows'][:2]}, indent=2))
        if args.write:
            INDEX.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    else:
        result = json.loads(INDEX.read_text(encoding='utf-8'))
        rows = result['rows']
        start, end = max(0, args.start - 1 - args.context), min(len(rows), args.start - 1 + args.count + args.context)
        with path.open('rb') as stream:
            for i in range(start, end):
                row = rows[i]
                print(json.dumps({'row': i + 1, 'id': row['id'], 'in_slice': args.start <= i + 1 < args.start + args.count,
                                  'source': read_source(stream, row), 'location': row['occurrences'][0]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
