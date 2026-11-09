"""Independent reconstruction, no inference, no run/score writes."""
import copy,hashlib,json,random,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from b1_controls import WORK,FINAL,vote,vote_scores
from prepare_answer_only_expert import SYSTEM
from b0_answers import answer_score,paired_interval
from b0_training import load_tokenizer
HERE=Path(__file__).resolve().parent;RUN=ROOT/'runs/b1-grounded-revision-20261107-v1'
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
lines=lambda p:[json.loads(x) for x in p.read_text().splitlines() if x.strip()]
actors=['M1','M2','M3','M4'];conds=['A','B','C','D','B_check','B_relation'];pub=['B','B_check','B_relation']
instructions={'B_check':'Before you finish this work turn, review the question, supplied paragraphs, your previous reasoning and the visible discussion. Check your current answer carefully, resolve inconsistencies and reconsider alternatives. Keep or revise your answer as needed, then give your best response.','B_relation':'When weighing competing answers, check the specific entity and relation required by the question against supplied paragraphs. Keep or revise your answer according to that match. Repeated agreement alone is not additional evidence. A supported correction from any participant is valid.'}
before={str(p):sha(p) for p in RUN.rglob('*') if p.is_file()}
assert sha(RUN/'FREEZE.json')=='f198ec875f11e138cf04d8323080c8320a559f38b8aa6c39717b136d7bb0bf6b'
for p,h in load(RUN/'FREEZE.json')['files'].items():assert sha(p)==h,('frozen_changed',p)
approval=load(RUN/'APPROVAL.json');assert approval['verdict']=='RUN_ALLOWED' and approval['freeze_sha256']==sha(RUN/'FREEZE.json')
c=load(RUN/'config.json');pack=load(RUN/'INPUTS.json');targets=load(RUN/'LABELS.json')['targets'];stored=load(RUN/'scores.json');result=load(RUN/'RESULTS.json')
responses=lines(RUN/'responses.jsonl');attempts=lines(RUN/'ATTEMPTS.jsonl');assert len(responses)==len(attempts)==6475
byid={x['request']['request_id']:x for x in responses};assert len(byid)==6475
assert Counter(e['cohort'] for e in pack['tasks'])==dict(fresh=56,old_coverage=36,mechanism=8)
assert sum(e.get('strict_training_answer_isolation',False) for e in pack['tasks'])==29
logical=shared=injected=0;rows=[];physical=[];failures=[];injection_tokens=[]
keys=['request_id','arm','stage','round','actor','seed','max_new_tokens','payload']
def request(e,cond,stage,rn,a,pos,io,initials,work):
  arm=cond if cond in ('A','B','C','D') else 'B';base=20261102+e['index']*10000;d={k:copy.deepcopy(e['task'][k]) for k in ('question','paragraphs')}
  if stage=='initial':rid=f'{e["id"]}/r0/initial/{pos}';seed=base+actors.index(a)
  else:
    history=[dict(sender=x,phase='initial',text=initials[x]) for x in (io if arm in ('B','D') else [a])]+[copy.deepcopy(m) for m in work if arm in ('B','D') or m['sender']==a]
    d.update(own_actor=a,history=history,work_visibility='team_message' if arm in ('B','D') else 'private_work')
    if arm in ('C','D'):d['team_information']='Participant M1 performed better on separate calibration questions from this task. This does not establish that their answer to the current question is correct.'
    if cond in instructions and a=='M1' and stage=='work' and rn==2:d['work_instruction']=instructions[cond]
    rid=f'{e["id"]}/r0/{cond}/{pos:02d}';seed=base+(1000+rn*100 if stage=='work' else 2000)+actors.index(a)
  return dict(request_id=rid,arm=None if stage=='initial' else arm,stage=stage,round=rn,actor=a,seed=seed,max_new_tokens=1024 if stage=='work' else 256,payload=dict(system=SYSTEM if stage=='initial' else WORK if stage=='work' else FINAL,user='TASK_DATA\n'+json.dumps(d,ensure_ascii=False,indent=2)+(c['answer_suffix'] if stage in ('initial','final') else '')))
def check(rec,r):
  global logical
  assert {k:rec[k] for k in keys}==r,('contract_mismatch',r['request_id']);logical+=1
  assert rec['source_kind']=='ACTUAL_LOCAL_MODEL_RESPONSE' and rec['fixture'] is False and isinstance(rec['raw_output'],str)
  if 'shared_prefix_from' in rec:
    z=byid[rec['shared_prefix_from']];assert rec['raw_output']==z['response']['raw_output'] and rec['usage']==z['response']['usage']
    assert {k:v for k,v in r.items() if k!='request_id'}=={k:v for k,v in z['request'].items() if k!='request_id'}
  else:
    z=byid[r['request_id']];assert z['request']==r and z['response']=={k:rec[k] for k in ('raw_output','status','usage')}
for e in pack['tasks']:
  t=load(RUN/f'trials/{e["index"]:03d}.json');base=20261102+e['index']*10000;rng=random.Random(base);io=rng.sample(actors,4);orders=[rng.sample(actors,4) for _ in range(2)];initials={}
  assert len(t['initial_records'])==4
  for j,z in enumerate(t['initial_records']):
    r=request(e,None,'initial',0,actors[j],j,io,{},[]);check(z,r);assert z['status']=='OK';initials[actors[j]]=z['raw_output']
  assert initials==t['initials']
  row=dict(index=e['index'],id=e['id'],cohort=e['cohort'],strict_training_answer_isolation=e.get('strict_training_answer_isolation'),old_index=e.get('old_index'),initial={a:answer_score(v,targets[e['id']]) for a,v in initials.items()},conditions={})
  for cond in conds:
    b=t['branches'][cond];assert b['initials']==initials and b['initial_order']==io and b['orders']==orders
    schedule=[('work',rn+1,a) for rn,order in enumerate(orders) for a in order]+[('final',3,a) for a in actors];work=[];finals={}
    for j,z in enumerate(b['records']):
      stage,rn,a=schedule[j];r=request(e,cond,stage,rn,a,j,io,initials,work);check(z,r)
      if 'shared_prefix_from' in z:assert cond in instructions and j<4+orders[1].index('M1');shared+=1
      if cond in instructions and a=='M1' and stage=='work' and rn==2:assert 'work_instruction' in json.loads(r['payload']['user'][10:]);injected+=1
      if z['status']!='OK':
        failures.append(dict(index=e['index'],condition=cond,id=r['request_id'],status=z['status'],tokens=z['usage']['output_tokens']));assert j==len(b['records'])-1 and e['index']==70 and cond=='C' and a=='M2' and j==0;break
      if stage=='work':work.append(dict(sender=a,phase='work',round=rn,text=z['raw_output']))
      else:finals[a]=z['raw_output']
    assert b['work']==work and b['finals']==finals
    if b['complete']:
      assert len(b['records'])==12 and len(finals)==4 and not b['failed'];ms={a:answer_score(v,targets[e['id']]) for a,v in finals.items()};v=vote(finals,base+1001)
      row['conditions'][cond]=dict(complete=True,members=ms,vote=v,**vote_scores(v,targets[e['id']]),expert_em=ms['M1']['em'])
    else:assert b['failed']==['C'] and len(b['records'])==1;row['conditions'][cond]=dict(complete=False)
  rows.append(row)
assert rows==stored['rows'] and logical==7589 and shared==1114 and injected==200 and len(failures)==1
ordered=sorted(pack['tasks'],key=lambda e:hashlib.sha256(('grounded-run-order-20261107|'+e['id']).encode()).hexdigest())
for pos,e in enumerate(ordered):
  t=load(RUN/f'trials/{e["index"]:03d}.json');prefix=4+t['branches']['B']['orders'][1].index('M1');physical += [r['request_id'] for r in t['initial_records']]+[r['request_id'] for r in t['branches']['B']['records'][:prefix]]
  rotation=pos%6
  for cond in conds[rotation:]+conds[:rotation]:physical += [r['request_id'] for r in t['branches'][cond]['records'][prefix if cond in pub else 0:]]
assert physical==[r['request']['request_id'] for r in responses]
assert [r['request'] for r in attempts]==[r['request'] for r in responses] and [r['attempt_index'] for r in attempts]==list(range(6475))
for cohort in ('fresh','fresh_strict','fresh_answer_overlap','old_coverage','mechanism','all'):
  rs=[r for r in rows if cohort=='all' or r['cohort']==cohort or (cohort=='fresh_strict' and r['cohort']=='fresh' and r['strict_training_answer_isolation']) or (cohort=='fresh_answer_overlap' and r['cohort']=='fresh' and not r['strict_training_answer_isolation'])];summ=stored['summaries'][cohort]
  assert summ['expected']==len(rs)
  for cond in conds:
    valid=[r for r in rs if r['conditions'][cond]['complete']];assert summ['conditions'][cond]['n']==len(valid)
    assert summ['conditions'][cond]['team_expected_em']==sum(r['conditions'][cond]['expected_em'] for r in valid)/len(valid)
    assert summ['conditions'][cond]['expert_em']==sum(r['conditions'][cond]['expert_em'] for r in valid)/len(valid)
  for left,right in [('B_relation','B_check'),('B_relation','B'),('B_check','B'),('B','A'),('D','C')]:
    valid=[r for r in rs if r['conditions'][left]['complete'] and r['conditions'][right]['complete']];values={r['id']:r['conditions'][left]['expected_em']-r['conditions'][right]['expected_em'] for r in valid};groups={i:pack['groups'][i] for i in values};z=summ['contrasts'][left+'-'+right]
    assert z['difference']==sum(values.values())/len(values) and z['cluster_ci95']==paired_interval(values,groups,10000,20261107)
tok=load_tokenizer(c);maximum=0;route=Counter()
for x in responses:
  r=x['request'];z=x['response'];u=z['usage'];assert u['adapter_enabled']==(r['actor']=='M1') and u['disabled_layers']==(0 if r['actor']=='M1' else 252) and u['lora_layers']==252 and u['batch_size']==1;route[r['actor']]+=1
  assert len(u['output_ids'])==u['output_tokens']<=r['max_new_tokens'] and tok.decode(u['output_ids'],skip_special_tokens=True)==z['raw_output']
  assert (u['finish_reason']=='EOS')==(z['status']=='OK')
  n=len(tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs']))
  assert n==u['input_tokens'] and n+r['max_new_tokens']<=c['max_length'];maximum=max(maximum,n+r['max_new_tokens'])
assert sum(z['response']['usage']['output_tokens'] for z in responses)==result['output_tokens']==666803
assert result['status']=='COMPLETED_WITH_INCOMPLETE_BRANCHES' and result['error'] is None and result['calls']==6475
assert before=={str(p):sha(p) for p in RUN.rglob('*') if p.is_file()},'run_files_mutated'
out=dict(verdict='PASS_RECORDS_REQUESTS_ROUTES_AND_SCORES',reviewer='assistant',independence='none/provisional',new_model_calls=0,new_training=0,new_C_H_evaluation=0,logical_records_reconstructed=logical,physical_attempts=len(attempts),physical_returns=len(responses),shared_prefix_records=shared,correct_second_E_instruction_inputs=injected,failures=failures,score_rows_exact=True,all_registered_contrasts_and_bootstraps_exact=True,output_tokens=666803,max_input_plus_cap=maximum,context=c['max_length'],all_output_tokens_decoded=True,actual_routes=dict(route),freeze_unchanged=True,all_original_run_files_unchanged=True,original_run_file_hashes=before)
(HERE/'POST_RUN_AUDIT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='original_run_file_hashes'}),flush=True)
