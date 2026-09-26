"""Verify whole-category coverage and preservation of briefing map/script commands."""
import json,unittest
from build_briefing_patch import BASE,INPUT,plan,parts,archive,parse_table,controls,visible,wrap,relocate_scene,u32

class BriefingTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.changes,cls.reports=plan();cls.before={}
  with BASE.open('rb') as f:
   fi,es=archive(f)
   for _,n,o,rid in es:
    if rid in cls.changes:f.seek(fi['offset']+o);cls.before[rid]=f.read(n)

 def test_complete_scenes_and_ordered_commands(self):
  for rid,n in [(4003020,25),(4003481,8)]:
   old=parts(self.before[rid]);new=parts(self.changes[rid]);a=parse_table(old[1])[3];b=parse_table(new[1])[3]
   self.assertEqual(len(b),n)
   for x,y in zip(a,b):
    self.assertEqual(x[:2],y[:2]);self.assertEqual(controls(x[3].decode('cp932')),controls(y[3].decode('cp932')))
    self.assertNotRegex(visible(y[3].decode('cp932')),'[\u3040-\u30ff\u4e00-\u9fff]')
   for k in old:
    if k!=1:self.assertEqual(old[k],new[k])

 def test_all_objectives_and_speaker_copies(self):
  expected={r['source']:r['en'] for r in json.loads(INPUT.read_text(encoding='utf-8'))['conditions']}
  for rid in (4002050,4002054,4002057):
   old=parse_table(parts(self.before[rid])[3056])[3];new=parse_table(parts(self.changes[rid])[3056])[3]
   self.assertEqual(len(new),152)
   self.assertEqual([r.decode('cp932') for _,_,_,r in new],[expected[r.decode('cp932')] for _,_,_,r in old])
  for rid in (4002050,4002052,4002053,4002054,4002057):
   names={i:r.decode('cp932') for _,i,_,r in parse_table(parts(self.changes[rid])[3014])[3]}
   self.assertEqual(names[5010],'Amuro Ray');self.assertEqual(names[30050],'Kouichiro Misumaru')

 def test_scene_relocation_preserves_scripts_and_other_dialogue(self):
  count=0
  for report in self.reports:
   if report['kind']!='scene_conditions':continue
   count+=1;old=self.before[report['resource_id']];new=self.changes[report['resource_id']]
   self.assertEqual(old[:20],new[:20]);self.assertEqual(old[24:],new[24:len(old)])
   a=parse_table(old,u32(old,20))[3];b=parse_table(new,u32(new,20))[3]
   self.assertEqual([r[:2] for r in a],[r[:2] for r in b])
   for x,y in zip(a,b):
    if x[1] not in (1,2):self.assertEqual(x[3],y[3])
  self.assertEqual(count,264)

 def test_oversized_body_rejected(self):
  font=parts(self.before[4002050])[2500]
  with self.assertRaisesRegex(ValueError,'three body lines|allocation'):wrap('Too much text. '*50,font)
  with self.assertRaisesRegex(ValueError,'Single word'):wrap('W'*100,font)

if __name__=='__main__':unittest.main()
