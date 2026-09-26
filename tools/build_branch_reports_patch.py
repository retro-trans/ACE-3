"""0.1.45: translate every remaining Japanese branching Situation Report.

Read-only audit by default. --write rebuilds a local test image and verifies
every archive payload and disc file, then audits the finished active tables.
Japanese source text is read from the user's image and never exported.
"""
import argparse
import hashlib
import json
import re
from build_ui_patch import ROOT, require, u32
from build_flight_save_patch import parts
from build_intermission_patch import replace_rows
from build_028_patch import rebuild_scene_bundle, wrap_words_soft
from dialogue_corpus import archive, parse_table
from ui_font import measure_text
import build_dialogue_patch as builder

VERSION = '0.1.45'
BASE = ROOT/'work/output/ACE3-English-0.1.44.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
INPUT = ROOT/'work/translation/en/branch_reports_045.json'
TAG = re.compile(r'<[^>]*>')
JAPANESE = re.compile(r'[\u3040-\u30ff\u4e00-\u9fff]')
PREFIX = re.compile(r'^(?:<(?:library|operator|speed|topic|thumbdown)\([^>]*\)>)*')
WIDTH, LINES, CHARS = 460, 3, 128
# The mission set already inserted by build_wave_patch and the earlier scene
# builders. Neighboring numeric IDs also contain previous-game material;
# numeric proximity alone does not establish runtime use.
MISSION_SCENES = set(range(2002010, 2002351, 10)) | {2002011, 2002021, 2002031, 2002311, 2002410}


def window_tables(data):
    if data[:4] != b'BND\0':
        return {}
    tables = {}
    for tid, raw in parts(data).items():
        try:
            tables[tid] = parse_table(raw)[3]
        except (ValueError, UnicodeError):
            pass
    return tables


def audit(path, replacements=None):
    """Audit active BND window tables, not obsolete appended string pools.

    Separately check the active main-mission tables (including route A/B).
    Legacy ACE2 scenes, battle shouts and baked image captions are outside
    this dialogue audit and are not claimed to be newly translated.
    """
    replacements = replacements or {}
    out = dict(window_resources=0, window_tables=0, window_rows=0,
               mission_resources=0, mission_dialogue_rows=0,
               japanese_window_rows=[], japanese_mission_rows=[])
    with path.open('rb') as f:
        fi, entries = archive(f)
        for _, size, offset, rid in entries:
            if not (4003000 <= rid < 4005000 or rid in MISSION_SCENES):
                continue
            f.seek(fi['offset']+offset)
            data = replacements.get(rid)
            if data is None:
                data = f.read(size)
            if rid >= 4003000:
                tables = window_tables(data)
                if tables:
                    out['window_resources'] += 1
                for tid, rows in tables.items():
                    out['window_tables'] += 1
                    for slot, text_id, _, raw in rows:
                        out['window_rows'] += 1
                        if JAPANESE.search(raw.decode('cp932')):
                            out['japanese_window_rows'].append([rid, tid, slot, text_id])
            else:
                try:
                    rows = parse_table(data, u32(data, 20))[3]
                except (ValueError, UnicodeError):
                    continue
                out['mission_resources'] += 1
                for slot, text_id, _, raw in rows:
                    if b'<sp(' not in raw:
                        continue
                    out['mission_dialogue_rows'] += 1
                    if JAPANESE.search(raw.decode('cp932')):
                        out['japanese_mission_rows'].append([rid, slot, text_id])
    return out


def plan():
    doc = json.loads(INPUT.read_text(encoding='utf-8'))
    require(doc['status'] == 'meaning_reviewed', 'Unreviewed dialogue')
    before_audit = audit(BASE)
    expected_rids = {int(k) for k in doc['scenes']}
    require({r[0] for r in before_audit['japanese_window_rows']} == expected_rids, 'Untranslated scene inventory changed')
    require(len(before_audit['japanese_window_rows']) == 141, 'Unexpected Japanese row count')
    changes, reports = {}, []
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        def get(rid):
            _, size, offset, _ = next(e for e in entries if e[3] == rid)
            f.seek(fi['offset']+offset)
            return f.read(size)
        fonts = [parts(get(rid))[2500] for rid in (4002050, 4002054, 4002057)]
        for rid in sorted(expected_rids):
            before = get(rid)
            p = parts(before)
            tables = window_tables(before)
            require(set(tables) == {1}, 'Unexpected report table set')
            rows = tables[1]
            drafts = doc['scenes'][str(rid)]
            require(len(rows) == len(drafts), 'Incomplete report')
            mappings, rr = {}, []
            for (slot, text_id, _, raw), body in zip(rows, drafts):
                source = raw.decode('cp932')
                prefix = PREFIX.match(source).group()
                target = prefix+body
                require(TAG.findall(source) == TAG.findall(target), 'Scene cues/links changed: %s/%s' % (rid, text_id))
                require(not JAPANESE.search(target), 'Untranslated draft')
                is_body = '<operator(' in target
                if is_body:
                    target = wrap_words_soft(target, fonts[0], WIDTH, LINES)
                    require(len(TAG.sub('', target)) <= CHARS, 'Text character capacity exceeded')
                else:
                    require('\n' not in target, 'Topic title split')
                widths = [max(measure_text(font, TAG.sub('', target))) for font in fonts]
                if is_body and max(widths) > WIDTH:
                    target = wrap_words_soft(prefix+body, fonts[0], WIDTH-10, LINES)
                    require(len(TAG.sub('', target)) <= CHARS, 'Text character capacity exceeded')
                    widths = [max(measure_text(font, TAG.sub('', target))) for font in fonts]
                require(max(widths) <= (WIDTH if is_body else 420), 'Text too wide: %s/%s %s' % (rid, text_id, widths))
                require(TAG.findall(source) == TAG.findall(target), 'Reflow changed cues')
                for linked in re.findall(r'<book\([^>]+>.*?<endbook\(\)>', target, re.S):
                    require('\n' not in linked, 'Glossary link split across lines')
                if target != source:
                    mappings[slot] = (source, target)
                rr.append(dict(slot=slot, text_id=text_id, source_sha256=hashlib.sha256(raw).hexdigest(),
                               target=target, role='body' if is_body else 'title',
                               lines=len(target.split('\n')), max_width=max(widths)))
            table = replace_rows(p[1], mappings)
            after = rebuild_scene_bundle(before, {1: table})
            ap = parts(after)
            require(all(v == ap[k] for k, v in p.items() if k != 1), 'Unrelated scene resource changed')
            require([(s, t, raw.decode('cp932')) for s, t, _, raw in parse_table(ap[1])[3]] ==
                    [(r['slot'], r['text_id'], r['target']) for r in rr], 'Finished table mismatch')
            require(parse_table(p[1])[2] == parse_table(ap[1])[2], 'Sparse slot count changed')
            changes[rid] = after
            reports.append(dict(resource_id=rid, source_sha256=hashlib.sha256(before).hexdigest(),
                                changed_rows=len(mappings), rows=rr))
    after_audit = audit(BASE, changes)
    require(not after_audit['japanese_window_rows'], 'Japanese remains in active window tables')
    require(not after_audit['japanese_mission_rows'], 'Japanese remains in live mission dialogue')
    return changes, reports, dict(before=before_audit, after=after_audit)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    changes, reports, coverage = plan()
    print('DRY RUN:', len(changes), 'reports;', sum(r['changed_rows'] for r in reports), 'updated rows (141 Japanese + D.O.M.E. title)', flush=True)
    print(json.dumps(coverage['after'], indent=2), flush=True)
    print(json.dumps(reports[0]['rows'][:3], indent=2), flush=True)
    if not args.write:
        return
    builder.VERSION, builder.BASE, builder.OUTPUT = VERSION, BASE, OUTPUT
    builder.build(changes, reports)
    with OUTPUT.open('rb') as f:
        fi, entries = archive(f)
        for rid, expected in changes.items():
            _, size, off, _ = next(e for e in entries if e[3] == rid)
            f.seek(fi['offset']+off)
            require(f.read(size) == expected, 'Finished-disc report mismatch')
    actual_audit = audit(OUTPUT)
    require(actual_audit == coverage['after'], 'Finished-disc audit differs')
    path = OUTPUT.with_suffix('.json')
    report = json.loads(path.read_text(encoding='utf-8'))
    report['coverage'] = coverage
    report['checks'] = dict(finished_disc_reports_match=True, branch_reports=16,
                           translated_rows=141, reviewed_rows=142, runtime_verified=False)
    report['translation_input_sha256'] = hashlib.sha256(INPUT.read_bytes()).hexdigest()
    path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('VERIFIED', OUTPUT, report['sha256'], flush=True)


if __name__ == '__main__':
    main()
