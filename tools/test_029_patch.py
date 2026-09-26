"""Checks for 0.1.29: repainted meeting pictures keep their container, and new scenes obey the window budgets."""
import re
import unittest
from build_ui_patch import ROOT
from dialogue_corpus import archive
from build_flight_save_patch import parts
import build_029_patch as patch
import hud_labels
import os
if os.environ.get("ACE3_WAVE"):
    v, b = os.environ["ACE3_WAVE"].split(":")
    patch.BASE = patch.ROOT/("work/output/ACE3-English-%s.iso" % b); patch.AUXILIARY = hud_labels.labels()
import meeting_captions as captions

TAG = re.compile(r'<[^>]*>')


class Patch029(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.changes, cls.reports, cls.summary = patch.plan()
        with patch.BASE.open('rb') as f:
            info, entries = archive(f); cls.before = {}
            for entry in entries:
                if entry[3] in cls.changes: f.seek(info['offset']+entry[2]); cls.before[entry[3]] = f.read(entry[1])

    def test_every_caption_picture_is_repainted(self):
        self.assertEqual(self.summary['pictures_repainted'], len(captions.CAPTIONS))

    def test_pictures_keep_header_palette_and_size_and_only_caption_rows_change(self):
        for report in self.reports:
            for picture in report.get('pictures', []):
                old = parts(self.before[report['resource_id']])[picture['chunk']]; new = parts(self.changes[report['resource_id']])[picture['chunk']]
                self.assertEqual(len(old), len(new)); self.assertEqual(old[:32], new[:32]); self.assertEqual(old[32+65536:], new[32+65536:])
                changed = {i//256 for i in range(65536) if old[32+i] != new[32+i]}
                self.assertTrue(changed)
                bands = [band for band, _ in captions.CAPTIONS[picture['picture']]]
                self.assertTrue(all(any(b[0]-8 <= y <= b[1]+8 for b in bands) for y in changed), (report['resource_id'], sorted(changed)))

    def test_other_chunks_of_meeting_files_are_untouched(self):
        for report in self.reports:
            if report['kind'] != 'window_scene': continue
            old, new = parts(self.before[report['resource_id']]), parts(self.changes[report['resource_id']])
            touched = {p['chunk'] for p in report['pictures']} | {t['table_id'] for t in report['tables']}
            for key in old:
                if key not in touched: self.assertEqual(old[key].rstrip(b'\0'), new[key].rstrip(b'\0'), (report['resource_id'], key))

    def test_new_window_rows_fit(self):
        for report in self.reports:
            if report['kind'] != 'window_scene': continue
            width, lines, chars = patch.previous.WINDOW[report['resource_id']//1000]
            for table in report['tables']:
                for row in table['rows']:
                    if '<operator(' not in row['target']: continue
                    self.assertLessEqual(len(row['target'].split('\n')), lines); self.assertLessEqual(max(row['widths']), width)
                    self.assertLessEqual(len(TAG.sub('', row['target'])), chars+lines)

    def test_portrait_chatter_width(self):
        for report in self.reports:
            if report['kind'] != 'relocated_dialogue_table': continue
            for row in report['rows']:
                self.assertLessEqual(max(row['widths']), 400 if row['target'].startswith('<op()>') else 480)


if __name__ == '__main__': unittest.main()
