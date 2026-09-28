"""0.1.51: unscaled Controls captions and full-width choice text boxes.

Dry run by default. --write builds and byte-verifies a local test ISO.
"""
from build_game_column_patch import ROOT, ranges, widen, parts, archive, parse_table, require
import build_stats_panel_patch as writer

VERSION = '0.1.51'
BASE = ROOT/'work/output/ACE3-English-0.1.50.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_SHA = '93cc89c3e958fc6e751e29c4f6e6e6e4ebfe6e68a1980632edc5087052b203c0'
CONFIG = dict(
    count=60, labels=(3, 11, 23, 31, 41, 49, 52),
    choices=tuple(n for lo, hi in ((4, 9), (12, 21), (24, 29), (32, 39), (42, 47)) for n in range(lo, hi)),
    grow=36, box_width=192, panel_node=32, expand_value_boxes=True,
    value_ids={120: 14, 121: 15, 122: 17, 123: 18, 124: 19, 125: 20,
               126: 22, 127: 23, 128: 25, 129: 26, 130: 27, 131: 29, 132: 30})


def plan():
    edits, reports = [], []
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        for rid in (4002050, 4002054, 4002057):
            _, size, off, _ = next(e for e in entries if e[3] == rid)
            f.seek(fi['offset']+off)
            bundle = f.read(size)
            p = parts(bundle)
            rows = {tid: raw.decode('cp932') for _, tid, _, raw in parse_table(p[3071])[3]}
            require([rows[x] for x in (5, 8, 10, 11)] ==
                    ['Control Scheme', 'Camera Movement', 'Button Mapping', 'Restore Defaults'], 'Caption preimage')
            before = parts(p[43])[0]
            after, report = widen(before, rows, p[2500], CONFIG)
            require(len(before) == len(after), 'Layout extent changed')
            edits.append(dict(offset=fi['offset']+off+ranges(bundle)[43][0]+ranges(p[43])[0][0],
                              before=before, after=after))
            reports.append(dict(bundle=rid, layout=43, **report))
    return edits, dict(panels=reports, runtime_verified=False), None


if __name__ == '__main__':
    writer.VERSION, writer.BASE, writer.OUTPUT, writer.BASE_HASH = VERSION, BASE, OUTPUT, BASE_SHA
    writer.plan = plan
    writer.main()
