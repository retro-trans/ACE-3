"""Check name identity, referenced tables, and preservation of dialogue/portraits."""
import struct
import unittest
from build_speaker_patch import BASE, actor_tables, mappings, plan, replace_table
from build_ui_patch import u32
from dialogue_corpus import archive, parse_table


class SpeakerPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.changes, cls.audit = plan()

    def test_shared_ranges_null_slots_and_unmapped_names_are_preserved(self):
        mapped = mappings()
        shared = [c for c in self.changes if c['report']['kind'] == 'shared_speakers']
        self.assertEqual(len(shared), 8)
        for c in shared:
            old, new = c['before'], c['after']
            size, pointers, count, rows = parse_table(old)
            self.assertEqual(old[:pointers], new[:pointers])
            after = parse_table(new)[3]
            self.assertEqual([(s, t) for s, t, _, _ in rows], [(s, t) for s, t, _, _ in after])
            for slot in range(count):
                self.assertEqual(u32(old, pointers + slot * 4) == 0, u32(new, pointers + slot * 4) == 0)
            for before, result in zip(rows, after):
                cid = before[1]
                self.assertEqual(result[3], mapped[cid]['target'].encode('cp932') if cid in mapped else before[3])

    def test_scene_references_resolve_and_dialogue_portraits_remain_intact(self):
        mapped = mappings()
        by_resource = {}
        for c in self.changes:
            if c['report']['kind'] != 'shared_speakers':
                by_resource.setdefault(c['report']['resource_id'], []).append(c)
        checked, relocated = 0, 0
        with BASE.open('rb') as f:
            fi, entries = archive(f)
            for _, size, offset, rid in entries:
                if rid not in by_resource:
                    continue
                origin = fi['offset'] + offset
                f.seek(origin)
                before = f.read(size)
                after = bytearray(before)
                for c in by_resource[rid]:
                    if c['report']['kind'] == 'archive_resource_size':
                        after.extend(bytes(c['report']['new_size'] - size))
                for c in by_resource[rid]:
                    if c['report']['kind'] == 'archive_resource_size':
                        continue
                    at = c['offset'] - origin
                    self.assertEqual(after[at:at + len(c['before'])], c['before'])
                    after[at:at + len(c['after'])] = c['after']
                original_actors, result_actors = actor_tables(before), actor_tables(after)
                self.assertEqual(len(original_actors), len(result_actors))
                for a, b in zip(original_actors, result_actors):
                    self.assertEqual(a[0], b[0])
                    self.assertEqual(b[3], mapped[a[0]]['target'] if a[0] in mapped else a[3])
                    # Actor ID, portrait pointer, and reserved field are untouched.
                    record = a[4] - 4
                    self.assertEqual(before[record:record + 4], after[record:record + 4])
                    self.assertEqual(before[record + 8:record + 16], after[record + 8:record + 16])
                    if a[1] != b[1]:
                        relocated += 1
                        self.assertEqual(before[a[1]:a[1] + a[2]], after[a[1]:a[1] + a[2]])
                # Active dialogue table and its commands remain byte-identical.
                at = u32(before, 20)
                self.assertEqual(at, u32(after, 20))
                table_size = parse_table(before, at)[0]
                self.assertEqual(before[at:at + table_size], after[at:at + table_size])
                checked += 1
        self.assertGreater(checked, 100)
        self.assertEqual(relocated, 10)

    def test_reported_tutorial_names_and_glossary_spelling(self):
        rows = [c['report'] for c in self.changes if c['report']['kind'] == 'scene_speaker']
        tutorial = {r['character_id']: r['target'] for r in rows if r['resource_id'] == 2002010}
        self.assertEqual(tutorial, {1041: 'Barrel', 1060: 'Faye', 5010: 'Amuro', 10010: 'Kaine', 10030: 'Light'})
        self.assertEqual(self.audit['translated_label_instances'], 1127)
        self.assertEqual(self.audit['scanned_archive_resources'], 10344)
        self.assertEqual(self.audit['character_count'], 26)

    def test_never_truncates_or_silently_replaces_wrong_source(self):
        c = next(c for c in self.changes if c['report'].get('target') == 'Barrel')
        with self.assertRaisesRegex(ValueError, 'never truncate'):
            replace_table(c['before'], {0: ('バレル', 'X' * 100)})
        with self.assertRaisesRegex(ValueError, 'preimage'):
            replace_table(c['before'], {0: ('フェイ', 'Faye')})


if __name__ == '__main__':
    unittest.main()
