"""Regression checks for fixed name fields and the 0.1.38 disc."""
import json
import struct
import unittest
import build_remaining_labels_patch as p


class FixedNames(unittest.TestCase):
    def test_reject_overlong_name_without_touching_stats(self):
        data=bytearray(2192)
        data[:4]=b'PRM\0';struct.pack_into('<I',data,4,2176)
        data[16:48]=b'Old\0'+b' '*28
        data[48:2176]=bytes((i%256 for i in range(2128)))
        data[2176:2180]=b'END\0';struct.pack_into('<I',data,2180,16)
        source=bytes(data)
        with self.assertRaisesRegex(ValueError,'fixed field'):
            p.patch_names(source,[{'source':'Old','en':'X'*32}])
        new,_=p.patch_names(source,[{'source':'Old','en':'Ixbrau'}])
        self.assertEqual(new[48:],source[48:])
        self.assertEqual(new[16:48],b'Ixbrau\0'+b' '*25)


@unittest.skipUnless(p.OUTPUT.exists(),'Build 0.1.38 first')
class BuiltDisc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(p.OUTPUT.with_suffix('.json').read_text(encoding='utf-8'))
        cls.names=json.loads((p.INPUT/'parameter_names_038.json').read_text(encoding='utf-8'))['rows']
        cls.old={};cls.new={}
        wanted={r['resource_id'] for r in cls.report['changes']}|set(range(1200000,1200008))|{4002050,4002053,4002054,4002057}
        wanted|={r['resource_id'] for r in cls.names}|{r['resource_id']-2300000 for r in cls.names}
        for path,dest in ((p.BASE,cls.old),(p.OUTPUT,cls.new)):
            with path.open('rb') as f:
                fi,es=p.archive(f)
                for _,size,off,rid in es:
                    if rid in wanted:f.seek(fi['offset']+off);dest[rid]=f.read(size)

    def test_shared_confirmation_all_copies_and_controls(self):
        rows=json.loads((p.INPUT/'shared_prompts_038.json').read_text(encoding='utf-8'))['rows']
        for rid,at in p.PROMPTS.items():
            before=self.old[rid];after=self.new[rid]
            self.assertEqual(before[:at],after[:at]);self.assertEqual(before[at+416:],after[at+416:])
            for row in rows:
                actual=p.game_lookup(after[at:at+416],row['text_id']).decode('cp932')
                self.assertEqual(actual,row['en']);self.assertEqual(p.controls(actual),p.controls(row['source']))

    def test_model_stats_and_scripts_unchanged(self):
        total=0
        for r in self.report['changes']:
            if r['kind']!='parameter_names':continue
            rid=r['resource_id'];before=self.old[rid];after=self.new[rid];restored=bytearray(after)
            self.assertEqual(p.chunks(before),p.chunks(after))
            for e in r['edits']:
                a=e['offset'];self.assertEqual(after[a:a+32].split(b'\0')[0].decode('cp932'),e['en'])
                restored[a:a+32]=before[a:a+32];total+=1
            self.assertEqual(bytes(restored),before)
        self.assertEqual(total,self.report['checks']['changed_model_fields'])
        self.assertEqual(total,344)
        self.assertEqual(self.new[2801040][759088:759095],b'Ixbrau\0')
        groups={}
        for row in self.names:groups.setdefault(row['resource_id'],[]).append(row)
        for live,rows in groups.items():
            rows.sort(key=lambda r:r['chunk_offset'])
            for rid in (live,live-2300000):
                fields=[a for tag,a,b in p.chunks(self.new[rid]) if tag==b'PRM\0']
                self.assertEqual(len(fields),len(rows))
                for a,row in zip(fields,rows):
                    self.assertEqual(self.new[rid][a+16:a+48].split(b'\0')[0].decode('cp932'),row['en'])

    def test_abilities_and_alignment_inherited(self):
        rows=json.loads((p.INPUT/'abilities_036.json').read_text(encoding='utf-8'))['rows']
        for rid in (4002050,4002053,4002054,4002057):
            table=p.parts(self.new[rid])[3079]
            for row in rows:self.assertEqual(p.game_lookup(table,row['text_id']).decode('cp932'),row['en'])
        for rid in range(1200000,1200008):self.assertEqual(self.old[rid],self.new[rid])


if __name__=='__main__':unittest.main()
