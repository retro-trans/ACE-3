import json
import struct
import unittest
import build_options_fit_patch as p


@unittest.skipUnless(p.OUTPUT.with_suffix('.json').exists(),'Build 0.1.40 first')
class OptionsFit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(p.OUTPUT.with_suffix('.json').read_text())
        cls.old={};cls.new={}
        for path,dest in ((p.BASE,cls.old),(p.OUTPUT,cls.new)):
            with path.open('rb') as f:
                fi,es=p.archive(f)
                for _,size,off,rid in es:
                    if rid in p.BUNDLES:f.seek(fi['offset']+off);dest[rid]=p.parts(f.read(size))

    def test_all_card_messages_fit_and_operation_cautions_are_complete(self):
        for rid in p.BUNDLES:
            font=self.new[rid][2500]
            rows={i:r.decode('cp932') for _,i,_,r in p.parse_table(self.new[rid][3041])[3]}
            self.assertEqual(len(rows),42)
            for i in (1,28,29,48):
                text=rows[i];self.assertIn('slot 1',text);self.assertIn('memory card (PS2)',text)
                self.assertEqual(len(text.split('\n')),3)
                self.assertIn('Do not turn off the power or insert\nor remove the memory card (PS2).',text)
                self.assertLessEqual(max(p.measure_text(font,text)),520)
            old={i:r.decode('cp932') for _,i,_,r in p.parse_table(self.old[rid][3041])[3]}
            for i in (3,5,19,31):self.assertEqual(rows[i],old[i])

    def test_requested_labels_and_help_in_all_three_copies(self):
        for rid in p.BUNDLES:
            for tid,targets in p.OPTIONS.items():
                rows={i:r.decode('cp932') for _,i,_,r in p.parse_table(self.new[rid][tid])[3]}
                for i,(_,target) in targets.items():self.assertEqual(rows[i],target)

    def test_option_labels_fit_and_only_horizontal_scale_changed(self):
        for report in self.report['changes']:
            rid=report['resource_id']
            for layout,tid,end in ((42,3070,14),(43,3071,12)):
                old=p.parts(self.old[rid][layout])[0];new=p.parts(self.new[rid][layout])[0]
                restored=bytearray(new)
                for row in report['layout_changes']:
                    if row['layout_id']!=layout:continue
                    a=row['offset'];restored[a:a+4]=old[a:a+4]
                self.assertEqual(bytes(restored),old)
                labels={i:r.decode('cp932') for _,i,_,r in p.parse_table(self.new[rid][tid])[3] if 5<=i<end}
                for i in range(p.u32(new,8)):
                    a=80+i*112;binding=struct.unpack_from('<h',new,a+86)[0]
                    if new[a+85]!=10 or not 103<=binding<103+len(labels):continue
                    text=labels[binding-98];width=max(p.measure_text(self.new[rid][2500],text))
                    self.assertLessEqual(width*struct.unpack_from('<f',new,a+32)[0],140.00001)
                    self.assertEqual(struct.unpack_from('<f',new,a+36)[0],1)

    def test_unselected_resources_and_text_rows_unchanged(self):
        for report in self.report['changes']:
            rid=report['resource_id'];old=self.old[rid];new=self.new[rid]
            self.assertEqual(old.keys(),new.keys())
            for k in old:
                if k not in (3041,3070,3071,42,43):self.assertEqual(old[k],new[k])
            for tid in (3041,3070,3071):
                before={i:(s,r) for s,i,_,r in p.parse_table(old[tid])[3]}
                after={i:(s,r) for s,i,_,r in p.parse_table(new[tid])[3]}
                changed={r['text_id'] for r in report['text_changes'] if r['table_id']==tid}
                self.assertEqual(before.keys(),after.keys())
                for i in before:
                    self.assertEqual(before[i][0],after[i][0])
                    if i not in changed:self.assertEqual(before[i],after[i])


if __name__=='__main__':unittest.main()
