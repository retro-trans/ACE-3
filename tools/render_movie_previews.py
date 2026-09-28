"""0.1.55 movie review MP4s. Preview-only: no ISO/PSS writes or patch creation.

Dry-run creates nothing. --write renders English captions with original audio.
Run with the project's Pillow-enabled Python. FFmpeg is isolated in work/local.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.1.55-preview'
SOURCE = ROOT/'work/build/movie_test'
WORK = ROOT/'work/build/movie_previews_055'
TRANSLATIONS = ROOT/'work/translation/en/movies_055'
OUTPUT = ROOT/'work/output/0.1.55-movie-previews'
FFMPEG = ROOT/'work/local/movie-python/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
FONT_PATH = 'C:/Windows/Fonts/georgia.ttf'
STARTS = {'MOVIE001':0.045966667, 'MOVIE003':0.047055556, 'MOVIE004':0.044333333,
          'MOVIE005':0.045311111, 'MOVIE006':0.045966667}


def stamp(t, srt=False):
    ms = round(t*1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    sec, ms = divmod(ms, 1000)
    return ('%02d:%02d:%02d,%03d' % (h,m,sec,ms)) if srt else '%d:%02d:%02d.%02d' % (h,m,sec,ms//10)


def wrap(text, size=18, limit=492):
    font = ImageFont.truetype(FONT_PATH, size)
    lines = []
    for word in text.split():
        if lines and font.getlength(lines[-1]+' '+word) <= limit:
            lines[-1] += ' '+word
        else:
            lines.append(word)
    if ' '.join(lines) != text or len(lines) > 2 or any(font.getlength(x)>limit for x in lines):
        raise ValueError('Subtitle will not fit: '+text)
    return lines


def plan(name):
    path = TRANSLATIONS/(name+'.json')
    doc = json.loads(path.read_text(encoding='utf-8'))
    allowed = ('meaning_reviewed', 'meaning_reviewed_with_speaker_uncertainty')
    if name == 'MOVIE001':
        allowed += ('lyric_draft_with_uncertainties', 'user_lyrics_meaning_reviewed')
    if doc['review']['status'] not in allowed:
        raise ValueError('Unreviewed translation: '+name)
    segments = {s['n']:s for s in json.loads((SOURCE/(name+'_segments')/'segments.json').read_text())}
    rows = []
    for entry in doc['subtitles']:
        row = dict(entry)
        if 'start' not in row:
            selected = [segments[n] for n in row['source_segments']]
            row['start'] = max(0, min(s['start'] for s in selected)-STARTS[name])
            row['end'] = max(s['end'] for s in selected)-STARTS[name]
        elif doc.get('timebase') == 'source_video_pts':
            row['start'] = max(0,row['start']-STARTS[name])
            row['end'] -= STARTS[name]
        row['lines'] = wrap(row['text'], limit=604 if name == 'MOVIE001' else 492)
        if name == 'MOVIE001':
            row['romaji_lines'] = wrap(row['romaji'], size=17, limit=604)
            if len(row['lines']) > 1 or len(row['romaji_lines']) > 1:
                raise ValueError('Split lyric into shorter timed phrases: '+row['text'])
        if row['start'] >= row['end'] or row['start'] < 0:
            raise ValueError('Bad timing')
        rows.append(row)
    if any(a['end'] > b['start']+0.001 for a,b in zip(rows,rows[1:])):
        raise ValueError('Overlapping subtitles')
    return doc, rows


def scripts(name, rows, review):
    if name == 'MOVIE001':
        return lyric_scripts(rows, review)
    ass = ['[Script Info]', 'ScriptType: v4.00+', 'PlayResX: 640', 'PlayResY: 448',
           'ScaledBorderAndShadow: yes', '', '[V4+ Styles]',
           'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
           'Style: Speaker,Georgia,14,&H00FFFFFF,&H00FFFFFF,&H00101010,&H00000000,0,0,0,0,100,100,0,0,1,0.5,0,7,0,0,0,1',
           'Style: Dialogue,Georgia,18,&H00FFFFFF,&H00FFFFFF,&H00101010,&H00000000,0,0,0,0,100,100,0,0,1,0.5,0,7,0,0,0,1',
           '', '[Events]', 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
    srt = []
    for n,row in enumerate(rows,1):
        start,end = stamp(row['start']),stamp(row['end'])
        if row.get('speaker'):
            ass.append('Dialogue: 0,%s,%s,Speaker,,0,0,0,,{\\pos(112,358)}%s' % (start,end,row['speaker']))
        ass.append('Dialogue: 0,%s,%s,Dialogue,,0,0,0,,{\\pos(124,380)\\q2}%s' % (start,end,'\\N'.join(row['lines'])))
        srt.extend([str(n),stamp(row['start'],True)+' --> '+stamp(row['end'],True),
                    (row.get('speaker','')+': ' if row.get('speaker') else '')+row['text'],''])
    return '\n'.join(ass)+'\n','\n'.join(srt)


def lyric_scripts(rows, review):
    # The complete 960x720 picture sits above a new 144-pixel subtitle band.
    ass = ['[Script Info]', 'ScriptType: v4.00+', 'PlayResX: 960', 'PlayResY: 864',
           'ScaledBorderAndShadow: yes', '', '[V4+ Styles]',
           'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
           'Style: Romaji,Georgia,25.5,&H008EDDF5,&H00FFFFFF,&H00101010,&H00000000,0,0,0,0,100,100,0,0,1,0.5,0,8,0,0,0,1',
           'Style: English,Georgia,27,&H00FFFFFF,&H00FFFFFF,&H00101010,&H00000000,0,0,0,0,100,100,0,0,1,0.5,0,8,0,0,0,1',
           'Style: Note,Arial,16,&H00AAAAAA,&H00FFFFFF,&H00101010,&H00000000,0,0,0,0,100,100,0,0,1,0,0,8,0,0,0,1',
           '', '[Events]', 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text',
           'Dialogue: 0,0:00:00.00,0:02:46.00,Note,,0,0,0,,{\\pos(480,839)}'+review.get('display_note', 'LYRIC REVIEW DRAFT - uncertain passages are marked')]
    events = [dict(row) for row in rows]
    for span in review.get('unresolved_spans', []):
        if any(span['start'] < row['end'] and span['end'] > row['start'] for row in rows):
            raise ValueError('Unresolved span overlaps a lyric')
        events.append(dict(start=span['start'], end=span['end'],
                           romaji='[romaji pending]', text='[Unclear lyric - needs review]'))
    srt = []
    for n,row in enumerate(sorted(events,key=lambda r:r['start']),1):
        start,end = stamp(row['start']),stamp(row['end'])
        ass.append('Dialogue: 0,%s,%s,Romaji,,0,0,0,,{\\pos(480,742)\\q2}%s' % (start,end,row['romaji']))
        ass.append('Dialogue: 0,%s,%s,English,,0,0,0,,{\\pos(480,783)\\q2}%s' % (start,end,row['text']))
        srt.extend([str(n),stamp(row['start'],True)+' --> '+stamp(row['end'],True),row['romaji'],row['text'],''])
    return '\n'.join(ass)+'\n','\n'.join(srt)


def main():
    global OUTPUT, TRANSLATIONS, VERSION
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--movies', nargs='+', default=['MOVIE001','MOVIE003','MOVIE004','MOVIE005','MOVIE006'])
    ap.add_argument('--output', type=Path, default=OUTPUT)
    ap.add_argument('--translations', type=Path, default=TRANSLATIONS)
    ap.add_argument('--version', default=VERSION)
    args = ap.parse_args()
    OUTPUT, TRANSLATIONS, VERSION = args.output.resolve(), args.translations.resolve(), args.version
    plans = []
    for name in args.movies:
        doc,rows = plan(name)
        print('PREVIEW', name, len(rows), 'English cues', flush=True)
        for row in rows[:2]: print(json.dumps(row),flush=True)
        plans.append((name,doc,rows))
    if not args.write:
        return
    OUTPUT.mkdir(parents=True,exist_ok=True)
    for name,doc,rows in plans:
        target = OUTPUT/(name+'_English_preview.mp4')
        if target.exists(): raise ValueError('Preview exists: '+str(target))
        ass,srt = scripts(name,rows,doc['review'])
        (OUTPUT/(name+'_English.ass')).write_text(ass,encoding='utf-8')
        (OUTPUT/(name+'_English.srt')).write_text(srt,encoding='utf-8')
        subtitle_filter = ',drawbox=x=0:y=352:w=640:h=96:color=black:t=fill,ass='+name+'_English.ass' if rows else ''
        filters = 'setpts=PTS-STARTPTS'+subtitle_filter+',scale=960:720:flags=lanczos,setsar=1'
        if name == 'MOVIE001':
            filters = 'setpts=PTS-STARTPTS,scale=960:720:flags=lanczos,setsar=1,pad=960:864:0:0:black,ass='+name+'_English.ass'
        cmd=[str(FFMPEG),'-hide_banner','-nostdin','-i',str(SOURCE/(name+'.PSS')),
             '-i',str(WORK/(name+'.wav')),'-map','0:v:0','-map','1:a:0','-vf',filters,
             '-c:v','libx264','-threads','4','-preset','medium','-crf','18','-pix_fmt','yuv420p',
             '-c:a','aac','-b:a','192k','-movflags','+faststart','-shortest',str(target)]
        with (OUTPUT/(name+'_render.log')).open('w',encoding='utf-8') as log:
            subprocess.run(cmd,cwd=str(OUTPUT),stdout=log,stderr=subprocess.STDOUT,check=True)
        report=dict(version=VERSION,movie=name,preview=target.name,cues=len(rows),
                    subtitle_rows=rows,source_sha256=hashlib.sha256((SOURCE/(name+'.PSS')).read_bytes()).hexdigest(),
                    preview_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),bytes=target.stat().st_size,
                    review=doc['review'],patched_into_game=False,user_approved=False)
        (OUTPUT/(name+'_validation.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print('RENDERED',target,flush=True)


if __name__ == '__main__':
    main()
