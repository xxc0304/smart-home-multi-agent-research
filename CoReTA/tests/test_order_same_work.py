from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import order_collaboration as runtime
from order_collaboration import read,run,score
from prepare_order_same_work import prepare
import test_order_collaboration as fixtures


class SameWorkTests(unittest.TestCase):
    def test_replay_12_calls_same_work_private_review_and_label_isolation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);prepared=root/'prepared';prepare(prepared)
            plan=read(prepared/'PLAN.json');labels=read(prepared/'offline_labels.json')
            self.assertEqual(len(plan['units']),4)
            self.assertEqual(sum(r['initial_correct'] for r in labels.values()),2)
            self.assertEqual([(v['episode'],v['source_arm']) for v in labels.values()],
                [('episode-03','A'),('episode-03','B'),('episode-04','B'),('episode-04','A')])
            (prepared/'offline_labels.json').unlink()
            fixture=fixtures.CollaborationTests();fixture.setUp()
            unit=prepared/'draft-01';original_read=runtime.read
            def guarded(path):
                self.assertNotIn('offline',str(path))
                self.assertNotIn('oracle',str(path))
                self.assertTrue(Path(path).is_relative_to(unit) or Path(path).is_relative_to(root/'run'))
                return original_read(path)
            with patch.object(runtime,'read',guarded):
                result=run(unit,root/'run',transport=fixture.response)
            self.assertEqual(result['attempts'],12)
            self.assertTrue(all(r['stage'] in {'REVIEW','FINAL'} for r in result['completed']))
            packets={}
            for p in fixture.packets:
                self.assertNotIn('initial_correct',str(p))
                self.assertEqual(p['own_sources'],read(unit/(p['member']+'.json'))['sources'])
                if p['stage']=='REVIEW':
                    self.assertNotIn('shared_reviews',p)
                    base={k:v for k,v in p.items() if k not in {'execution_report','application_links'}}
                    packets.setdefault(p['member'],[]).append(base)
            self.assertTrue(all(a==b==c for a,b,c in packets.values()))
            score(root/'run')
            self.assertTrue(all(r['final_score'] is not None for r in read(root/'run/offline_scores.json')['arms']))

    def test_same_work_replay_failure_has_12_entry_roster(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);prepare(root/'prepared')
            fixture=fixtures.CollaborationTests();fixture.setUp()
            count=0
            def mock(payload,timeout):
                nonlocal count
                count+=1
                value=fixture.response(payload,timeout)
                if count==5:value['output'][0]['content'][0]['text']='{'
                return value
            with self.assertRaises(ValueError):
                run(root/'prepared/draft-01',root/'run',transport=mock)
            state=read(root/'run/progress.json')
            self.assertEqual(state['attempts'],5)
            self.assertEqual(len(state['roster']),12)
            score(root/'run')
            rows=read(root/'run/offline_scores.json')['arms']
            self.assertIsNotNone(rows[0]['final_score'])
            self.assertIsNone(rows[1]['final_score'])


if __name__=='__main__':unittest.main()
