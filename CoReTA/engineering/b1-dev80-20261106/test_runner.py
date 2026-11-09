"""No-model regression of extension isolation, durable recovery and no clocks."""
import copy,importlib.util,json,math,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location('dev80',HERE/'experiment.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def config():return dict(expert_actor='M1',seed=20261102,fixture=True,answer_tokens=256,answer_suffix='\n\nOutput ONLY the short answer.',output_contract='B1_LONG_WORK1024_V6',max_length=16384)
def tasks():return [dict(id=f'FIXTURE_{i}',question='When was X founded?',paragraphs=[dict(idx=0,title='X',paragraph_text='X was founded in 1900.')]) for i in range(4)]
class Backend:
    source_kind='FIXTURE_NOT_MODEL_EVIDENCE'
    def __init__(self,change=None):self.calls=[];self.change=change
    def respond_many(self,requests,remaining):
        assert math.isinf(remaining);self.calls.extend(copy.deepcopy(requests));rows=[]
        for r in requests:
            row=dict(raw_output='1900',status='OK',usage={})
            if self.change:self.change(r,row)
            rows.append(row)
        return rows

class ExtensionChecks(unittest.TestCase):
    def run_fixture(self,backend=None,length=lambda r:20,existing=None):
        b=backend or Backend();records=[];attempts=[]
        result=m.execute(config(),tasks(),range(4),b,lambda *x:records.append(x),lambda *x:attempts.append(x),length,existing)
        return result,b,records,attempts
    def test_all_four_arms_and_uniform_caps_no_wall_budget(self):
        ts,b,_,_=self.run_fixture();self.assertEqual(len(b.calls),208);self.assertTrue(all(t['complete'] for t in ts.values()))
        self.assertTrue(all(r['max_new_tokens']==(1024 if r['stage']=='work' else 256) for r in b.calls))
        for t in ts.values():self.assertEqual(m.replay(t).export(),t)
    def test_four_failures_same_item_do_not_stop_other_items(self):
        def fail(r,row):
            if r['request_id'].startswith('FIXTURE_0|') and r['stage']=='work':row['status']='OUTPUT_LIMIT'
        ts,b,_,_=self.run_fixture(Backend(fail));self.assertEqual(ts[0]['failed'],list('ABCD'));self.assertTrue(all(ts[i]['complete'] for i in (1,2,3)))
        self.assertEqual(len(ts[0]['records']),8)
    def test_three_distinct_truncations_are_not_global_timer_or_stop(self):
        def fail(r,row):
            if r['request_id'].endswith('|00') and not r['request_id'].startswith('FIXTURE_3|'):row['status']='OUTPUT_LIMIT'
        ts,_,_,_=self.run_fixture(Backend(fail));self.assertTrue(ts[3]['complete']);self.assertTrue(all(ts[i]['initial_failed'] for i in (0,1,2)))
    def test_initial_overlength_has_no_generation_and_other_items_finish(self):
        ts,b,records,_=self.run_fixture(length=lambda r:17000 if r['request_id']=='FIXTURE_0|00' else 20)
        self.assertEqual(ts[0]['records'][0]['status'],'INPUT_TOO_LONG');self.assertEqual(len(b.calls),156)
        self.assertFalse(records[0][-1]);self.assertTrue(all(ts[i]['complete'] for i in (1,2,3)))
    def test_work_overlength_isolates_only_arm(self):
        ts,_,_,_=self.run_fixture(length=lambda r:17000 if r['request_id']=='FIXTURE_0|04' else 20)
        self.assertEqual(ts[0]['failed'],['A']);self.assertEqual(len(ts[0]['records']),41)
        self.assertTrue(all(ts[i]['complete'] for i in (1,2,3)))
    def test_empty_and_nontext_are_real_failures_not_unknown(self):
        for value,status in [('  ','EMPTY_OUTPUT'),(None,'NON_TEXT_OUTPUT')]:
            def fail(r,row):
                if r['request_id']=='FIXTURE_0|00':row['raw_output']=value
            ts,_,_,_=self.run_fixture(Backend(fail));self.assertEqual(ts[0]['records'][0]['status'],status);self.assertTrue(ts[1]['complete'])
    def test_private_visibility_and_disclosure(self):
        _,b,_,_=self.run_fixture()
        for r in b.calls:
            text=r['payload']['user'];suffix=config()['answer_suffix'];text=text[:-len(suffix)] if text.endswith(suffix) else text
            d=json.loads(text.split('\n',1)[1])
            if r['stage']=='initial':self.assertNotIn('history',d);continue
            if r['arm'] in 'AC':self.assertTrue(all(x['sender']==r['actor'] for x in d['history']))
            self.assertEqual('team_information' in d,r['arm'] in 'CD')
    def test_resume_preserves_recorded_requests_without_regeneration(self):
        ts,_,_,_=self.run_fixture();existing={}
        for i in range(4):
            t=m.Trial(tasks()[i],**m.trial_parameters(config(),i))
            for q in ts[i]['records'][:9]:
                r=t.next_request();t.submit(r['request_id'],q['raw_output'],status=q['status'],usage=q['usage'],source_kind=q['source_kind'])
            existing[i]=t.export()
        actual,b,_,_=self.run_fixture(existing=existing);self.assertEqual(actual,ts);self.assertEqual(len(b.calls),208-36)
    def test_recover_unconfirmed_attempt_without_retry_and_journal_wins_trace(self):
        previous=m.OUT
        try:
            with tempfile.TemporaryDirectory() as folder:
                m.OUT=Path(folder);m.atomic(m.OUT/'config.json',config());m.atomic(m.OUT/'INPUTS.json',dict(tasks=tasks()))
                cell=m.OUT/'cells/000';cell.mkdir(parents=True)
                t=m.Trial(tasks()[0],**m.trial_parameters(config(),0));r=t.next_request();q=t.submit(r['request_id'],'1900',source_kind='ACTUAL_LOCAL_MODEL_RESPONSE',usage={})
                m.append(cell/'responses.jsonl',dict(item_index=0,record=q,batch_size=2,position=0,generated=True))
                m.append(cell/'ATTEMPTS.jsonl',dict(requests=[[0,'FIXTURE_0|00'],[1,'FIXTURE_1|00']],position=0))
                recovered=m.recover(0);self.assertEqual(recovered[0]['records'][0],q)
                self.assertEqual(recovered[1]['records'][0]['status'],'INTERRUPTED_UNCONFIRMED')
                self.assertTrue(recovered[1]['initial_failed']);self.assertEqual(len(m.lines(cell/'responses.jsonl')),2)
                self.assertEqual(m.recover(0),recovered)
        finally:m.OUT=previous
    def test_original_v6_scheduler_same_prompt_seed_and_full_export(self):
        c=config();ts,b,_,_=self.run_fixture();base=Backend();base.remaining=lambda:1e9
        respond=base.respond_many;base.respond_many=lambda requests,remaining:respond(requests,math.inf)
        old=m.old.execute(c,tasks(),range(4),base,'batch2',lambda *_:None,lambda *_:None)
        self.assertEqual(old,ts);self.assertEqual(base.calls,b.calls)

if __name__=='__main__':unittest.main()
