"""Fixed32 early sharing experiment. No retries, wall cutoff, training or expansion."""
import copy, hashlib, json, math, os, random, signal, sys, tempfile, time, traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from b1_controls import vote, vote_scores, WORK, FINAL
from b1_runtime import validate_runtime
from b1_multi_backend import MultiBackend
from b0_answers import answer_score
from expert_mechanism_protocol import validate_task
from prepare_answer_only_expert import SYSTEM as INITIAL
ACTORS=('M1','M2','M3','M4'); ARMS=('A','B','C')
EXPLAIN=('Solve the question independently using only the supplied passages and your earlier answer. '
 'Give a brief explanation of your best candidate, identifying the requested entity or relation and '
 'the passage facts that support it. Cite paragraph indices when useful. If evidence is missing or '
 'contradictory, state that. Your earlier answer may be wrong. Write at most 220 words in natural language.')
load=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.tmp')
 with q.open('w',encoding='utf-8') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
 os.replace(q,p)
def append(p,v):
 with Path(p).open('a',encoding='utf-8') as f:f.write(json.dumps(v,ensure_ascii=False,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
def jsonlines(p):
 s=Path(p).read_text(encoding='utf-8');return [json.loads(z) for z in s[:s.rfind('\n')+1].splitlines()]
def seed_of(e):return 20261102+e['index']*10000+500000000+e['rep']*100000000
def orders(e):
 rng=random.Random(20261102+e['index']*10000)
 return rng.sample(list(ACTORS),4),[rng.sample(list(ACTORS),4) for _ in range(2)]
def packet(e,a,stage,arm,round_no,initials,explanation,candidate,history):
 c=load(HERE/'config.json');data={k:copy.deepcopy(e['task'][k]) for k in ['question','paragraphs']}
 if stage!='initial':data['own_actor']=a
 if stage in ('explanation','candidate'):
  data['history']=[dict(sender='M1',phase='initial',text=initials['M1'])]
  data['work_visibility']='private_work'
  if stage=='candidate':data['own_private_explanation']=explanation
 elif stage in ('work','final'):
  io,_=orders(e);data['history']=[dict(sender=k,phase='initial',text=initials[k]) for k in io]+copy.deepcopy(history)
  data['work_visibility']='team_message' if stage=='work' else 'private_final'
  if a=='M1':data['own_private_explanation']=explanation;data['own_private_candidate']=candidate
  data['additional_peer_records']=[]
  if a!='M1' and arm in ('B','C'):
   data['additional_peer_records']=[dict(sender='M1',phase='independent_candidate',text=candidate)]
   if arm=='C':data['additional_peer_records'].append(dict(sender='M1',phase='independent_explanation',text=explanation))
 system=INITIAL if stage=='initial' else EXPLAIN if stage=='explanation' else FINAL if stage in ('candidate','final') else WORK
 cap=1024 if stage in ('explanation','work') else 256
 offset=0 if stage=='initial' else 10000 if stage=='explanation' else 20000 if stage=='candidate' else 1000+round_no*100 if stage=='work' else 2000
 return dict(unit=e['unit'],id=e['id'],index=e['index'],rep=e['rep'],stratum=e['stratum'],actor=a,arm=arm,stage=stage,round=round_no,seed=seed_of(e)+offset+ACTORS.index(a),max_new_tokens=cap,adapter_enabled=a=='M1',payload=dict(system=system,user='TASK_DATA\n'+json.dumps(data,ensure_ascii=False,indent=2)+(c['answer_suffix'] if stage in ('initial','candidate','final') else '')))
def unit(e,provider):
 initials={};explanation=None;candidate=None;finals={};failures={};io,wo=orders(e)
 def call(a,stage,arm=None,r=0,history=[]):return provider(packet(e,a,stage,arm,r,initials,explanation,candidate,history))
 common_ok=True
 for a in ACTORS:
  z=call(a,'initial')
  if z['status']!='OK':common_ok=False;failures['common']=dict(stage='initial',actor=a,status=z['status']);break
  initials[a]=z['raw_output']
 if common_ok:
  z=call('M1','explanation')
  if z['status']!='OK':common_ok=False;failures['common']=dict(stage='explanation',status=z['status'])
  else:explanation=z['raw_output']
 if common_ok:
  z=call('M1','candidate')
  if z['status']!='OK':common_ok=False;failures['common']=dict(stage='candidate',status=z['status'])
  else:candidate=z['raw_output']
 if common_ok:
  permutation=[('A','B','C'),('B','C','A'),('C','A','B'),('C','B','A'),('B','A','C'),('A','C','B')][e['unit']%6]
  for arm in permutation:
   history=[];finals[arm]={};failed=False
   for rn,order in enumerate(wo,1):
    for a in order:
     z=call(a,'work',arm,rn,history)
     if z['status']!='OK':failures[arm]=dict(stage='work',round=rn,actor=a,status=z['status']);failed=True;break
     history.append(dict(sender=a,phase='work',round=rn,text=z['raw_output']))
    if failed:break
   if not failed:
    for a in ACTORS:
     z=call(a,'final',arm,3,history)
     if z['status']!='OK':failures[arm]=dict(stage='final',actor=a,status=z['status']);failed=True;break
     finals[arm][a]=z['raw_output']
 return dict(unit=e['unit'],id=e['id'],index=e['index'],rep=e['rep'],stratum=e['stratum'],common_complete=common_ok,initials=initials,explanation=explanation,candidate=candidate,finals=finals,failures=failures,orders=wo,initial_order=io)
def score(t):
 target=load(HERE/'LABELS.json')['targets'][t['id']];aux=load(HERE/'SCORING.json')['aliases'].get(str(t['index']),[])
 alt=dict(target,answer_aliases=target.get('answer_aliases',[])+aux)
 out={k:t[k] for k in ['unit','id','index','rep','stratum','common_complete','failures']};out['arms']={}
 out['initial']={a:answer_score(v,target) for a,v in t['initials'].items()}
 out['expert_candidate']=answer_score(t['candidate'],target) if t['candidate'] is not None else None
 for arm in ARMS:
  ans=t['finals'].get(arm,{})
  if len(ans)!=4 or arm in t['failures']:out['arms'][arm]=dict(complete=False);continue
  vs=vote(ans,20261102+t['index']*10000+1001)
  out['arms'][arm]=dict(complete=True,finals=ans,members={a:answer_score(v,target) for a,v in ans.items()},vote=vs,**vote_scores(vs,target),auxiliary=dict(members={a:answer_score(v,alt) for a,v in ans.items()},**vote_scores(vs,alt)))
 return out
def freeze():
 c=load(HERE/'config.json');names=['experiment.py','launch.py','config.json','INPUTS.json','LABELS.json','SCORING.json','SELECTION.json','DESIGN.md','MATERIAL_REVIEW.md','EXPERIMENT_REVIEW.md']
 files=[HERE/n for n in names]+[ROOT/'tools'/n for n in ['b1_controls.py','b1_runtime.py','b1_multi_backend.py','b0_answers.py','b0_training.py','b1_stop_status.py','b1_output_contract.py','expert_mechanism_protocol.py','prepare_answer_only_expert.py','prepare_expert_training.py']]
 files+=[ROOT/'research/musique-data-preparation-20261030/official_scorer/metrics/answer.py']
 files+=[Path(c['adapter_path'])/n for n in ['adapter_config.json','adapter_model.safetensors','b0_origin.json']]+[Path(c[k]) for k in ['baseline_C_score','expert_C_score']]
 files+=[ROOT/p for p in load(HERE/'INPUTS.json')['sources']]
 return {str(p):sha(p) for p in dict.fromkeys(files)}
def preflight():
 from b0_training import load_tokenizer
 c=load(HERE/'config.json');entries=load(HERE/'INPUTS.json')['entries'];tok=load_tokenizer(c);q=validate_runtime(c)
 assert len(entries)==64 and len({e['id'] for e in entries})==32 and len({e['group'] for e in entries})==32
 for e in entries:validate_task(e['task']);assert set(e['task'])=={'id','question','paragraphs'}
 cache={}
 def old(e):
  if e['index'] not in cache:
   t=load(ROOT/e['source_path']);rr=t['initial_records']+[r for r in t['branches']['B']['records']];cache[e['index']]={(r['actor'],r['stage'],r['round']):r for r in rr}
  return cache[e['index']]
 def length(r):return len(tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ['system','user']],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs']))
 saved=[];maxlen=0;longest=None
 for e in entries:
  for z in old(e).values():
   if z['stage']=='work' and z['status']=='OK' and (longest is None or z['usage']['output_tokens']>longest['usage']['output_tokens']):longest=z
 for e in entries:
  def replay(r):
   nonlocal maxlen
   rr=old(e);key=('M1','work',1) if r['stage']=='explanation' else ('M1','final',3) if r['stage']=='candidate' else (r['actor'],r['stage'],r['round'])
   z=rr[key];assert z['status']=='OK';n=length(r);maxlen=max(maxlen,n+r['max_new_tokens']);assert n+r['max_new_tokens']<=c['max_length']
   data=json.loads(r['payload']['user'][10:].split(c['answer_suffix'])[0])
   assert not any(k in data for k in ['gold','answer','correct','target','stratum','group'])
   if r['actor']!='M1' and r['stage'] in ('work','final'):
    p=data['additional_peer_records'];assert len(p)==({'A':0,'B':1,'C':2}[r['arm']])
    assert all(x['sender']=='M1' for x in p)
   saved.append(copy.deepcopy(r));return dict(raw_output=z['raw_output'],status=z['status'])
  t=unit(e,replay);assert t['common_complete'] and not t['failures'];score(t)
 assert len(saved)==2688
 # Counterfactual payload check before any branch messages can diverge.
 for e in entries:
  rs=[r for r in saved if r['unit']==e['unit'] and r['stage']=='work' and r['round']==1]
  for a in ACTORS:
   aa=[r for r in rs if r['actor']==a]
   assert len(aa)==3 and len({r['seed'] for r in aa})==1
   dd=[json.loads(r['payload']['user'][10:]) for r in aa]
   for x in dd:x.pop('additional_peer_records',None)
   # Historical replay supplies identical messages, so complete histories must match.
   assert dd[0]==dd[1]==dd[2]
 tests=[]
 for mode in ['initial_empty','explanation_limit','candidate_empty','branch_work_limit','branch_final_empty','missing_explanation_format','system','cancel','overlength']:
  calls=0
  def fixture(r):
   nonlocal calls
   calls+=1
   if mode=='system':raise RuntimeError('FIXTURE_SYSTEM')
   if mode=='cancel':raise InterruptedError('FIXTURE_CANCEL')
   z=dict(raw_output='Crawford County',status='OK')
   match=(mode=='initial_empty' and r['stage']=='initial') or (mode=='explanation_limit' and r['stage']=='explanation') or (mode=='candidate_empty' and r['stage']=='candidate') or (mode=='branch_work_limit' and r['arm']=='A' and r['stage']=='work') or (mode=='branch_final_empty' and r['arm']=='A' and r['stage']=='final') or (mode=='overlength' and r['arm']=='A' and r['stage']=='work')
   if match:z['status']='INPUT_OVERLENGTH' if mode=='overlength' else 'OUTPUT_LIMIT' if 'limit' in mode else 'EMPTY_OR_NON_TEXT';z['raw_output']=''
   return z
  try:
   t=unit(entries[0],fixture)
   if mode in ['system','cancel']:raise AssertionError('did not propagate')
   if mode.startswith(('initial','explanation','candidate')):assert not t['common_complete'] and calls<=6
   elif mode=='missing_explanation_format':assert calls==42 and not t['failures']
   else:assert 'A' in t['failures'] and len(t['finals']['B'])==len(t['finals']['C'])==4
  except (RuntimeError,InterruptedError):assert mode in ['system','cancel']
  tests.append(dict(mode=mode,result='PASS'))
 # Full real long response pressure: no text truncation; local isolation if cap would overflow.
 stressmax=0;isolated=0
 for e in entries:
  def stress(r):
   nonlocal stressmax,isolated
   n=length(r)+r['max_new_tokens'];stressmax=max(stressmax,n)
   if n>c['max_length']:isolated+=1;return dict(status='INPUT_OVERLENGTH',raw_output='')
   return dict(status='OK',raw_output=longest['raw_output'] if r['stage'] in ('work','explanation') else 'Crawford County')
  unit(e,stress)
 result=dict(result='PASS',qualification=q['qualification'],historical_full_requests=len(saved),max_historical_input_plus_cap=maxlen,stress_max_input_plus_cap=stressmax,stress_overlength_isolated=isolated,tests=tests,model_calls=0,freeze=freeze())
 write(HERE/'PREFLIGHT.json',result);print(json.dumps({k:v for k,v in result.items() if k!='freeze'}),flush=True)
def run():
 import fcntl
 c=load(HERE/'config.json');assert freeze()==load(HERE/'FREEZE.json')==load(HERE/'PREFLIGHT.json')['freeze'];assert load(HERE/'PREFLIGHT.json')['result']=='PASS' and 'RUN_ALLOWED' in (HERE/'EXPERIMENT_REVIEW.md').read_text()
 lock=(HERE/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 out=ROOT/c['run_dir'];out.mkdir(exist_ok=False);(out/'trials').mkdir();(out/'responses.jsonl').touch();(out/'attempts.jsonl').touch()
 write(out/'manifest.json',dict(config=c,freeze=freeze(),units=64,questions=32,max_new_calls=2688))
 state=dict(status='LOADING_MODEL',calls=0,generated_calls=0,processed_units=0,complete_units=0,total_units=64);start=time.monotonic();stopping=False;scores=[]
 def status(name,**kw):state.update(status=name,elapsed_seconds=time.monotonic()-start,**kw);write(out/'STATUS.json',state)
 status('LOADING_MODEL')
 def stop(sig,frame):
  nonlocal stopping
  stopping=True
 signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
 try:
  backend=MultiBackend(c)
  def provider(r):
   if stopping or (HERE/'STOP_REQUESTED').exists():raise InterruptedError('USER_STOP')
   r=dict(r,call=state['calls']);append(out/'attempts.jsonl',r)
   n=len(backend.tokenizer.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ['system','user']],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs']))
   if n+r['max_new_tokens']>c['max_length']:z=dict(raw_output='',status='INPUT_OVERLENGTH',origin='local_precheck',usage=dict(input_tokens=n,output_tokens=0))
   else:
    z=backend.respond_many([{k:r[k] for k in ['actor','seed','max_new_tokens','payload']}],math.inf)[0];z['origin']='model';u=z['usage']
    assert u['adapter_enabled']==r['adapter_enabled'] and u['disabled_layers']==(0 if r['actor']=='M1' else 252) and u['lora_layers']==252 and u['batch_size']==1
    if z['status']=='OK' and (not isinstance(z['raw_output'],str) or not z['raw_output'].strip()):z['status']='EMPTY_OR_NON_TEXT'
    state['generated_calls']+=1
   row=dict(r,**z);append(out/'responses.jsonl',row);state['calls']+=1;assert state['calls']<=2688
   status('RUNNING',unit=r['unit'],index=r['index'],rep=r['rep'],arm=r['arm'],actor=r['actor'],stage=r['stage']);return row
  for pos,e in enumerate(load(HERE/'INPUTS.json')['entries']):
   t=unit(e,provider);write(out/'trials'/f"{e['unit']:03d}.json",t);scores.append(score(t));write(out/'scores.json',scores)
   state['processed_units']+=1;state['complete_units']+=int(all(z['complete'] for z in scores[-1]['arms'].values()))
   if pos==1:
    status('WAITING_PREFIX_AUDIT');write(out/'PREFIX_CHECKPOINT.json',dict(calls=state['calls'],units=2))
    while not (HERE/'CONTINUE_CHECKED.json').exists():
     if stopping or (HERE/'STOP_REQUESTED').exists():raise InterruptedError('USER_STOP')
     time.sleep(.5)
  status('COMPLETED' if state['complete_units']==64 else 'COMPLETED_WITH_INCOMPLETE_UNITS')
 except InterruptedError as exc:status('CANCELLED_BY_USER',failure=str(exc))
 except BaseException as exc:status('STOPPED_SYSTEM_FAULT',failure=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()));raise
def audit():
 from b0_training import load_tokenizer
 c=load(HERE/'config.json');out=ROOT/c['run_dir'];assert freeze()==load(HERE/'FREEZE.json')==load(out/'manifest.json')['freeze'];tok=load_tokenizer(c)
 rows=jsonlines(out/'responses.jsonl');attempts=jsonlines(out/'attempts.jsonl');cursor=0;complete=0;maxlen=0
 class End(Exception):pass
 def replay(r):
  nonlocal cursor,maxlen
  if cursor==len(rows):raise End()
  z=rows[cursor];assert z['call']==cursor and all(z[k]==v for k,v in r.items()) and all(z[k]==v for k,v in attempts[cursor].items())
  n=len(tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ['system','user']],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs']));u=z['usage'];assert n==u['input_tokens'];maxlen=max(maxlen,n+r['max_new_tokens'])
  if z['origin']=='local_precheck':assert z['status']=='INPUT_OVERLENGTH' and n+r['max_new_tokens']>c['max_length'] and z['raw_output']==''
  else:
   assert n+r['max_new_tokens']<=c['max_length'] and len(u['output_ids'])==u['output_tokens']<=r['max_new_tokens'];assert tok.decode(u['output_ids'],skip_special_tokens=True)==z['raw_output']
   assert u['adapter_enabled']==(r['actor']=='M1') and u['lora_layers']==252 and u['disabled_layers']==(0 if r['actor']=='M1' else 252) and u['batch_size']==1
  cursor+=1;return z
 stored=load(out/'scores.json') if (out/'scores.json').exists() else []
 for e in load(HERE/'INPUTS.json')['entries']:
  try:t=unit(e,replay)
  except End:break
  p=out/'trials'/f"{e['unit']:03d}.json"
  if p.exists():assert load(p)==t and score(t)==stored[complete];complete+=1
 assert cursor==len(rows)
 result=dict(result='PASS',responses_checked=cursor,generated_calls=sum(z['origin']=='model' for z in rows),complete_unit_scores_reconstructed=complete,non_ok=sum(z['status']!='OK' for z in rows),max_input_plus_cap=maxlen,freeze_unchanged=True,full_actual_payload_history_seed_token_adapter_reconstruction=True)
 write(HERE/'RUN_AUDIT.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='freeze':write(HERE/'FREEZE.json',freeze())
 elif mode=='preflight':preflight()
 elif mode=='run':run()
 elif mode=='audit':audit()
