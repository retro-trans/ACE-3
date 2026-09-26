"""Directory helpers and the rejected DVD-detection-only boot experiment.

Root length correction alone DOES NOT fix the BIOS file-open failure.
Use repair_disc_layout.py for the release repair.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from build_ui_patch import ROOT, iso_files, require, u32

SECTOR = 2048
VERSION = '0.1.7'
BASE = ROOT / 'work/output/ACE3-English-0.1.6.iso'
OUTPUT = ROOT / ('work/output/ACE3-English-' + VERSION + '.iso')
SOURCE_SHA256 = '8e072d12351c2ef337d1d3e36e6820068d29ee3f8c2fad3d7b40614f67bac8cc'


def records(data):
    """Yield validated directory records, including dot and dot-dot."""
    at = 0
    while at < len(data):
        length = data[at]
        if not length:
            end = min((at // SECTOR + 1) * SECTOR, len(data))
            require(not any(data[at:end]), 'Nonzero directory sector padding')
            at = end
            continue
        require(length >= 34 and at + length <= len(data), 'Invalid directory record')
        require(at // SECTOR == (at + length - 1) // SECTOR, 'Record crosses sector')
        row = data[at:at + length]
        require(33 + row[32] <= length, 'Invalid directory identifier')
        require(u32(row, 2) == struct.unpack_from('>I', row, 6)[0], 'Extent endian mismatch')
        require(u32(row, 10) == struct.unpack_from('>I', row, 14)[0], 'Size endian mismatch')
        yield at, row
        at += length


def dvd_root_plan(stream):
    """Use Sony-style logical root length, preserving all sectors and payloads.

    PCSX2 2.8.2 classifies a 2048-byte-sector ISO as CD when the low
    16 bits of the PVD root directory size equal 2048. Its detection
    buffer includes a 24-byte prefix: buffer+190 is PVD+166.
    Every ISO reference to the root gets the same exact logical size.
    UDF describes separate directory streams and must remain untouched.
    """
    stream.seek(16 * SECTOR)
    pvd = stream.read(SECTOR)
    require(pvd[:7] == b'\x01CD001\x01', 'Missing ISO9660 PVD')
    root_lba, old_size = u32(pvd, 158), u32(pvd, 166)
    stream.seek(root_lba * SECTOR)
    root_data = stream.read(old_size)
    root_rows = list(records(root_data))
    require(root_rows, 'Empty root directory')
    logical_size = root_rows[-1][0] + len(root_rows[-1][1])
    require(logical_size <= old_size and logical_size & 0xffff != 2048,
            'Root cannot safely use the DVD detection convention')
    require(not any(root_data[logical_size:]), 'Root truncation would discard data')
    changes = []

    def add(at, previous, description):
        require(previous == old_size, 'Inconsistent root directory size')
        before = struct.pack('<I', previous) + struct.pack('>I', previous)
        after = struct.pack('<I', logical_size) + struct.pack('>I', logical_size)
        if before != after:
            changes.append({'offset': at, 'before': before.hex(), 'after': after.hex(),
                            'description': description})

    add(16 * SECTOR + 166, old_size, 'Primary volume root directory length')
    seen = set()

    def walk(lba, size, path):
        if lba in seen:
            return
        seen.add(lba)
        stream.seek(lba * SECTOR)
        rows = list(records(stream.read(size)))
        for at, row in rows:
            if not row[25] & 2:
                continue
            child_lba, child_size = u32(row, 2), u32(row, 10)
            name = row[33:33 + row[32]]
            if child_lba == root_lba:
                add(lba * SECTOR + at + 10, child_size, path + ': root reference ' + repr(name))
            if name not in (b'\0', b'\1'):
                walk(child_lba, child_size, path.rstrip('/') + '/' + name.decode('ascii'))

    walk(root_lba, old_size, '/')
    return sorted(changes, key=lambda c: c['offset']), {
        'root_lba': root_lba, 'old_root_length': old_size,
        'new_root_length': logical_size, 'directory_count': len(seen),
        'pcsx2_image_type_before': 'CD' if old_size & 0xffff == 2048 else 'DVD',
        'pcsx2_image_type_after': 'DVD',
    }


def apply_changes(stream, changes):
    for change in changes:
        before, after = bytes.fromhex(change['before']), bytes.fromhex(change['after'])
        stream.seek(change['offset'])
        require(stream.read(len(before)) == before, 'Metadata preimage mismatch')
        stream.seek(change['offset'])
        stream.write(after)


def verify_exact_delta(source, target, changes):
    """Compare the entire disc with only the declared metadata bytes substituted."""
    source.seek(0)
    target.seek(0)
    old_hash, new_hash = hashlib.sha256(), hashlib.sha256()
    position = 0
    while True:
        original = source.read(8 * 1024 * 1024)
        actual = target.read(len(original) if original else 1)
        if not original:
            require(not actual, 'Output grew unexpectedly')
            break
        old_hash.update(original)
        expected = bytearray(original)
        for change in changes:
            start = change['offset'] - position
            after = bytes.fromhex(change['after'])
            left, right = max(0, start), min(len(expected), start + len(after))
            if left < right:
                expected[left:right] = after[left - start:right - start]
        require(actual == expected, 'Unexpected disc change at block %s' % position)
        new_hash.update(actual)
        position += len(original)
    return old_hash.hexdigest(), new_hash.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    require(not args.write, 'Root-only repair failed runtime testing; use repair_disc_layout.py instead')
    with BASE.open('rb') as source:
        changes, details = dvd_root_plan(source)
    print(json.dumps({'mode': 'dry-run', **details, 'changes': changes}, indent=2))
    if not args.write:
        return
    require(not OUTPUT.exists(), 'Versioned output already exists')
    # Stream-copy into a new version, never modify the reported broken image.
    digest = hashlib.sha256()
    with BASE.open('rb') as source, OUTPUT.open('xb') as target:
        while True:
            block = source.read(8 * 1024 * 1024)
            if not block:
                break
            digest.update(block)
            target.write(block)
    require(digest.hexdigest() == SOURCE_SHA256, 'Unexpected 0.1.6 source hash')
    with OUTPUT.open('r+b') as target:
        apply_changes(target, changes)
    with BASE.open('rb') as source, OUTPUT.open('rb') as target:
        old_hash, new_hash = verify_exact_delta(source, target, changes)
        require(iso_files(source) == iso_files(target), 'File extents changed')
        remaining, verified = dvd_root_plan(target)
        require(not remaining and verified['pcsx2_image_type_before'] == 'DVD', 'DVD normalization failed')
    previous = json.loads(BASE.with_suffix('.json').read_text(encoding='utf-8'))
    report = {**previous, 'version': VERSION, 'base': BASE.name, 'source_sha256': old_hash,
              'output': OUTPUT.name, 'sha256': new_hash, 'runtime_verified': False,
              'filesystem': '0.1.6 ISO9660/UDF sectors retained; exact logical ISO root length restores DVD detection.',
              'boot_repair': {**details, 'changes': changes, 'whole_disc_delta_verified': True},
              'prior_failure': '0.1.6 black screen before title; PCSX2 detects CD, then BIOS TLB faults.'}
    OUTPUT.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    manifest = json.loads(BASE.with_suffix('.manifest.json').read_text(encoding='utf-8'))
    manifest['version'] = VERSION
    manifest['boot_repair'] = {'source_iso': BASE.name, 'source_sha256': old_hash,
                               'output_sha256': new_hash, 'changes': changes,
                               'builder': 'tools/repair_disc_boot.py',
                               'builder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(OUTPUT), 'sha256': new_hash,
                      'metadata_fields_changed': len(changes), 'all_other_bytes_unchanged': True}, indent=2))


if __name__ == '__main__':
    main()
