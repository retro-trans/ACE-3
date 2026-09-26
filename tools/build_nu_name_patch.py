"""0.1.47: capitalize Nu Gundam consistently. Read-only preview unless --write."""
import argparse
import hashlib
import json
import re
import struct
from build_ui_patch import ROOT, require
from dialogue_corpus import archive, parse_table

VERSION = '0.1.47'
BASE = ROOT/'work/output/ACE3-English-0.1.46.iso'
OUTPUT = ROOT/'work/output/ACE3-English-0.1.47.iso'
BASE_SHA = '9c4e95b4294ed8b017279ef5e957cb3388bd5802d444c08b9524baab9a7035f8'
OLD, NEW = b'nu Gundam', b'Nu Gundam'


def source_plan():
    changes = []
    for folder in ('work/glossary', 'work/translation/en'):
        for path in (ROOT/folder).rglob('*.json'):
            before = path.read_bytes()
            if OLD not in before:
                continue
            after = before.replace(OLD, NEW)
            after = after.replace(b"'Nu Gundam' kept lowercase at sentence-start per locked unit spelling (unit_names_014_a.json).",
                                  b"User corrected the locked unit spelling to 'Nu Gundam' in 0.1.47.")
            after = after.replace(b'Nu Gundam kept lowercase per unit_names_014_a.json, even though the line begins with it.',
                                  b'Nu Gundam capitalization follows the user correction in 0.1.47.')
            after = after.replace(b"'Nu Gundam' kept lowercase at sentence-start, matching the locked spelling in unit_names_014_a.json ('en': 'Nu Gundam').",
                                  b"Superseded in 0.1.47: user requested the locked spelling 'Nu Gundam'.")
            json.loads(after.decode('utf-8'))
            changes.append((path, before, after))
    return changes


def disc_plan():
    edits, checks = {}, []
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        for _, length, offset, rid in entries:
            origin = fi['offset']+offset
            f.seek(origin)
            data = f.read(length)
            if OLD not in data:
                continue
            covered = set()
            at = 0
            while True:
                at = data.find(b'\0\0\1\0', at)
                if at < 0:
                    break
                try:
                    size, _, _, rows = parse_table(data, at)
                except (ValueError, UnicodeError, struct.error):
                    at += 4
                    continue
                for slot, tid, ptr, raw in rows:
                    if OLD not in raw:
                        continue
                    # Same-byte-length spelling edit; pointers, commands and
                    # terminating zero are untouched, including shared aliases.
                    for match in re.finditer(re.escape(OLD), raw):
                        pos = at+ptr+match.start()
                        covered.add(pos)
                        edits[origin+pos] = NEW
                    checks.append(dict(resource=rid, table_offset=at, text_id=tid,
                                       before=raw.decode('cp932'), after=raw.replace(OLD, NEW).decode('cp932')))
                at += size
            for match in re.finditer(re.escape(OLD), data):
                pos = match.start()
                if pos in covered:
                    continue
                # Unit parameter records keep their display name in a fixed
                # 32-byte field at PRM+16, outside the indexed text tables.
                require(data[pos-16:pos-12] == b'PRM\0', 'Unclassified name occurrence')
                raw = data[pos:pos+32].split(b'\0', 1)[0]
                require(raw in (OLD, OLD+b' (HWS)'), 'Unexpected parameter name')
                edits[origin+pos] = NEW
                checks.append(dict(resource=rid, parameter_offset=pos-16,
                                   before=raw.decode('ascii'), after=raw.replace(OLD, NEW).decode('ascii')))
    require(edits, 'No active unit names found')
    return edits, checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    sources = source_plan()
    edits, checks = disc_plan()
    print(json.dumps(dict(source_files=[str(p.relative_to(ROOT)) for p, _, _ in sources],
                          edits=len(edits), rows=checks), indent=2), flush=True)
    if not args.write:
        return
    require(not OUTPUT.exists(), 'Output already exists')
    source_sha, output_sha = hashlib.sha256(), hashlib.sha256()
    position = 0
    with BASE.open('rb') as source, OUTPUT.open('xb') as output:
        while True:
            raw = source.read(8 << 20)
            if not raw:
                break
            expected = bytearray(raw)
            for at, replacement in edits.items():
                lo, hi = max(position, at), min(position+len(raw), at+len(OLD))
                if lo < hi:
                    require(raw[lo-position:hi-position] == OLD[lo-at:hi-at], 'Preimage mismatch')
                    expected[lo-position:hi-position] = replacement[lo-at:hi-at]
            output.write(expected)
            source_sha.update(raw)
            output_sha.update(expected)
            position += len(raw)
    require(source_sha.hexdigest() == BASE_SHA, 'Unexpected base ISO')
    verify = hashlib.sha256()
    with OUTPUT.open('rb') as output:
        for chunk in iter(lambda: output.read(8 << 20), b''):
            verify.update(chunk)
    require(verify.digest() == output_sha.digest(), 'Written ISO verification failed')
    for path, before, after in sources:
        require(path.read_bytes() == before, 'Source changed during build')
        path.write_bytes(after)
    report = dict(version=VERSION, size=position, base_sha256=source_sha.hexdigest(),
                  sha256=verify.hexdigest(), whole_disc_verified=True, runtime_verified=False,
                  active_occurrences=len(edits), rows=checks,
                  source_files=[str(p.relative_to(ROOT)) for p, _, _ in sources])
    OUTPUT.with_suffix('.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('VERIFIED', OUTPUT, report['sha256'], flush=True)


if __name__ == '__main__':
    main()
