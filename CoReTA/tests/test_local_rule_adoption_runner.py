from pathlib import Path
import tempfile
import unittest
import json
from unittest.mock import patch
import local_judgment_frontend as io
import run_local_rule_adoption as runner
from coreta.schemas import ProtocolError

class AdoptionRunnerTests(unittest.TestCase):
    @staticmethod
    def mock(payload,timeout):
        p=io.strict_json(payload['instructions'].split('PACKET=',1)[1])
        a=dict(choice=p['task']['choices'][0]['id'],reasoning='A technical fixture, not a model result.',used_contributions=['C1'])
        return dict(status='completed',usage=dict(input_tokens=10,output_tokens=10),output=[dict(type='message',content=[dict(type='output_text',text=json.dumps(a))])])

    def test_complete24_and_exact_frozen_payloads_no_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'p';o=Path(tmp)/'o';runner.freeze(p)
            s=runner.run(p,o,transport=self.mock,local_validation=True)
            self.assertEqual(s['attempts'],24);self.assertEqual(s['status'],'completed')
            self.assertEqual(s['reserved_output'],36864);self.assertEqual(len(list(o.glob('*.raw.txt'))),24)
            self.assertEqual(len(io.read(o/'review.json')['rows']),24)
            with self.assertRaisesRegex(ValueError,'no resume'):runner.run(p,o,transport=self.mock,local_validation=True)

    def test_independent_errors_and_global_stops(self):
        for mode in ('one_bad','two_bad','transport','usage','overcap'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'p';o=Path(tmp)/'o';runner.freeze(p);calls=0
                def mock(payload,timeout):
                    nonlocal calls
                    calls+=1
                    if mode=='transport' and calls==2:raise TimeoutError('local fixture')
                    r=self.mock(payload,timeout)
                    if (mode=='one_bad' and calls==1) or (mode=='two_bad' and calls<=2):r['output'][0]['content'][0]['text']='{'
                    if mode=='usage' and calls==2:r.pop('usage')
                    if mode=='overcap' and calls==2:r['usage']['output_tokens']=1537
                    return r
                if mode=='one_bad':
                    s=runner.run(p,o,transport=mock,local_validation=True)
                    self.assertEqual(s['status'],'completed_with_quarantine');self.assertEqual(calls,24)
                else:
                    with self.assertRaises((RuntimeError,ProtocolError)):runner.run(p,o,transport=mock,local_validation=True)
                    self.assertEqual(calls,2)
                self.assertEqual(len(io.read(o/'review.json')['rows']),24)

    def test_live_gates_and_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'p';runner.freeze(p)
            with self.assertRaises(FileNotFoundError):runner.gates(p)
            sha=io.digest(p/'manifest.json')
            io.write(p/'PREFLIGHT.json',dict(status='passed',manifest_sha256=sha))
            io.write(p/'EXPERIMENT_REVIEW.json',dict(science='PASS',readiness='PASS',technical_launch='RUN_ALLOWED',manifest_sha256=sha))
            io.write(p/'AUTHORIZATION.json',dict(authorized=True,max_requests=144,max_output_tokens=221184,destination='https://api.deepseek.com/responses',manifest_sha256=sha,user_authorization_text='TEST ONLY old batch'))
            with self.assertRaisesRegex(ValueError,'authorization'):runner.gates(p)
            (p/'packets/01.json').write_text('{}',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'changed'):runner.verify(p)

if __name__=='__main__':unittest.main()
