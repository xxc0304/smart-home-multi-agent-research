"""Four-task matched evidence-use probe: 8 units, two arms, at most128 new calls."""
import copy,importlib.util,json,math,os,re,signal,sys,tempfile,time,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('visibility',HERE.parent/'expert-final-visibility-design-20261109/build_design.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
b=d.b;load,write,append,sha=b.load,b.write,b.append,b.sha
ACTORS=b.ACTORS;ARMS=['A_private_review','B_peer_review']
SYSTEM='Review the supplied benchmark question using only its passages and visible records. Your earlier answer and other participants\' answers may be wrong. Assess candidates against the question and passages. Give a brief, checkable review.'
REVIEW='''Perform the following checks in at most 220 words total.
NEW RECORDS: List each newly provided sender and copy their answer exactly, using M1: ..., M2: ..., etc. If there are no new peer records, write NONE. Do not invent new records from the earlier discussion.
EVIDENCE CHECK: State the entity or relation the question asks for. Give up to three brief exact quotations, each at most 20 words, identifying the paragraph index as [P0], [P1], etc. Explain briefly whether those passages support or conflict with the candidate answers. If the supplied evidence is insufficient, say so.
DECISION: Retain or revise your earlier answer based on that evidence. You are not required to follow any participant or a majority. End with CURRENT ANSWER: followed by your best short answer.'''

def make_request(e,a,arm,stage,review=None):
 idx=b.source(e);old=idx[(a,'final','B',3)];suffix=e['trial_config']['answer_suffix']
 data=json.loads(old['payload']['user'][10:-len(suffix)])
 data['work_visibility']='private_review';data['own_sealed_answer']=old['raw_output']
 data['new_peer_records']=[] if arm==ARMS[0] else [dict(sender=k,text=idx[(k,'final','B',3)]['raw_output']) for k in ACTORS if k!=a]
 if stage=='review':system=SYSTEM;ending='\n\n'+REVIEW;cap=512;offset=300000000
 else:
  assert isinstance(review,str) and review.strip();data['own_private_review']=review
  system='Give only your final short answer to the question, using the supplied material and your review.';ending=suffix;cap=256;offset=400000000
 return dict(unit=e['unit'],task_id=e['id'],index=e['source_index'],rep=e['rep'],actor=a,arm=arm,stage=stage,seed=old['seed']+offset,max_new_tokens=cap,adapter_enabled=a=='M1',payload=dict(system=system,user='TASK_DATA\n'+json.dumps(data,ensure_ascii=False,indent=2)+ending))

def data_of(r):
 ending='\n\n'+REVIEW if r['stage']=='review' else next(e for e in load(HERE/'INPUTS.json')['entries'] if e['unit']==r['unit'])['trial_config']['answer_suffix']
 assert r['payload']['user'].endswith(ending);return json.loads(r['payload']['user'][10:-len(ending)])

def freeze():
 c=load(HERE/'config.json');entries=load(HERE/'INPUTS.json')['entries']
 files=[HERE/n for n in ['probe.py','launch.py','config.json','INPUTS.json','DESIGN.md','RUBRIC.md','EXPERIMENT_REVIEW.md']]
 files += [HERE.parent/'expert-final-visibility-design-20261109/build_design.py',HERE.parent/'expert-composition100-20261109/experiment.py',HERE.parent/'expert-composition100-20261109/LABELS.json']
 files += [ROOT/e['source_path'] for e in entries]
 files += [ROOT/'tools'/n for n in ['b1_controls.py','b1_runtime.py','b1_multi_backend.py','b0_answers.py','b0_training.py','b1_stop_status.py','b1_output_contract.py','expert_mechanism_protocol.py','prepare_answer_only_expert.py','prepare_expert_training.py']]
 files += [ROOT/'research/musique-data-preparation-20261030/official_scorer/metrics/answer.py']
 files += [Path(c['adapter_path'])/n for n in ['adapter_config.json','adapter_model.safetensors','b0_origin.json']]
 files += [Path(c[k]) for k in ['baseline_C_score','expert_C_score']]
 return {str(p):sha(p) for p in dict.fromkeys(files)}

def prepare():
 entries=load(HERE.parent/'expert-composition100-20261109/INPUTS.json')['units']
 order=[(6,1),(43,1),(17,1),(0,1),(6,0),(43,0),(17,0),(0,0)]
 selected=[next(e for e in entries if e['cohort']=='fresh' and (e['source_index'],e['rep'])==p) for p in order]
 for e in selected:assert all(b.source(e)[(a,'final','B',3)]['status']=='OK' for a in ACTORS)
 write(HERE/'INPUTS.json',dict(scope='PURPOSE_SELECTED4_TASKS_TWO_OLD_SEEDS_BEHAVIOR_PROBE_NOT_METHOD_CONFIRMATION',entries=selected,indices=[0,6,17,43],max_new_calls=128,max_output_cap=49152,no_auto_expansion=True))
 print(json.dumps(dict(entries=8,questions=4,max_calls=128)),flush=True)

def execute(entries,provider,out,fixture=False,stop_check=lambda:False):
 out.mkdir(parents=True,exist_ok=False)
 if not fixture:write(out/'manifest.json',dict(config=load(HERE/'config.json'),freeze=freeze(),questions=4,units=8,max_new_calls=128,purpose='BEHAVIOR_OBSERVABILITY_PROBE_NO_FORCED_ADOPTION'))
 for n in ['attempts.jsonl','responses.jsonl']:(out/n).touch()
 start=time.monotonic();rows=[];scores=[];done=0;failure=None;cancelled=False;labels=load(HERE.parent/'expert-composition100-20261109/LABELS.json')['targets']
 def status(state,**kw):write(out/'STATUS.json',dict(status=state,calls=len(rows),processed_units=done,complete_units=sum(all(s['arms'][a]['complete'] for a in ARMS) for s in scores),total_units=len(entries),elapsed_seconds=time.monotonic()-start,**kw))
 def call(r):
  if stop_check():raise InterruptedError('USER_STOP')
  attempt=dict(r,call=len(rows));append(out/'attempts.jsonl',attempt);z=provider(r)
  if z['status']=='OK' and (not isinstance(z['raw_output'],str) or not z['raw_output'].strip()):z=dict(z,status='EMPTY_OR_NON_TEXT')
  row=dict(attempt,**z);append(out/'responses.jsonl',row);rows.append(row);assert len(rows)<=128
  status('RUNNING',unit=r['unit'],index=r['index'],rep=r['rep'],arm=r['arm'],actor=r['actor'],stage=r['stage']);return row
 status('STARTING')
 try:
  for pos,e in enumerate(entries):
   arms=ARMS[pos%2:]+ARMS[:pos%2];reviews={};finals={}
   for arm in arms:
    reviews[arm]={};finals[arm]={}
    for a in ACTORS:reviews[arm][a]=call(make_request(e,a,arm,'review'))
    for a in ACTORS:
     if reviews[arm][a]['status']=='OK':finals[arm][a]=call(make_request(e,a,arm,'final',reviews[arm][a]['raw_output']))
   item=dict(unit=e['unit'],id=e['id'],index=e['source_index'],rep=e['rep'],arms={})
   for arm in ARMS:
    ok=len(finals[arm])==4 and all(z['status']=='OK' for z in finals[arm].values())
    if not ok:item['arms'][arm]=dict(complete=False);continue
    ans={a:z['raw_output'] for a,z in finals[arm].items()};seed=e['trial_config']['seed']+e['trial_config']['task_index']*10000+1001
    item['arms'][arm]=dict(complete=True,finals=ans,members={a:b.answer_score(z,labels[e['id']]) for a,z in ans.items()},**b.vote_scores(b.vote(ans,seed),labels[e['id']]))
   scores.append(item);write(out/'scores.json',scores);done+=1
   if pos==0 and not fixture:
    status('WAITING_FIRST_UNIT_AUDIT')
    write(out/'FIRST_UNIT_CHECKPOINT.json',dict(calls=len(rows),unit=e['unit'],index=e['source_index'],rep=e['rep']))
    while not (HERE/'CONTINUE_CHECKED.json').exists():
     if stop_check():raise InterruptedError('USER_STOP')
     time.sleep(.5)
   status('RUNNING',last_completed_unit=e['unit'])
 except InterruptedError as exc:cancelled=True;failure=dict(type=type(exc).__name__,message=str(exc))
 except BaseException as exc:failure=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
 status('CANCELLED_BY_USER' if cancelled else 'STOPPED_SYSTEM_FAULT' if failure else 'COMPLETED' if all(all(s['arms'][a]['complete'] for a in ARMS) for s in scores) else 'COMPLETED_WITH_INCOMPLETE_ARMS',failure=failure)
 return load(out/'STATUS.json')

def preflight():
 from b0_training import load_tokenizer
 c=load(HERE/'config.json');entries=load(HERE/'INPUTS.json')['entries'];tok=load_tokenizer(c);q=b.validate_runtime(c);maximum=0;requests=0
 old=[]
 for e in entries:old+=list(b.source(e).values())
 long_review=max((r for r in old if r['stage']=='work' and r['status']=='OK' and r['usage']['output_tokens']<=512),key=lambda r:r['usage']['output_tokens'])
 def length(r):
  ids=tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ['system','user']],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs']);assert len(ids)+r['max_new_tokens']<=c['max_length'];return len(ids)+r['max_new_tokens']
 for e in entries:
  for a in ACTORS:
   ra=make_request(e,a,ARMS[0],'review');rb=make_request(e,a,ARMS[1],'review')
   x,y=data_of(ra),data_of(rb);assert not x['new_peer_records'] and [p['sender'] for p in y['new_peer_records']]==[k for k in ACTORS if k!=a]
   del x['new_peer_records'];del y['new_peer_records'];assert x==y and ra['seed']==rb['seed'] and ra['payload']['system']==rb['payload']['system']
   assert not any(k in x for k in ['gold','target','correct','correct_answer'])
   for arm in ARMS:
    for r in [make_request(e,a,arm,'review'),make_request(e,a,arm,'final',long_review['raw_output']),make_request(e,a,arm,'final',' word'*512)]:maximum=max(maximum,length(r));requests+=1
 tests=[]
 for mode in ['actual_full_response_replay','missing_review_sections','empty','review_limit','system','cancel']:
  calls=0
  def provider(r):
   nonlocal calls
   calls+=1
   if mode=='system':raise RuntimeError('FIXTURE_SYSTEM')
   e=next(e for e in entries if e['unit']==r['unit']);z=long_review if r['stage']=='review' else b.source(e)[(r['actor'],'final','B',3)]
   z={k:copy.deepcopy(z[k]) for k in ['raw_output','status','usage']}
   if mode=='missing_review_sections' and r['stage']=='review':z['raw_output']='Crawford County'
   if mode=='empty' and calls==1:z['raw_output']=''
   if mode=='review_limit' and calls==1:z['status']='OUTPUT_LIMIT'
   return z
  with tempfile.TemporaryDirectory() as tmp:
   o=Path(tmp)/'fixture';st=execute(entries,provider,o,True,stop_check=lambda:mode=='cancel')
   if mode=='system':assert st['status']=='STOPPED_SYSTEM_FAULT' and st['calls']==0
   elif mode=='cancel':assert st['status']=='CANCELLED_BY_USER' and st['calls']==0
   elif mode in ['empty','review_limit']:assert st['calls']==127 and st['processed_units']==8 and st['complete_units']==7
   else:assert st['calls']==128 and st['complete_units']==8
  tests.append(dict(mode=mode,result='PASS'))
 result=dict(result='PASS',qualification=q['qualification'],request_lengths_checked=requests,max_input_plus_cap=maximum,full_actual_response_replay_calls=128,tests=tests,freeze=freeze(),model_calls=0)
 write(HERE/'PREFLIGHT.json',result);print(json.dumps({k:v for k,v in result.items() if k!='freeze'}),flush=True)

def audit():
 from b0_training import load_tokenizer
 c=load(HERE/'config.json');out=ROOT/c['run_dir'];assert freeze()==load(HERE/'FREEZE.json')==load(out/'manifest.json')['freeze'];tok=load_tokenizer(c);entries={e['unit']:e for e in load(HERE/'INPUTS.json')['entries']}
 def read(p):
  t=Path(p).read_text();return [json.loads(s) for s in t[:t.rfind('\n')+1].splitlines()]
 rows=read(out/'responses.jsonl');attempts=read(out/'attempts.jsonl');reviews={};maximum=0
 for i,r in enumerate(rows):
  assert r['call']==i and all(r[k]==v for k,v in attempts[i].items());e=entries[r['unit']]
  own=reviews.get((r['unit'],r['arm'],r['actor']));expected=make_request(e,r['actor'],r['arm'],r['stage'],own)
  assert all(r[k]==v for k,v in expected.items())
  ids=tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ['system','user']],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs']);u=r['usage']
  assert len(ids)==u['input_tokens'] and len(ids)+r['max_new_tokens']<=c['max_length'];maximum=max(maximum,len(ids)+r['max_new_tokens'])
  assert len(u['output_ids'])==u['output_tokens']<=r['max_new_tokens'] and tok.decode(u['output_ids'],skip_special_tokens=True)==r['raw_output']
  assert u['adapter_enabled']==(r['actor']=='M1') and u['lora_layers']==252 and u['disabled_layers']==(0 if r['actor']=='M1' else 252) and u['batch_size']==1
  if r['stage']=='review' and r['status']=='OK':reviews[(r['unit'],r['arm'],r['actor'])]=r['raw_output']
 result=dict(result='PASS',responses_checked=len(rows),full_payload_history_seed_token_route_reconstruction=True,max_input_plus_cap=maximum,non_ok=sum(r['status']!='OK' for r in rows),freeze_unchanged=True)
 labels=load(HERE.parent/'expert-composition100-20261109/LABELS.json')['targets'];stored=load(out/'scores.json') if (out/'scores.json').exists() else []
 for item in stored:
  e=entries[item['unit']]
  for arm in ARMS:
   rr=[r for r in rows if r['unit']==e['unit'] and r['arm']==arm and r['stage']=='final'];ok=len(rr)==4 and all(r['status']=='OK' for r in rr)
   assert item['arms'][arm]['complete']==ok
   if ok:
    ans={r['actor']:r['raw_output'] for r in rr};seed=e['trial_config']['seed']+e['trial_config']['task_index']*10000+1001
    assert item['arms'][arm]['finals']==ans and item['arms'][arm]['members']=={a:b.answer_score(v,labels[e['id']]) for a,v in ans.items()}
    assert all(item['arms'][arm][k]==v for k,v in b.vote_scores(b.vote(ans,seed),labels[e['id']]).items())
 result['complete_unit_scores_reconstructed']=len(stored)
 write(HERE/'RUN_AUDIT.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='prepare':prepare()
 elif mode=='freeze':write(HERE/'FREEZE.json',freeze())
 elif mode=='preflight':preflight()
 elif mode=='audit':audit()
 elif mode=='run':
  import fcntl
  c=load(HERE/'config.json');assert freeze()==load(HERE/'FREEZE.json')==load(HERE/'PREFLIGHT.json')['freeze'];assert load(HERE/'PREFLIGHT.json')['result']=='PASS' and 'RUN_ALLOWED' in (HERE/'EXPERIMENT_REVIEW.md').read_text()
  lock=(HERE/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);out=ROOT/c['run_dir'];assert not out.exists()
  stopping=False
  def stop(signum,frame):
   global stopping
   stopping=True
  signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
  try:backend=b.MultiBackend(c)
  except BaseException as exc:write(HERE/'STARTUP_FAILURE.json',dict(type=type(exc).__name__,message=str(exc)));raise
  def provider(r):
   z=backend.respond_many([{k:r[k] for k in ['actor','seed','max_new_tokens','payload']}],math.inf)[0];u=z['usage']
   assert u['adapter_enabled']==r['adapter_enabled'] and u['disabled_layers']==(0 if r['actor']=='M1' else 252) and u['lora_layers']==252 and u['batch_size']==1
   return z
  result=execute(load(HERE/'INPUTS.json')['entries'],provider,out,stop_check=lambda:stopping or (HERE/'STOP_REQUESTED').exists());print(json.dumps(result),flush=True)
