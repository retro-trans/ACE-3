"""Pack 4x Latin glyphs into native-sized atlases by omitting Japanese text.

Offline feasibility prototype only. Never writes an ISO. Remaining Japanese text
and the renderer's sampling behavior must be resolved before integration.
"""
import hashlib
import json
import re
import struct

from PIL import Image
from build_controller_patch import NativeGlyphs
from build_flight_save_patch import parts
from dialogue_corpus import archive
from dialogue_font import texture_pixels, encode_pixels
from preview_hd_font import BASE, OUT, BUNDLES, make_hd, rect, record, panel
from ui_font import font_map, measure_text

JAPANESE = re.compile('[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff\uff66-\uff9f\u3005\u303b]')


def compact_positions(glyphs, width, height):
    """Maximal-free-rectangle packing for mixed-height glyph sets."""
    for ordering in ('area','height','side'):
        key=lambda g: (g['w']+2*g['pad'])*(g['h']+2*g['pad'])
        if ordering=='height':key=lambda g:g['h']*10000+g['w']
        if ordering=='side':key=lambda g:max(g['w'],g['h'])*10000+g['w']*g['h']
        free=[(0,0,width,height)];positions={}
        for g in sorted(glyphs,key=lambda g:(-key(g),g['old_index'])):
            gw,gh=g['w']+2*g['pad'],g['h']+2*g['pad']
            candidates=[r for r in free if gw<=r[2] and gh<=r[3]]
            if not candidates:break
            x,y,rw,rh=min(candidates,key=lambda r:(min(r[2]-gw,r[3]-gh),max(r[2]-gw,r[3]-gh),r[1],r[0]))
            positions[g['old_index']]=(x+g['pad'],y+g['pad'])
            split=[]
            for fx,fy,fw,fh in free:
                if x>=fx+fw or x+gw<=fx or y>=fy+fh or y+gh<=fy:
                    split.append((fx,fy,fw,fh));continue
                if x>fx:split.append((fx,fy,x-fx,fh))
                if x+gw<fx+fw:split.append((x+gw,fy,fx+fw-x-gw,fh))
                if y>fy:split.append((fx,fy,fw,y-fy))
                if y+gh<fy+fh:split.append((fx,y+gh,fw,fy+fh-y-gh))
            split=list(dict.fromkeys(split))
            free=[r for i,r in enumerate(split) if not any(i!=j and q[0]<=r[0] and q[1]<=r[1]
                  and q[0]+q[2]>=r[0]+r[2] and q[1]+q[3]>=r[1]+r[3] for j,q in enumerate(split))]
        if len(positions)==len(glyphs):return positions
    raise ValueError('Glyph rectangles cannot fit the native atlas')


def is_japanese(code):
    try:
        char = code.to_bytes(1 if code < 256 else 2, 'big').decode('cp932')
    except (UnicodeError, ValueError):
        return False  # Unknown mappings are retained, never silently discarded.
    return bool(JAPANESE.search(char))


def pack(font, texture, retain_codes=(), pad_native=True):
    native = NativeGlyphs(font, texture)
    mapping, start, count = font_map(font)
    assert struct.unpack_from('<I',font,8)[0] == 19
    assert struct.unpack_from('<I',font,4)[0] == start+24*count
    retain_codes = set(retain_codes)
    keep = {code:index for code,index in mapping.items() if not is_japanese(code) or code in retain_codes}
    assert all(code in keep for code in range(32,127))
    indices = sorted(set(keep.values()))
    latin = {mapping[code] for code in range(33,127)}
    w,h,pixels = texture_pixels(texture)
    assert (w,h) == (1024,512)
    palette_at = 32+struct.unpack_from('<I',texture,4)[0]
    palette = texture[palette_at:palette_at+64]
    colors = [tuple(palette[i:i+3])+(min(255,palette[i+3]*2),) for i in range(0,64,4)]
    transparent = next(i for i,c in enumerate(colors) if c[3] == 0)
    hd, _ = make_hd(native)
    quantized = {}
    glyphs=[]
    for index in indices:
        row = record(font,start,index)
        if index in latin:
            tile = hd.crop(rect(row,hd.size))
            data=[]
            for rgba in tile.getdata():
                if rgba not in quantized:
                    quantized[rgba] = min(range(16),key=lambda i:sum((a-b)**2 for a,b in zip(rgba,colors[i])))
                data.append(quantized[rgba])
            gw,gh=tile.size
            data=bytes(data)
        else:
            x,y,xx,yy=rect(row,(w,h));gw,gh=xx-x,yy-y
            data=b''.join(pixels[j*w+x:j*w+xx] for j in range(y,yy))
        glyphs.append(dict(old_index=index,w=gw,h=gh,pixels=data,metrics=row[4:],
                           pad=1 if index in latin or pad_native else 0))
    shelves=[]
    for g in sorted(glyphs,key=lambda g:(-g['h'],-g['w'],g['old_index'])):
        gw,gh=g['w']+2*g['pad'],g['h']+2*g['pad']
        fits=[s for s in shelves if s['h']>=gh and s['x']+gw<=w]
        if fits:
            shelf=min(fits,key=lambda s:(s['h']-gh,w-s['x']-gw))
        else:
            shelf=dict(x=0,h=gh,items=[]);shelves.append(shelf)
        g['x']=shelf['x']+g['pad'];shelf['items'].append(g);shelf['x']+=gw
    height=sum(s['h'] for s in shelves)
    strategy='shelves'
    if height>h:
        positions=compact_positions(glyphs,w,h);strategy='maximal_free_rectangles'
        for g in glyphs:g['x'],g['y']=positions[g['old_index']]
        height=max(g['y']+g['h']+g['pad'] for g in glyphs)
    else:
        y=0
        for shelf in shelves:
            for g in shelf['items']:g['y']=y+g['pad']
            y+=shelf['h']
    assert height<=h, height
    packed=bytearray([transparent])*(w*h);occupied=bytearray(w*h)
    for g in glyphs:
        left,top=g['x']-g['pad'],g['y']-g['pad']
        right,bottom=g['x']+g['w']+g['pad'],g['y']+g['h']+g['pad']
        assert 0<=left<right<=w and 0<=top<bottom<=h
        for j in range(top,bottom):
            assert not any(occupied[j*w+left:j*w+right]), 'Packed glyph overlap'
            occupied[j*w+left:j*w+right]=b'\1'*(right-left)
        for j in range(g['h']):
            at=(g['y']+j)*w+g['x']
            packed[at:at+g['w']]=g['pixels'][j*g['w']:(j+1)*g['w']]
    remap={g['old_index']:i for i,g in enumerate(glyphs)}
    lookup={code:remap[index] for code,index in keep.items()}
    ranges=[]
    for code,index in sorted(lookup.items()):
        if ranges and code==ranges[-1][1]+1 and index==ranges[-1][2]+code-ranges[-1][0]:
            ranges[-1][1]=code
        else:
            ranges.append([code,code,index])
    out=bytearray(font[:32])
    for row in ranges:out.extend(struct.pack('<3I',*row))
    glyph_start=len(out)
    for g in glyphs:
        out.extend(struct.pack('<4f4h',g['x']/w,g['y']/h,(g['x']+g['w'])/w,
                               (g['y']+g['h'])/h,*g['metrics']))
    struct.pack_into('<I',out,4,len(out))
    struct.pack_into('<HH',out,16,len(ranges),len(glyphs))
    struct.pack_into('<I',out,24,glyph_start)
    output_texture=encode_pixels(texture,packed)
    assert output_texture[:32] == texture[:32] and len(output_texture)==len(texture)
    assert output_texture[palette_at:] == texture[palette_at:]
    rw,rh,decoded=texture_pixels(output_texture)
    assert (rw,rh,bytes(decoded)) == (w,h,bytes(packed))
    checked,gs,new_count=font_map(out)
    assert checked==lookup and new_count==len(glyphs)
    for code,index in keep.items():
        assert record(out,gs,checked[code])[4:] == record(font,start,index)[4:]
    for g in glyphs:
        row=record(out,gs,remap[g['old_index']]);x,y,xx,yy=rect(row,(w,h))
        actual=b''.join(decoded[j*w+x:j*w+xx] for j in range(y,yy))
        assert actual==g['pixels']
    for sample in ['Combat Records','Unit Upgrades',"They were fun days, but Eureka wasn't there."]:
        assert measure_text(out,sample)==measure_text(font,sample)
    report=dict(original_glyphs=count,retained_glyphs=len(glyphs),latin_4x_glyphs=len(latin),
                removed_japanese_only_glyphs=count-len(glyphs),used_height=height,atlas_height=h,
                atlas_dimensions=[w,h],texture_bytes=len(output_texture),
                metrics_preserved=True,non_latin_glyph_pixels_preserved=True,
                palette_and_gpu_header_preserved=True,texture_round_trip_verified=True,
                all_ascii_present=True,removed_codepoints=len(mapping)-len(lookup),
                retained_japanese_codepoints=sum(is_japanese(c) for c in lookup),
                latin_guard_texels=1,native_guard_texels=1 if pad_native else 0)
    report['packing_strategy']=strategy
    return bytes(out),output_texture,report


def main():
    folder=OUT/'native-prototype';folder.mkdir(parents=True,exist_ok=True)
    reports=[]
    with BASE.open('rb') as stream:
        fi,entries=archive(stream)
        for rid in BUNDLES:
            entry=next(e for e in entries if e[3]==rid)
            stream.seek(fi['offset']+entry[2]);p=parts(stream.read(entry[1]))
            font,texture,report=pack(p[2500],p[2000])
            (folder/('%d-font.bin'%rid)).write_bytes(font)
            (folder/('%d-texture.bin'%rid)).write_bytes(texture)
            report.update(bundle=rid,source_sha256=hashlib.sha256(p[2500]+p[2000]).hexdigest())
            reports.append(report)
            if rid==4002050:
                n=NativeGlyphs(font,texture)
                panel(n,n.atlas).save(folder/'native-packed-font-preview.png')
    result=dict(status='offline_native_resource_prototype_not_in_iso',base_version='0.9.6',
                font_typeface='Times New Roman from local Windows font; no TTF redistributed',
                samples=reports,remaining_work=[
                    'Translate Japanese text still reachable by each font user',
                    'Classify unreviewed/legacy mission variants and unsupported text formats',
                    'Verify renderer sampling and icons with native resources in-game',
                    'Handle smaller HUD fonts separately; this prototype only covers main 19px fonts'])
    (folder/'report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'samples':[{k:r[k] for k in ('bundle','retained_glyphs','used_height')} for r in reports],
                      'status':result['status']},indent=2))


if __name__=='__main__':main()
