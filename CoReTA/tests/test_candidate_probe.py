import json
from pathlib import Path
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

from coreta.workboard.candidate_probe import execute
import candidate_probe_004 as probe


class CandidateTests(unittest.TestCase):
    def test_incomplete_response_and_transport_failure_stop_without_retry(self):
        for failure in ['incomplete','transport']:
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as temp:
                root=Path(temp);p=root/'prepared';probe.prepare(p);probe.preflight(p);self.packets=[]
                count=0
                def fail(payload,timeout):
                    nonlocal count
                    count+=1
                    if failure=='transport':raise urllib.error.URLError('scripted local failure')
                    value=self.mock(payload,timeout);value['status']='incomplete';return value
                from coreta.schemas import ProtocolError
                with self.assertRaises((ValueError,ProtocolError)):
                    probe.run(p,root/'run',transport=fail)
                state=probe.read(root/'run/progress.json')
                self.assertEqual(count,1)
                self.assertEqual(state['attempts'],1)
                self.assertEqual(state['status'],'stopped')
                self.assertEqual(state['unknown_usage'],failure=='transport')
                self.assertEqual(len(state['roster']),10)

    def test_preflight_required_and_bound_to_frozen_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'prepared';probe.prepare(p);self.packets=[]
            with self.assertRaisesRegex(ValueError,'preflight required'):
                probe.run(p,root/'blocked',transport=self.mock)
            self.assertFalse((root/'blocked').exists())
            result=probe.preflight(p)
            self.assertEqual(result['network_requests'],0)
            self.assertLess(result['max_input_count'],result['input_limit'])
            manifest=p/'manifest.json'
            manifest.write_text(manifest.read_text(encoding='utf-8')+' ',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'preflight required'):
                probe.run(p,root/'stale',transport=self.mock)
            self.assertFalse(self.packets)

    def test_numeric_json_representations_are_not_false_conflicts(self):
        output={'M':dict(facts=[dict(candidate='A',field='age',value=v,source='P',quote='age') for v in [17,17.0]],
            conditions=[dict(field='age',op='eq',value=17.0,source='S',quote='age')])}
        report=execute(['A'],[dict(ref='P',content='age')],{'M':[dict(ref='S',content='age')]},output)
        self.assertFalse(report['fact_conflicts'])
        self.assertEqual(report['candidate_checks'][0]['checks'][0]['status'],'consistent')

    def test_exact_name_alias_and_optional_null_not_nonempty_solution(self):
        public=[dict(ref='P',content='Person X is 17.')]
        private={'M':[dict(ref='S',content='Under thirty.')]}
        output={'M':dict(facts=[dict(candidate='Person X',field='age',value=17,source='P',quote='Person X is 17.')],
              conditions=[dict(field='age',op='lt',value=30,source='S',quote='Under thirty.')])}
        report=execute(['option_1'],public,private,output,candidate_aliases={'Person X':'option_1'})
        self.assertEqual(report['candidate_checks'][0]['checks'][0]['status'],'consistent')
        self.assertEqual(report['notices'][0]['kind'],'exact_candidate_alias')
        from jsonschema import validate,ValidationError
        valid=dict(text='',facts=[],conditions=[],caveats=[],solution=None)
        validate(valid,probe.schema('EXTRACT'))
        with self.assertRaises(ValidationError):validate({**valid,'solution':'option_1'},probe.schema('EXTRACT'))

    def test_unknown_conflicts_invalid_reference_and_no_semantic_certification(self):
        public=[dict(ref='P',content='A is 17. B is 53. They travelled together.')]
        private={'M':[dict(ref='S',content='The culprit is under thirty.') ]}
        output={'M':dict(facts=[dict(candidate='A',field='age',value=17,source='P',quote='A is 17.'),
            dict(candidate='B',field='age',value=53,source='P',quote='B is 53.')],
            conditions=[dict(field='age',op='lt',value=30,source='S',quote='under thirty')])}
        report=execute(['A','B'],public,private,output)
        self.assertEqual(report['not_excluded'],['A'])
        output['M']['facts'].append(dict(candidate='A',field='age',value=40,source='P',quote='They travelled together.'))
        report=execute(['A','B'],public,private,output)
        self.assertTrue(report['fact_conflicts'])
        self.assertEqual(report['candidate_checks'][0]['checks'][0]['status'],'unknown')
        self.assertEqual(report['not_excluded'],['A'])
        output['M']['conditions'][0]['source']='other-member'
        report=execute(['A','B'],public,private,output)
        self.assertEqual(report['not_excluded'],['A','B'])

    def mock(self,payload,timeout):
        p=json.loads(payload['instructions'].split('PACKET=',1)[1]);self.packets.append(p)
        if 'shared_contributions' not in p:
            answer=dict(text='Scripted extraction only.',facts=[],conditions=[],caveats=['No encoded knowledge in this mock.'])
        else:answer=dict(reason='Scripted integration only.',artifact='option_3')
        return dict(status='completed',usage=dict(input_tokens=100,output_tokens=100),
            output=[dict(type='message',content=[dict(type='output_text',text=json.dumps(answer))])])

    def test_ten_calls_private_extraction_matched_integration_no_gold_read(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'prepared';probe.prepare(p);probe.preflight(p);self.packets=[]
            original=probe.read
            def guarded(path):
                self.assertNotIn('offline',str(path))
                self.assertNotIn('SOURCE_MAPPING',str(path))
                self.assertTrue(Path(path).is_relative_to(p) or Path(path).is_relative_to(root/'run'))
                return original(path)
            with patch.object(probe,'read',guarded):state=probe.run(p,root/'run',transport=self.mock)
            self.assertEqual(state['attempts'],10)
            for row,packet in zip(state['completed'],self.packets,strict=True):
                self.assertEqual(packet['own_sources'],probe.read(p/(row['owner']+'.json')))
                if row['stage']=='EXTRACT':self.assertNotIn('shared_contributions',packet)
            for repeat in [1,2]:
                packets=[p for row,p in zip(state['completed'],self.packets) if row['stage']=='INTEGRATE' and row['repeat']==repeat]
                self.assertEqual({k:v for k,v in packets[0].items() if k!='execution_report'},
                                 {k:v for k,v in packets[1].items() if k!='execution_report'})
            probe.score(p,root/'run')
            self.assertEqual(len(probe.read(root/'run/offline_scores.json')['rows']),4)

    def test_first_format_failure_stops_and_partial_scores_remain_null(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'prepared';probe.prepare(p);probe.preflight(p);self.packets=[]
            count=0
            def fail(payload,timeout):
                nonlocal count
                count+=1;response=self.mock(payload,timeout)
                if count==4:response['output'][0]['content'][0]['text']='{'
                return response
            with self.assertRaises(ValueError):probe.run(p,root/'run',transport=fail)
            state=probe.read(root/'run/progress.json')
            self.assertEqual(state['attempts'],4)
            self.assertEqual(len(state['roster']),10)
            probe.score(p,root/'run')
            self.assertTrue(all(r['correct'] is None for r in probe.read(root/'run/offline_scores.json')['rows']))


if __name__=='__main__':unittest.main()
