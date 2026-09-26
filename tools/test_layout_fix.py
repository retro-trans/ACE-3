"""Validate layout allocation repairs without touching non-text fields."""
import struct
import unittest
from build_layout_fix import layout_changes


def layout(types=(10,4,5), capacities=(7,255,3)):
    d=bytearray(80+112*len(types))
    struct.pack_into('<5I',d,0,len(d),0x202,len(types),80,32)
    for i,(kind,cap) in enumerate(zip(types,capacities)):
        at=80+i*112
        d[at+0x55]=kind
        struct.pack_into('<h',d,at+0x56,100+i)
        struct.pack_into('<H',d,at+0x62,cap)
    return bytes(d)


class LayoutTests(unittest.TestCase):
    def test_only_small_text_allocations_change(self):
        d=layout();changes=layout_changes(d)
        self.assertEqual(len(changes),1)
        c=changes[0]
        self.assertEqual(c['offset'],80+0x62)
        self.assertEqual(c['before'],b'\x07\x00')
        self.assertEqual(c['after'],b'\x80\x00')
        self.assertEqual(c['binding'],100)

    def test_nested_offsets_and_external_padding(self):
        d=layout();parent=bytearray(32)+d+b'TAIL'
        parent[:4]=b'BND\0'
        struct.pack_into('<II',parent,4,len(parent)-4,1)
        struct.pack_into('<II',parent,16,37,32)
        c=layout_changes(parent,1000,(8,))[0]
        self.assertEqual(c['path'],[8,37])
        self.assertEqual(c['offset'],1000+32+80+0x62)

    def test_unknown_record_extent_is_rejected(self):
        d=bytearray(layout());struct.pack_into('<I',d,8,10000)
        with self.assertRaisesRegex(ValueError,'Unknown layout'):
            layout_changes(d)

    def test_zero_default_and_existing_large_allocations(self):
        c=layout_changes(layout((4,10,11,12),(0,128,200,255)))
        self.assertEqual(len(c),1)
        self.assertEqual(c[0]['old_capacity'],32)


if __name__=='__main__':unittest.main()
