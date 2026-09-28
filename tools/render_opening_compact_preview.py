"""0.1.63 opening lyric layout preview; never changes the game or PSS."""
import argparse
import json
import subprocess
from PIL import ImageFont
from build_opening_song_patch import SOURCE, TRANSLATION, FFMPEG, sha, subtitles
from build_ui_patch import ROOT, require

VERSION = '0.1.63-preview'
OUTPUT = ROOT/'work/output/0.1.63-opening-preview'
AUDIO = ROOT/'work/build/movie_previews_055/MOVIE001.wav'
TARGET = OUTPUT/'Opening_compact_subtitles.mp4'


def plan():
    ass, count = subtitles()
    replacements = {
        'Style: Romaji,Georgia,15,': 'Style: Romaji,Georgia,14,',
        'Style: English,Georgia,16,': 'Style: English,Georgia,15,',
        ',1,0.5,0,8,0,0,0,1': ',1,1.2,0.4,8,0,0,0,1',
        r'\pos(320,382)': r'\pos(320,390)',
    }
    for before, after in replacements.items():
        require(before in ass, 'Opening style preimage')
        ass = ass.replace(before, after)
    rows = json.loads(TRANSLATION.read_text(encoding='utf-8'))['subtitles']
    widths = []
    for row in rows:
        for field,size in [('romaji',14),('text',15)]:
            width = ImageFont.truetype('C:/Windows/Fonts/georgia.ttf',size).getlength(row[field])*1.07
            require(width <= 572, 'Caption exceeds picture safe width')
            widths.append(width)
    return ass, dict(version=VERSION,cues=count,preview_frame=[960,720],
                     native_frame=[640,448],picture='Full original picture, no added subtitle band or crop',
                     romaji=dict(font_size=14,top=390),english=dict(font_size=15,top=408),
                     line_spacing=18,max_text_width=max(widths),
                     wording_and_timing='Unchanged from approved opening 0.1.59',
                     patched_into_game=False,user_approved=False)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true')
    args=ap.parse_args()
    ass,report=plan()
    print('DRY RUN: compact bilingual captions inside opening CG',flush=True)
    print(json.dumps(report,indent=2),flush=True)
    if not args.write:return
    require(not TARGET.exists(),'Preview already exists')
    OUTPUT.mkdir(parents=True,exist_ok=True)
    (OUTPUT/'opening.ass').write_text(ass,encoding='utf-8')
    cmd=[str(FFMPEG),'-hide_banner','-nostdin','-i',str(SOURCE),'-i',str(AUDIO),
         '-map','0:v:0','-map','1:a:0','-vf',
         'setpts=PTS-STARTPTS,ass=opening.ass,scale=960:720:flags=lanczos,setsar=1',
         '-c:v','libx264','-threads','2','-preset','medium','-crf','18','-pix_fmt','yuv420p',
         '-c:a','aac','-b:a','192k','-movflags','+faststart','-shortest',str(TARGET)]
    with (OUTPUT/'render.log').open('w',encoding='utf-8') as log:
        subprocess.run(cmd,cwd=str(OUTPUT),stdout=log,stderr=subprocess.STDOUT,check=True)
    with (OUTPUT/'decode.log').open('w',encoding='utf-8') as log:
        subprocess.run([str(FFMPEG),'-hide_banner','-nostdin','-v','error','-xerror',
                        '-i',str(TARGET),'-f','null','-'],stdout=log,stderr=subprocess.STDOUT,check=True)
    for seconds in [65,85,125]:
        subprocess.run([str(FFMPEG),'-hide_banner','-nostdin','-v','error','-ss',str(seconds),
                        '-i',str(TARGET),'-frames:v','1',str(OUTPUT/('sample_%d.png'%seconds))],check=True)
    report.update(preview=TARGET.name,preview_sha256=sha(TARGET),source_sha256=sha(SOURCE),
                  translation_sha256=sha(TRANSLATION),full_audio_video_decode_passed=True,
                  bytes=TARGET.stat().st_size)
    (OUTPUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('RENDERED',TARGET,flush=True)


if __name__=='__main__':main()
