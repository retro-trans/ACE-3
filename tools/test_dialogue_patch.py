"""Focused structural tests for longer, relocated, command-bearing subtitles."""
import hashlib
import struct
import unittest
from build_dialogue_patch import rebuild_table, wrap_text, TOKEN
from dialogue_corpus import parse_table
from dialogue_font import address4, address32


def test_font():
    result = bytearray(44 + 95 * 24)
    struct.pack_into('<4IHH3I', result, 0, 65536, len(result), 19, 0, 1, 95, 32, 44, 65536)
    struct.pack_into('<3I', result, 32, 32, 126, 0)
    for i in range(95):
        struct.pack_into('<4f4h', result, 44 + i * 24, 0, 0, .01, .04, 0, 10, 10, 0)
    return result


class DialogueTests(unittest.TestCase):
    def test_multiple_ranges_null_slot_and_growth(self):
        source = b'<op()><sp(20)>Short<ab(200><ed()>'
        original = bytearray(64 + len(source) + 1)
        struct.pack_into('<7I', original, 0, 65536, len(original), 0, 2, 3, 52, 0)
        struct.pack_into('<6I', original, 28, 0, 101, 102, 2, 501, 501)
        struct.pack_into('<3I', original, 52, 64, 0, 64)
        original[64:] = source + b'\0'
        target = '<op()><sp(20)>A full translation that is substantially longer than the original source.<ab(200><ed()>'
        rebuilt, reports = rebuild_table(original, {hashlib.sha256(source).hexdigest(): {'id': 'test', 'target': target}}, test_font())
        size, pointers, count, rows = parse_table(rebuilt)
        self.assertGreater(size, len(original))
        self.assertEqual([r[1] for r in rows], [101, 501])
        self.assertEqual(struct.unpack_from('<I', rebuilt, pointers + 4)[0], 0)
        self.assertEqual(rows[0][2], rows[1][2])
        self.assertEqual(TOKEN.findall(rows[0][3].decode()), TOKEN.findall(target))
        self.assertEqual(rows[0][3].decode().replace('\n', ' '), target)

    def test_author_line_breaks_and_words_retained(self):
        text = '<op()><sp(20)>W-wait a second!\nYou mean I have to pilot this?<ab(500)>'
        self.assertEqual(wrap_text(text, test_font()), text)

    def test_refuse_overflow_without_truncating(self):
        with self.assertRaises(ValueError):
            wrap_text('<sp(20)>' + 'unbroken' * 50, test_font())
        with self.assertRaises(ValueError):
            wrap_text('<sp(20)>' + '\n'.join(['line'] * 5), test_font())

    def test_psm_addresses_are_bijections(self):
        self.assertEqual({address4(x, y, 128) for y in range(128) for x in range(128)}, set(range(16384)))
        self.assertEqual({address32(x, y, 64) for y in range(32) for x in range(64)}, set(range(0, 8192, 4)))
        self.assertEqual(address4(1, 0, 128), 8)
        self.assertEqual(address4(0, 2, 128), 65)
        self.assertEqual(address4(128, 0, 256), 16384)


if __name__ == '__main__':
    unittest.main()
