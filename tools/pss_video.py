"""Demux the MPEG-2 video elementary stream of a PSS movie and describe how it was encoded. Read-only.

usage: python pss_video.py MOVIE002.PSS [out.m2v]
"""
import collections
import struct
import sys
from pss_inspect import packets

TYPES = {1:'I', 2:'P', 3:'B'}


def elementary(data):
    out = bytearray()
    for at, sid, head, pay, plen, info in packets(data):
        if sid == 0xE0: out += data[pay:pay+plen]
    return bytes(out)


def pictures(es):
    """Yield (offset, kind, temporal_reference) for each picture; kind 'S'/'G' marks sequence and GOP headers."""
    at = 0
    while True:
        at = es.find(b'\x00\x00\x01', at)
        if at < 0 or at+6 > len(es): return
        code = es[at+3]
        if code == 0x00:
            bits = es[at+4] << 8 | es[at+5]
            yield at, TYPES.get((bits >> 3) & 7, '?'), bits >> 6
        elif code == 0xB3: yield at, 'S', None
        elif code == 0xB8: yield at, 'G', es[at+7] >> 6 & 1   # closed_gop flag
        at += 4


def main():
    data = open(sys.argv[1], 'rb').read(); es = elementary(data)
    if len(sys.argv) > 2: open(sys.argv[2], 'wb').write(es)
    s = es.find(b'\x00\x00\x01\xb3')
    b = es[s+4:s+12]
    width, height = b[0] << 4 | b[1] >> 4, (b[1] & 15) << 8 | b[2]
    aspect, rate_code = b[3] >> 4, b[3] & 15
    bit_rate = (b[4] << 10 | b[5] << 2 | b[6] >> 6)*400
    vbv = ((b[6] & 0x1f) << 5 | b[7] >> 3)*16384
    print({'width':width, 'height':height, 'aspect_code':aspect, 'frame_rate_code':rate_code, 'bit_rate':bit_rate, 'vbv_bits':vbv,
           'load_intra_matrix':b[7] >> 1 & 1})
    ext = es.find(b'\x00\x00\x01\xb5', s)
    e = es[ext+4:ext+10]
    print({'ext_id':e[0] >> 4, 'profile_level':hex((e[0] & 15) << 4 | e[1] >> 4), 'progressive_sequence':e[1] >> 3 & 1, 'chroma_format':e[1] >> 1 & 3})
    order = list(pictures(es))
    kinds = ''.join(k for _, k, _ in order)
    print('start', kinds[:80])
    print('counts', collections.Counter(kinds))
    gops = [len(g.replace('S', '')) for g in kinds.split('G')[1:]]
    print('GOP lengths', collections.Counter(gops).most_common(5), 'closed flags', collections.Counter(t for _, k, t in order if k == 'G'))
    sizes = collections.defaultdict(list); pics = [(o, k) for o, k, _ in order if k in 'IPB']
    for (o, k), (n, _) in zip(pics, pics[1:]+[(len(es), None)]): sizes[k].append(n-o)
    for k, v in sizes.items(): print(k, 'count', len(v), 'avg', sum(v)//len(v), 'min', min(v), 'max', max(v))
    # picture coding extension of the first picture
    pce = es.find(b'\x00\x00\x01\xb5', es.find(b'\x00\x00\x01\x00'))
    c = es[pce+4:pce+9]
    print({'f_codes':hex(c[0] & 15)+hex(c[1]), 'intra_dc_precision':c[2] >> 2 & 3, 'picture_structure':c[2] & 3, 'top_field_first':c[3] >> 7,
           'frame_pred_frame_dct':c[3] >> 6 & 1, 'q_scale_type':c[3] >> 4 & 1, 'intra_vlc_format':c[3] >> 3 & 1, 'alternate_scan':c[3] >> 2 & 1,
           'repeat_first_field':c[3] >> 1 & 1, 'progressive_frame':c[4] >> 7})
    print('ES bytes', len(es), 'sequence headers', kinds.count('S'))


if __name__ == '__main__': main()
