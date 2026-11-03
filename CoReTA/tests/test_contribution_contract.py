import copy
import json
from pathlib import Path
import tempfile
import unittest

from jsonschema import validate
from jsonschema.exceptions import ValidationError
from coreta.workboard.contribution_contract import (
    VERSION, ContributionInterfaceError, extraction_schema, normalize_contribution,
    assert_execution_admission)
import candidate_transfer_probe as probe


class ContributionContractTests(unittest.TestCase):
    def packet(self):
        return dict(task=dict(choices=[dict(id='option_1',text='Shelter Alpha'),
                                      dict(id='option_2',text='Shelter Beta')]),
            public_sources=[dict(ref='TASK',content='Choose a reachable site.'),
                            dict(ref='PUBLIC.1',content='Bridge to Alpha closed.')],
            own_sources=[dict(ref='S01',content='Beta is reachable.')],
            field_meanings=dict(reachable='Current access, not historical reputation.'))

    def answer(self):
        return dict(text='Partial evidence.',facts=[dict(candidate='Shelter Beta',field='reachable',
            value=True,source='S01',quote='Beta is reachable.')],conditions=[],caveats=[],solution=None)

    def test_task_schema_excludes_unknown_candidates_sources_and_types(self):
        packet=self.packet();schema=extraction_schema(packet);answer=self.answer()
        validate(answer,schema)
        for key,value in [('candidate','Beta'),('source','S02'),('field','invented'),('value','true')]:
            changed=copy.deepcopy(answer);changed['facts'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValidationError):validate(changed,schema)

    def test_exact_names_and_unique_quote_source_normalization_preserve_input(self):
        answer=self.answer();answer['facts'][0]['source']='TASK';original=copy.deepcopy(answer)
        normalized,events=normalize_contribution(answer,self.packet())
        self.assertEqual(answer,original)
        self.assertEqual(normalized['facts'][0]['candidate'],'option_2')
        self.assertEqual(normalized['facts'][0]['source'],'S01')
        self.assertEqual(normalized['facts'][0]['quote'],answer['facts'][0]['quote'])
        self.assertEqual([e['kind'] for e in events],['exact_candidate_label','unique_exact_quote_source'])

    def test_ambiguous_or_unseen_quote_cannot_rebind(self):
        packet=self.packet();packet['public_sources'].append(dict(ref='PUBLIC.2',content='Beta is reachable.'))
        answer=self.answer();answer['facts'][0]['source']='TASK'
        with self.assertRaisesRegex(ContributionInterfaceError,'ambiguous'):
            normalize_contribution(answer,packet)
        for source,quote in [('S02','Secret other member text.'),('TASK','Not in any visible original.')]:
            answer=self.answer();answer['facts'][0].update(source=source,quote=quote)
            with self.assertRaises(ContributionInterfaceError):normalize_contribution(answer,self.packet())

    def test_short_or_unlisted_name_is_not_guessed_and_no_entailment_claim(self):
        answer=self.answer();answer['facts'][0]['candidate']='Beta'
        with self.assertRaisesRegex(ContributionInterfaceError,'candidate'):
            normalize_contribution(answer,self.packet())
        # Interface checking intentionally does not certify a value entailed by its quote.
        answer=self.answer();answer['facts'][0]['value']=False
        normalized,_=normalize_contribution(answer,self.packet())
        self.assertIs(normalized['facts'][0]['value'],False)

    def test_executor_rejection_is_not_silently_accepted(self):
        with self.assertRaises(ContributionInterfaceError):
            assert_execution_admission(dict(notices=[dict(kind='rejected_fact')],member_conditions=[]))
        with self.assertRaises(ContributionInterfaceError):
            assert_execution_admission(dict(notices=[],member_conditions=[dict(diagnostic='unsupported_expression')]))
        assert_execution_admission(dict(notices=[],member_conditions=[]))

    def test_scoped_failure_stops_real_runner_after_first_raw_response(self):
        with tempfile.TemporaryDirectory() as temp:
            prepared=Path(temp)/'prepared';out=Path(temp)/'run'
            probe.prepare(probe.ROOT/'runs/candidate-transfer-tasks-prepared-20261025-r1',prepared)
            self.assertEqual(probe.read(prepared/'manifest.json')['contribution_contract_version'],VERSION)
            calls=0
            def transport(payload,timeout):
                nonlocal calls
                calls+=1
                packet=json.loads(payload['instructions'].split('PACKET=',1)[1]);src=packet['own_sources'][0]
                answer=dict(text='Invalid candidate fixture.',facts=[dict(candidate='Unknown site',
                    field=next(iter(packet['field_meanings'])),value=None,source=src['ref'],quote=src['content'])],
                    conditions=[],caveats=[])
                self.assertIn('enum',payload['text']['format']['schema']['properties']['facts']['items']['properties']['candidate'])
                return dict(status='completed',usage=dict(input_tokens=1,output_tokens=1),
                    output=[dict(type='message',content=[dict(type='output_text',text=json.dumps(answer))])])
            with self.assertRaises(ContributionInterfaceError):
                probe.run(prepared,out,transport=transport,local_validation=True)
            state=probe.read(out/'progress.json')
            self.assertEqual(calls,1);self.assertEqual(state['attempts'],1)
            self.assertEqual(state['interface_audit'][0]['status'],'blocked')
            self.assertTrue((out/'01.raw.txt').exists())
            self.assertEqual(len(state['completed']),0)
            self.assertEqual(len(state['roster']),24)


if __name__=='__main__':unittest.main()
