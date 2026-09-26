import re
import unittest
from build_reviewed_scenes_patch import plan, copies, AUXILIARY, BASE
from build_scene_patch import wrap_words
from build_ui_patch import inner_bnd, u32
from dialogue_corpus import archive, parse_table
import build_dialogue_patch as builder

JP = re.compile('[぀-ヿ一-鿿]')


class ReviewedSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.replacements, cls.reports = plan()
        cls.before = {}
        with BASE.open('rb') as f:
            fi, es = archive(f)
            for _, sz, off, rid in es:
                if rid in cls.replacements or rid == 1200000:
                    f.seek(fi['offset']+off); cls.before[rid] = f.read(sz)
        bundle = cls.before[1200000]
        cls.font = {k:bundle[a:z] for k, a, z in inner_bnd(bundle)}[2500]

    def test_five_scenes_in_four_copies_are_english(self):
        self.assertEqual(sorted(self.replacements), sorted(r for s in AUXILIARY for r in copies(s)))
        for rid, data in self.replacements.items():
            rows = parse_table(data, u32(data, 20))[3]
            self.assertFalse([i for _, i, _, r in rows if JP.search(r.decode('cp932'))], rid)

    def test_commands_slots_and_original_bytes_are_kept(self):
        for rid, data in self.replacements.items():
            old = self.before[rid]
            self.assertEqual(data[:20]+data[24:len(old)], old[:20]+old[24:])
            a, b = parse_table(old, u32(old, 20))[3], parse_table(data, u32(data, 20))[3]
            self.assertEqual([(s, i) for s, i, _, _ in a], [(s, i) for s, i, _, _ in b])
            for (_, _, _, x), (_, _, _, y) in zip(a, b):
                self.assertEqual(builder.TOKEN.findall(x.decode('cp932')), builder.TOKEN.findall(y.decode('cp932')))

    def test_screenshot_lines(self):
        data = self.replacements[2002020]
        rows = {i:r.decode('cp932') for _, i, _, r in parse_table(data, u32(data, 20))[3]}
        self.assertEqual(rows[31], "Nav: Watch the Nadesico B's damage")
        self.assertTrue(any("enemy's main force" in t for t in rows.values()))

    def test_window_budget(self):
        for report in self.reports:
            for row in report['rows']:
                self.assertLessEqual(row['lines'], 4)
                self.assertLessEqual(max(row['widths']), 500)

    def test_wrapper_keeps_tags_glued_and_spans_whole(self):
        text = '<on()>Oh, Lieutenant <color(4)>Dyson<ce()>, the <book(10)>Londo Bell<endbook()> orders have arrived for both of you today.'
        out = wrap_words(text, self.font, 300, 6)
        self.assertIn('<color(4)>Dyson<ce()>,', out)
        self.assertIn('<book(10)>Londo Bell<endbook()>', out)
        self.assertEqual(out.split(), text.split())


if __name__ == '__main__': unittest.main()
