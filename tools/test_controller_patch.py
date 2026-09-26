"""Guard the controller image patch against mapping and artwork corruption."""
import unittest
from build_controller_patch import plan, captions


class ControllerPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.changes=plan()

    def test_both_schemes_have_complete_and_correct_captions(self):
        rows={tid:{key:text for key,text,_,_ in captions(tid)} for tid in (50512,50513)}
        self.assertEqual(len(rows[50512]),11);self.assertEqual(len(rows[50513]),11)
        self.assertEqual(rows[50512]['controls.main_shot'],'Main Fire')
        self.assertEqual(rows[50512]['controls.shift_menu'],'Shift Menu')
        self.assertEqual(rows[50513]['controls.fire'],'Fire')
        self.assertEqual(rows[50513]['controls.select_menu'],'Select Menu')
        self.assertNotIn('controls.main_shot',rows[50513])

    def test_only_caption_pixels_change(self):
        for c in self.changes:
            a,b=c['before'],c['after'];self.assertEqual(len(a),len(b))
            self.assertEqual(a[:32],b[:32]);self.assertEqual(a[65568:],b[65568:])
            allowed=set()
            for row in c['report']['captions']:
                x,y,w,h=row['rectangle']
                allowed.update(32+yy*256+xx for yy in range(y,y+h) for xx in range(x,x+w))
                self.assertLessEqual(row['ink_size'][0],w);self.assertLessEqual(row['ink_size'][1],h)
            changed={i for i,(v,z) in enumerate(zip(a,b)) if v!=z}
            self.assertTrue(changed);self.assertTrue(changed<=allowed)
            # Question icon and button/leader-line pixels must remain exact.
            for y in range(7,27):self.assertEqual(a[32+y*256+51:32+y*256+64],b[32+y*256+51:32+y*256+64])


if __name__=='__main__':unittest.main()
