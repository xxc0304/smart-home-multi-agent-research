"""Six-arm bounded diagnostic, full downstream, no training or wall cutoff."""
import argparse,copy,hashlib,importlib.util,json,math,random,sys,time
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
spec=importlib.util.spec_from_file_location('old_first_work',ROOT/'research/b1-independent-first-work-20261106/experiment.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
from b1_controls import Trial,vote,vote_scores
from b0_answers import answer_score,paired_interval
from b1_runtime import validate_runtime
from b1_multi_backend import MultiBackend
HERE=Path(__file__).resolve().parent;OUT=ROOT/'runs/b1-grounded-revision-20261107-v1';SOURCE=old.OUT
load,sha,atomic,append,length,decode=old.load,old.sha,old.atomic,old.append,old.length,old.decode
CONDITIONS=('A','B','C','D','B_check','B_relation');PUBLIC=('B','B_check','B_relation');MAX_CALLS=7600
INSTRUCTIONS={
'B_check':'Before you finish this work turn, review the question, supplied paragraphs, your previous reasoning and the visible discussion. Check your current answer carefully, resolve inconsistencies and reconsider alternatives. Keep or revise your answer as needed, then give your best response.',
'B_relation':'When weighing competing answers, check the specific entity and relation required by the question against supplied paragraphs. Keep or revise your answer according to that match. Repeated agreement alone is not additional evidence. A supported correction from any participant is valid.'}

class Branch(old.Branch):
  def __init__(self,e,c,condition,initial_records):
    assert condition in CONDITIONS
    super().__init__(e,c,0,condition if condition in ('A','B','C','D') else 'B',initial_records)
    self.condition=condition
  def next_request(self):
    r=super().next_request()
    if r is None:return None
    p=self.pending
    if self.condition in INSTRUCTIONS and p['actor']=='M1' and p['stage']=='work' and p['round']==2:
      d=decode(p);d['work_instruction']=INSTRUCTIONS[self.condition]
      p['payload']['user']='TASK_DATA\n'+json.dumps(d,ensure_ascii=False,indent=2)
    return copy.deepcopy(p)

def initial_trial(e,c):return Trial(e['task'],**old.options(c,e,0))
def initial_request(t):return old.initial_request(t,0)
def is_fork(r):return r['actor']=='M1' and r['stage']=='work' and r['round']==2
def entry_order(pack):return sorted(pack['tasks'],key=lambda e:hashlib.sha256(('grounded-run-order-20261107|'+e['id']).encode()).hexdigest())

def verify_pack(pack):
  assert len(pack['tasks'])==100 and len({e['id'] for e in pack['tasks']})==100
  assert Counter(e['cohort'] for e in pack['tasks'])==dict(fresh=56,old_coverage=36,mechanism=8)
  assert set(pack['groups'])=={e['id'] for e in pack['tasks']}
  for p,h in pack['source_sha256'].items():assert sha(p)==h,('source_changed',p)
  for e in pack['tasks']:
    assert set(e['task'])=={'id','question','paragraphs'} and all(set(p)=={'idx','title','paragraph_text'} for p in e['task']['paragraphs'])

def score():
  pack=load(OUT/'INPUTS.json');targets=load(OUT/'LABELS.json')['targets'];rows=[]
  for e in pack['tasks']:
    f=OUT/f'trials/{e["index"]:03d}.json';t=load(f) if f.exists() else None
    row=dict(index=e['index'],id=e['id'],cohort=e['cohort'],strict_training_answer_isolation=e.get('strict_training_answer_isolation'),old_index=e.get('old_index'),initial={},conditions={})
    if t and len(t['initials'])==4:row['initial']={a:answer_score(v,targets[e['id']]) for a,v in t['initials'].items()}
    for cond in CONDITIONS:
      b=t['branches'].get(cond) if t else None
      if not b or not b['complete']:row['conditions'][cond]=dict(complete=False);continue
      members={a:answer_score(v,targets[e['id']]) for a,v in b['finals'].items()};v=vote(b['finals'],20261102+e['index']*10000+1001)
      row['conditions'][cond]=dict(complete=True,members=members,vote=v,**vote_scores(v,targets[e['id']]),expert_em=members['M1']['em'])
    rows.append(row)
  result=dict(scope='56_FRESH_36_OLD_COVERAGE_8_OLD_MECHANISM_T_ANSWER_OVERLAP_STRATIFIED',primary='B_relation-B_check team expected EM on fresh56',rows=rows,summaries={})
  for cohort in ('fresh','fresh_strict','fresh_answer_overlap','old_coverage','mechanism','all'):
    rs=[r for r in rows if cohort=='all' or r['cohort']==cohort or (cohort=='fresh_strict' and r['cohort']=='fresh' and r['strict_training_answer_isolation']) or (cohort=='fresh_answer_overlap' and r['cohort']=='fresh' and not r['strict_training_answer_isolation'])];summ=dict(expected=len(rs),conditions={},contrasts={})
    for cond in CONDITIONS:
      valid=[r for r in rs if r['conditions'][cond]['complete']]
      summ['conditions'][cond]=dict(n=len(valid),team_expected_em=sum(r['conditions'][cond]['expected_em'] for r in valid)/len(valid) if valid else None,expert_em=sum(r['conditions'][cond]['expert_em'] for r in valid)/len(valid) if valid else None)
    for left,right in [('B_relation','B_check'),('B_relation','B'),('B_check','B'),('B','A'),('D','C')]:
      valid=[r for r in rs if r['conditions'][left]['complete'] and r['conditions'][right]['complete']]
      values={r['id']:r['conditions'][left]['expected_em']-r['conditions'][right]['expected_em'] for r in valid};groups={i:pack['groups'][i] for i in values}
      summ['contrasts'][left+'-'+right]=dict(n=len(valid),difference=sum(values.values())/len(values) if values else None,cluster_ci95=paired_interval(values,groups,10000,20261107) if values else None,gains=sum(x>0 for x in values.values()),losses=sum(x<0 for x in values.values()))
    result['summaries'][cohort]=summ
  atomic(OUT/'scores.json',result);return result

def prepare():
  from b0_training import load_tokenizer
  pack=load(HERE/'INPUTS.json');verify_pack(pack);tests=load(HERE/'TESTS.json')
  assert tests['verdict']=='PASS' and tests['code_sha256']==sha(HERE/'experiment.py') and tests['tests_sha256']==sha(HERE/'test_experiment.py')
  assert 'SCIENCE_PASS' in (HERE/'EXPERIMENT_REVIEW.md').read_text()
  c=load(SOURCE/'config.json');q=validate_runtime(c);c['purpose']='FRESH_AND_REUSED_GROUNDED_REVISION_DEVELOPMENT'
  tok=load_tokenizer(c);real=[]
  for f in (SOURCE/'trials').glob('*.json'):
    t=load(f);real+=t['initial_records'];real+=t['branches']['B']['records']
  good=[r for r in real if r['status']=='OK'];li=max((r for r in good if r['stage']=='initial'),key=lambda r:r['usage']['output_tokens']);lw=max((r for r in good if r['stage']=='work'),key=lambda r:r['usage']['output_tokens'])
  maxima=[];requests=0;shared=0;maxinput=0
  for e in pack['tasks']:
    t=initial_trial(e,c);recs=[]
    for _ in range(4):
      r=initial_request(t);n=length(tok,c,r)+r['max_new_tokens'];maxinput=max(maxinput,n);assert n<=c['max_length'];recs.append(t.submit(r['request_id'],li['raw_output'],usage=li['usage'],source_kind='ACTUAL_LOCAL_MODEL_RESPONSE'))
    shared+=2*(4+t.orders[1].index('M1'))
    for cond in CONDITIONS:
      b=Branch(e,c,cond,recs)
      while (r:=b.next_request()) is not None:
        n=length(tok,c,r)+r['max_new_tokens'];maxinput=max(maxinput,n);assert n<=c['max_length'],('pressure_over_context',e['index'],cond,n)
        z=lw if r['stage']=='work' else li;b.submit(r['request_id'],z['raw_output'],usage=z['usage'],source_kind='ACTUAL_LOCAL_MODEL_RESPONSE');requests+=1
      assert b.complete
  assert requests==7200
  # Exact historical replay plus altered-instruction payload check is in CPU tests.
  OUT.mkdir(parents=True,exist_ok=False)
  for n in ('INPUTS.json','LABELS.json','SELECTION_REVIEW.json'):atomic(OUT/n,load(HERE/n))
  atomic(OUT/'config.json',c)
  budget=dict(unique_questions=100,fresh_primary=56,old_coverage=36,old_mechanism=8,conditions=list(CONDITIONS),max_calls=7600,expected_complete_physical_calls=7600-shared,max_output_tokens=5632000,wall_clock_cutoff=None,generation_retry=False,execution='ALL_SINGLETON',failure_policy='Initial failure skips one task; shared upstream failure isolates its three dependent public arms; independent arm output/length/empty failure isolated; system fault stops; no automatic replay')
  atomic(OUT/'BUDGET.json',budget)
  pf=dict(science='PASS',engineering='PASS',qualification=q['qualification'],full_actual_long_response_requests=requests+400,pressure_max_input_plus_cap=maxinput,context=c['max_length'],runtime_exact_length_guard=True,shared_prefix_saved_calls=shared,new_model_calls=0,tests=tests['tests'])
  atomic(OUT/'PREFLIGHT.json',pf)
  files=[HERE/n for n in ('experiment.py','build_pack.py','launch.py','test_experiment.py','run_checks.py','TESTS.json','INPUTS.json','LABELS.json','SELECTION_REVIEW.json','EXPERIMENT_REVIEW.md','BRIEF.md')]
  files += [OUT/n for n in ('config.json','INPUTS.json','LABELS.json','SELECTION_REVIEW.json','PREFLIGHT.json','BUDGET.json')]
  files += [Path(p) for p in pack['source_sha256']]
  files += [ROOT/p for p in ('research/b1-independent-first-work-20261106/experiment.py','tools/b1_controls.py','tools/b1_runtime.py','tools/b1_multi_backend.py','tools/b1_stop_status.py','tools/b1_output_contract.py','tools/b0_answers.py','tools/b0_training.py','tools/expert_mechanism_protocol.py','tools/prepare_answer_only_expert.py','tools/prepare_expert_training.py','research/musique-data-preparation-20261030/official_scorer/metrics/answer.py')]
  files += [Path(c['adapter_path'])/n for n in ('adapter_config.json','adapter_model.safetensors','b0_origin.json')]
  files += [Path(c[k]) for k in ('baseline_C_score','expert_C_score')]+[ROOT/'implement-stage/expert-answer-only-20261101/C_GROUPS.json']
  atomic(OUT/'FREEZE.json',dict(files={str(p):sha(p) for p in dict.fromkeys(files)}));atomic(OUT/'STATUS.json',dict(status='PREPARED_NOT_LAUNCHED',calls=0))
  print(json.dumps(dict(preflight=pf,budget=budget,freeze_sha256=sha(OUT/'FREEZE.json'))),flush=True)

def verify_freeze():
  for p,h in load(OUT/'FREEZE.json')['files'].items():assert sha(p)==h,('frozen_changed',p)

def run():
  import fcntl
  lock=(OUT/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  verify_freeze();approval=load(OUT/'APPROVAL.json');assert approval['verdict']=='RUN_ALLOWED' and approval['freeze_sha256']==sha(OUT/'FREEZE.json')
  (OUT/'STARTED').touch(exist_ok=False);c=load(OUT/'config.json');pack=load(OUT/'INPUTS.json');begin=time.monotonic();calls=done=0;error=None
  atomic(OUT/'STATUS.json',dict(status='LOADING_MODEL',calls=0))
  def save_status(e=None,cond=None):
    atomic(OUT/'STATUS.json',dict(status='RUNNING',calls=calls,max_calls=MAX_CALLS,completed_questions=done,total_questions=len(pack['tasks']),index=e['index'] if e else None,cohort=e['cohort'] if e else None,condition=cond,elapsed_seconds=time.monotonic()-begin))
  try:
    backend=MultiBackend(c)
    def generate(r):
      nonlocal calls
      n=length(backend.tokenizer,c,r)
      if n+r['max_new_tokens']>c['max_length']:
        z=dict(status='INPUT_TOO_LONG',raw_output=None,usage=dict(input_tokens=n,output_tokens=0,host_no_generation=True));append(OUT/'host_failures.jsonl',dict(request=r,response=z));return z
      assert calls<MAX_CALLS;append(OUT/'ATTEMPTS.jsonl',dict(attempt_index=calls,request=r));calls+=1
      z=backend.respond_many([r],math.inf)[0]
      if z['status']=='OK' and (not isinstance(z['raw_output'],str) or not z['raw_output'].strip()):z['status']='EMPTY_OR_NON_TEXT'
      append(OUT/'responses.jsonl',dict(request=r,response=z,source_kind='ACTUAL_LOCAL_MODEL_RESPONSE',fixture=False))
      u=z['usage'];assert u['adapter_enabled']==(r['actor']=='M1') and u['disabled_layers']==(0 if r['actor']=='M1' else 252) and u['lora_layers']==252 and u['batch_size']==1
      return z
    for pos,e in enumerate(entry_order(pack)):
      t=initial_trial(e,c);item=dict(index=e['index'],id=e['id'],cohort=e['cohort'],initial_records=[],initials={},branches={},status='RUNNING');f=OUT/f'trials/{e["index"]:03d}.json'
      for _ in range(4):
        r=initial_request(t)
        if r is None:break
        z=generate(r);item['initial_records'].append(t.submit(r['request_id'],z['raw_output'],status=z['status'],usage=z['usage'],source_kind='ACTUAL_LOCAL_MODEL_RESPONSE'));item['initials']=copy.deepcopy(t.initials);atomic(f,item);save_status(e,'initial')
      if len(t.initials)==4 and not t.initial_failed:
        bs={cond:Branch(e,c,cond,t.records) for cond in CONDITIONS}
        while (r:=bs['B'].next_request()) is not None and not is_fork(r):
          reqs={cond:bs[cond].next_request() for cond in PUBLIC}
          assert all(reqs[k]['payload']==r['payload'] and reqs[k]['seed']==r['seed'] for k in PUBLIC)
          z=generate(r)
          for cond,req in reqs.items():
            rec=bs[cond].submit(req['request_id'],z['raw_output'],status=z['status'],usage=z['usage'],source_kind='ACTUAL_LOCAL_MODEL_RESPONSE')
            if cond!='B':rec['shared_prefix_from']=r['request_id']
            item['branches'][cond]=bs[cond].export()
          atomic(f,item);save_status(e,'shared_public_prefix')
        rotation=pos%len(CONDITIONS);conds=CONDITIONS[rotation:]+CONDITIONS[:rotation]
        for cond in conds:
          b=bs[cond]
          while (r:=b.next_request()) is not None:
            z=generate(r);b.submit(r['request_id'],z['raw_output'],status=z['status'],usage=z['usage'],source_kind='ACTUAL_LOCAL_MODEL_RESPONSE');item['branches'][cond]=b.export();atomic(f,item);save_status(e,cond)
          item['branches'][cond]=b.export();atomic(f,item)
        item['status']='COMPLETE' if all(b.complete for b in bs.values()) else 'INCOMPLETE_BRANCHES'
      else:item['status']='SHARED_INITIAL_FAILED'
      done+=1;atomic(f,item);save_status(e)
    state='FINISHED'
  except BaseException as ex:state='STOPPED_SYSTEM_FAULT';error=type(ex).__name__+':'+str(ex)
  failures=[]
  for e in pack['tasks']:
    f=OUT/f'trials/{e["index"]:03d}.json';t=load(f) if f.exists() else None
    if not t or t['status']!='COMPLETE':failures.append(dict(index=e['index'],id=e['id'],status=t['status'] if t else 'MISSING'))
  if state=='FINISHED':state='COMPLETE' if not failures else 'COMPLETED_WITH_INCOMPLETE_BRANCHES'
  responses=[json.loads(s) for s in (OUT/'responses.jsonl').read_text().splitlines()] if (OUT/'responses.jsonl').exists() else []
  result=dict(status=state,error=error,calls=calls,confirmed_returns=len(responses),completed_questions=done,total_questions=len(pack['tasks']),incomplete_or_missing_questions=failures,elapsed_seconds=time.monotonic()-begin,no_wall_cutoff=True,statuses=dict(Counter(z['response']['status'] for z in responses)),output_tokens=sum(z['response']['usage'].get('output_tokens',0) for z in responses),new_training=False)
  atomic(OUT/'RESULTS.json',result);atomic(OUT/'STATUS.json',result)
  try:score()
  except BaseException as ex:atomic(OUT/'SCORING_ERROR.json',dict(error=type(ex).__name__+':'+str(ex),generation_state_preserved=True))
  lock.close();print(json.dumps(result),flush=True)

if __name__=='__main__':
  p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run','score']);args=p.parse_args();{'prepare':prepare,'run':run,'score':score}[args.command]()
