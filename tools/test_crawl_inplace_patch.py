import re
import unittest
from build_crawl_inplace_patch import plan, PACKED, PLAIN, LAST_SLOT
from build_crawl_packed_patch import stuf_table
from build_history_patch import chunks
from build_ui_patch import ROOT
from dialogue_corpus import archive, parse_table
from packed_resource import unpack

JP = re.compile('[぀-ヿ一-鿿]')


def stock(rid):
    with next(ROOT.glob('*.iso')).open('rb') as f:
        fi, es = archive(f); _, sz, off, _ = next(e for e in es if e[3] == rid)
        f.seek(fi['offset']+off); return f.read(sz)


class InPlaceCrawlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.new, cls.reports = plan()
        cls.old_packed, cls.old_plain = stock(PACKED), stock(PLAIN)

    def test_no_size_changes_anywhere(self):
        self.assertEqual(len(self.new[PACKED]), len(self.old_packed))
        self.assertEqual(len(self.new[PLAIN]), len(self.old_plain))
        self.assertEqual(len(unpack(self.new[PACKED])[0]), len(unpack(self.old_packed)[0]))

    def test_only_the_2304_table_bytes_differ(self):
        for old, new in ((unpack(self.old_packed)[0], unpack(self.new[PACKED])[0]), (self.old_plain, self.new[PLAIN])):
            diff = [i for i, (a, b) in enumerate(zip(old, new)) if a != b]
            self.assertLess(max(diff)-min(diff), 2304)
            self.assertEqual([c[:2] for c in chunks(old)], [c[:2] for c in chunks(new)])    # every chunk at its original offset

    def test_crawl_is_english_inside_the_original_span(self):
        for scene in (unpack(self.new[PACKED])[0], self.new[PLAIN]):
            size, _, count, rows = parse_table(stuf_table(scene)[3])
            self.assertEqual((size, count), (2304, 81))
            self.assertEqual(rows[0][3], b'Unified Calendar 058')
            self.assertLessEqual(max(r[0] for r in rows), LAST_SLOT)
            self.assertFalse([r for r in rows if JP.search(r[3].decode('cp932'))])

    def test_both_copies_carry_the_same_table(self):
        self.assertEqual(stuf_table(unpack(self.new[PACKED])[0])[3], stuf_table(self.new[PLAIN])[3])


def game_decoder(data):
    """The EE routine at 0x0023E950 transcribed step by step: window base t0, slid flag t2, source = t0 + field."""
    import struct
    size = struct.unpack('>I', data[4:8])[0]
    out = bytearray(size+32); o = 0; t0 = 0; slid = False; at = 12
    while o < size:
        flags = data[at]; at += 1
        for bit in range(8):
            if o >= size: break
            if flags >> bit & 1:
                field = data[at] << 4 | data[at+1] >> 4; nibble = data[at+1] & 15; at += 2
                if nibble == 0: return bytes(out[:o])            # the game stops here
                length = nibble+1
                for k in range(length): out[o+k] = out[t0+field+k]
            else:
                out[o] = data[at]; at += 1; length = 1
            o += length
            if slid: t0 += length
            elif o-t0 >= 4096: t0 = o-4096; slid = True
    return bytes(out[:size])


class GameDecoderTests(unittest.TestCase):
    def test_transcribed_game_decoder_agrees_on_stock_and_new_streams(self):
        new, _ = plan()
        old = stock(PACKED)
        self.assertEqual(game_decoder(old), stock(PLAIN))                 # the packed scene is the plain scene
        self.assertEqual(game_decoder(old), unpack(old)[0])
        self.assertEqual(game_decoder(new[PACKED]), unpack(new[PACKED])[0])
        self.assertEqual(game_decoder(new[PACKED]), new[PLAIN])           # both copies end up identical


if __name__ == '__main__': unittest.main()
