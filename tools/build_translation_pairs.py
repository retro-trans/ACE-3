"""Maintainer: pair supported original/release tables by resource, BND path and text ID."""
import argparse
import gzip
import json
from pathlib import Path
from translation_tables import JP, ROOT, row_key, scan_iso, sha

DEFAULT = ROOT/'work/translation/en/comparison_0.1.42.json.gz'


def pair(original, translated, version):
    left, lc = scan_iso(original); right, rc = scan_iso(translated)
    rows = []
    for key, table in sorted(left.items()):
        target = {tid: raw for _, tid, _, raw in right.get(key, {}).get('rows', [])}
        for _, tid, ptr, raw in table['rows']:
            if raw is None: continue
            other = target.get(tid); text = raw.decode('cp932')
            if other is None: status = 'no_match'
            elif other == raw: status = 'untranslated' if JP.search(text) else 'unchanged'
            elif JP.search(other.decode('cp932')): status = 'needs_review'
            else: status = 'translated'
            # No Japanese corpus is checked in, including untranslated target rows.
            english = other.decode('cp932') if other is not None and not JP.search(other.decode('cp932')) else None
            rows.append({'id': row_key(key, tid), 'resource': table['resource'],
                         'source_offset': table['offset']+ptr, 'source_bytes': len(raw),
                         'source_sha256': sha(raw), 'target': english, 'status': status})
    return {'schema': 'ace3-comparison-v1', 'version': version, 'source_size': Path(original).stat().st_size,
            'pairing': 'resource + structural table path + text ID; no offset guesses',
            'source_scan': lc, 'translation_scan': rc, 'rows': rows}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('original', type=Path); ap.add_argument('translated', type=Path)
    ap.add_argument('--version', required=True); ap.add_argument('--output', type=Path, default=DEFAULT)
    ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    doc = pair(a.original, a.translated, a.version)
    from collections import Counter
    print(json.dumps({'rows': len(doc['rows']), 'statuses': dict(Counter(r['status'] for r in doc['rows'])),
                      'output': str(a.output), 'samples': [r['id'] for r in doc['rows'][:3]]}, indent=2))
    if a.write:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        with a.output.open('xb') as f:
            with gzip.GzipFile(filename='', fileobj=f, mode='wb', mtime=0) as zipped:
                zipped.write(json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))


if __name__ == '__main__': main()
