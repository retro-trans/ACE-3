"""0.1.59 approved opening lyrics. Dry-run; --prepare movie, then --write ISO.

Preserves source audio, PSS pack layout and disc extents. Does not publish a release.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from PIL import ImageFont
from build_ui_patch import ROOT, iso_files, require
from pss_inspect import packets
from pss_remux import plan as remux
from render_movie_previews import stamp

VERSION = '0.1.59'
BASE = ROOT/'work/output/ACE3-English-0.1.54.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
WORK = ROOT/'work/build/opening_059'
SOURCE = ROOT/'work/build/movie_test/MOVIE001.PSS'
TRANSLATION = ROOT/'work/translation/en/movies_058/MOVIE001.json'
MOVIE = WORK/'MOVIE001_en.PSS'
NAME = '/MOVIE0/MOVIE001.PSS'
FFMPEG = ROOT/'work/local/movie-python/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
CHUNK = 8*1024*1024

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for raw in iter(lambda:f.read(CHUNK),b''):h.update(raw)
    return h.hexdigest()

def subtitles():
    doc=json.loads(TRANSLATION.read_text(encoding='utf-8'))
    require(doc['review']['status']=='user_lyrics_meaning_reviewed','Unreviewed lyrics')
    lines=['[Script Info]','ScriptType: v4.00+','PlayResX: 640','PlayResY: 448',
        'ScaledBorderAndShadow: yes','','[V4+ Styles]',
        'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
        'Style: Romaji,Georgia,15,&H008EDDF5,&H00FFFFFF,&H00101010,&H00000000,0,0,0,0,107,100,0,0,1,0.5,0,8,0,0,0,1',
        'Style: English,Georgia,16,&H00FFFFFF,&H00FFFFFF,&H00101010,&H00000000,0,0,0,0,107,100,0,0,1,0.5,0,8,0,0,0,1',
        '','[Events]','Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
    previous=0
    for row in doc['subtitles']:
        require(previous<=row['start']<row['end']<=166,'Invalid lyric timing')
        previous=row['end']
        for key,style,size,y in [('romaji','Romaji',15,382),('text','English',16,408)]:
            text=row[key]
            font=ImageFont.truetype('C:/Windows/Fonts/georgia.ttf',size)
            require(font.getlength(text)*1.07<=596,'Caption exceeds game width: '+text)
            require(not any(x in text for x in ['{','}','\\','\n']),'Unexpected ASS control')
            lines.append('Dialogue: 0,%s,%s,%s,,0,0,0,,{\\pos(320,%d)\\q2}%s' %
                (stamp(row['start']),stamp(row['end']),style,y,text))
    return '\n'.join(lines)+'\n',len(doc['subtitles'])

def verify_movie(original,patched):
    require(len(original)==len(patched),'Movie extent changed')
    pts=[];nonvideo=0
    for at,sid,head,pay,plen,info in packets(original):
        if sid!=0xe0:
            require(original[at:pay+plen]==patched[at:pay+plen],'Non-video packet changed')
            nonvideo+=1
    for at,sid,head,pay,plen,info in packets(patched):
        if sid==0xe0 and info.get('pts') is not None:pts.append(info['pts'])
    ordered=sorted(pts)
    require(len(ordered)==4980 and len(set(ordered))==4980,'Invalid frame timestamps')
    require(all(b-a==3000 for a,b in zip(ordered,ordered[1:])),'Expected exact 30fps PTS')
    return dict(non_video_packets_verified=nonvideo,unique_picture_pts=len(pts),ticks_per_picture=3000)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--prepare',action='store_true')
    ap.add_argument('--write',action='store_true')
    args=ap.parse_args()
    ass,cues=subtitles()
    with BASE.open('rb') as f:
        entry=iso_files(f)[NAME];f.seek(entry['offset']);original=f.read(entry['size'])
    require(original==SOURCE.read_bytes(),'Cached original differs from base disc movie')
    print(json.dumps(dict(version=VERSION,base=BASE.name,output=OUTPUT.name,movie=NAME,
        offset=entry['offset'],bytes=entry['size'],captions=cues,frame='640x448, 30fps',
        picture='532x372 centered above romaji and English; original proportions retained',
        audio='preserved byte-for-byte',prepare=args.prepare,write=args.write)),flush=True)
    if args.prepare:
        require(not MOVIE.exists(),'Prepared movie already exists')
        WORK.mkdir(parents=True,exist_ok=True)
        (WORK/'opening.ass').write_text(ass,encoding='utf-8')
        es=WORK/'opening.m2v'
        require(not es.exists(),'Encoded video already exists')
        cmd=[str(FFMPEG),'-hide_banner','-nostdin','-i',str(SOURCE),'-an',
            '-vf','setpts=PTS-STARTPTS,scale=532:372:flags=lanczos,pad=640:448:54:0:black,ass=opening.ass',
            '-c:v','mpeg2video','-threads','4','-profile:v','4','-level:v','8','-pix_fmt','yuv420p',
            '-r','30','-aspect','10:7','-b:v','4400k','-minrate','4400k','-maxrate','4400k',
            '-bufsize','1572864','-g','18','-bf','2','-sc_threshold','0','-dc','8','-mbd','rd',
            '-trellis','2','-cmp','2','-subcmp','2','-f','mpeg2video',str(es)]
        with (WORK/'encode.log').open('w') as log:
            subprocess.run(cmd,cwd=str(WORK),stdout=log,stderr=subprocess.STDOUT,check=True)
        patched,report=remux(original,es.read_bytes(),ticks=3000,pace_to_original=True)
        require(report['pictures_new']==report['pictures_original']==4980,'Frame count changed')
        report.update(verify_movie(original,patched))
        MOVIE.write_bytes(patched)
        with (WORK/'decode.log').open('w') as log:
            subprocess.run([str(FFMPEG),'-v','error','-xerror','-nostdin','-i',str(MOVIE),'-an','-f','null','-'],stdout=log,stderr=subprocess.STDOUT,check=True)
        report.update(version=VERSION,movie_sha256=sha(MOVIE),translation_sha256=sha(TRANSLATION),
            video_decode_verified=True,original_movie_sha256=sha(SOURCE),runtime_verified=False)
        (WORK/'movie_validation.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report),flush=True)
    if not args.write:return
    require(MOVIE.exists(),'Run --prepare first')
    report=json.loads((WORK/'movie_validation.json').read_text())
    require(report['movie_sha256']==sha(MOVIE),'Movie changed after verification')
    require(report['translation_sha256']==sha(TRANSLATION),'Lyrics changed after encode')
    verify_movie(original,MOVIE.read_bytes())
    require(not OUTPUT.exists(),'Output already exists')
    shutil.copyfile(BASE,OUTPUT)
    with OUTPUT.open('r+b') as f,MOVIE.open('rb') as m:
        f.seek(entry['offset']);shutil.copyfileobj(m,f,CHUNK)
    digest=hashlib.sha256();pos=0;start=entry['offset'];end=start+entry['size']
    with BASE.open('rb') as b,OUTPUT.open('rb') as f,MOVIE.open('rb') as m:
        while True:
            before=b.read(CHUNK);after=f.read(CHUNK)
            if not after:break
            require(len(before)==len(after),'Disc size changed')
            expected=bytearray(before);lo=max(pos,start);hi=min(pos+len(after),end)
            if lo<hi:
                m.seek(lo-start);expected[lo-pos:hi-pos]=m.read(hi-lo)
            require(expected==after,'Unexpected disc difference at '+str(pos))
            digest.update(after);pos+=len(after)
    report.update(base=BASE.name,output=OUTPUT.name,sha256=digest.hexdigest(),size=pos,
        replaced_file=NAME,whole_disc_verified=True,approved_lyrics_preview='0.1.58',published=False)
    OUTPUT.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
