import json
from pathlib import Path
import tempfile
import unittest
from coreta.schemas import ProtocolError

import local_judgment_frontend as interface
import local_judgment_handle_contract as contract
import prepare_local_judgment_calibration_v2 as prep
import run_local_judgment_calibration_v2 as runner


class HandleContractTests(unittest.TestCase):
    @staticmethod
    def packet():
        return prep.build_packet(interface.read(prep.ITEMS)['items'][0], 'with_resources')

    @staticmethod
    def mock(payload, timeout):
        packet = interface.strict_json(payload['instructions'].split('PACKET=', 1)[1])
        source = (packet['own_sources'] or packet['public_sources'])[0]['ref']
        answer = dict(conclusion='Synthetic response, not a capability result.', status='conditional',
                      source_ids=[source], scope='Technical fixture.', missing=[])
        return dict(status='completed', usage=dict(input_tokens=10,output_tokens=10),
                    output=[dict(type='message',content=[dict(type='output_text',text=json.dumps(answer))])])

    def test_handles_render_exact_visible_original_and_do_not_certify_truth(self):
        packet=self.packet()
        raw=json.dumps(dict(conclusion='An intentionally unsupported full guarantee.',source_ids=['S06','S06']))
        value,issues=contract.decode(raw,'second',packet)
        source=next(s['content'] for s in packet['own_sources'] if s['ref']=='S06')
        self.assertEqual(len(value['evidence']),1)
        self.assertEqual(value['evidence'][0]['quote'],source)
        self.assertEqual(value['conclusion'],'An intentionally unsupported full guarantee.')
        self.assertTrue(any(x['issue']=='duplicate' for x in issues))
        self.assertIsNone(value['scope'])

    def test_annotation_errors_do_not_discard_answer_or_invent_evidence(self):
        value,issues=contract.decode(json.dumps(dict(conclusion='Readable finding.', source_ids=['S01',False],
            status='certain',scope=5,missing=False,evidence=[{'quote':'Mis-copied text'}])), 'second',self.packet())
        self.assertEqual(value['evidence'],[])
        self.assertEqual(value['conclusion'],'Readable finding.')
        self.assertIsNone(value['status'])
        self.assertGreaterEqual(len(issues),5)
        for raw in ['{','{"conclusion":"a","conclusion":"b"}','{}','{"conclusion":" "}']:
            with self.assertRaises(ValueError):contract.decode(raw,'second',self.packet())

    def test_actual_failed_v1_response_survives_only_as_explicit_adaptation(self):
        path=interface.ROOT/'runs/local-judgment-moon-calibration-live-20261025-r1/14.raw.txt'
        original=interface.read(path)
        item=interface.read(prep.ITEMS)['items'][3]
        packet=prep.build_packet(item,'without_resources')
        adapted={k:original[k] for k in ['conclusion','status','scope','missing']}
        adapted['source_ids']=['T']
        result,_=contract.decode(json.dumps(adapted),'second',packet)
        self.assertEqual(result['conclusion'],original['conclusion'])
        self.assertTrue(result['evidence'][0]['quote'].startswith('You'))
        self.assertTrue(original['evidence'][0]['quote'].startswith('you'))
        # No rewrite or re-admission of v1's raw response occurs.
        self.assertEqual(interface.read(path),original)

    def test_one_unreadable_slot_continues_without_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            prepared=Path(folder)/'p';out=Path(folder)/'out';runner.freeze(prepared)
            calls=0
            def mock(payload,timeout):
                nonlocal calls
                calls+=1;r=self.mock(payload,timeout)
                if calls==14:r['output'][0]['content'][0]['text']='{'
                return r
            state=runner.run(prepared,out,transport=mock,local_validation=True)
            self.assertEqual(calls,24)
            self.assertEqual(state['status'],'completed_with_quarantine')
            self.assertEqual(len(state['completed']),23)
            self.assertEqual([r['slot'] for r in state['quarantined']],[14])
            self.assertEqual(len((out/'requests.jsonl').read_text(encoding='utf-8').splitlines()),24)
            self.assertEqual((out/'14.raw.txt').read_text(encoding='utf-8'),'{')
            self.assertEqual(interface.read(out/'review.json')['rows'][13]['status'],'quarantined')

    def test_two_consecutive_unreadable_stops_and_transport_stops_immediately(self):
        for mode in ['two','transport','incomplete','no_text','unknown_usage']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                prepared=Path(folder)/'p';out=Path(folder)/'out';runner.freeze(prepared)
                calls=0
                def mock(payload,timeout):
                    nonlocal calls
                    calls+=1
                    if mode=='transport' and calls==14:raise TimeoutError('synthetic')
                    r=self.mock(payload,timeout)
                    if mode=='two' and calls in (14,15):r['output'][0]['content'][0]['text']='{'
                    if mode=='incomplete' and calls==14:r['status']='incomplete'
                    if mode=='no_text' and calls==14:r['output']=[]
                    if mode=='unknown_usage' and calls==14:r.pop('usage')
                    return r
                if mode in ['incomplete','no_text']:
                    state=runner.run(prepared,out,transport=mock,local_validation=True)
                    self.assertEqual(state['status'],'completed_with_quarantine');self.assertEqual(calls,24)
                else:
                    with self.assertRaises((ValueError,ProtocolError)):runner.run(prepared,out,transport=mock,local_validation=True)
                    state=interface.read(out/'progress.json')
                    self.assertEqual(state['status'],'stopped')
                    self.assertEqual(calls,15 if mode=='two' else 14)

    def test_invalid_source_is_visible_quality_issue_not_a_budget_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            prepared=Path(folder)/'p';out=Path(folder)/'out';runner.freeze(prepared)
            calls=0
            def mock(payload,timeout):
                nonlocal calls
                calls+=1;r=self.mock(payload,timeout)
                if calls in [14,15]:
                    a=json.loads(r['output'][0]['content'][0]['text']);a['source_ids']=['UNSEEN'];r['output'][0]['content'][0]['text']=json.dumps(a)
                return r
            state=runner.run(prepared,out,transport=mock,local_validation=True)
            self.assertEqual(state['status'],'completed')
            self.assertEqual(len(state['completed']),24)
            for index in [13,14]:
                self.assertEqual(state['completed'][index]['answer']['evidence'],[])
                self.assertTrue(state['completed'][index]['answer']['annotation_issues'])

    def test_v1_frozen_package_rejected_and_v2_load_marked_mock(self):
        with self.assertRaisesRegex(ValueError,'new v2 batch'):
            runner.verify(interface.ROOT/'runs/local-judgment-moon-calibration-prepared-20261025-r2')
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'p';runner.freeze(p)
            result=runner.preflight(p)
            self.assertEqual(result['mock_attempts'],24)
            self.assertEqual(result['real_new_task_provider_outputs'],0)
            self.assertLess(result['maximum_adapted_output_tokens'],1536)


if __name__=='__main__':unittest.main()
