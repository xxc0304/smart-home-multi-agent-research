import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from coreta.schemas import ProtocolError
import local_judgment_frontend as io
import run_local_rule_frontend as runner


class RuleLiveRunnerTests(unittest.TestCase):
    @staticmethod
    def mock(payload,timeout):
        packet=io.strict_json(payload['instructions'].split('PACKET=',1)[1])
        source=(packet['own_sources'] or packet['public_sources'])[0]['ref']
        if 'historical_work' in packet:
            answer=dict(text='A self-contained local synthetic question.',status='proceed',source_ids=[source],target_ids=['new'])
        else:answer=dict(conclusion='Technical fixture only.',source_ids=[source],status='conditional',scope='Fixture.',missing=[])
        return dict(status='completed',usage=dict(input_tokens=10,output_tokens=10),output=[dict(type='message',content=[dict(type='output_text',text=json.dumps(answer))])])

    def test_full72_live_transport_mock_with_actual_dynamic_stage2_and_no_gold_read(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'p';o=Path(temp)/'o';runner.freeze(p);original=io.read
            def guard(path):
                self.assertNotIn('OFFLINE_',str(path));self.assertNotIn('offline/',str(path).replace('\\','/'));return original(path)
            with patch.object(io,'read',guard):s=runner.run(p,o,transport=self.mock,local_validation=True)
            self.assertEqual(s['attempts'],72);self.assertEqual(s['reserved_output'],110592)
            self.assertEqual(s['status'],'completed');self.assertEqual(s['input_tokens'],720)
            self.assertEqual(len(original(o/'review.json')['rows']),72)
            self.assertEqual(len(original(o/'ANNOTATION_VIEWS.json')['views']),36)
            self.assertEqual(len(list(o.glob('*.raw.txt'))),72)
            second=original(o/'actual_requests/02.json');packet=io.strict_json(second['instructions'].split('PACKET=',1)[1])
            self.assertEqual(packet['earlier_work'],'A self-contained local synthetic question.')
            self.assertNotIn('historical_work',packet)
            self.assertNotIn('target_ids',packet)
            with self.assertRaisesRegex(ValueError,'no resume'):runner.run(p,o,transport=self.mock,local_validation=True)

    def test_pass_and_first_failure_do_not_corrupt_dependent_input(self):
        for kind in ('pass','bad_first','bad_second','incomplete'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as temp:
                p=Path(temp)/'p';o=Path(temp)/'o';runner.freeze(p);calls=0
                def mock(payload,timeout):
                    nonlocal calls
                    calls+=1;r=self.mock(payload,timeout)
                    if calls==1 and kind=='pass':
                        a=json.loads(r['output'][0]['content'][0]['text']);a['status']='pass';r['output'][0]['content'][0]['text']=json.dumps(a)
                    if (calls==1 and kind=='bad_first') or (calls==2 and kind=='bad_second'):r['output'][0]['content'][0]['text']='{'
                    if calls==1 and kind=='incomplete':r['status']='incomplete'
                    return r
                s=runner.run(p,o,transport=mock,local_validation=True)
                review=io.read(o/'review.json')['rows']
                if kind=='pass':self.assertEqual(review[1]['status'],'skipped_pass');self.assertEqual(calls,71)
                elif kind in ('bad_first','incomplete'):self.assertEqual(review[1]['status'],'blocked_upstream');self.assertEqual(calls,71)
                else:self.assertEqual(review[1]['status'],'quarantined');self.assertEqual(calls,72)
                self.assertEqual(review[2]['status'],'readable')

    def test_global_faults_and_consecutive_bad_outputs_preserve_full_roster(self):
        for mode in ('transport','usage','overcap','two_bad'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temp:
                p=Path(temp)/'p';o=Path(temp)/'o';runner.freeze(p);calls=0
                def mock(payload,timeout):
                    nonlocal calls
                    calls+=1
                    if mode=='transport' and calls==2:raise TimeoutError('fixture')
                    r=self.mock(payload,timeout)
                    if mode=='usage' and calls==2:r.pop('usage')
                    if mode=='overcap' and calls==2:r['usage']['output_tokens']=1537
                    if mode=='two_bad' and calls in (1,2):r['output'][0]['content'][0]['text']='{'
                    return r
                with self.assertRaises((RuntimeError,ProtocolError)):runner.run(p,o,transport=mock,local_validation=True)
                s=io.read(o/'progress.json');self.assertEqual(s['status'],'stopped');self.assertEqual(calls,2)
                self.assertEqual(len(io.read(o/'review.json')['rows']),72)
                self.assertTrue(any(r['second_status']=='not_run' for r in io.read(o/'ANNOTATION_VIEWS.json')['views']))

    def test_live_gates_mock_gate_and_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'p';o=Path(temp)/'o';runner.freeze(p)
            with self.assertRaisesRegex(ValueError,'explicit mock'):runner.run(p,o,local_validation=True)
            with self.assertRaises(FileNotFoundError):runner.gates(p)
            sha=io.digest(p/'manifest.json')
            io.write(p/'PREFLIGHT.json',dict(status='passed',manifest_sha256=sha))
            io.write(p/'EXPERIMENT_REVIEW.json',dict(science='PASS',readiness='PASS',technical_launch='RUN_ALLOWED',manifest_sha256=sha))
            io.write(p/'AUTHORIZATION.json',dict(authorized=True,max_requests=12,manifest_sha256=sha,destination='https://api.deepseek.com/responses',user_authorization_text='TEST ONLY'))
            with self.assertRaisesRegex(ValueError,'authorization'):runner.gates(p)
            (p/'contexts/rule-dev-01/A1.json').write_text('{}',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'changed'):runner.verify(p)

    def test_preflight_full_history_load_is_marked_mock(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'p';runner.freeze(p);r=runner.preflight(p)
            self.assertEqual(r['mock_attempts'],72);self.assertEqual(r['real_history_inputs'],22)
            self.assertEqual(r['real_first_stage_provider_outputs'],0)
            self.assertLessEqual(r['maximum_adapted_output_tokens'],1536)
            self.assertLess(r['maximum_input_estimate'],8192)
            with self.assertRaisesRegex(ValueError,'new preflight'):runner.preflight(p)


if __name__=='__main__':unittest.main()
