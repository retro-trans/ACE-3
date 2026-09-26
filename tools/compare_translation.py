"""Build an offline Japanese/English review page from your original ACE3 ISO. Dry-run by default."""
import argparse
import gzip
import html
import json
from collections import Counter
from pathlib import Path
from translation_tables import ROOT, require, save_new, sha
from build_ui_patch import iso_files

CATALOG = ROOT/'work/translation/en/comparison_0.1.42.json.gz'
STATES = ('all', 'translated', 'untranslated', 'unchanged', 'no_match', 'needs_review')


def comparison_rows(iso, catalog, resource=None, only='all'):
    require(catalog.get('schema') == 'ace3-comparison-v1', 'Unsupported comparison catalog')
    require(Path(iso).suffix.lower() == '.iso', 'Use an unpacked .iso file')
    require(Path(iso).stat().st_size == catalog['source_size'], 'Expected the original Japanese ISO, not a patched ISO')
    rows = []
    with Path(iso).open('rb') as f:
        require('/SLPS_257.84' in iso_files(f), 'Expected ACE3 SLPS-25784')
        for row in catalog['rows']:
            if resource is not None and row['resource'] != resource: continue
            if only != 'all' and row['status'] != only: continue
            f.seek(row['source_offset']); raw = f.read(row['source_bytes'])
            require(sha(raw) == row['source_sha256'], 'Source mismatch at '+row['id'])
            rows.append({'id': row['id'], 'resource': row['resource'], 'status': row['status'],
                         'source': raw.decode('cp932'), 'target': row['target']})
    return rows


def render(rows, version):
    # Escape '<' even inside JSON: a game string must never close the script tag.
    payload = json.dumps(rows, ensure_ascii=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    return '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ACE3 translation review</title><style>
body{font:16px system-ui,sans-serif;background:#101923;color:#eef4fa;margin:0;padding:24px;max-width:1500px;margin:auto}
h1{margin:0 0 8px}p{line-height:1.5;color:#bdcedd}a{color:#84caff}
.controls{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0}label{display:flex;gap:6px;align-items:center}
input,select,button{font:inherit;padding:8px;border:1px solid #587084;border-radius:5px;background:#1d3041;color:white}
input{min-width:260px}button:disabled{opacity:.4}table{border-collapse:collapse;width:100%;table-layout:fixed}
th,td{padding:12px;text-align:left;vertical-align:top;border:1px solid #3c5060}th{background:#20374b}
th:first-child{width:19%}td{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.5}small{color:#bed5e5}
.pages{display:flex;gap:12px;align-items:center;margin:18px 0}#summary{min-height:24px}
@media(max-width:700px){body{padding:12px}th:first-child{width:24%}td,th{padding:7px;font-size:14px}}
</style><h1>Check the translation</h1><p>ACE3 English VERSION. Japanese is read from your own disc; English is the recorded release text.
Pairing uses resource, table and text IDs. “Translated” means changed text, not human approval.
Scope: supported BND and mission tables, including duplicate and legacy resources. Models/battle shouts, packed-only text,
fixed name fields, images and movies are excluded. This is not a whole-game completion count.</p>
<details><summary>What the statuses mean</summary><p>Translated: matched and changed to non-Japanese text.
Untranslated: matched Japanese text is unchanged. Unchanged: other matched text is unchanged.
No match: no corresponding target row; no translation conclusion can be drawn.
Needs review: changed target still contains Japanese; its target text is omitted from the catalog.</p></details>
<div class="controls"><label>Search <input id="search" aria-label="Search" placeholder="Japanese, English or row ID"></label>
<label>Status <select id="state" aria-label="Status"><option value="all">All statuses</option></select></label>
<label>Resource <select id="resource" aria-label="Resource"><option value="all">All resources</option></select></label>
<label><input type="checkbox" id="codes" style="min-width:0"> Show control codes</label></div>
<div id="summary" aria-live="polite"></div><div class="pages"><button id="prev">Previous</button><span id="page"></span><button id="next">Next</button></div>
<table><thead><tr><th>Location / status</th><th>Japanese source</th><th>Release text</th></tr></thead><tbody id="rows"></tbody></table>
<script id="data" type="application/json">PAYLOAD</script><script>
const data=JSON.parse(document.getElementById('data').textContent), $=id=>document.getElementById(id);
for(const s of ['translated','untranslated','unchanged','no_match','needs_review']){let o=document.createElement('option');o.value=s;o.textContent=s.replaceAll('_',' ');$('state').append(o)}
for(const r of [...new Set(data.map(x=>x.resource))].sort((a,b)=>a-b)){let o=document.createElement('option');o.value=r;o.textContent=r;$('resource').append(o)}
let page=0, filtered=data;const size=100;
function display(text){return $('codes').checked?text:text.replace(/<[^<>]*>|#[a-z](?:\\[[^\\]]*\\])?/g,'')}
function show(){const total=Math.ceil(filtered.length/size);page=Math.max(0,Math.min(page,total-1));$('rows').replaceChildren();
for(const r of filtered.slice(page*size,(page+1)*size)){let tr=document.createElement('tr');
let target=r.target;if(target===null)target=r.status==='untranslated'?'Unchanged from Japanese source':r.status==='no_match'?'No confident match':'Target contains Japanese; inspect the translated disc';
for(const text of [r.id+'\\n'+r.status.replaceAll('_',' '),display(r.source),display(target)]){let td=document.createElement('td');td.textContent=text;tr.append(td)}$('rows').append(tr)}
$('summary').textContent=filtered.length.toLocaleString()+' of '+data.length.toLocaleString()+' row instances';$('page').textContent=total?'Page '+(page+1)+' of '+total:'No matches';$('prev').disabled=page===0;$('next').disabled=page+1>=total;}
function filter(){const q=$('search').value.toLocaleLowerCase(),s=$('state').value,r=$('resource').value;
filtered=data.filter(x=>(s==='all'||x.status===s)&&(r==='all'||String(x.resource)===r)&&(!q||(x.id+' '+x.source+' '+(x.target||'')).toLocaleLowerCase().includes(q)));page=0;show()}
$('search').addEventListener('input',filter);$('state').addEventListener('change',filter);$('resource').addEventListener('change',filter);
$('codes').addEventListener('change',show);
$('prev').onclick=()=>{page--;show()};$('next').onclick=()=>{page++;show()};show();
</script></html>'''.replace('VERSION', html.escape(version)).replace('PAYLOAD', payload)


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('iso', type=Path)
    ap.add_argument('--catalog', type=Path, default=CATALOG); ap.add_argument('--resource', '--rec', type=int)
    ap.add_argument('--only', choices=STATES, default='all')
    ap.add_argument('--output', type=Path, default=ROOT/'work/local/translation-review.html')
    ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    with gzip.open(a.catalog, 'rt', encoding='utf-8') as f: catalog = json.load(f)
    rows = comparison_rows(a.iso, catalog, a.resource, a.only)
    print(json.dumps({'snapshot': catalog['version'], 'rows': len(rows), 'statuses': dict(Counter(r['status'] for r in rows)),
                      'output': str(a.output), 'samples': [r['id'] for r in rows[:3]]}, indent=2))
    require(rows, 'No rows matched the selected filters')
    if a.write: save_new(a.output, render(rows, catalog['version']))


if __name__ == '__main__': main()
