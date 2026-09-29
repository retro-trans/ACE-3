"""0.9.3: integrate the two reviewed story-movie subtitle previews.

Dry run by default. --prepare encodes/verifies PSS files; --write builds ISO.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from build_ui_patch import ROOT, require, iso_files
from build_opening_song_patch import sha, FFMPEG
from render_movie_previews import plan as subtitle_plan, scripts, SOURCE, OUTPUT as PREVIEWS, TRANSLATIONS
from pss_inspect import packets
from pss_remux import plan as remux
import build_stats_panel_patch as writer

VERSION = '0.9.3'
BASE = ROOT/'work/output/ACE3-English-0.9.2.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_HASH = '6096ff5e7e633a1ec13686f36ae38fdd8a8e5cc8a0fae05d2fb24724caf728aa'
WORK = ROOT/'work/build/movies_093'
SPECS = {
    'MOVIE003': dict(ticks=3003, rate='30000/1001', aspect='4:3', bitrate='3800k',
                     buffer='1835008', sha256='521f791e076ee813de0b3718476ecf7982138af5c2c1ee72fea8b826bbc24cdf', cues=48),
    'MOVIE006': dict(ticks=3000, rate='30', aspect='10:7', bitrate='4400k',
                     buffer='1572864', sha256='5bc12d45309db9f20d9481109aa897c9cb016a02e9b4254cdaf121db1fa486cd', cues=11),
}


def prepare(name, spec):
    source = SOURCE/(name+'.PSS')
    require(sha(source) == spec['sha256'], 'Source movie changed')
    doc, rows = subtitle_plan(name)
    require(len(rows) == spec['cues'], 'Subtitle coverage changed')
    ass, _ = scripts(name, rows, doc['review'])
    require(ass == (PREVIEWS/(name+'_English.ass')).read_text(encoding='utf-8'), 'Reviewed preview differs')
    out = WORK/(name+'_en.PSS')
    report_path = WORK/(name+'_validation.json')
    ass_hash = hashlib.sha256(ass.encode('utf-8')).hexdigest()
    if out.exists():
        record = json.loads(report_path.read_text(encoding='utf-8'))
        require(record['movie_sha256'] == sha(out) and record['ass_sha256'] == ass_hash,
                'Existing prepared movie differs')
        require(record['translation_sha256'] == sha(TRANSLATIONS/(name+'.json')), 'Translation changed')
        print('REUSE VERIFIED', name, flush=True)
        return
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK/(name+'.ass')).write_text(ass, encoding='utf-8')
    es = WORK/(name+'.m2v')
    require(not es.exists(), 'Unverified encoded stream already exists')
    cmd = [str(FFMPEG), '-hide_banner', '-nostdin', '-i', str(source), '-an',
           '-vf', 'setpts=PTS-STARTPTS,drawbox=x=0:y=352:w=640:h=96:color=black:t=fill,ass='+name+'.ass',
           '-c:v', 'mpeg2video', '-threads', '2', '-profile:v', '4', '-level:v', '8', '-pix_fmt', 'yuv420p',
           '-r', spec['rate'], '-aspect', spec['aspect'], '-b:v', spec['bitrate'],
           '-minrate', spec['bitrate'], '-maxrate', spec['bitrate'], '-bufsize', spec['buffer'],
           '-g', '18', '-bf', '2', '-sc_threshold', '0', '-dc', '8', '-mbd', 'rd',
           '-trellis', '2', '-cmp', '2', '-subcmp', '2', '-f', 'mpeg2video', str(es)]
    print('ENCODE', name, len(rows), 'subtitle cues', flush=True)
    with (WORK/(name+'_encode.log')).open('w') as log:
        subprocess.run(cmd, cwd=str(WORK), stdout=log, stderr=subprocess.STDOUT, check=True)
    original = source.read_bytes()
    patched, report = remux(original, es.read_bytes(), ticks=spec['ticks'], pace_to_original=True)
    require(report['pictures_original'] == report['pictures_new'], 'Frame count changed')
    require(len(original) == len(patched), 'Movie size changed')
    nonvideo = 0
    for at, sid, head, pay, plen, info in packets(original):
        if sid != 0xe0:
            require(original[at:pay+plen] == patched[at:pay+plen], 'Original audio/packet changed')
            nonvideo += 1
    pts = sorted(info['pts'] for at, sid, head, pay, plen, info in packets(patched)
                 if sid == 0xe0 and info.get('pts') is not None)
    require(len(pts) == len(set(pts)) == report['pictures_new'], 'Picture timestamps incomplete')
    require(all(b-a == spec['ticks'] for a,b in zip(pts,pts[1:])), 'Frame timing changed')
    out.write_bytes(patched)
    del original, patched
    with (WORK/(name+'_decode.log')).open('w') as log:
        subprocess.run([str(FFMPEG), '-v', 'error', '-xerror', '-nostdin', '-i', str(out),
                        '-an', '-f', 'null', '-'], stdout=log, stderr=subprocess.STDOUT, check=True)
    for seconds in ([12, 80, 170] if name == 'MOVIE003' else [2, 20, 54]):
        subprocess.run([str(FFMPEG), '-v', 'error', '-nostdin', '-ss', str(seconds), '-i', str(out),
                        '-frames:v', '1', '-vf', 'scale=960:720,setsar=1',
                        str(WORK/(name+'_%d.png'%seconds))], check=True)
    report.update(version=VERSION, movie=name, cues=len(rows), source_sha256=spec['sha256'],
                  movie_sha256=sha(out), ass_sha256=ass_hash, original_audio_preserved=True,
                  translation_sha256=sha(TRANSLATIONS/(name+'.json')),
                  nonvideo_packets_verified=nonvideo, decode_verified=True,
                  layout_matches_reviewed_preview=True, runtime_verified=False)
    report_path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('PREPARED', name, json.dumps(report), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--prepare', action='store_true')
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    for name, spec in SPECS.items():
        doc, rows = subtitle_plan(name)
        print('PLAN', name, len(rows), 'cues', spec['rate'], 'fps', flush=True)
        if args.prepare:
            prepare(name, spec)
    if not args.write:
        return
    edits, reports = [], []
    with BASE.open('rb') as f:
        files = iso_files(f)
        for name, spec in SPECS.items():
            out = WORK/(name+'_en.PSS')
            report = json.loads((WORK/(name+'_validation.json')).read_text(encoding='utf-8'))
            require(report['decode_verified'] and sha(out) == report['movie_sha256'], 'Unverified PSS')
            require(sha(TRANSLATIONS/(name+'.json')) == report['translation_sha256'], 'Translation changed')
            doc, rows = subtitle_plan(name)
            ass = scripts(name, rows, doc['review'])[0]
            require(hashlib.sha256(ass.encode('utf-8')).hexdigest() == report['ass_sha256'], 'Subtitle layout changed')
            entry = files['/MOVIE0/'+name+'.PSS']
            f.seek(entry['offset'])
            before, after = f.read(entry['size']), out.read_bytes()
            require(hashlib.sha256(before).hexdigest() == spec['sha256'], 'Disc movie preimage')
            require(len(before) == len(after), 'Movie extent changed')
            edits.append(dict(offset=entry['offset'], before=before, after=after))
            reports.append(report)
    edits.sort(key=lambda e: e['offset'])
    writer.VERSION, writer.BASE, writer.OUTPUT, writer.BASE_HASH = VERSION, BASE, OUTPUT, BASE_HASH
    writer.plan = lambda: (edits, dict(movies=reports, runtime_verified=False), None)
    sys.argv = [sys.argv[0], '--write']
    writer.main()


if __name__ == '__main__':
    main()
