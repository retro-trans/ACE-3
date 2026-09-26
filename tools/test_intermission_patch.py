"""Unit-name relocation and runtime-expanded notice regression checks."""
import copy
import unittest
from build_intermission_patch import BASE,plan,parts,parse_table,archive,replace_rows,load_translations,notice_fit


class IntermissionPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.changes,cls.reports,cls.inventory = plan()
        cls.before = {}
        with BASE.open('rb') as f:
            fi,entries = archive(f)
            for rid in cls.changes:
                _,size,off,_ = next(e for e in entries if e[3] == rid)
                f.seek(fi['offset']+off)
                cls.before[rid] = parts(f.read(size))

    def test_complete_roster_and_notice_copies(self):
        notices,names = load_translations()
        for rid in (4002050,4002053,4002054,4002057):
            source = parse_table(self.before[rid][3000])[3]
            actual = parse_table(parts(self.changes[rid])[3000])[3]
            self.assertEqual(len(actual),106)
            self.assertEqual([r.decode('cp932') for _,_,_,r in actual],
                             [names[r.decode('cp932')] for _,_,_,r in source])
        expected = {r['slot']:r['en'] for r in notices['rows']}
        for rid in (4002050,4002054,4002057):
            self.assertEqual({s:r.decode('cp932') for s,_,_,r in parse_table(parts(self.changes[rid])[3069])[3]},expected)

    def test_all_runtime_expansions_fit_six_line_dialog(self):
        for report in self.reports:
            fit = report['notice_fit']
            if fit:
                self.assertGreaterEqual(fit['expansions_checked'],600)
                self.assertLessEqual(fit['max_width'],410)
                self.assertLessEqual(fit['six_line_capacity_bound'],255)
                self.assertEqual(fit['runtime_roster_count'],103)
                self.assertLessEqual(fit['max_encoded_bytes'],63)
        notices,_ = load_translations()
        with self.assertRaisesRegex(ValueError,'too wide|overflow|64-byte record'):
            notice_fit(notices,['W'*100],self.before[4002050][2500])

    def test_encoded_record_limit_is_enforced(self):
        # Double-byte glyphs can overflow the sprintf record before reaching
        # the shared widget's character capacity.
        with self.assertRaisesRegex(ValueError,'64-byte record'):
            notice_fit({'rows':[{'slot':9,'en':'%s'}]},['界'*32],self.before[4002050][2500])

    def test_ids_nulls_source_pools_and_unrelated_parts_preserved(self):
        for report in self.reports:
            before = self.before[report['resource_id']]
            after = parts(self.changes[report['resource_id']])
            for tid in before:
                if tid not in report['changed_subresources']:
                    self.assertEqual(before[tid],after[tid])
            for row in report['tables']:
                tid = row['table_id']
                size,ptr,count,old = parse_table(before[tid])
                _,np,nc,new = parse_table(after[tid])
                self.assertEqual((ptr,count),(np,nc))
                self.assertEqual([(s,i) for s,i,_,_ in old],[(s,i) for s,i,_,_ in new])
                self.assertEqual(before[tid][ptr+4*count:size],after[tid][ptr+4*count:size])

    def test_invalid_source_or_printf_changes_rejected(self):
        table = self.before[4002050][3069]
        source = dict((s,r.decode('cp932')) for s,_,_,r in parse_table(table)[3])[9]
        with self.assertRaisesRegex(ValueError,'Printf arguments'):
            replace_rows(table,{9:(source,'Added: %d')})
        with self.assertRaisesRegex(ValueError,'Source preimage'):
            replace_rows(table,{9:('Incorrect source','Added: %s')})


if __name__ == '__main__':unittest.main()
