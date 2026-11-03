import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

import order_collaboration as experiment
from order_collaboration import ROOT, prepare, run, score, read


class CollaborationTests(unittest.TestCase):
    def response(self,payload,timeout):
        p=json.loads(payload['instructions'].split('PACKET=',1)[1])
        stage=p['stage']
        self.packets.append(p)
        if stage=='INIT':
            source=p['own_sources'][0]
            condition=dict(source=source['id'],quote=source['text'],expression=dict(op='before',a='J1',b='J2'))
            invalid=dict(source='not-owned',quote='invented',expression={})
            answer=dict(text='Scripted local simulation only.',conditions=[condition,invalid])
        elif stage=='REVIEW':
            source=p['own_sources'][0]
            # Unauthorized update must be logged as semantic rejection, not kill the batch.
            answer=dict(text='Review. '*180,applications=[],updates=[dict(condition='not-owned',
                source=source['id'],quote=source['text'],reason='Invalid reference probe.',withdraw=True,expression={})])
        else:
            answer=dict(reason='Long but structurally valid explanation. '*60,order=list(p['task']['jobs']))
            if stage=='FINAL':answer.update(retain_work='W1',exceptions={})
        return dict(status='completed',usage=dict(input_tokens=300,output_tokens=100),
            output=[dict(type='message',content=[dict(type='output_text',text=json.dumps(answer))])])

    def setUp(self):
        self.packets=[]
        self.pack=ROOT/'runs/distributed-order-tasks-prepared-20261024-r2'

    def test_full_18_calls_semantic_rejections_and_separate_gold_scoring(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'prepared';prepare(self.pack,p)
            original=experiment.read
            def guarded(path):
                self.assertNotIn('oracle',str(path))
                self.assertNotIn('reference',str(path))
                self.assertTrue(Path(path).is_relative_to(p) or Path(path).is_relative_to(root/'run'))
                return original(path)
            with patch.object(experiment,'read',guarded):
                result=run(p,root/'run',transport=self.response)
            self.assertEqual(result['attempts'],18)
            self.assertEqual(result['status'],'completed')
            self.assertTrue(all(r['status']=='completed' for r in result['roster']))
            review_outputs=[r['answer'] for r in result['completed'] if r['stage']=='REVIEW']
            self.assertTrue(all(r['updates'][0]['condition']=='not-owned' for r in review_outputs))
            for arm in ['A','B','C']:
                self.assertTrue(result['arm_states'][arm]['semantic_errors'])
                self.assertEqual(len(result['arm_states'][arm]['conditions']),3)
            for packet in self.packets:
                expected=read(p/f"{packet['member']}.json")['sources']
                self.assertEqual(packet['own_sources'],expected)
                if packet['stage']=='REVIEW':self.assertNotIn('shared_reviews',packet)
            score(root/'run')
            report=read(root/'run/offline_scores.json')
            self.assertEqual(len(report['arms']),3)
            self.assertTrue(all(r['final_score'] is not None for r in report['arms']))

    def test_malformed_json_stops_and_exports_uncompleted_not_wrong(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'prepared';prepare(self.pack,p)
            count=0
            def mock(payload,timeout):
                nonlocal count
                count+=1
                response=self.response(payload,timeout)
                if count==5:response['output'][0]['content'][0]['text']='{'
                return response
            with self.assertRaises(json.JSONDecodeError):run(p,root/'run',transport=mock)
            state=read(root/'run/progress.json')
            self.assertEqual(state['attempts'],5)
            self.assertEqual(state['roster'][4]['status'],'failed')
            self.assertEqual(sum(r['status']=='not_run' for r in state['roster']),13)
            score(root/'run')
            rows=read(root/'run/offline_scores.json')['arms']
            self.assertTrue(all(r['final_score'] is None for r in rows))
            self.assertIn('W0',rows[0]['raw_work_scores'])

    def test_transport_error_no_retry_preserves_completed_arm(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'prepared';prepare(self.pack,p)
            count=0
            def mock(payload,timeout):
                nonlocal count
                count+=1
                if count==10:raise urllib.error.URLError('scripted failure')
                return self.response(payload,timeout)
            with self.assertRaises(ValueError):run(p,root/'run',transport=mock)
            state=read(root/'run/progress.json')
            self.assertEqual(count,10)
            self.assertTrue(state['unknown_usage'])
            score(root/'run')
            rows=read(root/'run/offline_scores.json')['arms']
            self.assertIsNotNone(rows[0]['final_score'])
            self.assertIsNone(rows[1]['final_score'])
            self.assertIsNone(rows[2]['final_score'])

    def test_rotated_editor_and_arm_order_follow_frozen_schedule(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'prepared'
            prepare(self.pack,p,case='calibration-03',editor='A2',arm_order=('B','C','A'))
            result=run(p,root/'run',transport=self.response)
            builds=[r for r in result['completed'] if r['stage']=='BUILD']
            self.assertEqual([r['arm'] for r in builds],['B','C','A'])
            self.assertTrue(all(r['owner']=='A2' for r in builds))


if __name__=='__main__':unittest.main()
