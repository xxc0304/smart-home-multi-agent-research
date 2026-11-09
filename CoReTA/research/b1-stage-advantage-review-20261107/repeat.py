"""Same56, four unchanged controls, fixed original order, one new generation seed."""
import argparse,copy,hashlib,json,os,sys,time,traceback,fcntl
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];os.chdir(ROOT);sys.path.insert(0,str(ROOT/'tools'))
from b1_controls import Trial,vote,vote_scores
from b1_runtime import validate_runtime
from b1_multi_backend import MultiBackend
from b0_answers import answer_score
OUT=ROOT/'runs/b1-stage-advantage-seed1-20261107-v1'
load=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ARMS=('A','B','C','D');ACTORS=('M1','M2','M3','M4');OFFSET=100000000

def atomic(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.tmp')
 with q.open('w',encoding='utf-8') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
 os.replace(q,p)

def append(p,v):
 with Path(p).open('a',encoding='utf-8') as f:f.write(json.dumps(v,ensure_ascii=False,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())

class RepeatTrial(Trial):
 def __init__(self,e,fixture=False):
  cfg=copy.deepcopy(e['sourceConfig']);cfg['fixture']=fixture
  super().__init__(e['task'],**cfg)
  assert self.initial_order==e['initial_order'] and self.orders==e['orders']
 def next_request(self):
  r=super().next_request()
  if r is None:return None
  p=self.pending;stage=p['stage'];stage_seed=0 if stage=='initial' else 1000+p['round']*100 if stage=='work' else 2000
  p['seed']=self.base_seed+stage_seed+ACTORS.index(p['actor'])+OFFSET
  p['request_id']=f'{self.task["id"]}/newseed/{self.cursor:02d}'
  return copy.deepcopy(p)
 def export(self):
  d=super().export();d.update(protocol='B1_FOUR_ARM_FIXED_ORDER_NEW_GENERATION_SEED',generation_seed_offset=OFFSET,order_policy='ORIGINAL_FIXED')
  return d

def source_records(e):
 t=load(ROOT/e['sourcePath']);return t,t['initial_records']+[r for c in ARMS for r in t['branches'][c]['records']]

def validate_pack(pack):
 assert pack['generation_seed_offset']==OFFSET and len(pack['tasks'])==56 and len({e['id'] for e in pack['tasks']})==56
 assert sum(e['strict'] for e in pack['tasks'])==29 and len({e['group'] for e in pack['tasks']})==46
 for p,h in pack['source_sha256'].items():assert sha(p)==h
 for e in pack['tasks']:
  assert set(e['task'])=={'id','question','paragraphs'}
  t,rs=source_records(e);assert t['id']==e['id'] and len(rs)==52
  assert all(t['branches'][c]['complete'] for c in ARMS)
 return pack['tasks']

def score_saved():
 pack=load(OUT/'REPEAT_INPUTS.json');labels=load(OUT/'REPEAT_LABELS.json')['targets'];rows=[]
 for e in pack['tasks']:
  p=OUT/'trials'/f'{e["index"]:03d}.json';t=load(p) if p.exists() else None
  if not t:rows.append(dict(id=e['id'],index=e['index'],complete=False,not_started=True));continue
  # Rebuild exact custom state machine, not base replay which lacks seed offset.
  replay=RepeatTrial(e)
  for z in t['records']:
   req=replay.next_request();assert req and all(z[k]==v for k,v in req.items())
   replay.submit(req['request_id'],z['raw_output'],status=z['status'],usage=z['usage'],source_kind=z['source_kind'])
  assert replay.export()==t
  # score_trial accepts the reconstructed object; seed change leaves tie rule fixed.
  target=labels[e['id']];scored=dict(complete=replay.complete,initial=None,arms={})
  if len(replay.initials)==4:scored['initial']={a:answer_score(v,target) for a,v in replay.initials.items()}
  for arm in ARMS:
   if arm in replay.failed or len(replay.finals[arm])!=4:scored['arms'][arm]=dict(complete=False);continue
   members={a:answer_score(v,target) for a,v in replay.finals[arm].items()};v=vote(replay.finals[arm],replay.base_seed+1001)
   scored['arms'][arm]=dict(complete=True,members=members,vote=v,**vote_scores(v,target),expert_em=members['M1']['em'])
  rows.append(dict(id=e['id'],index=e['index'],group=e['group'],strict=e['strict'],**scored))
 result=dict(scope='SAME56_FIXED_ORDER_NEW_GENERATION_SEED_DEVELOPMENT_REPLICATION',rows=rows)
 atomic(OUT/'scores.json',result);return result

def tests():
 pack=load(HERE/'REPEAT_INPUTS.json');entries=validate_pack(pack);checks=[];count=0
 for e in entries:
  old,records=source_records(e);t=RepeatTrial(e,fixture=True)
  for z in records:
   req=t.next_request();assert req['payload']==z['payload'] and req['seed']==z['seed']+OFFSET and req['max_new_tokens']==z['max_new_tokens']
   assert req['actor']==z['actor'] and req['arm']==z['arm'] and req['stage']==z['stage']
   t.submit(req['request_id'],z['raw_output'],usage=z['usage'],source_kind='REAL_ORIGINAL_RESPONSE_REPLAY_FIXTURE');count+=1
  assert t.complete and len(t.records)==52 and t.next_request() is None
  assert t.initial_order==e['initial_order'] and t.orders==e['orders']
 checks+=['2912_real_full_response_replay_same_payload_and_order_only_generation_seed_changed','all56_task_ids_strata_groups_and_source_hashes','four_controls_and52_calls_per_item']
 e=entries[0];old,records=source_records(e);t=RepeatTrial(e,fixture=True)
 for i,z in enumerate(records):
  req=t.next_request()
  if req is None:break
  t.submit(req['request_id'],z['raw_output'],status='OUTPUT_LIMIT' if i==4 else 'OK',usage=z['usage'])
  if i==4:break
 assert 'A' in t.failed
 while (req:=t.next_request()) is not None:
  assert req['arm']!='A';t.submit(req['request_id'],'fixture output')
 assert len(t.finals['B'])==len(t.finals['C'])==len(t.finals['D'])==4
 checks+=['independent_arm_output_limit_skips_only_dependent_A_no_retry']
 t=RepeatTrial(e,fixture=True);q=t.next_request();t.submit(q['request_id'],'truncated',status='OUTPUT_LIMIT');assert t.initial_failed and t.next_request() is None
 checks+=['initial_failure_isolates_task','pending_request_is_idempotent']
 t=RepeatTrial(e,fixture=True);assert t.next_request()==t.next_request()
 atomic(HERE/'REPEAT_TESTS.json',dict(verdict='PASS',checks=checks,real_replayed_requests=count,fixture_only=True,new_model_calls=0,code_sha256=sha(HERE/'repeat.py')));print(json.dumps(load(HERE/'REPEAT_TESTS.json')),flush=True)

def prepare():
 from b0_training import load_tokenizer
 test=load(HERE/'REPEAT_TESTS.json');assert test['verdict']=='PASS' and test['code_sha256']==sha(HERE/'repeat.py')
 assert load(HERE/'REPEAT_SCIENCE.json')['verdict']=='PASS'
 pack=load(HERE/'REPEAT_INPUTS.json');entries=validate_pack(pack);config=load(HERE/'repeat_config.json');q=validate_runtime(config);tok=load_tokenizer(config)
 original=[]
 for e in entries:original+=source_records(e)[1]
 long_work=max((z for z in original if z['stage']=='work' and z['status']=='OK'),key=lambda z:z['usage']['output_tokens'])
 long_answer=max((z for z in original if z['stage']!='work' and z['status']=='OK'),key=lambda z:z['usage']['output_tokens'])
 lengths=[]
 for e in entries:
  for mode in ('original_replay','long_real_response_pressure'):
   t=RepeatTrial(e,fixture=True);source=source_records(e)[1]
   for i in range(52):
    req=t.next_request();assert req
    n=len(tok.apply_chat_template([dict(role=k,content=req['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**config['template_kwargs']))
    assert n+req['max_new_tokens']<=config['max_length'],('context',e['index'],mode,i,n)
    z=source[i] if mode=='original_replay' else long_work if req['stage']=='work' else long_answer
    t.submit(req['request_id'],z['raw_output'],usage=z['usage'],source_kind='REAL_RESPONSE_PRESSURE_FIXTURE')
    lengths.append(dict(index=e['index'],mode=mode,cursor=i,input_plus_cap=n+req['max_new_tokens']))
   assert t.complete
 OUT.mkdir(exist_ok=False);(OUT/'trials').mkdir()
 for n in ('REPEAT_INPUTS.json','REPEAT_LABELS.json','repeat_config.json','REPEAT_BUDGET.json'):(OUT/n).write_bytes((HERE/n).read_bytes())
 atomic(OUT/'LENGTHS.json',lengths);atomic(OUT/'PREFLIGHT.json',dict(science='PASS',engineering='PASS',qualification=q['qualification'],real_replay_and_pressure_requests=len(lengths),max_input_plus_cap=max(x['input_plus_cap'] for x in lengths),context=config['max_length'],new_model_calls=0))
 files=[HERE/n for n in ('repeat.py','repeat_launch.py','REPEAT_INPUTS.json','REPEAT_LABELS.json','repeat_config.json','REPEAT_BUDGET.json','REPEAT_TESTS.json','REPEAT_SCIENCE.json','REPEAT_EXPERIMENT_REVIEW.md','rules.json')]
 files += [ROOT/'tools'/n for n in ('b1_controls.py','b1_runtime.py','b1_multi_backend.py','b0_training.py','b0_answers.py','b1_stop_status.py','b1_output_contract.py','expert_mechanism_protocol.py','prepare_answer_only_expert.py')]
 files += [Path(p) for p in pack['source_sha256']]
 files += [Path(config['adapter_path'])/n for n in ('adapter_config.json','adapter_model.safetensors','b0_origin.json')]
 files += [OUT/n for n in ('REPEAT_INPUTS.json','REPEAT_LABELS.json','repeat_config.json','REPEAT_BUDGET.json','LENGTHS.json','PREFLIGHT.json')]
 atomic(OUT/'FREEZE.json',dict(files={str(p):sha(p) for p in dict.fromkeys(files)}));atomic(OUT/'STATUS.json',dict(status='PREPARED_NOT_LAUNCHED',completed_tasks=0,planned_tasks=56,returned=0));print(json.dumps(load(OUT/'PREFLIGHT.json')),flush=True)

def verify_freeze():
 assert all(sha(p)==h for p,h in load(OUT/'FREEZE.json')['files'].items())

def run():
 verify_freeze();pf=load(OUT/'PREFLIGHT.json');assert pf['science']==pf['engineering']=='PASS'
 lock=(OUT/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);(OUT/'STARTED').touch(exist_ok=False)
 started=time.monotonic();pack=load(OUT/'REPEAT_INPUTS.json');entries=validate_pack(pack);config=load(OUT/'repeat_config.json');done=0;returned=0;attempts=0;outputs=0;technical=[]
 try:
  backend=MultiBackend(config)
  for e in sorted(entries,key=lambda e:e['index']):
   t=RepeatTrial(e)
   while (req:=t.next_request()) is not None:
    append(OUT/'ATTEMPTS.jsonl',dict(event='START',index=e['index'],request=req));attempts+=1
    try:res=backend.respond_many([req],1e12)[0]
    except ValueError as exc:
     if str(exc)!='overlength_no_truncation':raise
     res=dict(raw_output='',status='INPUT_LIMIT',usage=None)
    returned+=1;u=res['usage']
    if u:
     assert u['lora_layers']==252 and u['disabled_layers']==(0 if req['actor']=='M1' else 252)
     assert u['batch_size']==1 and u['adapter_enabled']==(req['actor']=='M1')
     outputs+=u['output_tokens']
    if res['status']!='OK':technical.append(dict(index=e['index'],id=req['request_id'],status=res['status']))
    rec=t.submit(req['request_id'],res['raw_output'],status=res['status'],usage=u,source_kind='ACTUAL_LOCAL_MODEL_RESPONSE')
    append(OUT/'responses.jsonl',rec);append(OUT/'ATTEMPTS.jsonl',dict(event='RETURN',index=e['index'],request_id=req['request_id'],status=rec['status']))
    atomic(OUT/'trials'/f'{e["index"]:03d}.json',t.export())
    atomic(OUT/'STATUS.json',dict(status='RUNNING',completed_tasks=done,planned_tasks=56,current_index=e['index'],attempts=attempts,returned=returned,output_tokens=outputs,seconds=time.monotonic()-started,technical=technical))
   done+=1
   if done in (1,2,8,16,32,48,56):score_saved()
  score_saved();verify_freeze();atomic(OUT/'STATUS.json',dict(status='COMPLETE',completed_tasks=done,planned_tasks=56,attempts=attempts,returned=returned,output_tokens=outputs,seconds=time.monotonic()-started,technical=technical));print(json.dumps(load(OUT/'STATUS.json')),flush=True)
 except Exception as exc:
  atomic(OUT/'STATUS.json',dict(status='SYSTEM_ERROR',completed_tasks=done,planned_tasks=56,attempts=attempts,returned=returned,output_tokens=outputs,seconds=time.monotonic()-started,type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),technical=technical));raise

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['tests','prepare','run']);args=parser.parse_args();{'tests':tests,'prepare':prepare,'run':run}[args.action]()
