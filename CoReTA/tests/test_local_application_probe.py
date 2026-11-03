import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from jsonschema.exceptions import ValidationError
from coreta.schemas import ProtocolError
import local_application_probe as probe


class LocalApplicationTests(unittest.TestCase):
    def mock(self,payload,timeout):
        packet=json.loads(payload['instructions'].split('PACKET=',1)[1])
        if 'member' in packet and 'shared_contributions' not in packet:
            src=packet['own_sources'][0]
            answer=dict(text='Technical fixture.',facts=[dict(candidate=packet['task']['choices'][0]['text'],
                field=next(iter(packet['field_meanings'])),value=None,source=src['ref'],quote=src['content'])],
                conditions=[],caveats=[],revision=dict(reason=None,artifact=None),solution=None)
        else:answer=dict(reason='Technical fixture.',artifact=packet['task']['choices'][0]['text'])
        return dict(status='completed',usage=dict(input_tokens=10,output_tokens=10),
            output=[dict(type='message',content=[dict(type='output_text',text=json.dumps(answer))])])

    def test_full_70_calls_isolation_no_gold_and_diagnostic_separate(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'prepared';out=Path(temp)/'run';probe.prepare(p);original=probe.read
            def guarded(path):
                self.assertNotIn('offline_labels',str(path));return original(path)
            with patch.object(probe,'read',guarded):s=probe.run(p,out,transport=self.mock,local_validation=True)
            self.assertEqual(s['attempts'],70)
            self.assertEqual(sum(r['stage']=='CONTRIBUTE' for r in s['completed']),48)
            self.assertEqual(sum(r['stage']=='INTEGRATE' for r in s['completed']),16)
            self.assertEqual(sum(r['stage']=='FULL' for r in s['completed']),6)
            probe.score(p,out)
            self.assertEqual(len(probe.read(out/'offline_scores.json')['rows']),22)

    def test_gate_and_manifest_staleness(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'prepared';probe.prepare(p)
            with self.assertRaisesRegex(ValueError,'fresh dual'):probe.run(p,Path(temp)/'blocked',transport=self.mock)
            probe.write(p/'PREFLIGHT.json',dict(status='passed',manifest_sha256=probe.sha(p/'manifest.json')))
            with self.assertRaisesRegex(ValueError,'fresh dual'):probe.run(p,Path(temp)/'blocked2',transport=self.mock)
            with self.assertRaisesRegex(ValueError,'requires mock'):probe.run(p,Path(temp)/'blocked3',local_validation=True)
            (p/'unit-01/W0.json').write_text('{}',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'frozen input'):probe.verify(p)

    def test_shared_schema_null_noop_alias_and_invalid_revision(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'prepared';probe.prepare(p);row=probe.schedule()[0];packet=probe.packet_for(p,row,[])
            answer=dict(text='No supported change.',facts=[],conditions=[],caveats=[],solution=None)
            for revision in [None,dict(reason=None,artifact=None)]:
                value=copy.deepcopy(answer);value['revision']=revision
                decoded,_=probe.decode(json.dumps(value),'CONTRIBUTE',packet)
                self.assertEqual(probe.materialize(packet['W0'],{'A2':decoded}),[])
            choice=packet['task']['choices'][0]
            value=dict(answer,revision=dict(reason='Actual replacement.',artifact=choice['text']))
            decoded,_=probe.decode(json.dumps(value),'CONTRIBUTE',packet)
            self.assertEqual(decoded['revision']['artifact'],choice['id'])
            self.assertEqual(probe.materialize(packet['W0'],{'A2':decoded})[0]['after']['reason'],'Actual replacement.')
            for revision in [dict(reason=None,artifact='option_4'),dict(reason='x'),dict(reason=None,artifact=None,extra=True)]:
                with self.assertRaises(ValidationError):probe.decode(json.dumps(dict(answer,revision=revision)),'CONTRIBUTE',packet)
            row2=dict(row,method='applied')
            self.assertEqual(probe.schema('CONTRIBUTE',packet),probe.schema('CONTRIBUTE',probe.packet_for(p,row2,[])))
            self.assertNotEqual(probe.prompt(row,packet),probe.prompt(row2,packet))

    def test_partial_json_incomplete_transport_stop_and_export(self):
        for mode,offset in [('json',12),('incomplete',1),('transport',9)]:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temp:
                p=Path(temp)/'prepared';out=Path(temp)/'run';probe.prepare(p);calls=0
                def fail(payload,timeout):
                    nonlocal calls
                    calls+=1
                    if calls==offset and mode=='transport':raise TimeoutError('fixture')
                    response=self.mock(payload,timeout)
                    if calls==offset:
                        if mode=='json':response['output'][0]['content'][0]['text']='{'
                        else:response['status']='incomplete'
                    return response
                with self.assertRaises((ValueError,ProtocolError)):probe.run(p,out,transport=fail,local_validation=True)
                s=probe.read(out/'progress.json')
                self.assertEqual(calls,offset);self.assertEqual(s['attempts'],offset)
                self.assertEqual(s['status'],'stopped');self.assertEqual(len(s['roster']),70)
                self.assertEqual(len(probe.read(out/'review.json')['rows']),22)
                if mode=='json':self.assertEqual((out/f'{offset:02d}.raw.txt').read_text(encoding='utf-8'),'{')

    def test_full_preflight_with_real_history_and_long_new_shape(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'prepared';probe.prepare(p);r=probe.preflight(p)
            self.assertEqual(r['mock_callbacks'],70)
            self.assertEqual(r['known_legacy_violations'],4)
            self.assertEqual(len(probe.read(p/'PREFLIGHT.json')['real_historical_outputs']),120)
            self.assertLessEqual(r['maximum_mock_output_tokens'],3072)
            self.assertLess(r['maximum_input_estimate'],32768)


if __name__=='__main__':unittest.main()
