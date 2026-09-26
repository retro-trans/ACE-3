"""Print the released English speaker name for operator/speaker IDs (<operator(ID,n)> in meetings and demos).

usage: python tools/speaker_lookup.py <id> [<id> ...]      (no ids: print every speaker)
Reads the full-name table 3014 of menu bundle 4002050 and the short-label table 3021 of gameplay bundle 1200000
from the 0.1.27 build. Read-only.
"""
import sys
from build_ui_patch import ROOT
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    wanted = set(map(int, sys.argv[1:]))
    with (ROOT/'work/output/ACE3-English-0.1.27.iso').open('rb') as f:
        info, entries = archive(f)
        def table(rid, tid):
            entry = next(e for e in entries if e[3] == rid); f.seek(info['offset']+entry[2])
            return {i:r.decode('cp932') for _, i, _, r in parse_table(parts(f.read(entry[1]))[tid])[3]}
        full, short = table(4002050, 3014), table(1200000, 3021)
    for i in sorted(set(full) | set(short)):
        if not wanted or i in wanted: print(i, '| full:', full.get(i, '-'), '| short:', short.get(i, '-'))


if __name__ == '__main__': main()
