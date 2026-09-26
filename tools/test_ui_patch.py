"""Focused, in-memory tests for the UI string-pool patcher."""
import struct
import unittest
from build_ui_patch import patch_table, text_table, patch_bundle, inner_bnd
from ui_font import patch_font, font_map, measure_text


def fixture():
    # Three live strings and a null slot. The last four bytes are external padding.
    data = bytearray(128)
    struct.pack_into('<10I', data, 0, 0x10000, 124, 0, 1, 4, 40, 0, 0, 1, 4)
    struct.pack_into('<4I', data, 40, 56, 0, 61, 69)
    data[56:61] = '決定'.encode('cp932') + b'\0'
    data[61:69] = b'untouch\0'
    data[69:76] = '○：×'.encode('cp932') + b'\0'
    data[124:] = b'TAIL'
    return bytes(data)


class StringPoolTests(unittest.TestCase):
    def test_longer_translation_relocates_without_losing_next_string(self):
        source = fixture()
        mapping = {'id': 'confirm', 'source': '決定', 'target': 'Confirm settings', 'table_ids': [10]}
        output, changes = patch_table(source, [mapping], 10)
        self.assertEqual(text_table(output)[2], [b'Confirm settings', None, b'untouch', '○：×'.encode('cp932')])
        self.assertEqual(output[124:], b'TAIL')
        self.assertEqual(len(source), len(output))
        self.assertNotEqual(struct.unpack_from('<I', source, 48), struct.unpack_from('<I', output, 48))
        self.assertEqual(changes[0]['slot'], 0)

    def test_unselected_table_is_byte_identical(self):
        source = fixture()
        output, changes = patch_table(source, [{'id': 'x', 'source': '決定', 'target': 'OK', 'table_ids': [11]}], 10)
        self.assertEqual(output, source)
        self.assertEqual(changes, [])

    def test_overflow_refuses_truncation(self):
        with self.assertRaisesRegex(ValueError, 'refusing to truncate'):
            patch_table(fixture(), [{'id': 'long', 'source': '決定', 'target': 'A' * 128, 'table_ids': [10]}], 10)

    def test_growth_updates_logical_size_and_preserves_all_strings(self):
        output, _ = patch_table(fixture(), [{'id': 'long', 'source': '決定', 'target': 'A' * 128, 'table_ids': [10]}], 10, allow_growth=True)
        self.assertGreater(len(output), len(fixture()))
        self.assertEqual(text_table(output)[2], [b'A' * 128, None, b'untouch', '○：×'.encode('cp932')])

    def test_missing_button_icon_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Game icon changed'):
            patch_table(fixture(), [{'id': 'bad', 'source': '○：×', 'target': 'OK', 'table_ids': [10]}], 10)

    def test_pointer_into_header_is_rejected(self):
        source = bytearray(fixture())
        struct.pack_into('<I', source, 40, 8)
        with self.assertRaisesRegex(ValueError, 'outside logical table'):
            text_table(source)

    def test_unterminated_string_is_rejected(self):
        source = bytearray(fixture())
        source[69:124] = b'A' * 55
        with self.assertRaisesRegex(ValueError, 'Unterminated'):
            text_table(source)


def font_fixture():
    # Only ASCII O and fullwidth C are initially available.
    data = bytearray(104)
    struct.pack_into('<4IHH3I', data, 0, 0x10000, 104, 19, 0, 2, 2, 32, 56, 0x10000)
    struct.pack_into('<6I', data, 32, ord('O'), ord('O'), 0, 0x8262, 0x8262, 1)
    struct.pack_into('<4f4h', data, 56, 0, 0, .1, .1, 0, 14, 14, 0)
    struct.pack_into('<4f4h', data, 80, .1, 0, .2, .1, 0, 15, 15, 0)
    return bytes(data)


class FontTests(unittest.TestCase):
    def test_missing_ascii_reuses_existing_glyph_without_changing_metrics(self):
        before = font_fixture()
        after, aliases = patch_font(before)
        old_map, old_start, count = font_map(before)
        new_map, new_start, _ = font_map(after)
        self.assertEqual(new_map[ord('C')], old_map[0x8262])
        self.assertEqual(after[new_start:], before[old_start:])
        self.assertEqual(measure_text(after, 'CO'), [29])
        self.assertEqual(aliases, [{'character': 'C', 'existing_character': 'Ｃ', 'glyph': 1}])

    def test_unavailable_glyph_fails_instead_of_silently_rendering_question_mark(self):
        with self.assertRaisesRegex(ValueError, 'no glyph'):
            measure_text(font_fixture(), 'C')

    def test_relocation_and_unmapped_category_detection(self):
        table = bytearray(80)
        struct.pack_into('<10I', table, 0, 0x10000, 80, 0, 1, 1, 40, 0, 0, 1, 1)
        struct.pack_into('<I', table, 40, 44)
        table[44:49] = '決定'.encode('cp932') + b'\0'
        resources = [(2500, font_fixture() + b'P' * 24), (10, bytes(table)), (9999, b'UNCHANGED' * 4)]
        bundle = bytearray(64)
        bundle[:4] = b'BND\0'
        struct.pack_into('<I', bundle, 8, len(resources))
        for i, (entry, data) in enumerate(resources):
            struct.pack_into('<II', bundle, 16 + i * 8, entry, len(bundle))
            bundle.extend(data)
        struct.pack_into('<I', bundle, 4, len(bundle))
        manifest = {'complete_table_ids': [10], 'preserved_slots': {}, 'mappings': []}
        with self.assertRaisesRegex(ValueError, 'Untranslated category member'):
            patch_bundle(bytes(bundle), manifest)
        manifest['mappings'] = [{'id': 'long', 'table_ids': [10], 'source': '決定', 'target': 'C' * 60, 'max_width': 1000}]
        output, tables, _ = patch_bundle(bytes(bundle), manifest)
        rebuilt = {i: output[s:e] for i, s, e in inner_bnd(output)}
        self.assertEqual(text_table(rebuilt[10])[2], [b'C' * 60])
        self.assertEqual(rebuilt[9999][:36], b'UNCHANGED' * 4)
        self.assertGreater(tables[0]['relative_offset'], 64)


if __name__ == '__main__':
    unittest.main()
