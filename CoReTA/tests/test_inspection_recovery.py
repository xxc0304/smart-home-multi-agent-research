import copy
import json
import time
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from tokenizers import Tokenizer
from coreta.inspection_recovery import RecoveryClient, InspectionRecoveryRunner, inspection_prompt
from coreta.audit_delivery import audit_reference_index
from coreta.schemas import ProtocolError

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'runs/math140-audit-delivery-20261020/4276ec64c178dafa'
def rows(name): return [json.loads(x) for x in (RUN/name).read_text(encoding='utf-8').splitlines()]
def config(): return json.loads((ROOT/'config/deepseek_flash_inspection.json').read_text(encoding='utf-8'))
def response(text): return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':text}]}]}

class InspectionRecoveryChecks(unittest.TestCase):
    def test_full_fixture_uses_real_schema_and_accepts_audit(self):
        from coreta.task_audit_binding import SourceBindingContracts
        from test_source_binding import BindingScript
        from test_revision import TASK
        tok=Tokenizer.from_file(str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'))
        with tempfile.TemporaryDirectory() as tmp:
            r=InspectionRecoveryRunner(TASK,Path(tmp),'recovery-fixture',
                SourceBindingContracts(ROOT/'design/v0.3/coreta.schema.json'),None,config(),
                json.loads((ROOT/'design/source_binding_prompts.json').read_text(encoding='utf-8')))
            r.client=RecoveryClient(r.config,r.log,transport=BindingScript(),
                token_counter=lambda s:len(tok.encode(s,add_special_tokens=False).ids))
            result=r.run()
            self.assertEqual(result['status'],'completed')
            self.assertTrue(result['pipeline_completed'])
            self.assertGreater(result['audit_record_count'],0)

    def test_only_inspection_limit_changed(self):
        old=json.loads((ROOT/'config/deepseek_flash_delivery.json').read_text(encoding='utf-8'))
        new=config();self.assertEqual(new['generation']['max_output_tokens']['inspect'],8192)
        new['generation']['max_output_tokens']['inspect']=4096
        self.assertEqual(old,new)

    def test_two_real_truncations_retained_exactly(self):
        incomplete=[x['response'] for x in rows('responses.jsonl') if x['response'].get('status')=='incomplete']
        self.assertEqual(len(incomplete),2)
        for saved in incomplete:
            logs=[];client=RecoveryClient(config(),lambda n,v:logs.append((n,v)),transport=lambda *a:copy.deepcopy(saved),token_counter=lambda x:1)
            with self.assertRaises(ProtocolError): client.complete({},deadline=time.monotonic()+5,logical_seed='offline')
            expected=''.join(c['text'] for o in saved['output'] if o['type']=='message' for c in o['content'] if c['type']=='output_text')
            self.assertEqual(client.last_incomplete['partial_output'],expected)
            self.assertEqual(client.last_incomplete['details'],{'reason':'max_output_tokens'})
            self.assertTrue(any(n=='responses.jsonl' for n,v in logs))

    def test_recovery_input_retains_material_and_partial_within_budget(self):
        req=rows('requests.jsonl')[-2]['payload'];old=req['instructions'];offset=old.index('\n{"ACTOR"')
        ctx=json.JSONDecoder().raw_decode(old[offset+1:])[0]
        tok=Tokenizer.from_file(str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'))
        client=RecoveryClient(config(),lambda *a:None,token_counter=lambda s:len(tok.encode(s,add_special_tokens=False).ids))
        for saved in [x['response'] for x in rows('responses.jsonl') if x['response'].get('status')=='incomplete']:
            partial=''.join(c['text'] for o in saved['output'] if o['type']=='message' for c in o['content'] if c['type']=='output_text')
            feedback={'code':'SCHEMA_ERROR','partial_output':partial,'incomplete_details':saved['incomplete_details']}
            prompt=inspection_prompt(old[:offset],'',ctx['ACTOR'],ctx['MATERIAL'],audit_reference_index(ctx['MATERIAL']),feedback)
            decoded=json.loads(prompt[prompt.index('\n{"ACTOR"')+1:])
            self.assertEqual(decoded['MATERIAL'],ctx['MATERIAL'])
            self.assertEqual(decoded['recovery_feedback']['partial_output'],partial)
            self.assertLess(client.size(client.payload(prompt,req['text']['format']['schema'],8192)),32768)

    def make_runner(self,transport):
        r=object.__new__(InspectionRecoveryRunner);r.calls=0;r.CAP=15;r.seed=17;r.repairs=0
        r.config=config();r.deadline=time.monotonic()+10;r.prompts={'system':'system','inspect':'inspect'}
        r.current={'candidate':{'artifact':'current','steps':[]}};r.pending={}
        r.contracts=Mock();r.contracts.schema.return_value={};r.log=Mock();r.accept_inspection=Mock()
        r.client=RecoveryClient(r.config,r.log,transport=transport,token_counter=lambda s:1)
        return r

    def test_partial_never_accepted_then_complete_recovery(self):
        saved=next(x['response'] for x in rows('responses.jsonl') if x['response'].get('status')=='incomplete')
        requests=[]
        def transport(payload,timeout):
            requests.append(copy.deepcopy(payload))
            return copy.deepcopy(saved) if len(requests)==1 else response('{}')
        r=self.make_runner(transport)
        value=r.call('inspect','A2','ClosureInspection',{'before':copy.deepcopy(r.current)})
        self.assertEqual(value,{})
        self.assertEqual(r.repairs,1);self.assertEqual(r.calls,1)
        r.accept_inspection.assert_called_once()
        self.assertIn('partial_output',requests[1]['instructions'])
        self.assertEqual(requests[1]['max_output_tokens'],8192)

    def test_two_truncations_stop_without_accepting(self):
        saved=next(x['response'] for x in rows('responses.jsonl') if x['response'].get('status')=='incomplete')
        r=self.make_runner(lambda *a:copy.deepcopy(saved))
        with self.assertRaises(ProtocolError): r.call('inspect','A2','ClosureInspection',{'before':copy.deepcopy(r.current)})
        r.accept_inspection.assert_not_called();self.assertEqual(r.client.attempts,2)

    def test_over_budget_sends_nothing(self):
        r=self.make_runner(Mock());r.client.size=lambda p:999999
        with self.assertRaises(ProtocolError): r.call('inspect','A2','ClosureInspection',{'before':copy.deepcopy(r.current)})
        self.assertEqual(r.client.attempts,0);r.accept_inspection.assert_not_called()

if __name__=='__main__': unittest.main()
