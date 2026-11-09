"""Frozen natural expert proposals; matched local/generic/self reviews, no retries."""
import copy, hashlib, itertools, json, math, os, re, signal, sys, time, traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from b0_answers import answer_score
from b1_runtime import validate_runtime
from b1_multi_backend import MultiBackend
from expert_mechanism_protocol import validate_task
ARMS=('S','G','L'); ACTORS=('M1','M2','M3','M4')
REVIEW_COMMON=(
 'Review the proposed answer and explanation against the question and supplied passages. '
 'Your earlier independent answer and the proposal may both be wrong. '
 'You may support, challenge, or be unable to judge the proposal; do not invent objections. '
 'Use only the supplied evidence. Cite paragraph indices and explain what the evidence supports, '
 'rather than treating a real quotation as proof of a relation. If proposing a correction, '
 'give its evidence; do not change answers merely because of agreement or confidence. '
 'Write a concise review of at most 150 words, beginning VERDICT: SUPPORT, CHALLENGE, or UNCERTAIN. '
 'Then give your assessment and any proposed answer. ')
GENERIC='Assess the proposal as a whole for correctness, considering any relevant issue.'
LOCAL=(
 'Focus on the requested target: which entity or property is asked for, and whether the '
 'proposed answer has the requested type and refers to that target rather than an intermediate entity.',
 'Focus on the links between facts: check whether the same entities and relations actually '
 'connect across the cited passages. Identify any unsupported substitution, reversed relation, '
 'or missing link; individual true facts alone do not establish the chain.',
 'Focus on qualifications: check time, geographic scope, comparisons, quantifiers, '
 'and any passage that contradicts the proposed conclusion. A fact outside the required '
 'scope need not support that conclusion.')
REVISION=(
 'Decide the answer using only the question and supplied passages. You have your own earlier '
 'answer, a proposed answer and explanation, and three independent reviews. All may contain errors. '
 'Evaluate the reviews against the passages. An unsupported challenge should not overturn a '
 'supported answer, and one valid counterexample can justify correction without majority agreement. '
 'Choose the best current answer; do not simply copy your first answer or count reviewers. '
 'Output ONLY the short answer: a name, entity, date, number, or short phrase. '
 'Do not explain, restate the question, list alternatives, or describe your reasoning. '
 'This reply is the submitted decision, with no further answer generation. '
 'If evidence is insufficient, output unknown.')
load=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.tmp')
 with q.open('w',encoding='utf-8') as f:
  f.write(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
 os.replace(q,p)

def append(p,v):
 with Path(p).open('a',encoding='utf-8') as f:
  f.write(json.dumps(v,ensure_ascii=False,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())

def jsonlines(p):
 s=Path(p).read_text(encoding='utf-8');return [json.loads(z) for z in s[:s.rfind('\n')+1].splitlines()]

def parse_answer(raw):
 if not isinstance(raw,str):return None,'NON_TEXT'
 # The entire revision is the answer. Never extract an entity from explanatory prose.
 if not raw.strip():return None,'EMPTY_ANSWER'
 return raw.strip(),None

def packet(e,arm,stage,slot,reviews):
 c=load(HERE/'config.json');p=e['prefix']
 actor='M1' if arm=='S' or stage=='revision' else ACTORS[slot+1]
 data={k:copy.deepcopy(e['task'][k]) for k in ('question','paragraphs')}
 data['own_earlier_answer']=p['initials'][actor]
 data['proposal']={'answer':p['candidate'],'explanation':p['explanation']}
 if stage=='revision':data['independent_reviews']=copy.deepcopy(reviews)
 system=REVISION if stage=='revision' else REVIEW_COMMON+(LOCAL[slot] if arm=='L' else GENERIC)
 return dict(unit=e['unit'],id=e['id'],index=e['index'],rep=e['rep'],stratum=e['stratum'],
  arm=arm,stage=stage,slot=slot,actor=actor,adapter_enabled=actor=='M1',
  seed=1200000000+e['unit']*100000+(4000 if stage=='revision' else slot),
  max_new_tokens=c['revision_cap'] if stage=='revision' else c['review_cap'],
  payload={'system':system,'user':'TASK_DATA\n'+json.dumps(data,ensure_ascii=False,indent=2)})

def unit(e,provider):
 t={k:e[k] for k in ('unit','id','index','rep','stratum','group')}
 t.update(prefix_complete=e['prefix']['complete'],candidate=e['prefix']['candidate'],
  inherited_failure=e['prefix']['failures'],arms={})
 if not t['prefix_complete']:return t
 for arm in list(itertools.permutations(ARMS))[e['unit']%6]:
  reviews=[];a={'reviews':reviews,'complete':False};t['arms'][arm]=a
  for slot in range(3):
   z=provider(packet(e,arm,'review',slot,[]))
   if z['status']!='OK':a['failure']={'stage':'review','slot':slot,'status':z['status']};break
   reviews.append({'slot':slot+1,'text':z['raw_output']})
  else:
   z=provider(packet(e,arm,'revision',3,reviews))
   a['revision']=z['raw_output'];a['revision_status']=z['status']
   if z['status']!='OK':a['failure']={'stage':'revision','status':z['status']};continue
   answer,error=parse_answer(z['raw_output'])
   if error:a['failure']={'stage':'parse','status':error};continue
   a.update(answer=answer,complete=True)
 return t

def score(t):
 target=load(HERE/'LABELS.json')['targets'][t['id']]
 aliases=load(HERE/'SCORING.json')['aliases'].get(str(t['index']),[])
 alt=dict(target,answer_aliases=target.get('answer_aliases',[])+aliases)
 out={k:copy.deepcopy(t[k]) for k in ('unit','id','index','rep','stratum','group','prefix_complete','inherited_failure')}
 out['arms']={}
 if t['prefix_complete']:
  out['arms']['R']={'complete':True,'answer':t['candidate'],'metrics':answer_score(t['candidate'],target),'auxiliary':answer_score(t['candidate'],alt)}
 else:out['arms']['R']={'complete':False,'failure':'INHERITED_COMMON_PREFIX_FAILURE'}
 for arm in ARMS:
  a=t['arms'].get(arm,{});out['arms'][arm]={'complete':bool(a.get('complete'))}
  if a.get('complete'):out['arms'][arm].update(answer=a['answer'],metrics=answer_score(a['answer'],target),auxiliary=answer_score(a['answer'],alt))
  else:out['arms'][arm]['failure']=a.get('failure','INHERITED_COMMON_PREFIX_FAILURE')
 return out

def freeze():
 c=load(HERE/'config.json')
 files=[HERE/n for n in ['experiment.py','launch.py','prepare.cjs','config.json','INPUTS.json','LABELS.json','SCORING.json','DESIGN.md','EXPERIMENT_REVIEW.md']]
 files += [ROOT/'tools'/n for n in ['b1_runtime.py','b1_multi_backend.py','b1_controls.py','b0_answers.py','b0_training.py','b1_stop_status.py','b1_output_contract.py','expert_mechanism_protocol.py','prepare_answer_only_expert.py','prepare_expert_training.py']]
 files += [ROOT/'research/musique-data-preparation-20261030/official_scorer/metrics/answer.py']
 files += [Path(c['adapter_path'])/n for n in ['adapter_config.json','adapter_model.safetensors','b0_origin.json']]
 files += [Path(c[k]) for k in ['baseline_C_score','expert_C_score']]
 files += [ROOT/p for p in load(HERE/'INPUTS.json')['sources']]
 return {str(p):sha(p) for p in dict.fromkeys(files)}

def preflight():
 from b0_training import load_tokenizer
 c=load(HERE/'config.json');entries=load(HERE/'INPUTS.json')['entries'];q=validate_runtime(c);tok=load_tokenizer(c)
 assert len(entries)==64 and len({e['id'] for e in entries})==32 and len({e['group'] for e in entries})==32
 assert sum(e['prefix']['complete'] for e in entries)==62 and c['review_cap']==768 and c['revision_cap']==256
 assert c['wall_clock_cutoff'] is None and c['generation_retries']==0
 rows=jsonlines(ROOT/'runs/expert-evidence-scale32-20261109-v1/responses.jsonl')
 previous=jsonlines(ROOT/c['reused_response_source']);assert len(previous)==24
 reused=[z for z in previous if z['stage']=='review'];assert len(reused)==c['reused_response_count']==18
 actual={(z['unit'],z['arm'],z['stage'],z['slot']):z for z in reused}
 old={(z['unit'],z['arm'],z['stage'],z['actor'],z['round']):z for z in rows}
 lengths=[];requests=[];new_format_wrappers=0
 def length(r):return len(tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs']))
 for e in entries:
  validate_task(e['task']);assert set(e['task'])=={'id','question','paragraphs'}
  source=load(ROOT/e['prefix_source']);p=e['prefix']
  assert (p['initials'],p['explanation'],p['candidate'],p['complete'])==(source['initials'],source['explanation'],source['candidate'],source['common_complete'])
  def replay(r):
   nonlocal new_format_wrappers
   d=json.loads(r['payload']['user'][10:]);assert set(d)==({'question','paragraphs','own_earlier_answer','proposal'}|({'independent_reviews'} if r['stage']=='revision' else set()))
   assert d['proposal']=={'answer':p['candidate'],'explanation':p['explanation']}
   if r['stage']=='review':assert 'independent_reviews' not in d
   else:assert [x['slot'] for x in d['independent_reviews']]==[1,2,3]
   assert r['adapter_enabled']==(r['actor']=='M1')
   n=length(r)+r['max_new_tokens'];assert n<=c['max_length'];lengths.append(n);requests.append(copy.deepcopy(r))
   key=(r['unit'],r['arm'],r['stage'],r['slot'])
   if key in actual:
    z=actual[key];assert all(z[k]==v for k,v in r.items())
    return {'status':z['status'],'raw_output':z['raw_output']}
   a=r['actor'];stage='work' if r['stage']=='review' else 'final';rn=1 if r['stage']=='review' else 3
   z=old[e['unit'],'C',stage,a,rn];assert z['status']=='OK'
   raw=z['raw_output']
   return {'status':'OK','raw_output':raw}
  t=unit(e,replay);s=score(t)
  if p['complete']:assert all(s['arms'][a]['complete'] for a in ('R',)+ARMS)
 assert len(requests)==744 and new_format_wrappers==0
 # Generic vs local inputs, sampling and revision instructions share everything except review system.
 for e in entries:
  if not e['prefix']['complete']:continue
  for slot in range(3):
   g=packet(e,'G','review',slot,[]);l=packet(e,'L','review',slot,[])
   assert g['payload']['user']==l['payload']['user'] and g['seed']==l['seed'] and g['actor']==l['actor']
  assert packet(e,'G','revision',3,[])['payload']==packet(e,'L','revision',3,[])['payload']==packet(e,'S','revision',3,[])['payload']
 tests=[]
 for raw,expected in [('Ryan Eggold','Ryan Eggold'),('Crawford County','Crawford County'),('unknown','unknown'),('Answer: Crawford County','Answer: Crawford County'),('text\nCrawford County','text\nCrawford County'),('FINAL_ANSWER: A\nFINAL_ANSWER: B','FINAL_ANSWER: A\nFINAL_ANSWER: B'),('',None),(None,None),('{"answer":"A"}','{"answer":"A"}')]:
  assert parse_answer(raw)[0]==expected
 tests.append('nine_whole_reply_cases_no_entity_or_json_extraction_no_gold_repair')
 e=next(e for e in entries if e['prefix']['complete'])
 for mode in ('review_limit','revision_empty','overlength','system','cancel'):
  calls=[]
  def fail(r):
   calls.append(r)
   if mode=='system':raise RuntimeError('FIXTURE_SYSTEM')
   if mode=='cancel':raise InterruptedError('FIXTURE_CANCEL')
   status='OK';raw='VERDICT: UNCERTAIN\nI cannot establish the needed relation.\nFINAL_ANSWER: unknown'
   if r['arm']=='G':
    if mode in ('review_limit','overlength') and r['stage']=='review':status='OUTPUT_LIMIT' if mode=='review_limit' else 'INPUT_OVERLENGTH'
    elif mode=='revision_empty' and r['stage']=='revision':status='EMPTY_OR_NON_TEXT';raw=''
   return {'status':status,'raw_output':raw}
  try:
   t=unit(e,fail)
   assert mode not in ('system','cancel')
   assert not t['arms']['G']['complete'] and t['arms']['S']['complete'] and t['arms']['L']['complete']
   if mode in ('review_limit','overlength'):assert len([r for r in calls if r['arm']=='G'])==1
  except (RuntimeError,InterruptedError):assert mode in ('system','cancel')
  tests.append(mode)
 longest=max((z for z in rows if z['status']=='OK' and z['stage']=='work'),key=lambda z:z['usage']['output_tokens'])['raw_output']
 stressmax=0;isolated=0
 for e in entries:
  def stress(r):
   nonlocal stressmax,isolated
   n=length(r)+r['max_new_tokens'];stressmax=max(stressmax,n)
   if n>c['max_length']:isolated+=1;return {'status':'INPUT_OVERLENGTH','raw_output':''}
   return {'status':'OK','raw_output':longest if r['stage']=='review' else 'FINAL_ANSWER: unknown'}
  unit(e,stress)
 # Old full outputs without marker are explicitly NOT called new-format real successes.
 result={'result':'PASS','qualification':q['qualification'],'replay_requests':len(requests),'historical_responses_available':len(rows),
  'new_revision_contract_synthetic_wrappers':new_format_wrappers,'new_contract_real_validation':'18_REAL_V1_REVIEWS_IDENTICAL_PAYLOADS; ANSWER_ONLY_REVISION_PENDING_FIRST_TWO_ACTUAL_UNITS',
  'max_replay_input_plus_cap':max(lengths),'stress_max_input_plus_cap':stressmax,'stress_overlength_isolated':isolated,
  'tests':tests,'model_calls':0,'freeze':freeze()}
 write(HERE/'PREFLIGHT.json',result);print(json.dumps({k:v for k,v in result.items() if k!='freeze'}),flush=True)

def run():
 import fcntl
 c=load(HERE/'config.json');assert freeze()==load(HERE/'FREEZE.json')==load(HERE/'PREFLIGHT.json')['freeze']
 assert load(HERE/'PREFLIGHT.json')['result']=='PASS' and 'RUN_ALLOWED' in (HERE/'EXPERIMENT_REVIEW.md').read_text()
 lock=(HERE/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 out=ROOT/c['run_dir'];out.mkdir(exist_ok=False);(out/'trials').mkdir();(out/'responses.jsonl').touch();(out/'attempts.jsonl').touch()
 write(out/'manifest.json',{'config':c,'freeze':freeze(),'planned_units':64,'eligible_units':62,'max_total_logged_responses':744,'max_fresh_model_calls':726,'reused_v1_reviews':18,'v1_discarded_revision_calls_preserved':6,'study_unique_new_calls_max':750,'reused_common_calls_per_eligible_unit':6})
 previous=jsonlines(ROOT/c['reused_response_source']);assert len(previous)==24
 reused={(z['unit'],z['arm'],z['stage'],z['slot']):z for z in previous if z['stage']=='review'};assert len(reused)==18
 state={'status':'LOADING_MODEL','calls':0,'generated_calls':0,'reused_calls':0,'processed_units':0,'eligible_complete_units':0,'total_units':64,'eligible_units':62};start=time.monotonic();stopping=False;scores=[]
 def status(name,**kw):state.update(status=name,elapsed_seconds=time.monotonic()-start,**kw);write(out/'STATUS.json',state)
 def stop(sig,frame):
  nonlocal stopping
  stopping=True
 signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop);status('LOADING_MODEL')
 try:
  backend=MultiBackend(c)
  def provider(r):
   if stopping or (HERE/'STOP_REQUESTED').exists():raise InterruptedError('USER_STOP')
   r=dict(r,call=state['calls']);append(out/'attempts.jsonl',r)
   n=len(backend.tokenizer.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs']))
   key=(r['unit'],r['arm'],r['stage'],r['slot'])
   if key in reused:
    old=reused[key];assert all(old[k]==v for k,v in r.items())
    z={k:copy.deepcopy(old[k]) for k in ('raw_output','status','usage')}
    z.update(origin='reused_model_response_v1',source_call=old['call']);state['reused_calls']+=1
   elif n+r['max_new_tokens']>c['max_length']:z={'raw_output':'','status':'INPUT_OVERLENGTH','origin':'local_precheck','usage':{'input_tokens':n,'output_tokens':0}}
   else:
    z=backend.respond_many([{k:r[k] for k in ('actor','seed','max_new_tokens','payload')}],math.inf)[0];z['origin']='model';u=z['usage']
    assert u['adapter_enabled']==r['adapter_enabled'] and u['disabled_layers']==(0 if r['actor']=='M1' else 252) and u['lora_layers']==252 and u['batch_size']==1
    if z['status']=='OK' and (not isinstance(z['raw_output'],str) or not z['raw_output'].strip()):z['status']='EMPTY_OR_NON_TEXT'
    state['generated_calls']+=1
   row=dict(r,**z);append(out/'responses.jsonl',row);state['calls']+=1;assert state['calls']<=744
   status('RUNNING',unit=r['unit'],index=r['index'],rep=r['rep'],arm=r['arm'],stage=r['stage'],slot=r['slot']);return row
  for pos,e in enumerate(load(HERE/'INPUTS.json')['entries']):
   t=unit(e,provider);write(out/'trials'/f"{e['unit']:03d}.json",t);s=score(t);scores.append(s);write(out/'scores.json',scores)
   state['processed_units']+=1;state['eligible_complete_units']+=int(e['prefix']['complete'] and all(s['arms'][a]['complete'] for a in ARMS))
   if pos==1:
    status('WAITING_PREFIX_AUDIT');write(out/'PREFIX_CHECKPOINT.json',{'calls':state['calls'],'units':2})
    while not (HERE/'CONTINUE_CHECKED.json').exists():
     if stopping or (HERE/'STOP_REQUESTED').exists():raise InterruptedError('USER_STOP')
     time.sleep(.5)
  status('COMPLETED_WITH_INHERITED_MISSING' if state['eligible_complete_units']==62 else 'COMPLETED_WITH_NEW_INCOMPLETE_ARMS')
 except InterruptedError as exc:status('CANCELLED_BY_USER',failure=str(exc))
 except BaseException as exc:
  status('STOPPED_SYSTEM_FAULT',failure={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()});raise

def audit():
 from b0_training import load_tokenizer
 c=load(HERE/'config.json');out=ROOT/c['run_dir'];assert freeze()==load(HERE/'FREEZE.json')==load(out/'manifest.json')['freeze']
 tok=load_tokenizer(c);rows=jsonlines(out/'responses.jsonl');attempts=jsonlines(out/'attempts.jsonl');cursor=0;complete=0;maxlen=0
 reused=jsonlines(ROOT/c['reused_response_source'])
 class End(Exception):pass
 def replay(r):
  nonlocal cursor,maxlen
  if cursor==len(rows):raise End()
  z=rows[cursor];assert z['call']==cursor and all(z[k]==v for k,v in r.items()) and all(z[k]==v for k,v in attempts[cursor].items())
  n=len(tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs']));u=z['usage'];assert n==u['input_tokens'];maxlen=max(maxlen,n+r['max_new_tokens'])
  if z['origin']=='local_precheck':assert z['status']=='INPUT_OVERLENGTH' and n+r['max_new_tokens']>c['max_length']
  else:
   assert n+r['max_new_tokens']<=c['max_length'] and len(u['output_ids'])==u['output_tokens']<=r['max_new_tokens']
   assert tok.decode(u['output_ids'],skip_special_tokens=True)==z['raw_output']
   assert u['adapter_enabled']==(r['actor']=='M1') and u['lora_layers']==252 and u['disabled_layers']==(0 if r['actor']=='M1' else 252) and u['batch_size']==1
   if z['origin']=='reused_model_response_v1':
    previous=reused[z['source_call']];assert previous['stage']=='review'
    assert all(previous[k]==v for k,v in r.items()) and all(previous[k]==z[k] for k in ('raw_output','status','usage'))
  cursor+=1;return z
 stored=load(out/'scores.json') if (out/'scores.json').exists() else []
 for e in load(HERE/'INPUTS.json')['entries']:
  try:t=unit(e,replay)
  except End:break
  p=out/'trials'/f"{e['unit']:03d}.json"
  if p.exists():assert load(p)==t and score(t)==stored[complete];complete+=1
 assert cursor==len(rows) and len(attempts) in (cursor,cursor+1)
 result={'result':'PASS','responses_checked':cursor,'fresh_model_calls':sum(z['origin']=='model' for z in rows),'reused_v1_responses':sum(z['origin']=='reused_model_response_v1' for z in rows),'unit_scores_reconstructed':complete,'non_ok':sum(z['status']!='OK' for z in rows),
  'max_input_plus_cap':maxlen,'freeze_unchanged':True,'full_actual_payload_history_seed_token_adapter_reconstruction':True}
 write(HERE/'RUN_AUDIT.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='preflight':preflight()
 elif mode=='freeze':write(HERE/'FREEZE.json',freeze())
 elif mode=='run':run()
 elif mode=='audit':audit()
