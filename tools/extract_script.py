"""Export editable ACE3 table rows. Japanese is represented by hashes and null text. Dry-run first."""
import argparse
from pathlib import Path
from translation_tables import export_document, json_text, save_new


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('iso', type=Path); ap.add_argument('output', type=Path)
    ap.add_argument('--resource', action='append', type=int); ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    doc, counts = export_document(a.iso, set(a.resource) if a.resource else None)
    print(json_text({k: len(v) if isinstance(v, list) else v for k, v in counts.items()}))
    print('Samples:', ', '.join(r['id'] for r in doc['rows'][:3]))
    if not doc['rows']: ap.error('No supported text rows found')
    if a.write: save_new(a.output, json_text(doc))


if __name__ == '__main__': main()
