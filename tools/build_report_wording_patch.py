"""0.9.5: apply the user's 'at us' correction to Hayato's Situation Report."""
import json
from build_ui_patch import ROOT, require, inner_bnd, u32
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts
from ui_font import measure_text
import build_dialogue_patch as dialogue
import build_stats_panel_patch as writer

VERSION = '0.9.5'
BASE = ROOT/'work/output/ACE3-English-0.9.4.iso'
BASE_HASH = '8e0aae322dd12f3fe202e4e2784a1c671189a07f1a985be05fcbc67852a3afd5'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
TRANSLATION = ROOT/'work/translation/en/branch_reports_045.json'


def plan():
    draft = json.loads(TRANSLATION.read_text(encoding='utf-8'))['scenes']['4004072'][9]
    require(draft.endswith(' at us.'), 'Corrected translation changed')
    edits, reports = [], []
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        fonts = []
        for rid in (4002050, 4002054, 4002057):
            e = next(e for e in entries if e[3] == rid)
            f.seek(fi['offset']+e[2])
            fonts.append(parts(f.read(e[1]))[2500])
        for _, size, off, rid in entries:
            if not 4003000 <= rid < 4005000:
                continue
            f.seek(fi['offset']+off)
            data = f.read(size)
            if data[:4] != b'BND\0' or b'at Earth.' not in data:
                continue
            p = parts(data)
            spans = {k: a for k, a, _ in inner_bnd(data[:u32(data, 4)])}
            for table_id, table in p.items():
                try:
                    rows = parse_table(table)[3]
                except ValueError:
                    continue
                for slot, tid, ptr, raw in rows:
                    if b'Fearing ' not in raw or not raw.endswith(b' at Earth.'):
                        continue
                    require(rid == 4004072 and table_id == 1, 'Unexpected matching report')
                    old = raw.decode('cp932')
                    target = old[:-len('Earth.')]+ 'us.'
                    # Retain existing line breaks, commands, links and picture cue.
                    require(dialogue.TOKEN.findall(target) == dialogue.TOKEN.findall(old), 'Control code changed')
                    start = target.index('Fearing ')
                    require(target[start:].split() == draft.split(), 'Source draft differs from game wording')
                    widths = [measure_text(font, dialogue.TOKEN.sub('', target)) for font in fonts]
                    require(max(max(ws) for ws in widths) <= 460 and len(target.split('\n')) <= 3, 'Report no longer fits')
                    replacement = target.encode('cp932')+b'\0'
                    replacement += bytes(len(raw)+1-len(replacement))
                    before = raw+b'\0'
                    changed = table[:ptr]+replacement+table[ptr+len(before):]
                    expected = [(s, i, at, target.encode('cp932') if s == slot else r) for s, i, at, r in rows]
                    require(parse_table(changed)[3] == expected, 'Other table row or pointer changed')
                    edits.append(dict(offset=fi['offset']+off+spans[table_id]+ptr, before=before, after=replacement))
                    reports.append(dict(resource_id=rid, table_id=table_id, text_id=tid, slot=slot,
                        target=target, line_widths=widths, pointers_preserved=True))
    require(len(edits) == 1, 'Expected exactly one active matching report row')
    return edits, dict(corrections=reports, runtime_verified=False), None


if __name__ == '__main__':
    writer.VERSION, writer.BASE, writer.OUTPUT, writer.BASE_HASH = VERSION, BASE, OUTPUT, BASE_HASH
    writer.plan = plan
    writer.main()
