"""0.1.62: retain ending captions for 0.5 seconds after each line. Dry-run first."""
import argparse
import json
import struct
import sys

from build_ui_patch import ROOT, require, u32
from dialogue_corpus import archive
from build_history_patch import chunks
from build_flight_save_patch import parts
from build_credits_subtitles_patch import captions, MOTION_ID
import build_stats_panel_patch as writer

VERSION = '0.1.62'
BASE = ROOT/'work/output/ACE3-English-0.1.61.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_HASH = 'f572cf2cb5b3aa3977dcedd3e338a355f8cb5b86462f2aaa70bffb1ec5d70836'
HOLD_SECONDS = 0.5
TURNOVER_SECONDS = 2/60


def plan():
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        def get(rid):
            _, size, off, _ = next(e for e in entries if e[3] == rid)
            f.seek(fi['offset']+off)
            return fi['offset']+off, f.read(size)
        rows = captions(parts(get(1200000)[1])[2500])
        origin, data = get(MOTION_ID)
    by_id = {r['id']: r for r in rows}
    for track in ('dialogue', 'song'):
        seq = sorted((r for r in rows if r['track'] == track), key=lambda r: r['start'])
        for index, row in enumerate(seq):
            limit = seq[index+1]['start'] if index+1 < len(seq) else 350.
            row['next_start'] = limit
            row['display_end'] = min(row['end']+HOLD_SECONDS, limit-TURNOVER_SECONDS)
            require(row['display_end'] >= row['end']-TURNOVER_SECONDS-1e-6,
                    'Caption duration would be shortened')
    _, start, end = next(c for c in chunks(data) if c[0] == b'POLY')
    poly = data[start+16:end]
    edits, seen, report = [], set(), []
    for clip_id in range(7, 23):
        record = 0x50+(clip_id-1)*32
        require(u32(poly, record) == clip_id, 'Clip identity')
        off, size = u32(poly, record+12), u32(poly, record+16)
        clip = poly[off:off+size]
        for channel in range(u32(clip, 16)):
            at = u32(clip, 20)+channel*64
            if u32(clip, at+4) != 0x1000:
                continue
            for n in range(u32(clip, at+12) & 0xffff):
                key = u32(clip, at+16)+n*48
                if u32(clip, key+36) != 25:
                    continue
                payload = u32(clip, key+32)
                if u32(clip, payload) != 0:
                    continue
                rid = u32(clip, payload+4)
                if rid not in by_id:
                    continue
                require(rid not in seen, 'Duplicate caption event')
                seen.add(rid)
                row = by_id[rid]
                frame, old_duration = struct.unpack_from('<2f', clip, key)
                require(abs(frame/60+(clip_id-7)*20-row['start']) < 0.0001,
                        'Caption start preimage')
                require(abs(old_duration-((row['end']-row['start'])*60-2)) < 0.001,
                        'Caption duration preimage')
                new = struct.pack('<f', (row['display_end']-row['start'])*60)
                duration = struct.unpack('<f', new)[0]
                actual_end = row['start']+duration/60
                require(actual_end <= row['next_start']-TURNOVER_SECONDS+0.0001,
                        'Caption overlaps next event')
                require(abs(actual_end-row['display_end']) < 0.0001, 'Duration precision')
                before = clip[key+4:key+8]
                if before != new:
                    edits.append(dict(offset=origin+start+16+off+key+4, before=before, after=new))
                report.append(dict(id=rid, track=row['track'], text=row['text'],
                                   start=row['start'], previous_end=row['start']+old_duration/60,
                                   new_end=actual_end, source_end=row['end'],
                                   limited_by_next_line=row['display_end'] < row['end']+HOLD_SECONDS-1e-6))
    require(seen == set(by_id), 'Caption coverage')
    edits.sort(key=lambda c: c['offset'])
    require(all(a['offset']+4 <= b['offset'] for a,b in zip(edits,edits[1:])), 'Overlapping edits')
    report.sort(key=lambda r: r['id'])
    return edits, dict(resource=MOTION_ID, captions_checked=len(report), durations_changed=len(edits),
                       hold_seconds=HOLD_SECONDS, turnover_frames=2,
                       limited_by_next_line=sum(r['limited_by_next_line'] for r in report),
                       cues=report), None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    edits, report, _ = plan()
    print('DRY RUN: ending dialogue and lyric hold; starts, text and audio unchanged', flush=True)
    print(json.dumps(dict((k,v) for k,v in report.items() if k != 'cues'), indent=2))
    print(json.dumps(report['cues'][:4], indent=2), flush=True)
    if args.write:
        writer.VERSION, writer.BASE, writer.OUTPUT, writer.BASE_HASH = VERSION, BASE, OUTPUT, BASE_HASH
        writer.plan = lambda: (edits, report, None)
        sys.argv = [sys.argv[0], '--write']
        writer.main()


if __name__ == '__main__':
    main()
