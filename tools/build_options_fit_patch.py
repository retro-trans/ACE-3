"""0.1.40: three-line memory warnings and fully fitted Game/Controls labels.

Default read-only dry run; --write builds a versioned test ISO.
"""
import argparse
import json
import struct
from build_ui_patch import ROOT,require,u32,inner_bnd
from dialogue_corpus import archive,parse_table
from build_flight_save_patch import parts
from build_intermission_patch import replace_rows
from ui_font import measure_text
import build_dialogue_patch as builder

VERSION='0.1.40'
BASE=ROOT/'work/output/ACE3-English-0.1.39.iso'
OUTPUT=ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
INPUT=ROOT/'work/translation/en/memory_warnings_040.json'
BUNDLES=(4002050,4002054,4002057)
LABEL_WIDTH=140
OPTIONS={3070:{10:('Attack Demo','Combo scene'),11:('Text','Comm messages'),
    44:('Play the demo when a Combo Attack triggers.','Play the Combo scene when a Combo Attack triggers.'),
    45:('Skip the demo when a Combo Attack triggers.','Skip the Combo scene when a Combo Attack triggers.')},
    3071:{8:('Camera Control','Camera Movement')}}


def fit_layout(data,labels,font):
    """Fit the seven/nine left-hand option labels within their existing row.

    Layout records use position/rotation/scale vectors at +0/+16/+32. Change
    only scale X for overwide text nodes, preserving height and row geometry.
    """
    nested=parts(data);d=nested[0];out=bytearray(d);edits=[]
    require(u32(d,4)==514 and u32(d,12)==80,'Unexpected options layout')
    found=[]
    for i in range(u32(d,8)):
        a=80+i*112;binding=struct.unpack_from('<h',d,a+86)[0]
        if d[a+85]!=10 or binding not in range(103,103+len(labels)):continue
        tid=binding-98;label=labels[tid];width=max(measure_text(font,label))
        x,y=struct.unpack_from('<2f',d,a)
        require(-293<x<-290 and abs(y-(-160.080154+30*(tid-5)))<0.01,'Unexpected option row coordinates')
        require(struct.unpack_from('<4f',d,a+32)==(1,1,1,1),'Unexpected text scale preimage')
        require(struct.unpack_from('<H',d,a+98)[0]>=len(label)+1,'Insufficient glyph capacity')
        scale=min(1.0,LABEL_WIDTH/float(width))
        if scale<1:
            struct.pack_into('<f',out,a+32,scale)
            edits.append({'widget':i,'binding':binding,'text_id':tid,'offset':a+32,'label':label,
                          'unscaled_width':width,'scale_x':scale,'display_width':width*scale})
        found.append(tid)
    require(sorted(found)==sorted(labels),'Missing/duplicate option label widgets')
    start,end=next((a,b) for k,a,b in inner_bnd(data[:u32(data,4)]) if k==0)
    require(end-start==len(out),'Layout extent changed')
    return data[:start]+bytes(out)+data[end:],edits


def plan():
    doc=json.loads(INPUT.read_text(encoding='utf-8'))
    require(doc['review']['status']=='meaning_reviewed' and doc['review']['rows_examined']==42,'Incomplete warning review')
    warning={r['text_id']:r for r in doc['rows'] if r['text_id'] in (1,28,29,48)}
    require(len(warning)==4,'Operation warning scope changed')
    changes={};reports=[]
    with BASE.open('rb') as f:
        fi,es=archive(f)
        for rid in BUNDLES:
            e=next(e for e in es if e[3]==rid);f.seek(fi['offset']+e[2]);before=f.read(e[1]);p=parts(before)
            edits={};text_changes=[];layout_changes=[]
            for tid in (3041,3070,3071):
                mapping={}
                for slot,i,_,raw in parse_table(p[tid])[3]:
                    old=raw.decode('cp932')
                    if tid==3041 and i in warning:
                        row=warning[i];require(old==row['source_current'],'Warning preimage changed')
                        target=row['target'];widths=measure_text(p[2500],target)
                        require(len(widths)==3 and max(widths)<=520,'Warning exceeds three-line box')
                    elif i in OPTIONS.get(tid,{}):
                        expected,target=OPTIONS[tid][i];require(old==expected,'Option preimage changed')
                        widths=measure_text(p[2500],target)
                        require(max(widths)<=620 and '\n' not in target,'Option line overflow')
                    else:continue
                    mapping[slot]=(old,target)
                    text_changes.append({'table_id':tid,'text_id':i,'slot':slot,'before':old,'target':target,'widths':widths})
                edits[tid]=replace_rows(p[tid],mapping)
            for layout,tid,end in ((42,3070,14),(43,3071,12)):
                labels={i:r.decode('cp932') for _,i,_,r in parse_table(edits[tid])[3] if 5<=i<end}
                new,rr=fit_layout(p[layout],labels,p[2500]);edits[layout]=new
                layout_changes.extend(dict(r,layout_id=layout,table_id=tid) for r in rr)
            changes[rid]=builder.rebuild_bundle(before,edits)
            after=parts(changes[rid])
            require(all(v==after[k] for k,v in p.items() if k not in edits),'Unrelated resource changed')
            reports.append({'resource_id':rid,'kind':'options_and_memory_fit','text_changes':text_changes,'layout_changes':layout_changes})
    return changes,reports


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    changes,reports=plan()
    summary={'menu_copies':len(reports),'text_changes':sum(len(r['text_changes']) for r in reports),
             'fitted_labels':sum(len(r['layout_changes']) for r in reports),'label_width_limit':LABEL_WIDTH,'warning_lines':3}
    print('DRY RUN',json.dumps(summary),flush=True)
    print(json.dumps(reports[0],indent=2),flush=True)
    if not args.write:return
    builder.VERSION,builder.BASE,builder.OUTPUT=VERSION,BASE,OUTPUT
    builder.build(changes,reports)
    path=OUTPUT.with_suffix('.json');report=json.loads(path.read_text(encoding='utf-8'))
    report['coverage']='Four three-line memory-card operation warnings and requested Game/Controls wording in three copies; fit every overwide left-column label. Narrow scrolling confirmations retained.'
    report['checks']=summary
    report['runtime_note']='Blank labels exist in active tables; horizontal fitting addresses their row width. In-game visibility still needs fresh-boot verification.'
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
