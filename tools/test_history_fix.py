import re
import unittest
from build_history_fix import plan, compact, BASE
from build_history_patch import chunks
from build_ui_patch import inner_bnd
from dialogue_corpus import archive, parse_table

JP = re.compile('[぀-ヿ一-鿿]')


def table_of(data):
    (a, z), = [(lo, hi) for tag, lo, hi in chunks(data) if tag == b'STUF']
    bnd = data[a+16:z]; (_, ta, tz), = inner_bnd(bnd)
    return bnd[ta:tz]


class HistoryFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (cls.after,), cls.reports = (lambda r, rep: (tuple(r.values()), rep))(*plan())
        with BASE.open('rb') as f:
            fi, es = archive(f); _, sz, off, _ = next(e for e in es if e[3] == 4010)
            f.seek(fi['offset']+off); cls.before = f.read(sz)

    def test_rows_are_unchanged_and_pool_starts_with_english(self):
        old, new = table_of(self.before), table_of(self.after)
        a, b = parse_table(old), parse_table(new)
        self.assertEqual([(s, i, r) for s, i, _, r in a[3]], [(s, i, r) for s, i, _, r in b[3]])
        pool = new[b[1]+b[2]*4:]
        self.assertTrue(pool.startswith(b'Unified Calendar 058\0'))
        self.assertFalse(JP.search(pool.decode('cp932', 'replace')))
        self.assertTrue(JP.search(old[a[1]+a[2]*4:].decode('cp932', 'replace')))   # 0.1.23 still carried the Japanese pool

    def test_strings_are_stored_in_slot_order(self):
        rows = parse_table(table_of(self.after))[3]
        self.assertEqual([p for _, _, p, _ in rows], sorted(p for _, _, p, _ in rows))

    def test_every_other_scene_chunk_is_identical(self):
        old, new = chunks(self.before), chunks(self.after)
        self.assertEqual([t for t, _, _ in old], [t for t, _, _ in new])
        for (tag, lo, hi), (_, nlo, nhi) in zip(old, new):
            if tag != b'STUF': self.assertEqual(self.before[lo:hi], self.after[nlo:nhi])

    def test_japanese_table_is_refused(self):
        with next(BASE.parent.parent.parent.glob('*.iso')).open('rb') as f:
            fi, es = archive(f); _, sz, off, _ = next(e for e in es if e[3] == 4010)
            f.seek(fi['offset']+off); original = f.read(sz)
        with self.assertRaisesRegex(ValueError, 'English crawl'):
            compact(table_of(original))


if __name__ == '__main__': unittest.main()
