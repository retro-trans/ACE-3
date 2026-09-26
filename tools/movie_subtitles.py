"""Preview render: English subtitles over the burned-in Japanese ones in the opening movie (MOVIE002.PSS).

Writes the .ass subtitle script and prints the ffmpeg command for the MP4 preview. The same .ass file feeds
the in-game MPEG-2 encode (see docs/MOVIE_SUBTITLES.md and tools/pss_remux.py). It does not touch the disc.
Timings come from tools/movie_subtitle_scan.py; English comes from the reviewed scene batch, matched to each
burned-in line by reading the rendered strips (work/build/movie_test/MOVIE002_segments/sheet.png).
usage: python movie_subtitles.py            (writes the .ass file and prints the ffmpeg command)
"""
import json
import re
from build_ui_patch import ROOT

WORK = ROOT/'work/build/movie_test'
BATCH = ROOT/'work/translation/en/dialogue/batch_scene_2002410.json'
# Segment number -> game text IDs shown in it. The movie plays the lines in its own order, skips the
# interjections, merges 349+350 into one subtitle and uses take 354 of the two stored replies.
SEGMENT_IDS = {1:[301], 2:[302], 3:[303], 4:[304], 5:[306], 6:[307], 7:[308], 8:[309], 9:[310], 10:[361], 11:[312],
               12:[362], 13:[360], 14:[314], 15:[315], 16:[316], 17:[317], 18:[320], 19:[321], 20:[323], 21:[326],
               22:[329], 23:[343], 24:[332], 25:[330], 26:[331], 27:[349, 350], 28:[351], 29:[352], 30:[354],
               31:[355], 32:[356], 33:[357], 34:[358]}
# The date caption is drawn inside the picture, not the letterbox: wipes in at 29.0 s, fades by 33.2 s.
CAPTION = {'start':29.0, 'end':33.2, 'text':'Unified Calendar 060, January - Saint Cruz City', 'box':(286, 303, 352, 26)}
TAG = re.compile(r'<[^<>]*>')


def stamp(seconds):
    h, rest = divmod(seconds, 3600); m, s = divmod(rest, 60)
    return '%d:%02d:%05.2f' % (h, m, s)


def main():
    segments = json.loads((WORK/'MOVIE002_segments/segments.json').read_text(encoding='utf-8'))
    body = {r['text_id']:TAG.sub('', r['target']) for r in json.loads(BATCH.read_text(encoding='utf-8'))['rows']}
    assert len(segments) == len(SEGMENT_IDS) == 34
    lines = ['[Script Info]', 'ScriptType: v4.00+', 'PlayResX: 640', 'PlayResY: 448', 'ScaledBorderAndShadow: yes', '',
             '[V4+ Styles]',
             'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
             # 14:15 pixels are narrower than square ones, so glyphs are widened slightly to keep their shape.
             'Style: Sub,Georgia,19,&H00FFFFFF,&H00FFFFFF,&H00101010,&H00000000,1,0,0,0,107,100,0.4,0,1,0.6,0,7,0,0,0,1',
             'Style: Cap,Georgia,14,&H00FFFFFF,&H00FFFFFF,&H00101010,&H00000000,0,0,0,0,107,100,0.2,0,1,0.6,0,7,0,0,0,1', '',
             '[Events]', 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
    report = []
    for s in segments:
        text = '\n'.join(body[i] for i in SEGMENT_IDS[s['n']])
        # Same anchor as the burned-in text: left edge x=139, first line top y=378.
        lines.append('Dialogue: 0,%s,%s,Sub,,0,0,0,,{\\pos(139,376)}%s' % (stamp(s['start']), stamp(s['end']), text.replace('\n', '\\N')))
        report.append({'segment':s['n'], 'start':s['start'], 'end':s['end'], 'text_ids':SEGMENT_IDS[s['n']], 'en':text})
    x, y, w, h = CAPTION['box']
    lines.append('Dialogue: 1,%s,%s,Cap,,0,0,0,,{\\pos(%d,%d)\\fad(300,500)}%s' % (stamp(CAPTION['start']), stamp(CAPTION['end']), x+6, y+6, CAPTION['text']))
    (WORK/'MOVIE002_en.ass').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    (WORK/'MOVIE002_en.json').write_text(json.dumps({'movie':'/MOVIE0/MOVIE002.PSS', 'caption':CAPTION, 'subtitles':report}, indent=1)+'\n', encoding='utf-8')
    # 1. black out the letterbox band that carries the Japanese text (it is pure black under the picture);
    # 2. darken the in-picture caption while it shows; 3. draw the English.
    vf = ("drawbox=x=0:y=356:w=640:h=92:color=black:t=fill,"
          "drawbox=x=%d:y=%d:w=%d:h=%d:color=black@0.78:t=fill:enable='between(t,%.2f,%.2f)',"
          "ass=MOVIE002_en.ass" % (x, y, w, h, CAPTION['start'], CAPTION['end']))
    print('cd "%s"' % WORK)
    print('ffmpeg -i MOVIE002.PSS -i MOVIE002.wav -vf "%s" -c:v libx264 -crf 17 -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k -shortest MOVIE002_en_preview.mp4' % vf)


if __name__ == '__main__': main()
