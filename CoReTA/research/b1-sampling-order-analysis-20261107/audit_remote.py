"""Independent request reconstruction; no inference or run/score mutations."""
import copy,hashlib,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from b1_controls import WORK,FINAL,vote,vote_scores
from b0_answers import answer_score,paired_interval
from b0_training import load_tokenizer
HERE=Path(__file__).resolve().parent;RUN=ROOT/'runs/b1-sampling-order-cross-20261107-v1';OLD=ROOT/'runs/b1-independent-first-work-20261106-v1'
load=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
lines=lambda p:[json.loads(x) for x in p.read_text().splitlines() if x.strip()]
A=['M1','M2','M3','M4'];C=['B','B_delay'];OFF=[0,100000000]
before={str(p):sha(p) for p in RUN.rglob('*') if p.is_file()}
old_before={str(p):sha(p) for p in OLD.rglob('*') if p.is_file()}
assert sha(RUN/'FREEZE.json')=='86e92af0c0967429f9bc54a0c50f1139a921560e516eb393a43c82789e33bc23'
for p,h in load(RUN/'FREEZE.json')['files'].items():assert sha(p)==h,('frozen_changed',p)
ap=load(RUN/'APPROVAL.json');assert ap['verdict']=='RUN_ALLOWED' and ap['freeze_sha256']==sha(RUN/'FREEZE.json')
for p,h in load(ROOT/'research/b1-independent-first-analysis-20261107/POST_RUN_AUDIT.json')['original_run_file_hashes'].items():assert sha(p)==h
c=load(RUN/'config.json');pack=load(RUN/'INPUTS.json');targets=load(RUN/'LABELS.json')['targets'];scores=load(RUN/'scores.json')
res=load(RUN/'RESULTS.json');responses=lines(RUN/'responses.jsonl');attempts=lines(RUN/'ATTEMPTS.jsonl')
assert len(responses)==len(attempts)==1133 and len({x['request']['request_id'] for x in responses})==1133
byid={x['request']['request_id']:x for x in responses};physical=[];rows=[];logical=shared=first=second=0
keys=['request_id','arm','stage','round','actor','seed','max_new_tokens','payload']
for position,e in enumerate(pack['tasks']):
  for s in (0,1):
    src=load(OLD/f'trials/{e["index"]:03d}-r{s}.json')
    for o in (0,1):
      rng=random.Random(20261102+OFF[o]+e['index']*10000);io=rng.sample(A,4);orders=[rng.sample(A,4) for _ in range(2)]
      if s==o:t=src
      else:
        t=load(RUN/f'trials/{e["index"]:03d}-S{s}O{o}.json');assert t['status']=='COMPLETE'
        assert t['initial_records']==src['initial_records'] and t['initials']==src['initials']
      row=dict(index=e['index'],id=e['id'],sampling=s,order_setting=o,coverage=e['coverage'],mechanism=e['mechanism'],origin='INHERITED_DIAGONAL' if s==o else 'NEW_CROSSED_CELL',initial={a:answer_score(z,targets[e['id']]) for a,z in src['initials'].items()},conditions={})
      for cond in C:
        b=t['branches'][cond];assert b['complete'] and not b['failed'] and b['orders']==orders and b['initial_order']==io
        assert b['initials']==src['initials'] and len(b['records'])==12
        if s!=o:
          assert b['config']['seed']==20261102+OFF[s] and b['config']['order_seed']==20261102+OFF[o]
          history=[];finals={}
          schedule=[('work',rn+1,a) for rn,order in enumerate(orders) for a in order]+[('final',3,a) for a in A]
          for j,(stage,rn,a) in enumerate(schedule):
            rec=b['records'][j];h=[dict(sender=x,phase='initial',text=src['initials'][x]) for x in io]+copy.deepcopy(history)
            if cond=='B_delay' and a=='M1' and stage=='work' and rn==1:
              h=[m for m in h if m['sender']=='M1'];assert len(h)==1;first+=1
            if cond=='B_delay' and a=='M1' and stage=='work' and rn==2:
              assert {m['sender'] for m in h if m['phase']=='initial'}==set(A);second+=1
            data={k:copy.deepcopy(e['task'][k]) for k in ('question','paragraphs')};data.update(own_actor=a,history=h,work_visibility='team_message')
            req=dict(request_id=f'{e["id"]}/S{s}O{o}/{cond}/{j:02d}',arm='B',stage=stage,round=rn,actor=a,seed=20261102+OFF[s]+e['index']*10000+(1000+rn*100 if stage=='work' else 2000)+A.index(a),max_new_tokens=1024 if stage=='work' else 256,payload=dict(system=WORK if stage=='work' else FINAL,user='TASK_DATA\n'+json.dumps(data,ensure_ascii=False,indent=2)+(c['answer_suffix'] if stage=='final' else '')))
            assert {k:rec[k] for k in keys}==req,('contract_mismatch',req['request_id']);logical+=1
            assert rec['status']=='OK' and rec['source_kind']=='ACTUAL_LOCAL_MODEL_RESPONSE' and rec['fixture'] is False and rec['raw_output'].strip()
            if 'shared_prefix_from' in rec:
              z=byid[rec['shared_prefix_from']];assert cond=='B_delay' and j<orders[0].index('M1')
              assert {k:v for k,v in req.items() if k!='request_id'}=={k:v for k,v in z['request'].items() if k!='request_id'}
              assert rec['raw_output']==z['response']['raw_output'] and rec['usage']==z['response']['usage'];shared+=1
            else:
              z=byid[req['request_id']];assert z['request']==req and z['response']=={k:rec[k] for k in ('raw_output','status','usage')}
            if stage=='work':history.append(dict(sender=a,phase='work',round=rn,text=rec['raw_output']))
            else:finals[a]=rec['raw_output']
          assert history==b['work'] and finals==b['finals']
        ms={a:answer_score(z,targets[e['id']]) for a,z in b['finals'].items()};v=vote(b['finals'],20261102+OFF[s]+e['index']*10000+1001)
        ini=row['initial']['M1']['em'];last=ms['M1']['em'];row['conditions'][cond]=dict(complete=True,members=ms,vote=v,**vote_scores(v,targets[e['id']]),expert_em=last,expert_harm=int(ini==1 and last==0),expert_correction=int(ini==0 and last==1))
      row['paired_complete']=True;row['delta']=row['conditions']['B_delay']['expected_em']-row['conditions']['B']['expected_em'];rows.append(row)
  for s,o in ([(0,1),(1,0)] if position%2==0 else [(1,0),(0,1)]):
    t=load(RUN/f'trials/{e["index"]:03d}-S{s}O{o}.json');prefix=t['branches']['B']['orders'][0].index('M1')
    physical.extend(r['request_id'] for r in t['branches']['B']['records'][:prefix])
    for cond in (C if (position+s+o)%2==0 else C[::-1]):physical.extend(r['request_id'] for r in t['branches'][cond]['records'][prefix:])
assert rows==scores['rows'] and logical==1200 and shared==67 and first==second==50
assert physical==[x['request']['request_id'] for x in responses]
assert [x['request'] for x in attempts]==[x['request'] for x in responses] and [x['attempt_index'] for x in attempts]==list(range(1133))
ci_checks={}
for name,flag in [('coverage','coverage'),('mechanism','mechanism'),('union',None)]:
  sub=[r for r in rows if flag is None or r[flag]];summ=scores['summaries'][name]
  for s in (0,1):
    for o in (0,1):
      rs=[r for r in sub if r['sampling']==s and r['order_setting']==o];cell=summ['cells'][f'S{s}O{o}']
      for cond in C:
        assert cell['conditions'][cond]['team_expected_em']==sum(r['conditions'][cond]['expected_em'] for r in rs)/len(rs)
        assert cell['conditions'][cond]['expert_em']==sum(r['conditions'][cond]['expert_em'] for r in rs)/len(rs)
      assert cell['delta']==sum(r['delta'] for r in rs)/len(rs)
  ds={e['id']:{(r['sampling'],r['order_setting']):r['delta'] for r in sub if r['id']==e['id']} for e in pack['tasks'] if flag is None or e[flag]}
  fns={'average_intervention_delta':lambda d:sum(d.values())/4,'sampling_at_O0':lambda d:d[1,0]-d[0,0],'sampling_at_O1':lambda d:d[1,1]-d[0,1],'order_at_S0':lambda d:d[0,1]-d[0,0],'order_at_S1':lambda d:d[1,1]-d[1,0],'sampling_main_on_delta':lambda d:(d[1,0]+d[1,1]-d[0,0]-d[0,1])/2,'order_main_on_delta':lambda d:(d[0,1]+d[1,1]-d[0,0]-d[1,0])/2,'interaction_on_delta':lambda d:d[1,1]-d[1,0]-d[0,1]+d[0,0]}
  ci_checks[name]={}
  for key,fn in fns.items():
    values={i:fn(d) for i,d in ds.items()};groups={i:pack['groups'][i] for i in values};stored=summ['factorial_contrasts'][key]
    assert abs(stored['difference']-sum(values.values())/len(values))<1e-12
    ci=paired_interval(values,groups,10000,20261107)
    ci_checks[name][key]=dict(point=stored['difference'],stored_ci=stored['cluster_ci95'],deterministic_pack_order_ci=ci)
tok=load_tokenizer(c);maximum=0
for x in responses:
  r=x['request'];z=x['response'];u=z['usage'];assert z['status']=='OK' and x['source_kind']=='ACTUAL_LOCAL_MODEL_RESPONSE' and x['fixture'] is False
  assert u['adapter_enabled']==(r['actor']=='M1') and u['disabled_layers']==(0 if r['actor']=='M1' else 252) and u['lora_layers']==252 and u['batch_size']==1
  assert u['finish_reason']=='EOS' and u['ended_with_eos'] is True and len(u['output_ids'])==u['output_tokens']<=r['max_new_tokens']
  assert tok.decode(u['output_ids'],skip_special_tokens=True)==z['raw_output']
  n=len(tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs']))
  assert n==u['input_tokens'] and n+r['max_new_tokens']<=c['max_length'];maximum=max(maximum,n+r['max_new_tokens'])
assert res['status']=='COMPLETE' and res['incomplete_or_missing_cells']==[] and res['calls']==res['confirmed_returns']==1133
assert sum(x['response']['usage']['output_tokens'] for x in responses)==res['output_tokens']==131217
assert before=={str(p):sha(p) for p in RUN.rglob('*') if p.is_file()}
assert old_before=={str(p):sha(p) for p in OLD.rglob('*') if p.is_file()}
out=dict(verdict='PASS_RECORDS_REQUESTS_AND_SCORE_POINTS',reviewer='assistant',independence='none/provisional',new_model_calls=0,logical_new_requests=logical,shared_new_prefix=shared,physical_returns=1133,initial_source_reuse_verified=50,diagonal_inherited_cells=50,first_E_censored=first,second_E_restored=second,official_rows_exact=True,all_new_tokens_decoded=True,max_input_plus_cap=maximum,context=c['max_length'],output_tokens=131217,original_and_new_run_files_unchanged=True,freeze_unchanged=True,bootstrap_note='Stored scoring uses unordered set iteration for bootstrap block order. Independent pack-order replay below; raw scores preserved.',factorial_interval_replay=ci_checks,original_run_file_hashes=before)
(HERE/'POST_RUN_AUDIT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('original_run_file_hashes','factorial_interval_replay')}),flush=True)
