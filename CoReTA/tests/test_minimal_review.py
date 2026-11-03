import copy
import json
import tempfile
import unittest
from pathlib import Path
from jsonschema import Draft202012Validator
from coreta.minimal_review import ReviewAdapter,preflight,dynamic_schema
from coreta.schemas import ProtocolError
ROOT=Path(__file__).resolve().parents[1]
DESIGN=ROOT/'design/convergence'

class MinimalReviewChecks(unittest.TestCase):
    def example(self,name='same_object'):
        return json.loads((DESIGN/f'example_{name}.json').read_text(encoding='utf-8'))
    def adapter(self,**kwargs):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        return ReviewAdapter(tmp.name,DESIGN/'minimal_review.schema.json',token_counter=lambda s:len(s)//4,**kwargs)
    def evaluate(self,example,adapter=None):
        a=adapter or self.adapter();r=a.request(example['input_packet'])
        return a.consume(r['request_id'],json.dumps(example['model_output_example']),example['input_packet']['candidate_identity'])
    def test_three_design_paths(self):
        for name,status in [('same_object','addressed'),('replacement','addressed'),('rebuttal','dismissed')]:
            x=self.example(name);original=copy.deepcopy(x)
            out=self.evaluate(x)
            self.assertEqual(out['issues']['I1']['status'],status);self.assertTrue(out['all_issues_resolved'])
            self.assertEqual(x,original);self.assertFalse(out['task_correctness_proven'])
    def test_fresh_rebuttal_does_not_overwrite_history(self):
        out=self.evaluate(self.example('rebuttal'));row=out['issues']['I1']['historical_observations'][0]
        self.assertEqual(row['old_observed_value'],'-1');self.assertEqual(row['fresh_observed_value'],'0')
    def test_no_new_observation_from_loading_history(self):
        x=self.example();x['model_output_example']['issue_reviews']['I1']['original_case_reviews']=[]
        self.assertEqual(self.evaluate(x)['issues']['I1']['status'],'open')
    def test_still_used_unknown_and_failed_replacement(self):
        for dep in ['still_used','unknown']:
            x=self.example('replacement');x['model_output_example']['issue_reviews']['I1']['dependency']=dep
            self.assertEqual(self.evaluate(x)['issues']['I1']['status'],'open')
        x=self.example('replacement');x['model_output_example']['issue_reviews']['I1']['current_checks'][0]['observed_value']='1'
        self.assertEqual(self.evaluate(x)['issues']['I1']['status'],'open')
    def test_inconsistent_historical_assessment(self):
        x=self.example();x['model_output_example']['issue_reviews']['I1']['original_case_reviews'][0]['observed_value']='0'
        self.assertEqual(self.evaluate(x)['issues']['I1']['status'],'open')
    def test_unknown_target_case_and_duplicate_cases(self):
        for field in ['target','case','duplicate']:
            x=self.example();r=x['model_output_example']['issue_reviews']['I1']
            if field=='target':r['current_checks'][0]['target_handle']='invisible'
            elif field=='case':r['original_case_reviews'][0]['case_handle']='invisible'
            else:r['original_case_reviews']*=2
            self.assertEqual(self.evaluate(x)['issues']['I1']['status'],'open')
    def test_packet_preflight_blocks_role_and_missing_content(self):
        for kind in ['role','content','stale_target']:
            x=self.example()['input_packet']
            if kind=='role':x['roles']['checker']='A1'
            elif kind=='content':del x['issues']['I1']['historical_cases']['H1']['definition']
            else:x['current_targets']['C1']['candidate_version']=0
            with self.assertRaises(ProtocolError):self.adapter().request(x)
    def test_stale_candidate_and_duplicate_response_block(self):
        x=self.example();a=self.adapter();request=a.request(x['input_packet']);raw=json.dumps(x['model_output_example'])
        wrong=copy.deepcopy(x['input_packet']['candidate_identity']);wrong['version']=999
        self.assertTrue(a.consume(request['request_id'],raw,wrong)['global_errors'])
        self.assertTrue(a.consume(request['request_id'],raw,x['input_packet']['candidate_identity'])['global_errors'])
    def test_invalid_json_and_partial_never_accepted(self):
        x=self.example();a=self.adapter();r=a.request(x['input_packet'])
        self.assertTrue(a.consume(r['request_id'],'{',x['input_packet']['candidate_identity'])['global_errors'])
        r=a.request(x['input_packet'])
        self.assertTrue(a.consume(r['request_id'],json.dumps(x['model_output_example']),x['input_packet']['candidate_identity'],'incomplete')['global_errors'])
    def test_issue_local_failure_does_not_poison_other_issue(self):
        x=self.example();x['input_packet']['issues']['I2']=copy.deepcopy(x['input_packet']['issues']['I1'])
        x['model_output_example']['issue_reviews']['I2']=copy.deepcopy(x['model_output_example']['issue_reviews']['I1'])
        x['model_output_example']['issue_reviews']['I1']['unallowed']='extra'
        out=self.evaluate(x);self.assertEqual(out['issues']['I1']['status'],'open');self.assertEqual(out['issues']['I2']['status'],'addressed')
    def test_new_contradiction_precedes_closure(self):
        for related in ['I1',None]:
            x=self.example();check=copy.deepcopy(x['model_output_example']['issue_reviews']['I1']['current_checks'][0]);check['observed_value']='1'
            x['model_output_example']['new_findings']=[{'related_issue_handle':related,'check':check}]
            out=self.evaluate(x);self.assertFalse(out['all_issues_resolved'])
            if related:self.assertEqual(out['issues']['I1']['status'],'open')
    def test_unparsable_exact_equality_not_treated_as_success(self):
        x=self.example();x['model_output_example']['issue_reviews']['I1']['current_checks'][0]['observed_value']='0.0'
        self.assertEqual(self.evaluate(x)['issues']['I1']['status'],'open')
    def test_budget_and_global_repair_cap(self):
        x=self.example();a=self.adapter(max_input_tokens=1)
        with self.assertRaises(ProtocolError):a.request(x['input_packet'])
        a=self.adapter();r=a.request(x['input_packet'])
        a.repair(r['request_id'],'{','Invalid JSON');a.repair(r['request_id'],'{','Invalid JSON')
        with self.assertRaises(ProtocolError):a.repair(r['request_id'],'{','Invalid JSON')
    def test_dynamic_schema_enum_and_no_manual_generated_ids(self):
        x=self.example();a=self.adapter();r=a.request(x['input_packet']);Draft202012Validator.check_schema(r['schema'])
        Draft202012Validator(r['schema']).validate(x['model_output_example'])
        output=json.dumps(x['model_output_example'])
        for forbidden in ['record_id','current_record_indexes','candidate_hash']:self.assertNotIn(forbidden,output)
    def test_old_actual_mixed_output_is_not_migrated(self):
        raw=(ROOT/'runs/math140-correct-repair-review-v3-20261020/inspection.json').read_text(encoding='utf-8')
        x=self.example();a=self.adapter();r=a.request(x['input_packet'])
        self.assertTrue(a.consume(r['request_id'],raw,x['input_packet']['candidate_identity'])['global_errors'])

if __name__=='__main__':unittest.main()
