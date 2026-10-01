"""Finish reference-matched credits without exporting the source script."""
import json
from build_ui_patch import ROOT, require

NAMES = '''218|Kenji Akiba
219|Daisuke Deguchi
220|Hironori Hagiwara
221|Haruhiko Kumaki
222|Takuma Kinjo
223|Kei Sato
224|Naoto Tomita
225|Koshi Seike
226|Takuro Seguchi
227|Tomohiro Ito
228|Kazumi Kawada
229|Hiroyasu Itakura
230|Yoshie Iizuka
231|Hiroki Izumi
232|Youhei Watahiki
233|Yuji Takei
307|Masaaki Miyata
309|Yasuyuki Mochida (Edge Works)
311|Ryu Nakamura (Edge Works)
313|Hiroyuki Fujii (Edge Works)
392|Yasuhiko Onda
402|Junya Shinozaki
412|Wataru Yoshioka
420|Toshiyasu Takahashi
443|Kenichiro Kimura
463|Hiromi Kikuta (Rakuonsha)
465|Kaoru Machida
470|Yasuaki Sumi (Aoni Production)
472|Sachiko Sekine (Aoni Production)
488|Yosuke Akimoto
489|Kazue Ikura
490|Shuichi Ikeda
491|Shozo Iizuka
492|Hideo Ishikawa
493|Akira Ishida
494|Unsho Ishizuka
495|Yuji Ueda
496|Naoya Uchida
497|Hisao Egawa
498|Akio Otsuka
499|Tomoko Otsuka
500|Hochu Otsuka
502|Yumi Kakazu
503|Michiko Neya
504|Osamu Kato
505|Mika Kanai
506|Akira Kamiya
507|Otoya Kawano
508|Maria Kawamura
509|Shiho Kikuchi
510|Masami Kikuchi
511|Banjo Ginga
512|Ami Koshimizu
513|Jurota Kosugi
514|Ai Kobayashi
515|Tetsuo Komura
516|Takehito Koyasu
517|Rikiya Koyama
519|Nozomu Sasaki
520|Yuko Sanpei
521|Saeko Shimazu
522|Yu Shimamura
523|Tetsu Shiratori
524|Naomi Shindo
525|Hirotaka Suzuoki
526|Tomokazu Seki
527|Mie Sonozaki
529|Wataru Takagi
530|Eri Takeda
531|Koji Tsujitani
532|Mika Doi
534|Kazuya Nakai
535|Miki Nagasawa
536|Shigeru Nakahara
538|Daisuke Namikawa
539|Kenji Nojima
540|Hirofumi Nojima
542|Romi Park
543|Sho Hayami
544|Aya Hisakawa
545|Narumi Hidaka
546|Noriko Hidaka
547|Kohei Fukuhara
548|Takahiro Fujimoto
549|Keiji Fujiwara
550|Jun Fukuyama
551|Toru Furuya
552|Soichiro Hoshi
553|Kenyu Horiuchi
555|Naoko Matsui
556|Kohei Matsumoto
557|Yasunori Matsumoto
558|Rica Matsumoto
559|Fumie Mizusawa
560|Rena Mizushiro
561|Yutaro Mitsuoka
562|Hikaru Midorikawa
563|Omi Minami
564|Mugihito
565|Akino Murata
566|Toshiyuki Morikawa
567|Takeshi Mori
569|Akiko Yajima
570|Mayu Yamaguchi
571|Takumi Yamazaki
572|Shigenori Yamazaki
573|Koichi Yamadera
574|Keiichiro Yamamoto
575|Chisa Yokoyama
577|Kumiko Watanabe
598|Koji Kumakura (Banpresto)
599|Yoshifumi Matsuda (Banpresto)
600|Takashi Watabe (Banpresto)
601|Chikae Kimura (Banpresto)
602|Tomoko Takehara (Banpresto)
603|Shota Tsujimoto (Banpresto)
604|Hideo Emoto (Banpresto)
605|Shoichi Yoshiba (Banpresto)
606|Morito Ishii (Banpresto)
607|Momoko Suzuki (Banpresto)
608|Seiko Okugaki (Banpresto)
610|Yoshinori Komatsu (FromSoftware)
611|Yasunori Ogura (FromSoftware)
612|Suminobu Sato (FromSoftware)
613|Tomohiro Shimokawa (FromSoftware)
617|Hiroyuki Kani (FromSoftware)
621|Tomomi Nakano (FromSoftware)
622|Hiroyuki Yanai (FromSoftware)
629|Akihiro Morita (Sunrise)
630|Makoto Shibuya (Sunrise)
631|Takeshi Mukai (Sunrise)
632|Koji Nakajima (Sunrise)
634|Retsu Tamura (Sotsu)
636|Yasu Tokuhara (Dynamic Planning)
637|Kazuomi Nagai (Dynamic Planning)
639|Kamon Onishi (Big West Ad)
640|Shinichi Hirai (Big West Ad)
641|Toshiko Shibuya (Big West Ad)
643|Aya Shibata (BONES)
644|Yoshiko Kanaya (Bandai)
645|Jun Satoyoshi (Bandai)
647|Keiko Hirakawa (Rights Inn)
654|Yoshiyuki Tomino
655|Shoji Kawamori
656|Tomoki Kyoda
658|Koichi Inoue (Sunrise)
660|Yoshihiro Yoshida (Sunrise)
661|Hirofumi Inagaki (Namco Bandai Games)
662|Yoshihiro Okamoto (BEC)
664|Kuninori Yoshizaki (Banpresto)
665|Ayako Higuchi (Banpresto)
666|Yoshihisa Kanesaka (Banpresto)
667|Satoshi Otsuka (Banpresto)
669|Masato Miyazaki (FromSoftware)
670|Daisuke Satake (FromSoftware)
671|Makoto Sato (FromSoftware)
672|Tatsuya Kawate (FromSoftware)
673|Aiko Goto
701|Hiroshi Kosuge (Banpresto)
703|Hiroyuki Goto (FromSoftware)
705|Tomohiro Shibuya (FromSoftware)
712|Naotoshi Zin
719|Toshihiro Nada (Banpresto)
721|Eiichi Nakajima (FromSoftware)'''

CORRECTIONS = {
    191: ('Hideki Tachibana', 'https://www.mobygames.com/game/76099/enkaku-sosa-shinjitsu-e-no-23-hiai/credits/psp/'),
    487: ('Go Aoba', 'https://www.excite.co.jp/news/dictionary/person/PE046e0afa3ceda69a2388e34473f779752d3e463c/'),
    537: ('Kaori Nazuka', 'https://www.mobygames.com/person/206799/kaori-nazuka/'),
    659: ('Kojiro Taniguchi (Sunrise)', 'https://www.eventernote.com/actors/initial/た'),
}
UNVERIFIED = {177, 179, 184, 186, 427, 434}
PROVISIONAL = {
    177: 'Naoto Sawaguchi', 179: 'Tomohiro Ishii', 184: 'Tokuya Saito',
    186: 'Tomonori Nishikawa', 427: 'Ryo Shin (Burning Publishers)',
    434: 'Daiki Watanabe (Burning Production)',
}


def main():
    path = ROOT/'work/translation/en/staff_credits.json'
    doc = json.loads(path.read_text(encoding='utf-8'))
    targets = {int(line.split('|', 1)[0]): line.split('|', 1)[1] for line in NAMES.splitlines()}
    targets.update({key: value[0] for key, value in CORRECTIONS.items()})
    require(len(targets) == 168, 'Reference coverage')
    for row in doc['rows']:
        tid = row['text_id']
        if tid in targets:
            row.update(target=targets[tid], status='reference_matched', reference=CORRECTIONS[tid][1] if tid in CORRECTIONS else doc['name_reference'])
        elif tid in UNVERIFIED:
            row.update(target=PROVISIONAL[tid], status='provisional_romanization', note='Unverified reading. User authorized provisional romanizations on 2026-10-01; flag in build notes.')
        elif row['status'].endswith('_draft'):
            row['status'] = row['status'].replace('_draft', '')
        if tid in (487, 537, 659):
            row['note'] = 'Corrects a different person attributed by the main online credit list; source spelling checked on disc.'
        if tid == 496:
            row['note'] = 'Use the established actor spelling; the disc uses a variant final kanji.'
    doc.update(schema='ace3-staff-credits-v1', status='ready_for_local_test_build', unverified_name_ids=sorted(UNVERIFIED))
    doc['counts'] = {s: sum(r['status'] == s for r in doc['rows']) for s in sorted({r['status'] for r in doc['rows']})}
    doc['notes'] = [
        'Original row IDs, blank rows, graphic commands and roll timing must be preserved.',
        'English lines are measured and centered; the song-title color commands are retained.',
        'Six personal-name readings use provisional romanizations explicitly authorized by the user; listed in build notes.',
        'Native embedded font supplies full ASCII and every character actually used by the new roll.',
        'Source-script hashes are stored instead of a duplicate Japanese script.'
    ]
    path.write_text(json.dumps(doc, ensure_ascii=True, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(doc['counts']))


if __name__ == '__main__':
    main()
