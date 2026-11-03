import copy
import json
import unittest
from unittest.mock import Mock
from coreta.schemas import ProtocolError
from pathlib import Path
from tokenizers import Tokenizer
from coreta.audit_delivery import audit_reference_index, apply_prompt, DeliveryAuditRunner
from coreta.model_client import DeepSeekClient
from coreta.revision import check_refs

ROOT = Path(__file__).resolve().parents[1]

class DeliveryChecks(unittest.TestCase):
    def test_citation_alone_does_not_grant_visibility(self):
        for key in ['evidence_refs', 'evidence_record_ids', 'target_refs']:
            self.assertNotIn('fake', audit_reference_index({key: ['fake']}))
        self.assertNotIn('fake', audit_reference_index({'record_id': 'fake'}))

    def test_complete_record_grants_visibility(self):
        row = {'record_id':'audit1','event_id':'event1','auditor':'A2','candidate_version':2,
               'candidate_hash':'hash','payload':{'cases':[]},'effective_outcome':'finding_open',
               'validation_errors':[]}
        self.assertIn('audit1', audit_reference_index({'issues':[{'evidence_records':[row]}]}))

    def test_budget_overflow_sends_nothing(self):
        runner=object.__new__(DeliveryAuditRunner)
        runner.calls=0; runner.CAP=15; runner.issues={}; runner.config={'generation':{'max_output_tokens':{'apply':100},'max_input_tokens':200}}
        runner.contracts=Mock(); runner.contracts.schema.return_value={}
        runner.prompts={'system':'system','apply':'apply'}
        runner.client=Mock();runner.client.size.return_value=150
        runner.log=Mock()
        with self.assertRaises(ProtocolError): runner.call('apply','A0','ClosureUpdate',{})
        runner.client.complete.assert_not_called()

    def test_invalid_reference_does_not_get_silently_rewritten(self):
        from coreta.schemas import ProtocolError
        with self.assertRaises(ProtocolError):
            check_refs({'evidence_refs':['fake']},set(audit_reference_index({'evidence_record_ids':['fake']})))

    def test_real_failed_apply_is_visible_and_lossless_repair_fits(self):
        p=ROOT/'runs/math140-closure-reference-20261020/4276ec64c178dafa'
        rows=lambda name:[json.loads(x) for x in (p/name).read_text(encoding='utf-8').splitlines()]
        request=rows('requests.jsonl')[-1]['payload']
        old=request['instructions']
        ctx=json.JSONDecoder().raw_decode(old[old.index('\n{"ACTOR"')+1:])[0]
        material=ctx['MATERIAL']; original=copy.deepcopy(material)
        visible=audit_reference_index(material)
        error=next(x for x in rows('validation.jsonl') if x['stage']=='apply' and x['code']=='REFERENCE_ERROR')
        value=json.loads(error['raw'])
        check_refs(value,set(visible))
        self.assertIn('coreta-source-binding-6a3cd0d909ca:e0007:a01',visible)
        config=json.loads((ROOT/'config/deepseek_flash_delivery.json').read_text(encoding='utf-8'))
        tok=Tokenizer.from_file(str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'))
        client=DeepSeekClient(config,lambda *args:None,token_counter=lambda s:len(tok.encode(s,add_special_tokens=False).ids))
        header=old[:old.index('\n{"ACTOR"')]
        prompt=apply_prompt(header,'',ctx['ACTOR'],material,visible,error['raw'],error['detail'])
        payload=client.payload(prompt,request['text']['format']['schema'],4096)
        self.assertLessEqual(client.size(payload),32768)
        decoded=json.JSONDecoder().raw_decode(prompt[prompt.rindex('\n{')+1:])[0]
        self.assertEqual(decoded['MATERIAL'],original)
        self.assertEqual(decoded['PREVIOUS_OUTPUT'],value)
        self.assertEqual(material,original)

if __name__=='__main__': unittest.main()
