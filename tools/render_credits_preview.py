"""Render the 0.1.57 credits review MP4. Dry-run by default; never patches the game."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import ImageFont
from render_movie_previews import stamp

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'work/translation/en/credits_057.json'
OUTPUT = ROOT / 'work/output/0.1.57-credits-preview'
FFMPEG = ROOT / 'work/local/movie-python/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    doc = json.loads(DOC.read_text(encoding='utf-8'))
    source = next((ROOT / 'work/local/credits_057/profile/videos').glob('*.mp4'))
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 20)
    rows = doc['subtitles']
    previous = 0
    for row in rows:
        if not 0 <= previous <= row['start'] < row['end'] <= 356.5:
            raise ValueError('Invalid timing: '+str(row))
        previous = row['end']
        text = row['text'] or '[Unclear dialogue - needs review]'
        lines = []
        for word in text.split():
            if lines and font.getlength(lines[-1]+' '+word) <= 600:
                lines[-1] += ' '+word
            else:
                lines.append(word)
        if len(lines) > 2 or any(font.getlength(x) > 600 for x in lines):
            raise ValueError('Split long cue: '+text)
        row['lines'] = lines
    print('PREVIEW',len(rows),'cues',str(source),flush=True)
    for row in rows[:4]:
        print(json.dumps(row),flush=True)
    if not args.write:
        return
    OUTPUT.mkdir(parents=True,exist_ok=True)
    target = OUTPUT / 'Credits_English_preview.mp4'
    if target.exists():
        raise ValueError('Preview already exists')
    ass = ['[Script Info]','ScriptType: v4.00+','PlayResX: 640','PlayResY: 576',
        'ScaledBorderAndShadow: yes','','[V4+ Styles]',
        'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
        'Style: English,Arial,20,&H00FFFFFF,&H00FFFFFF,&H00101010,&H00000000,0,0,0,0,100,100,0,0,1,0.5,0,8,0,0,0,1',
        'Style: Note,Arial,11,&H00AAAAAA,&H00FFFFFF,&H00101010,&H00000000,0,0,0,0,100,100,0,0,1,0,0,8,0,0,0,1',
        '','[Events]','Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text',
        'Dialogue: 0,0:00:00.00,0:05:56.44,Note,,0,0,0,,{\\pos(320,558)}CREDITS TRANSLATION REVIEW - 0.1.57']
    srt=[]
    for n,row in enumerate(rows,1):
        ass.append('Dialogue: 0,%s,%s,English,,0,0,0,,{\\pos(320,497)\\q2}%s' %
            (stamp(row['start']),stamp(row['end']),'\\N'.join(row['lines'])))
        srt.extend([str(n),stamp(row['start'],True)+' --> '+stamp(row['end'],True),'\n'.join(row['lines']),''])
    (OUTPUT/'Credits_English.ass').write_text('\n'.join(ass)+'\n',encoding='utf-8')
    (OUTPUT/'Credits_English.srt').write_text('\n'.join(srt),encoding='utf-8')
    cmd = [str(FFMPEG),'-hide_banner','-nostdin','-i',str(source),'-map','0:v:0','-map','0:a:0',
        '-vf','scale=640:480,setsar=1,pad=640:576:0:0:black,ass=Credits_English.ass',
        '-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','copy',
        '-movflags','+faststart',str(target)]
    with (OUTPUT/'render.log').open('w',encoding='utf-8') as log:
        subprocess.run(cmd,cwd=str(OUTPUT),stdout=log,stderr=subprocess.STDOUT,check=True)
    with (OUTPUT/'decode.log').open('w',encoding='utf-8') as log:
        subprocess.run([str(FFMPEG),'-v','error','-xerror','-i',str(target),'-f','null','-'],stdout=log,stderr=subprocess.STDOUT,check=True)
    report = dict(version='0.1.57-preview',cues=len(rows),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        preview_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),decode_verified=True,
        review=doc['review'],patched_into_game=False,approved=False)
    (OUTPUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('RENDERED',target,flush=True)

if __name__ == '__main__':
    main()
