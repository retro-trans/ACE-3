"""Print Encyclopedia entries from the user's ISO to the console. Read-only; never writes Japanese to disk.

usage: python encyclopedia_source.py [first_id] [last_id]
Table 3018 holds the 88 term names and table 3019 the entry bodies (menu bundle 4002050).
"""
import json
import sys
from build_ui_patch import ROOT
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts


def entries():
    with next(ROOT.glob('*.iso')).open('rb') as f:
        fi, es = archive(f); _, sz, off, _ = next(e for e in es if e[3] == 4002050)
        f.seek(fi['offset']+off); p = parts(f.read(sz))
    names = {i:r.decode('cp932') for _, i, _, r in parse_table(p[3018])[3]}
    bodies = {i:r.decode('cp932') for _, i, _, r in parse_table(p[3019])[3]}
    return names, bodies


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    first, last = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (1, 88)
    names, bodies = entries()
    print('ALL TERM NAMES:', json.dumps(names, ensure_ascii=False))
    for i in range(first, last+1):
        print(json.dumps({'id':i, 'name':names[i], 'body':bodies[i]}, ensure_ascii=False))


if __name__ == '__main__': main()
