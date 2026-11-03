import json
from pathlib import Path
import tempfile
import unittest
import local_judgment_frontend as io
import prepare_local_rule_adoption as probe

class AdoptionPreparationTests(unittest.TestCase):
    def test_all_original_groups_and_exact_shared_evidence_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'p';result=probe.build(out)
            self.assertEqual(result['packets'],24);self.assertEqual(result['contributions'],72)
            plan=io.read(out/'PLAN.json');self.assertEqual(len(plan['schedule']),24)
            for idx in range(0,24,2):
                rows=plan['schedule'][idx:idx+2]
                packets=[io.read(out/r['packet']) for r in rows]
                self.assertEqual(packets[0]['disclosed_evidence'],packets[1]['disclosed_evidence'])
                self.assertEqual(packets[0]['task'],packets[1]['task'])
                self.assertEqual(packets[0]['historical_work'],packets[1]['historical_work'])
                for packet in packets:
                    self.assertEqual(len(packet['contributions']),3)
                    self.assertNotIn('method',packet)
                    self.assertNotIn('expected',packet)
                    self.assertNotIn('offline',packet)
                    self.assertEqual([x['id'] for x in packet['contributions']],['C1','C2','C3'])
            manifest=io.read(out/'manifest.json')
            for name,sha in manifest['files'].items():self.assertEqual(io.digest(out/name),sha)

    def test_choice_faults_remain_visible_without_discarding_reasoning(self):
        packet=dict(task=dict(choices=[dict(id='X'),dict(id='Y')]))
        for choice in ('X','Y',None):
            a=probe.decode(json.dumps(dict(choice=choice,reasoning='A substantive explanation.',used_contributions=['C1'])),packet)
            self.assertEqual(a['choice'],choice);self.assertEqual(a['annotation_issues'],[])
        for choice in ('wrong',[1],True):
            a=probe.decode(json.dumps(dict(choice=choice,reasoning='Keep this explanation.',used_contributions=['C9',None])),packet)
            self.assertEqual(a['reasoning'],'Keep this explanation.')
            self.assertTrue(a['annotation_issues']);self.assertEqual(a['used_contributions'],[])
        for raw in ('{','{}','{"reasoning":null}','{"reasoning":""}','{"reasoning":"a","reasoning":"b"}'):
            with self.assertRaises(ValueError):probe.decode(raw,packet)

    def test_real_complete_final_contributions_replay_with_explicit_field_adaptation(self):
        rows=io.read(probe.HISTORY/'review.json')['rows'];seen=0
        packet=dict(task=dict(choices=[dict(id='placeholder')]))
        for row in rows:
            if row['stage']!='second':continue
            raw=io.read(probe.HISTORY/f"{row['slot']:02d}.raw.txt")
            # Old responses do not contain a final team choice. Do not fabricate one.
            value=dict(choice=None,reasoning=raw['conclusion'],used_contributions=[])
            decoded=probe.decode(json.dumps(value),packet)
            self.assertEqual(decoded['reasoning'],raw['conclusion'])
            self.assertEqual(decoded['choice'],None)
            seen+=1
        self.assertEqual(seen,72)

if __name__=='__main__':unittest.main()
