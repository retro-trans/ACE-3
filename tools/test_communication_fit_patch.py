"""0.1.39: detect hidden communication lines and preserve links and scene scripts."""
import json
import unittest
import build_communication_fit_patch as p


class ReflowContract(unittest.TestCase):
    def test_screenshot_ruri_line_retains_full_link_and_all_words(self):
        with p.BASE.open('rb') as f:
            fi,es=p.archive(f)
            def get(rid):
                e=next(e for e in es if e[3]==rid);f.seek(fi['offset']+e[2]);return f.read(e[1])
            font=p.parts(get(1200000))[2500];d=get(2002020)
            old=next(raw.decode('cp932') for _,i,_,raw in p.parse_table(d,p.u32(d,20))[3] if i==521)
        self.assertEqual(len(old.split('\n')),4)
        new=p.reflow(old,font)
        self.assertEqual(old.split(),new.split())
        self.assertEqual(len(new.split('\n')),3)
        self.assertIn('<book(10)>Londo Bell<endbook()>',new.split('\n')[2])
        self.assertEqual(p.links(new),p.links(old))


@unittest.skipUnless(p.OUTPUT.with_suffix('.json').exists(),'Build 0.1.39 first')
class BuiltDisc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads(p.OUTPUT.with_suffix('.json').read_text(encoding='utf-8'))
        cls.rows=json.loads((p.ROOT/'work/translation/en/communication_reflow_039.json').read_text(encoding='utf-8'))['rows']
        cls.old={};cls.new={}
        wanted={r['resource_id'] for r in cls.report['changes']}|set(range(1200000,1200008))
        for path,dest in ((p.BASE,cls.old),(p.OUTPUT,cls.new)):
            with path.open('rb') as f:
                fi,es=p.archive(f)
                for _,size,off,rid in es:
                    if rid in wanted or 2002000<=rid<2003000:
                        f.seek(fi['offset']+off);dest[rid]=f.read(size)

    def test_all_communication_lines_visible_and_highlighted_terms_preserved(self):
        n=0
        for rid,d in self.new.items():
            if not 2002000<=rid<2003000:continue
            try:rows=p.parse_table(d,p.u32(d,20))[3]
            except ValueError:continue
            for _,i,_,raw in rows:
                text=raw.decode('cp932')
                if p.communication(text):self.assertLessEqual(len(text.split('\n')),3,(rid,i));n+=1
        self.assertEqual(n,3411)
        fonts=[p.parts(self.new[rid])[2500] for rid in range(1200000,1200008)]
        for r in self.rows:
            self.assertEqual(p.links(r['before']),p.links(r['target']))
            color=lambda s:p.builder.re.findall(r'<color\((\d+)\)>(.*?)<ce\(\)>',s,flags=p.builder.re.S)
            self.assertEqual(color(r['before']),color(r['target']))
            self.assertEqual(p.builder.TOKEN.findall(r['before']),p.builder.TOKEN.findall(r['target']))
            for font in fonts:self.assertLessEqual(max(p.measure_text(font,p.builder.TOKEN.sub('',r['target']))),460)
            if r['kind']=='line_breaks_only':self.assertEqual(r['before'].split(),r['target'].split())
            if r['id'] in ('dialogue_00823','dialogue_00833'):
                self.assertIn('Londo Bell',r['target']);self.assertLessEqual(len(r['target'].split('\n')),3)

    def test_scene_scripts_and_unselected_rows_unchanged_in_every_copy(self):
        checked=0
        for report in self.report['changes']:
            if report['kind']!='communication_fit':continue
            rid=report['resource_id'];old=self.old[rid];new=self.new[rid]
            self.assertEqual(old[:20],new[:20]);self.assertEqual(old[24:],new[24:len(old)])
            before={i:(s,r) for s,i,_,r in p.parse_table(old,p.u32(old,20))[3]}
            after={i:(s,r) for s,i,_,r in p.parse_table(new,p.u32(new,20))[3]}
            self.assertEqual(before.keys(),after.keys())
            for i,(s,r) in before.items():
                self.assertEqual(s,after[i][0])
                if i not in report['text_ids']:self.assertEqual(r,after[i][1])
                else:
                    a=r.decode('cp932');b=after[i][1].decode('cp932')
                    self.assertEqual(p.links(a),p.links(b));self.assertLessEqual(len(b.split('\n')),3);checked+=1
        self.assertEqual(checked,456)

    def test_purchasable_template_and_other_menu_resources(self):
        checked=0
        for report in self.report['changes']:
            if report['kind']!='purchasable_notice':continue
            rid=report['resource_id'];old=p.parts(self.old[rid]);new=p.parts(self.new[rid])
            for key in old:
                if key!=3069:self.assertEqual(old[key],new[key])
            before={i:r for _,i,_,r in p.parse_table(old[3069])[3]}
            after={i:r for _,i,_,r in p.parse_table(new[3069])[3]}
            self.assertEqual(before.keys(),after.keys())
            for i,raw in before.items():self.assertEqual(after[i],b'Purchasable: %s' if raw==b'Can add: %s' else raw)
            checked+=1
        self.assertEqual(checked,3)


if __name__=='__main__':unittest.main()
