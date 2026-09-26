import struct
import unittest
import build_objective_alignment_patch as p


class ObjectiveAlignment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.changes,cls.summary=p.plan();cls.layouts=[]
        with p.BASE.open('rb') as f:
            fi,es=p.archive(f)
            for rid in cls.summary['layout_bundles']:
                e=next(e for e in es if e[3]==rid);origin=fi['offset']+e[2]
                f.seek(origin);data=bytearray(f.read(e[1]));before=bytes(data)
                for c in cls.changes:
                    if c['resource_id']==rid:
                        a=c['offset']-origin;data[a:a+len(c['after'])]=c['after']
                selfparts=p.parts(bytes(data));key=57 if rid==1200007 else 5
                cls.layouts.append((rid,p.parts(selfparts[key])[0],51 if rid==1200007 else 45))
                if rid==1200000:
                    cls.before=p.parts(p.parts(before)[key])[0]

    def test_same_left_edge_and_separate_heading_rows(self):
        for rid,d,first in self.layouts:
            rows=[struct.unpack_from('<2f',d,80+(first+i)*112) for i in range(7)]
            self.assertTrue(all(x==p.LEFT for x,y in rows),rid)
            self.assertAlmostEqual(rows[1][1]-rows[0][1],24,places=4)
            self.assertAlmostEqual(rows[5][1]-rows[4][1],24,places=4)
            for i,j in ((1,2),(2,3),(3,4),(5,6)):
                self.assertGreater(rows[j][1]-rows[i][1],20,rid)

    def test_panels_contain_full_condition_rows_and_do_not_overlap(self):
        for rid,d,first in self.layouts:
            a=80+(first-1)*112;bx,by=struct.unpack_from('<2f',d,a);v=p.u32(d,a+64)
            ys=[by+struct.unpack_from('<f',d,v+i*16+4)[0] for i in range(22)]
            self.assertGreater(min(ys[11:])-max(ys[:11]),5)
            right=bx+max(struct.unpack_from('<f',d,v+i*16)[0] for i in range(22))
            self.assertGreater(right-p.LEFT,p.WIDTH+5)
            for j in range(7):
                y=struct.unpack_from('<f',d,80+(first+j)*112+4)[0]
                panel=ys[:11] if j<4 else ys[11:]
                self.assertGreater(y-9.5,min(panel));self.assertLess(y+9.5,max(panel))

    def test_all_translated_conditions_fit_and_preserve_allocations(self):
        self.assertEqual(len(self.summary['objective_occurrences']),6)
        self.assertGreaterEqual(len(self.summary['width_checks']),900)
        self.assertTrue(all(r['max_width']<=355 for r in self.summary['width_checks']))
        for c in self.changes:
            self.assertEqual(len(c['before']),len(c['after']))
            if 'old' in c:
                self.assertEqual(c['old'].count(' / '),c['new'].count(' / '))
                self.assertEqual(c['after'].split(b'\0')[0].decode('cp932'),c['new'])

    def test_reject_unexpected_layout_instead_of_patching_wrong_widgets(self):
        bad=bytearray(self.before);struct.pack_into('<f',bad,80+46*112,123)
        with self.assertRaisesRegex(ValueError,'X preimage'):
            p.layout_edits(bytes(bad),0,[5,0],1200000)


if __name__=='__main__':unittest.main()
