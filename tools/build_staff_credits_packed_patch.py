"""0.9.12: update the compressed credits scene used by the game.

0.9.11 changed plain resource 4350 only. A fresh-boot saved-state table
matched the original table in packed resource 701349 exactly. Keep the
unpacked scene/chunk extents and the packed archive allocation unchanged.
"""
import hashlib
import json
import struct
from build_ui_patch import ROOT, require, u32
from dialogue_corpus import archive, parse_table
from build_history_patch import chunks
from build_flight_save_patch import parts
from packed_resource import is_packed, pack, unpack
from ui_font import font_map
import build_stats_panel_patch as writer

VERSION = '0.9.12'
BASE = ROOT/'work/output/ACE3-English-0.9.11.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_HASH = 'b0a48f3d4f3b1c82c720cfdefe4bc54e599852f8e6e8b207b7658de0121bb8ee'
PLAIN, PACKED = 4350, 701349
FOLDER = ROOT/'work/ui/staff_credits_0912'


def stuf(scene):
    _,a,z = next(c for c in chunks(scene) if c[0] == b'STUF')
    return a,z,scene[a+16:z]


def plan():
    FOLDER.mkdir(parents=True,exist_ok=True)
    with BASE.open('rb') as f:
        fi,es = archive(f)
        def get(rid):
            _,n,o,_ = next(e for e in es if e[3] == rid)
            f.seek(fi['offset']+o); return fi['offset']+o,f.read(n)
        _,english = get(PLAIN); origin,source = get(PACKED)
        # Enumerate every archive header, not only plain searchable strings.
        # The packed twin retains the exact known scene extent.
        twins = []
        packed_headers = 0
        for _,n,o,rid in es:
            f.seek(fi['offset']+o); header = f.read(min(n,12))
            if is_packed(header):
                packed_headers += 1
                if struct.unpack_from('>I',header,4)[0] == len(english): twins.append(rid)
    require(twins == [PACKED], 'Credits packed-twin coverage changed')
    scene,used = unpack(source)
    require(not any(source[used:]), 'Unexpected packed tail')
    a,z,before = stuf(scene); ea,ez,after = stuf(english)
    require(chunks(scene) == chunks(english) and (a,z) == (ea,ez), 'Scene/chunk extent mismatch')
    p,q = parts(before),parts(after)
    require(set(p) == set(q), 'Credits resource IDs changed')
    changed = [rid for rid in p if p[rid] != q[rid]]
    require(changed == [1,2,3,107], 'Unexpected credits differences')
    # 107 is the closing story disclaimer, already translated in the plain
    # copy; all six other logo/image assets must remain byte-identical.
    for rid in p:
        if rid not in changed: require(p[rid] == q[rid], 'Unrelated logo/asset changed')
    rows = parse_table(q[3])[3]; oldrows = parse_table(p[3])[3]
    require([(s,t) for s,t,_,_ in rows] == [(s,t) for s,t,_,_ in oldrows], 'Row order/null slots changed')
    doc = json.loads((ROOT/'work/translation/en/staff_credits.json').read_text(encoding='utf-8'))
    require(hashlib.sha256(p[3]).hexdigest() == doc['source_table_sha256'], 'Packed source translation mismatch')
    by_id = {t:r for _,t,_,r in rows}
    for row in doc['rows']:
        raw = by_id[row['text_id']]
        if row['status'] == 'preserve_graphics_commands':
            require(hashlib.sha256(raw).hexdigest() == row['source_sha256'], 'Logo command changed')
        else:
            require(raw.isascii() and raw.endswith(row['target'].encode('ascii')), 'English target missing')
    mapping,_,_ = font_map(q[2])
    require(all(c in mapping for c in range(32,127)), 'Missing ASCII glyphs')
    new_scene = scene[:a+16]+after+scene[z:]
    require(len(new_scene) == len(scene) and chunks(new_scene) == chunks(scene), 'Unpacked extent changed')
    require(new_scene[:a+16] == scene[:a+16] and new_scene[z:] == scene[z:], 'Other scene chunks changed')
    encoded = pack(new_scene)
    require(len(encoded) <= len(source), 'Compressed credits no longer fit allocation')
    encoded += bytes(len(source)-len(encoded))
    decoded,end = unpack(encoded)
    require(decoded == new_scene and not any(encoded[end:]), 'Compressed round-trip mismatch')
    _,_,readback = stuf(decoded)
    require(readback == after, 'Decoded credits differ from translated donor')
    summary = dict(resource=PACKED,donor=PLAIN,changed_stuf_resources=changed,
        packed_headers_audited=packed_headers,matching_unpacked_size_resources=twins,
        old_packed_bytes=len(source),new_stream_bytes=end,allocation_bytes=len(encoded),
        unpacked_bytes=len(decoded),chunk_extents_preserved=True,
        decoded_scene_sha256=hashlib.sha256(decoded).hexdigest(),
        english_credit_rows=323,logo_command_rows=9,closing_disclaimer_english=True,
        font_sampling=3,compressed_round_trip_verified=True,
        all_other_scene_chunks_unchanged=True,runtime_verified=False,
        diagnosis='Fresh boot of 0.9.11 loaded the original packed credits table; old table exactly matched saved EE RAM at 0x01213360.')
    (FOLDER/'packed-layout.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    return [dict(offset=origin,before=source,after=encoded)],summary,None


if __name__ == '__main__':
    writer.VERSION,writer.BASE,writer.OUTPUT,writer.BASE_HASH = VERSION,BASE,OUTPUT,BASE_HASH
    writer.plan = plan
    writer.main()
