"""Checks for 0.1.28: demo-player font, HUD/Results and movie labels, in-mission wrapping, window scenes."""
import re
import unittest
from build_ui_patch import u32
from dialogue_corpus import parse_table
from build_flight_save_patch import parts
from ui_font import font_map, measure_text
import build_028_patch as patch

TAG = re.compile(r'<[^>]*>')
JP = re.compile('[぀-ヿ一-鿿]')


class Patch028(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.changes, cls.reports, cls.summary = patch.plan()

    def test_demo_player_font_has_every_ascii_glyph(self):
        font = parts(self.changes[patch.DEMO_PLAYER])[2500]; mapping = font_map(font)[0]
        self.assertTrue(all(code in mapping for code in range(32, 127)))
        self.assertGreater(measure_text(font, 'What the... do you think you are doing?')[0], 300)

    def test_no_text_buffer_grows(self):
        self.assertEqual(self.summary['allocation_adjustments'], 0)

    def test_hud_and_movie_tables_are_english_everywhere(self):
        seen = {3013:0, 3090:0}
        for rid, data in self.changes.items():
            if not (1200000 <= rid <= 1200011 or 4002050 <= rid <= 4002058): continue
            for tid, chunk in parts(data).items():
                if tid not in seen: continue
                rows = [r.decode('cp932') for _, _, _, r in parse_table(chunk)[3]]
                if not any('Movie Viewer' in r or 'Mission Update' in r for r in rows): continue
                seen[tid] += 1
                self.assertFalse([r for r in rows if JP.search(r)], (rid, tid))
        self.assertEqual(seen, {3013:8, 3090:3})

    def test_portrait_chatter_stays_clear_of_the_wingman_icons(self):
        for report in self.reports:
            if report['kind'] != 'relocated_dialogue_table': continue
            for row in report['rows']:
                self.assertLessEqual(row['lines'], 4)
                limit = 400 if row['target'].startswith('<op()>') else 480
                self.assertLessEqual(max(row['widths']), limit, row['target'])

    def test_scene_pointer_redirected_and_script_untouched(self):
        for report in self.reports:
            if report['kind'] != 'relocated_dialogue_table': continue
            data = self.changes[report['resource_id']]
            self.assertEqual(u32(data, 20), report['relocated_offset'])
            self.assertEqual(parse_table(data, report['relocated_offset'])[0], len(data)-report['relocated_offset'])

    def test_window_scenes_fit_three_lines_and_keep_commands(self):
        for report in self.reports:
            if report['kind'] != 'window_scene': continue
            family = report['resource_id']//1000
            for table in report['tables']:
                for row in table['rows']:
                    if family == 4003 and row['slot'] == 0: continue
                    self.assertLessEqual(len(row['target'].split('\n')), 3)
                    self.assertLessEqual(max(row['widths']), patch.WINDOW[family][0])
                    self.assertFalse(JP.search(TAG.sub('', row['target'])))


if __name__ == '__main__': unittest.main()
