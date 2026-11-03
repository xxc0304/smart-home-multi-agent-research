import copy
import json
import tempfile
import unittest
from pathlib import Path
from jsonschema import Draft202012Validator
from coreta.aligned_review import ReviewAdapter,align_packet,dynamic_schema,REVIEW_INSTRUCTIONS
ROOT=Path(__file__).resolve().parents[1]
SCHEMA=ROOT/'design/convergence/aligned_review.schema.json'
class AlignedChecks(unittest.TestCase):
    def example(self,name='same_object'):return json.loads((ROOT/f'design/convergence/example_{name}.json').read_text(encoding='utf-8'))
    def adapter(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        return ReviewAdapter(tmp.name,SCHEMA,token_counter=lambda s:1)
    def run_example(self,x):
        a=self.adapter();r=a.request(x['input_packet'])
        return a.consume(r['request_id'],json.dumps(x['model_output_example']),x['input_packet']['candidate_identity'])
    def test_three_paths_unchanged(self):
        for name,status in [('same_object','addressed'),('replacement','addressed'),('rebuttal','dismissed')]:
            self.assertEqual(self.run_example(self.example(name))['issues']['I1']['status'],status)
    def test_old_candidate_refuted_means_old_observation_supported(self):
        x=self.example('replacement');r=x['model_output_example']['issue_reviews']['I1']
        r['original_case_reviews'][0]['original_assessment']='refuted'
        out=self.run_example(x);self.assertEqual(out['issues']['I1']['status'],'open')
        self.assertTrue(any('unchanged' in e for e in out['issues']['I1']['errors']))
    def test_equation_prose_nonzero_and_decimals_rejected_for_exact(self):
        for text in ['1-1=0','nonzero','not an integer','0.0','4 (nonzero)']:
            x=self.example();x['model_output_example']['issue_reviews']['I1']['current_checks'][0]['observed_value']=text
            out=self.run_example(x);self.assertEqual(out['issues']['I1']['status'],'open')
    def test_qualitative_checks_use_model_judged(self):
        x=self.example();c=x['model_output_example']['issue_reviews']['I1']['current_checks'][0]
        c.update(comparison_kind='model_judged',quantity='integrality',expected_value='non-integer',observed_value='non-integer')
        self.assertEqual(self.run_example(x)['issues']['I1']['status'],'addressed')
    def test_unreduced_fraction_still_not_mechanical_match(self):
        x=self.example();c=x['model_output_example']['issue_reviews']['I1']['current_checks'][0];c['expected_value']='2/4';c['observed_value']='2/4'
        self.assertEqual(self.run_example(x)['issues']['I1']['status'],'open')
    def test_no_original_case_allows_relevant_narrow_source(self):
        x=self.example();issue=x['input_packet']['issues']['I1'];issue['required_case_handles']=[];issue['historical_cases']={};issue['required_task_refs']=['T1']
        x['input_packet']['task']['sources']['T2']='F(1)=0'
        r=x['model_output_example']['issue_reviews']['I1'];r['original_case_reviews']=[];r['current_checks'][0]['task_refs']=['T2']
        out=self.run_example(x);self.assertEqual(out['issues']['I1']['status'],'addressed')
        self.assertEqual(out['issues']['I1']['task_coverage_mode'],'reviewer_selected');self.assertFalse(out['issues']['I1']['task_exhaustiveness_proven'])
    def test_original_affected_constraints_not_waived(self):
        x=self.example();x['input_packet']['issues']['I1']['required_task_refs']=['T1']
        x['input_packet']['task']['sources']['T2']='different supplied source';x['model_output_example']['issue_reviews']['I1']['current_checks'][0]['task_refs']=['T2']
        self.assertEqual(self.run_example(x)['issues']['I1']['status'],'open')
    def test_current_conflict_not_relabelled_as_old_rejection(self):
        x=self.example();x['model_output_example']['issue_reviews']['I1']['current_checks'][0]['outcome']='counterexample'
        self.assertEqual(self.run_example(x)['issues']['I1']['status'],'open')
    def test_original_scalar_recheck_also_has_scalar_schema(self):
        x=self.example();x['model_output_example']['issue_reviews']['I1']['original_case_reviews'][0]['observed_value']='1-2=-1'
        self.assertEqual(self.run_example(x)['issues']['I1']['status'],'open')
    def test_real_output_kept_and_rejected_not_repaired_automatically(self):
        folder=ROOT/'runs/minimal-review-component-20261020/live'
        raw=json.loads((folder/'responses.jsonl').read_text(encoding='utf-8').splitlines()[-1])['raw'];before=str(raw)
        packet=json.loads((ROOT/'runs/minimal-real-packet-20261020/packet.json').read_text(encoding='utf-8'))
        a=self.adapter();r=a.request(packet);out=a.consume(r['request_id'],raw,packet['candidate_identity'])
        self.assertEqual(raw,before);self.assertFalse(out['all_issues_resolved'])
        self.assertTrue(all(x['status']=='open' for x in out['issues'].values()))
    def test_rebuttal_can_challenge_premise_while_observation_confirmed(self):
        x=self.example('rebuttal');case=x['input_packet']['issues']['I1']['historical_cases']['H1']
        case['old_observed_value']='0';case['expected_value']='1'
        row=x['model_output_example']['issue_reviews']['I1']
        row['original_case_reviews'][0]['original_assessment']='supported'
        row['reason']='Original value0 is confirmed, but objection demanded1 contrary to public T1 demanding F(1)=0; current check satisfies T1.'
        self.assertEqual(self.run_example(x)['issues']['I1']['status'],'dismissed')

    def test_no_new_output_fields(self):
        old=json.loads((ROOT/'design/convergence/minimal_review.schema.json').read_text(encoding='utf-8'));new=json.loads(SCHEMA.read_text(encoding='utf-8'))
        self.assertEqual(old['$defs']['review']['properties'].keys(),new['$defs']['review']['properties'].keys())
        self.assertEqual(old['$defs']['check']['properties'].keys(),new['$defs']['check']['properties'].keys())
        for phrase in ['OBSERVATION','canonical','CURRENT','model_judged']:self.assertIn(phrase,REVIEW_INSTRUCTIONS)
        packet=align_packet(self.example()['input_packet']);Draft202012Validator.check_schema(dynamic_schema(new,packet))
if __name__=='__main__':unittest.main()
