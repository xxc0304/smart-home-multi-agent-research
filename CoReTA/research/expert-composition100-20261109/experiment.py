"""Fixed 100 tasks + 56 repeated seeds: all-adapter private/discussion vs stored mixed teams."""
import copy,hashlib,json,os,sys,tempfile,time,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT/'tools'))
from b1_controls import Trial,vote,vote_scores
from b0_answers import answer_score
from b1_runtime import validate_runtime
from b1_multi_backend import MultiBackend
ACTORS=('M1','M2','M3','M4');ARMS=('A','B')
load=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.tmp')
 with tmp.open('w',encoding='utf-8') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
 os.replace(tmp,p)

def append(p,v):
 with Path(p).open('a',encoding='utf-8') as f:f.write(json.dumps(v,ensure_ascii=False,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())

class Team(Trial):
 def __init__(self,e,fixture=False):
  cfg=dict(e['trial_config'],fixture=fixture);super().__init__(e['task'],**cfg);self.entry=e
  self.schedule=[s for s in self.schedule if s[0]=='initial' or s[1] in ARMS]
 def next_request(self):
  r=super().next_request()
  if r is None:return None
  self.pending['seed']=self.base_seed+(0 if r['stage']=='initial' else 1000+r['round']*100 if r['stage']=='work' else 2000)+ACTORS.index(r['actor'])+self.entry['rep']*100000000
  self.pending['request_id']=f'{self.task["id"]}/composition/r{self.entry["rep"]}/{self.cursor:02d}'
  return copy.deepcopy(self.pending)
 @property
 def complete(self):return not self.initial_failed and not self.failed and all(len(self.finals[a])==4 for a in ARMS)

def source(e):
 t=load(ROOT/e['source_path'])
 rows=t['initial_records']+[r for a in ARMS for r in t['branches'].get(a,{}).get('records',[])] if 'initial_records' in t else [r for r in t['records'] if r['stage']=='initial' or r['arm'] in ARMS]
 return {(r['actor'],r['stage'],r['arm'],r['round']):r for r in rows}

def equal(r,z):return all(r[k]==z[k] for k in ['actor','stage','arm','round','seed','max_new_tokens','payload'])

def freeze():
 c=load(HERE/'config.json');entries=load(HERE/'INPUTS.json')['units']
 files=[HERE/n for n in ['experiment.py','launch.py','INPUTS.json','LABELS.json','config.json','DESIGN.md','EXPERIMENT_REVIEW.md']]
 files += [ROOT/e['source_path'] for e in entries]
 files += [ROOT/'tools'/n for n in ['b1_controls.py','b1_runtime.py','b1_multi_backend.py','b0_answers.py','b0_training.py','b1_stop_status.py','b1_output_contract.py','expert_mechanism_protocol.py','prepare_answer_only_expert.py','prepare_expert_training.py']]
 files += [ROOT/'research/musique-data-preparation-20261030/official_scorer/metrics/answer.py']
 files += [Path(c['adapter_path'])/n for n in ['adapter_config.json','adapter_model.safetensors','b0_origin.json']]
 files += [Path(c[k]) for k in ['baseline_C_score','expert_C_score']]
 files += [ROOT/'implement-stage/expert-answer-only-20261101/C_GROUPS.json',ROOT/'research/b1-grounded-revision-20261107/SELECTION_REVIEW.json',ROOT/'research/b1-grounded-revision-20261107/QUALITY_DECISIONS.json']
 return {str(p):sha(p) for p in dict.fromkeys(files)}

def score(e,t,labels):
 result=dict(unit=e['unit'],id=e['id'],rep=e['rep'],cohort=e['cohort'],group=e['group'],strict=e['strict'],complete=t.complete,initial={},arms={})
 if len(t.initials)==4:result['initial']={a:answer_score(v,labels[e['id']]) for a,v in t.initials.items()}
 for arm in ARMS:
  if arm in t.failed or len(t.finals[arm])!=4:result['arms'][arm]=dict(complete=False);continue
  members={a:answer_score(v,labels[e['id']]) for a,v in t.finals[arm].items()};v=vote(t.finals[arm],t.base_seed+1001)
  result['arms'][arm]=dict(complete=True,members=members,finals=t.finals[arm],vote=v,**vote_scores(v,labels[e['id']]),M1_em=members['M1']['em'])
 return result

def execute(entries,provider,out,fixture=False,save_freeze=True):
 out.mkdir(parents=True,exist_ok=False)
 if save_freeze:write(out/'manifest.json',dict(config=load(HERE/'config.json'),freeze=freeze(),units=len(entries),unique_tasks=len({e['id'] for e in entries}),maximum_logical_calls=28*len(entries),adapter_route='ALL_FOUR_ENABLED',scope='DEVELOPMENT_COMPOSITION_CONTROL_NOT_METHOD_CONFIRMATION'))
 for n in ['attempts.jsonl','responses.jsonl']:(out/n).touch()
 labels=load(HERE/'LABELS.json')['targets'];start=time.monotonic();calls=new=reused=done=0;scores=[];failure=None
 def state(status,**kw):write(out/'STATUS.json',dict(status=status,calls=calls,new_calls=new,reused_calls=reused,processed_units=done,total_units=len(entries),complete_units=sum(s['complete'] for s in scores),elapsed_seconds=time.monotonic()-start,**kw))
 state('STARTING')
 try:
  for e in entries:
   t=Team(e,fixture=fixture);idx=source(e)
   while (r:=t.next_request()) is not None:
    old=idx.get((r['actor'],r['stage'],r['arm'],r['round'])) if r['actor']=='M1' else None
    if r['actor']=='M1' and r['stage']=='initial':assert old and old['status']=='OK' and equal(r,old),'M1_INITIAL_EXACT_REQUIRED'
    if old and old['status']=='OK' and r['arm']=='A':assert equal(r,old),'M1_PRIVATE_EXACT_REQUIRED'
    cached=old if old and old['status']=='OK' and equal(r,old) else None
    attempt=dict(call=calls,unit=e['unit'],request=r,reused=cached is not None,backend_actor='M1',all_members_adapter=True,source_path=e['source_path'] if cached else None,source_request_id=cached['request_id'] if cached else None)
    append(out/'attempts.jsonl',attempt)
    if cached:z={k:cached[k] for k in ['raw_output','status','usage']};reused+=1
    else:
     z=provider(r,e);new+=1
     if z['status']=='OK' and (not isinstance(z['raw_output'],str) or not z['raw_output'].strip()):z=dict(z,status='EMPTY_OR_NON_TEXT')
    rec=t.submit(r['request_id'],z['raw_output'],status=z['status'],usage=z['usage'],source_kind=None if fixture else 'ACTUAL_LOCAL_MODEL_RESPONSE')
    row=dict(rec,call=calls,unit=e['unit'],reused=cached is not None,backend_actor='M1',all_members_adapter=True,source_path=attempt['source_path'],source_request_id=attempt['source_request_id'])
    append(out/'responses.jsonl',row);calls+=1
    assert calls<=4368 and new<=3747
    write(out/'trials'/f'{e["unit"]:03d}.json',t.export());state('RUNNING',task_id=e['id'],rep=e['rep'],unit=e['unit'],actor=r['actor'],stage=r['stage'],arm=r['arm'])
   scores.append(score(e,t,labels));write(out/'scores.json',scores);done+=1;state('RUNNING',unit=e['unit'])
 except BaseException as exc:failure=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
 state('STOPPED_SYSTEM_FAULT' if failure else 'COMPLETED' if all(s['complete'] for s in scores) else 'COMPLETED_WITH_INCOMPLETE_UNITS',failure=failure)
 return load(out/'STATUS.json')

def preflight():
 from b0_training import load_tokenizer
 c=load(HERE/'config.json');pack=load(HERE/'INPUTS.json');entries=pack['units'];qualification=validate_runtime(c)['qualification'];tok=load_tokenizer(c)
 assert len(entries)==156 and len({e['id'] for e in entries})==100 and sum(e['rep']==1 for e in entries)==56
 assert len({e['group'] for e in entries if e['cohort']=='fresh'})==46
 oldc=load(ROOT/'runs/b1-grounded-revision-20261107-v1/config.json')
 for run in ['b1-grounded-revision-20261107-v1','b1-stage-advantage-seed1-20261107-v1']:
  for p,h in load(ROOT/'runs'/run/'FREEZE.json')['files'].items():assert sha(p)==h,('historical_freeze_changed',p)
 for k in ['seed','generation','adapter_path','model_path','revision','dtype','quantization','max_length','template_kwargs','answer_tokens','answer_suffix','work_tokens','output_contract']:assert c[k]==oldc[k],k
 for e in entries:
  assert set(e['task'])=={'id','question','paragraphs'} and all(set(p)=={'idx','title','paragraph_text'} for p in e['task']['paragraphs'])
  idx=source(e);assert idx[('M1','initial',None,0)]['status']=='OK'
 # REAL full responses in state-machine replay, not generated expert outcomes.
 maximum=pressure=0;guaranteed=0;source_checks=0;replayed=0
 all_real=[r for e in entries for r in source(e).values() if r['status']=='OK']
 long_work=max((r for r in all_real if r['stage']=='work'),key=lambda r:r['usage']['output_tokens'])
 long_initial=max((r for r in all_real if r['stage']=='initial'),key=lambda r:r['usage']['output_tokens'])
 def length(r):
  ids=tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs']);n=len(ids)+r['max_new_tokens'];assert n<=c['max_length'],('overlength',r['request_id'],n);return n
 for e in entries:
  idx=source(e)
  for mode in ['actual','long_history']:
   t=Team(e,True)
   while (r:=t.next_request()) is not None:
    z=idx.get((r['actor'],r['stage'],r['arm'],r['round']))
    if mode=='actual' and z:
     assert equal(r,z);source_checks+=1
    n=length(r)
    if mode=='actual':maximum=max(maximum,n)
    else:pressure=max(pressure,n)
    zz=z if mode=='actual' and z and z['status']=='OK' else long_work if r['stage']=='work' else long_initial
    t.submit(r['request_id'],zz['raw_output'],usage=zz['usage']);replayed+=1
   assert t.complete
  guaranteed+=sum(r['actor']=='M1' and (r['stage']=='initial' or r['arm']=='A') and r['status']=='OK' for r in idx.values())
 assert guaranteed==621 and source_checks>=4300
 tests=[]
 for mode in ['valid','empty_initial','limit_A','limit_B','input_limit_A','semantic_unknown','system']:
  count=0
  def provider(r,e):
   nonlocal count
   count+=1
   if mode=='system':raise RuntimeError('FIXTURE_SYSTEM')
   z=copy.deepcopy(long_work if r['stage']=='work' else long_initial)
   if mode=='semantic_unknown':z['raw_output']='No determinate answer.'
   if mode=='empty_initial' and count==1:z['raw_output']=''
   if mode=='limit_A' and r['arm']=='A' and count==4:z['status']='OUTPUT_LIMIT'
   if mode=='input_limit_A' and r['arm']=='A' and count==4:z['status']='INPUT_LIMIT'
   if mode=='limit_B' and r['arm']=='B' and count==13:z['status']='OUTPUT_LIMIT'
   return {k:z[k] for k in ['raw_output','status','usage']}
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'fixture';st=execute(entries[:2],provider,out,True,False)
   if mode=='system':assert st['status']=='STOPPED_SYSTEM_FAULT' and st['processed_units']==0
   elif mode=='empty_initial':assert st['processed_units']==2 and st['complete_units']==1
   elif mode in ['limit_A','input_limit_A']:
    ss=load(out/'scores.json');assert not ss[0]['arms']['A']['complete'] and ss[0]['arms']['B']['complete'] and ss[1]['complete']
   elif mode=='limit_B':
    ss=load(out/'scores.json');assert ss[0]['arms']['A']['complete'] and not ss[0]['arms']['B']['complete'] and ss[1]['complete']
   else:assert st['complete_units']==2
  tests.append(dict(mode=mode,result='PASS'))
 # A cache request mismatch must never be accepted.
 e=entries[0];t=Team(e,True);r=t.next_request();z=copy.deepcopy(source(e)[('M1','initial',None,0)]);assert equal(r,z);z['seed']+=1;assert not equal(r,z)
 tests.append(dict(mode='cache_mismatch_rejected',result='PASS'))
 result=dict(result='PASS',qualification=qualification,logical_requests=4368,max_new_calls=3747,guaranteed_cached_requests=guaranteed,real_replay_and_pressure_requests=replayed,source_requests_exactly_reconstructed=source_checks,max_real_input_plus_cap=maximum,max_pressure_input_plus_cap=pressure,tests=tests,freeze=freeze(),no_new_generations=True)
 write(HERE/'PREFLIGHT.json',result);print(json.dumps({k:v for k,v in result.items() if k!='freeze'}),flush=True)

def audit():
 from b0_training import load_tokenizer
 c=load(HERE/'config.json');out=ROOT/c['run_dir'];entries=load(HERE/'INPUTS.json')['units'];assert freeze()==load(HERE/'FREEZE.json')==load(out/'manifest.json')['freeze']
 def read(p):
  s=Path(p).read_text(encoding='utf-8');return [json.loads(x) for x in s[:s.rfind('\n')+1].splitlines()]
 rows=read(out/'responses.jsonl');attempts=read(out/'attempts.jsonl');cursor=0
 def provider(r,e):
  nonlocal cursor
  while cursor<len(rows) and rows[cursor]['reused']:cursor+=1
  if cursor>=len(rows):raise EOFError('AUDIT_PREFIX_END')
  z=rows[cursor];assert z['unit']==e['unit'] and all(z[k]==v for k,v in r.items()),('request_diff',cursor)
  cursor+=1;return {k:z[k] for k in ['raw_output','status','usage']}
 with tempfile.TemporaryDirectory() as tmp:
  dst=Path(tmp)/'audit';st=execute(entries,provider,dst,False,False);rr=read(dst/'responses.jsonl');assert len(rr)>=len(rows)
  for a,b in zip(rows,rr):assert a==b,('replay_diff',a['call'])
  original_scores=load(out/'scores.json') if (out/'scores.json').exists() else []
  replay_scores=load(dst/'scores.json') if (dst/'scores.json').exists() else []
  assert original_scores==replay_scores[:len(original_scores)]
  if load(out/'STATUS.json')['status'].startswith('COMPLETED'):assert st['status'].startswith('COMPLETED') and len(rr)==len(rows)
 tok=load_tokenizer(c);maximum=0
 for i,r in enumerate(rows):
  at=attempts[i];assert at['call']==r['call']==i and at['unit']==r['unit'] and at['reused']==r['reused']
  assert all(r[k]==v for k,v in at['request'].items())
  u=r['usage'];ids=tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs'])
  assert len(ids)==u['input_tokens'];maximum=max(maximum,len(ids)+r['max_new_tokens'])
  if u.get('host_no_generation'):
   assert r['status']=='INPUT_LIMIT' and len(ids)+r['max_new_tokens']>c['max_length'] and r['raw_output'] is None and u['output_tokens']==0
   continue
  assert len(ids)+r['max_new_tokens']<=c['max_length']
  assert len(u['output_ids'])==u['output_tokens']<=r['max_new_tokens'] and tok.decode(u['output_ids'],skip_special_tokens=True)==r['raw_output']
  assert u['adapter_enabled'] is True and u['lora_layers']==252 and u['disabled_layers']==0 and u['batch_size']==1
 result=dict(result='PASS',responses_checked=len(rows),new_calls=sum(not r['reused'] for r in rows),complete_scores_replayed=len(original_scores),full_requests_histories_seeds_tokens_and_all_adapter_routes=True,max_input_plus_cap=maximum,non_ok=sum(r['status']!='OK' for r in rows),freeze_unchanged=True)
 write(HERE/'RUN_AUDIT.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='freeze':write(HERE/'FREEZE.json',freeze())
 elif mode=='preflight':preflight()
 elif mode=='audit':audit()
 elif mode=='run':
  import fcntl,math
  c=load(HERE/'config.json');assert freeze()==load(HERE/'FREEZE.json')==load(HERE/'PREFLIGHT.json')['freeze'];assert load(HERE/'PREFLIGHT.json')['result']=='PASS'
  assert 'RUN_ALLOWED' in (HERE/'EXPERIMENT_REVIEW.md').read_text(encoding='utf-8')
  lock=(HERE/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);out=ROOT/c['run_dir'];assert not out.exists()
  try:backend=MultiBackend(c)
  except BaseException as exc:write(HERE/'STARTUP_FAILURE.json',dict(type=type(exc).__name__,message=str(exc)));raise
  write(HERE/'BACKEND.json',dict(generation_config=backend.generation_config.to_dict(),all_four_expert_instances_same_adapter=True))
  def provider(r,e):
   # actor here controls ONLY adapter dispatch; payload retains the real M1/M2/M3/M4 identity.
   ids=backend.tokenizer.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs'])
   if len(ids)+r['max_new_tokens']>c['max_length']:
    return dict(raw_output=None,status='INPUT_LIMIT',usage=dict(input_tokens=len(ids),output_tokens=0,output_ids=[],host_no_generation=True))
   dispatched=dict(r,actor='M1');z=backend.respond_many([dispatched],math.inf)[0]
   u=z['usage'];assert u['adapter_enabled'] is True and u['lora_layers']==252 and u['disabled_layers']==0 and u['batch_size']==1
   return z
  result=execute(load(HERE/'INPUTS.json')['units'],provider,out);print(json.dumps(result),flush=True)
