from pathlib import Path
import tempfile
import unittest
from prepare_candidate_transfer_tasks import prepare
from order_calibration import read
from coreta.workboard.candidate_probe import execute


class TransferTests(unittest.TestCase):
    def test_native_four_member_packets_no_gold_or_other_originals(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'pack';prepare(root)
            roster=read(root/'SOURCE_MANIFEST.json')['roster']
            self.assertEqual([r['source_id'] for r in roster],[9,12])
            for row in roster:
                self.assertEqual(row['members'],4)
                folder=root/row['directory']
                for i in range(1,5):
                    packet=read(folder/f'A{i}.json')
                    self.assertEqual([s['ref'] for s in packet['own_sources']],[f'S{i:02d}'])
                    self.assertNotIn('correct_answer',packet)
                    self.assertNotIn('label',packet)
                    self.assertEqual(set(packet),{'member','task','public_sources','own_sources'})
                label=read(folder/'offline/label.json')
                self.assertEqual(next(c['text'] for c in read(folder/'task.json')['choices']
                    if c['id']==label['correct_option_id']),label['official_correct_text'])

    def test_private_named_fact_and_public_requirement_without_other_source_access(self):
        public=[dict(ref='TASK',content='The destination must be reachable.')]
        private={'A1':[dict(ref='S1',content='B is unreachable.')],
                 'A2':[dict(ref='S2',content='A is reachable.') ]}
        outputs={'A1':dict(facts=[dict(candidate='B',field='reachable',value=False,source='S1',quote='B is unreachable.'),
            dict(candidate='A',field='reachable',value=True,source='S2',quote='A is reachable.')],
            conditions=[dict(field='reachable',op='eq',value=True,source='TASK',quote='must be reachable')])}
        kwargs=dict(allowed_fields=['reachable'],private_candidate_facts=True,public_conditions=True)
        report=execute(['A','B'],public,private,outputs,**kwargs)
        self.assertEqual(report['not_excluded'],['A'])
        self.assertTrue(any(n['kind']=='rejected_fact' for n in report['notices']))
        self.assertNotIn('A',report['model_fact_table'])
        # Original 004 permissions remain narrow by default.
        original=execute(['A','B'],public,private,outputs)
        self.assertEqual(original['not_excluded'],['A','B'])


if __name__=='__main__':unittest.main()
