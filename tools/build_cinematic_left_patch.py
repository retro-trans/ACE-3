"""0.9.14: shift native cinematic speaker/body text 90 units left.

Dry-run by default; --write makes a local test ISO and verifies every byte.
Only the two signed X coordinates change, in the standalone configuration
and its embedded copy. No executable, dialogue, movie or font changes.
"""
import hashlib
import json
import struct

from build_ui_patch import ROOT, require, u32, iso_files
from dialogue_corpus import archive
from build_flight_save_patch import parts
from build_stats_panel_patch import ranges
from packed_resource import is_packed
import build_stats_panel_patch as writer

VERSION = '0.9.14'
BASE = ROOT/'work/output/ACE3-English-0.9.13.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_HASH = 'cb62b115d750ba4fa534c3e69e6979c37452fd67c1048e99c337a174726c659c'
CONFIG_HASH = '80fc3c3d6c65991855d08be4d35d34e80c50b5a4d5080f45f3f9ffd1b49ece42'
FOLDER = ROOT/'work/ui/cinematic_left_0914'
SHIFT = -90
SOURCE_COORDINATES = [(0,'speaker',(-200,145)),(1,'dialogue',(-184,165))]
SPEAKER_MARGIN = 30
TOTAL_SHIFT = -90


def plan():
    edits, copies = [], []
    with BASE.open('rb') as f:
        fi, entries = archive(f)
        def get(rid):
            _, size, off, _ = next(e for e in entries if e[3] == rid)
            f.seek(fi['offset']+off)
            return f.read(size)
        config = get(102006)
        require(hashlib.sha256(config).hexdigest() == CONFIG_HASH, 'Cinematic config preimage')
        parameter = parts(config)[1]
        require((u32(parameter,0),u32(parameter,8),u32(parameter,12)) == (80,2,16), 'Coordinate table header')
        local, _ = ranges(config)[1]
        coordinates = []
        for index, role, expected in SOURCE_COORDINATES:
            at = 16+32*index
            require(struct.unpack_from('<3h',parameter,at) == (2,)+expected, 'Coordinate record')
            coordinates.append(dict(role=role,offset=local+at+2,
                old_x=expected[0],new_x=expected[0]+SHIFT,y=expected[1],
                old_screen_x=320+expected[0],new_screen_x=320+expected[0]+SHIFT))
        require(coordinates[1]['new_screen_x']-coordinates[0]['new_screen_x'] == 16, 'Indent changed')
        require(coordinates[0]['new_screen_x'] == SPEAKER_MARGIN, 'Left safety margin')

        # Verify the native cinematic draw path still takes its X/Y values
        # from these two 32-byte records, rather than a portrait UI layout.
        elf = iso_files(f)['/SLPS_257.84']
        for va, word in [(0x233d40,0x86440002),(0x233d48,0x86450004),
                         (0x233d8c,0x86440022),(0x233d94,0x86450024)]:
            f.seek(elf['offset']+va-0xfff80)
            require(f.read(4) == struct.pack('<I',word), 'Cinematic renderer changed')

        # Search every plain payload, including large containers, with bounded
        # memory. Check packed headers for standalone/container-sized twins.
        packed_count, packed_candidates = 0, []
        needle = parameter[16:80]
        for _, size, off, rid in entries:
            origin = fi['offset']+off
            f.seek(origin); header = f.read(min(size,12))
            if is_packed(header):
                packed_count += 1
                if struct.unpack_from('>I',header,4)[0] in (len(config),2350080):
                    packed_candidates.append(rid)
                continue
            cursor, tail = 0, b''
            while cursor < size:
                f.seek(origin+cursor)
                block = f.read(min(8<<20,size-cursor))
                data = tail+block
                start, pos = cursor-len(tail), 0
                while True:
                    pos = data.find(needle,pos)
                    if pos < 0: break
                    config_at = start+pos-(local+16)
                    f.seek(origin+config_at)
                    require(f.read(len(config)) == config, 'Unexpected coordinate-table copy')
                    copies.append(dict(resource_id=rid,config_offset=config_at))
                    for row in coordinates:
                        edits.append(dict(offset=origin+config_at+row['offset'],
                            before=struct.pack('<h',row['old_x']),after=struct.pack('<h',row['new_x'])))
                    pos += len(needle)
                cursor += len(block)
                tail = data[-(len(needle)-1):]
        require(copies == [dict(resource_id=102006,config_offset=0),
                           dict(resource_id=103000,config_offset=0x102000)], 'Cinematic copy inventory changed')
        require(not packed_candidates, 'Packed cinematic copies need investigation')
    edits.sort(key=lambda e:e['offset'])
    require(len(edits) == 4 and all(len(e['before']) == len(e['after']) == 2 for e in edits), 'Patch size')
    require(all(a['offset']+2 <= b['offset'] for a,b in zip(edits,edits[1:])), 'Overlapping edits')
    summary = dict(version=VERSION,shift_x=SHIFT,total_shift_from_original=TOTAL_SHIFT,coordinates=coordinates,copies=copies,
        coordinate_table_resource=1,config_sha256=CONFIG_HASH,
        plain_archive_payloads_scanned=len(entries)-packed_count,packed_headers_audited=packed_count,
        packed_matching_extent_candidates=packed_candidates,changed_coordinate_fields=4,
        preserve=['vertical positions','16-unit dialogue indent','line breaks','font',
                  'timing','portrait dialogue layouts','movies','credits and lyrics'],
        renderer='0x233c50: speaker X/Y at record +2/+4, dialogue X/Y at +0x22/+0x24; centered native X plus 320',
        runtime_verified=False)
    FOLDER.mkdir(parents=True,exist_ok=True)
    (FOLDER/'layout.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    return edits,summary,None


if __name__ == '__main__':
    writer.VERSION,writer.BASE,writer.OUTPUT,writer.BASE_HASH = VERSION,BASE,OUTPUT,BASE_HASH
    writer.plan = plan
    writer.main()
