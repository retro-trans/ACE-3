"""Restore Sony's boot filesystem around 0.1.6's unchanged translated files."""
import argparse
import binascii
import hashlib
import io
import json
import shutil
import struct
from pathlib import Path
import pycdlib
from build_ui_patch import ROOT, iso_files, require, u32
from repair_disc_boot import records

BASE = ROOT / 'work/output/ACE3-English-0.1.6.iso'
TEMPLATE = ROOT / 'work/output/ACE3-English-0.1.5.iso'
OUTPUT = ROOT / 'work/output/ACE3-English-0.1.7.iso'
VERSION = '0.1.7'
BASE_SHA = '8e072d12351c2ef337d1d3e36e6820068d29ee3f8c2fad3d7b40614f67bac8cc'
TEMPLATE_SHA = 'f4bbd24499168f7f65cd7bb9a6f0732c6e57edc47c63519cf895736e0e8ca776'


def align(n):
    return (n + 2047) // 2048 * 2048


def fix_udf_checksum(data):
    length = struct.unpack_from('<H', data, 10)[0]
    require(16 + length <= len(data), 'UDF checksum extent invalid')
    struct.pack_into('<H', data, 8, binascii.crc_hqx(data[16:16 + length], 0))
    data[4] = 0
    data[4] = sum(data[:16]) & 255


def plan(image=BASE):
    with image.open('rb') as source, TEMPLATE.open('rb') as template:
        wanted, old = iso_files(source), iso_files(template)
        require(wanted.keys() == old.keys(), 'Source file inventory changed')
        prefix_end = min(r['offset'] for r in wanted.values())
        require(prefix_end == min(r['offset'] for r in old.values()), 'Metadata regions differ')
        template.seek(0)
        prefix = bytearray(template.read(prefix_end))
        tail_start = align(max(r['offset'] + r['size'] for r in wanted.values()))
        require(tail_start >= align(max(r['offset'] + r['size'] for r in old.values())),
                'Would copy original file data into metadata tail')
        require(tail_start < TEMPLATE.stat().st_size, 'Remaster exceeds original volume capacity')
        template.seek(tail_start)
        tail = template.read()
    files_patched = []

    def walk(lba, size, path):
        for at, row in records(prefix[lba * 2048:lba * 2048 + size]):
            name = row[33:33 + row[32]]
            if name in (b'\0', b'\1'):
                continue
            name = path + '/' + name.decode('ascii').split(';')[0]
            if row[25] & 2:
                walk(u32(row, 2), u32(row, 10), name)
                continue
            record = wanted[name]
            address = lba * 2048 + at
            for delta, value in [(2, record['offset'] // 2048), (10, record['size'])]:
                struct.pack_into('<I', prefix, address + delta, value)
                struct.pack_into('>I', prefix, address + delta + 4, value)
            files_patched.append(name)

    walk(u32(prefix, 16 * 2048 + 158), u32(prefix, 16 * 2048 + 166), '')
    require(set(files_patched) == set(wanted), 'Incomplete ISO directory update')
    udf = pycdlib.PyCdlib()
    udf.open(str(TEMPLATE))
    partition_start = udf.udf_main_descs.partitions[0].part_start_location
    udf_files = []
    for parent, _, names in udf.walk(udf_path='/'):
        for name in names:
            path = parent.rstrip('/') + '/' + name
            record = wanted[path.upper()]
            entry = udf.get_record(udf_path=path)
            require(len(entry.alloc_descs) == 1, 'Expected original single Sony allocation')
            start = entry.orig_extent_loc * 2048
            require(start + 2048 <= len(prefix), 'UDF file entry outside metadata prefix')
            raw = bytearray(prefix[start:start + 2048])
            require(struct.unpack_from('<H', raw)[0] == 261, 'Expected UDF file entry')
            ad = 176 + u32(raw, 168)
            require(u32(raw, 172) == 8 and ad + 8 <= 2048, 'Expected short allocation descriptor')
            struct.pack_into('<Q', raw, 56, record['size'])
            struct.pack_into('<Q', raw, 64, align(record['size']) // 2048)
            # Preserve Sony's original full 32-bit allocation length convention,
            # including its >1 GiB DATA.BIN extent. Do not reserialize this as
            # generic UDF allocation flags or introduce a new extent chain.
            struct.pack_into('<II', raw, ad, record['size'], record['offset'] // 2048 - partition_start)
            fix_udf_checksum(raw)
            prefix[start:start + 2048] = raw
            udf_files.append(path)
    udf.close()
    require(len(udf_files) == len(wanted), 'Incomplete UDF update')
    require(iso_files(io.BytesIO(prefix)) == wanted, 'Restored ISO metadata does not match file extents')
    summary = {'iso_files': len(wanted), 'udf_files': len(udf_files),
               'metadata_prefix_bytes': prefix_end, 'tail_start': tail_start,
               'output_size': TEMPLATE.stat().st_size, 'root_length': u32(prefix, 16 * 2048 + 166),
               'prefix_sha256': hashlib.sha256(prefix).hexdigest(), 'tail_sha256': hashlib.sha256(tail).hexdigest(),
               'sample_files': {name: wanted[name] for name in ['/SYSTEM.CNF', '/SLPS_257.84', '/DATA.BIN']}}
    return bytes(prefix), tail_start, tail, summary


def install_metadata(path, prefix, tail_start, tail):
    with path.open('r+b') as target:
        target.seek(0)
        target.write(prefix)
        target.seek(tail_start)
        target.write(tail)
        target.truncate(tail_start + len(tail))


def verify(path, prefix, tail_start, tail):
    with BASE.open('rb') as source, path.open('rb') as target:
        source_hash, output_hash = hashlib.sha256(), hashlib.sha256()
        while True:
            data = source.read(8 * 1024 * 1024)
            if not data:
                break
            source_hash.update(data)
        require(source_hash.hexdigest() == BASE_SHA, 'Unexpected translated source ISO')
        source.seek(len(prefix))
        require(target.read(len(prefix)) == prefix, 'Prefix mismatch')
        output_hash.update(prefix)
        remaining = tail_start - len(prefix)
        while remaining:
            count = min(remaining, 8 * 1024 * 1024)
            before, after = source.read(count), target.read(count)
            require(len(before) == count and before == after, 'Game payload changed during repair')
            output_hash.update(after)
            remaining -= count
        require(target.read() == tail, 'Tail mismatch')
        output_hash.update(tail)
        require(iso_files(source) == iso_files(target), 'ISO file locations changed')
        wanted = iso_files(target)
    disc = pycdlib.PyCdlib()
    disc.open(str(path))
    partition = disc.udf_main_descs.partitions[0].part_start_location
    for parent, _, names in disc.walk(udf_path='/'):
        for name in names:
            udf_path = parent.rstrip('/') + '/' + name
            entry = disc.get_record(udf_path=udf_path)
            record = wanted[udf_path.upper()]
            require(entry.info_len == record['size'], 'UDF logical size mismatch')
            require((partition + entry.alloc_descs[0].log_block_num) * 2048 == record['offset'],
                    'UDF/ISO location mismatch')
    disc.close()
    return output_hash.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--probe', type=Path, help='Apply metadata to an existing diagnostic ISO inside work/build/0.1.7')
    args = parser.parse_args()
    prefix, tail_start, tail, summary = plan()
    print(json.dumps({'mode': 'dry-run', **summary}, indent=2))
    if not args.write:
        return
    if args.probe:
        path = args.probe.resolve()
        require(path.parent == (ROOT / 'work/build/0.1.7').resolve(), 'Probe outside diagnostic folder')
        install_metadata(path, prefix, tail_start, tail)
        print('Diagnostic metadata installed:', path)
        return
    require(not OUTPUT.exists(), 'Versioned output already exists')
    with TEMPLATE.open('rb') as template:
        digest = hashlib.sha256()
        for block in iter(lambda: template.read(8 * 1024 * 1024), b''):
            digest.update(block)
        require(digest.hexdigest() == TEMPLATE_SHA, 'Unexpected working template ISO')
    with BASE.open('rb') as source, OUTPUT.open('xb') as target:
        shutil.copyfileobj(source, target, 8 * 1024 * 1024)
    install_metadata(OUTPUT, prefix, tail_start, tail)
    digest = verify(OUTPUT, prefix, tail_start, tail)
    report = json.loads(BASE.with_suffix('.json').read_text(encoding='utf-8'))
    report.update(version=VERSION, base=BASE.name, output=OUTPUT.name, size=OUTPUT.stat().st_size,
                  sha256=digest, runtime_verified=False,
                  filesystem='Original Sony ISO9660/UDF 1.02 metadata with remastered file extents and regenerated UDF checksums.',
                  boot_repair={**summary, 'template': TEMPLATE.name, 'template_sha256': TEMPLATE_SHA,
                               'source_sha256': BASE_SHA, 'all_game_payload_bytes_unchanged': True})
    OUTPUT.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    manifest = json.loads(BASE.with_suffix('.manifest.json').read_text(encoding='utf-8'))
    manifest.update(version=VERSION)
    manifest['payload_provenance'] = 'Base and tool_sha256 describe the inherited 0.1.6 payload; boot_repair describes this release.'
    manifest['boot_repair'] = {**report['boot_repair'], 'output_sha256': digest,
                              'builder': 'tools/repair_disc_layout.py',
                              'builder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    OUTPUT.with_suffix('.manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(OUTPUT), 'sha256': digest, 'payloads_unchanged': True}, indent=2))


if __name__ == '__main__':
    main()
