import copy
import json
import tempfile
import unittest
from pathlib import Path
from coreta.review_packet import build_packet
from coreta.minimal_review import ReviewAdapter,RepairBudget,preflight
from coreta.schemas import ProtocolError
from coreta.closure import digest
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'runs/math140-correct-repair-review-v3-20261020/public_component_input.json'
class RealPacketChecks(unittest.TestCase):
    def data(self):return json.loads(SOURCE.read_text(encoding='utf-8'))
    def test_candidate_and_input_preserved(self):
        data=self.data();before=copy.deepcopy(data);packet,mapping=build_packet(data)
        self.assertEqual(data,before)
        self.assertEqual(packet['current_targets']['C1']['definition'],data['MATERIAL']['current']['candidate']['artifact'])
        self.assertEqual(packet['candidate_identity']['hash'],digest(data['MATERIAL']['current']['candidate']))
        self.assertEqual(packet['roles'],{'integrator':'A0','builder':'A1','checker':'A2'})
    def test_four_issues_six_exact_original_cases(self):
        data=self.data();p,m=build_packet(data)
        self.assertEqual(len(p['issues']),4);self.assertEqual(len(m['case_handles']),6)
        for issue in p['issues'].values():
            for handle,case in issue['historical_cases'].items():
                original=m['case_handles'][handle]['original_case']
                self.assertEqual(case['input'],original['input']);self.assertEqual(case['quantity'],original['quantity_key'])
                self.assertEqual(case['expected_value'],original['expected_value']);self.assertEqual(case['old_observed_value'],original['observed_value'])
    def test_historical_definition_deduplicated_and_verified(self):
        p,m=build_packet(self.data());self.assertEqual(len(p['historical_objects']),1)
        old=self.data()['MATERIAL']['before']
        obj=next(iter(p['historical_objects'].values()))
        self.assertEqual(obj['definition'],old['candidate']['artifact'])
        self.assertEqual(obj['candidate_hash'],digest(old['candidate']))
        del p['historical_objects']
        with self.assertRaises(ProtocolError):preflight(p)
    def test_wrong_historical_hash_not_replaced_by_current(self):
        data=self.data();issue=next(x for x in data['MATERIAL']['issues'] if x.get('evidence_records'))
        issue['evidence_records'][0]['candidate_hash']='wrong'
        with self.assertRaises(ProtocolError):build_packet(data)
    def test_unavailable_original_snapshot_blocks(self):
        data=self.data();del data['MATERIAL']['before']['candidate']['artifact']
        with self.assertRaises(ProtocolError):build_packet(data)
    def test_no_observations_generated_by_mapping(self):
        p,m=build_packet(self.data())
        self.assertNotIn('issue_reviews',p);self.assertNotIn('new_findings',p)
        self.assertTrue(all('fresh_observed_value' not in x for i in p['issues'].values() for x in i['historical_cases'].values()))
    def test_shared_budget_not_reset_by_new_adapter(self):
        packet,_=build_packet(self.data());budget=RepairBudget(2,1)
        with tempfile.TemporaryDirectory() as d:
            a=ReviewAdapter(Path(d)/'a',ROOT/'design/convergence/minimal_review.schema.json',token_counter=lambda s:1,shared_budget=budget)
            b=ReviewAdapter(Path(d)/'b',ROOT/'design/convergence/minimal_review.schema.json',token_counter=lambda s:1,shared_budget=budget)
            r=a.request(packet);a.repair(r['request_id'],'{','syntax')
            r=b.request(packet)
            with self.assertRaises(ProtocolError):b.repair(r['request_id'],'{','syntax')
            self.assertEqual(a.repairs,2);self.assertEqual(b.repairs,2)
    def test_required_constraint_handles_have_original_source(self):
        p,m=build_packet(self.data())
        for key,issue in p['issues'].items():
            for case in issue['historical_cases'].values():
                self.assertTrue(set(case['task_refs'])<=set(issue['required_task_refs']))
                source=p['task']['sources'][case['task_refs'][0]]
                self.assertEqual(source['interpretation_status'],'model_asserted')
                self.assertIn(source['quoted_text'],p['task']['text'])

if __name__=='__main__':unittest.main()
