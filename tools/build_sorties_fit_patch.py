"""0.9.18: use a standard caption cell for the overlapping sortie label."""
import json
import struct
from build_ui_patch import ROOT, require, patch_table
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts
from build_briefing_banner_patch import spans
from ui_font import measure_text
import build_stats_panel_patch as writer

VERSION = '0.9.18'
BASE = ROOT/'work/output/ACE3-English-0.9.17.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_HASH = '0a50626f430844498290a3b73d934ad91965c92a0667876623202ac85abd47a9'
FOLDER = ROOT/'work/ui/sorties_0918'


def plan():
    with BASE.open('rb') as f:
        fi,es = archive(f)
        _,n,o,_ = next(e for e in es if e[3] == 4002053)
        origin = fi['offset']+o
        f.seek(origin);data = f.read(n)
    p = parts(data)
    before = parts(p[21])[0]
    after = bytearray(before)
    dst,donor,counter = (80+i*112 for i in (6,8,7))
    require(before[dst+85] == before[donor+85] == 10, 'Caption type changed')
    require(struct.unpack_from('<h',before,dst+86)[0] == 72, 'Sortie label binding changed')
    require(struct.unpack_from('<h',before,donor+86)[0] == 73, 'Streak binding changed')
    require(before[counter+85] == 11 and struct.unpack_from('<h',before,counter+86)[0] == 144,
            'Counter binding changed')
    count,ptr = struct.unpack_from('<II',before,dst+60)
    dc,dp = struct.unpack_from('<II',before,donor+60)
    require(count == dc == 4, 'Caption quad changed')
    require(abs(struct.unpack_from('<f',before,dst+32)[0]-66/141) < 1e-6, 'Unexpected old fitting')
    require(struct.unpack_from('<4f',before,donor+32) == (1,1,1,1), 'Donor scale changed')
    # Retain the caption's own Y and bindings. Copy the known-good label-cell
    # geometry and position used by Streak directly below it, with no scaling.
    allowed = set()
    def put(at,raw):
        after[at:at+len(raw)] = raw
        allowed.update(range(at,at+len(raw)))
    put(dst,before[donor:donor+4])
    put(dst+32,before[donor+32:donor+48])
    put(ptr,before[dp:dp+64])
    require(all(a == b or i in allowed for i,(a,b) in enumerate(zip(before,after))), 'Unrelated layout changed')
    require(after[counter:counter+112] == before[counter:counter+112], 'Counter changed')
    text = 'Sorties'
    width = measure_text(p[2500],text)[0]
    xs = [struct.unpack_from('<f',after,ptr+i*16)[0] for i in range(4)]
    cell_width = max(xs)-min(xs)
    require(width+4 <= cell_width, 'Caption does not fit normal cell')
    cc,cp = struct.unpack_from('<II',before,counter+60)
    require(cc == 4, 'Counter quad changed')
    label_right = struct.unpack_from('<f',after,dst)[0]+max(xs)
    counter_left = struct.unpack_from('<f',before,counter)[0]+min(
        struct.unpack_from('<f',before,cp+i*16)[0] for i in range(cc))
    require(counter_left-label_right >= 20, 'Label cell overlaps counter cell')
    table,edits = patch_table(p[3013],[dict(id='sorties_fit',table_ids=[3013],
        source='Player Sorties',target=text)],3013)
    require(len(edits) == 1 and edits[0]['slot'] == 71, 'Unexpected string edits')
    oldrows,newrows = parse_table(p[3013])[3],parse_table(table)[3]
    require([(a,b) for a,b,_,_ in oldrows] == [(a,b) for a,b,_,_ in newrows], 'Text slots changed')
    for old,new in zip(oldrows,newrows):
        require(new[3] == (b'Sorties' if old[1] == 72 else old[3]), 'Other strings changed')
    a,_ = spans(data)[21];s,_ = spans(p[21])[0];t,_ = spans(data)[3013]
    changes = [dict(offset=origin+a+s,before=before,after=bytes(after)),
               dict(offset=origin+t,before=p[3013],after=table)]
    changes.sort(key=lambda c:c['offset'])
    require(all(len(c['before']) == len(c['after']) for c in changes), 'Extent changed')
    require(changes[0]['offset']+len(changes[0]['after']) <= changes[1]['offset'], 'Overlapping edits')
    summary = dict(bundle=4002053,layout=21,node=6,text_id=72,
        old_label='Player Sorties',new_label=text,caption_width=width,cell_width=cell_width,
        horizontal_scale=1,vertical_scale=1,geometry_donor_node=8,
        caption_to_counter_gap=counter_left-label_right,
        counter_node=7,counter_unchanged=True,other_strings_unchanged=True,
        fonts_unchanged=True,runtime_verified=False,
        diagnosis='User screenshot shows the fitted HD label overlapping the numeric counter; use the standard Streak caption geometry and shorter wording.')
    FOLDER.mkdir(parents=True,exist_ok=True)
    (FOLDER/'layout.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    return changes,summary,None


if __name__ == '__main__':
    writer.VERSION,writer.BASE,writer.OUTPUT,writer.BASE_HASH = VERSION,BASE,OUTPUT,BASE_HASH
    writer.plan = plan
    writer.main()
