"""0.1.61: native ending dialogue and bilingual lyric captions. Dry-run by default.

Adds type-0x1000 / event-25 tracks to the original POLY animation, using the
game's two STUF text slots. No recorded video replaces the live credits.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from build_ui_patch import ROOT, require, u32, iso_files
from dialogue_corpus import archive, parse_table
from build_history_patch import chunks
from build_flight_save_patch import parts
from build_scene_patch import wrap_words
from ui_font import measure_text
import build_dialogue_patch as builder

VERSION = '0.1.61'
BASE = ROOT/'work/output/ACE3-English-0.1.59.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_SHA = '02a88eef45164866969f6892910b4f88ff739eda62cf6f182a84739744ce1faa'
MOTION_ID = 3823496
TABLE_IDS = (6350, 2002350, 3200350, 3201350)
ELF_DELTA = 0xfff80
# The capture starts 157 emulated frames into clip 7, where the roll begins.
CAPTURE_ROLL_SECONDS = 157/60
# PCSX2 capture PTS advances at 59.94 Hz; POLY uses nominal 60-frame seconds.
CAPTURE_TO_POLY = 59.94/60
# Nine independent 12-second waveform matches, capture seconds 5..310.
SONG_CAPTURE_INTERCEPT = 14.554918
SONG_CAPTURE_RATE = 0.99994404


def align(data, n=16):
    return data+b'\0'*(-len(data) % n)


def clean(text):
    return text.translate(str.maketrans({'—':'--', '–':'-', '’':"'", '“':'"', '”':'"', '…':'...'}))


def captions(font):
    dialogue = json.loads((ROOT/'work/translation/en/credits_057.json').read_text(encoding='utf-8'))
    song = json.loads((ROOT/'work/translation/en/ending_song_060.json').read_text(encoding='utf-8'))
    require(len(dialogue['subtitles']) == 72 and len(song['subtitles']) == 26, 'Caption coverage changed')
    require(dialogue['review_status'] == 'meaning_reviewed_for_user_preview', 'Dialogue review missing')
    require(song['review']['status'] == 'meaning_reviewed_with_uncertainties', 'Song review missing')
    font_height = struct.unpack_from('<h', font, 8)[0]
    require(font_height > 0, 'Font height invalid')
    rows = []
    for track, source, size, y in [('dialogue', dialogue, 18, 374), ('song', song, 17, 10)]:
        for index, cue in enumerate(source['subtitles']):
            start, end = cue['start'], cue['end']
            if track == 'song':
                start = (start-SONG_CAPTURE_INTERCEPT)/SONG_CAPTURE_RATE
                end = (end-SONG_CAPTURE_INTERCEPT)/SONG_CAPTURE_RATE
                text = clean(cue['romaji'])+'\n'+clean(cue['text'])
                require(len(text.splitlines()) == 2, 'Lyric layout')
            else:
                text = wrap_words(clean(cue['text']), font, 572*font_height/size, 3)
            widths = [v*size/font_height for v in measure_text(font, text)]
            require(max(widths) <= 572, 'Caption too wide')
            require(y+len(widths)*size <= 438, 'Caption too tall')
            rows.append(dict(track=track, source_index=index, id=10001+len(rows), text=text,
                             start=start*CAPTURE_TO_POLY+CAPTURE_ROLL_SECONDS,
                             end=end*CAPTURE_TO_POLY+CAPTURE_ROLL_SECONDS,
                             size=size, x=34, y=y, widths=widths))
    require(all(0 <= r['start'] < r['end'] < 350 for r in rows), 'Caption time range')
    for track in ['dialogue','song']:
        seq=sorted((r for r in rows if r['track']==track),key=lambda r:r['start'])
        require(all(a['end'] <= b['start']+.001 for a,b in zip(seq,seq[1:])), 'Overlapping track')
    return rows


def extend_table(source, rows):
    oldsize, oldptr, count, oldrows = parse_table(source)
    ranges = u32(source,12)
    ptr = oldptr+12
    result=bytearray(source[:28])
    result.extend(source[28:oldptr])
    result.extend(struct.pack('<3I',count,10001,10000+len(rows)))
    result.extend(bytes((count+len(rows))*4))
    # Preserve the entire original string pool, including unindexed strings.
    pool_start=oldptr+count*4
    shift=len(result)-pool_start
    result.extend(source[pool_start:oldsize])
    for slot in range(count):
        old=u32(source,oldptr+slot*4)
        struct.pack_into('<I',result,ptr+slot*4,old+shift if old else 0)
    for index,row in enumerate(rows):
        struct.pack_into('<I',result,ptr+(count+index)*4,len(result))
        result.extend(row['text'].encode('cp932')+b'\0')
    result=bytearray(align(bytes(result),32))
    struct.pack_into('<I',result,4,len(result))
    struct.pack_into('<3I',result,12,ranges+1,count+len(rows),ptr)
    parsed=parse_table(result)[3]
    require([(s,i,raw) for s,i,_,raw in parsed[:len(oldrows)]] ==
            [(s,i,raw) for s,i,_,raw in oldrows], 'Original text changed')
    require([raw.decode('cp932') for _,i,_,raw in parsed if i>=10001]==[r['text'] for r in rows],
            'Added text round-trip failed')
    return bytes(result)


def add_tracks(clip, cues, template, metadata):
    count, old_channels=u32(clip,16),u32(clip,20)
    result=bytearray(align(clip))
    channel_at=len(result)
    result.extend(clip[old_channels:old_channels+count*64])
    tracks=[(track,[c for c in cues if c['track']==track]) for track in ['dialogue','song']]
    tracks=[(track,cs) for track,cs in tracks if cs]
    result.extend(bytes(64*len(tracks)))
    # Preserve the original hierarchy and append caption tracks as root siblings.
    root=0;visited=set()
    while True:
        require(root not in visited and root<count,'Invalid root channel chain')
        visited.add(root)
        sibling=struct.unpack_from('<i',clip,old_channels+root*64+60)[0]
        if sibling<0:break
        root=sibling
    struct.pack_into('<I',result,channel_at+root*64+60,count)
    for t,(_,cs) in enumerate(tracks):
        cs=sorted(cs,key=lambda c:c['local_start'])
        channel=bytearray(template)
        # The channel template's offsets belong to clip 7. Give every new
        # channel its own metadata and empty interpolation storage instead.
        meta_at=len(result);result.extend(metadata)
        empty_at=len(result);result.extend(bytes(64))
        struct.pack_into('<I',channel,0,0)
        struct.pack_into('<I',channel,12,(u32(channel,12)&0xffff0000)|len(cs))
        struct.pack_into('<I',channel,16,len(result))
        struct.pack_into('<I',channel,20,meta_at)
        for field in (36,40,44,48):struct.pack_into('<I',channel,field,empty_at)
        struct.pack_into('<I',channel,24,0xffffffff)
        struct.pack_into('<2I',channel,56,0xffffffff,count+t+1 if t+1<len(tracks) else 0xffffffff)
        keys=len(result)
        result.extend(bytes(len(cs)*48))
        for n,cue in enumerate(cs):
            # Two native text slots; leave two frames for expiry before next cue.
            duration=max(1.,(cue['end']-cue['start'])*60-2.)
            payload=len(result)
            result.extend(struct.pack('<IIHHfIHH',0,cue['id'],cue['x'],cue['y'],0.,0,cue['size'],0))
            key=bytearray(48)
            struct.pack_into('<2f',key,0,cue['local_start']*60,duration)
            struct.pack_into('<I',key,20,32)
            struct.pack_into('<2I',key,32,payload,25)
            result[keys+n*48:keys+(n+1)*48]=key
        result[channel_at+(count+t)*64:channel_at+(count+t+1)*64]=channel
    struct.pack_into('<2I',result,16,count+len(tracks),channel_at)
    require(result[24:len(clip)] == clip[24:], 'Original clip data changed')
    return align(bytes(result))


def patch_motion(data, rows):
    blocks=chunks(data)
    _,start,end=next(b for b in blocks if b[0]==b'POLY')
    poly=data[start+16:end]
    require(u32(poly,12)==23 and u32(poly,0)==len(poly), 'Unexpected POLY format')
    roll_record=0x50+6*32
    roll=poly[u32(poly,roll_record+12):][:u32(poly,roll_record+16)]
    template=roll[u32(roll,20):u32(roll,20)+64]
    metadata=roll[u32(template,20):u32(template,20)+16]
    require(u32(template,4)==4096 and u32(roll,u32(template,16)+36)==26,'Roll start not found')
    out=bytearray(poly)
    report=[]
    used=[]
    for clip_id in range(7,23):
        record=0x50+(clip_id-1)*32
        require(u32(poly,record)==clip_id,'Clip identity')
        off,size=u32(poly,record+12),u32(poly,record+16)
        clip=poly[off:off+size]
        duration=u32(clip,12)/60
        origin=(clip_id-7)*20
        require(duration==(50 if clip_id==22 else 20),'Clip duration changed')
        cues=[dict(r,local_start=r['start']-origin) for r in rows if origin<=r['start']<origin+duration]
        used.extend(c['id'] for c in cues)
        if not cues:continue
        added=add_tracks(clip,cues,template,metadata)
        out=bytearray(align(bytes(out)))
        struct.pack_into('<2I',out,record+12,len(out),len(added))
        out.extend(added)
        report.append(dict(clip=clip_id,original_size=size,new_size=len(added),captions=len(cues)))
    require(sorted(used)==sorted(r['id'] for r in rows),'Missing/duplicate timed captions')
    struct.pack_into('<I',out,0,len(out))
    header=bytearray(data[start:start+16])
    struct.pack_into('<I',header,4,len(out)+16)
    result=data[:start]+bytes(header)+bytes(out)+data[end:]
    require([x[0] for x in chunks(result)]==[x[0] for x in blocks],'Chunk chain broken')
    return result,report


def roll_window_code():
    """Reassemble the existing staff-only loop in place, skipping baselines outside
    64..351. Original font, parsing, timing, names and dynamic line count survive.
    No code cave, new ELF segment, global draw hook or writable executable data.
    """
    start,end=0x30ead0,0x30eb78
    words=[];labels={};fix=[]
    def emit(w):words.append(w)
    def imm(op,rt,rs,value):emit((op<<26)|(rs<<21)|(rt<<16)|(value&65535))
    def r(fn,rd,rs,rt):emit((rs<<21)|(rt<<16)|(rd<<11)|fn)
    def jal(addr):emit(0x0c000000|(addr>>2))
    def branch(op,rs,rt,label):fix.append((len(words),label));imm(op,rt,rs,0)
    def mtc(rt,fs):emit(0x44800000|(rt<<16)|(fs<<11))
    def cvt(fd,fs):emit(0x46800020|(fs<<11)|(fd<<6))
    imm(9,16,0,0) # s0 = line index
    labels['loop']=len(words)
    imm(33,2,17,18);imm(33,3,17,10)
    emit((2<<21)|(16<<16)|(2<<11)|0x18) # R5900 MULT v0,v0,s0
    r(0x21,2,2,3)
    imm(9,1,2,-64);imm(11,1,1,288)
    branch(4,1,0,'next');emit(0)
    imm(33,6,17,16);r(0x21,6,6,16)
    imm(35,5,17,0xc8)
    jal(0x1b60c0);imm(9,4,29,0x838)
    imm(35,5,29,0x838)
    branch(4,5,0,'next');emit(0)
    jal(0x213910);imm(9,4,29,0x390)
    imm(33,2,17,18);imm(33,3,17,10)
    emit((2<<21)|(16<<16)|(2<<11)|0x18)
    r(0x21,2,2,3);imm(33,3,17,8)
    mtc(2,13);mtc(3,12);cvt(13,13);cvt(12,12)
    jal(0x194ce0);imm(9,4,29,0x390)
    labels['next']=len(words)
    imm(33,3,17,18);imm(9,2,0,448)
    emit((2<<21)|(3<<16)|0x1a);emit((2<<11)|0x12)
    imm(9,2,2,7);imm(9,16,16,1);r(0x2a,2,16,2)
    branch(5,2,0,'loop');emit(0)
    for index,label in fix:words[index]|=(labels[label]-index-1)&65535
    require(len(words)*4<=end-start,'Loop exceeds original function space')
    return struct.pack('<%dI'%len(words),*words)+bytes(end-start-len(words)*4)


def credits_draw_code():
    """Clip scrolling text and logo slots, then draw captions at full height.

    Reuses the original 0x130-byte credits draw function. When the roll is
    inactive, standalone images (including the disclaimer) retain full bounds.
    """
    start,end=0x30e380,0x30e4b0
    words=[];labels={};fix=[]
    def emit(w):words.append(w)
    def imm(op,rt,rs,value):emit((op<<26)|(rs<<21)|(rt<<16)|(value&65535))
    def jal(addr):emit(0x0c000000|(addr>>2))
    def branch(op,rs,rt,label):fix.append((len(words),label));imm(op,rt,rs,0)
    def move(rd,rs):emit((rs<<21)|(rd<<11)|0x21)
    # Original stack and 128-bit callee-saved register convention.
    emit(0x27bdff90);emit(0xffbf0020);emit(0x7fb10010);emit(0x7fb00000)
    imm(35,3,28,-0x7564);branch(4,3,0,'return');emit(0)
    jal(0x150f50);emit(0);imm(9,3,0,2)
    branch(5,2,3,'return');emit(0)
    jal(0x14ad50);move(4,0)
    imm(55,3,2,0x20);imm(63,3,29,0x30)
    jal(0x16d3e0);emit(0)
    imm(35,2,28,-0x7564);imm(33,2,2,14)
    branch(4,2,0,'set_clip');imm(55,5,29,0x30)
    imm(15,3,0,363);imm(13,3,3,64)
    emit((3<<16)|(3<<11)|0x3c) # dsll32 v1,v1,0
    imm(15,2,0,639);emit((2<<21)|(3<<16)|(5<<11)|0x25)
    labels['set_clip']=len(words)
    jal(0x16d550);imm(9,4,0,0x40)
    jal(0x16d420);emit(0)
    move(16,0);move(17,0)
    labels['images']=len(words)
    imm(35,2,28,-0x7564);emit((2<<21)|(17<<16)|(2<<11)|0x21)
    jal(0x30ee40);imm(9,4,2,0x48)
    imm(9,16,16,1);imm(11,2,16,6)
    branch(5,2,0,'images');imm(9,17,17,0x14)
    jal(0x30e980);imm(35,4,28,-0x7564)
    jal(0x16d3e0);emit(0)
    imm(55,5,29,0x30);jal(0x16d550);imm(9,4,0,0x40)
    jal(0x16d420);emit(0)
    move(17,0);move(16,0)
    labels['texts']=len(words)
    imm(35,2,28,-0x7564);emit((2<<21)|(16<<16)|(2<<11)|0x21)
    jal(0x30ebf0);imm(9,4,2,0x18)
    imm(9,17,17,1);imm(11,2,17,2)
    branch(5,2,0,'texts');imm(9,16,16,0x18)
    jal(0x16d3e0);emit(0)
    imm(15,2,0,447);imm(9,4,0,0x40)
    emit((2<<16)|(3<<11)|0x3c);imm(15,2,0,639)
    jal(0x16d550);emit((2<<21)|(3<<16)|(5<<11)|0x25)
    jal(0x16d420);emit(0)
    labels['return']=len(words)
    emit(0xdfbf0020);emit(0x7bb10010);emit(0x7bb00000)
    emit(0x03e00008);emit(0x27bd0070)
    for index,label in fix:words[index]|=(labels[label]-index-1)&65535
    require(len(words)*4<=end-start,'Draw function exceeds original space')
    return struct.pack('<%dI'%len(words),*words)+bytes(end-start-len(words)*4)


def plan():
    changes={};reports=[]
    with BASE.open('rb') as f:
        fi,entries=archive(f)
        def get(rid):
            _,size,off,_=next(e for e in entries if e[3]==rid)
            f.seek(fi['offset']+off);return f.read(size)
        rows=captions(parts(get(1200000))[2500])
        for rid in TABLE_IDS:
            data=get(rid);at=u32(data,20)
            table=extend_table(data[at:],rows)
            result=bytearray(align(data,32));new=len(result);result.extend(table)
            struct.pack_into('<I',result,20,new)
            require(result[:20]==data[:20] and result[24:len(data)]==data[24:], 'Original scene changed')
            changes[rid]=bytes(result)
            reports.append(dict(resource=rid,old_size=len(data),new_size=len(result),new_table_offset=new))
        changes[MOTION_ID],clips=patch_motion(get(MOTION_ID),rows)
        elf=iso_files(f)['/SLPS_257.84'];f.seek(elf['offset']);exe=f.read(elf['size'])
        old=exe[0x30ead0-ELF_DELTA:0x30eb78-ELF_DELTA]
        require(old[:8]==bytes.fromhex('12002386c0010224'),'Staff loop preimage')
    return changes,dict(captions=rows,tables=reports,clips=clips),old


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true')
    args=ap.parse_args()
    changes,report,old=plan()
    code=roll_window_code()
    draw=credits_draw_code()
    with BASE.open('rb') as f:
        elf=iso_files(f)['/SLPS_257.84'];f.seek(elf['offset']+0x30e380-ELF_DELTA)
        old_draw=f.read(len(draw))
    require(old_draw[:8]==bytes.fromhex('90ffbd272000bfff'),'Credits draw preimage')
    code_patches=[(0x30ead0,old,code),(0x30e380,old_draw,draw)]
    print('DRY RUN: 72 dialogue captions + 26 romaji/English lyric captions; native credits tracks')
    print(json.dumps(dict(resources={k:len(v) for k,v in changes.items()},clips=report['clips'],
                          sample=report['captions'][:2]+report['captions'][72:74],
                          staff_loop_bytes=len(code),credits_draw_bytes=len(draw)),indent=2),flush=True)
    if not args.write:return
    with BASE.open('rb') as f:require(builder.sha_region(f,0,BASE.stat().st_size)==BASE_SHA,'Base disc mismatch')
    builder.VERSION,builder.BASE,builder.OUTPUT=VERSION,BASE,OUTPUT
    builder.build(changes,[report])
    with OUTPUT.open('r+b') as f:
        exe=iso_files(f)['/SLPS_257.84']
        for address,before,after in code_patches:
            at=exe['offset']+address-ELF_DELTA
            f.seek(at);require(f.read(len(before))==before,'Finished ELF preimage')
            f.seek(at);f.write(after)
    with BASE.open('rb') as src,OUTPUT.open('rb') as dst:
        oldfiles,newfiles=iso_files(src),iso_files(dst)
        for name,record in newfiles.items():
            if name=='/DATA.BIN':continue
            src.seek(oldfiles[name]['offset']);expected=src.read(oldfiles[name]['size'])
            if name=='/SLPS_257.84':
                for address,before,after in code_patches:
                    at=address-ELF_DELTA
                    expected=expected[:at]+after+expected[at+len(before):]
            dst.seek(record['offset']);require(dst.read(record['size'])==expected,'Unexpected file change: '+name)
        fi,es=archive(dst)
        for rid,expected in changes.items():
            _,size,off,_=next(e for e in es if e[3]==rid);dst.seek(fi['offset']+off)
            require(dst.read(size)==expected,'Final resource mismatch')
        digest=builder.sha_region(dst,0,OUTPUT.stat().st_size)
    path=OUTPUT.with_suffix('.json');doc=json.loads(path.read_text(encoding='utf-8'))
    doc.update(sha256=digest,base_sha256=BASE_SHA,
               coverage='Ending live credits: 72 dialogue captions and 26 romaji/English lyric captions. Original staff names, animation, audio and postcredits dialogue retained.',
               staff_loop=dict(address='0x0030ead0',bytes=len(code),before_sha256=hashlib.sha256(old).hexdigest(),after_sha256=hashlib.sha256(code).hexdigest()),
               credits_draw=dict(address='0x0030e380',bytes=len(draw),before_sha256=hashlib.sha256(old_draw).hexdigest(),after_sha256=hashlib.sha256(draw).hexdigest()),
               runtime_verified=False)
    path.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
    print('BUILT',OUTPUT,digest,flush=True)


if __name__=='__main__':main()
