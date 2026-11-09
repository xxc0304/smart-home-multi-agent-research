"""Two frozen stages with automatic quantitative audit/gate, no invented follow-up methods."""
import copy,hashlib,importlib.util,json,math,os,re,signal,sys,tempfile,time,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('visibility_design',HERE.parent/'expert-final-visibility-design-20261109/build_design.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
b=d.b;load,write,append,sha=b.load,b.write,b.append,b.sha
ARMS=d.ARMS;ACTORS=b.ACTORS
SOURCE=HERE.parent/'expert-composition100-20261109'

def key(r):return json.dumps({k:r[k] for k in ['payload','seed','max_new_tokens','adapter_enabled']},sort_keys=True)

def freeze():
 c=load(HERE/'config.json');entries=load(HERE/'PLAN.json')['entries']
 files=[HERE/n for n in ['pipeline.py','launch.py','config.json','PLAN.json','REQUESTS.json','DESIGN.md','EXPERIMENT_REVIEW.md']]
 files += [HERE.parent/'expert-final-visibility-design-20261109/build_design.py',SOURCE/'experiment.py',SOURCE/'LABELS.json']
 files += [ROOT/e['source_path'] for e in entries]
 files += [ROOT/'tools'/n for n in ['b1_controls.py','b1_runtime.py','b1_multi_backend.py','b0_training.py','b0_answers.py','b1_output_contract.py','b1_stop_status.py','expert_mechanism_protocol.py','prepare_answer_only_expert.py','prepare_expert_training.py']]
 files += [ROOT/'research/musique-data-preparation-20261030/official_scorer/metrics/answer.py']
 files += [Path(c['adapter_path'])/n for n in ['adapter_config.json','adapter_model.safetensors','b0_origin.json']]
 files += [Path(c[k]) for k in ['baseline_C_score','expert_C_score']]
 return {str(p):sha(p) for p in dict.fromkeys(files)}

def prepare():
 from b0_training import load_tokenizer
 c=load(HERE/'config.json');q=b.validate_runtime(c);tok=load_tokenizer(c);entries=[];excluded=[]
 for e in load(SOURCE/'INPUTS.json')['units']:
  idx=b.source(e)
  if not all((z:=idx.get((a,'final','B',3))) and z['status']=='OK' for a in ACTORS):excluded.append(dict(unit=e['unit'],id=e['id'],rep=e['rep'],reason='OLD_B_FINALS_INCOMPLETE'));continue
  entries.append(e)
 pilot=[e for e in entries if e['cohort']=='fresh' and e['source_index'] in d.IDS]
 extension=[e for e in entries if e not in pilot];ordered=sorted(pilot,key=lambda e:(e['source_index'],e['rep']))+sorted(extension,key=lambda e:(e['cohort']!='fresh',e['source_index'],e['rep']))
 rows=[];maximum=0;unique=0
 for i,e in enumerate(ordered):
  idx=b.source(e);phase=1 if e in pilot else 2;cache=set();arms=ARMS[i%5:]+ARMS[:i%5]
  for arm in arms:
   for r in d.build(e,idx,arm):
    ids=tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ['system','user']],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs'])
    n=len(ids)+r['max_new_tokens'];assert n<=c['max_length'];maximum=max(maximum,n)
    k=key(r);unique+=int(k not in cache);cache.add(k);rows.append(dict(r,unit=e['unit'],phase=phase,planned_input_tokens=len(ids)))
 assert len(entries)==155 and len(pilot)==28 and len(extension)==127 and len(rows)==3100 and unique==2635
 write(HERE/'PLAN.json',dict(scope='TWO_STAGE_ALREADY_KNOWN_DEVELOPMENT_NOT_CONFIRMATORY',entries=ordered,excluded_old_units=excluded,pilot_units=28,extension_units=127,total_unique_questions=100,pilot_questions=14,primary_unique_questions=56,maximum_logical_calls=3100,maximum_new_calls=2635,phase1_max_new=476,phase2_max_new=2159,gate_clean_indices=[6,17],gate_excluded_measurement=[9,51],gate_excluded_boundary=[1,24,31,43,49,54],wall_cutoff=None,automatic_method_change=False))
 write(HERE/'REQUESTS.json',rows);write(HERE/'BUILD_CHECK.json',dict(result='PASS',requests=3100,maximum_new=2635,max_input_plus_cap=maximum,qualification=q['qualification'],source_exclusions=excluded,model_calls=0))
 print(json.dumps(load(HERE/'BUILD_CHECK.json')),flush=True)

def score(rows):
 plan=load(HERE/'PLAN.json');labels=load(SOURCE/'LABELS.json')['targets'];by={};result=[]
 for r in rows:by.setdefault((r['unit'],r['arm']),{})[r['actor']]=r
 for e in plan['entries']:
  if not any((e['unit'],arm) in by for arm in ARMS):continue
  target=labels[e['id']];item=dict(unit=e['unit'],id=e['id'],index=e['source_index'],rep=e['rep'],cohort=e['cohort'],group=e['group'],arms={});idx=b.source(e)
  old={a:idx[(a,'final','B',3)]['raw_output'] for a in ACTORS};seed=e['trial_config']['seed']+e['trial_config']['task_index']*10000+1001
  item['old_B']=b.vote_scores(b.vote(old,seed),target);item['old_M1']=b.answer_score(old['M1'],target)
  for arm in ARMS:
   rr=by.get((e['unit'],arm),{});complete=len(rr)==4 and all(r['status']=='OK' for r in rr.values())
   if not complete:item['arms'][arm]=dict(complete=False,returned=len(rr));continue
   ans={a:rr[a]['raw_output'] for a in ACTORS};members={a:b.answer_score(v,target) for a,v in ans.items()}
   item['arms'][arm]=dict(complete=True,finals=ans,members=members,**b.vote_scores(b.vote(ans,seed),target))
  result.append(item)
 return result

def gate(scores):
 clean=set(load(HERE/'PLAN.json')['gate_clean_indices']);measurement={9,51};primary=[s for s in scores if s['cohort']=='fresh' and s['index'] in d.IDS and s['index'] not in measurement and all(s['arms'][a]['complete'] for a in ARMS)]
 candidates=[]
 for arm in ['E_expert_final','EO_all_finals']:
  gains=[]
  for s in primary:
   if s['index'] not in clean or s['arms'][arm]['expected_em']<=s['arms']['N_self']['expected_em'] or s['arms'][arm]['expected_em']<=s['old_B']['expected_em']:continue
   wrong,correct={6:('ashtabula county','crawford county'),17:('ulster county','greene county')}[s['index']]
   pattern=r'\b(?:ashtabula|crawford|ulster|greene) county\b';switched=[]
   for a in ACTORS:
    before=set(re.findall(pattern,s['arms']['N_self']['finals'][a].casefold()));after=set(re.findall(pattern,s['arms'][arm]['finals'][a].casefold()))
    if before=={wrong} and after=={correct}:switched.append(a)
   if switched:gains.append(dict(id=s['id'],index=s['index'],rep=s['rep'],difference=s['arms'][arm]['expected_em']-s['arms']['N_self']['expected_em'],distinct_county_target_switches=switched))
  net=sum(s['arms'][arm]['expected_em']-s['arms']['N_self']['expected_em'] for s in primary)
  net_old=sum(s['arms'][arm]['expected_em']-s['old_B']['expected_em'] for s in primary)
  candidates.append(dict(arm=arm,clean_gain_units=gains,non_measurement_net_expected_points=net,net_vs_original_B=net_old,eligible=bool(gains) and net>=0 and net_old>=0))
 allowed=any(x['eligible'] for x in candidates)
 return dict(decision='EXPAND_FIXED_ALL_FIVE_ARMS' if allowed else 'STOP_THIS_ROUTE_WITH_REPORT',scope='Budget routing rule, not statistical significance or semantic mechanism certification',candidate_checks=candidates,ambiguous_or_measurement_cases_cannot_alone_trigger=True,manual_semantic_review_pending=True)

def validate_row(r,tok,c):
 u=r['usage'];ids=tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ['system','user']],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs'])
 assert len(ids)==u['input_tokens']==r['planned_input_tokens'] and len(ids)+r['max_new_tokens']<=c['max_length']
 assert len(u['output_ids'])==u['output_tokens']<=r['max_new_tokens'] and tok.decode(u['output_ids'],skip_special_tokens=True)==r['raw_output']
 assert u['adapter_enabled']==r['adapter_enabled']==(r['actor']=='M1') and u['lora_layers']==252 and u['disabled_layers']==(0 if r['actor']=='M1' else 252) and u['batch_size']==1

def report(out,rows,phase):
 ss=score(rows);write(out/'scores.json',ss);completed=[s for s in ss if all(s['arms'][a]['complete'] for a in ARMS)]
 means={}
 for cohort in ['fresh','old_coverage','mechanism','all_descriptive']:
  selected=[s for s in completed if cohort=='all_descriptive' or s['cohort']==cohort]
  if selected:means[cohort]={a:sum(s['arms'][a]['expected_em'] for s in selected)/len(selected) for a in ARMS}|dict(n_units=len(selected),n_tasks=len({s['id'] for s in selected}),old_B=sum(s['old_B']['expected_em'] for s in selected)/len(selected),old_M1=sum(s['old_M1']['em'] for s in selected)/len(selected))
 fresh=[s for s in completed if s['cohort']=='fresh'];eligible={s['id'] for s in fresh if sum(t['id']==s['id'] for t in fresh)==2}
 for name,selected in [('primary_fresh_both_seeds',[s for s in fresh if s['id'] in eligible]),('fresh_extension_only',[s for s in fresh if s['index'] not in d.IDS]),('fresh_seed0',[s for s in fresh if s['rep']==0]),('fresh_seed1',[s for s in fresh if s['rep']==1])]:
  if selected:means[name]={a:sum(s['arms'][a]['expected_em'] for s in selected)/len(selected) for a in ARMS}|dict(n_units=len(selected),n_tasks=len({s['id'] for s in selected}))
 doc=dict(phase=phase,complete_units=len(completed),non_ok=sum(r['status']!='OK' for r in rows),quantitative_only=True,manual_semantic_review_pending=True,means=means,source_responses=len(rows),scores=ss)
 write(out/f'PHASE{phase}_ANALYSIS.json',doc)
 lines=['# Automatic quantitative analysis', '', 'Semantic case review is pending. These are development data, not confirmation.', '',f'Complete task-seed units: {len(completed)}; non-OK responses: {doc["non_ok"]}.', '', '|View|N self|P repeat public|E expert final|O ordinary finals|EO all finals|', '|---|---:|---:|---:|---:|---:|']
 for name,values in means.items():lines.append('|'+name+'|'+ '|'.join(f'{100*values[a]:.2f}%' for a in ['N_self','P_expert_public_repeat','E_expert_final','O_ordinary_finals','EO_all_finals'])+'|')
 (out/f'PHASE{phase}_ANALYSIS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 return ss,doc

def execute(provider,out,fixture=False,stop_check=lambda:False):
 plan=load(HERE/'PLAN.json');requests=load(HERE/'REQUESTS.json');out.mkdir(parents=True,exist_ok=False)
 if not fixture:write(out/'manifest.json',dict(config=load(HERE/'config.json'),freeze=freeze(),plan=plan,analysis='automatic quantitative; manual semantics pending'))
 for n in ['attempts.jsonl','responses.jsonl']:(out/n).touch()
 start=time.monotonic();rows=[];new=0;cache={};last_unit=None;failure=None;phase=1;stopped=False
 def state(status,**kw):
  groups={}
  for r in rows:groups.setdefault(r['unit'],[]).append(r)
  write(out/'STATUS.json',dict(status=status,phase=phase,responses=len(rows),new_calls=new,reused_calls=len(rows)-new,processed_units=sum(len(v)==20 for v in groups.values()),complete_units=sum(len(v)==20 and all(r['status']=='OK' for r in v) for v in groups.values()),elapsed_seconds=time.monotonic()-start,**kw))
 state('STARTING')
 try:
  for request in requests:
   if stop_check():
    stopped=True;break
   if request['phase']==2 and phase==1:
    ss,doc=report(out,rows,1);decision=gate(ss);write(out/'ROUTE_DECISION.json',decision)
    if not fixture and len(rows)!=560:raise ValueError('INCOMPLETE_PHASE1_PREFIX')
    if not decision['decision'].startswith('EXPAND'):break
    phase=2;state('RUNNING_EXTENSION',route_decision=decision['decision'])
   if request['unit']!=last_unit:cache={};last_unit=request['unit']
   k=key(request);old=cache.get(k);attempt=dict(request,call=len(rows),reused=old is not None,source_call=old['call'] if old else None)
   append(out/'attempts.jsonl',attempt)
   if old:z={n:old[n] for n in ['raw_output','status','usage']}
   else:
    z=provider(request);new+=1
    if z['status']=='OK' and (not isinstance(z['raw_output'],str) or not z['raw_output'].strip()):z=dict(z,status='EMPTY_OR_NON_TEXT')
   row=dict(attempt,**z);append(out/'responses.jsonl',row);rows.append(row);cache[k]=row
   if len(rows)%20==0:write(out/'scores.json',score(rows))
   state('RUNNING',unit=request['unit'],index=request['index'],rep=request['rep'],arm=request['arm'],actor=request['actor'])
   assert new<=plan['maximum_new_calls'] and len(rows)<=plan['maximum_logical_calls']
 except BaseException as exc:failure=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
 if rows:report(out,rows,phase)
 state('STOPPED_SYSTEM_FAULT' if failure else 'CANCELLED_BY_USER' if stopped else 'COMPLETED_FIXED_EXTENSION' if phase==2 else 'COMPLETED_PILOT_ROUTE_CLOSED',failure=failure)
 return load(out/'STATUS.json')

def preflight():
 from b0_training import load_tokenizer
 c=load(HERE/'config.json');tok=load_tokenizer(c);requests=load(HERE/'REQUESTS.json');plan=load(HERE/'PLAN.json');assert len(requests)==3100
 assert b.validate_runtime(c)['qualification']=='SUPPORTED_TASK_ADVANTAGE'
 for run in ['b1-grounded-revision-20261107-v1','b1-stage-advantage-seed1-20261107-v1']:
  for p,h in load(ROOT/'runs'/run/'FREEZE.json')['files'].items():assert sha(p)==h
 tests=[]
 # Actual old full terminal outputs validate record/scoring interfaces, not simulated new research evidence.
 sources={e['unit']:b.source(e) for e in plan['entries']}
 def real(r):
  z=sources[r['unit']][(r['actor'],'final','B',3)];return {k:copy.deepcopy(z[k]) for k in ['raw_output','status','usage']}
 for mode in ['actual_full_terminal_replay','semantic_unknown','empty','limit','system']:
  count=0
  def provider(r):
   nonlocal count
   count+=1
   if mode=='system':raise RuntimeError('fixture_system')
   z=real(r)
   if mode=='semantic_unknown':z['raw_output']='No determinate answer.'
   if mode=='empty' and count==1:z['raw_output']=''
   if mode=='limit' and count==1:z['status']='OUTPUT_LIMIT'
   return z
  with tempfile.TemporaryDirectory() as tmp:
   o=Path(tmp)/'fixture';st=execute(provider,o,True)
   if mode=='system':assert st['status']=='STOPPED_SYSTEM_FAULT'
   else:
    assert st['responses']==560 and st['new_calls']==476 and st['status']=='COMPLETED_PILOT_ROUTE_CLOSED'
    assert load(o/'ROUTE_DECISION.json')['decision']=='STOP_THIS_ROUTE_WITH_REPORT'
   tests.append(dict(mode=mode,result='PASS'))
 # Deterministic gate has both paths and excludes measurement-only gains.
 synthetic=[]
 for idx in [6,9]:
  arms={a:dict(complete=True,expected_em=0) for a in ARMS};arms['E_expert_final']['expected_em']=1
  for a in ARMS:arms[a]['finals']={actor:('Crawford County' if a=='E_expert_final' else 'Ashtabula County') for actor in ACTORS}
  synthetic.append(dict(id=str(idx),index=idx,rep=0,cohort='fresh',arms=arms,old_B=dict(expected_em=0)))
 assert gate(synthetic)['decision'].startswith('EXPAND') and gate(synthetic[1:])['decision'].startswith('STOP')
 artificial=copy.deepcopy(synthetic[:1]);artificial[0]['old_B']['expected_em']=1;assert gate(artificial)['decision'].startswith('STOP')
 tests.append(dict(mode='gate_positive_and_measurement_only_rejection',result='PASS'))
 # Fully replay extension without changing its requests; synthetic success is solely a control-flow fixture.
 oldgate=globals()['gate']
 try:
  globals()['gate']=lambda ss:dict(decision='EXPAND_FIXED_ALL_FIVE_ARMS',fixture=True)
  with tempfile.TemporaryDirectory() as tmp:
   st=execute(real,Path(tmp)/'extension',True);assert st['responses']==3100 and st['new_calls']==2635 and st['status']=='COMPLETED_FIXED_EXTENSION'
 finally:globals()['gate']=oldgate
 tests.append(dict(mode='all_3100_actual_terminal_replay_extension_path',result='PASS'))
 with tempfile.TemporaryDirectory() as tmp:
  st=execute(real,Path(tmp)/'cancel',True,stop_check=lambda:True);assert st['status']=='CANCELLED_BY_USER' and st['responses']==0
 tests.append(dict(mode='user_cancellation_before_generation',result='PASS'))
 with tempfile.TemporaryDirectory() as tmp:
  calls=0
  def once(r):
   nonlocal calls
   calls+=1;return real(r)
  o=Path(tmp)/'partial_cancel';st=execute(once,o,True,stop_check=lambda:calls>=1);assert st['status']=='CANCELLED_BY_USER' and st['responses']==1 and (o/'responses.jsonl').stat().st_size>0
 tests.append(dict(mode='user_cancellation_preserves_partial_response',result='PASS'))
 # Lengths are fixed because no new output enters any later request.
 maximum=0
 for r in requests:
  ids=tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ['system','user']],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs']);assert len(ids)==r['planned_input_tokens'];maximum=max(maximum,len(ids)+r['max_new_tokens']);assert maximum<=c['max_length']
 write(HERE/'PREFLIGHT.json',dict(result='PASS',fixed_requests_tokenized=3100,maximum_input_plus_cap=maximum,actual_old_terminal_response_replay=3100,tests=tests,freeze=freeze(),model_calls=0));print(json.dumps({k:v for k,v in load(HERE/'PREFLIGHT.json').items() if k!='freeze'}),flush=True)

def audit():
 from b0_training import load_tokenizer
 c=load(HERE/'config.json');out=ROOT/c['run_dir'];assert freeze()==load(HERE/'FREEZE.json')==load(out/'manifest.json')['freeze'];tok=load_tokenizer(c)
 def read(p):
  s=Path(p).read_text();return [json.loads(v) for v in s[:s.rfind('\n')+1].splitlines()]
 rows=read(out/'responses.jsonl');attempts=read(out/'attempts.jsonl');requests=load(HERE/'REQUESTS.json');by={}
 for i,r in enumerate(rows):
  assert r['call']==i and all(r[k]==v for k,v in requests[i].items()) and all(r[k]==v for k,v in attempts[i].items());validate_row(r,tok,c)
  if r['reused']:
   old=rows[r['source_call']];assert old['call']<i and old['unit']==r['unit'] and key(old)==key(r) and all(old[k]==r[k] for k in ['raw_output','status','usage'])
 assert score(rows)==load(out/'scores.json') if len(rows)%20==0 else True
 result=dict(result='PASS',responses_checked=len(rows),all_fixed_inputs_seeds_token_ids_adapter_routes_and_reuse_verified=True,non_ok=sum(r['status']!='OK' for r in rows),freeze_unchanged=True)
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
  lock=(HERE/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  stopping=False
  def stop(signum,frame):
   global stopping
   stopping=True
  signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
  try:backend=b.MultiBackend(c)
  except BaseException as exc:write(HERE/'STARTUP_FAILURE.json',dict(type=type(exc).__name__,message=str(exc)));raise
  write(HERE/'BACKEND.json',dict(generation_config=backend.generation_config.to_dict(),expert_route='M1_only',batch_size=1))
  def provider(r):
   dispatched={k:r[k] for k in ['actor','seed','max_new_tokens','payload']};z=backend.respond_many([dispatched],math.inf)[0]
   validate_row(dict(r,**z),backend.tokenizer,c);return z
  result=execute(provider,ROOT/c['run_dir'],stop_check=lambda:stopping or (HERE/'STOP_REQUESTED').exists());print(json.dumps(result),flush=True)
