import unittest
from build_hangar_fix import capacity_bound, layouts
from test_layout_fix import layout


class HangarCapacityTests(unittest.TestCase):
    def test_all_candidate_translations_fit_with_spare(self):
        pairs = [('AB', 'Confirm'), ('12345678', 'Resume Game'),
                 ('1234567890', 'A considerably longer description')]
        for stock in (2, 8, 10, 32, 64):
            bound = capacity_bound(stock, pairs)
            self.assertGreaterEqual(bound, stock)
            for source,target in pairs:
                if len(source) <= stock: self.assertGreater(bound,len(target))

    def test_long_dialog_does_not_inflate_short_labels(self):
        self.assertEqual(capacity_bound(2, [('AB','Confirm'), ('A'*80,'B'*200)]),32)

    def test_default_and_existing_large_bound(self):
        self.assertEqual(capacity_bound(0, [('A'*32,'B'*57)]),58)
        self.assertEqual(capacity_bound(255, []),255)

    def test_layout_inventory_keeps_original_capacities(self):
        self.assertEqual([(p,cap) for p,_,cap in layouts(layout())], [((0,),7),((1,),255)])


if __name__ == '__main__': unittest.main()
