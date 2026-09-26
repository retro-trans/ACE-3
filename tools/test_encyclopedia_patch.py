import json
import re
import unittest
from build_encyclopedia_patch import plan, INPUT, BASE
from build_dialogs_patch import fit
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts

JP = re.compile('[぀-ヿ一-鿿]')
LINK = re.compile(r'<book\((\d+)\)>(.*?)<endbook\(\)>')
TABLES = {4002050:(3018, 3019), 4002054:(3018, 3019), 4002057:(3018, 3019),
          1200000:(3028, 3029), 1200001:(3028, 3029), 1200005:(3028, 3029), 1200006:(3028, 3029)}


class EncyclopediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.changes, cls.reports, cls.inventory = plan()
        cls.before = {}
        with BASE.open('rb') as f:
            fi, es = archive(f)
            for _, sz, off, rid in es:
                if rid in cls.changes:
                    f.seek(fi['offset']+off); cls.before[rid] = f.read(sz)
        cls.font = parts(cls.before[4002050])[2500]

    def test_all_88_entries_in_every_copy(self):
        self.assertEqual(sorted(self.changes), sorted(TABLES))
        for rid, (names, pages) in TABLES.items():
            p = parts(self.changes[rid])
            for table in (names, pages):
                rows = parse_table(p[table])[3]
                self.assertEqual([i for _, i, _, _ in rows], list(range(1, 89)))
                self.assertFalse([i for _, i, _, r in rows if JP.search(r.decode('cp932'))])

    def test_links_keep_their_targets_and_use_the_entry_name(self):
        old, new = parts(self.before[4002050]), parts(self.changes[4002050])
        names = {i:r.decode('cp932') for _, i, _, r in parse_table(new[3018])[3]}
        before = {i:r.decode('cp932') for _, i, _, r in parse_table(old[3019])[3]}
        for _, i, _, r in parse_table(new[3019])[3]:
            text = r.decode('cp932')
            self.assertEqual(sorted(n for n, _ in LINK.findall(before[i])), sorted(n for n, _ in LINK.findall(text)), i)
            for n, inner in LINK.findall(text):
                stem = names[int(n)].lower().replace('the ', '')[:-1]
                self.assertIn(stem[:8], inner.lower(), (i, n, inner))

    def test_pages_stay_inside_stock_lines_width_and_bytes(self):
        for rid, (_, pages) in TABLES.items():
            for _, i, _, r in parse_table(parts(self.changes[rid])[pages])[3]:
                self.assertLessEqual(len(r), 599, (rid, i))
                self.assertLessEqual(r.count(b'\n')+1, 17, (rid, i))

    def test_only_the_four_text_tables_change_and_nothing_is_reallocated(self):
        for rid, data in self.changes.items():
            before, after = parts(self.before[rid]), parts(data)
            self.assertEqual({k for k in before if before[k] != after[k]}, set(TABLES[rid]))
        self.assertEqual(sum(len(r['allocations']) for r in self.reports), 0)

    def test_lost_link_is_rejected_but_reordered_links_pass(self):
        row = {'dialog':False, 'page_text':True, 'limit':443, 'max_lines':17, 'max_chars':599}
        source = '<book(1)>a<endbook()> x <book(2)>b<endbook()>'
        self.assertTrue(fit(dict(row, en='<book(2)>B<endbook()> then <book(1)>A<endbook()>'), source, self.font))
        with self.assertRaisesRegex(ValueError, 'Control code'):
            fit(dict(row, en='<book(2)>B<endbook()> only'), source, self.font)


if __name__ == '__main__': unittest.main()
