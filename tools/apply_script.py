"""Apply an edited export to a NEW ISO, inside existing table extents. Dry-run by default."""
import argparse
import json
import re
import sys
from pathlib import Path
from translation_tables import ROOT, json_text, plan_edits, require, save_new, write_copy


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('iso', type=Path); ap.add_argument('script', type=Path)
    ap.add_argument('--version', required=True); ap.add_argument('--output', type=Path); ap.add_argument('--write', action='store_true')
    a = ap.parse_args(); require(re.fullmatch(r'0\.\d+\.\d+', a.version), 'Use a version such as 0.1.43')
    output = a.output or ROOT/('work/output/ACE3-English-'+a.version+'-local.iso')
    require(output.suffix.lower() == '.iso', 'Output must be an ISO')
    doc = json.loads(a.script.read_text(encoding='utf-8')); patches = plan_edits(a.iso, doc)
    summary = {'version': a.version, 'source': a.iso.name, 'output': str(output),
               'changed_tables': len(patches), 'changed_rows': sum(len(p['rows']) for p in patches),
               'changes': [{'table': p['table'], 'text_ids': list(p['rows']), 'targets': list(p['rows'].values())} for p in patches]}
    print(json_text(summary))
    if not patches:
        print('No changes; no output is written.'); return
    print('Only the listed resource copies change. Check other menu/mission copies separately. Rendering needs an in-game check.')
    if a.write:
        summary.update(write_copy(a.iso, output, patches))
        save_new(output.with_suffix('.json'), json_text(summary))
        print('Verified output SHA-256:', summary['sha256'])


if __name__ == '__main__': main()
