"""0.9.17: translate the active Extra Mission 3/4 text tables in place.

Dry-run by default. --write creates a separate test ISO and verifies every
byte against 0.9.16 plus the eight fixed-size table edits. Mission scripts,
resource offsets, text IDs, timing commands and fonts remain unchanged.
"""
import hashlib
import json
import struct

from build_ui_patch import ROOT, require, u32
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts
from build_combat_ui_patch import compact
from build_scene_patch import wrap_words
from build_dialogue_patch import TOKEN
from packed_resource import is_packed
from ui_font import measure_text
import build_stats_panel_patch as writer

VERSION = '0.9.17'
BASE = ROOT/'work/output/ACE3-English-0.9.16.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_HASH = 'b57fe1b77a041282e2a3b43ea068dab8008010ee5f85688c6a9c68e2a5d1998d'
INPUT = ROOT/'work/translation/en/extra_missions_0917.json'
LAYOUT = ROOT/'work/ui/extra_missions_0917/layout.json'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def copies(rid):
    return [rid-1996000, rid, rid+1198000, rid+1199000]


def plan():
    doc = json.loads(INPUT.read_text(encoding='utf-8'))
    require(doc['status'] == 'meaning_reviewed', 'Translation needs review')
    require([s['resource_id'] for s in doc['scenes']] == [2002442, 2002443], 'Unexpected mission coverage')
    require(sum(len(s['rows']) for s in doc['scenes']) == 51, 'Incomplete translation')
    changes, scenes, unchanged = [], [], []
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        by_id = {rid:(n,o) for _,n,o,rid in entries}

        def get(rid):
            n,o = by_id[rid]
            f.seek(fi['offset']+o)
            return fi['offset']+o,f.read(n)

        font = parts(get(1200000)[1])[2500]
        expected_sizes = set()
        for scene in doc['scenes']:
            rid = scene['resource_id']
            require(scene['copies'] == copies(rid), 'Unexpected copy IDs')
            translated = None
            instances = []
            for copy in scene['copies']:
                origin,data = get(copy)
                expected_sizes.add(len(data))
                at = u32(data,20)
                size,_,_,rows = parse_table(data,at)
                before = data[at:at+size]
                require(digest(before) == scene['source_table_sha256'], 'Source table changed')
                source = {tid:raw for _,tid,_,raw in rows}
                targets, report = {}, []
                for row in scene['rows']:
                    tid = row['text_id']
                    raw = source[tid]
                    require(digest(raw) == row['source_sha256'], 'Translation source mismatch')
                    target = row['target']
                    dialogue = b'<sp(' in raw
                    limit = 400 if dialogue else 480
                    if dialogue:
                        target = wrap_words(target,font,limit,4)
                    require(target.isascii(), 'Non-English target')
                    require(TOKEN.findall(raw.decode('cp932')) == TOKEN.findall(target), 'Timing/control change')
                    widths = measure_text(font,TOKEN.sub('',target))
                    require(max(widths) <= limit, 'Text exceeds display width')
                    require(dialogue or len(widths) == 1, 'HUD alert must stay on one line')
                    targets[tid] = target
                    report.append(dict(text_id=tid,target=target,widths=widths,limit=limit))
                after = compact(before,targets)
                require(len(after) == size, 'Table extent changed')
                oldrows = [(s,t) for s,t,_,_ in rows]
                newrows = parse_table(after)[3]
                require(oldrows == [(s,t) for s,t,_,_ in newrows], 'Slots changed')
                for _,tid,_,raw in newrows:
                    expected = targets[tid].encode('cp932') if tid in targets else source[tid]
                    require(raw == expected, 'Readback mismatch')
                    require(raw.isascii(), 'Japanese remains in an active row')
                if translated is None:
                    translated = after
                    scenes.append(dict(resource_id=rid,table_bytes=size,rows=report))
                else:
                    require(after == translated, 'Translated copies disagree')
                changes.append(dict(offset=origin+at,before=before,after=after))
                instances.append(dict(resource_id=copy,resource_bytes=len(data),table_offset=at,table_bytes=size))
            scenes[-1]['copies'] = instances

        # The first two Extra Missions use single-row objective tables, already
        # English. Check their active pointers rather than stale embedded text.
        for rid in (2002440,2002441):
            for copy in copies(rid):
                _,data = get(copy)
                rows = parse_table(data,u32(data,20))[3]
                require(len(rows) == 1 and rows[0][3] == b'Destroy all targets', 'Extra 1/2 objective changed')
                unchanged.append(copy)

        # Check every compressed header for an exact scene-size twin. This is
        # a bounded twin audit, not a claim about all unknown container formats.
        packed_count, packed_candidates, plain_candidates, matched_plain = 0, [], [], []
        table_hashes = {s['source_table_sha256'] for s in doc['scenes']}
        for _,n,o,rid in entries:
            f.seek(fi['offset']+o)
            header = f.read(min(n,12))
            # Text-only mission stubs share the magic but have a zero size at
            # offset 4; they are not compressed streams.
            if is_packed(header) and struct.unpack_from('>I',header,4)[0] > 0:
                packed_count += 1
                if struct.unpack_from('>I',header,4)[0] in expected_sizes:
                    packed_candidates.append(rid)
            elif n in expected_sizes:
                plain_candidates.append(rid)
                _,data = get(rid)
                try:
                    at = u32(data,20)
                    size = parse_table(data,at)[0]
                except (ValueError,struct.error,UnicodeError):
                    continue
                if digest(data[at:at+size]) in table_hashes:
                    matched_plain.append(rid)
        wanted = sorted(c for s in doc['scenes'] for c in s['copies'])
        require(sorted(matched_plain) == wanted, 'Additional same-size plain copies need review')
        require(not packed_candidates, 'Packed scene-size twin needs review')
    changes.sort(key=lambda c:c['offset'])
    require(len(changes) == 8, 'Unexpected table count')
    require(all(a['offset']+len(a['after']) <= b['offset'] for a,b in zip(changes,changes[1:])), 'Overlapping edits')
    summary = dict(scenes=scenes,unique_dialogue_rows=15,unique_hud_rows=36,
        translated_instances=204,extra_1_2_active_objectives_verified=unchanged,
        packed_headers_audited=packed_count,packed_size_candidates=packed_candidates,
        plain_size_candidates=plain_candidates,matching_plain_copies=matched_plain,
        fixed_table_extents=True,script_offsets_and_timing_unchanged=True,
        translation_sha256=digest(INPUT.read_bytes()),runtime_verified=False)
    LAYOUT.parent.mkdir(parents=True,exist_ok=True)
    LAYOUT.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    return changes,summary,None


if __name__ == '__main__':
    writer.VERSION,writer.BASE,writer.OUTPUT,writer.BASE_HASH = VERSION,BASE,OUTPUT,BASE_HASH
    writer.plan = plan
    writer.main()
