"""Contract failure propagation, visibility and version separation; no model data."""
import sys,unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from b1_controls import Trial,replay,summarize,score_trial
from b1_output_contract import VERSION,READABLE_VERSION
from test_b1_controls import task,finish

def trial():return Trial(task(),expert_actor='M1',fixture=True,answer_tokens=128,output_contract=VERSION)

class ConciseChecks(unittest.TestCase):
    def test_readable_word_warning_keeps_raw_text_and_all_dependencies(self):
        t=Trial(task(),expert_actor='M1',fixture=True,answer_tokens=128,output_contract=READABLE_VERSION)
        r=t.next_request();raw='word '*28;rec=t.submit(r['request_id'],raw)
        self.assertEqual(rec['status'],'OK');self.assertEqual(rec['raw_output'],raw)
        self.assertEqual(rec['usage']['format_warning'],'WORD_LIMIT')
        finish(t);self.assertTrue(t.complete);self.assertEqual(len(t.records),52)
        self.assertEqual(replay(t.export()).export(),t.export())

    def test_readable_empty_text_still_blocks_and_prompts_are_identical(self):
        v4=trial();v5=Trial(task(),expert_actor='M1',fixture=True,answer_tokens=128,output_contract=READABLE_VERSION)
        self.assertEqual(v4.next_request()['payload'],v5.next_request()['payload'])
        rec=v5.submit(v5.next_request()['request_id'],' ')
        self.assertEqual(rec['status'],'FORMAT_VIOLATION');self.assertIsNone(v5.next_request())

    def test_readable_cannot_be_pooled_with_strict_contract(self):
        a=finish(trial()).export()
        b=finish(Trial(dict(task(),id='SECOND'),expert_actor='M1',fixture=True,answer_tokens=128,output_contract=READABLE_VERSION)).export()
        targets={i:dict(id=i,answer='1900') for i in ('HOST_FIXTURE','SECOND')}
        with self.assertRaisesRegex(ValueError,'mixed_batch_conditions'):
            summarize([a,b],targets,list(targets),{i:i for i in targets})

    def test_complete_visibility_and_paired_seeds(self):
        t=finish(trial());self.assertTrue(t.complete);self.assertEqual(len(t.records),52)
        for r in t.records:
            text=r['payload']['user'].split('TASK_DATA\n')[1].split('\n\nOUTPUT FORMAT:')[0]
            data=json.loads(text)
            self.assertEqual(r['max_new_tokens'],768 if r['stage']=='work' else 128)
            self.assertIn('OUTPUT FORMAT:',r['payload']['user'])
            if r['stage']!='initial':
                self.assertEqual('team_information' in data,r['arm'] in 'CD')
                self.assertTrue(all(h['phase']!='final' for h in data['history']))
                if r['arm'] in 'AC':self.assertTrue(all(h['sender']==r['actor'] for h in data['history']))
        self.assertEqual(replay(t.export()).export(),t.export())
        for a,b in [('A','B'),('C','D')]:
            rs=lambda arm:[(r['actor'],r['round'],r['seed']) for r in t.records if r['stage']=='work' and r['arm']==arm]
            self.assertEqual(rs(a),rs(b))

    def test_initial_format_failure_never_starts_dependents(self):
        t=trial();r=t.next_request();rec=t.submit(r['request_id'],'word '*13,usage={'finish_reason':'EOS'})
        self.assertEqual(rec['status'],'FORMAT_VIOLATION');self.assertEqual(rec['usage']['finish_reason'],'EOS')
        self.assertIsNone(t.next_request());self.assertFalse(t.complete)

    def test_work_failure_isolated_to_that_arm_and_replayable(self):
        t=trial()
        for _ in range(4):r=t.next_request();t.submit(r['request_id'],'1900')
        r=t.next_request();self.assertEqual(r['arm'],'A');t.submit(r['request_id'],'word '*121)
        finish(t)
        self.assertEqual(t.failed,{'A'});self.assertEqual(set(t.finals['B']),{'M1','M2','M3','M4'})
        self.assertEqual(replay(t.export()).export(),t.export())

    def test_natural_answer_and_technical_failure_are_distinct(self):
        t=trial();r=t.next_request();rec=t.submit(r['request_id'],'Unknown')
        self.assertEqual(rec['status'],'OK')
        r=t.next_request();rec=t.submit(r['request_id'],'word '*20,status='OUTPUT_LIMIT')
        self.assertEqual(rec['status'],'OUTPUT_LIMIT')
        t=trial();r=t.next_request();rec=t.submit(r['request_id'],'1900\n1901')
        self.assertEqual(rec['status'],'FORMAT_VIOLATION')

    def test_mixed_contract_cannot_be_reported_as_one_batch(self):
        a=finish(Trial(task(),expert_actor='M1',fixture=True)).export()
        b=finish(Trial(dict(task(),id='SECOND'),expert_actor='M1',fixture=True,answer_tokens=128,output_contract=VERSION)).export()
        targets={i:dict(id=i,answer='1900') for i in ('HOST_FIXTURE','SECOND')}
        with self.assertRaisesRegex(ValueError,'mixed_batch_conditions'):
            summarize([a,b],targets,list(targets),{i:i for i in targets})

if __name__=='__main__':unittest.main()
