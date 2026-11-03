import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import candidate_transfer_probe as probe
import prepare_candidate_screening as source


class ScreeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        cls.source=cls.root/'source'
        with patch.object(source,'exposure_audit',return_value={'hits':{},'test_fixture':True}):
            source.prepare(cls.source)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def response(self,payload,timeout):
        packet=json.loads(payload['instructions'].split('PACKET=',1)[1])
        if 'shared_contributions' not in packet:
            s=packet['own_sources'][0]
            answer=dict(text='Non-model test fixture.',facts=[dict(candidate=c['text'],
                field=next(iter(packet['field_meanings'])),value=None,source=s['ref'],quote=s['content'])
                for c in packet['task']['choices']],conditions=[],caveats=['Unknown, no invented requirement.'])
        else:answer=dict(reason='Non-model fixture.',artifact=packet['task']['choices'][0]['text'])
        return dict(status='completed',usage=dict(input_tokens=1,output_tokens=1),
                    output=[dict(type='message',content=[dict(type='output_text',text=json.dumps(answer))])])

    def test_dynamic_schedule_and_native_sources(self):
        m=probe.read(self.source/'SOURCE_MANIFEST.json')
        self.assertEqual([r['source_id'] for r in m['roster']],source.IDS)
        for r in m['roster']:
            folder=self.source/r['directory']
            for i in range(1,5):
                p=probe.read(folder/f'A{i}.json')
                self.assertEqual([s['ref'] for s in p['own_sources']],[f'S{i:02d}'])
                self.assertNotIn('correct_answer',p)
                self.assertEqual(len(p['task']['choices']),3)

    def test_full_preflight_120_and_34_real_responses(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'prepared';probe.prepare(self.source,p)
            result=probe.preflight(p)
            self.assertEqual(len(result['actual_historical_full_output_fixtures']),34)
            self.assertEqual(result['mock_callbacks'],120)
            self.assertTrue(result['execution_admission_checked'])
            self.assertEqual(len(result['task_scoped_legacy_extraction_audit']),80)
            self.assertEqual(sum(r['status']=='blocked_legacy_violation'
                for r in result['task_scoped_legacy_extraction_audit']),4)
            m=probe.read(p/'manifest.json')
            self.assertEqual(m['max_requests'],120)
            self.assertEqual(m['max_output_tokens'],368640)
            self.assertEqual(len(probe.read(p/'local_full_load/review.json')['rows']),40)
            self.assertLess(result['max_input_count'],32768)

    def test_late_failure_exports_all_rows_without_gold_reads(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'prepared';out=Path(temp)/'run';probe.prepare(self.source,p)
            calls=0;original=probe.read
            def guarded(path):
                self.assertNotIn('offline',str(path))
                return original(path)
            def transport(payload,timeout):
                nonlocal calls
                calls+=1
                response=self.response(payload,timeout)
                if calls==119:response['output'][0]['content'][0]['text']='{'
                return response
            with patch.object(probe,'read',guarded),self.assertRaises(ValueError):
                probe.run(p,out,transport=transport,local_validation=True)
            state=original(out/'progress.json')
            self.assertEqual(calls,119);self.assertEqual(state['attempts'],119)
            self.assertEqual(state['status'],'stopped');self.assertEqual(len(state['roster']),120)
            self.assertEqual(len(original(out/'review.json')['rows']),40)
            self.assertEqual(sum(r['status']=='not_completed' for r in original(out/'review.json')['rows']),2)
            self.assertEqual((out/'119.raw.txt').read_text(encoding='utf-8'),'{')


if __name__=='__main__':unittest.main()
