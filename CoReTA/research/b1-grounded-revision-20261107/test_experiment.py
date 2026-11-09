import contextlib,copy,io,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import experiment as m

class ProtocolTests(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.c=m.load(m.SOURCE/'config.json');cls.pack=m.load(m.HERE/'INPUTS.json');cls.src=m.load(m.SOURCE/'trials/026-r0.json')
    cls.e=dict(index=26,id=cls.src['id'],task=m.load(m.ROOT/'research/b1-independent-first-work-20261106/INPUTS.json')['tasks'][6]['task'])
    cls.e=next(copy.deepcopy(e) for e in m.load(m.ROOT/'research/b1-independent-first-work-20261106/INPUTS.json')['tasks'] if e['index']==26)
    cls.e['cohort']='fresh'
  def branch(self,c):return m.Branch(self.e,self.c,c,self.src['initial_records'])
  def test_real_four_arm_request_replay(self):
    for c in ('A','B','C','D'):
      b=self.branch(c)
      for z in self.src['branches'][c]['records']:
        r=b.next_request()
        for k in ('payload','actor','arm','stage','round','seed','max_new_tokens'):self.assertEqual(r[k],z[k])
        b.submit(r['request_id'],z['raw_output'],usage=z['usage'],source_kind=z['source_kind'])
      self.assertTrue(b.complete)
  def test_exactly_second_expert_input_changes(self):
    for c in m.INSTRUCTIONS:
      b=self.branch(c);changed=0
      for z in self.src['branches']['B']['records']:
        r=b.next_request();d=m.decode(r,self.c['answer_suffix'] if r['stage']=='final' else '')
        if m.is_fork(r):
          self.assertEqual(d.pop('work_instruction'),m.INSTRUCTIONS[c]);self.assertEqual(d,m.decode(z));changed+=1
        else:self.assertEqual(r['payload'],z['payload'])
        self.assertEqual(r['seed'],z['seed']);b.submit(r['request_id'],z['raw_output'],source_kind=z['source_kind'])
      self.assertEqual(changed,1)
  def test_new_expert_message_reaches_all_downstream_not_private_finals(self):
    for c in m.INSTRUCTIONS:
      b=self.branch(c);seen=False
      for z in self.src['branches']['B']['records']:
        r=b.next_request();d=m.decode(r,self.c['answer_suffix'] if r['stage']=='final' else '')
        if seen:self.assertIn('AUDIT_NEW_EXPERT_MESSAGE',r['payload']['user'])
        self.assertFalse(any(x['phase']=='final' for x in d['history']))
        text=z['raw_output']
        if m.is_fork(r):text+=' AUDIT_NEW_EXPERT_MESSAGE';seen=True
        b.submit(r['request_id'],text,source_kind=z['source_kind'])
      self.assertTrue(b.complete)
  def test_no_label_or_role_metadata_in_model_payload(self):
    for c in m.CONDITIONS:
      b=self.branch(c)
      for z in self.src['branches'][c if c in ('A','B','C','D') else 'B']['records']:
        r=b.next_request();d=m.decode(r,self.c['answer_suffix'] if r['stage']=='final' else '')
        self.assertFalse({'id','answer','answer_aliases','cohort','coverage','mechanism','question_decomposition'}&set(d));self.assertEqual(d['paragraphs'],self.e['task']['paragraphs'])
        b.submit(r['request_id'],z['raw_output'],source_kind=z['source_kind'])
  def test_pack_and_budget_selection(self):
    m.verify_pack(self.pack);self.assertEqual(len(m.entry_order(self.pack)),100)
    self.assertEqual(m.MAX_CALLS,100*(4+6*12));self.assertEqual(abs(len(m.INSTRUCTIONS['B_check'].split())-len(m.INSTRUCTIONS['B_relation'].split())),1)
  def test_next_request_idempotent(self):
    b=self.branch('B_relation');self.assertEqual(b.next_request(),b.next_request())
  def replay_worker(self,fail=None,long=False,score_fail=False):
    e=copy.deepcopy(self.e);pack=dict(tasks=[e],groups={e['id']:'g0'});source=self.src
    class Cache:
      tokenizer=None
      def __init__(self,*_):pass
      def respond_many(self,requests,remaining):
        assert m.math.isinf(remaining);out=[]
        for r in requests:
          if r['stage']=='initial':z=next(z for z in source['initial_records'] if z['actor']==r['actor'])
          else:z=next(z for z in source['branches'][r['arm']]['records'] if all(z[k]==r[k] for k in ('stage','round','actor')))
          response={k:copy.deepcopy(z[k]) for k in ('raw_output','status','usage')}
          cond=r['request_id'].split('/')[-2]
          if fail=='system' and cond=='B_relation' and m.is_fork(r):raise RuntimeError('AUDIT_SIMULATED_SYSTEM_FAULT')
          if (fail=='initial' and r['stage']=='initial' and r['actor']=='M1') or (fail=='shared' and r['arm']=='B' and r['stage']=='work' and r['round']==1) or (fail=='target' and cond=='B_relation' and m.is_fork(r)):response['status']='OUTPUT_LIMIT'
          if fail=='empty' and cond=='B_relation' and m.is_fork(r):response['raw_output']=''
          out.append(response)
        return out
    def fake_length(tok,c,r):return c['max_length'] if long and '/B_relation/' in r['request_id'] and m.is_fork(r) else 100
    with tempfile.TemporaryDirectory() as d:
      out=Path(d)
      for n,z in [('config.json',self.c),('INPUTS.json',pack),('LABELS.json',m.load(m.SOURCE/'LABELS.json')),('FREEZE.json',dict(files={}))]:m.atomic(out/n,z)
      m.atomic(out/'APPROVAL.json',dict(verdict='RUN_ALLOWED',freeze_sha256=m.sha(out/'FREEZE.json')))
      if score_fail:m.atomic(out/'LABELS.json',dict(targets={}))
      with patch.object(m,'OUT',out),patch.object(m,'MultiBackend',Cache),patch.object(m,'length',fake_length),contextlib.redirect_stdout(io.StringIO()):m.run()
      t=m.load(next((out/'trials').glob('*.json')));result=m.load(out/'RESULTS.json')
      return result,t,(out/'SCORING_ERROR.json').exists()
  def test_full_executor_shared_prefix_counts_and_scores(self):
    result,t,_=self.replay_worker();self.assertEqual(result['status'],'COMPLETE');self.assertTrue(all(b['complete'] for b in t['branches'].values()))
    prefix=4+self.src['branches']['B']['orders'][1].index('M1');self.assertEqual(result['calls'],76-2*prefix)
  def test_single_target_failure_keeps_other_five(self):
    result,t,_=self.replay_worker('target');self.assertEqual(result['status'],'COMPLETED_WITH_INCOMPLETE_BRANCHES');self.assertFalse(t['branches']['B_relation']['complete']);self.assertTrue(all(t['branches'][c]['complete'] for c in m.CONDITIONS if c!='B_relation'))
  def test_shared_prefix_failure_isolates_three_dependents(self):
    result,t,_=self.replay_worker('shared');self.assertEqual(result['status'],'COMPLETED_WITH_INCOMPLETE_BRANCHES');self.assertTrue(all(t['branches'][c]['complete'] for c in ('A','C','D')));self.assertFalse(any(t['branches'][c]['complete'] for c in m.PUBLIC))
  def test_shared_initial_failure_skips_only_task(self):
    result,t,_=self.replay_worker('initial');self.assertEqual(t['status'],'SHARED_INITIAL_FAILED');self.assertEqual(result['calls'],1)
  def test_empty_response_isolated(self):
    result,t,_=self.replay_worker('empty');self.assertFalse(t['branches']['B_relation']['complete']);self.assertTrue(t['branches']['B']['complete'])
  def test_host_overlength_isolated_without_generation(self):
    result,t,_=self.replay_worker(long=True);self.assertFalse(t['branches']['B_relation']['complete']);self.assertTrue(t['branches']['A']['complete'])
  def test_scoring_error_preserves_complete_generation_state(self):
    result,t,error=self.replay_worker(score_fail=True);self.assertEqual(result['status'],'COMPLETE');self.assertTrue(error)
  def test_system_fault_records_specific_reason_and_partial_data(self):
    result,t,_=self.replay_worker('system');self.assertEqual(result['status'],'STOPPED_SYSTEM_FAULT');self.assertIn('AUDIT_SIMULATED_SYSTEM_FAULT',result['error']);self.assertGreater(result['confirmed_returns'],0)

if __name__=='__main__':unittest.main(verbosity=2)
