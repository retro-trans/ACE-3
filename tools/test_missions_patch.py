import json
import re
import unittest
from build_missions_patch import plan, INPUT, BASE
from dialogue_corpus import archive, parse_table
from build_flight_save_patch import parts

JP = re.compile('[぀-ヿ一-鿿]')
NUMBERS = re.compile('[0-9０-９]+')


def digits(text):
    return [int(n) for n in NUMBERS.findall(text)]


class MissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.changes, cls.reports, cls.inventory = plan()
        cls.doc = json.loads(INPUT.read_text(encoding='utf-8'))
        cls.before = {}
        with BASE.open('rb') as f:
            fi, es = archive(f)
            for _, sz, off, rid in es:
                if rid in cls.changes or rid == 4002055:
                    f.seek(fi['offset']+off); cls.before[rid] = f.read(sz)

    def test_both_categories_complete_in_three_copies(self):
        self.assertEqual(sorted((rid, tid) for rid, tid, _ in self.inventory),
                         [(rid, tid) for rid in (4002050, 4002054, 4002057) for tid in (3055, 3057)])
        for rid, tid, _ in self.inventory:
            rows = parse_table(parts(self.changes[rid])[tid])[3]
            self.assertFalse([i for _, i, _, r in rows if JP.search(r.decode('cp932'))])

    def test_every_number_survives_translation(self):
        for cat in self.doc['categories']:
            for row in cat['rows']:
                self.assertEqual(sorted(digits(row['source'])), sorted(digits(row['en'])), (cat['table_id'], row['text_id']))

    def test_unnumbered_titles_match_their_numbered_twins(self):
        titles = {r['text_id']:r['en'] for r in self.doc['categories'][0]['rows']}
        for plain, numbered in ((450, 280), (451, 130), (452, 170), (453, 180), (454, 70), (455, 310), (457, 350)):
            self.assertEqual(titles[numbered].split(None, 1)[1], titles[plain])
        self.assertEqual((titles[30], titles[310], titles[340]), (titles[31], titles[311], titles[341]))

    def test_legacy_tables_and_other_resources_are_untouched(self):
        self.assertNotIn(4002055, self.changes)
        for rid, data in self.changes.items():
            before, after = parts(self.before[rid]), parts(data)
            self.assertEqual({k for k in before if before[k] != after[k]}, {3055, 3057})
        self.assertEqual(sum(len(r['allocations']) for r in self.reports), 0)

    def test_secret_goals_stay_within_two_lines(self):
        for row in self.doc['categories'][1]['rows']:
            self.assertLessEqual(len(row['en'].split('\n')), 2)


if __name__ == '__main__': unittest.main()
