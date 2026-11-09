"""Full actual histories and finite whole-worker replay, not model generations."""
import contextlib,copy,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import experiment as m

class CrossTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.pack=m.load(m.SOURCE/'INPUTS.json');cls.c=m.load(m.SOURCE/'config.json')
    def entry(self,i):return next(e for e in self.pack['tasks'] if e['index']==i)
    def finish_replay(self,b,src):
        by={(r['stage'],r['round'],r['actor']):r for r in src['records']};requests=[]
        while (r:=b.next_request()) is not None:
            requests.append(r);z=by[r['stage'],r['round'],r['actor']];b.submit(r['request_id'],z['raw_output'],status=z['status'],usage=z['usage'],source_kind=z['source_kind'])
        return requests
    def test_all_diagonal_inputs_seeds_exactly_match_audited_sources(self):
        count=0
        for e in self.pack['tasks']:
            for s in (0,1):
                src=m.source_trace(e,s)
                for cond in m.CONDITIONS:
                    requests=self.finish_replay(m.make_branch(e,self.c,s,s,cond),src['branches'][cond])
                    for r,z in zip(requests,src['branches'][cond]['records']):
                        for k in ('payload','seed','actor','stage','round','arm','max_new_tokens'):self.assertEqual(r[k],z[k])
                        count+=1
        self.assertEqual(count,1200)
    def test_order_and_display_fixed_when_only_sampling_changes(self):
        for e in self.pack['tasks']:
            for o in (0,1):
                a=m.make_branch(e,self.c,0,o,'B');b=m.make_branch(e,self.c,1,o,'B')
                self.assertEqual(a.orders,b.orders);self.assertEqual(a.initial_order,b.initial_order)
                ar=self.finish_replay(a,m.source_trace(e,0)['branches']['B']);br=self.finish_replay(b,m.source_trace(e,1)['branches']['B'])
                for x,y in zip(ar,br):
                    self.assertEqual((x['actor'],x['stage'],x['round']),(y['actor'],y['stage'],y['round']));self.assertEqual(y['seed']-x['seed'],100000000)
    def test_sampling_and_initials_fixed_when_only_order_changes(self):
        for e in self.pack['tasks']:
            for s in (0,1):
                a=m.make_branch(e,self.c,s,0,'B');b=m.make_branch(e,self.c,s,1,'B')
                self.assertEqual(a.initials,b.initials);self.assertNotEqual(a.initial_order,b.initial_order)
                ar=self.finish_replay(a,m.source_trace(e,s)['branches']['B']);br=self.finish_replay(b,m.source_trace(e,s)['branches']['B'])
                am={(r['actor'],r['stage'],r['round']):r['seed'] for r in ar};bm={(r['actor'],r['stage'],r['round']):r['seed'] for r in br};self.assertEqual(am,bm)
    def test_delayed_first_input_independent_of_order_and_restored_second(self):
        for e in self.pack['tasks']:
            for s in (0,1):
                first=[]
                for o in (0,1):
                    rs=self.finish_replay(m.make_branch(e,self.c,s,o,'B_delay'),m.source_trace(e,s)['branches']['B_delay'])
                    for r in rs:
                        if r['actor']=='M1' and r['stage']=='work':
                            h=m.decode(r)['history']
                            if r['round']==1:
                                self.assertEqual(h,[dict(sender='M1',phase='initial',text=m.source_trace(e,s)['initials']['M1'])]);first.append(r)
                            else:self.assertEqual({x['sender'] for x in h if x['phase']=='initial'},set(m.ACTORS))
                self.assertEqual(first[0]['payload'],first[1]['payload']);self.assertEqual(first[0]['seed'],first[1]['seed'])
    def test_private_finals_not_broadcast_and_labels_absent(self):
        e=self.entry(26)
        for s,o in m.CELLS:
            for cond in m.CONDITIONS:
                rs=self.finish_replay(m.make_branch(e,self.c,s,o,cond),m.source_trace(e,s)['branches'][cond])
                for r in rs:
                    d=m.decode(r,self.c['answer_suffix'] if r['stage']=='final' else '')
                    self.assertFalse({'target','answer','answer_aliases','question_decomposition','sampling_setting','order_setting'}&set(d));self.assertFalse(any(x['phase']=='final' for x in d['history']));self.assertEqual(d['paragraphs'],e['task']['paragraphs'])
    def test_new_work_propagates_to_all_future_receivers(self):
        e=self.entry(26);b=m.make_branch(e,self.c,0,1,'B_delay');src=m.source_trace(e,0)['branches']['B_delay'];by={(r['stage'],r['round'],r['actor']):r for r in src['records']};seen=False;later=0
        while (r:=b.next_request()) is not None:
            if seen:self.assertIn('CROSS_PROTOCOL_SENTINEL',r['payload']['user']);later+=1
            z=by[r['stage'],r['round'],r['actor']];text=z['raw_output']
            if r['actor']=='M1' and r['stage']=='work' and r['round']==1:text+=' CROSS_PROTOCOL_SENTINEL';seen=True
            b.submit(r['request_id'],text,source_kind=z['source_kind'])
        self.assertGreater(later,4)
    def test_failure_stops_only_dependent_branch(self):
        e=self.entry(26);b=m.make_branch(e,self.c,0,1,'B_delay');other=m.make_branch(e,self.c,0,1,'B');r=b.next_request();b.submit(r['request_id'],'actual full text capped',status='OUTPUT_LIMIT',source_kind='ACTUAL_LOCAL_MODEL_RESPONSE');self.assertIsNone(b.next_request());self.assertIsNotNone(other.next_request())
    def test_budget_and_shared_prefix_count(self):
        shared=sum(m.source_trace(e,o)['branches']['B']['orders'][0].index('M1') for e in self.pack['tasks'] for s,o in m.CELLS)
        self.assertEqual(shared,67);self.assertEqual(25*2*2*12,m.MAX_CALLS);self.assertEqual(m.MAX_CALLS-shared,1133)
    def test_next_request_idempotent(self):
        b=m.make_branch(self.entry(34),self.c,0,1,'B_delay');self.assertEqual(b.next_request(),b.next_request())
    def worker_replay(self,fail=False):
        e=self.entry(26);pack=copy.deepcopy(self.pack);pack['tasks']=[e]
        class Cache:
            tokenizer=None
            def __init__(self,*_):pass
            def respond_many(self,requests,remaining):
                assert m.math.isinf(remaining);out=[]
                for r in requests:
                    s=int(r['request_id'].split('/')[1][1]);cond=r['request_id'].split('/')[2]
                    x=next(x for x in m.source_trace(e,s)['branches'][cond]['records'] if all(x[k]==r[k] for k in ('stage','round','actor')))
                    z={k:copy.deepcopy(x[k]) for k in ('raw_output','status','usage')}
                    if fail and cond=='B_delay' and r['actor']=='M1' and r['stage']=='work' and r['round']==1:z['status']='OUTPUT_LIMIT'
                    out.append(z)
                return out
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)
            for n,v in [('INPUTS.json',pack),('LABELS.json',m.load(m.SOURCE/'LABELS.json')),('config.json',self.c),('FREEZE.json',{'files':{}})]:m.atomic(out/n,v)
            m.atomic(out/'APPROVAL.json',dict(verdict='RUN_ALLOWED',freeze_sha256=m.sha(out/'FREEZE.json')))
            with patch.object(m,'OUT',out),patch.object(m,'MultiBackend',Cache),patch.object(m,'length',return_value=100),contextlib.redirect_stdout(io.StringIO()):m.run()
            return m.load(out/'RESULTS.json'),m.load(out/'scores.json'),[m.load(p) for p in (out/'trials').glob('*.json')]
    def test_whole_worker_replay_diagonal_reuse_crosses_and_factorial_score(self):
        result,score,trials=self.worker_replay();self.assertEqual(result['status'],'COMPLETE');self.assertEqual(len(trials),2);self.assertEqual(len(score['rows']),4);self.assertEqual(score['summaries']['coverage']['four_cell_complete_questions'],1)
        e=self.entry(26);expected=48-sum(m.source_trace(e,o)['branches']['B']['orders'][0].index('M1') for _,o in m.CELLS);self.assertEqual(result['calls'],expected)
        self.assertEqual({r['origin'] for r in score['rows']},{'INHERITED_DIAGONAL','NEW_CROSSED_CELL'})
    def test_whole_worker_failure_preserves_other_branches_and_diagonals(self):
        result,score,trials=self.worker_replay(True);self.assertEqual(result['status'],'COMPLETED_WITH_INCOMPLETE_BRANCHES');self.assertEqual(len(result['incomplete_or_missing_cells']),2);self.assertEqual(score['summaries']['coverage']['four_cell_complete_questions'],0)
        self.assertTrue(all(t['branches']['B']['complete'] and not t['branches']['B_delay']['complete'] for t in trials));self.assertEqual(sum(r['paired_complete'] for r in score['rows']),2)

if __name__=='__main__':unittest.main(verbosity=2)
