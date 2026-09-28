"""Render a user-supplied MP3 with reviewed romaji/English lyric captions.

Dry-run by default. Produces a review MP4 and editable bilingual ASS/SRT;
does not alter a game image. Run with the project's Pillow-enabled Python.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
FFMPEG = ROOT/'work/local/movie-python/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
FONT = 'C:/Windows/Fonts/georgia.ttf'


def stamp(value, srt=False):
    ms = round(value*1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return ('%02d:%02d:%02d,%03d' % (h,m,s,ms)) if srt else '%d:%02d:%02d.%02d' % (h,m,s,ms//10)


def wrap(text, size):
    font = ImageFont.truetype(FONT, size)
    lines = []
    for word in text.split():
        if lines and font.getlength(lines[-1]+' '+word) <= 1120:
            lines[-1] += ' '+word
        else:
            lines.append(word)
    if len(lines)>2 or any(font.getlength(line)>1120 for line in lines):
        raise ValueError('Split caption into shorter phrases: '+text)
    if any(c in text for c in '{}\\'):
        raise ValueError('Unsupported subtitle control character')
    return lines


def scripts(doc):
    duration = doc['duration']
    rows = doc['subtitles']
    last = 0
    for row in rows:
        if not last <= row['start'] < row['end'] <= duration:
            raise ValueError('Invalid/overlapping subtitle timing')
        row['romaji_lines'] = wrap(row['romaji'], 43)
        row['english_lines'] = wrap(row['text'], 37)
        last = row['end']
    ass = ['[Script Info]', 'ScriptType: v4.00+', 'PlayResX: 1280', 'PlayResY: 720',
           'ScaledBorderAndShadow: yes', '', '[V4+ Styles]',
           'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
           'Style: Label,Arial,18,&H00C0A778,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,0,0,7,0,0,0,1',
           'Style: Title,Georgia,51,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1',
           'Style: Romaji,Georgia,43,&H009EE6F5,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,8,0,0,0,1',
           'Style: English,Georgia,37,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,8,0,0,0,1',
           'Style: Note,Arial,20,&H00B4A59A,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,8,0,0,0,1',
           'Style: Timer,Consolas,21,&H00B4A59A,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,9,0,0,0,1',
           '', '[Events]', 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
    def event(start,end,style,x,y,text):
        ass.append('Dialogue: 0,%s,%s,%s,,0,0,0,,{\\pos(%s,%s)\\q2}%s' % (stamp(start),stamp(end),style,x,y,text))
    event(0,duration,'Label',64,45,'ACE 3  /  ENDING SONG')
    event(0,duration,'Title',64,85,doc['title'])
    event(0,duration,'Label',65,156,'ROMAJI + ENGLISH')
    event(0,duration,'Note',640,672,'Whisper lyric review  |  '+doc['version']+'  |  Preview only')
    for second in range(int(duration)+1):
        total=round(duration)
        event(second,min(second+1,duration),'Timer',1216,156,
              '%02d:%02d / %02d:%02d' % (second//60,second%60,total//60,total%60))
    srt=[]
    cursor=0
    for i,row in enumerate(rows,1):
        if row['start']-cursor >= 4:
            event(cursor,row['start'],'Note',640,335,'[Music]')
        start,end=row['start'],row['end']
        event(start,end,'Romaji',640,276,'\\N'.join(row['romaji_lines']))
        event(start,end,'English',640,395,'\\N'.join(row['english_lines']))
        if row.get('uncertain'):
            note=row.get('uncertainty_note','Wording uncertain - please check against the singing')
            event(start,end,'Note',640,515,note)
        srt.extend([str(i),stamp(start,True)+' --> '+stamp(end,True),row['romaji'],row['text'],
                    '[Wording uncertain]' if row.get('uncertain') else '', ''])
        cursor=end
    if duration-cursor >=4:
        event(cursor,duration,'Note',640,335,'[Music]')
    return '\n'.join(ass)+'\n','\n'.join(srt)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('audio',type=Path)
    ap.add_argument('translation',type=Path)
    ap.add_argument('output',type=Path)
    ap.add_argument('--write',action='store_true')
    args=ap.parse_args()
    doc=json.loads(args.translation.read_text(encoding='utf-8'))
    if doc['review']['status'] not in ('meaning_reviewed','meaning_reviewed_with_uncertainties'):
        raise ValueError('Independent meaning review required')
    source_sha=hashlib.sha256(args.audio.read_bytes()).hexdigest()
    if source_sha != doc['source_sha256']:
        raise ValueError('Audio differs from transcription source')
    ass,srt=scripts(doc)
    out=args.output.resolve()
    target=out/'Ending_Song_Romaji_English_preview.mp4'
    if target.exists():
        raise ValueError('Refusing to overwrite preview')
    print(json.dumps(dict(version=doc['version'],duration=doc['duration'],cues=len(doc['subtitles']),
        output=str(target),sample=doc['subtitles'][:2],write=args.write)),flush=True)
    if not args.write:
        return
    out.mkdir(parents=True,exist_ok=True)
    (out/'Ending_Song.ass').write_text(ass,encoding='utf-8')
    (out/'Ending_Song.srt').write_text(srt,encoding='utf-8')
    graph=('[0:a]showwaves=s=1152x44:mode=line:rate=24:colors=0x43B7CA:scale=sqrt[wave];'
        '[1:v]drawbox=x=64:y=210:w=1152:h=1:color=0x2D4658:t=fill[bg];'
        '[bg][wave]overlay=64:582:shortest=1,ass=Ending_Song.ass[v]')
    cmd=[str(FFMPEG),'-hide_banner','-nostdin','-i',str(args.audio.resolve()),'-f','lavfi','-i',
         'color=c=0x0C1929:s=1280x720:r=24','-filter_complex_threads','2','-filter_complex',graph,
         '-map','[v]','-map','0:a:0','-t',str(doc['duration']),'-c:v','libx264','-threads','4',
         '-preset','fast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k',
         '-movflags','+faststart',str(target)]
    with (out/'render.log').open('w',encoding='utf-8') as log:
        subprocess.run(cmd,cwd=str(out),stdout=log,stderr=subprocess.STDOUT,check=True)
    with (out/'decode.log').open('w',encoding='utf-8') as log:
        subprocess.run([str(FFMPEG),'-v','error','-xerror','-i',str(target),'-f','null','-'],
                       stdout=log,stderr=subprocess.STDOUT,check=True)
    report=dict(version=doc['version'],duration=doc['duration'],cues=len(doc['subtitles']),
        preview_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),bytes=target.stat().st_size,
        source_sha256=source_sha,translation_sha256=hashlib.sha256(args.translation.read_bytes()).hexdigest(),
        audio_video_decode_verified=True,review=doc['review'],patched_into_game=False,user_approved=False)
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('RENDERED',target,flush=True)


if __name__=='__main__':
    main()
