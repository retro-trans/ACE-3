import re
import unittest
from build_crawl_packed_patch import plan, stuf_table, BASE, PACKED
from build_history_patch import chunks
from build_ui_patch import ROOT
from dialogue_corpus import archive, parse_table
from packed_resource import pack, unpack, is_packed

JP = re.compile('[぀-ヿ一-鿿]')


def resource(path, rid):
    with path.open('rb') as f:
        fi, es = archive(f); _, sz, off, _ = next(e for e in es if e[3] == rid)
        f.seek(fi['offset']+off); return f.read(sz)


class PackedCrawlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (cls.packed,), cls.reports = (lambda r, rep: (tuple(r.values()), rep))(*plan())
        cls.before = unpack(resource(BASE, PACKED))[0]
        cls.after = unpack(cls.packed)[0]

    def test_decoder_consumes_the_stock_stream_exactly(self):
        stock = resource(next(ROOT.glob('*.iso')), PACKED)
        self.assertTrue(is_packed(stock))
        out, used = unpack(stock)
        self.assertEqual(len(out), 3377616)
        self.assertFalse(any(stock[used:]))                 # only zero padding is left
        self.assertEqual(out[:4], b'PRM\0')

    def test_encoder_round_trips_and_handles_edges(self):
        for sample in (b'', b'a', b'abcabcabcabcabcabcabcabc'*40, bytes(5000), bytes(range(256))*20, self.before[:70000]):
            self.assertEqual(unpack(pack(sample))[0], sample)

    def test_crawl_is_english_and_japanese_is_gone(self):
        rows = parse_table(stuf_table(self.after)[3])[3]
        self.assertEqual(len(rows), 68)
        self.assertEqual(rows[0][3], b'Unified Calendar 058')
        self.assertFalse(JP.search(self.after[stuf_table(self.after)[0]:stuf_table(self.after)[1]].decode('cp932', 'replace')))
        self.assertTrue(JP.search(stuf_table(self.before)[3].decode('cp932', 'replace')))

    def test_every_other_chunk_of_the_scene_is_identical(self):
        old, new = chunks(self.before), chunks(self.after)
        self.assertEqual([t for t, _, _ in old], [t for t, _, _ in new])
        for (tag, lo, hi), (_, nlo, nhi) in zip(old, new):
            if tag != b'STUF': self.assertEqual(self.before[lo:hi], self.after[nlo:nhi])


if __name__ == '__main__': unittest.main()
