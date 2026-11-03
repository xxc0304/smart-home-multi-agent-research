import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import local_judgment_frontend as io
import run_local_rule_confirmation as runner
from coreta.schemas import ProtocolError

class ConfirmationRunnerTests(unittest.TestCase):
    @staticmethod
    def response(payload,call):
        packet=json.loads(payload['instructions'].split('PACKET=',1)[1])
        if 'historical_work' in packet:
            value=dict(text=f'Unique first contribution {call}',status='proceed',source_ids=[packet['member']+'.S1'],target_ids=['new'])
        else:
            value=dict(conclusion='Technical execution fixture.',status='conditional',source_ids=[packet['member']+'.S1'],scope='Local fixture.',missing=[])
        return dict(status='completed',usage=dict(input_tokens=10,output_tokens=10),output=[dict(type='message',content=[dict(type='output_text',text=json.dumps(value))])])

    def test_full144_repeat_isolation_dynamic_inputs_and_no_offline_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'p';o=Path(tmp)/'o';runner.freeze(p);calls=0;original=io.read
            def guard(path):
                self.assertNotIn('OFFLINE_',str(path));return original(path)
            def mock(payload,timeout):
                nonlocal calls
                calls+=1
                packet=json.loads(payload['instructions'].split('PACKET=',1)[1])
                if calls%2==0:
                    self.assertEqual(packet['earlier_work'],f'Unique first contribution {calls-1}')
                    self.assertNotIn('historical_work',packet)
                return self.response(payload,calls)
            with patch.object(io,'read',guard):s=runner.run(p,o,transport=mock,local_validation=True)
            self.assertEqual(s['attempts'],144);self.assertEqual(s['reserved_output'],221184)
            self.assertEqual(s['status'],'completed');self.assertEqual(s['output_tokens'],1440)
            keys=original(o/'ANNOTATION_KEY.json');self.assertEqual(len(keys),72)
            self.assertEqual(sum(k['repeat']==1 for k in keys),36)
            self.assertEqual(len(set(k['group'] for k in keys)),72)
            self.assertEqual(len(list(o.glob('*.raw.txt'))),144)
            for r in original(p/'PLAN.json')['schedule']:
                if r['stage']=='first' and r['repeat']==1:
                    counterpart=next(x for x in original(p/'PLAN.json')['schedule'] if x['task']==r['task'] and x['member']==r['member'] and x['repeat']==2 and x['stage']=='first' and x['method']==r['method'])
                    self.assertNotEqual(counterpart['group'],r['group'])

    def test_pass_quarantine_and_systemic_stop_keep_roster(self):
        for mode in ('pass','bad_first','bad_second','two_bad','transport','unknown_usage','overcap'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'p';o=Path(tmp)/'o';runner.freeze(p);calls=0
                def mock(payload,timeout):
                    nonlocal calls
                    calls+=1
                    if mode=='transport' and calls==2:raise TimeoutError('local fixture')
                    r=self.response(payload,calls)
                    if mode=='pass' and calls==1:
                        value=json.loads(r['output'][0]['content'][0]['text']);value['status']='pass';r['output'][0]['content'][0]['text']=json.dumps(value)
                    if (mode=='bad_first' and calls==1) or (mode=='bad_second' and calls==2) or (mode=='two_bad' and calls<=2):r['output'][0]['content'][0]['text']='{'
                    if mode=='unknown_usage' and calls==2:r.pop('usage')
                    if mode=='overcap' and calls==2:r['usage']['output_tokens']=1537
                    return r
                if mode in ('two_bad','transport','unknown_usage','overcap'):
                    with self.assertRaises((ProtocolError,RuntimeError)):runner.run(p,o,transport=mock,local_validation=True)
                    self.assertEqual(calls,2)
                else:runner.run(p,o,transport=mock,local_validation=True)
                rows=io.read(o/'review.json')['rows'];self.assertEqual(len(rows),144)
                if mode=='pass':self.assertEqual(rows[1]['status'],'skipped_pass');self.assertEqual(calls,143)
                if mode=='bad_first':self.assertEqual(rows[1]['status'],'blocked_upstream');self.assertEqual(calls,143)
                if mode=='bad_second':self.assertEqual(rows[1]['status'],'quarantined');self.assertEqual(calls,144)
                self.assertEqual(len(io.read(o/'ANNOTATION_VIEWS.json')['views']),72)

    def test_gates_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'p';runner.freeze(p);sha=io.digest(p/'manifest.json')
            with self.assertRaises(FileNotFoundError):runner.gates(p)
            io.write(p/'PREFLIGHT.json',dict(status='passed',manifest_sha256=sha))
            io.write(p/'EXPERIMENT_REVIEW.json',dict(science='PASS',readiness='PASS',technical_launch='RUN_ALLOWED',manifest_sha256=sha))
            auth=dict(authorized=True,max_requests=144,max_output_tokens=221184,manifest_sha256=sha,destination='https://api.deepseek.com/responses',user_authorization_text='LOCAL TEST ONLY')
            io.write(p/'AUTHORIZATION.json',auth);runner.gates(p)
            io.write(p/'AUTHORIZATION.json',dict(auth,max_requests=72))
            with self.assertRaisesRegex(ValueError,'authorization'):runner.gates(p)
            (p/'contexts/rule-confirm-07/A1.json').write_text('{}',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'changed'):runner.verify(p)

    def test_long_first_and_annotation_faults_do_not_corrupt_protocol(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'p';o=Path(tmp)/'o';runner.freeze(p);calls=0
            text='A local basis. '*300
            def mock(payload,timeout):
                nonlocal calls
                calls+=1;r=self.response(payload,calls)
                if calls==1:
                    a=json.loads(r['output'][0]['content'][0]['text']);a.update(text=text,source_ids=['A2.S1',None],extra='preserve raw')
                    r['output'][0]['content'][0]['text']=json.dumps(a)
                if calls==2:
                    packet=json.loads(payload['instructions'].split('PACKET=',1)[1]);self.assertEqual(packet['earlier_work'],text)
                return r
            s=runner.run(p,o,transport=mock,local_validation=True)
            self.assertEqual(s['status'],'completed')
            self.assertTrue(s['rows'][0]['answer']['annotation_issues'])
            self.assertEqual(s['rows'][0]['answer']['evidence'],[])

if __name__=='__main__':unittest.main()
