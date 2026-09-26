"""Regressions for full crawl coverage, relocation and chunk preservation."""
import copy
import json
import unittest
from build_history_patch import BASE, TRANSLATION, chunks, plan, rebuild_history
from build_ui_patch import inner_bnd, u32
from dialogue_corpus import archive, parse_table


class HistoryPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.replacements, cls.reports = plan()
        with BASE.open('rb') as f:
            fi, entries = archive(f)
            def get(rid):
                _,size,off,_ = next(e for e in entries if e[3] == rid)
                f.seek(fi['offset']+off)
                return f.read(size)
            cls.source = get(4010)
            d = get(1200000)
            cls.font = next(d[a:z] for k,a,z in inner_bnd(d) if k == 2500)
        cls.draft = json.loads(TRANSLATION.read_text(encoding='utf-8'))
        cls.table = cls.source[3374368:3374368+2304]

    def test_all_meaning_survives_reflow_and_fits(self):
        report = self.reports[0]
        self.assertEqual(report['source_rows'], 39)
        self.assertEqual(len(report['groups']), 20)
        for source, result in zip(self.draft['groups'], report['groups']):
            self.assertEqual(' '.join(source['en'].split()), ' '.join(result['lines']))
            self.assertLessEqual(max(result['widths']), report['width_limit'])
        self.assertLess(report['last_text_slot'], 200)
        self.assertEqual(report['groups'][-1]['lines'][-1], 'recorded strikes Saint Cruz.')

    def test_new_pool_is_relocated_and_old_script_chunks_are_exact(self):
        result, _ = rebuild_history(self.table, self.draft, self.font)
        _,ptr,count,rows = parse_table(result)
        self.assertEqual(result[ptr+count*4:2304], self.table[ptr+count*4:])
        self.assertTrue(all(at >= 2304 for _,_,at,_ in rows))
        patched = self.replacements[4010]
        before,after = chunks(self.source),chunks(patched)
        self.assertEqual([t for t,_,_ in before], [t for t,_,_ in after])
        for (tag,a,z),(_,b,y) in zip(before,after):
            if tag != b'STUF':self.assertEqual(self.source[a:z],patched[b:y])
        _,a,z = next(t for t in after if t[0] == b'STUF')
        bundle = patched[a+16:z]
        _,lo,hi = inner_bnd(bundle)[0]
        self.assertEqual(parse_table(bundle[lo:hi])[0],len(result))

    def test_missing_review_or_source_mismatch_is_rejected(self):
        d = copy.deepcopy(self.draft)
        d['review']['status'] = 'draft'
        with self.assertRaisesRegex(ValueError, 'Unreviewed'):
            rebuild_history(self.table,d,self.font)
        d['review']['status'] = 'meaning_reviewed'
        d['groups'][0]['source_rows'][0]['source_sha256'] = 'bad'
        with self.assertRaisesRegex(ValueError, 'hash/ID'):
            rebuild_history(self.table,d,self.font)


if __name__ == '__main__':unittest.main()
