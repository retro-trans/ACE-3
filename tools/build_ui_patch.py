"""Build a versioned UI test ISO from verified BND text tables. Dry-run by default."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
from collections import Counter
from ui_font import patch_font, measure_text
from ui_capacity import plan_capacity, CAPACITY

ROOT = Path(__file__).resolve().parents[1]
SECTOR = 2048


def u32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def require(value, message):
    if not value:
        raise ValueError(message)


def iso_files(stream):
    stream.seek(16 * SECTOR)
    pvd = stream.read(SECTOR)
    require(pvd[:7] == b'\x01CD001\x01', 'Expected ISO9660 primary volume')
    found = {}

    def walk(lba, size, parent):
        stream.seek(lba * SECTOR)
        data = stream.read(size)
        at = 0
        while at < len(data):
            length = data[at]
            if not length:
                at = (at // SECTOR + 1) * SECTOR
                continue
            record = data[at:at + length]
            require(len(record) == length and length >= 34, 'Invalid directory record')
            at += length
            name = record[33:33 + record[32]]
            if name in (b'\0', b'\1'):
                continue
            name = parent + '/' + name.decode('ascii').split(';')[0]
            extent, size = u32(record, 2), u32(record, 10)
            if record[25] & 2:
                walk(extent, size, name)
            else:
                found[name] = {'offset': extent * SECTOR, 'size': size}

    walk(u32(pvd, 158), u32(pvd, 166), '')
    return found


def inner_bnd(data):
    require(data[:4] == b'BND\0' and u32(data, 4) == len(data), 'Unexpected inner BND header')
    count = u32(data, 8)
    require(16 + count * 8 <= len(data), 'BND index outside archive')
    rows = [struct.unpack_from('<II', data, 16 + i * 8) for i in range(count)]
    require(len({i for i, _ in rows}) == count, 'Duplicate inner BND ID')
    result = []
    for n, (entry_id, offset) in enumerate(rows):
        end = rows[n + 1][1] if n + 1 < count else len(data)
        require(16 + count * 8 <= offset < end <= len(data), 'Unordered BND offsets')
        result.append((entry_id, offset, end))
    return result


def text_table(data):
    require(data[:4] == b'\0\0\1\0', 'Unexpected text table magic')
    size, count, table = u32(data, 4), u32(data, 16), u32(data, 20)
    require(table == 40 and u32(data, 12) == 1 and u32(data, 32) == 1, 'Unsupported text table layout')
    require(u32(data, 36) == count, 'Text table count mismatch')
    start = table + count * 4
    require(start <= size <= len(data), 'Invalid logical text table extent')
    rows = []
    for i in range(count):
        pointer = u32(data, table + i * 4)
        if pointer == 0:
            rows.append(None)
            continue
        require(start <= pointer < size, 'Text pointer outside logical table')
        end = data.find(b'\0', pointer, size)
        require(end >= 0, 'Unterminated text')
        rows.append(data[pointer:end])
    return size, start, rows


def patch_table(data, mappings, table_id, allow_growth=False):
    size, start, rows = text_table(data)
    next_rows = list(rows)
    changes = []
    for index, source in enumerate(rows):
        if source is None:
            continue
        for mapping in mappings:
            if table_id not in mapping['table_ids']:
                continue
            if source != mapping['source'].encode('cp932'):
                continue
            target = mapping['target'].encode('cp932')
            require(b'\0' not in target, 'Embedded null in target')
            icons = '㍉㌢㌔㍍㌘㊤㊦㊧㊨○×△□'
            require(Counter(c for c in mapping['source'] if c in icons) ==
                    Counter(c for c in mapping['target'] if c in icons),
                    'Game icon changed: ' + mapping['id'])
            next_rows[index] = target
            changes.append({'mapping_id': mapping['id'], 'slot': index, 'old_pointer': u32(data, 40 + index * 4), 'target': mapping['target']})
            break
    if not changes:
        return data, []
    needed = start + sum(len(text) + 1 for text in set(next_rows) if text is not None)
    if needed > size:
        require(allow_growth, 'Repacked table needs archive relocation; refusing to truncate')
        size = (needed + 31) & ~31
    output = bytearray(data)
    if len(output) < size:
        output.extend(b'\0' * (size - len(output)))
    struct.pack_into('<I', output, 4, size)
    output[start:size] = b'\0' * (size - start)
    cursor = start
    pointer_cache = {}
    for i, text in enumerate(next_rows):
        if text is None:
            continue
        if text not in pointer_cache:
            pointer_cache[text] = cursor
            require(cursor + len(text) + 1 <= size, 'Repacked table needs archive relocation; refusing to truncate')
            output[cursor:cursor + len(text) + 1] = text + b'\0'
            cursor += len(text) + 1
        struct.pack_into('<I', output, 40 + i * 4, pointer_cache[text])
    require(allow_growth or len(output) == len(data), 'Table allocation changed')
    require(text_table(output)[2] == next_rows, 'Repacked strings do not round-trip')
    require(output[size:] == data[size:], 'Unrelated table padding changed')
    for change in changes:
        change['new_pointer'] = u32(output, 40 + change['slot'] * 4)
    return bytes(output), changes


def patch_bundle(bundle, manifest):
    resources = inner_bnd(bundle)
    font_row = next(row for row in resources if row[0] == 2500)
    font, aliases = patch_font(bundle[font_row[1]:font_row[2]])
    for mapping in manifest['mappings']:
        if manifest.get('menu_capacity_fix') and set(mapping['table_ids']) & {3036, 3065}:
            require(len(mapping['target']) <= CAPACITY, 'Translation exceeds menu drawing capacity: ' + mapping['id'])
        mapping_widths = measure_text(font, mapping['target'])
        require(max(mapping_widths) <= mapping.get('max_width', 620),
                'Text exceeds measured layout budget: ' + mapping['id'] + ' ' + str(mapping_widths))
        if mapping.get('max_width') == 410:
            require(len(mapping_widths) <= 6, 'Modal exceeds six-line budget: ' + mapping['id'])
    output = bytearray(bundle[:resources[0][1]])
    reports = []
    for index, (entry_id, start, end) in enumerate(resources):
        before = bundle[start:end]
        after = before
        changes = []
        if entry_id in manifest['complete_table_ids']:
            _, _, rows = text_table(before)
            keep = manifest['preserved_slots'].get(str(entry_id), {})
            for slot, source in enumerate(rows):
                if not source:
                    continue
                matches = [m for m in manifest['mappings'] if entry_id in m['table_ids'] and m['source'].encode('cp932') == source]
                require(len(matches) <= 1, 'Ambiguous translation')
                if not matches:
                    require(str(slot) in keep and keep[str(slot)]['source'].encode('cp932') == source,
                            'Untranslated category member: ' + str((entry_id, slot, source)))
                elif source.startswith('Ｎｏ．00'.encode('cp932')):
                    require(matches[0]['target'].startswith('Ｎｏ．00'), 'Runtime save slot prefix moved')
            after, changes = patch_table(before, manifest['mappings'], entry_id, allow_growth=True)
        elif entry_id == 2500:
            after = font
        allocation = len(before) if after == before else max(len(before), (len(after) + 31) & ~31)
        after = after + before[len(after):allocation] + b'\0' * max(0, allocation - max(len(after), len(before)))
        require(len(after) == allocation, 'Resource allocation mismatch')
        new_start = len(output)
        struct.pack_into('<I', output, 20 + index * 8, new_start)
        output.extend(after)
        if changes:
            reports.append({'table_id': entry_id, 'relative_offset': new_start, 'changes': changes})
        if entry_id not in manifest['complete_table_ids'] and entry_id != 2500:
            require(output[new_start:] == before, 'Unselected resource changed')
    struct.pack_into('<I', output, 4, len(output))
    rebuilt = inner_bnd(output)
    for entry_id, start, end in rebuilt:
        if entry_id in manifest['complete_table_ids']:
            text_table(output[start:end])
    return bytes(output), reports, aliases


def make_plan(iso, manifest):
    patches = []
    counts = {m['id']: 0 for m in manifest['mappings']}
    with iso.open('rb') as stream:
        files = iso_files(stream)
        require('/SLPS_257.84' in files, 'Wrong game executable')
        if manifest.get('menu_capacity_fix'):
            executable = files['/SLPS_257.84']
            stream.seek(executable['offset'])
            patches.extend(plan_capacity(stream.read(executable['size']), executable['offset']))
        data_file = files['/DATA.BIN']
        stream.seek(data_file['offset'])
        head = stream.read(32)
        require(head[:4] == b'BND3' and head[12:16] == b'@\0\0\0', 'Unsupported DATA.BIN binder')
        count = u32(head, 16)
        require(count == manifest['expected_bnd_entries'], 'Unexpected DATA.BIN version')
        entries = stream.read(count * 16)
        found = set()
        for i in range(count):
            flags, size, offset, entry_id = struct.unpack_from('<IIII', entries, i * 16)
            if entry_id not in manifest['bundle_ids']:
                continue
            found.add(entry_id)
            require(flags == 64 and offset + size <= data_file['size'], 'Invalid target binder entry')
            base = data_file['offset'] + offset
            stream.seek(base)
            next_offset = struct.unpack_from('<I', entries, (i + 1) * 16 + 8)[0] if i + 1 < count else data_file['size']
            require(next_offset >= offset + size, 'Bundle allocation overlaps next entry')
            before = stream.read(next_offset - offset)
            after, tables, aliases = patch_bundle(before[:size], manifest)
            require(len(after) <= len(before), 'Expanded bundle exceeds available archive space: ' + str((entry_id, len(after), len(before))))
            new_size = len(after)
            after += before[new_size:]
            for table in tables:
                table['iso_table_offset'] = base + table['relative_offset']
                for change in table['changes']:
                    counts[change['mapping_id']] += 1
            patches.append({'offset': base, 'before': before, 'after': after, 'bundle_id': entry_id, 'kind': 'bundle', 'tables': tables, 'font_aliases': aliases, 'old_size': size, 'new_size': new_size})
            if new_size != size:
                patches.append({'offset': data_file['offset'] + 32 + i * 16 + 4, 'before': struct.pack('<I', size), 'after': struct.pack('<I', new_size), 'kind': 'bundle_size', 'bundle_id': entry_id})
    require(found == set(manifest['bundle_ids']), 'Missing target UI bundles')
    for mapping in manifest['mappings']:
        require(counts[mapping['id']] >= mapping.get('minimum_matches', 1), 'Unmatched translation: ' + mapping['id'])
    patches.sort(key=lambda p: p['offset'])
    require(all(a['offset'] + len(a['after']) <= b['offset'] for a, b in zip(patches, patches[1:])), 'Overlapping patch regions')
    return patches, counts


def verify_iso(source, output, patches):
    require(source.stat().st_size == output.stat().st_size, 'ISO size changed')
    before_hash, after_hash = hashlib.sha256(), hashlib.sha256()
    with source.open('rb') as original, output.open('rb') as patched:
        position = 0
        while True:
            before = original.read(8 * 1024 * 1024)
            if not before:
                break
            actual = patched.read(len(before))
            expected = bytearray(before)
            for patch in patches:
                low, high = max(position, patch['offset']), min(position + len(before), patch['offset'] + len(patch['after']))
                if low < high:
                    rel = low - patch['offset']
                    require(before[low - position:high - position] == patch['before'][rel:rel + high - low], 'Original data changed')
                    expected[low - position:high - position] = patch['after'][rel:rel + high - low]
            require(actual == expected, 'Unexpected ISO difference at chunk ' + hex(position))
            before_hash.update(before)
            after_hash.update(actual)
            position += len(before)
    return before_hash.hexdigest(), after_hash.hexdigest()


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iso', type=Path)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'work/translation/en/patch_manifest.json')
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8-sig'))
    iso = args.iso or next(ROOT.glob('*.iso'))
    output = ROOT / 'work/output' / ('ACE3-English-' + manifest['version'] + '.iso')
    require(iso.resolve() != output.resolve(), 'Original ISO cannot be the destination')
    patches, counts = make_plan(iso, manifest)
    print('Source:', iso)
    print('Output:', output)
    print('PLAN:', len(patches), 'archive patches;', sum(counts.values()), 'translated string instances;', len(counts), 'mappings')
    for patch in patches:
        print('  Target', patch.get('bundle_id', patch.get('menu')), patch['kind'], 'ISO offset', hex(patch['offset']))
        if patch['kind'] == 'bundle':
            print('  Size:', patch['old_size'], '->', patch['new_size'], 'font aliases:', ''.join(a['character'] for a in patch['font_aliases']))
    for patch in patches:
        for table in patch.get('tables', []):
            for change in table['changes']:
                if change['mapping_id'] in ('load.question', 'settings.title', 'settings.shift_description', 'no_save_data', 'category.3065.10', 'category.3065.11'):
                    print('SAMPLE:', change['mapping_id'], repr(change['target']), hex(change['old_pointer']), '->', hex(change['new_pointer']))
    if not args.write and not args.verify:
        print('DRY RUN: no files written. Read the samples, then repeat with --write.')
        return
    if args.write:
        require(not output.exists(), 'Output already exists; choose a new version or explicitly remove the old test artifact')
        output.parent.mkdir(parents=True, exist_ok=True)
        with iso.open('rb') as source, output.open('xb') as target:
            while True:
                chunk = source.read(8 * 1024 * 1024)
                if not chunk:
                    break
                target.write(chunk)
        with output.open('r+b') as target:
            for patch in patches:
                target.seek(patch['offset'])
                require(target.read(len(patch['before'])) == patch['before'], 'Patch preimage mismatch')
                target.seek(patch['offset'])
                target.write(patch['after'])
        print('Wrote test ISO; verifying every byte against the plan...', flush=True)
    source_hash, output_hash = verify_iso(iso, output, patches)
    report = {'version': manifest['version'], 'source_iso': iso.name, 'source_sha256': source_hash, 'output_iso': output.name, 'output_sha256': output_hash, 'size': output.stat().st_size, 'validation': 'All bytes match the source plus planned bundle/index replacements. All text tables round-trip; complete categories and target glyph coverage checked; non-target resources and original font glyphs preserved.', 'in_game_validation': 'pending', 'mapping_counts': counts, 'patches': [{k: v for k, v in patch.items() if k not in ('before', 'after')} for patch in patches]}
    if args.write:
        output.with_suffix('.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        output.with_suffix('.manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('PASS: full ISO comparison, table pointers, untouched resources, size, and SHA-256 hashes.')
    print('Output SHA-256:', output_hash)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, StopIteration, struct.error) as error:
        print('ERROR:', error, file=sys.stderr)
        raise SystemExit(1)
