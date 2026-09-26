"""Pull the PS2 audio track out of a PSS movie for preview renders. Read-only on the source.

PSS is an MPEG-2 program stream: video in PES stream 0xE0, audio in private stream 1 (0xBD) as a Sony
"SShd"/"SSbd" container. Only 16-bit PCM is converted here; ADPCM is reported and skipped.
usage: python pss_audio.py MOVIE002.PSS out.wav
"""
import struct
import sys
import wave


def private_payloads(data):
    at = 0
    while True:
        at = data.find(b'\x00\x00\x01\xbd', at)
        if at < 0: return
        length = struct.unpack_from('>H', data, at+4)[0]
        header = data[at+8]                      # PES_header_data_length
        yield data[at+9+header:at+6+length]
        at += 6+length


def main():
    source, target = sys.argv[1], sys.argv[2]
    data = open(source, 'rb').read()
    stream = bytearray()
    for payload in private_payloads(data):
        stream += payload[4:]                    # 4-byte Sony sub-stream header on every packet
    start = stream.find(b'SShd')
    if start < 0: raise SystemExit('No SShd header; first bytes: %r' % bytes(stream[:32]))
    size, fmt, rate, channels, interleave = struct.unpack_from('<5I', stream, start+4)
    body = stream.find(b'SSbd', start)
    length = struct.unpack_from('<I', stream, body+4)[0]
    pcm = bytes(stream[body+8:body+8+length])
    print({'format':fmt, 'rate':rate, 'channels':channels, 'interleave':interleave, 'declared_bytes':length, 'found_bytes':len(pcm)})
    if fmt not in (0, 1): raise SystemExit('Audio is not PCM (format %s); preview will be silent' % fmt)
    if fmt == 0:                                 # big-endian samples
        pcm = b''.join(pcm[i+1:i+2]+pcm[i:i+1] for i in range(0, len(pcm)-1, 2))
    if channels == 2 and interleave:
        # Sony interleaves by block, not by sample: `interleave` bytes of left, then as many of right.
        # Reading it as ordinary L/R sample pairs plays both channels chopped together, which is what
        # the first preview did. A WAV wants sample pairs, so the blocks are zipped back together.
        block, out = interleave, bytearray()
        for at in range(0, len(pcm)-2*block+1, 2*block):
            left, right = pcm[at:at+block], pcm[at+block:at+2*block]
            pairs = bytearray(2*block)
            pairs[0::4], pairs[1::4] = left[0::2], left[1::2]
            pairs[2::4], pairs[3::4] = right[0::2], right[1::2]
            out += pairs
        pcm = bytes(out)
    with wave.open(target, 'wb') as out:
        out.setnchannels(channels); out.setsampwidth(2); out.setframerate(rate); out.writeframes(pcm)


if __name__ == '__main__': main()
