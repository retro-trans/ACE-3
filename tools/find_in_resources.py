"""Find text inside DATA.BIN resources, looking inside LZSS-packed ones too. Read-only; prints locations only.

usage: python find_in_resources.py <iso under work/output or 'original'> <text> [<text> ...]
For every hit: resource ID, whether the resource is packed, and the text table (if the hit sits in one) with its
text ID, so the owner of a string can be identified without dumping the script.
"""
import struct
import sys
from build_ui_patch import ROOT
from dialogue_corpus import archive, parse_table
from packed_resource import is_packed, unpack


def tables(data):
    at = 0
    while True:
        at = data.find(b'\x00\x00\x01\x00', at)
        if at < 0: return
        try:
            size, pointers, count, rows = parse_table(data, at)
        except (ValueError, UnicodeError, struct.error):
            at += 4; continue
        yield at, size, rows
        at += max(size, 4)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    iso = next(ROOT.glob('*.iso')) if sys.argv[1] == 'original' else ROOT/'work/output'/sys.argv[1]
    needles = [(t, t.encode('cp932')) for t in sys.argv[2:]]
    with iso.open('rb') as f:
        info, entries = archive(f)
        for _, size, off, rid in entries:
            f.seek(info['offset']+off); data = f.read(size); packed = is_packed(data)
            if packed:
                if struct.unpack('>I', data[4:8])[0] > 16_000_000: continue
                try: data = unpack(data)[0]
                except IndexError: continue
            hits = [t for t, n in needles if n in data]
            if not hits: continue
            owners = []
            for at, tsize, rows in tables(data):
                for slot, text_id, _, raw in rows:
                    for t, n in needles:
                        if n in raw: owners.append((t, at, text_id, len(rows), raw.decode('cp932')[:40]))
            print(rid, 'packed' if packed else 'plain', len(data), hits)
            for o in owners[:12]: print('     table@%d id %d of %d rows: %s  [%s]' % (o[1], o[2], o[3], o[4], o[0]))


if __name__ == '__main__': main()
