import copy
import json
import tempfile
import unittest
from pathlib import Path
from coreta.minimal_review import ReviewAdapter,RepairBudget
from coreta.protocol_stability import StabilityClient
from coreta.minimal_review_transport import execute_review
ROOT=Path(__file__).resolve().parents[1]

def response(text,status='completed'):
    return {'status':status,'incomplete_details':{'reason':'max_output_tokens'} if status=='incomplete' else None,
        'output':[{'type':'message','content':[{'type':'output_text','text':text}]}]}
class MinimalTransportChecks(unittest.TestCase):
    def setup_run(self,outputs,limit=32768):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        cfg=json.loads((ROOT/'config/deepseek_flash_inspection.json').read_text());cfg['generation']['max_input_tokens']=limit
        ex=json.loads((ROOT/'design/convergence/example_same_object.json').read_text())
        adapter=ReviewAdapter(Path(tmp.name)/'adapter',ROOT/'design/convergence/minimal_review.schema.json',token_counter=lambda s:1,shared_budget=RepairBudget())
        requests=[]
        def transport(p,timeout):requests.append(copy.deepcopy(p));return copy.deepcopy(outputs[len(requests)-1])
        client=StabilityClient(cfg,adapter.log,transport=transport,token_counter=lambda s:1)
        return ex,adapter,client,requests
    def good(self):return json.loads((ROOT/'design/convergence/example_same_object.json').read_text())['model_output_example']
    def test_success_one_call(self):
        ex,a,c,req=self.setup_run([response(json.dumps(self.good()))]);r=execute_review(a,c,ex['input_packet'])
        self.assertEqual(r['http_attempts'],1);self.assertTrue(r['final_projection']['all_issues_resolved']);self.assertEqual(req[0]['max_output_tokens'],8192)
    def test_truncated_then_complete_includes_original(self):
        partial='{"issue_reviews":';ex,a,c,req=self.setup_run([response(partial,'incomplete'),response(json.dumps(self.good()))])
        r=execute_review(a,c,ex['input_packet']);self.assertEqual(r['repairs_used'],1)
        self.assertIn('previous_output',req[1]['instructions']);self.assertIn('issue_reviews',req[1]['instructions'])
        self.assertTrue(r['final_projection']['all_issues_resolved'])
    def test_business_conflict_is_not_retried(self):
        bad=self.good();bad['issue_reviews']['I1']['current_checks'][0]['observed_value']='1'
        ex,a,c,req=self.setup_run([response(json.dumps(bad))]);r=execute_review(a,c,ex['input_packet'])
        self.assertEqual(len(req),1);self.assertFalse(r['final_projection']['all_issues_resolved'])
    def test_provider_payload_preflight_sends_zero(self):
        ex,a,c,req=self.setup_run([],limit=1);r=execute_review(a,c,ex['input_packet'])
        self.assertEqual(c.attempts,0);self.assertEqual(r['terminal_error']['code'],'CONTEXT_OVERFLOW')
    def test_structural_error_is_bounded_and_retained(self):
        ex,a,c,req=self.setup_run([response('{'),response('{'),response('{')]);r=execute_review(a,c,ex['input_packet'])
        self.assertEqual(len(req),3);self.assertEqual(r['repairs_used'],2);self.assertEqual(r['terminal_error']['code'],'REPAIR_LIMIT')
if __name__=='__main__':unittest.main()
