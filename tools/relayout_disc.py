"""Re-lay a built disc onto the original disc's file order so an xdelta patch against the original stays small.

The builders master the disc with pycdlib, which reorders files: almost every file lands about 1.7 GB away from
where the original disc keeps it, and xdelta3 cannot match across that distance (a 0.1.32 patch came out at 1 GB
although only DATA.BIN, the ELF and one movie differ). This tool takes the ORIGINAL disc as the template - its
metadata prefix, its file order, its tail - and writes every file back at its original sector; only files that grew
(DATA.BIN, +4 MB) push the files after them, so nothing moves more than a few megabytes. Directory records
(ISO9660, both endians) and UDF file entries are rewritten the same way tools/repair_disc_layout.py does.

    python tools/relayout_disc.py <built iso name under work/output> [--write]
Writes work/release/<name>-orig-layout.iso and verifies every file's bytes against the built disc.
"""
import argparse
import hashlib
import io
import json
import struct
import sys
import pycdlib
from build_ui_patch import ROOT, iso_files, require, u32
from repair_disc_boot import records
from repair_disc_layout import align, fix_udf_checksum

SECTOR = 2048


def layout(original, built):
    """New extents: original order and positions, shifted only by growth of earlier files."""
    require(original.keys() == built.keys(), 'File inventory differs from the original disc')
    order = sorted(original, key=lambda k: original[k]['offset'])
    wanted, shift = {}, 0
    for name in order:
        o, b = original[name], built[name]
        wanted[name] = {'offset': o['offset']+shift, 'size': b['size']}
        shift += align(b['size'])-align(o['size'])
    return wanted, order


def metadata(template, wanted):
    """Original metadata prefix and tail with the file extents rewritten (same method as repair_disc_layout)."""
    with template.open('rb') as t:
        original = iso_files(t); prefix_end = min(r['offset'] for r in original.values())
        t.seek(0); prefix = bytearray(t.read(prefix_end))
        old_tail_start = align(max(r['offset']+r['size'] for r in original.values())); t.seek(old_tail_start); tail = t.read()
    tail_start = align(max(r['offset']+r['size'] for r in wanted.values()))
    patched = []

    def walk(lba, size, path):
        for at, row in records(prefix[lba*SECTOR:lba*SECTOR+size]):
            name = row[33:33+row[32]]
            if name in (b'\0', b'\1'): continue
            name = path+'/'+name.decode('ascii').split(';')[0]
            if row[25] & 2: walk(u32(row, 2), u32(row, 10), name); continue
            record = wanted[name]; address = lba*SECTOR+at
            for delta, value in ((2, record['offset']//SECTOR), (10, record['size'])):
                struct.pack_into('<I', prefix, address+delta, value); struct.pack_into('>I', prefix, address+delta+4, value)
            patched.append(name)
    walk(u32(prefix, 16*SECTOR+158), u32(prefix, 16*SECTOR+166), '')
    require(set(patched) == set(wanted), 'Incomplete ISO directory update')
    udf = pycdlib.PyCdlib(); udf.open(str(template)); partition = udf.udf_main_descs.partitions[0].part_start_location; count = 0
    for parent, _, names in udf.walk(udf_path='/'):
        for name in names:
            path = parent.rstrip('/')+'/'+name; record = wanted[path.upper()]; entry = udf.get_record(udf_path=path)
            require(len(entry.alloc_descs) == 1, 'Expected a single allocation')
            start = entry.orig_extent_loc*SECTOR; raw = bytearray(prefix[start:start+SECTOR])
            require(struct.unpack_from('<H', raw)[0] == 261, 'Expected a UDF file entry')
            ad = 176+u32(raw, 168); require(u32(raw, 172) == 8 and ad+8 <= SECTOR, 'Expected a short allocation descriptor')
            struct.pack_into('<Q', raw, 56, record['size']); struct.pack_into('<Q', raw, 64, align(record['size'])//SECTOR)
            struct.pack_into('<II', raw, ad, record['size'], record['offset']//SECTOR-partition)
            fix_udf_checksum(raw); prefix[start:start+SECTOR] = raw; count += 1
    udf.close()
    require(count == len(wanted), 'Incomplete UDF update')
    require(iso_files(io.BytesIO(bytes(prefix))) == wanted, 'Rewritten metadata does not describe the planned extents')
    return bytes(prefix), tail_start, tail


class Null:
    def write(self, block): pass


def copy(src, dst, offset, size, digest=None):
    src.seek(offset); left = size
    while left:
        block = src.read(min(8 << 20, left)); require(block, 'Short read'); dst.write(block); left -= len(block)
        if digest is not None: digest.update(block)


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('built'); ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    template = next(ROOT.glob('*.iso')); built_path = ROOT/'work/output'/a.built
    out = ROOT/'work/release'/(built_path.stem+'-orig-layout.iso')
    with template.open('rb') as t, built_path.open('rb') as b:
        original, built = iso_files(t), iso_files(b)
    wanted, order = layout(original, built)
    moved = {k: wanted[k]['offset']-original[k]['offset'] for k in order if wanted[k]['offset'] != original[k]['offset']}
    prefix, tail_start, tail = metadata(template, wanted)
    summary = {'files': len(order), 'moved': len(moved), 'max_shift_bytes': max(moved.values(), default=0),
               'grown': [k for k in order if built[k]['size'] != original[k]['size']], 'output': str(out), 'output_size': tail_start+len(tail)}
    print(('WRITE' if a.write else 'DRY RUN'), json.dumps(summary))
    if not a.write: return
    out.parent.mkdir(exist_ok=True); require(not out.exists(), 'Output exists')
    hashes = {}
    with built_path.open('rb') as b, out.open('wb') as o:
        o.write(prefix)
        for name in order:
            record = wanted[name]; require(o.tell() <= record['offset'], 'Extent overlap at '+name)
            o.write(b'\0'*(record['offset']-o.tell())); d = hashlib.sha256(); copy(b, o, built[name]['offset'], record['size'], d); hashes[name] = d.hexdigest()
        o.write(b'\0'*(tail_start-o.tell())); o.write(tail)
    # Verify: extents as planned, every file byte-identical to the built disc, UDF agrees with ISO9660.
    with out.open('rb') as o, built_path.open('rb') as b:
        require(iso_files(o) == wanted, 'Output extents differ from plan')
        for name in order:
            d1, d2 = hashlib.sha256(), hashlib.sha256(); copy(o, Null(), wanted[name]['offset'], wanted[name]['size'], d1)
            copy(b, Null(), built[name]['offset'], built[name]['size'], d2); require(d1.hexdigest() == d2.hexdigest() == hashes[name], 'File payload differs: '+name)
    disc = pycdlib.PyCdlib(); disc.open(str(out)); partition = disc.udf_main_descs.partitions[0].part_start_location
    for parent, _, names in disc.walk(udf_path='/'):
        for name in names:
            path = parent.rstrip('/')+'/'+name; entry = disc.get_record(udf_path=path); record = wanted[path.upper()]
            require(entry.info_len == record['size'] and (partition+entry.alloc_descs[0].log_block_num)*SECTOR == record['offset'], 'UDF/ISO mismatch '+path)
    disc.close()
    digest = hashlib.sha256()
    with out.open('rb') as o:
        for block in iter(lambda: o.read(8 << 20), b''): digest.update(block)
    summary['sha256'] = digest.hexdigest(); summary['verified'] = True
    out.with_suffix('.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8'); print(json.dumps(summary))


if __name__ == '__main__': main()
