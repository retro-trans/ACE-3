"""Regression checks for slot-specific pause text relocation and safeguards."""
import unittest
from unittest.mock import patch
from build_pause_patch import replace_slots
from build_ui_patch import text_table
from test_ui_patch import fixture


class PausePatchTests(unittest.TestCase):
    def row(self, **values):
        result = {'id': 'test', 'slot': 0, 'source': '決定',
                  'target': 'Confirm ' * 20, 'status': 'meaning_reviewed'}
        result.update(values)
        return {'rows': [result]}

    @patch('build_pause_patch.measure_text', return_value=[160])
    def test_growth_preserves_null_and_unselected_slots(self, measure):
        before = fixture()
        output, report = replace_slots(before, self.row(), b'')
        self.assertGreater(len(output), len(before))
        self.assertEqual(text_table(output)[2],
                         [b'Confirm ' * 20, None, b'untouch', '○：×'.encode('cp932')])

    def test_stale_source_rejected(self):
        with self.assertRaisesRegex(ValueError, 'source preimage'):
            replace_slots(fixture(), self.row(source='different'), b'')

    def test_missing_icon_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Control glyph changed'):
            replace_slots(fixture(), self.row(slot=3, source='○：×', target='Confirm'), b'')

    def test_unreviewed_translation_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unreviewed'):
            replace_slots(fixture(), self.row(status='draft'), b'')


if __name__ == '__main__':
    unittest.main()
