"""0.9.10: replace the baked Player Sorties sprite with the native HD text widget."""
import hashlib
import json
import struct
from PIL import Image, ImageDraw, ImageFont
from build_ui_patch import ROOT, require, u32, patch_table
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts
from build_briefing_banner_patch import spans
from build_controller_patch import NativeGlyphs
from preview_hd_font import text_image
from ui_font import measure_text
from ui_textures import decode
import build_stats_panel_patch as writer

VERSION='0.9.10'
BASE=ROOT/'work/output/ACE3-English-0.9.9.iso'
OUTPUT=ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_HASH='84a8c7b22475c602b97340a44f06181e9bc503ff59e1195801eb03f02df30a8b'
FOLDER=ROOT/'work/ui/sorties_0910'


def plan():
    FOLDER.mkdir(parents=True,exist_ok=True)
    with BASE.open('rb') as f:
        fi,entries=archive(f);_,size,off,_=next(e for e in entries if e[3]==4002053)
        origin=fi['offset']+off;f.seek(origin);data=f.read(size)
    p=parts(data);s=spans(data);nested=parts(p[21]);before=nested[0];d=bytearray(before)
    dst=80+6*112;donor=80+8*112
    require(d[dst+85]==1 and d[donor+85]==10,'Widget types changed')
    require(struct.unpack_from('<h',d,donor+86)[0]==73,'Streak donor binding changed')
    c,v,uc,uv=struct.unpack_from('<4I',d,dst+60)
    dc,dv,duc,duv=struct.unpack_from('<4I',d,donor+60)
    require((c,uc,dc,duc)==(4,4,4,4),'Unexpected quad')
    coords=[struct.unpack_from('<2f',d,uv+i*8) for i in range(4)]
    require(abs(coords[0][0]-.36875)<.00001 and abs(coords[0][1]-.21681)<.00001,'Sprite UV preimage')
    text='Player Sorties';width=measure_text(p[2500],text)[0];local_width=width+4
    old_x=struct.unpack_from('<f',d,dst)[0]
    right=max(struct.unpack_from('<f',d,v+i*16)[0] for i in range(4))
    display_width=66.0;left=old_x+right-display_width
    allowed=set()
    def put(at,raw):d[at:at+len(raw)]=raw;allowed.update(range(at,at+len(raw)))
    put(dst+84,before[donor+84:donor+112])
    put(dst+86,struct.pack('<h',72))
    put(dst,struct.pack('<f',left));put(dst+32,struct.pack('<f',display_width/local_width))
    put(dst+36,struct.pack('<f',.85))
    for i in range(4):
        y=struct.unpack_from('<f',before,dv+i*16+4)[0]
        put(v+i*16,struct.pack('<2f',0 if i<2 else local_width,y))
    put(uv,before[duv:duv+32])
    require(all(a==b or i in allowed for i,(a,b) in enumerate(zip(before,d))),'Unrelated layout change')
    require(struct.unpack_from('<H',d,dst+98)[0]>=len(text)+1,'Text buffer too small')
    table,changes=patch_table(p[3013],[dict(id='player_sorties_hd',table_ids=[3013],source='Sorties',target=text)],3013)
    require(len(changes)==1 and changes[0]['slot']==71,'Unexpected text replacements')
    oldrows=parse_table(p[3013])[3];newrows=parse_table(table)[3]
    require(all(a[3]==b[3] for a,b in zip(oldrows,newrows) if a[1]!=72),'Other strings changed')
    a,z=s[21];substart,subend=spans(p[21])[0]
    t,tz=s[3013]
    edits=[dict(offset=origin+a+substart,before=before,after=bytes(d)),
           dict(offset=origin+t,before=p[3013],after=table)]
    edits.sort(key=lambda e:e['offset'])
    require(all(len(e['before'])==len(e['after']) for e in edits),'Resource size changed')
    n=NativeGlyphs(p[2500],p[2000]);new=text_image(n,n.atlas,text,4)
    # Reconstruct at the game's fitted physical dimensions; not an emulator capture.
    new=new.resize((round(display_width*5),round(19*.85*5)),Image.Resampling.LANCZOS)
    old=decode(p[50101]).crop((47,28,125,45)).resize((round((right+2.49646)*5),15*5),Image.Resampling.BILINEAR)
    canvas=Image.new('RGB',(700,330),'#111820');draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',23)
    for y,title,img in [(15,'Previous bitmap label',old),(175,'Native HD font',new)]:
        draw.text((20,y),title,font=font,fill='white');canvas.paste(img,(30,y+40),img)
    canvas.save(FOLDER/'comparison.png')
    report=dict(bundle=4002053,layout=21,node=6,text_id=72,text=text,
                display_width=display_width,font_size=19,vertical_scale=.85,font_bundle_unchanged=True,
                replaces_sprite=True,credits_translation='Draft only; not integrated',runtime_verified=False)
    (FOLDER/'layout.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return edits,report,None


if __name__=='__main__':
    writer.VERSION,writer.BASE,writer.OUTPUT,writer.BASE_HASH=VERSION,BASE,OUTPUT,BASE_HASH
    writer.plan=plan;writer.main()
