"""Account for dialogue commands outside indexed tables, without storing scripts."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from build_ui_patch import ROOT, iso_files
from dialogue_corpus import INDEX, archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    index = json.loads(INDEX.read_text(encoding='utf-8'))
    hashes = {r['source_sha256'] for r in index['rows']}
    missed = {r['resource_id']: r['offsets'] for r in index['unmapped_speed_commands']}
    orphan_known, candidates, other_resources, outside = 0, {}, [], []
    with next(ROOT.glob('*.iso')).open('rb') as stream:
        file, entries = archive(stream)
        for flags, size, offset, resource_id in entries:
            stream.seek(file['offset'] + offset)
            data = stream.read(size)
            if b'<sp(' not in data and any(tag in data for tag in (b'<op()>', b'<on()>', b'<book(')):
                other_resources.append(resource_id)
            for position in missed.get(resource_id, []):
                start, end = data.rfind(b'\0', 0, position) + 1, data.find(b'\0', position)
                raw = data[start:end]
                digest = hashlib.sha256(raw).hexdigest()
                if digest in hashes:
                    orphan_known += 1
                    continue
                record = candidates.setdefault(digest, {'source_sha256': digest, 'source_bytes': len(raw),
                                                        'starts_with_command': raw.startswith(b'<'), 'occurrences': []})
                record['occurrences'].append({'resource_id': resource_id, 'resource_offset': start,
                                              'iso_offset': file['offset'] + offset + start})
        for name, record in iso_files(stream).items():
            if name == '/DATA.BIN':
                continue
            stream.seek(record['offset'])
            remaining, hits, tail = record['size'], 0, b''
            while remaining:
                data = stream.read(min(8 * 1024 * 1024, remaining))
                hits += (tail + data).count(b'<sp(')
                tail = data[-3:]
                remaining -= len(data)
            if hits:
                outside.append({'file': name, 'speed_commands': hits})
    result = {'version': '0.1.6', 'mapped_distinct_strings': len(index['rows']),
              'unreferenced_known_string_occurrences': orphan_known,
              'unreferenced_distinct_candidates': len(candidates),
              'unreferenced_candidates': list(candidates.values()),
              'other_dialogue_tag_resources_without_speed': other_resources,
              'speed_commands_outside_data_bin': outside,
              'complete_dialogue_discovery_certified': False,
              'notes': ['Unreferenced pools include old string tails and fragments; do not patch by blind search/replace.',
                        'A speed-command search cannot rule out untagged dialogue or image-based captions.',
                        'All candidates are tracked by offset/hash; original Japanese remains only on the source disc.']}
    print(json.dumps({k: v for k, v in result.items() if k != 'unreferenced_candidates'}, indent=2))
    print('Sample candidate:', json.dumps(result['unreferenced_candidates'][:1], indent=2))
    if args.write:
        (ROOT / 'work/translation/en/dialogue_audit.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
