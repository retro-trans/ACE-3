"""Normalize glossary-backed speaker labels; dry run unless --write is given."""
import argparse
import hashlib
import json
import shutil
import struct
from collections import Counter
from build_ui_patch import ROOT, inner_bnd, require, u32
from dialogue_corpus import archive, parse_table
from ui_font import measure_text
import build_controller_patch as disc_verifier

VERSION = '0.1.11'
BASE = ROOT / 'work/output/ACE3-English-0.1.10.iso'
OUTPUT = ROOT / ('work/output/ACE3-English-' + VERSION + '.iso')
EXPECTED_BASE = '6e8ab72ddae6f061e212fe899a1f87c1d5c12579ae6955ace71ec1d79bfe3ecf'
MANIFEST = ROOT / 'work/translation/en/speaker_names.json'
GLOSSARY = ROOT / 'work/glossary/glossary.json'


def mappings():
    draft = json.loads(MANIFEST.read_text(encoding='utf-8'))
    glossary = {r['id']: r for r in json.loads(GLOSSARY.read_text(encoding='utf-8'))['entries']}
    result = {}
    for row in draft['rows']:
        name = glossary[row['glossary_id']]['name']
        require(row['target'] in name['en'].split(), 'Speaker spelling differs from glossary')
        require(any(row['source'] in s for s in name['ja']), 'Japanese identity differs from glossary')
        for character_id in row['ids']:
            require(character_id not in result, 'Duplicate character ID')
            result[character_id] = row
    return result


def replace_table(table, targets):
    """Rebuild a name pool, retaining all ID ranges, null slots and table extent.

    Names are complete glossary short names, never truncated to fit. These label
    pools have ample existing padding; reject insufficient storage rather than
    shortening a name or changing a parent allocation. Dialogue is not edited.
    """
    size, pointers, count, rows = parse_table(table)
    require(size == len(table), 'Use the logical table extent')
    require(set(targets) <= {r[0] for r in rows}, 'Cannot translate a null/absent slot')
    output = bytearray(table[:pointers + count * 4])
    pool, expected = {}, []
    for slot, text_id, _, raw in rows:
        if slot in targets:
            source, target = targets[slot]
            require(raw.decode('cp932') == source, 'Speaker source preimage mismatch')
            raw = target.encode('cp932')
        if raw not in pool:
            pool[raw] = len(output)
            output.extend(raw + b'\0')
        struct.pack_into('<I', output, pointers + slot * 4, pool[raw])
        expected.append((slot, text_id, raw))
    require(len(output) <= size, 'Name pool needs relocation; never truncate a name')
    output.extend(bytes(size - len(output)))
    require([(s, t, r) for s, t, _, r in parse_table(output)[3]] == expected,
            'Name table round-trip failed')
    return bytes(output)


def actor_tables(data):
    """Version-0x100 scene actors: header +4 start, +31 count, 16-byte records.

    Each record contains character ID, name-table pointer, portrait pointer,
    and a reserved word. Only validated single-label tables are returned.
    """
    if (len(data) < 48 or u32(data, 0) != 0x100 or
            u32(data, 8) not in (0, 48) or data[36:48] != bytes(12)):
        return []
    start, count = u32(data, 4), data[31]
    if count == 0:
        return []
    require(start >= 48 and start % 16 == 0 and start + count * 16 <= len(data),
            'Invalid scene actor directory')
    result = []
    for i in range(count):
        at = start + i * 16
        cid, name, portrait, reserved = struct.unpack_from('<4I', data, at)
        require(reserved == 0 and start + count * 16 <= name < len(data), 'Invalid actor record')
        size, _, slots, rows = parse_table(data, name)
        require(slots == 1 and len(rows) == 1 and rows[0][1] == 1, 'Unexpected actor label schema')
        result.append((cid, name, size, rows[0][3].decode('cp932'), at + 4))
    return result


def plan():
    names, changes, audit = mappings(), [], {'shared_tables': 0, 'scene_resources': 0,
                                            'scanned_archive_resources': 0, 'untranslated_shared': []}
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        for entry_index, (_, length, offset, rid) in enumerate(entries):
            f.seek(fi['offset'] + offset)
            data = f.read(length)
            audit['scanned_archive_resources'] += 1
            origin = fi['offset'] + offset
            if 1200000 <= rid <= 1200007:
                resources = {k: (a, z) for k, a, z in inner_bnd(data)}
                a, z = resources[3021]
                logical = u32(data, a + 4)
                table = data[a:a + logical]
                targets, labels = {}, []
                font = data[slice(*resources[2500])]
                for slot, cid, _, raw in parse_table(table)[3]:
                    if cid not in names:
                        if rid == 1200000:
                            audit['untranslated_shared'].append({'character_id': cid, 'source': raw.decode('cp932')})
                        continue
                    row = names[cid]
                    widths = measure_text(font, row['target'])
                    require(max(widths) <= 300, 'Speaker label too wide')
                    targets[slot] = (row['source'], row['target'])
                    labels.append({'character_id': cid, 'slot': slot, 'target': row['target'], 'widths': widths})
                require(len(targets) == len(names), 'Mapped shared speaker ID missing')
                after = replace_table(table, targets)
                changes.append({'offset': origin + a, 'before': table, 'after': after,
                                'report': {'resource_id': rid, 'table_id': 3021, 'kind': 'shared_speakers', 'labels': labels}})
                audit['shared_tables'] += 1
            actors = actor_tables(data)
            if actors:
                audit['scene_resources'] += 1
            seen = set()
            appended = bytearray()
            for cid, at, size, source, reference in actors:
                if cid not in names:
                    continue
                row = names[cid]
                require(source == row['source'], 'Actor ID/source identity mismatch: %d/%d' % (rid, cid))
                if at in seen:
                    continue
                seen.add(at)
                before = data[at:at + size]
                needed = 44 + len(row['target'].encode('cp932')) + 1
                if needed > size:
                    # Grow only this complete label into unused archive-sector
                    # padding. Update its pointer and archive size, preserving
                    # all existing scene bytes and every disc/file extent.
                    new_size = (needed + 15) // 16 * 16
                    grown = bytearray(before + bytes(new_size - size))
                    struct.pack_into('<I', grown, 4, new_size)
                    after = replace_table(bytes(grown), {0: (source, row['target'])})
                    new_at = length + len(appended)
                    require(new_at % 16 == 0, 'Unaligned scene end')
                    changes.append({'offset': origin + reference, 'before': struct.pack('<I', at),
                                    'after': struct.pack('<I', new_at),
                                    'report': {'resource_id': rid, 'kind': 'speaker_pointer',
                                               'old_offset': at, 'new_offset': new_at}})
                    changes.append({'offset': origin + new_at, 'before': bytes(new_size), 'after': after,
                                    'report': {'resource_id': rid, 'kind': 'scene_speaker', 'relocated': True,
                                               'table_offset': new_at, 'character_id': cid, 'target': row['target']}})
                    appended.extend(after)
                    continue
                after = replace_table(before, {0: (source, row['target'])})
                changes.append({'offset': origin + at, 'before': before, 'after': after,
                                'report': {'resource_id': rid, 'table_offset': at, 'kind': 'scene_speaker',
                                           'character_id': cid, 'target': row['target']}})
            if appended:
                next_offset = entries[entry_index + 1][2] if entry_index + 1 < len(entries) else fi['size']
                require(offset + length + len(appended) <= next_offset, 'Insufficient unused archive padding')
                f.seek(origin + length)
                require(f.read(len(appended)) == bytes(len(appended)), 'Archive padding is not empty')
                changes.append({'offset': fi['offset'] + 32 + entry_index * 16 + 4,
                                'before': struct.pack('<I', length), 'after': struct.pack('<I', length + len(appended)),
                                'report': {'resource_id': rid, 'kind': 'archive_resource_size',
                                           'old_size': length, 'new_size': length + len(appended)}})
    changes.sort(key=lambda c: c['offset'])
    require(all(a['offset'] + len(a['after']) <= b['offset'] for a, b in zip(changes, changes[1:])),
            'Overlapping name tables')
    require(audit['shared_tables'] == 8, 'Missing gameplay bundle')
    for rid, target in [(6010, 'Barrel'), (2002010, 'Barrel'), (2002010, 'Faye')]:
        require(any(c['report'].get('resource_id') == rid and c['report'].get('target') == target for c in changes),
                'Required tutorial speaker missing')
    audit['character_count'] = len(set(r['glossary_id'] for r in names.values()))
    audit['shared_label_ids'] = len(names)
    audit['changed_tables'] = sum(c['report']['kind'] in ('scene_speaker', 'shared_speakers') for c in changes)
    audit['relocated_label_tables'] = sum(c['report'].get('relocated', False) for c in changes)
    audit['scene_label_instances'] = sum(c['report']['kind'] == 'scene_speaker' for c in changes)
    audit['translated_label_instances'] = audit['shared_tables'] * len(names) + audit['scene_label_instances']
    return changes, audit


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    changes, audit = plan()
    print('DRY RUN', json.dumps({k: v for k, v in audit.items() if k != 'untranslated_shared'}))
    for rid in (1200000, 6010, 2002010):
        for c in changes:
            if c['report']['resource_id'] == rid:
                print(json.dumps(c['report']))
    if not args.write:
        return
    require(not OUTPUT.exists(), 'Released output already exists')
    shutil.copyfile(BASE, OUTPUT)
    with OUTPUT.open('r+b') as f:
        for c in changes:
            f.seek(c['offset'])
            require(f.read(len(c['before'])) == c['before'], 'ISO preimage mismatch')
            f.seek(c['offset'])
            f.write(c['after'])
    disc_verifier.BASE, disc_verifier.OUTPUT, disc_verifier.EXPECTED_BASE = BASE, OUTPUT, EXPECTED_BASE
    base_hash, output_hash, size = disc_verifier.verify_disc(changes)
    report = {'version': VERSION, 'base': BASE.name, 'base_sha256': base_hash,
              'output': OUTPUT.name, 'sha256': output_hash, 'size': size,
              'whole_disc_verified': True, 'runtime_verified': False, 'coverage': audit,
              'changes': [{'iso_offset': c['offset'], **c['report']} for c in changes]}
    OUTPUT.with_suffix('.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    manifest = {'version': VERSION, 'base_sha256': base_hash, 'output_sha256': output_hash,
                'inputs': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in (MANIFEST, GLOSSARY, ROOT/'tools/build_speaker_patch.py',
                                     ROOT/'tools/build_controller_patch.py')}}
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print('BUILT', OUTPUT, output_hash)


if __name__ == '__main__':
    main()
