import unittest
import build_encyclopedia_paging_patch as p


class Pagination(unittest.TestCase):
    def test_zentradi_reproduces_cutoff_and_keeps_missing_words(self):
        text = ("A race naturalized on Earth after the\n"
                "<book(4)>First Defense War<endbook()>. Once a race of giants\n"
                "skilled in combat, they were reduced in\nsize upon naturalization.\n\n"
                "However, because of the\n<book(9)>Earth Federation<endbook()>'s insufficient\n"
                "immigration policy and their innate\nfighting instinct, riots by some immigrants\n"
                "break out often and have become a social\nproblem.")
        old_pages = p.pages(text)
        self.assertTrue(p.visible(old_pages[0]).replace('\n', '')[:189].endswith("'s insuff"))
        self.assertTrue(old_pages[1].startswith('fighting instinct'))
        new_pages = p.pages(p.paginate(text))
        self.assertEqual(len(new_pages), 2)
        self.assertTrue(new_pages[1].startswith('However'))
        self.assertIn("insufficient\nimmigration policy and their innate\nfighting instinct", new_pages[1])
        self.assertEqual(p.paginate(text).split(), text.split())

    def test_long_paragraph_and_whole_links_survive_without_blank_pages(self):
        source = '\n'.join(['A line with enough words to need space.']*24)
        source += '\n\n<book(9)>Earth Federation<endbook()> remains linked.'
        result = p.paginate(source)
        self.assertEqual(source.split(), result.split())
        self.assertEqual(p.LINK.findall(source), p.LINK.findall(result))
        for page in p.pages(result):
            self.assertTrue(page.strip())
            self.assertLess(len(p.visible(page)), 190)
        self.assertEqual(p.paginate(result), result)


@unittest.skipUnless(p.OUTPUT.with_suffix('.json').exists(), 'Build 0.1.41 first')
class FinishedDisc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before, cls.after = {}, {}
        # Include every gameplay Encyclopedia copy to guard against accidental
        # eight-line padding in the separate, shorter glossary window.
        cls.bundles = p.BUNDLES + (1200000, 1200001, 1200005, 1200006)
        for path, dest in ((p.BASE, cls.before), (p.OUTPUT, cls.after)):
            with path.open('rb') as f:
                p.verify_renderer(f)
                fi, es = p.archive(f)
                for _, size, off, rid in es:
                    if rid in cls.bundles:
                        f.seek(fi['offset']+off); dest[rid] = p.parts(f.read(size))

    def test_all_88_entries_in_three_copies_preserve_words_and_links(self):
        for rid in p.BUNDLES:
            old = {i: (s, r.decode('cp932')) for s, i, _, r in p.parse_table(self.before[rid][3019])[3]}
            new = {i: (s, r.decode('cp932')) for s, i, _, r in p.parse_table(self.after[rid][3019])[3]}
            self.assertEqual(set(old), set(range(1, 89)))
            self.assertEqual(old.keys(), new.keys())
            for i, (slot, source) in old.items():
                self.assertEqual(new[i][0], slot)
                self.assertEqual(new[i][1].split(), source.split())
                self.assertEqual(p.LINK.findall(new[i][1]), p.LINK.findall(source))

    def test_every_built_page_is_complete_and_fits(self):
        for rid in p.BUNDLES:
            for _, _, _, raw in p.parse_table(self.after[rid][3019])[3]:
                text = raw.decode('cp932')
                self.assertLess(len(text.split('\n')), 255)
                for page in p.pages(text):
                    self.assertTrue(page.strip())
                    self.assertLess(len(p.visible(page)), 190)
                    self.assertEqual(page.count('<book('), page.count('<endbook()>'))
                    self.assertLessEqual(max(p.measure_text(self.after[rid][2500], p.visible(page))), 443)

    def test_other_resources_and_gameplay_copies_unchanged(self):
        for rid in self.bundles:
            self.assertEqual(self.before[rid].keys(), self.after[rid].keys())
            for k in self.before[rid]:
                if rid in p.BUNDLES and k == 3019:
                    continue
                self.assertEqual(self.before[rid][k], self.after[rid][k], (rid, k))


if __name__ == '__main__':
    unittest.main()
