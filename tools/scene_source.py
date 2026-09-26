"""Print the text rows of meeting/briefing/story-demo scenes (4003xxx/4004xxx) to the console. Read-only.

usage: python tools/scene_source.py <resource id> [<resource id> ...] [--iso <name under work/output>]
Nothing is written to disk: the Japanese script stays on the user's disc. Each row prints as
  <table> <slot> <text id> <repr of text>
Slot 0 of a meeting/briefing table is the screen title. Commands in angle brackets must be kept, in order.
"""
import sys
from build_ui_patch import ROOT
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts


def scene_tables(data):
    out = {}
    for tid, chunk in parts(data).items():
        if tid > 1: continue
        try: out[tid] = parse_table(chunk)[3]
        except ValueError: continue
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    args = sys.argv[1:]; iso = ROOT/'work/output/ACE3-English-0.1.27.iso'
    if '--iso' in args:
        at = args.index('--iso'); iso = ROOT/'work/output'/args[at+1]; del args[at:at+2]
    with iso.open('rb') as f:
        info, entries = archive(f)
        for rid in map(int, args):
            entry = next(e for e in entries if e[3] == rid); f.seek(info['offset']+entry[2])
            print('== resource', rid)
            for tid, rows in scene_tables(f.read(entry[1])).items():
                for slot, text_id, _, raw in rows: print(tid, slot, text_id, repr(raw.decode('cp932')))


if __name__ == '__main__': main()
