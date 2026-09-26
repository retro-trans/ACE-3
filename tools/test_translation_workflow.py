"""Public workflow checks on small synthetic discs, never on a user's game save."""
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from translation_tables import export_document, json_text, plan_edits, read_table, rebuild_table, scan_iso, sha, write_copy
from build_translation_pairs import pair
from compare_translation import comparison_rows, render


def directory_record(name, lba, size, directory=True):
    result = bytearray(33+len(name)+(len(name) % 2 == 0))
    result[0] = len(result)
    struct.pack_into('<I', result, 2, lba); struct.pack_into('>I', result, 6, lba)
    struct.pack_into('<I', result, 10, size); struct.pack_into('>I', result, 14, size)
    result[25] = 2 if directory else 0; result[28:32] = b'\x01\0\0\x01'
    result[32] = len(name); result[33:33+len(name)] = name
    return bytes(result)


def table(texts, capacity=256):
    out = bytearray(capacity); n = len(texts)
    struct.pack_into('<7I', out, 0, 65536, capacity, 0, 1, n, 40, 0)
    struct.pack_into('<3I', out, 28, 0, 1, n); at = 40+4*n
    for i, text in enumerate(texts):
        if text is None: continue
        raw = text.encode('cp932')+b'\0'; struct.pack_into('<I', out, 40+i*4, at)
        out[at:at+len(raw)] = raw; at += len(raw)
    return bytes(out)


def disc(path, texts=('<op()>Start', None, 'Exit'), table_id=3010):
    payload = table(texts); bnd = bytearray(32)+payload
    bnd[:4] = b'BND\0'; struct.pack_into('<II', bnd, 4, len(bnd), 1)
    struct.pack_into('<II', bnd, 16, table_id, 32)
    archive = bytearray(48)+bnd; archive[:4] = b'BND3'; struct.pack_into('<I', archive, 16, 1)
    struct.pack_into('<4I', archive, 32, 0, len(bnd), 48, 4002050)
    image = bytearray(24*2048); image[16*2048:16*2048+7] = b'\x01CD001\x01'
    image[16*2048+156:16*2048+190] = directory_record(b'\0', 20, 2048)
    root = directory_record(b'\0', 20, 2048)+directory_record(b'\1', 20, 2048)
    root += directory_record(b'SLPS_257.84;1', 21, 4, False)+directory_record(b'DATA.BIN;1', 22, len(archive), False)
    image[20*2048:20*2048+len(root)] = root; image[21*2048:21*2048+4] = b'ELF!'
    image[22*2048:22*2048+len(archive)] = archive; path.write_bytes(image)


class Workflow(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.iso = self.root/'source.iso'; disc(self.iso)

    def test_rebuild_preserves_ids_nulls_and_sibling_text(self):
        before = table(('Start', None, 'Exit'))
        after = rebuild_table(before, {1: 'Begin'})
        self.assertEqual(len(after), len(before))
        self.assertEqual([(tid, raw) for _, tid, _, raw in read_table(after)['rows']], [(1,b'Begin'),(2,None),(3,b'Exit')])

    def test_reject_invalid_pointer_overflow_nul_and_control_changes(self):
        original = table(('<book(10)>Londo Bell<endbook()>', 'Exit'))
        for value in ('Londo Bell', '<book(11)>Londo Bell<endbook()>', 'A\0B', '<book(10)>'+'x'*400+'<endbook()>'):
            with self.assertRaises(ValueError): rebuild_table(original, {1:value})
        bad = bytearray(original); struct.pack_into('<I',bad,40,9999)
        with self.assertRaises(ValueError): read_table(bad)

    def test_compact_singleton_is_supported(self):
        data = bytearray(48); struct.pack_into('<7I',data,0,65536,48,0,1,1,24,40)
        struct.pack_into('<3I',data,28,0,1,1); data[40:47]=b'Hikaru\0'
        self.assertEqual(read_table(data)['rows'][0][3], b'Hikaru')
        self.assertEqual(read_table(rebuild_table(data,{1:'Hikaru'}))['rows'][0][3],b'Hikaru')

    def test_shared_pointers_can_split_without_changing_the_other_row(self):
        data = bytearray(table(('Shared','Unused')))
        struct.pack_into('<I',data,44,struct.unpack_from('<I',data,40)[0])
        rows = read_table(rebuild_table(data,{1:'Changed'}))['rows']
        self.assertEqual([r[3] for r in rows],[b'Changed',b'Shared'])

    def test_direction_icons_and_hash_commands_cannot_be_removed(self):
        data = table(('#iSelect:㊤㊦ %s',))
        for text in ('Select:㊤㊦ %s','#iSelect:㊤ %s','#iSelect:㊤㊦','\x01#iSelect:㊤㊦ %s'):
            with self.assertRaises(ValueError): rebuild_table(data,{1:text})

    def test_runtime_save_slot_stays_at_its_byte_position(self):
        data = table(('Ｎｏ．00 Save',))
        for text in ('No.00 Save','Save Ｎｏ．00','Ｎｏ．01 Save'):
            with self.assertRaises(ValueError): rebuild_table(data,{1:text})
        self.assertEqual(read_table(rebuild_table(data,{1:'Ｎｏ．00 File'}))['rows'][0][3].decode('cp932'),'Ｎｏ．00 File')

    def test_export_noop_and_stale_or_forged_rows_rejected(self):
        doc, counts = export_document(self.iso)
        self.assertEqual(counts['rows'], 2); self.assertEqual(plan_edits(self.iso,doc),[])
        doc['rows'][0]['before_sha256']='bad'
        with self.assertRaises(ValueError): plan_edits(self.iso,doc)
        doc,_=export_document(self.iso); doc['rows'].append(dict(doc['rows'][0]))
        with self.assertRaises(ValueError): plan_edits(self.iso,doc)

    def test_japanese_is_not_exported_and_null_preserves_it(self):
        disc(self.iso, ('開始', 'Exit'))
        doc,_=export_document(self.iso); self.assertNotIn('開始',json_text(doc))
        self.assertIsNone(doc['rows'][0]['text']); self.assertEqual(plan_edits(self.iso,doc),[])

    def test_changed_copy_only_differs_in_planned_table_and_refuses_overwrite(self):
        doc,_=export_document(self.iso); doc['rows'][0]['text']='<op()>Begin'
        patches=plan_edits(self.iso,doc); source=self.iso.read_bytes(); out=self.root/'edited.iso'
        report=write_copy(self.iso,out,patches); expected=bytearray(source)
        for p in patches: expected[p['offset']:p['offset']+len(p['after'])]=p['after']
        self.assertEqual(out.read_bytes(),bytes(expected)); self.assertEqual(self.iso.read_bytes(),source)
        self.assertEqual(report['sha256'],sha(bytes(expected)))
        with self.assertRaises(ValueError): write_copy(self.iso,self.iso,patches)
        with self.assertRaises(ValueError): write_copy(self.iso,out,patches)

    def test_pairing_never_guesses_when_table_id_changes(self):
        disc(self.iso, ('開始','Exit'))
        target=self.root/'target.iso'; disc(target,('Start','Exit'))
        catalog=pair(self.iso,target,'test'); self.assertEqual([r['status'] for r in catalog['rows']],['translated','unchanged'])
        self.assertNotIn('開始',json.dumps(catalog,ensure_ascii=False))
        rows=comparison_rows(self.iso,catalog); self.assertEqual(rows[0]['source'],'開始')
        self.assertEqual(len(comparison_rows(self.iso,catalog,only='translated')),1)
        disc(target,('Start','Exit'),table_id=3011)
        self.assertTrue(all(r['status']=='no_match' for r in pair(self.iso,target,'test')['rows']))

    def test_bad_comparison_source_is_rejected(self):
        catalog=pair(self.iso,self.iso,'test'); disc(self.iso,('Other','Exit'))
        with self.assertRaises(ValueError): comparison_rows(self.iso,catalog)

    def test_html_never_executes_game_text(self):
        attack='</script><img src=x onerror=alert(1)>'
        page=render([{'id':'x','resource':1,'status':'translated','source':attack,'target':attack}],'test')
        self.assertNotIn(attack,page); self.assertIn('\\u003c/script\\u003e',page)
        self.assertIn('td.textContent=text',page)

    def test_command_line_dry_run_write_and_verification(self):
        tools=Path(__file__).resolve().parent; export=self.root/'edit.json'; out=self.root/'local.iso'
        def run(tool,*args):
            return subprocess.run([sys.executable,str(tools/tool),*map(str,args)],capture_output=True,text=True)
        r=run('extract_script.py',self.iso,export); self.assertEqual(r.returncode,0,r.stderr); self.assertFalse(export.exists())
        r=run('extract_script.py',self.iso,export,'--write'); self.assertEqual(r.returncode,0,r.stderr)
        doc=json.loads(export.read_text()); doc['rows'][0]['text']='<op()>Begin'; export.write_text(json_text(doc))
        args=(self.iso,export,'--version','0.1.43','--output',out)
        r=run('apply_script.py',*args); self.assertEqual(r.returncode,0,r.stderr); self.assertFalse(out.exists())
        r=run('apply_script.py',*args,'--write'); self.assertEqual(r.returncode,0,r.stderr); self.assertTrue(out.exists())
        r=run('verify_translation.py',out,'--script',export); self.assertEqual(r.returncode,0,r.stderr)
        self.assertTrue(json.loads(out.with_suffix('.json').read_text())['exact_delta_verified'])


if __name__ == '__main__': unittest.main()
