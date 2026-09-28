"""0.1.64: integrate approved compact opening preview. Dry-run, --prepare, --write."""
import argparse
import hashlib
import json
import subprocess
import sys

from build_opening_song_patch import SOURCE, TRANSLATION, FFMPEG, NAME, sha, verify_movie
from render_opening_compact_preview import plan as preview_plan, OUTPUT as PREVIEW
from build_ui_patch import ROOT, iso_files, require
from pss_remux import plan as remux
import build_stats_panel_patch as writer

VERSION = '0.1.64'
BASE = ROOT/'work/output/ACE3-English-0.1.62.iso'
OUTPUT = ROOT/('work/output/ACE3-English-'+VERSION+'.iso')
BASE_HASH = '8c6b1d425f9c797896bd441bb7dec9de971281934ed769f9720b9c033a689c9c'
SOURCE_HASH = 'be40a134137c9fb8d299dcb2e54b0f6c6d62b193b816aaa9226fc4b8810178e1'
WORK = ROOT/'work/build/opening_064'
MOVIE = WORK/'MOVIE001_en.PSS'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--prepare',action='store_true')
    ap.add_argument('--write',action='store_true')
    args=ap.parse_args()
    ass,layout=preview_plan()
    require(ass==(PREVIEW/'opening.ass').read_text(encoding='utf-8'), 'Approved preview layout changed')
    approval=json.loads((PREVIEW/'validation.json').read_text(encoding='utf-8'))
    require(sha(TRANSLATION)==approval['translation_sha256'],'Approved lyrics changed')
    require(sha(SOURCE)==SOURCE_HASH==approval['source_sha256'],'Original movie identity')
    original=SOURCE.read_bytes()
    with BASE.open('rb') as f:
        entry=iso_files(f)[NAME];f.seek(entry['offset']);current=f.read(entry['size'])
    verify_movie(original,current)
    ass_hash=hashlib.sha256(ass.encode('utf-8')).hexdigest()
    print(json.dumps(dict(version=VERSION,base=BASE.name,output=OUTPUT.name,
                          movie=NAME,cues=layout['cues'],approved_layout='0.1.63-preview',
                          picture=layout['picture'],romaji=layout['romaji'],english=layout['english'],
                          preserved='Original movie audio; ending dialogue and lyric holds from 0.1.62',
                          prepare=args.prepare,write=args.write),indent=2),flush=True)
    if args.prepare:
        require(not MOVIE.exists(),'Prepared movie already exists')
        WORK.mkdir(parents=True,exist_ok=True)
        (WORK/'opening.ass').write_text(ass,encoding='utf-8')
        es=WORK/'opening.m2v'
        require(not es.exists(),'Encoded video already exists')
        cmd=[str(FFMPEG),'-hide_banner','-nostdin','-i',str(SOURCE),'-an',
             '-vf','setpts=PTS-STARTPTS,ass=opening.ass',
             '-c:v','mpeg2video','-threads','2','-profile:v','4','-level:v','8','-pix_fmt','yuv420p',
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
            subprocess.run([str(FFMPEG),'-v','error','-xerror','-nostdin','-i',str(MOVIE),
                            '-an','-f','null','-'],stdout=log,stderr=subprocess.STDOUT,check=True)
        for seconds in [65,125]:
            subprocess.run([str(FFMPEG),'-hide_banner','-nostdin','-v','error','-ss',str(seconds),
                            '-i',str(MOVIE),'-vf','scale=960:720,setsar=1','-frames:v','1',
                            str(WORK/('sample_%d.png'%seconds))],check=True)
        report.update(version=VERSION,movie_sha256=sha(MOVIE),translation_sha256=sha(TRANSLATION),
                      ass_sha256=ass_hash,video_decode_verified=True,original_movie_sha256=SOURCE_HASH,
                      approved_layout='0.1.63-preview',layout=layout,runtime_verified=False)
        # The preview record remains historical; this build records the later approval.
        report['layout']=dict(layout,user_approved=True,patched_into_game=True)
        (WORK/'movie_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print('PREPARED',MOVIE,flush=True)
    if not args.write:return
    require(MOVIE.exists(),'Run --prepare first')
    report=json.loads((WORK/'movie_validation.json').read_text(encoding='utf-8'))
    require(report['movie_sha256']==sha(MOVIE),'Verified movie changed')
    require(report['ass_sha256']==ass_hash and report['translation_sha256']==sha(TRANSLATION),
            'Caption source changed after encode')
    patched=MOVIE.read_bytes()
    verify_movie(original,patched)
    edits=[dict(offset=entry['offset'],before=current,after=patched)]
    summary=dict(replaced_file=NAME,movie=report,published=False)
    writer.VERSION,writer.BASE,writer.OUTPUT,writer.BASE_HASH=VERSION,BASE,OUTPUT,BASE_HASH
    writer.plan=lambda:(edits,summary,None)
    sys.argv=[sys.argv[0],'--write']
    writer.main()


if __name__=='__main__':main()
