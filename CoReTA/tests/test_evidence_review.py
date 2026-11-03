import copy
import json
import tempfile
import unittest
from pathlib import Path
from coreta.evidence_review import ReviewAdapter,REVIEW_INSTRUCTIONS
from coreta.schemas import ProtocolError
ROOT=Path(__file__).resolve().parents[1]
SCHEMA=ROOT/'design/convergence/evidence_review.schema.json'
class EvidenceReviewChecks(unittest.TestCase):
    def example(self,name='same_object'):
        x=json.loads((ROOT/f'design/convergence/example_{name}.json').read_text(encoding='utf-8'))
        for r in x['model_output_example']['issue_reviews'].values():
            r.pop('resolution');r.pop('dependency')
        return x
    def adapter(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        return ReviewAdapter(tmp.name,SCHEMA,token_counter=lambda s:1)
    def run_example(self,x):
        a=self.adapter();r=a.request(x['input_packet'])
        return a.consume(r['request_id'],json.dumps(x['model_output_example']),x['input_packet']['candidate_identity'])
    def test_three_paths_use_input_proposal(self):
        for name,status in [('same_object','addressed'),('replacement','addressed'),('rebuttal','dismissed')]:
            x=self.example(name);self.assertEqual(self.run_example(x)['issues']['I1']['status'],status)
    def test_removed_fields_no_longer_accepted_or_requested(self):
        x=self.example();x['model_output_example']['issue_reviews']['I1']['dependency']='removed'
        self.assertEqual(self.run_example(x)['issues']['I1']['status'],'open')
        schema=json.loads(SCHEMA.read_text());self.assertNotIn('dependency',schema['$defs']['review']['properties']);self.assertNotIn('resolution',schema['$defs']['review']['properties'])
    def test_current_false_match_exact_mismatch_blocks(self):
        x=self.example();x['model_output_example']['issue_reviews']['I1']['current_checks'][0]['observed_value']='1'
        self.assertEqual(self.run_example(x)['issues']['I1']['status'],'open')
    def test_missing_and_uncertain_fresh_case_blocks(self):
        for missing in [True,False]:
            x=self.example();r=x['model_output_example']['issue_reviews']['I1']
            if missing:r['original_case_reviews']=[]
            else:r['original_case_reviews'][0]['original_assessment']='uncertain'
            self.assertEqual(self.run_example(x)['issues']['I1']['status'],'open')
    def test_truthfully_reported_old_dependency_retained_stays_unresolved(self):
        x=self.example('replacement');r=x['model_output_example']['issue_reviews']['I1'];r['verdict']='unresolved';r['reason']='Current proof still relies on old false G; bridge not repaired.'
        self.assertEqual(self.run_example(x)['issues']['I1']['status'],'open')
    def test_role_and_stale_response_still_blocked(self):
        x=self.example();x['input_packet']['roles']['checker']='A1'
        with self.assertRaises(ProtocolError):self.adapter().request(x['input_packet'])
        x=self.example();a=self.adapter();request=a.request(x['input_packet'])
        out=a.consume(request['request_id'],json.dumps(x['model_output_example']),{'version':999,'hash':'stale'})
        self.assertTrue(out['global_errors'])
    def test_unknown_handle_and_required_constraint_blocks(self):
        for typ in ['handle','constraint']:
            x=self.example();r=x['model_output_example']['issue_reviews']['I1']
            if typ=='handle':r['current_checks'][0]['target_handle']='bad'
            else:
                x['input_packet']['task']['sources']['T2']='extra';x['input_packet']['issues']['I1']['required_task_refs']=['T2']
            self.assertEqual(self.run_example(x)['issues']['I1']['status'],'open')
    def test_new_counterexample_prevents_closure(self):
        x=self.example();c=copy.deepcopy(x['model_output_example']['issue_reviews']['I1']['current_checks'][0]);c['observed_value']='1'
        x['model_output_example']['new_findings']=[{'related_issue_handle':'I1','check':c}]
        self.assertEqual(self.run_example(x)['issues']['I1']['status'],'open')
    def test_candidate_identity_and_history_not_overwritten(self):
        x=self.example('rebuttal');original=copy.deepcopy(x)
        out=self.run_example(x);self.assertEqual(x,original)
        self.assertEqual(out['issues']['I1']['historical_observations'][0]['old_observed_value'],'-1')
        self.assertEqual(out['issues']['I1']['historical_observations'][0]['fresh_observed_value'],'0')
    def test_raw_real_output_is_not_automatically_migrated(self):
        raw=json.loads((ROOT/'runs/aligned-review-component-20261020/live/responses.jsonl').read_text(encoding='utf-8').splitlines()[-1])['raw']
        packet=json.loads((ROOT/'runs/minimal-real-packet-20261020/packet.json').read_text(encoding='utf-8'))
        a=self.adapter();request=a.request(packet);out=a.consume(request['request_id'],raw,packet['candidate_identity'])
        self.assertTrue(all(x['status']=='open' for x in out['issues'].values()))
    def test_known_semantic_blindspot_not_disguised_as_correctness(self):
        # Explicit human counterfactual only: removing labels cannot fix bad qualitative reasoning.
        raw=json.loads((ROOT/'runs/aligned-review-component-20261020/live/responses.jsonl').read_text(encoding='utf-8').splitlines()[-1])['raw'];value=json.loads(raw)
        for r in value['issue_reviews'].values():r.pop('resolution');r.pop('dependency')
        packet=json.loads((ROOT/'runs/minimal-real-packet-20261020/packet.json').read_text(encoding='utf-8'));a=self.adapter();req=a.request(packet)
        out=a.consume(req['request_id'],json.dumps(value),packet['candidate_identity'])
        self.assertEqual(out['issues']['I2']['status'],'addressed')
        self.assertFalse(out['task_correctness_proven'])
        i2=value['issue_reviews']['I2']['current_checks']
        self.assertEqual(i2[1]['observed_value'],'-1/sqrt2')  # Known wrong; no automatic arithmetic correction.
    def test_program_keeps_input_path_not_checker_reclassification(self):
        self.assertIn('closure_path',REVIEW_INSTRUCTIONS)
        x=self.example();out=self.run_example(x);self.assertEqual(out['issues']['I1']['status'],'addressed')
if __name__=='__main__':unittest.main()
