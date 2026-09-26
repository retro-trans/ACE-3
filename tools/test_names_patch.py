import json
import re
import unittest
from build_names_patch import plan, INPUT, BASE
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts
from build_ui_patch import ROOT

JP = re.compile('[぀-ヿ一-鿿]')
EXPECTED = {3014:[4002050, 4002052, 4002053, 4002054, 4002057], 3026:[4002053], 3074:[4002054], 3021:list(range(1200000, 1200008))}


class NameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.changes, cls.reports, cls.inventory = plan()
        cls.before = {}
        with BASE.open('rb') as f:
            fi, es = archive(f)
            for _, sz, off, rid in es:
                if rid in cls.changes:
                    f.seek(fi['offset']+off); cls.before[rid] = f.read(sz)

    def test_every_copy_of_every_family_is_english(self):
        for tid, bundles in EXPECTED.items():
            self.assertEqual(sorted(rid for rid, t, _ in self.inventory if t == tid), bundles)
            for rid in bundles:
                rows = parse_table(parts(self.changes[rid])[tid])[3]
                self.assertFalse([i for _, i, _, r in rows if JP.search(r.decode('cp932'))], (rid, tid))

    def test_same_character_id_gets_consistent_names(self):
        short = {}
        for tid, bundles in EXPECTED.items():
            if tid == 3014: continue
            for rid in bundles:
                for _, i, _, r in parse_table(parts(self.changes[rid])[tid])[3]:
                    short.setdefault(i, set()).add(r.decode('cp932'))
        # The disc itself labels Gym Ghingham by given name in one table and by surname in another.
        self.assertEqual({i:v for i, v in short.items() if len(v) > 1}, {20110:{'Gym', 'Ghingham'}})
        self.assertEqual((short[17080], short[21030], short[1060]), ({'Sala'}, {'Sara'}, {'Faye'}))

    def test_names_match_the_glossary(self):
        glossary = {e['name']['en'] for e in json.loads((ROOT/'work/glossary/glossary.json').read_text(encoding='utf-8'))['entries']
                    if e['id'].startswith('char.')}
        full = {r.decode('cp932') for _, _, _, r in parse_table(parts(self.changes[4002050])[3014])[3]}
        for name in ('Barrel Orland', 'Faye Rochenante', 'Amuro Ray', 'Kaine Wakaba', 'Ruri Hoshino'):
            self.assertIn(name, glossary); self.assertIn(name, full)

    def test_ids_slots_and_other_resources_are_untouched(self):
        for rid, data in self.changes.items():
            before, after = parts(self.before[rid]), parts(data)
            changed = {k for k in before if before[k] != after[k]}
            self.assertLessEqual(changed, {3014, 3021, 3026, 3074})
            for tid in changed:
                self.assertEqual([(s, i) for s, i, _, _ in parse_table(before[tid])[3]], [(s, i) for s, i, _, _ in parse_table(after[tid])[3]])
        self.assertEqual(sum(len(r['allocations']) for r in self.reports), 0)

    def test_encyclopedia_menu_table_with_the_same_id_is_left_alone(self):
        before, after = parts(self.before[4002054]), parts(self.changes[4002054])
        self.assertEqual(before[3021], after[3021])


if __name__ == '__main__': unittest.main()
