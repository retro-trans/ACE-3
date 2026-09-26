import json
import re
import unittest
from build_dialogs_patch import plan, fit, INPUT, BASE
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts

JP = re.compile('[぀-ヿ一-鿿]')
TEXT = {3009, 3013, 3021, 3037, 3040, 3044, 3054, 3070, 3072, 3073, 3076, 3086, 3090, 3091}


class DialogsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.changes, cls.reports, cls.inventory = plan()
        cls.doc = json.loads(INPUT.read_text(encoding='utf-8'))
        cls.before = {}
        with BASE.open('rb') as f:
            fi, es = archive(f)
            for _, sz, off, rid in es:
                if rid in cls.changes:
                    f.seek(fi['offset']+off); cls.before[rid] = f.read(sz)
        cls.font = parts(cls.before[4002050])[2500]

    def test_complete_categories_in_every_copy(self):
        copies = {tid:[rid for rid, t, _ in self.inventory if t == tid] for tid in TEXT}
        self.assertEqual(copies[3091], [4002050, 4002054, 4002057])
        self.assertEqual(copies[3009], [4002052])
        self.assertEqual(copies[3044], [4002054])
        self.assertEqual(copies[3054], [4002050, 4002055, 4002057])
        complete = {c['table_id'] for c in self.doc['categories'] if c['complete']}
        for rid, tid, _ in self.inventory:
            if tid not in complete: continue
            rows = parse_table(parts(self.changes[rid])[tid])[3]
            self.assertFalse([i for _, i, _, r in rows if JP.search(r.decode('cp932'))], (rid, tid))

    def test_screenshot_dialog_is_translated(self):
        rows = {i:r.decode('cp932') for _, i, _, r in parse_table(parts(self.changes[4002050])[3091])[3]}
        self.assertIn('Ace Series', rows[12])
        self.assertEqual(rows[12].count('㍻'), 1)
        self.assertLessEqual(len(rows[12].split('\n')), 10)

    def test_only_text_tables_change_and_no_allocation_grows(self):
        for rid, data in self.changes.items():
            before, after = parts(self.before[rid]), parts(data)
            self.assertEqual(before.keys(), after.keys())
            self.assertLessEqual({k for k in before if before[k] != after[k]}, TEXT)
        self.assertEqual(sum(len(r['allocations']) for r in self.reports), 0)

    def test_ids_slots_and_excluded_rows_are_preserved(self):
        for rid, data in self.changes.items():
            before, after = parts(self.before[rid]), parts(data)
            for tid in TEXT & before.keys():
                old, new = parse_table(before[tid])[3], parse_table(after[tid])[3]
                self.assertEqual([(s, i) for s, i, _, _ in old], [(s, i) for s, i, _, _ in new])
        # Song titles stay out of scope and untouched.
        old = {i:r for _, i, _, r in parse_table(parts(self.before[4002050])[3072])[3]}
        new = {i:r for _, i, _, r in parse_table(parts(self.changes[4002050])[3072])[3]}
        self.assertTrue(all(old[i] == new[i] for i in range(30, 75)))

    def test_free_mission_labels_fit_their_fields(self):
        rows = {i:r.decode('cp932') for _, i, _, r in parse_table(parts(self.changes[4002050])[3054])[3]}
        self.assertEqual((rows[14], rows[71], rows[72]), ('Records', 'Secret Goal', 'Status'))

    def test_stray_percent_and_lost_controls_are_rejected(self):
        row = {'en':'Upgrade?\n%s\n(㍻ -25%)', 'dialog':True, 'limit':410}
        with self.assertRaisesRegex(ValueError, 'Stray percent'):
            fit(row, '%s ㍻', self.font)
        with self.assertRaisesRegex(ValueError, 'Control code'):
            fit({'en':'Back', 'dialog':False, 'limit':620}, '戻る：×', self.font)
        with self.assertRaisesRegex(ValueError, 'Width exceeded'):
            fit({'en':'Combat Records', 'dialog':False, 'limit':131}, '戦闘記録', self.font)


if __name__ == '__main__': unittest.main()
