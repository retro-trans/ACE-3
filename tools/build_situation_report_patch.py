"""0.1.42: user-requested Situation Report title. Read-only unless --write."""
import argparse
import json
from build_ui_patch import ROOT, require
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts
from build_intermission_patch import replace_rows
from ui_font import measure_text
import build_dialogue_patch as builder

VERSION = '0.1.42'
BASE = ROOT/'work/output/ACE3-English-0.1.41.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
INPUT = ROOT/'work/translation/en/situation_report_042.json'


def plan():
    spec = json.loads(INPUT.read_text(encoding='utf-8'))
    changes, reports = {}, []
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        for rid in spec['bundles']:
            _, size, off, _ = next(e for e in entries if e[3] == rid)
            f.seek(fi['offset']+off); old = f.read(size); resources = parts(old)
            rows = parse_table(resources[spec['table_id']])[3]
            hits = [(slot, tid, raw) for slot, tid, _, raw in rows if raw.decode('cp932') == spec['before']]
            require(hits == [(spec['slot'], spec['text_id'], spec['before'].encode('cp932'))], 'Title preimage changed')
            before_width = max(measure_text(resources[2500], spec['before']))
            width = max(measure_text(resources[2500], spec['target']))
            require(width <= before_width and len(spec['target']) <= len(spec['before']), 'Replacement exceeds existing title')
            table = replace_rows(resources[spec['table_id']], {spec['slot']: (spec['before'], spec['target'])})
            updated = builder.rebuild_bundle(old, {spec['table_id']: table})
            after = parts(updated)
            require(all(after[k] == v for k, v in resources.items() if k != spec['table_id']), 'Unrelated resource changed')
            expected = [(s, i, spec['target'].encode('cp932') if s == spec['slot'] else r) for s, i, _, r in rows]
            require([(s, i, r) for s, i, _, r in parse_table(after[spec['table_id']])[3]] == expected, 'Unselected title row changed')
            changes[rid] = updated
            reports.append({'resource_id': rid, 'table_id': spec['table_id'], 'text_id': spec['text_id'],
                            'before': spec['before'], 'target': spec['target'], 'old_width': before_width, 'new_width': width})
    return changes, reports


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--write', action='store_true'); args = ap.parse_args()
    changes, reports = plan()
    print('DRY RUN', json.dumps(reports, indent=2), flush=True)
    if not args.write:
        return
    builder.VERSION, builder.BASE, builder.OUTPUT = VERSION, BASE, OUTPUT
    builder.build(changes, reports)
    # Read the finished ISO, rather than only trusting planned bundle bytes.
    with OUTPUT.open('rb') as f:
        fi, entries = archive(f)
        for rid, expected in changes.items():
            _, size, off, _ = next(e for e in entries if e[3] == rid)
            f.seek(fi['offset']+off)
            require(f.read(size) == expected, 'Finished-disc bundle differs')
    path = OUTPUT.with_suffix('.json'); doc = json.loads(path.read_text(encoding='utf-8'))
    doc['coverage'] = 'Situation Archive renamed to Situation Report in all three shared title copies.'
    doc['checks'] = {'title_copies': 3, 'finished_disc_bundles_match': True, 'no_width_or_capacity_growth': True}
    path.write_text(json.dumps(doc, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
