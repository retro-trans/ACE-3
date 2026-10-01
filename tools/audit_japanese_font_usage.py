"""Inventory remaining Japanese in supported text formats, without exporting it.

Structurally referenced does not imply player-visible: legacy and unclassified
mission variants remain in the archive. This is a translation worklist, not a
completion percentage or proof that Japanese font glyphs can all be removed.
"""
import collections
import json

from preview_hd_font import ROOT, BASE, OUT
from translation_tables import scan_iso, sha
from prototype_english_hd_font import JAPANESE
from dialogue_corpus import archive
from build_history_patch import chunks
from translation_tables import walk


def main():
    tables, counts = scan_iso(BASE)
    # Credits live in a chunked STUF container, outside the generic BND scan.
    # Follow the known ending resource explicitly rather than silently omitting it.
    with BASE.open('rb') as stream:
        fi, entries = archive(stream)
        entry = next(e for e in entries if e[3] == 4350)
        stream.seek(fi['offset']+entry[2]);data=stream.read(entry[1])
        _, start, end = next(c for c in chunks(data) if c[0] == b'STUF')
        for locator, offset, table in walk(data[start+16:end]):
            tables['4350:STUF/'+locator]=table
    rows=[]
    for key, table in tables.items():
        for _, tid, _, raw in table['rows']:
            if raw is None:
                continue
            matched=JAPANESE.findall(raw.decode('cp932'))
            if matched:
                rows.append(dict(table=key,text_id=tid,source_sha256=sha(raw),
                                 japanese_characters=len(matched)))
    folder=ROOT/'work/local/font-audit';folder.mkdir(parents=True,exist_ok=True)
    details=folder/'remaining-japanese-audit.json'
    details.write_text(json.dumps(dict(counts=counts,rows=rows),indent=2)+'\n',encoding='utf-8')
    summary=dict(base_version='0.9.6',
                 scope='BND text tables, structurally selected mission tables, and the ending staff-roll STUF table in resource 4350; excludes fixed parameter names, battle shouts, other chunked text, images and movies',
                 caveat='Includes legacy and unclassified resources; runtime reachability is not established. Unsupported candidates are not certified absent.',
                 resources_examined=counts['resources_examined'],tables_examined=counts['tables'],
                 rows_examined=counts['rows'],unsupported_candidates=len(counts['unsupported_containers']),
                 additional_credits_tables=1,additional_credits_nonnull_rows=sum(r[3] is not None for r in tables['4350:STUF/3']['rows']),
                 japanese_row_instances=len(rows),unique_japanese_rows=len({r['source_sha256'] for r in rows}),
                 japanese_rows_per_table=dict(collections.Counter(r['table'] for r in rows)),
                 details=str(details.relative_to(ROOT)).replace('\\','/'),
                 confirmed_categories=[
                     {'tables':['4350:STUF/3'],
                      'note':'Live staff roll: 333 nonempty rows, 315 contain Japanese. Uses its dedicated STUF font/texture (2/1), not the five main-font prototypes. Translate roles and verify romanized staff names before removing its Japanese glyphs.'},
                     {'tables':['4002050:3040','4002050:3072','4002054:3040','4002054:3072','4002057:3040','4002057:3072'],
                      'note':'Song-title rows were explicitly excluded by the earlier dialog builder; translate before removing their glyphs.'},
                     {'tables':['4002052:3024','4002053:3024'],
                      'note':'Three Type Change menu labels remain Japanese; review this menu and translate its text.'},
                     {'tables':['4002055:3055','4002055:3056','4002055:3057'],
                      'note':'Earlier builder documents these as legacy ACE2 mission tables; do not infer runtime use from their presence.'}])
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'remaining-japanese-audit.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:summary[k] for k in ('resources_examined','tables_examined','rows_examined',
                                           'japanese_row_instances','unique_japanese_rows','unsupported_candidates')},indent=2))


if __name__=='__main__':main()
