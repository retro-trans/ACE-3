"""Put a re-encoded MPEG-2 video stream back into a PS2 PSS movie. Dry-run unless --write.

The original file is the skeleton: every pack header, SCR, system header, audio packet and padding packet is
kept byte-for-byte and the file size does not change. Only the payload of the video PES packets (stream 0xE0)
is refilled with the new elementary stream, and their 10 timestamp bytes are regenerated:

- each access unit (sequence/GOP headers + picture) starts in a packet of its own, as in the original, so every
  picture keeps its own PTS/DTS; the gap is zero-byte stuffing, which MPEG-2 allows in front of a start code;
- I and P pictures carry PTS+DTS, B pictures PTS only, exactly like the original muxer;
- the clock starts at the original first DTS and advances 3003 ticks (1/29.97 s at 90 kHz) per picture.

usage: python pss_remux.py original.PSS new.m2v out.PSS [--write]
"""
import sys
from pss_inspect import packets
from pss_video import pictures

TICKS = 3003


def stamp(prefix, value):
    return bytes([prefix << 4 | (value >> 29 & 0x0e) | 1, value >> 22 & 0xff, (value >> 14 & 0xfe) | 1, value >> 7 & 0xff, (value << 1 & 0xfe) | 1])


def access_units(es):
    """Split the stream into access units and give each its picture type and display position."""
    marks = list(pictures(es)); units = []; start = None
    for at, kind, _ in marks:
        if start is None: start = at
        if kind in 'IPB': units.append([start, kind]); start = None
    bounds = [u[0] for u in units]+[len(es)]
    # Display order: a B picture is shown at once, an I/P picture after the B pictures that follow it.
    order, pending, shown = {}, None, 0
    for n, (_, kind) in enumerate(units):
        if kind == 'B': order[n] = shown; shown += 1
        else:
            if pending is not None: order[pending] = shown; shown += 1
            pending = n
    if pending is not None: order[pending] = shown
    return [(bounds[n], bounds[n+1], units[n][1], order[n]) for n in range(len(units))]


def plan(original, es, ticks=TICKS, pace_to_original=False, max_lead_packets=16):
    slots = [(at, pay, plen, info) for at, sid, head, pay, plen, info in packets(original) if sid == 0xE0]
    first = slots[0][3]
    base_dts, base_pts = first['dts'], first['pts']
    old_units = access_units(b''.join(original[pay:pay+plen] for _, pay, plen, _ in slots))
    units = access_units(es)
    import bisect
    edges = []; position = 0
    for at, pay, plen, _ in slots:
        edges.append(position); position += plen
    old_slots = [bisect.bisect_right(edges, a)-1 for a, _, _, _ in old_units]
    if pace_to_original and len(units) != len(old_units):
        raise ValueError('Pacing requires unchanged picture count')
    out = bytearray(original); slot = 0; used = 0; starts_here = False; stuffing = 0; drift = 0; placed = []
    def header(index, unit):
        at, pay, plen, info = slots[index]
        hlen = info['header_len']; field = bytearray(b'\xff'*hlen); flags = out[at+7] & 0x3f
        if unit is not None:
            n, (_, _, kind, shown) = unit
            dts, pts = base_dts+n*ticks, base_pts+shown*ticks
            if pts == dts: field[:5] = stamp(2, pts); flags |= 0x80
            else: field[:5] = stamp(3, pts); field[5:10] = stamp(1, dts); flags |= 0xc0
        if hlen > 10: field[10:] = original[at+9+10:at+9+hlen]     # the first packet's P-STD extension
        out[at+7] = flags; out[at+9:at+9+hlen] = field
    for index in range(len(slots)): header(index, None)
    for n, (a, b, kind, shown) in enumerate(units):
        if starts_here or (pace_to_original and used):   # paced units always start in a fresh packet
            at, pay, plen, _ = slots[slot]
            out[pay+used:pay+plen] = bytes(plen-used); stuffing += plen-used; slot += 1; used = 0
        if pace_to_original:
            while slot < max(0, old_slots[n]-max_lead_packets):
                at, pay, plen, _ = slots[slot]
                out[pay:pay+plen] = bytes(plen); stuffing += plen
                slot += 1
        if slot >= len(slots): raise ValueError('New stream does not fit: picture %d of %d' % (n, len(units)))
        header(slot, (n, (a, b, kind, shown))); starts_here = True; placed.append(slot)
        data = es[a:b]; done = 0
        while done < len(data):
            if slot >= len(slots): raise ValueError('New stream does not fit: picture %d of %d' % (n, len(units)))
            at, pay, plen, _ = slots[slot]
            take = min(plen-used, len(data)-done)
            out[pay+used:pay+used+take] = data[done:done+take]; used += take; done += take
            if used == plen: slot += 1; used = 0; starts_here = False
    tail = 0
    if slot < len(slots):
        at, pay, plen, _ = slots[slot]; out[pay+used:pay+plen] = bytes(plen-used); tail += plen-used
        for at, pay, plen, _ in slots[slot+1:]: out[pay:pay+plen] = bytes(plen); tail += plen
    # How far each picture sits from where the original had it, in packets of 4 KB (about 7 ms each at 4.5 Mb/s).
    shift = [p-o for p, o in zip(placed, old_slots)]
    report = {'pictures_new':len(units), 'pictures_original':len(old_units), 'video_packets':len(slots), 'ticks_per_picture':ticks, 'paced_to_original':pace_to_original,
              'pacing_max_lead_packets':max_lead_packets if pace_to_original else None,
              'stuffing_between_pictures':stuffing, 'unused_tail_bytes':tail,
              'max_packets_late':max(shift), 'max_packets_early':-min(shift),
              'types_new':''.join(u[2] for u in units[:19]), 'types_original':''.join(u[2] for u in old_units[:19])}
    return bytes(out), report


def main():
    original = open(sys.argv[1], 'rb').read(); es = open(sys.argv[2], 'rb').read()
    out, report = plan(original, es)
    assert len(out) == len(original)
    # Everything that is not video must be untouched.
    changed_outside = 0
    for at, sid, head, pay, plen, info in packets(original):
        if sid != 0xE0 and out[at:pay+plen] != original[at:pay+plen]: changed_outside += 1
    report['non_video_packets_changed'] = changed_outside
    print(report)
    if '--write' in sys.argv:
        open(sys.argv[3], 'wb').write(out); print('wrote', sys.argv[3])


if __name__ == '__main__': main()
