import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
from jsonschema.exceptions import ValidationError

import candidate_transfer_probe as probe
from coreta.schemas import ProtocolError


class TransferProbeTests(unittest.TestCase):
    def setUp(self):
        self.source=probe.ROOT/'runs/candidate-transfer-tasks-prepared-20261025-r1'
        self.packets=[]

    def response(self,payload,timeout):
        p=json.loads(payload['instructions'].split('PACKET=',1)[1]);self.packets.append(p)
        if 'shared_contributions' not in p:
            s=p['own_sources'][0];field=next(iter(p['field_meanings']))
            answer=dict(text='Scripted new-task fixture only. '*12,
                facts=[dict(candidate=c['text'],field=field,value=None,source=s['ref'],quote=s['content'])
                       for c in p['task']['choices']],conditions=[dict(field=field,op='eq',value=True,
                       source='TASK',quote=p['task']['scenario'][-100:])],caveats=['Uncertain fixture. '*30],solution=None)
        else:answer=dict(reason='Scripted integration. '*100,artifact=p['task']['choices'][0]['text'])
        return dict(status='completed',usage=dict(input_tokens=100,output_tokens=100),
            output=[dict(type='message',content=[dict(type='output_text',text=json.dumps(answer))])])

    def allow_local_gate(self,p):
        digest=probe.sha(p/'manifest.json')
        probe.write(p/'PREFLIGHT.json',dict(status='passed',manifest_sha256=digest,fixture_only=True))
        probe.write(p/'EXPERIMENT_REVIEW.json',dict(science='PASS',readiness='PASS',decision='RUN_ALLOWED',
                                                  manifest_sha256=digest,fixture_only=True))

    def test_full_24_calls_native_four_and_isolated_labels(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'prepared';probe.prepare(self.source,p);self.allow_local_gate(p)
            original=probe.read
            def guarded(path):
                self.assertNotIn('offline',str(path))
                self.assertTrue(Path(path).is_relative_to(p) or Path(path).is_relative_to(root/'run'))
                return original(path)
            with patch.object(probe,'read',guarded):s=probe.run(p,root/'run',transport=self.response)
            self.assertEqual(s['attempts'],24)
            self.assertEqual(s['execution_mode'],'mock')
            grouped={}
            for row,packet in zip(s['completed'],self.packets,strict=True):
                private=probe.load_task(p,row['case'])[2]
                self.assertEqual(packet['own_sources'],private[row['owner']])
                if row['stage']=='EXTRACT':self.assertNotIn('shared_contributions',packet)
                else:
                    self.assertEqual(set(packet['shared_contributions']),set(probe.TEAM))
                    self.assertEqual(row['owner'],'A1' if row['repeat']==1 else 'A2')
                    self.assertIn(row['answer']['artifact'],[c['id'] for c in packet['task']['choices']])
                    grouped.setdefault((row['case'],row['repeat']),[]).append(
                        {k:v for k,v in packet.items() if k!='execution_report'})
            self.assertTrue(all(a==b for a,b in grouped.values()))
            probe.score(p,root/'run')
            self.assertEqual(len(probe.read(root/'run/offline_scores.json')['rows']),8)

    def test_dual_review_and_preflight_gates_before_requests(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'prepared';probe.prepare(self.source,p)
            with self.assertRaisesRegex(ValueError,'preflight'):probe.run(p,root/'blocked',transport=self.response)
            probe.write(p/'PREFLIGHT.json',dict(status='passed',manifest_sha256=probe.sha(p/'manifest.json')))
            with self.assertRaisesRegex(ValueError,'dual experiment review'):probe.run(p,root/'blocked',transport=self.response)
            self.assertFalse(self.packets)
            self.assertFalse((root/'blocked').exists())
            with self.assertRaisesRegex(ValueError,'mock transport'):probe.run(p,root/'blocked',local_validation=True)

    def test_partial_json_network_and_incomplete_stop_without_retry(self):
        for failure,offset in [('json',5),('transport',8),('incomplete',1)]:
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);p=root/'prepared';probe.prepare(self.source,p);calls=0
                def fail(payload,timeout):
                    nonlocal calls
                    calls+=1
                    if failure=='transport' and calls==offset:raise urllib.error.URLError('fixture')
                    r=self.response(payload,timeout)
                    if calls==offset:
                        if failure=='json':r['output'][0]['content'][0]['text']='{'
                        else:r['status']='incomplete'
                    return r
                with self.assertRaises((ValueError,ProtocolError)):
                    probe.run(p,root/'run',transport=fail,local_validation=True)
                state=probe.read(root/'run/progress.json')
                self.assertEqual(state['attempts'],offset);self.assertEqual(calls,offset)
                self.assertEqual(len(state['roster']),24)
                self.assertEqual(state['unknown_usage'],failure=='transport')
                probe.score(p,root/'run')
                rows=probe.read(root/'run/offline_scores.json')['rows']
                self.assertEqual(sum(r['correct'] is not None for r in rows),2 if failure=='transport' else 0)

    def test_native_three_option_contract_alias_and_nonempty_extra(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'prepared';probe.prepare(self.source,p)
            task=probe.load_task(p,probe.CASES[0])[0]
            display=task['choices'][0]['text']
            value=probe.decode(json.dumps(dict(reason='',artifact=display)),'INTEGRATE',task)
            self.assertEqual(value['artifact'],task['choices'][0]['id'])
            for artifact in ['option_4','unlisted']:
                with self.assertRaises(ValidationError):probe.decode(json.dumps(dict(reason='',artifact=artifact)),'INTEGRATE',task)

    def test_boolean_type_errors_stay_unknown_not_false_exclusions(self):
        public=[dict(ref='T',content='reachable required')]
        private={'A1':[dict(ref='S',content='candidate A') ]}
        outputs={'A1':dict(facts=[dict(candidate='A',field='reachable',value='false',source='S',quote='candidate A')],
            conditions=[dict(field='reachable',op='eq',value=True,source='T',quote='reachable required')])}
        result=probe.execute(['A'],public,private,outputs,allowed_fields=['reachable'],
            private_candidate_facts=True,public_conditions=True,boolean_fields=['reachable'])
        self.assertEqual(result['not_excluded'],['A'])
        self.assertEqual(result['candidate_checks'][0]['checks'][0]['status'],'unknown')

    def test_full_preflight_replays_real_and_native_mock_load(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'prepared';probe.prepare(self.source,p);r=probe.preflight(p)
            self.assertEqual(r['network_requests'],0)
            self.assertEqual(len(r['actual_historical_full_output_fixtures']),10)
            self.assertEqual(r['mock_callbacks'],24)
            self.assertLess(r['max_input_count'],r['input_limit'])


if __name__=='__main__':unittest.main()
