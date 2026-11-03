import copy,json,tempfile,unittest
from pathlib import Path
from coreta.converged_flow import ConvergedFlow
from coreta.protocol_stability import StabilityRunner,StabilityClient
from coreta.task_audit_binding import SourceBindingContracts
from test_source_binding import BindingScript
from test_revision import TASK
ROOT=Path(__file__).resolve().parents[1]
class FlowScript(BindingScript):
    def __init__(self,fail_rounds=1,malformed=0):
        super().__init__();self.round=0;self.fail_rounds=fail_rounds;self.malformed=malformed;self.packets=[]
    def __call__(self,payload,timeout):
        props=payload['text']['format']['schema']['properties']
        if 'issue_reviews' not in props:
            response=super().__call__(payload,timeout)
            if 'closure_proposals' in props and getattr(self,'repair_candidate',False):
                value=json.loads(response['output'][0]['content'][0]['text'])
                if value['closure_proposals']:
                    value['candidate']['artifact']='Repaired fixture artifact'
                    value['candidate']['steps'][0]['text']='Repaired fixture derivation'
                    for proposal in value['closure_proposals']:
                        proposal.update(closure_path='repair',disposition='addressed',changed_step_ids=['s1'])
                    response['output'][0]['content'][0]['text']=json.dumps(value)
            return response
        packet=json.loads(payload['instructions'].split('\n')[-1])['packet'];self.packets.append(packet)
        if self.malformed:
            self.malformed-=1;value='broken'
        else:
            bad=self.round<self.fail_rounds;self.round+=1;reviews={}
            for handle,issue in packet['issues'].items():
                check={'target_handle':'C1','task_refs':['T1'],'input':'fixture input','quantity':'fixture scalar',
                    'expected_value':'0','observed_value':'1' if bad else '0','comparison_kind':'exact_equality',
                    'outcome':'match','reason':'Controlled offline observation'}
                reviews[handle]={'original_case_reviews':[{'case_handle':h,'observed_value':c['old_observed_value'],
                    'original_assessment':'supported','reason':'Controlled fresh recomputation'} for h,c in issue['historical_cases'].items()],
                    'current_checks':[check],'verdict':'resolved','reason':'Controlled offline review'}
            value=json.dumps({'issue_reviews':reviews,'new_findings':[]})
        return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':value}]}]}
class FlowChecks(unittest.TestCase):
    def run_flow(self,script):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);path=Path(temp.name)
        config=json.loads((ROOT/'config/deepseek_flash_inspection.json').read_text());config['generation']['max_input_tokens']=1000000
        b=StabilityRunner(TASK,path,'flow-fixture',SourceBindingContracts(ROOT/'design/v0.3/coreta.schema.json'),None,config,
            json.loads((ROOT/'design/source_binding_prompts.json').read_text()))
        b.client=StabilityClient(config,b.log,transport=script)
        flow=ConvergedFlow(b,ROOT/'design/convergence/evidence_review.schema.json',token_counter=lambda _:1)
        return flow,flow.run()
    def test_clean_chain(self):
        flow,r=self.run_flow(FlowScript(0));self.assertEqual(r['stop_reason'],'complete',r)
        self.assertEqual(r['normal_calls'],8);self.assertEqual(r['review_status'],'reviewed');self.assertFalse(r['finalizer_changed'])
    def test_counterexample_then_recheck(self):
        script=FlowScript(1);flow,r=self.run_flow(script)
        self.assertEqual(r['stop_reason'],'complete',r);self.assertEqual(r['normal_calls'],11)
        self.assertEqual(r['native_evidence_count'],1)
        self.assertEqual(r['issues']['i0001']['status'],'dismissed')
        self.assertEqual(next(iter(script.packets[1]['issues'].values()))['historical_cases']['H1']['old_observed_value'],'1')
        self.assertEqual(flow.native_ledger[0]['check']['observed_value'],'1')
        for p in script.packets:self.assertEqual(len(set(p['roles'].values())),3)
    def test_repair_changes_candidate_then_closes(self):
        script=FlowScript(1);script.repair_candidate=True
        flow,r=self.run_flow(script)
        self.assertEqual(r['stop_reason'],'complete',r)
        self.assertEqual(r['issues']['i0001']['status'],'addressed')
        self.assertEqual(r['artifact'],'Repaired fixture artifact')
        self.assertNotEqual(script.packets[0]['candidate_identity'],script.packets[1]['candidate_identity'])
        self.assertNotEqual(script.packets[1]['historical_objects']['O1']['definition'],r['artifact'])
    def test_last_round_conflict_kept(self):
        flow,r=self.run_flow(FlowScript(9));self.assertEqual(r['stop_reason'],'budget_exhausted',r)
        self.assertEqual(r['normal_calls'],14);self.assertEqual(r['review_status'],'unreviewed')
        self.assertTrue(any(i['status']=='open' for i in r['issues'].values()))
    def test_bounded_structural_repair(self):
        flow,r=self.run_flow(FlowScript(0,1));self.assertEqual(r['stop_reason'],'complete',r)
        self.assertEqual(r['format_repairs'],1);self.assertEqual(r['http_attempts'],9)
    def test_facts_and_review_share_repair_budget(self):
        script=FlowScript(0,1);script.initial_bad=True
        flow,r=self.run_flow(script)
        self.assertEqual(r['stop_reason'],'complete',r)
        self.assertEqual(r['format_repairs'],2)
        self.assertEqual(flow.budget.used,2)
    def test_repair_exhaustion(self):
        flow,r=self.run_flow(FlowScript(0,3));self.assertEqual(r['stop_reason'],'runtime_error',r)
        self.assertEqual(r['format_repairs'],2);self.assertEqual(r['review_status'],'unreviewed')
if __name__=='__main__':unittest.main()
