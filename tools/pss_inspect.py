"""Describe the pack/PES layout of a PS2 PSS movie. Read-only.

usage: python pss_inspect.py MOVIE002.PSS [packs_to_print]
"""
import collections
import struct
import sys


def pts(b):
    return ((b[0] >> 1) & 7) << 30 | b[1] << 22 | (b[2] >> 1) << 15 | b[3] << 7 | b[4] >> 1


def packets(data):
    """Yield (offset, stream_id, header_bytes, payload_offset, payload_length, info) for every start code >= 0xB9."""
    at = 0
    while at+4 <= len(data):
        if data[at:at+3] != b'\x00\x00\x01':
            nxt = data.find(b'\x00\x00\x01', at)
            if nxt < 0: return
            yield at, None, None, at, nxt-at, {'gap':nxt-at}; at = nxt; continue
        sid = data[at+3]
        if sid == 0xB9: yield at, sid, None, at+4, 0, {}; at += 4; continue
        if sid == 0xBA:
            stuffing = data[at+13] & 7
            scr = data[at+4:at+10]
            base = ((scr[0] >> 3) & 7) << 30 | (scr[0] & 3) << 28 | scr[1] << 20 | (scr[2] >> 3) << 15 | (scr[2] & 3) << 13 | scr[3] << 5 | scr[4] >> 3
            rate = (data[at+10] << 14 | data[at+11] << 6 | data[at+12] >> 2)
            yield at, sid, None, at+14+stuffing, 0, {'scr':base, 'mux_rate':rate*50, 'stuffing':stuffing}; at += 14+stuffing; continue
        length = struct.unpack_from('>H', data, at+4)[0]
        info = {'length':length}
        payload = at+6
        if sid in (0xBD,) or 0xC0 <= sid <= 0xEF:
            flags, hlen = data[at+7], data[at+8]
            info.update(flags1=data[at+6], flags2=flags, header_len=hlen)
            if flags & 0x80: info['pts'] = pts(data[at+9:at+14])
            if flags & 0x40: info['dts'] = pts(data[at+14:at+19])
            payload = at+9+hlen
        yield at, sid, data[at:payload], payload, at+6+length-payload, info
        at += 6+length


def main():
    data = open(sys.argv[1], 'rb').read(); show = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    count = collections.Counter(); sizes = collections.defaultdict(collections.Counter); headers = collections.Counter()
    pack_gaps = collections.Counter(); last_pack = None; video = audio = 0; stamped = 0
    for n, (at, sid, head, pay, plen, info) in enumerate(packets(data)):
        if n < show: print(hex(at), hex(sid) if sid is not None else 'gap', plen, info, head[6:9+info.get('header_len', 0)].hex() if head else '')
        count[sid] += 1
        if sid == 0xBA:
            if last_pack is not None: pack_gaps[at-last_pack] += 1
            last_pack = at
        elif sid == 0xE0:
            video += plen; sizes['video'][plen] += 1; headers[(info['flags1'], info['flags2'], info['header_len'])] += 1; stamped += 'pts' in info
        elif sid == 0xBD:
            audio += plen; sizes['audio'][plen] += 1
    print('counts', {hex(k) if k is not None else 'gap':v for k, v in count.items()})
    print('pack spacing', pack_gaps.most_common(4))
    print('video ES bytes', video, 'audio payload bytes', audio, 'video packets with PTS', stamped)
    print('video payload sizes', sizes['video'].most_common(5)); print('audio payload sizes', sizes['audio'].most_common(4))
    print('video PES header variants (flags1, flags2, header_len)', headers.most_common(6))
    print('file size', len(data), 'tail', data[-16:].hex())


if __name__ == '__main__': main()
