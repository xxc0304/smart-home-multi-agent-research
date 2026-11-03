import copy
import json
import tempfile
import unittest
from pathlib import Path
from tokenizers import Tokenizer
from coreta.protocol_stability import StabilityRunner, StabilityClient
from coreta.task_audit_binding import SourceBindingContracts
from coreta.schemas import ProtocolError

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'runs/math140-inspection-recovery-20261020/4276ec64c178dafa'

def saved_outputs():
    result=[]
    for l in (RUN/'responses.jsonl').read_text(encoding='utf-8').splitlines():
        r=json.loads(l)['response'];result.append(''.join(c.get('text','') for o in r['output'] if o['type']=='message' for c in o['content'] if c['type']=='output_text'))
    return result

def response(text): return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':text}]}]}

class StabilityChecks(unittest.TestCase):
    def make_runner(self,outputs,used_repairs=0):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        cfg=json.loads((ROOT/'config/deepseek_flash_inspection.json').read_text(encoding='utf-8'))
        task=json.loads((RUN/'public_task.json').read_text(encoding='utf-8'))
        r=StabilityRunner(task,Path(tmp.name),'stability-fixture',SourceBindingContracts(ROOT/'design/v0.3/coreta.schema.json'),None,cfg,json.loads((ROOT/'design/source_binding_prompts.json').read_text(encoding='utf-8')))
        tok=Tokenizer.from_file(str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'))
        self.requests=[]
        def transport(payload,timeout):
            self.requests.append(copy.deepcopy(payload));return response(outputs[len(self.requests)-1])
        r.client=StabilityClient(cfg,r.log,transport=transport,token_counter=lambda s:len(tok.encode(s,add_special_tokens=False).ids));r.repairs=used_repairs
        return r

    def patch(self):
        prompt=json.loads((RUN/'public_task.json').read_text(encoding='utf-8'))['prompt']
        quote=prompt[prompt.index('p(0,0)'):prompt.index('\\end{align*}')].strip()
        return json.dumps({'replacements':[{'fact_id':'F2','source_id':'prompt','quoted_text':quote}]})

    def test_real_syntax_then_quote_then_synthetic_patch(self):
        original=saved_outputs();r=self.make_runner(original+[self.patch()])
        bound=r._bound_facts_call('A2')
        self.assertEqual(r.repairs,2);self.assertEqual(r.calls,1);self.assertEqual(len(self.requests),3)
        self.assertEqual(bound['binding_status'],'all_sources_bound')
        second=json.loads(self.requests[1]['instructions'].split('\n')[-1])
        self.assertEqual(second['MATERIAL']['recovery_feedback']['previous_output'],original[0])
        third=json.loads(self.requests[2]['instructions'].split('\n')[-1])
        self.assertEqual([x['fact_id'] for x in third['MATERIAL']['binding_feedback']['unresolved']],['F2'])
        expected=json.loads(original[1])
        self.assertEqual(r.fact_binding_session.original_payload,expected)
        for f in bound['facts']:
            prior=next(x for x in expected['facts'] if x['fact_id']==f['fact_id'])
            self.assertEqual(f['normalized_fact'],prior['normalized_fact']);self.assertEqual(f['check_items'],prior['check_items'])

    def test_complete_v6_fixture_with_real_schema(self):
        from test_revision import TASK
        from test_source_binding import BindingScript
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        cfg=json.loads((ROOT/'config/deepseek_flash_inspection.json').read_text(encoding='utf-8'))
        r=StabilityRunner(TASK,Path(tmp.name),'full-stability',SourceBindingContracts(ROOT/'design/v0.3/coreta.schema.json'),None,cfg,json.loads((ROOT/'design/source_binding_prompts.json').read_text(encoding='utf-8')))
        tok=Tokenizer.from_file(str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'))
        r.client=StabilityClient(cfg,r.log,transport=BindingScript(),token_counter=lambda s:len(tok.encode(s,add_special_tokens=False).ids))
        result=r.run()
        self.assertEqual(result['status'],'completed');self.assertTrue(result['pipeline_completed'])
        self.assertGreater(result['audit_record_count'],0)

    def test_global_cap_not_increased(self):
        r=self.make_runner(saved_outputs(),used_repairs=1)
        with self.assertRaises(ProtocolError):r._bound_facts_call('A2')
        self.assertEqual(len(self.requests),2);self.assertEqual(r.repairs,2)

    def test_repeated_invalid_output_stops(self):
        r=self.make_runner(['{','{','{'])
        with self.assertRaises(ProtocolError):r._bound_facts_call('A2')
        self.assertEqual(len(self.requests),3);self.assertEqual(r.repairs,2)

    def test_patch_cannot_rewrite_locked_fact(self):
        bad=json.dumps({'replacements':[{'fact_id':'F1','source_id':'prompt','quoted_text':'invented'}]})
        r=self.make_runner(saved_outputs()+[bad])
        with self.assertRaises(ProtocolError):r._bound_facts_call('A2')
        self.assertEqual(r.fact_binding_session.bindings['F1']['status'],'unique_exact')
        self.assertEqual(r.fact_binding_session.pending,['F2'])

    def test_over_budget_zero_requests(self):
        r=self.make_runner([]);r.config['generation']['max_input_tokens']=1
        with self.assertRaises(ProtocolError):r._bound_facts_call('A2')
        self.assertEqual(len(self.requests),0)

if __name__=='__main__':unittest.main()
