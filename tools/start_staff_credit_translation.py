"""Create a source-hashed English staff-roll draft; never modify the game.

Original Japanese remains on the user's disc. Preserve rows and graphics tags;
leave personal-name readings unresolved unless matched to a credit reference.
"""
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont
from build_ui_patch import ROOT
from dialogue_corpus import archive, parse_table
from build_history_patch import chunks
from build_flight_save_patch import parts

BASE=ROOT/'work/output/ACE3-English-0.9.9.iso'
OUTPUT=ROOT/'work/translation/en/staff_credits.json'
REFERENCE='https://www.mobygames.com/game/59035/another-centurys-episode-3-the-final/credits/ps2/'
# Independently translated role labels, anchored to the disc's original IDs.
LABELS={
6:"Another Century's Episode 3",7:'THE FINAL',9:'Staff',
29:'Director',36:'Programming Director',43:'Graphics Director',50:'CG Director',57:'Sound Director',
68:'Programmers',81:'Game Designers',94:'3D Graphics Designers',113:'2D Graphics Designers',128:'Designers',
137:'Sound',156:'CG Designers',173:'Assistants',175:'Event Scripting',182:'Character Logic',189:'Design Assistant',
200:'Development Management',202:'Product Support Manager',207:'QA Staff',214:'Debugging',216:'Testers',
251:'A.C.E. Original Mecha Design',260:'Design Assistance',271:'A.C.E. Original Character Design',
284:'Falguen Custom Design',295:'Scenario',297:'Original Concept',305:'Scenario Writing',
322:'Satellite Imagery',332:'CG Assets',334:'3D ENCICLOPEDIA BY',335:'DE ESPONA Infografica TM',
351:'Theme Song',353:'Shinku',356:'Lyrics',358:'Music',360:'Arrangement',362:'Vocals',
368:'Ending Song',370:'Ai no Uta',373:'Lyrics',375:'Music',377:'Arrangement',379:'Vocals',385:'Music Production Support',
388:'A&R Producer',398:'A&R Director',408:'Recording Director',418:'Artist Promotion',425:'Project Producer',
432:'Artist Manager',439:'Promotional Tie-In Coordination',459:'Voice Recording',461:'Voice Directors',
468:'Casting',475:'Recording Studio',486:'Cast',579:'Listed in Japanese Syllabary Order',
596:'Advertising, Publicity and Sales',615:'Design',619:'Support',627:'Supervision',652:'Special Thanks',
677:'Supporting Companies',699:'Producers',710:'Supervisor',717:'Executive Producers',737:'Development',755:'Published by'}
# Name readings matched against the indexed credit reference, not inferred
# from kanji. ASCII transliteration omits macrons for native font coverage.
NAMES={
31:'Yui Tanimura',38:'Yoshitaka Suzuki',45:'Tomoya Kawasaki',52:'Toshiyuki Suzuki',59:'Tsukasa Saitoh',
70:'Yusuke Ebata',72:'Kazuaki Ito',74:'Akira Sadoyama',76:'Yoshiaki Watanabe',
83:'Shigeto Hirai',85:'Hayato Taka',87:'Shinichiro Naito',89:'Nozomi Saito',
96:'Akihiro Hayano',98:'Suguru Ueda',100:'Kohkichi Takahashi',102:'Fuuta Kamei',104:'Takashi Matsuo',106:'Takayuki Sugimura',108:'Yoshihito Okada',
115:'Junichiro Ishino',117:'Tomoko Watanabe',119:'Naomi Maehara',121:'Rie Seki',123:'Reinu Takenaka',
130:'Masahiro Miki',132:'Akira Takimoto',139:'Yoshikazu Takayama',141:'Koichi Suenaga',143:'Ayako Minami',
145:'Yuki Ichiki',147:'Kota Hoshino',149:'Hideyuki Eto',151:'Yuji Takenouchi',
158:'Ikuko Matsui',160:'Shota Hirasawa',162:'Shigeru Maeda',164:'Koji Sugiyama',166:'Takayuki Ozawa',
204:'Yoshiyuki Ikeda',209:'Atsushi Miyamoto',
253:'Junya Ishigaki',255:'Takayuki Yanase',257:'Daisei Fujii (Layup)',262:'Fujiro',
273:'Shigenori Soejima (Atlus)',275:'Takuya Saito',286:'Kunio Okawara',
357:'Hiroki Nagase',359:'Hideki Yanagisawa',361:'Yuta Nakano',363:'Hitomi Shimatani',380:'Hitomi Shimatani'}
COMPANIES={168:'Shirogumi Inc.',235:'DIGITAL HEARTS Co., Ltd.',299:'Banpresto',300:'FromSoftware',
324:'(C) Japan Space Imaging Corporation',477:'MIT Studio',
679:'Sunrise Inc.',680:'Sotsu Co., Ltd.',681:'Big West Ad Co., Ltd.',682:'Rights Inn Inc.',
683:'Dynamic Planning Co., Ltd.',685:'Atlus Co., Ltd.',686:'Bandai Co., Ltd.',687:'PolyAssets United Inc.',
688:'Japan Space Imaging Corporation',689:'Shirogumi Inc.',690:'Edge Works Co., Ltd.',691:'DIGITAL HEARTS Co., Ltd.',
692:'Layup Co., Ltd.',693:'Artpresto Co., Ltd.',694:'Dimps Corporation'}


def main():
    with BASE.open('rb') as f:
        fi,entries=archive(f);_,size,offset,_=next(e for e in entries if e[3]==4350)
        f.seek(fi['offset']+offset);data=f.read(size)
    _,a,z=next(c for c in chunks(data) if c[0]==b'STUF');table=parts(data[a+16:z])[3]
    rows=[];seen=set()
    for slot,tid,_,raw in parse_table(table)[3]:
        if raw is None:continue
        text=raw.decode('cp932').strip()
        if not text:continue
        seen.add(tid)
        row=dict(text_id=tid,slot=slot,source_sha256=hashlib.sha256(raw).hexdigest())
        if text.startswith('<picture('):row.update(status='preserve_graphics_commands',target=text)
        elif tid in LABELS:row.update(status='translated_draft',kind='heading',target=LABELS[tid])
        elif tid in NAMES:row.update(status='reference_matched_draft',kind='person',target=NAMES[tid],reference=REFERENCE)
        elif tid in COMPANIES:row.update(status='translated_draft',kind='organization',target=COMPANIES[tid])
        elif text.isascii():row.update(status='retain_existing',target=text)
        else:row.update(status='name_verification_pending',kind='person',target=None)
        rows.append(row)
    assert set(LABELS)|set(NAMES)|set(COMPANIES)<=seen
    counts={s:sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})}
    doc=dict(schema='ace3-staff-credits-draft-v1',base=BASE.name,resource=4350,chunk='STUF',table=3,
             source_table_sha256=hashlib.sha256(table).hexdigest(),status='translation_in_progress_not_integrated',
             source_of_roles='Original user-owned disc credits',name_reference=REFERENCE,
             reference_checked='2026-10-01',counts=counts,
             notes=['Keep row order, blank rows, picture commands and roll timing when integrating.',
                    'Recenter translated lines using measured widths; do not reuse Japanese indentation.',
                    'Names with uncertain readings remain pending; no placeholder names should enter the game.',
                    'Song-title color commands must be retained when applying targets.',
                    'The staff font currently lacks full ASCII coverage; complete and test it before integration.',
                    'Reference contains a surname/given-name discrepancy at text ID 659; verify against the disc and another source.'],rows=rows)
    OUTPUT.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
    folder=ROOT/'work/ui/staff_credits';folder.mkdir(parents=True,exist_ok=True)
    im=Image.new('RGB',(1000,950),'#07101c');draw=ImageDraw.Draw(im)
    title=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',22)
    heading=ImageFont.truetype('C:/Windows/Fonts/times.ttf',29)
    name=ImageFont.truetype('C:/Windows/Fonts/times.ttf',34)
    draw.text((30,22),'Staff credits translation draft — layout preview, not in game',font=title,fill='#b6c5d8')
    y=100
    for role,person in [(29,31),(36,38),(43,45),(50,52),(57,59)]:
        draw.text((500,y),LABELS[role],font=heading,fill='#b9c9dd',anchor='mt')
        draw.text((500,y+43),NAMES[person],font=name,fill='white',anchor='mt');y+=150
    im.save(folder/'first-page-preview.png')
    print(json.dumps(dict(path=str(OUTPUT),counts=counts,nonempty_rows=len(rows)),indent=2))


if __name__=='__main__':main()
