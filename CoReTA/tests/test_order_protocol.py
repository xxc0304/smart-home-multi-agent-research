import copy
import json
import unittest
from pathlib import Path
from coreta.workboard.order_protocol import OrderBoard, simulate_episode


TASK = dict(id='local-fixture', jobs={j:dict(duration=1) for j in 'XYZ'})
SOURCES = {'A1':[dict(id='S1',text='X precedes Y. PRIVATE_ONE')],
           'A2':[dict(id='S2',text='Y is not first. PRIVATE_TWO')],
           'A3':[dict(id='S3',text='Z ends by three. PRIVATE_THREE')]}


def board():
    b=OrderBoard(TASK,SOURCES)
    b.contribute('A1','ordering constraint',[dict(source='S1',quote='X precedes Y.',
                 expression=dict(op='before',a='X',b='Y'))])
    return b


class ProtocolTests(unittest.TestCase):
    def test_real_archived_job_field_gets_diagnostic_and_explicit_owner_repair(self):
        root=Path(__file__).resolve().parents[1]
        prepared=root/'runs/order-collaboration-prepared-20261024-r1'
        archived=json.loads((root/'runs/order-collaboration-live-20261024-r1/progress.json').read_text(encoding='utf-8'))
        task=json.loads((prepared/'task.json').read_text(encoding='utf-8'))
        sources={a:json.loads((prepared/f'{a}.json').read_text(encoding='utf-8'))['sources']
                 for a in ['A1','A2','A3']}
        b=OrderBoard(task,sources)
        for row in archived['completed']:
            if row['stage']=='INIT':b.contribute(row['owner'],row['answer']['text'],row['answer']['conditions'])
        b.put_work('W0','A1',dict(order=['J6','J5','J4','J1','J2','J3']))
        before=b.check('W0');bad=before['checks'][0]
        self.assertEqual(bad['status'],'unknown')
        self.assertEqual(bad['diagnostic']['reason'],'field_mismatch')
        self.assertEqual(bad['diagnostic']['missing_fields'],['a'])
        self.assertEqual(bad['diagnostic']['unexpected_fields'],['job'])
        self.assertIn('job',b.conditions['A1.C1']['expression'])
        self.assertEqual(b.packet('A1','B','REVIEW',before)['execution_report'],
                         b.packet('A1','C','REVIEW',before)['execution_report'])
        c=b.conditions['A1.C1']
        b.revise_round({'A1':dict(updates=[dict(condition=c['id'],source=c['source'],quote=c['quote'],
            reason='Repair invalid field using the supplied compiler diagnostic.',withdraw=False,
            expression=dict(op='deadline',a='J6',value=13))])})
        after=b.check('W0')
        self.assertEqual(after['checks'][0]['status'],'consistent')
        self.assertIsNone(after['checks'][0]['diagnostic'])
        self.assertEqual(b.history[0]['old']['expression']['job'],'J6')
        with self.assertRaises(ValueError):b.packet('A1','C','FINAL',before)

    def test_diagnostic_does_not_certify_semantic_truth(self):
        b=board()
        self.assertIsNone(b.diagnose_expression(dict(op='deadline',a='X',value=0)))
        self.assertEqual(b.diagnose_expression(dict(op='deadline',a='X',value=True))['reason'],
                         'expected_nonnegative_integer')

    def test_private_sources_and_legal_shared_excerpt(self):
        b=board();p=b.packet('A2','B','BUILD');raw=json.dumps(p)
        self.assertIn('PRIVATE_TWO',raw)
        self.assertNotIn('PRIVATE_ONE',raw);self.assertNotIn('PRIVATE_THREE',raw)
        self.assertIn('X precedes Y.',raw)
        p['own_sources'].clear()
        self.assertEqual(len(b.sources['A2']),1)

    def test_owner_and_quote_checked_before_sharing(self):
        b=board()
        with self.assertRaises(ValueError):
            b.contribute('A2','bad',[dict(source='S1',quote='X precedes Y.',expression={})])
        with self.assertRaises(ValueError):
            b.revise_round({'A2':dict(updates=[dict(condition='A1.C1',source='S2',
                quote='Y is not first.',reason='change',withdraw=True)])})
        self.assertTrue(b.conditions['A1.C1']['active'])

    def test_revision_rechecks_same_work_and_preserves_history(self):
        b=board();b.put_work('W0','A1',dict(order=['Y','X','Z']))
        old=b.check('W0')
        b.revise_round({'A1':dict(updates=[dict(condition='A1.C1',source='S1',quote='X precedes Y.',
            reason='Diagnostic reversed interpretation; not semantically certified.',
            expression=dict(op='before',a='Y',b='X'))])})
        new=b.check('W0')
        self.assertEqual(old['checks'][0]['status'],'violates')
        self.assertEqual(new['checks'][0]['status'],'consistent')
        self.assertNotEqual(old['condition_snapshot'],new['condition_snapshot'])
        self.assertEqual(b.history[0]['old']['expression']['a'],'X')
        with self.assertRaises(ValueError):
            b.packet('A1','C','FINAL',old)

    def test_same_tool_feedback_for_b_c(self):
        b=board();b.put_work('W0','A1',dict(order=['Y','X','Z']))
        report=b.check('W0')
        self.assertEqual(b.packet('A1','B','REVIEW',report)['execution_report'],
                         b.packet('A1','C','REVIEW',report)['execution_report'])
        self.assertNotIn('execution_report',b.packet('A1','A','REVIEW',report))

    def test_new_violation_default_retains_old_c_b_submits(self):
        b=board();b.put_work('W0','A1',dict(order=['X','Y','Z']))
        b.put_work('W1','A1',dict(order=['Y','X','Z']))
        self.assertEqual(b.select('C',{})['selected'],'W0')
        self.assertEqual(b.select('B',{})['selected'],'W1')
        self.assertEqual(b.select('C',{})['raw_works']['W1']['order'],['Y','X','Z'])

    def test_repair_promoted_and_acknowledgment_does_not_clear_conflict(self):
        b=board();b.put_work('W0','A1',dict(order=['Y','X','Z']))
        b.revise_round({'A1':dict(text='I accept the suggestion.')})
        self.assertEqual(b.check('W0')['checks'][0]['status'],'violates')
        b.put_work('W1','A1',dict(order=['X','Y','Z']))
        self.assertEqual(b.select('C',{})['selected'],'W1')

    def test_wrong_condition_can_block_correct_repair_and_explicit_exception(self):
        b=board()
        # A source-faithfulness error, deliberately not corrected by the host.
        b.conditions['A1.C1']['expression']=dict(op='before',a='Y',b='X')
        b.put_work('W0','A1',dict(order=['Y','X','Z']))
        b.put_work('W1','A1',dict(order=['X','Y','Z']))
        self.assertEqual(b.select('C',{})['selected'],'W0')
        result=b.select('C',dict(exceptions={'A1.C1':'The quoted source says X precedes Y.'}))
        self.assertEqual(result['selected'],'W1')
        self.assertEqual(result['status'],'unresolved')

    def test_illegal_order_cannot_override(self):
        b=board();b.put_work('W0','A1',dict(order=['X','Y','Z']))
        b.put_work('W1','A1',dict(order=['X','X','Z']))
        result=b.select('C',dict(exceptions={'A1.C1':'Override.'}))
        self.assertEqual(result['selected'],'W0')

    def test_unknown_expression_not_executed(self):
        b=board();b.conditions['A1.C1']['expression']=dict(op='exec',code='raise RuntimeError')
        b.put_work('W0','A1',dict(order=['X','Y','Z']))
        self.assertEqual(b.check('W0')['checks'][0]['status'],'unknown')
        b.conditions['A1.C1']['expression']=dict(op=['bad'],a=['bad'])
        self.assertEqual(b.check('W0')['checks'][0]['status'],'unknown')

    def test_complete_simulation_18_calls_independent_reviews(self):
        calls=[]
        def callback(stage,owner,arm,packet):
            calls.append(dict(stage=stage,owner=owner,arm=arm,packet=copy.deepcopy(packet)))
            if stage=='INIT':
                self.assertEqual(packet['shared_contributions'],[])
                if owner=='A1':
                    return dict(text='Ordering.',conditions=[dict(source='S1',quote='X precedes Y.',
                        expression=dict(op='before',a='X',b='Y'))])
                return dict(text='No encoded condition.',conditions=[])
            if stage in {'BUILD','FINAL'}:
                return dict(reason='Long explanation. '*200,order=['X','Y','Z'] if stage=='BUILD' else ['Y','X','Z'])
            self.assertNotIn('shared_reviews',packet)
            return dict(text='Review without semantic oracle.',updates=[])
        result=simulate_episode(TASK,SOURCES,'A1',callback)
        self.assertEqual(len(calls),18)
        self.assertEqual(result['A']['selection']['selected'],'W1')
        self.assertEqual(result['B']['selection']['selected'],'W1')
        self.assertEqual(result['C']['selection']['selected'],'W0')
        reports={r['arm']:r['packet']['execution_report'] for r in calls
                 if r['stage']=='REVIEW' and r['owner']=='A1' and r['arm']!='A'}
        self.assertEqual(reports['B'],reports['C'])


if __name__=='__main__':unittest.main()
