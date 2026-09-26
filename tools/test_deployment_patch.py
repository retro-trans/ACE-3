import json
import re
import unittest
from build_deployment_patch import plan, fit, INPUT, BASE
from build_ui_patch import ROOT
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts
from build_hangar_fix import layouts


class DeploymentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.changes,cls.reports,cls.inventory=plan()
        cls.before={}
        with BASE.open('rb') as f:
            fi,es=archive(f)
            for _,sz,off,rid in es:
                if rid in cls.changes:
                    f.seek(fi['offset']+off);cls.before[rid]=f.read(sz)
        cls.font=parts(cls.before[4002050])[2500]

    def test_complete_category_in_every_copy(self):
        self.assertEqual([(rid,n) for rid,tid,n in self.inventory if tid==3013],
                         [(4002050,181),(4002053,181),(4002057,181)])
        for rid in (4002050,4002053,4002057):
            original=parse_table(parts(self.before[rid])[3013])[3]
            result=parse_table(parts(self.changes[rid])[3013])[3]
            self.assertEqual([(s,i) for s,i,_,_ in original],[(s,i) for s,i,_,_ in result])
            self.assertTrue(all(not re.search('[\u3040-\u30ff\u4e00-\u9fff]',raw.decode('cp932')) for _,_,_,raw in result))

    def test_no_allocator_or_unrelated_asset_changes(self):
        for rid,data in self.changes.items():
            before,after=parts(self.before[rid]),parts(data)
            self.assertEqual(before.keys(),after.keys())
            changed={k for k in before if before[k]!=after[k]}
            self.assertLessEqual(changed,{3013,3014,3022,3072,3093})
        self.assertEqual(sum(len(r['allocations']) for r in self.reports),0)

    def test_format_argument_loss_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Format arguments'):
            fit('Upgrade?', '%s',3013,190,self.font,['Ixbrau'])

    def test_discount_icon_is_preserved(self):
        with self.assertRaisesRegex(ValueError,'Discount icon'):
            fit('Upgrade %s?', '%s ㍻',3013,192,self.font,['Ixbrau'])

    def test_expanded_dialog_capacity_is_checked(self):
        with self.assertRaisesRegex(ValueError,'Capacity exceeded'):
            fit('%s\n%s\n%s','%s\n%s\n%s',3013,163,self.font,['W'*100])


if __name__=='__main__':unittest.main()
