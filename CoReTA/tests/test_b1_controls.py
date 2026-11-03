"""B1 protocol fixtures; never task/model evidence."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from b1_controls import Trial, ARMS, vote, vote_scores, score_trial, summarize
from b0_answers import answer_score


def task():
    return dict(id='HOST_FIXTURE',question='When was X established?',paragraphs=[
        dict(idx=0,title='X',paragraph_text='X was established in 1900.')])


def data(req):
    return json.loads(req['payload']['user'].split('\n',1)[1])


def finish(trial):
    while (req:=trial.next_request()) is not None:
        text=(f"SECRET_{req['arm']}_{req['actor']}_{req['round']}" if req['stage']=='work'
              else f"FINAL_{req['arm']}_{req['actor']}" if req['stage']=='final' else '1900')
        trial.submit(req['request_id'],text)
    return trial


class ProtocolChecks(unittest.TestCase):
    def test_initials_shared_only_once_and_disclosure_delayed(self):
        t=Trial(task(),expert_actor='M2',fixture=True)
        initial_payloads=[]
        for _ in range(4):
            req=t.next_request();initial_payloads.append(req['payload'])
            self.assertNotIn('team_information',data(req))
            self.assertNotIn('history',data(req))
            t.submit(req['request_id'],'1900')
        self.assertTrue(all(v==initial_payloads[0] for v in initial_payloads))
        finish(t)
        self.assertEqual(len(t.records),52)
        self.assertEqual(sum(r['stage']=='initial' for r in t.records),4)
        for r in t.records[4:]:
            self.assertEqual('team_information' in data(r),r['arm'] in ('C','D'))

    def test_private_history_is_only_own_and_no_cross_arm(self):
        t=finish(Trial(task(),expert_actor='M1',fixture=True))
        for r in t.records[4:]:
            history=data(r)['history']
            self.assertTrue(all(m['phase']!='final' for m in history))
            if r['arm'] in ('A','C'):
                self.assertTrue(all(m['sender']==r['actor'] for m in history))
                self.assertEqual(len(history),3 if r['stage']=='final' else r['round'])
            for other in set(ARMS)-{r['arm']}:
                self.assertNotIn('SECRET_'+other,r['payload']['user'])

    def test_immediate_broadcast_and_no_other_final(self):
        t=finish(Trial(task(),expert_actor='M1',fixture=True))
        for arm in ('B','D'):
            rows=[r for r in t.records if r['arm']==arm and r['stage']=='work']
            for i,r in enumerate(rows):
                self.assertEqual([m['text'] for m in data(r)['history'][4:]],
                                 [x['raw_output'] for x in rows[:i]])
            for r in [x for x in t.records if x['arm']==arm and x['stage']=='final']:
                self.assertEqual(len(data(r)['history']),12)
                self.assertNotIn('FINAL_',r['payload']['user'])

    def test_matched_orders_seeds_and_two_turns(self):
        t=finish(Trial(task(),expert_actor='M1',fixture=True))
        def slots(arm):
            return [(r['stage'],r['round'],r['actor'],r['seed'],r['max_new_tokens'])
                    for r in t.records if r['arm']==arm]
        self.assertTrue(all(slots(a)==slots('A') for a in ARMS))
        for arm in ARMS:
            for actor in ('M1','M2','M3','M4'):
                self.assertEqual(sum(r['arm']==arm and r['actor']==actor and r['stage']=='work'
                                     for r in t.records),2)
        self.assertTrue(t.complete)

    def test_branch_failure_blocks_dependents_not_other_arms(self):
        t=Trial(task(),expert_actor='M1',fixture=True)
        for _ in range(4):
            r=t.next_request();t.submit(r['request_id'],'1900')
        r=t.next_request();t.submit(r['request_id'],None,status='TIMEOUT')
        finish(t)
        self.assertEqual(t.failed,{'A'})
        self.assertEqual(len(t.finals['A']),0)
        self.assertTrue(all(len(t.finals[a])==4 for a in ('B','C','D')))
        self.assertFalse(t.complete)
        self.assertEqual(len(t.records),41)

    def test_initial_failure_stops_dependencies_and_raw_kept(self):
        t=Trial(task(),expert_actor='M1',fixture=True)
        r=t.next_request();t.submit(r['request_id'],'raw interruption',status='TIMEOUT')
        self.assertIsNone(t.next_request())
        self.assertEqual(t.records[0]['raw_output'],'raw interruption')

    def test_snapshots_and_real_origin(self):
        t=Trial(task(),expert_actor='M1',fixture=False)
        r=t.next_request();r['payload']['user']='mutated'
        self.assertNotEqual(t.next_request()['payload']['user'],'mutated')
        with self.assertRaises(ValueError):t.submit(r['request_id'],'1900')
        t.submit(r['request_id'],'1900',source_kind='ACTUAL_LOCAL_MODEL_RESPONSE')
        view=t.export();view['initials'].clear()
        self.assertEqual(len(t.initials),1)


class ScoringChecks(unittest.TestCase):
    def test_raw_short_answers_are_not_cleaned_twice(self):
        t=Trial(task(),expert_actor='M1',fixture=True)
        raw='Answer: Answer: 1900'
        while (request:=t.next_request()) is not None:
            if request['stage']!='initial':
                self.assertTrue(all(m['text']==raw for m in data(request)['history']
                                    if m['phase']=='initial'))
            t.submit(request['request_id'],'work' if request['stage']=='work' else raw)
        target=dict(id=task()['id'],answer='1900')
        result=score_trial(t.export(),target)
        self.assertEqual(result['initial']['members']['M1']['em'],answer_score(raw,target)['em'])
        self.assertEqual(result['arms']['A']['expert_em'],0)
        self.assertEqual(result['arms']['A']['expected_em'],0)

    def trace(self, index=0):
        item=task();item['id']=f'FIXTURE_{index}'
        t=Trial(item,expert_actor='M1',fixture=True,task_index=index)
        while (r:=t.next_request()) is not None:
            answer='1900' if r['actor'] in ('M1','M2') else '1950'
            t.submit(r['request_id'],'work text' if r['stage']=='work' else answer)
        return t.export()

    def target(self,index=0):return dict(id=f'FIXTURE_{index}',answer='1900',answer_aliases=['nineteen hundred'])

    def test_tie_expected_score_and_no_expert_priority(self):
        answers=dict(M1='1900',M2='1900',M3='1950',M4='1950')
        selected=vote(answers,13)
        self.assertTrue(selected['tie'])
        self.assertEqual(vote_scores(selected,self.target())['expected_em'],.5)
        self.assertEqual(selected,vote(answers,13))
        self.assertEqual(vote(dict(M1='alpha',M2='alpha',M3='beta',M4='gamma'),13)['answer'],'alpha')
        self.assertEqual(vote(dict.fromkeys(answers,''),13)['answer'],'')
        before=deepcopy(selected)
        vote_scores(selected,dict(answer='1950'))
        self.assertEqual(selected,before)

    def test_readout_loss_distinct_from_expert_harm_and_fixture(self):
        report=score_trial(self.trace(),self.target())
        self.assertTrue(report['complete'])
        self.assertFalse(report['primary_enabled'])
        for arm in ARMS:
            self.assertEqual(report['arms'][arm]['expert_em'],1)
            self.assertEqual(report['arms'][arm]['expert_harm'],0)
            self.assertEqual(report['arms'][arm]['expert_correct_but_not_selected_expected'],.5)

    def test_replay_rejects_changed_visibility(self):
        trace=self.trace()
        trace['records'][5]['payload']['user']+=' leaked history'
        with self.assertRaisesRegex(ValueError,'trace_does_not_match_protocol'):
            score_trial(trace,self.target())

    def test_batch_missing_not_hidden_and_zero_denominator(self):
        traces=[self.trace(0),self.trace(1)]
        targets={self.target(i)['id']:self.target(i) for i in range(3)}
        groups={f'FIXTURE_{i}':i for i in range(3)}
        report=summarize(traces,targets,list(groups),groups,repeats=100)
        self.assertEqual(report['status'],'INCOMPLETE')
        self.assertEqual(report['n_expected'],3)
        self.assertEqual(report['n_complete'],2)
        self.assertFalse(report['primary_enabled'])
        self.assertIsNone(report['arms']['A']['expert_correction_rate'])
        self.assertEqual(report['contrasts']['B-A']['expected_em']['difference'],0)
        with self.assertRaises(ValueError):summarize(traces+traces[:1],targets,list(groups),groups,100)

    def test_empty_short_answer_abstains_without_schema_error(self):
        t=Trial(task(),expert_actor='M1',fixture=True)
        while (r:=t.next_request()) is not None:t.submit(r['request_id'],'')
        report=score_trial(t.export(),dict(id=task()['id'],answer='1900'))
        self.assertTrue(report['complete'])
        self.assertEqual(report['arms']['A']['expected_em'],0)
        self.assertEqual(report['arms']['A']['vote']['abstained'],['M1','M2','M3','M4'])


if __name__=='__main__':unittest.main()
