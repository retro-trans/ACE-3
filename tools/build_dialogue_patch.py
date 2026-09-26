"""Relocate a complete reviewed dialogue table and build an ISO/UDF test disc.

Dry-run by default. This milestone inserts the complete opening tutorial;
the corpus inventory deliberately retains every other row as outstanding.
"""
import argparse
import hashlib
import io
import json
import re
import struct
from pathlib import Path
import pycdlib
from build_ui_patch import ROOT, inner_bnd, iso_files, require, u32
from dialogue_corpus import archive, parse_table, INDEX, read_source
from dialogue_font import complete_font
from ui_font import measure_text
from repair_disc_layout import plan as plan_disc_layout, install_metadata

VERSION = '0.1.7'
BASE = ROOT / 'work/output/ACE3-English-0.1.5.iso'
OUTPUT = ROOT / ('work/output/ACE3-English-' + VERSION + '.iso')
TOKEN = re.compile(r'<[^<>]*>|#c(?:\[[^\]]*\])?')
TUTORIAL_IDS = (6010, 2002010, 3200010, 3201010)

# Exact source table IDs; UI strings are allowed in the repository.
AUXILIARY = {
    1: 'Destroy all enemies', 3: 'Destroy all enemies',
    4: 'Objective: Destroy all enemies', 10: 'Objective: Destroy all enemies',
    11: '△: Lock On', 12: '□: Weapon 1', 13: '○: Blade',
    14: 'Objective: Destroy all enemies', 15: '×: Dash',
    16: '①: Select Weapon', 17: '① + □△○×⑤⑦: Weapons 2-7',
    18: 'Warning: 5 minutes remaining', 19: 'Mission Failed: Time Over',
    20: '① + □: Weapon 2', 21: 'Hold □ for rapid fire',
    22: 'Hold ① + □ to lock onto multiple targets',
    309: "Another Century's Episode 3", 310: 'THE FINAL',
}


def align(value, alignment):
    return (value + alignment - 1) // alignment * alignment


def wrap_text(text, font, width=460):
    """Wrap words without moving commands across words or changing commands."""
    parts = TOKEN.split(text)
    tokens = TOKEN.findall(text)
    result = ''
    line_width = 0
    for i, part in enumerate(parts):
        for word in re.findall(r'\n|[^\s]+', part):
            if word == '\n':
                result += '\n'
                line_width = 0
                continue
            word_width = measure_text(font, word)[0]
            require(word_width <= width, 'One word exceeds subtitle width')
            separator = '' if not line_width else ' '
            if line_width and line_width + measure_text(font, separator)[0] + word_width > width:
                separator = '\n'
                line_width = 0
            result += separator + word
            line_width += (measure_text(font, separator)[0] if separator == ' ' else 0) + word_width
        if i < len(tokens):
            result += tokens[i]
    require(TOKEN.findall(result) == tokens, 'Control sequence changed while wrapping')
    require(len(result.splitlines()) <= 4, 'Subtitle exceeds measured four-line portrait area')
    return result


def rebuild_table(table, translations, font):
    size, pointers, count, rows = parse_table(table)
    result = bytearray(table[:pointers + count * 4])
    reports = []
    pool = {}
    for slot, text_id, pointer, raw in rows:
        digest = hashlib.sha256(raw).hexdigest()
        source = raw.decode('cp932')
        if b'<sp(' in raw:
            require(digest in translations, 'Incomplete dialogue category, missing text ID %s' % text_id)
            draft = translations[digest]
            require(TOKEN.findall(source) == TOKEN.findall(draft['target']), 'Commands changed: ' + draft['id'])
            target = wrap_text(draft['target'], font)
            row_id = draft['id']
        else:
            require(text_id in AUXILIARY, 'Untranslated auxiliary text ID %s' % text_id)
            target, row_id = AUXILIARY[text_id], 'tutorial_ui_%s' % text_id
            require(max(measure_text(font, target)) <= 460, 'Auxiliary line too wide')
        encoded = target.encode('cp932')
        require(b'\0' not in encoded, 'Embedded null')
        if encoded not in pool:
            pool[encoded] = len(result)
            result.extend(encoded + b'\0')
        struct.pack_into('<I', result, pointers + slot * 4, pool[encoded])
        reports.append({'id': row_id, 'slot': slot, 'text_id': text_id,
                        'target': target, 'lines': len(target.splitlines()),
                        'widths': measure_text(font, TOKEN.sub('', target))})
    result.extend(b'\0' * (align(len(result), 32) - len(result)))
    struct.pack_into('<I', result, 4, len(result))
    parsed = parse_table(result)[3]
    require(len(parsed) == len(rows), 'Lost non-null rows')
    require([r[3].decode('cp932') for r in parsed] == [r['target'] for r in reports], 'Table round-trip failed')
    return bytes(result), reports


def rebuild_bundle(data, replacements):
    rows = inner_bnd(data)
    output = bytearray(data[:rows[0][1]])
    for i, (entry, start, end) in enumerate(rows):
        struct.pack_into('<I', output, 20 + i * 8, len(output))
        output.extend(replacements.get(entry, data[start:end]))
        output.extend(b'\0' * (align(len(output), 32) - len(output)))
    struct.pack_into('<I', output, 4, len(output))
    new_rows = inner_bnd(output)
    for (entry, start, end), (_, ns, ne) in zip(rows, new_rows):
        if entry not in replacements:
            require(output[ns:ne] == data[start:end], 'Unrelated bundle resource changed')
    return bytes(output)


def plan():
    index = json.loads(INDEX.read_text(encoding='utf-8'))
    indexed = {r['id']: r for r in index['rows']}
    translations = {}
    for path in sorted((ROOT / 'work/translation/en/dialogue').glob('batch_*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        for row in data.get('rows', []):
            if row['status'] == 'meaning_reviewed':
                require(row['id'] in indexed, 'Unknown translation row')
                translations[indexed[row['id']]['source_sha256']] = row
    replacements, reports, cache = {}, [], {}
    with BASE.open('rb') as stream:
        file, entries = archive(stream)
        def get(resource_id):
            entry = next(e for e in entries if e[3] == resource_id)
            stream.seek(file['offset'] + entry[2])
            return stream.read(entry[1])
        donor_font, donor_texture = get(35), get(36)
        for resource_id in (1200000, 1200001, 1200004, 1200005, 1200006, 1200007):
            data = get(resource_id)
            resources = {entry: data[start:end] for entry, start, end in inner_bnd(data)}
            key = hashlib.sha256(resources[2500] + resources[2000]).hexdigest()
            if key not in cache:
                cache[key] = complete_font(resources[2500], resources[2000], donor_font, donor_texture)
            font, texture, report = cache[key]
            replacements[resource_id] = rebuild_bundle(data, {2500: font, 2000: texture})
            reports.append({'resource_id': resource_id, 'kind': 'complete_latin_font', **report})
            if resource_id == 1200000:
                subtitle_font = font
        for resource_id in TUTORIAL_IDS:
            data = get(resource_id)
            old_offset = u32(data, 20)
            size = parse_table(data, old_offset)[0]
            table, rows = rebuild_table(data[old_offset:old_offset + size], translations, subtitle_font)
            new_offset = align(len(data), 32)
            output = bytearray(data + b'\0' * (new_offset - len(data)) + table)
            struct.pack_into('<I', output, 20, new_offset)
            require(output[24:len(data)] == data[24:] and output[:20] == data[:20], 'Original script modified')
            require(parse_table(output, new_offset)[0] == len(table), 'Relocated table invalid')
            replacements[resource_id] = bytes(output)
            reports.append({'resource_id': resource_id, 'kind': 'relocated_dialogue_table',
                            'original_offset': old_offset, 'relocated_offset': new_offset,
                            'original_size': len(data), 'new_size': len(output), 'rows': rows})
    return replacements, reports


def sha_region(stream, offset, length):
    stream.seek(offset)
    digest = hashlib.sha256()
    while length:
        data = stream.read(min(length, 8 * 1024 * 1024))
        require(data, 'Unexpected EOF')
        digest.update(data)
        length -= len(data)
    return digest.hexdigest()


class FileExtent(io.RawIOBase):
    """Seekable bounded ISO file view, sharing a read-only underlying stream."""
    def __init__(self, stream, offset, length):
        super().__init__()
        self.stream, self.offset, self.length, self.position = stream, offset, length, 0

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        position = offset if whence == 0 else self.position + offset if whence == 1 else self.length + offset
        require(0 <= position <= self.length, 'Extent seek outside file')
        self.position = position
        return position

    def read(self, size=-1):
        size = self.length - self.position if size < 0 else min(size, self.length - self.position)
        self.stream.seek(self.offset + self.position)
        data = self.stream.read(size)
        self.position += len(data)
        return data


def master_disc(archive_path):
    """Create fresh ISO/UDF records; Sony's padded original DRs cannot be reserialized."""
    original = pycdlib.PyCdlib()
    original.open(str(BASE))
    udf_names, udf_dirs = {}, {}
    for parent, directories, files in original.walk(udf_path='/'):
        for name in directories:
            path = parent.rstrip('/') + '/' + name
            udf_dirs[path.upper()] = path
        for name in files:
            path = parent.rstrip('/') + '/' + name
            udf_names[path.upper()] = path
    original.close()
    disc = pycdlib.PyCdlib()
    with BASE.open('rb') as source, archive_path.open('rb') as data:
        files = iso_files(source)
        require(files.keys() == udf_names.keys(), 'ISO and UDF source paths disagree')
        source.seek(16 * 2048)
        pvd = source.read(2048)
        disc.new(interchange_level=1, sys_ident=pvd[8:40].decode('ascii').rstrip(),
                 vol_ident=pvd[40:72].decode('ascii').rstrip(), udf='2.60')
        for path in sorted(udf_dirs, key=lambda p: (p.count('/'), p)):
            disc.add_directory(iso_path=path, udf_path=udf_dirs[path])
        views = []
        for path, record in sorted(files.items(), key=lambda item: item[1]['offset']):
            if path == '/DATA.BIN':
                view, length = data, archive_path.stat().st_size
            else:
                view, length = FileExtent(source, record['offset'], record['size']), record['size']
                views.append(view)
            disc.add_fp(view, length, iso_path=path + ';1', udf_path=udf_names[path])
        disc.write(str(OUTPUT), blocksize=4 * 1024 * 1024)
    disc.close()
    # Keep the Sony boot filesystem conventions. Generic ISO/UDF mastering
    # alone passes payload checks but the PS2 BIOS cannot open the boot ELF.
    prefix, tail_start, tail, _ = plan_disc_layout(OUTPUT)
    install_metadata(OUTPUT, prefix, tail_start, tail)


def build(replacements, reports):
    require(not OUTPUT.exists(), 'Versioned output already exists')
    directory = ROOT / 'work/build' / VERSION
    directory.mkdir(parents=True, exist_ok=True)
    archive_path = directory / 'DATA.BIN'
    with BASE.open('rb') as source, archive_path.open('wb') as target:
        file, entries = archive(source)
        source.seek(file['offset'])
        target.write(source.read(entries[0][2]))
        relocated = []
        for i, (flags, size, offset, resource_id) in enumerate(entries):
            target.write(b'\0' * (align(target.tell(), 2048) - target.tell()))
            new_offset = target.tell()
            source.seek(file['offset'] + offset)
            data = replacements.get(resource_id)
            if data is None:
                data = source.read(size)
            target.write(data)
            relocated.append((flags, len(data), new_offset, resource_id))
        target.write(b'\0' * (align(target.tell(), 2048) - target.tell()))
        target.seek(32)
        for row in relocated:
            target.write(struct.pack('<4I', *row))
    # Verify every archive payload, not just the changed tables.
    with BASE.open('rb') as source, archive_path.open('rb') as target:
        for old, new in zip(entries, relocated):
            resource_id = old[3]
            expected = hashlib.sha256(replacements[resource_id]).hexdigest() if resource_id in replacements else sha_region(source, file['offset'] + old[2], old[1])
            require(sha_region(target, new[2], new[1]) == expected, 'Archive payload mismatch')
    master_disc(archive_path)
    # Preserve the original PS2 system/license area that mastering libraries omit.
    with BASE.open('rb') as source, OUTPUT.open('r+b') as target:
        target.write(source.read(16 * 2048))
    with BASE.open('rb') as source, OUTPUT.open('rb') as target, archive_path.open('rb') as data:
        before, after = iso_files(source), iso_files(target)
        require(before.keys() == after.keys(), 'ISO file list changed')
        for name in before:
            wanted = sha_region(data, 0, archive_path.stat().st_size) if name == '/DATA.BIN' else sha_region(source, before[name]['offset'], before[name]['size'])
            require(sha_region(target, after[name]['offset'], after[name]['size']) == wanted, 'ISO file mismatch: ' + name)
        digest = sha_region(target, 0, OUTPUT.stat().st_size)
    disc = pycdlib.PyCdlib()
    disc.open(str(OUTPUT))
    require(disc.get_record(udf_path='/data.bin').info_len == archive_path.stat().st_size, 'UDF DATA length mismatch')
    disc.close()
    report = {'version': VERSION, 'base': BASE.name, 'output': OUTPUT.name, 'sha256': digest,
              'size': OUTPUT.stat().st_size, 'archive_payloads_verified': len(entries),
              'iso_files_verified': len(before), 'runtime_verified': False,
              'filesystem': 'Original Sony ISO9660/UDF 1.02 metadata with remastered file extents and regenerated UDF checksums.',
              'coverage': 'Opening tutorial: all 120 distinct timed strings and all 18 auxiliary slots in all four table copies. Other dialogue remains outstanding.',
              'changes': reports}
    OUTPUT.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key != 'changes'}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    replacements, reports = plan()
    print('DRY RUN: %s resource replacements' % len(replacements))
    for report in reports:
        if report['kind'] == 'relocated_dialogue_table':
            print(report['resource_id'], 'new table at', hex(report['relocated_offset']), 'rows', len(report['rows']))
            print(json.dumps(report['rows'][16:20], ensure_ascii=True))
    if args.write:
        build(replacements, reports)


if __name__ == '__main__':
    main()
