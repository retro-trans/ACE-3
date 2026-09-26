"""Regression checks for complete categories, controls and UI allocations."""
import copy
import json
import struct
import unittest
from build_flight_save_patch import BASE, INPUTS, parts, plan, replace_table, flight_capacity, placeholders
from dialogue_corpus import archive, parse_table
from build_ui_patch import u32


class FlightSavePatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.replacements, cls.reports, cls.discovered = plan()
        cls.before = {}
        with BASE.open('rb') as f:
            fi, entries = archive(f)
            for rid in cls.replacements:
                _,size,off,_ = next(e for e in entries if e[3] == rid)
                f.seek(fi['offset']+off)
                cls.before[rid] = parts(f.read(size))
        cls.flight = next(c for c in json.loads(INPUTS[0].read_text(encoding='utf-8'))['categories'] if c['table_id'] == 3092)
        cls.font = cls.before[4002050][2500]

    def test_all_three_flight_copies_and_both_layouts(self):
        expected = {r['slot']:r['en'] for r in self.flight['rows']}
        for rid in (4002050,4002054,4002057):
            current = parts(self.replacements[rid])
            self.assertEqual({s:r.decode('cp932').split() for s,_,_,r in parse_table(current[3092])[3]},
                             {s:t.split() for s,t in expected.items()})
        for rid in (4002050,4002057):
            before = self.before[rid][27]
            after = parts(self.replacements[rid])[27]
            self.assertEqual(after,flight_capacity(before))
            # The only layout mutation is the low byte of capacity200 ->255.
            self.assertEqual(sum(a != b for a,b in zip(before,after)),1)
            self.assertEqual(len(before),len(after))

    def test_relocation_preserves_original_pool_null_slots_and_other_resources(self):
        for report in self.reports:
            rid = report['resource_id']
            before,after = self.before[rid],parts(self.replacements[rid])
            for key,value in before.items():
                if key not in report['changed_subresources']:
                    self.assertEqual(value,after[key])
            for c in report['categories']:
                tid = c['table_id']
                size,ptr,count,rows = parse_table(before[tid])
                ns,np,nc,new_rows = parse_table(after[tid])
                self.assertEqual((ptr,count),(np,nc))
                self.assertEqual([(s,i) for s,i,_,_ in rows],[(s,i) for s,i,_,_ in new_rows])
                self.assertEqual(before[tid][ptr+4*count:size],after[tid][ptr+4*count:size])
                for row,(_,_,address,_) in zip(c['rows'],new_rows):
                    if row['changed']:
                        self.assertGreaterEqual(address,size)

    def test_missing_rows_wrong_source_and_lost_button_are_rejected(self):
        table = self.before[4002050][3092]
        d = copy.deepcopy(self.flight)
        d['rows'].pop()
        with self.assertRaisesRegex(ValueError,'Incomplete'):
            replace_table(table,d,self.font)
        d = copy.deepcopy(self.flight)
        d['rows'][0]['source'] = 'Wrong source'
        with self.assertRaisesRegex(ValueError,'Source mismatch'):
            replace_table(table,d,self.font)
        d = copy.deepcopy(self.flight)
        d['rows'][1]['en'] = 'Select'
        with self.assertRaisesRegex(ValueError,'Control sequence'):
            replace_table(table,d,self.font)

    def test_dynamic_slots_and_double_tap_counts_survive(self):
        for report in self.reports:
            before = self.before[report['resource_id']]
            for c in report['categories']:
                originals = {s:r.decode('cp932') for s,_,_,r in parse_table(before[c['table_id']])[3]}
                for row in c['rows']:
                    self.assertEqual(placeholders(originals[row['slot']]),placeholders(row['target']))
        d = copy.deepcopy(self.flight)
        row = next(r for r in d['rows'] if r['slot'] == 50)
        row['en'] = row['en'].replace('③×２','③×１')
        with self.assertRaisesRegex(ValueError,'Runtime placeholder'):
            replace_table(self.before[4002050][3092],d,self.font)


if __name__ == '__main__':
    unittest.main()
