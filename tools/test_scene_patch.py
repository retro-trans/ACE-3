import re
import unittest
from build_scene_patch import plan, wrap, rebuild_table, BASE, COPIES
from build_ui_patch import inner_bnd, u32
from dialogue_corpus import archive, parse_table
import build_dialogue_patch as builder

JP = re.compile('[぀-ヿ一-鿿]')


class SceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.replacements, cls.reports = plan()
        cls.before = {}
        with BASE.open('rb') as f:
            fi, es = archive(f)
            for _, sz, off, rid in es:
                if rid in COPIES or rid == 1200000:
                    f.seek(fi['offset']+off); cls.before[rid] = f.read(sz)
        bundle = cls.before[1200000]
        cls.font = {k:bundle[a:z] for k, a, z in inner_bnd(bundle)}[2500]

    def test_all_four_copies_are_complete_english(self):
        self.assertEqual(sorted(self.replacements), sorted(COPIES))
        for rid, data in self.replacements.items():
            rows = parse_table(data, u32(data, 20))[3]
            self.assertEqual(len(rows), 65)
            self.assertFalse([i for _, i, _, r in rows if JP.search(r.decode('cp932'))])

    def test_screenshot_line_and_commands(self):
        data = self.replacements[2002410]
        rows = {i:r.decode('cp932') for _, i, _, r in parse_table(data, u32(data, 20))[3]}
        self.assertIn('gentle coercion', rows[303])
        old = self.before[2002410]
        for _, i, _, r in parse_table(old, u32(old, 20))[3]:
            self.assertEqual(builder.TOKEN.findall(r.decode('cp932')), builder.TOKEN.findall(rows[i]))

    def test_original_script_and_table_bytes_are_kept(self):
        for rid, data in self.replacements.items():
            old = self.before[rid]
            self.assertEqual(data[:20]+data[24:len(old)], old[:20]+old[24:])
            self.assertGreaterEqual(u32(data, 20), len(old))

    def test_subtitles_stay_within_two_lines(self):
        for row in self.reports[0]['rows']:
            self.assertLessEqual(row['lines'], 2)
            self.assertLessEqual(max(row['widths']), 500)

    def test_three_line_subtitle_and_missing_row_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exceeds 2 lines'):
            wrap('<on()>' + 'word '*60 + '<off()>', self.font)
        old = self.before[2002410]; at = u32(old, 20)
        with self.assertRaisesRegex(ValueError, 'Incomplete scene'):
            rebuild_table(old[at:at+parse_table(old, at)[0]], {}, self.font)


if __name__ == '__main__': unittest.main()
