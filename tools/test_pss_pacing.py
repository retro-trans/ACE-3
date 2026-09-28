"""Regression checks for multi-packet pictures and exact 30 fps PSS clocks."""
import struct
import unittest
from pss_inspect import packets
from pss_remux import plan, stamp
from pss_video import elementary

def picture(n, length):
    return b'\0\0\1\0'+struct.pack('>H',(n<<6)|8)+b'V'*(length-6)

def fixture():
    result=bytearray()
    for n in range(16):
        body=picture(n//3,20) if n in (0,3,6,9) else b''
        body=body.ljust(96,b'\0')
        header=b'\x83\xc0\x0a'+stamp(3,9000)+stamp(1,6000)
        result+=b'\0\0\1\xe0'+struct.pack('>H',len(header)+len(body))+header+body
        result+=b'\0\0\1\xbe\0\x08AUDIO123'
    return bytes(result)+b'\0\0\1\xb9'

class PacingTests(unittest.TestCase):
    def test_cross_packet_picture_keeps_extents_and_next_picture(self):
        original=fixture()
        es=picture(0,120)+picture(1,31)+picture(2,135)+picture(3,29)
        out,report=plan(original,es,ticks=3000,pace_to_original=True,max_lead_packets=0)
        self.assertEqual(len(out),len(original))
        self.assertEqual(report['pictures_new'],4)
        for at,sid,head,pay,length,info in packets(original):
            if sid!=0xe0:self.assertEqual(original[at:pay+length],out[at:pay+length])
        for n,size in enumerate((120,31,135,29)):
            self.assertIn(picture(n,size),elementary(out))
        pts=sorted(x[-1]['pts'] for x in packets(out) if x[1]==0xe0 and 'pts' in x[-1])
        self.assertEqual(pts,[9000,12000,15000,18000])
        self.assertEqual(report['max_packets_early'],0)

    def test_default_clock_remains_2997(self):
        out,_=plan(fixture(),b''.join(picture(n,96) for n in range(4)))
        pts=sorted(x[-1]['pts'] for x in packets(out) if x[1]==0xe0 and 'pts' in x[-1])
        self.assertEqual(pts,[9000,12003,15006,18009])

    def test_reject_changed_frame_count_when_pacing(self):
        with self.assertRaisesRegex(ValueError,'picture count'):
            plan(fixture(),picture(0,30),pace_to_original=True)

if __name__=='__main__':unittest.main()
