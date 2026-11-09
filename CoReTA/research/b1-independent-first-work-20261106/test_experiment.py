"""Protocol regression against actual full histories, plus dependency failures."""
import contextlib,copy,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import experiment as m

class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack=m.load(m.HERE/'INPUTS.json');cls.c=m.load(m.SOURCE/'config.json')

    def entry(self,i):return next(e for e in self.pack['tasks'] if e['index']==i)

    def initials(self,e,rep=0):
        old=m.load(m.ROOT/e['source_path']);t=m.Trial(e['task'],**m.options(self.c,e,rep));recs=[]
        for x in [r for r in old['records'] if r['stage']=='initial']:
            r=m.initial_request(t,rep);recs.append(t.submit(r['request_id'],x['raw_output'],usage=x['usage'],source_kind='ACTUAL_LOCAL_MODEL_RESPONSE'))
        return recs

    def test_frozen_selection_and_deduplicated_overlap(self):
        m.verify_pack(self.pack)
        self.assertEqual(len(self.pack['tasks']),25)
        self.assertEqual(len(set(self.pack['coverage_indices'])&set(self.pack['mechanism_indices'])),7)
        review=m.load(m.HERE/'SELECTION_REVIEW.json')['reviewed']
        self.assertEqual(len(review),41);self.assertEqual(sum(not r['eligible'] for r in review),17)

    def test_all_original_arm_inputs_and_seeds_exact_replay(self):
        for e in self.pack['tasks']:
            old=m.load(m.ROOT/e['source_path'])
            for arm in ('A','B','C','D'):
                b=m.Branch(e,self.c,0,arm,self.initials(e))
                for x in [r for r in old['records'] if r['arm']==arm]:
                    r=b.next_request()
                    for key in ('payload','actor','arm','stage','round','seed','max_new_tokens'):self.assertEqual(r[key],x[key])
                    b.submit(r['request_id'],x['raw_output'],status=x['status'],usage=x['usage'],source_kind=x['source_kind'])
                self.assertIsNone(b.next_request())

    def test_only_one_work_input_changed_and_full_visibility_restored(self):
        changed=0;max_removed=0
        for e in self.pack['tasks']:
            old=m.load(m.ROOT/e['source_path']);b=m.Branch(e,self.c,0,'B_delay',self.initials(e))
            for x in [r for r in old['records'] if r['arm']=='B']:
                r=b.next_request();altered=r['actor']=='M1' and r['stage']=='work' and r['round']==1
                if altered:
                    changed+=1;before=m.decode(x);after=m.decode(r);max_removed=max(max_removed,len(before['history'])-len(after['history']))
                    self.assertEqual(after['history'],[q for q in before['history'] if q['sender']=='M1'])
                    self.assertEqual({k:v for k,v in before.items() if k!='history'},{k:v for k,v in after.items() if k!='history'})
                    self.assertEqual(r['payload']['system'],x['payload']['system'])
                else:self.assertEqual(r['payload'],x['payload'])
                b.submit(r['request_id'],x['raw_output'],status=x['status'],usage=x['usage'],source_kind=x['source_kind'])
            self.assertTrue(b.complete)
        self.assertEqual(changed,25);self.assertGreater(max_removed,3)

    def test_changed_real_message_propagates_all_downstream_without_mutating_control(self):
        e=self.entry(26);old=m.load(m.ROOT/e['source_path']);recs=self.initials(e)
        b=m.Branch(e,self.c,0,'B_delay',recs);control=m.Branch(e,self.c,0,'B',recs);seen=False;later=0
        for x in [r for r in old['records'] if r['arm']=='B']:
            r=b.next_request();rc=control.next_request()
            if seen:
                self.assertIn('COUNTERFACTUAL_PROTOCOL_TEST_ONLY',r['payload']['user']);self.assertNotIn('COUNTERFACTUAL_PROTOCOL_TEST_ONLY',rc['payload']['user']);later+=1
            raw=x['raw_output']
            if r['actor']=='M1' and r['stage']=='work' and r['round']==1:
                raw+=' COUNTERFACTUAL_PROTOCOL_TEST_ONLY';seen=True
            b.submit(r['request_id'],raw,usage=x['usage'],source_kind=x['source_kind'])
            control.submit(rc['request_id'],x['raw_output'],usage=x['usage'],source_kind=x['source_kind'])
        self.assertGreater(later,4)

    def test_no_final_answers_broadcast_or_gold_in_payload(self):
        for e in self.pack['tasks']:
            old=m.load(m.ROOT/e['source_path']);b=m.Branch(e,self.c,0,'B_delay',self.initials(e))
            for x in [r for r in old['records'] if r['arm']=='B']:
                r=b.next_request();d=m.decode(r,self.c['answer_suffix'] if r['stage']=='final' else '')
                self.assertFalse({'target','answer','answer_aliases','question_decomposition','quality_note','mechanism_reason','is_supporting'}&set(d))
                self.assertFalse(any(z['phase']=='final' for z in d['history']))
                self.assertEqual(d['paragraphs'],e['task']['paragraphs'])
                self.assertFalse(any('is_supporting' in p for p in d['paragraphs']))
                b.submit(r['request_id'],x['raw_output'],status=x['status'],usage=x['usage'],source_kind=x['source_kind'])

    def test_two_seed_offsets_match_all_five_conditions(self):
        e=self.entry(26)
        for rep in (0,1):
            recs=self.initials(e,rep);branches=[m.Branch(e,self.c,rep,c,recs) for c in m.CONDITIONS]
            seeds=[]
            for b in branches:
                while (r:=b.next_request()) is not None:
                    if r['stage']=='work' and r['actor']=='M1' and r['round']==1:seeds.append(r['seed'])
                    b.submit(r['request_id'],'actual text replay boundary',source_kind='ACTUAL_LOCAL_MODEL_RESPONSE')
            self.assertEqual(len(set(seeds)),1);self.assertEqual(seeds[0],20261102+m.OFFSETS[rep]+260000+1100)

    def test_branch_output_limit_isolates_dependency(self):
        e=self.entry(26);recs=self.initials(e);b=m.Branch(e,self.c,0,'B_delay',recs);other=m.Branch(e,self.c,0,'D',recs)
        r=b.next_request();b.submit(r['request_id'],'truncated full response',status='OUTPUT_LIMIT',source_kind='ACTUAL_LOCAL_MODEL_RESPONSE')
        self.assertIsNone(b.next_request());self.assertFalse(b.complete);self.assertIsNotNone(other.next_request())

    def test_failed_shared_initial_rejects_branch_creation(self):
        e=self.entry(26);recs=self.initials(e);recs[0]['status']='OUTPUT_LIMIT'
        with self.assertRaises(AssertionError):m.Branch(e,self.c,0,'B',recs)

    def test_budget_finite_no_new_work_turn(self):
        e=self.entry(26);recs=self.initials(e);total=4
        for cond in m.CONDITIONS:
            b=m.Branch(e,self.c,0,cond,recs);work=0;final=0
            while (r:=b.next_request()) is not None:
                work+=r['stage']=='work';final+=r['stage']=='final'
                self.assertEqual(r['max_new_tokens'],1024 if r['stage']=='work' else 256)
                b.submit(r['request_id'],'real response interface check',source_kind='ACTUAL_LOCAL_MODEL_RESPONSE');total+=1
            self.assertEqual((work,final),(8,4));self.assertTrue(b.complete)
        self.assertEqual(total,64);self.assertEqual(25*2*total,m.MAX_CALLS)

    def test_pack_mutation_rejected(self):
        bad=copy.deepcopy(self.pack);bad['source_sha256'][next(iter(bad['source_sha256']))]='0'*64
        with self.assertRaises(AssertionError):m.verify_pack(bad)

    def test_repeated_next_request_is_idempotent(self):
        e=self.entry(34);b=m.Branch(e,self.c,0,'B_delay',self.initials(e))
        self.assertEqual(b.next_request(),b.next_request());self.assertEqual(len(m.decode(b.next_request())['history']),1)

    def replay_worker(self,fail=False):
        # Temporary engineering replay only: old full actual texts feed the new
        # state machine; these files are deleted, never research generations.
        e=self.entry(26);old=m.load(m.ROOT/e['source_path']);pack=copy.deepcopy(self.pack);pack['tasks']=[e]
        class Cache:
            tokenizer=None
            def __init__(self,*_):pass
            def respond_many(self,requests,remaining):
                assert m.math.isinf(remaining)
                result=[]
                for r in requests:
                    x=next(x for x in old['records'] if all(x[k]==r[k] for k in ('actor','arm','stage','round')))
                    z={k:copy.deepcopy(x[k]) for k in ('raw_output','status','usage')}
                    z['usage']['replay_original_batch_size']=z['usage']['batch_size']
                    z['usage']['batch_size']=1 # Mock runtime contract, not new inference evidence.
                    if fail and '/B_delay/' in r['request_id'] and r['stage']=='work' and r['actor']=='M1' and r['round']==1:z['status']='OUTPUT_LIMIT'
                    result.append(z)
                return result
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)
            for n,v in [('INPUTS.json',pack),('LABELS.json',m.load(m.HERE/'LABELS.json')),('config.json',self.c),('FREEZE.json',{'files':{}})]:m.atomic(out/n,v)
            m.atomic(out/'APPROVAL.json',{'verdict':'RUN_ALLOWED','freeze_sha256':m.sha(out/'FREEZE.json')})
            with patch.object(m,'OUT',out),patch.object(m,'MultiBackend',Cache),patch.object(m,'length',return_value=100),contextlib.redirect_stdout(io.StringIO()):m.run()
            assert (out/'trials/026-r0.json').exists(),m.load(out/'RESULTS.json')
            return m.load(out/'RESULTS.json'),m.load(out/'trials/026-r0.json'),m.load(out/'scores.json'),[json.loads(x) for x in (out/'responses.jsonl').read_text().splitlines()]

    def test_actual_worker_shared_fork_and_offline_scoring_replay(self):
        result,item,scores,responses=self.replay_worker()
        expected=sum(64-m.Trial(self.entry(26)['task'],**m.options(self.c,self.entry(26),rep)).orders[0].index('M1') for rep in (0,1))
        self.assertEqual(result['status'],'COMPLETE');self.assertEqual(result['calls'],expected);self.assertEqual(len(responses),expected)
        self.assertTrue(all(b['complete'] for b in item['branches'].values()))
        shared=[r for r in item['branches']['B_delay']['records'] if 'shared_prefix_from' in r]
        self.assertEqual(len(shared),3)
        self.assertEqual(scores['summaries']['coverage']['complete_B_pair_units'],2)

    def test_actual_worker_failure_keeps_independent_arms_and_records_missing(self):
        result,item,scores,responses=self.replay_worker(True)
        self.assertEqual(result['status'],'COMPLETED_WITH_INCOMPLETE_BRANCHES')
        self.assertFalse(item['branches']['B_delay']['complete'])
        self.assertTrue(all(item['branches'][k]['complete'] for k in ('A','B','C','D')))
        self.assertEqual(scores['summaries']['coverage']['complete_B_pair_units'],0)
        self.assertEqual(len(result['incomplete_or_missing_units']),2)

if __name__=='__main__':unittest.main(verbosity=2)
