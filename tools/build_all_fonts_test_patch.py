"""0.9.9: redraw remaining Latin text fonts within existing game allocations.

Preserve every character mapping and all non-Latin glyph pixels. Dialogue
already upgraded in 0.9.7 stays byte-identical. Dry-run unless --write.
"""
import hashlib
import json
import struct
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from build_ui_patch import ROOT, require, u32
from dialogue_corpus import archive
from build_briefing_banner_patch import spans
from build_history_patch import chunks
from dialogue_font import texture_pixels, encode_pixels
from ui_font import font_map
from preview_hd_font import record, rect, text_image
from prototype_english_hd_font import compact_positions
from build_controller_patch import NativeGlyphs
import build_stats_panel_patch as writer

VERSION='0.9.9'
BASE=ROOT/'work/output/ACE3-English-0.9.8.iso'
OUTPUT=ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_HASH='c43427a77d155731c7f4f2e1a57128f5e948036a0dc595bdc3d1ccf1ecc5b9eb'
FOLDER=ROOT/'work/ui/font_all_099'


def cpu_texture(texture):
    t=struct.unpack_from('<Q',texture,16)[0]
    require((t>>20)&63 in (20,44),'Unsupported font texture')
    out=bytearray(texture)
    struct.pack_into('<Q',out,16,(t&~(63<<20))|(20<<20))
    return bytes(out)


def place(glyphs,w,h):
    shelves=[]
    for g in sorted(glyphs,key=lambda a:(-a['h'],-a['w'],a['old_index'])):
        gw,gh=g['w']+g['pad']*2,g['h']+g['pad']*2
        fit=[s for s in shelves if s['h']>=gh and s['x']+gw<=w]
        if fit:s=min(fit,key=lambda s:(s['h']-gh,w-s['x']-gw))
        else:s=dict(x=0,h=gh,items=[]);shelves.append(s)
        g['x']=s['x']+g['pad'];s['items'].append(g);s['x']+=gw
    height=sum(s['h'] for s in shelves)
    if height<=h:
        y=0
        for s in shelves:
            for g in s['items']:g['y']=y+g['pad']
            y+=s['h']
    else:
        positions=compact_positions(glyphs,w,h)
        for g in glyphs:g['x'],g['y']=positions[g['old_index']]


def redraw(font,texture,hud=False):
    view=cpu_texture(texture);native=NativeGlyphs(font,view)
    mapping,start,count=font_map(font);w,h,oldpixels=texture_pixels(view)
    latin={mapping[c]:chr(c) for c in range(33,127) if c in mapping}
    require(latin,'No Latin letters')
    palette=bytearray(texture[32+u32(texture,4):32+u32(texture,4)+64])
    if hud:
        # Only previously unused palette entries; preserve the colors sampled
        # by every existing symbol and non-Latin glyph.
        for index,color in zip((11,12,13,14,15),((32,32,32,32),(32,32,32,64),(32,32,32,96),(210,210,210,128),(235,235,235,128))):
            require(index not in oldpixels,'Reserved HUD palette color is used')
            palette[index*4:index*4+4]=bytes(color)
    colors=[tuple(palette[i:i+3])+(min(255,palette[i+3]*2),) for i in range(0,64,4)]
    def premult(c):return tuple(v*c[3]/255 for v in c[:3])+(c[3],)
    color_vectors=[premult(c) for c in colors]
    blank=next(i for i,c in enumerate(colors) if c[3]==0)
    vector=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf' if hud else 'C:/Windows/Fonts/times.ttf',160)
    hud_vector=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',14*4)
    masks={}
    for i,char in latin.items():
        original=native.atlas.crop(rect(record(font,start,i),(w,h)))
        bounds=original.getchannel('R').point(lambda a:255 if a>80 else 0).getbbox()
        if bounds is None:continue
        scratch=Image.new('L',(300,260));ImageDraw.Draw(scratch).text((20,10),char,font=vector,fill=255)
        require(scratch.getbbox() is not None,'Missing vector glyph')
        masks[i]=(original.size,bounds,scratch.crop(scratch.getbbox()))
    quant={};failures=[]
    for scale in (4,3,2,1.5,1.25,1.125,1):
        glyphs=[]
        for i in range(count):
            row=record(font,start,i);x,y,xx,yy=rect(row,(w,h))
            if i in masks:
                size,bounds,mask=masks[i];gw,gh=[max(1,round(v*scale)) for v in size]
                l,t,r,b=[round(v*scale) for v in bounds]
                ink=Image.new('L',(gw,gh));ink.paste(mask.resize((max(1,r-l),max(1,b-t)),Image.Resampling.LANCZOS),(l,t))
                # Dark outline stays inside the original font cell. Stronger
                # sans-serif strokes make target names readable over scenery.
                radius=max(1,round(scale*.5))
                if hud:
                    # The old font mixes 16px originals and 12px donor glyphs.
                    # Use one physical baseline instead of inheriting mismatched
                    # bitmap bounds. Supersample the fill AND outline together.
                    hi=Image.new('L',(max(1,row[5])*4,16*4))
                    hd=ImageDraw.Draw(hi);char=latin[i]
                    bb=hd.textbbox((0,0),char,font=hud_vector,anchor='ls')
                    hd.text((max(0,(hi.width-(bb[2]-bb[0]))//2-bb[0]),12*4),char,font=hud_vector,anchor='ls',fill=255)
                    tile=Image.new('RGBA',hi.size,(32,32,32,0));tile.putalpha(hi.filter(ImageFilter.MaxFilter(5)))
                    white=Image.new('RGBA',hi.size,(235,235,235,0));white.putalpha(hi);tile.alpha_composite(white)
                    tile=tile.resize((gw,gh),Image.Resampling.LANCZOS)
                else:
                    outline=ink.filter(ImageFilter.MaxFilter(radius*2+1))
                    tile=Image.new('RGBA',(gw,gh),(32,32,32,0));tile.putalpha(outline)
                    white=Image.new('RGBA',(gw,gh),(245,245,245,0));white.putalpha(ink);tile.alpha_composite(white)
                pixels=[]
                for c in tile.getdata():
                    if c not in quant:
                        q=premult(c)
                        quant[c]=min(range(16),key=lambda j:sum((a-b)**2*(3 if k==3 else 1) for k,(a,b) in enumerate(zip(q,color_vectors[j]))))
                    pixels.append(quant[c])
                pixels=bytes(pixels)
            else:
                gw,gh=xx-x,yy-y
                pixels=b''.join(oldpixels[j*w+x:j*w+xx] for j in range(y,yy))
            glyphs.append(dict(old_index=i,w=gw,h=gh,pad=1 if i in masks else 0,pixels=pixels))
        if sum((g['w']+2*g['pad'])*(g['h']+2*g['pad']) for g in glyphs)>w*h:
            failures.append([scale,'pixel capacity']);continue
        try:place(glyphs,w,h)
        except ValueError:failures.append([scale,'rectangle packing']);continue
        break
    else:raise ValueError('No safe packing fits while preserving every glyph')
    packed=bytearray([blank])*(w*h);occupied=bytearray(w*h);out=bytearray(font)
    for g in glyphs:
        x,y=g['x'],g['y'];gw,gh=g['w'],g['h'];pad=g['pad']
        require(0<=x-pad and x+gw+pad<=w and 0<=y-pad and y+gh+pad<=h,'Glyph bounds')
        for j in range(y-pad,y+gh+pad):
            require(not any(occupied[j*w+x-pad:j*w+x+gw+pad]),'Glyph overlap')
            occupied[j*w+x-pad:j*w+x+gw+pad]=b'\1'*(gw+pad*2)
        for j in range(gh):packed[(y+j)*w+x:(y+j)*w+x+gw]=g['pixels'][j*gw:(j+1)*gw]
        struct.pack_into('<4f',out,start+g['old_index']*24,x/w,y/h,(x+gw)/w,(y+gh)/h)
    enc=encode_pixels(view,packed);tx=bytearray(texture[:32]+enc[32:])
    paloff=32+u32(texture,4);tx[paloff:paloff+64]=palette;tx=bytes(tx)
    require(len(tx)==len(texture) and tx[:32]==texture[:32],'Texture allocation/header changed')
    for index in set(oldpixels):
        require(tx[paloff+index*4:paloff+index*4+4]==texture[paloff+index*4:paloff+index*4+4],'Existing glyph palette color changed')
    require(font_map(out)==font_map(font),'Font mappings changed')
    _,_,decoded=texture_pixels(cpu_texture(tx));require(bytes(decoded)==bytes(packed),'Texture encoding mismatch')
    for g in glyphs:
        i=g['old_index'];a=record(font,start,i);b=record(out,start,i)
        require(a[4:]==b[4:],'Text metrics changed')
        if i not in masks:
            x,y,xx,yy=rect(a,(w,h));source=b''.join(oldpixels[j*w+x:j*w+xx] for j in range(y,yy))
            x,y,xx,yy=rect(b,(w,h));dest=b''.join(decoded[j*w+x:j*w+xx] for j in range(y,yy))
            require(source==dest,'Non-Latin glyph changed')
    return bytes(out),tx,dict(scale=scale,atlas=[w,h],glyphs=count,redrawn_latin=len(masks),
                             all_mappings_preserved=True,non_latin_pixels_preserved=True,
                             metrics_preserved=True,gpu_header_preserved=True,unused_palette_entries_added=5 if hud else 0,larger_scales_unavailable=failures)


def proof(label,oldfont,oldtx,font,tx,hud):
    a=NativeGlyphs(oldfont,cpu_texture(oldtx));b=NativeGlyphs(font,cpu_texture(tx))
    sample='Daughtress Flyer / Monsuno type10' if hud else 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    sample=''.join(c for c in sample if ord(c) in a.mapping)
    canvas=Image.new('RGB',(1200,320),'#94a8b0');d=ImageDraw.Draw(canvas)
    title=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',24)
    for y,text,n in [(15,'Previous',a),(165,'New',b)]:
        d.text((20,y),label+' / '+text,font=title,fill='#101820')
        im=text_image(n,n.atlas,sample,3)
        canvas.paste(im,(20,y+42),im)
    canvas.save(FOLDER/(label+'.png'))


def plan():
    FOLDER.mkdir(parents=True,exist_ok=True)
    edits=[];reports=[];cache={}
    with BASE.open('rb') as f:
        fi,entries=archive(f)
        def get(rid):
            _,size,off,_=next(e for e in entries if e[3]==rid)
            f.seek(fi['offset']+off);return fi['offset']+off,f.read(size)
        def change(label,fa,ft,ta,tx,hud=False):
            key=hashlib.sha256(ft+tx+bytes([hud])).hexdigest()
            if key not in cache:
                try:cache[key]=redraw(ft,tx,hud)
                except ValueError as e:
                    reports.append(dict(location=label,changed=False,reason=str(e)));return
                proof(label,ft,tx,*cache[key][:2],hud)
            nf,nt,report=cache[key]
            for pos,before,after in ((fa,ft,nf),(ta,tx,nt)):
                require(len(before)==len(after),'Resource size changed')
                edits.append(dict(offset=pos,before=before,after=after))
            reports.append(dict(location=label,changed=True,**report))
            print(label,'scale',report['scale'],flush=True)
        # The eight enemy-name fonts and both untouched 20px secondary fonts.
        for rid in range(1200000,1200008):
            off,data=get(rid);s=spans(data)
            for fontid,texid in [(2501,2001)]+([(2500,2000)] if rid in (1200002,1200003) else []):
                a,z=s[fontid];t,zz=s[texid]
                change(str(rid)+'-'+str(fontid),off+a,data[a:z],off+t,data[t:zz],fontid==2501)
        # Standalone small fallback font; keep every Japanese character.
        fa,ft=get(35);ta,tx=get(36);change('global-12px',fa,ft,ta,tx)
        # Credits keep all names, Japanese glyphs and the existing scroll data.
        off,data=get(4350);_,a,z=next(c for c in chunks(data) if c[0]==b'STUF')
        origin=off+a+16;data=data[a+16:z];s=spans(data);fa,fz=s[2];ta,tz=s[1]
        change('staff-20px',origin+fa,data[fa:fz],origin+ta,data[ta:tz])
    edits.sort(key=lambda e:e['offset'])
    require(all(a['offset']+len(a['before'])<=b['offset'] for a,b in zip(edits,edits[1:])),'Overlapping resources')
    summary=dict(fonts=reports,dialogue_and_menu_19px_unchanged=True,all_character_mappings_preserved=True,
                 texture_replacements_required=False,runtime_verified=False,
                 limitations=['Fonts only: baked HUD artwork, movies and image labels remain unchanged',
                              'Existing 19px HD dialogue/menu fonts are preserved',
                              'In-game filtering, target labels, secondary text and credits need fresh-boot testing'])
    (FOLDER/'layout.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    return edits,summary,None


if __name__=='__main__':
    writer.VERSION,writer.BASE,writer.OUTPUT,writer.BASE_HASH=VERSION,BASE,OUTPUT,BASE_HASH
    writer.plan=plan
    writer.main()
