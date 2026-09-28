"""0.1.68: bake the stat gauge shift into vertices, retaining native origins.

The reported Player Select screen has shifted tick frames but fills at their
old origins. Match the menu-spacing repair: avoid an origin-only adjustment.
Dry run by default; --write builds and verifies a new local test ISO.
"""
import struct
from build_ui_patch import ROOT, require
from build_flight_save_patch import parts
from dialogue_corpus import archive
from build_stat_columns_patch import PANELS, ranges, quad, BAR_SHIFT
import build_stats_panel_patch as writer

VERSION = '0.1.68'
BASE = ROOT/'work/output/ACE3-English-0.1.67.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_HASH = '076778669f43e958b1376231385789ff6147a689b5de4f1d857462db1ad85475'


def repair(data, labels, layers, frame, groups):
    out = bytearray(data); touched = set(); reports = []
    def put(at, value):
        struct.pack_into('<f',out,at,value);touched.update(range(at,at+4))
    fa = 80+frame*112
    fp = struct.unpack_from('<I',data,fa+64)[0]
    fx = struct.unpack_from('<f',data,fa)[0]
    for label, group in zip(labels,groups):
        la,lp,lxs = quad(data,label,10)
        label_right = struct.unpack_from('<f',data,la)[0]+max(lxs)
        frame_xs = [fx+struct.unpack_from('<f',data,fp+i*16)[0] for i in range(group,group+16)]
        for node in range(label+1,label+1+layers):
            a,ptr,xs = quad(data,node,3)
            origin = struct.unpack_from('<f',data,a)[0]
            require(abs(min(xs))<.001 and 63<max(xs)<64,'Expected shortened 0.1.49 gauge')
            put(a,origin-BAR_SHIFT)
            for i,x in enumerate(xs):put(ptr+i*16,x+BAR_SHIFT)
            new_origin=struct.unpack_from('<f',out,a)[0]
            new_xs=[struct.unpack_from('<f',out,ptr+i*16)[0] for i in range(4)]
            actual=[new_origin+x for x in new_xs]
            require(all(abs(origin+x-y)<.001 for x,y in zip(xs,actual)), 'Intended world placement changed')
            # Recruitment panels have a pre-existing 2.07-unit fill/frame
            # offset; retain it while removing the 28-unit runtime drift.
            require(abs(min(actual)-min(frame_xs))<2.2 and abs(max(actual)-max(frame_xs))<2.2,
                    'Fill and tick-frame bounds differ')
            require(min(actual)-label_right>=6,'Label clearance lost')
            # The existing binding/value controls retain their original form;
            # 0%, 50% and 100% span the same shortened frame from its new left.
            samples=[min(actual)+(max(actual)-min(actual))*v for v in (0,.5,1)]
            require(all(min(frame_xs)-2.2<=x<=max(frame_xs)+2.2 for x in samples),'Gauge range outside frame')
            reports.append(dict(node=node,label_node=label,origin=new_origin,
                                local_left=min(new_xs),local_right=max(new_xs),
                                label_clearance=min(actual)-label_right,
                                fill_bounds=[min(actual),max(actual)],
                                frame_bounds=[min(frame_xs),max(frame_xs)]))
    require(all(x==y or i in touched for i,(x,y) in enumerate(zip(data,out))), 'Unrelated layout bytes changed')
    return bytes(out), reports


def plan():
    edits=[];reports=[]
    with BASE.open('rb') as f:
        fi,es=archive(f)
        for rid,lid,frame,heading,labels,layers,groups in PANELS:
            e=next(e for e in es if e[3]==rid)
            origin=fi['offset']+e[2];f.seek(origin);bundle=f.read(e[1]);p=parts(bundle)
            before=parts(p[lid])[0]
            after,rows=repair(before,labels,layers,frame,groups)
            edits.append(dict(offset=origin+ranges(bundle)[lid][0]+ranges(p[lid])[0][0],before=before,after=after))
            reports.append(dict(bundle=rid,layout=lid,gauges=rows))
    edits.sort(key=lambda e:e['offset'])
    require(len(edits)==4 and sum(len(p['gauges']) for p in reports)==42,'Panel coverage changed')
    require(all(a['offset']+len(a['after'])<=b['offset'] for a,b in zip(edits,edits[1:])), 'Overlapping edits')
    return edits,dict(panels=reports,gauge_layers=42,runtime_verified=False),None


if __name__=='__main__':
    writer.VERSION,writer.BASE,writer.OUTPUT,writer.BASE_HASH=VERSION,BASE,OUTPUT,BASE_HASH
    writer.plan=plan
    writer.main()
