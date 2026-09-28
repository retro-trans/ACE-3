import struct
import unittest
from build_lock_priority_patch import edge_widths, repair_quad


class LockPriorityGeometry(unittest.TestCase):
    def test_both_edges_fit_with_real_float_coordinate_asymmetry(self):
        data = b''.join(struct.pack('<4f', *v) for v in [
            (-.0196669996, -10.5313511, -.000001, 1),
            (-.0196439996, 10.5313339, .000001, 1),
            (158.189041, -10.5313215, -.000001, 1),
            (171.9803314, 10.5313568, .000001, 1)])
        # The old min/max width check passed even with an undersized top edge.
        self.assertGreater(max(edge_widths(data, 0)), 164)
        self.assertLess(min(edge_widths(data, 0)), 164)
        fixed = repair_quad(data, 0, 164)
        self.assertGreaterEqual(min(edge_widths(fixed, 0)), 171.99)
        self.assertEqual(fixed[:32], data[:32])
        self.assertEqual(fixed[36:], data[36:])

    def test_refuses_unexpected_geometry(self):
        data = b''.join(struct.pack('<4f', x, y, 0, 1)
                        for x, y in [(0, -10), (0, 10), (100, -10), (100, 10)])
        with self.assertRaises(Exception):
            repair_quad(data, 0, 164)


if __name__ == '__main__':
    unittest.main()
