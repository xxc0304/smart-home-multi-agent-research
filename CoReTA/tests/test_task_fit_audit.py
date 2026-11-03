import unittest
import tempfile
from pathlib import Path
import audit_existing_task_fit_20261025 as audit
import local_judgment_frontend as io

class TaskFitAuditTests(unittest.TestCase):
    def test_native_facts_options_and_privacy_survive_without_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'audit';p=Path(tmp)/'pack';r=audit.build(a,p)
            self.assertEqual(r['selected'],4);self.assertEqual(r['distributed_packets'],16)
            source={x['id']:x for x in io.read(audit.SOURCE)}
            for n in audit.SELECTION:
                tid=f'hb-local-dev-{n:03d}';entry=source[n]
                for i,original in enumerate(entry['hidden_information'],1):
                    packet=io.read(p/tid/'packets/distributed'/f'A{i}.json')
                    self.assertEqual(set(packet),{'task','member','public_sources','own_sources'})
                    self.assertEqual(packet['own_sources'],[dict(ref=f'A{i}.S1',content=original)])
                    self.assertEqual(packet['task']['scenario'],entry['description'])
                    self.assertEqual([x['text'] for x in packet['task']['choices']],entry['possible_answers'])
                    self.assertNotIn('correct_answer',packet);self.assertNotIn('evaluation',packet)
                    self.assertEqual(len(packet['public_sources']),1+len(entry['shared_information']))
                full=io.read(p/tid/'packets/all_information/A1.json')
                self.assertEqual([s['content'] for s in full['own_sources']],entry['hidden_information'])
                gold=io.read(p/tid/'offline/evaluation.json')
                self.assertEqual(gold['reference_name'],entry['correct_answer'])
            manifest=io.read(p/'dataset_manifest.json')
            for name,sha in manifest['files'].items():self.assertEqual(io.digest(p/name),sha)
            self.assertFalse(manifest['heldout']);self.assertFalse(manifest['source_text_rewritten'])

    def test_no_discarded_rows_or_silent_split_relabel(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'audit';p=Path(tmp)/'pack';audit.build(a,p)
            inventory=io.read(a/'INVENTORY.json');self.assertEqual(len(inventory['rows']),24)
            self.assertEqual(len(inventory['not_included_ids']),41)
            self.assertEqual({r['source_id'] for r in inventory['rows'] if r['status']=='selected'},set(audit.SELECTION))
            self.assertEqual(next(r for r in inventory['rows'] if r['source_id']==9)['original_planning_split'],'evaluation_candidate')
            with self.assertRaises(ValueError):audit.build(a,p)

if __name__=='__main__':unittest.main()
