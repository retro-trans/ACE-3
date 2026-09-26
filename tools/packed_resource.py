"""Codec for the compressed resources in DATA.BIN.

Layout, settled against resource 701009 whose plain twin (resource 4010) is on the same disc:

    00 01 00 00 | unpacked size, big-endian u32 | 00 00 00 00 | LZSS body | zero padding

Body: a flag byte announces eight items, least significant bit first. A clear bit is one literal byte. A set bit
is a two-byte reference `b0 b1`: field = b0 << 4 | b1 >> 4, length = (b1 & 15) + 1 (2..16; a zero nibble makes the
game's decoder stop). Where the copy starts depends on how much has been written, exactly as in the game's decoder
(EE code at 0x0023E950): while fewer than 4096 bytes are out, `field` is an absolute offset from the start of the
output; from then on the window base slides and the copy starts `4096 - field` bytes back. Copies are byte by byte,
so they may overlap their own output. An earlier version of this codec used the sliding rule everywhere; it still
decoded stock files to almost the right bytes, but every early reference it *wrote* pointed at the wrong place,
which corrupted the scene header and froze the game (0.1.25, 0.1.26).
"""
import struct

MAGIC = b'\x00\x01\x00\x00'
WINDOW, MAX_LEN, MIN_LEN = 4096, 16, 2


def is_packed(data):
    return len(data) >= 12 and data[:4] == MAGIC and data[8:12] == b'\0\0\0\0'


def unpack(data):
    if not is_packed(data): raise ValueError('Not a packed resource')
    size = struct.unpack('>I', data[4:8])[0]
    out = bytearray(); at = 12
    while len(out) < size:
        flags = data[at]; at += 1
        for bit in range(8):
            if len(out) >= size: break
            if flags >> bit & 1:
                b0, b1 = data[at], data[at+1]; at += 2
                field = b0 << 4 | b1 >> 4
                source = field if len(out) < WINDOW else len(out)-WINDOW+field
                for k in range((b1 & 15)+1):
                    out.append(out[source+k] if source+k < len(out) else 0)
            else:
                out.append(data[at]); at += 1
    return bytes(out), at


def pack(plain, align=16):
    """Greedy LZSS with hash chains on three-byte prefixes; output is valid for `unpack` and the game's decoder."""
    out = bytearray(MAGIC+struct.pack('>I', len(plain))+b'\0\0\0\0')
    chains, n, at = {}, len(plain), 0
    flag_at, bit, items = None, 8, bytearray()

    def insert(p):
        if p+3 <= n: chains.setdefault(plain[p:p+3], []).append(p)

    while at < n:
        best_len, best_src = 0, 0
        if at+3 <= n:
            candidates = chains.get(plain[at:at+3], ())
            limit = min(MAX_LEN, n-at)
            for p in reversed(candidates[-64:]):
                if at-p > WINDOW: break
                k = 3
                while k < limit and plain[p+k] == plain[at+k]: k += 1
                if k > best_len:
                    best_len, best_src = k, p
                    if k == limit: break
        if bit == 8:
            out += items; items = bytearray(); flag_at = len(out); out.append(0); bit = 0
        if best_len >= 3:
            field = best_src if at < WINDOW else WINDOW-(at-best_src)
            out[flag_at] |= 1 << bit
            items += bytes([field >> 4, (field & 15) << 4 | (best_len-1)])
            for p in range(at, at+best_len): insert(p)
            at += best_len
        else:
            items.append(plain[at]); insert(at); at += 1
        bit += 1
    out += items
    out += bytes(-len(out) % align)
    return bytes(out)


if __name__ == '__main__':
    from build_ui_patch import ROOT
    from dialogue_corpus import archive
    with next(ROOT.glob('*.iso')).open('rb') as f:
        fi, es = archive(f)
        def get(rid):
            e = next(x for x in es if x[3] == rid); f.seek(fi['offset']+e[2]); return f.read(e[1])
        packed, plain = get(701009), get(4010)
    got, used = unpack(packed)
    print('unpack(701009) == plain 4010:', got == plain, '| stream bytes used', used, 'of', len(packed), '| tail', packed[used:used+8].hex())
    again = pack(plain)
    print('repacked size', len(again), 'vs original', len(packed), '| round trip:', unpack(again)[0] == plain)
