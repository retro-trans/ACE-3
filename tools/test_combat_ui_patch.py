"""0.1.36 table-format regression checks and built-disc coverage checks."""
import json
import struct
import unittest
import build_combat_ui_patch as p


def table(magic=0, size=128, values=(b'Old', None, b'Other')):
    out=bytearray(size)
    struct.pack_into('<7I',out,0,magic,size,0,1,len(values),40,0)
    struct.pack_into('<3I',out,28,0,10,9+len(values))
    at=40+4*len(values)
    for i,value in enumerate(values):
        if value is not None:
            struct.pack_into('<I',out,40+i*4,at)
            out[at:at+len(value)+1]=value+b'\0';at+=len(value)+1
    return bytes(out)


class TableFormats(unittest.TestCase):
    def test_zero_magic_and_null_slots_survive_compaction(self):
        before=table();after=p.compact(before,{10:'New',12:'New'})
        self.assertEqual(len(after),len(before));self.assertEqual(after[:4],bytes(4))
        self.assertEqual(p.game_lookup(after,10),b'New')
        self.assertIsNone(p.game_lookup(after,11))
        self.assertEqual(p.game_lookup(after,12),b'New')
        self.assertIsNone(p.game_lookup(after,13))

    def test_singleton_uses_proven_compact_layout(self):
        before=table(65536,48,(b'A',));after=p.compact(before,{10:'Hikaru'})
        self.assertEqual(len(after),48);self.assertEqual(p.u32(after,20),24)
        self.assertEqual(p.game_lookup(after,10),b'Hikaru')

    def test_overflow_rejected_before_touching_following_chunk(self):
        with self.assertRaises(ValueError):p.compact(table(65536,48,(b'A',)),{10:'Way too long'})

    def test_append_preserves_zero_magic_and_null_slots(self):
        before=table();after=p.append(before,{0:('Old','A longer replacement')})
        self.assertEqual(after[:4],bytes(4));self.assertIsNone(p.game_lookup(after,11))
        self.assertEqual(p.game_lookup(after,12),b'Other')
        self.assertEqual(p.game_lookup(after,10),b'A longer replacement')


@unittest.skipUnless(p.OUTPUT.exists(),'Build 0.1.36 first for disc checks')
class BuiltDisc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(p.OUTPUT.with_suffix('.json').read_text(encoding='utf-8'))
        cls.docs=p.load_inputs();cls.old={};cls.new={}
        wanted={r['resource_id'] for r in cls.report['changes']}
        for path,dest in ((p.BASE,cls.old),(p.OUTPUT,cls.new)):
            with path.open('rb') as f:
                fi,es=p.archive(f)
                for _,size,off,rid in es:
                    if rid in wanted:f.seek(fi['offset']+off);dest[rid]=f.read(size)

    def test_all_104_shared_command_lists_and_inputs(self):
        lookup={r['source']:r['en'] for r in self.docs['commands']['rows']}
        for rid in (4002053,4002054):
            old=p.parts(p.parts(self.old[rid])[3049]);new=p.parts(p.parts(self.new[rid])[3049])
            self.assertEqual(len(new),104);count=0
            for unit,t in old.items():
                self.assertEqual(new[unit][:4],t[:4])
                for _,tid,_,raw in p.parsed(t)[3]:
                    self.assertEqual(p.game_lookup(new[unit],tid),lookup[raw.decode('cp932')].encode('cp932'));count+=1
            self.assertEqual(count,1966)
        for r in self.report['changes']:
            if r['kind']!='command_inputs':continue
            rid=r['resource_id'];old=p.parts(self.old[rid])[r['path'][0]];new=p.parts(self.new[rid])[r['path'][0]]
            for _,tid,_,raw in p.parsed(old)[3]:
                self.assertEqual(p.controls(raw.decode('cp932')),p.controls(p.game_lookup(new,tid).decode('cp932')))

    def test_all_abilities_support_names_categories_triggers(self):
        lookup={r['source']:r['en'] for r in self.docs['abilities']['rows']}
        for rid in (4002050,4002053,4002054,4002057):
            old=p.parts(self.old[rid])[3079];new=p.parts(self.new[rid])[3079]
            self.assertEqual(len(p.parsed(new)[3]),338)
            for _,tid,_,raw in p.parsed(old)[3]:
                self.assertEqual(p.game_lookup(new,tid),lookup[raw.decode('cp932')].encode('cp932'))

    def test_map_categories_and_nadesico_scene_label(self):
        menu=p.parts(self.new[4002052])
        for tid,count in ((3061,102),(3062,60),(3063,29)):
            rows=p.parsed(menu[tid])[3];self.assertEqual(len(rows),count)
            for _,_,_,raw in rows:self.assertIsNone(p.JP.search(raw.decode('cp932')))
        labels=[e['target'] for r in self.report['changes'] if r['kind']=='scene_labels' for e in r['edits']]
        self.assertIn('Nadesico B',labels)

    def test_scene_script_and_model_boundaries_unchanged(self):
        for report in self.report['changes']:
            if report['kind'] not in ('scene_labels','model_labels'):continue
            rid=report['resource_id'];old=self.old[rid];new=self.new[rid];restored=bytearray(new)
            self.assertEqual(len(old),len(new))
            for e in report['edits']:
                a,b=e['offset'],e['offset']+e['size'];restored[a:b]=old[a:b]
                if 'target' in e:self.assertEqual(p.game_lookup(new[a:b],1),e['target'].encode('cp932'))
            self.assertEqual(bytes(restored),old,rid)
            if report['kind']=='model_labels':self.assertEqual(p.chunks(new),p.chunks(old))


if __name__=='__main__':unittest.main()
