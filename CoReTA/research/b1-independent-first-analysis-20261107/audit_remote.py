"""Read-only independent contract reconstruction; no inference or score rewriting."""
import copy,hashlib,json,random,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from b1_controls import WORK,FINAL,vote,vote_scores
from prepare_answer_only_expert import SYSTEM
from b0_answers import answer_score,paired_interval
from b0_training import load_tokenizer
RUN=ROOT/'runs/b1-independent-first-work-20261106-v1';HERE=Path(__file__).resolve().parent
load=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
lines=lambda p:[json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
ACTORS=['M1','M2','M3','M4'];CONDS=['A','B','C','D','B_delay']
before={str(p):sha(p) for p in RUN.rglob('*') if p.is_file()}
f=load(RUN/'FREEZE.json');assert all(sha(p)==h for p,h in f['files'].items())
a=load(RUN/'APPROVAL.json');assert a['verdict']=='RUN_ALLOWED' and a['freeze_sha256']==sha(RUN/'FREEZE.json')
assert sha(RUN/'FREEZE.json')=='9c9f8616414f8c2b03cb2d852e1c43fe89ee2cab896e752c501f06cfaaf75edb'
c=load(RUN/'config.json');p=load(RUN/'INPUTS.json');labels=load(RUN/'LABELS.json')['targets'];s=load(RUN/'scores.json');result=load(RUN/'RESULTS.json')
attempts=lines(RUN/'ATTEMPTS.jsonl');responses=lines(RUN/'responses.jsonl')
assert len(attempts)==len(responses)==3133 and len({x['request']['request_id'] for x in responses})==3133
byid={x['request']['request_id']:x for x in responses};physical=[];all_records=[];shared=0;reconstructed=0;rows=[];censored=0;restored=0
request_keys=['request_id','arm','stage','round','actor','seed','max_new_tokens','payload']
def expected(entry,rep,condition,stage,round_no,actor,pos,initial_order,initials,work):
    arm='B' if condition=='B_delay' else condition
    data=copy.deepcopy(entry['task'])
    assert set(data)=={'id','question','paragraphs'}
    # task_data deliberately exposes question+paragraphs only, never task id.
    data.pop('id')
    base=c['seed']+(100000000 if rep else 0)+entry['index']*10000
    if stage=='initial':rid=f'{entry["id"]}/r{rep}/initial/{pos}';seed=base+ACTORS.index(actor)
    else:
        ids=initial_order if arm in ('B','D') else [actor]
        history=[dict(sender=x,phase='initial',text=initials[x]) for x in ids]
        history += [copy.deepcopy(x) for x in work if arm in ('B','D') or x['sender']==actor]
        if condition=='B_delay' and stage=='work' and round_no==1 and actor=='M1':history=[x for x in history if x['sender']=='M1']
        data.update(own_actor=actor,history=history,work_visibility='team_message' if arm in ('B','D') else 'private_work')
        if arm in ('C','D'):data['team_information']='Participant M1 performed better on separate calibration questions from this task. This does not establish that their answer to the current question is correct.'
        rid=f'{entry["id"]}/r{rep}/{condition}/{pos:02d}'
        seed=base+(1000+round_no*100 if stage=='work' else 2000)+ACTORS.index(actor)
    suffix=c['answer_suffix'] if stage in ('initial','final') else ''
    return dict(request_id=rid,arm=None if stage=='initial' else arm,stage=stage,round=round_no,actor=actor,seed=seed,max_new_tokens=1024 if stage=='work' else 256,payload=dict(system=SYSTEM if stage=='initial' else WORK if stage=='work' else FINAL,user='TASK_DATA\n'+json.dumps(data,ensure_ascii=False,indent=2)+suffix))
def check_record(rec,r):
    global reconstructed
    assert {k:rec[k] for k in request_keys}==r,('request_contract_mismatch',r['request_id'])
    assert rec['status']=='OK' and rec['source_kind']=='ACTUAL_LOCAL_MODEL_RESPONSE' and rec['fixture'] is False
    assert isinstance(rec['raw_output'],str) and rec['raw_output'].strip()
    reconstructed+=1;all_records.append(rec)
for position,e in enumerate(p['tasks']):
    assert e['task']['id']==e['id'] and set(e['task']['paragraphs'][0])=={'idx','title','paragraph_text'}
    for rep in (0,1):
        t=load(RUN/f'trials/{e["index"]:03d}-r{rep}.json');assert t['status']=='COMPLETE' and len(t['initial_records'])==4 and set(t['branches'])==set(CONDS)
        base=c['seed']+(100000000 if rep else 0)+e['index']*10000;rng=random.Random(base)
        io=rng.sample(ACTORS,4);orders=[rng.sample(ACTORS,4) for _ in range(2)];initials={}
        for i,rec in enumerate(t['initial_records']):
            r=expected(e,rep,None,'initial',0,ACTORS[i],i,io,{},[]);check_record(rec,r);initials[ACTORS[i]]=rec['raw_output'];physical.append(r['request_id'])
        assert initials==t['initials']
        row=dict(index=e['index'],id=e['id'],rep=rep,coverage=e['coverage'],mechanism=e['mechanism'],conditions={},initial={x:answer_score(v,labels[e['id']]) for x,v in initials.items()})
        for cond in CONDS:
            b=t['branches'][cond];assert b['complete'] and not b['failed'] and b['orders']==orders and b['initial_order']==io and b['initials']==initials and len(b['records'])==12
            schedule=[('work',rn+1,x) for rn,order in enumerate(orders) for x in order]+[('final',3,x) for x in ACTORS]
            work=[];finals={}
            for i,(stage,rn,actor) in enumerate(schedule):
                rec=b['records'][i];r=expected(e,rep,cond,stage,rn,actor,i,io,initials,work);check_record(rec,r)
                if stage=='work':work.append(dict(sender=actor,phase='work',round=rn,text=rec['raw_output']))
                else:finals[actor]=rec['raw_output']
                if cond=='B_delay' and stage=='work' and actor=='M1':
                    data=json.loads(r['payload']['user'][10:])
                    if rn==1:assert len(data['history'])==1 and data['history'][0]['sender']=='M1';censored+=1
                    else:assert {x['sender'] for x in data['history'] if x['phase']=='initial'}==set(ACTORS);restored+=1
                if 'shared_prefix_from' in rec:
                    original=byid[rec['shared_prefix_from']];assert cond=='B_delay' and i<orders[0].index('M1')
                    assert {k:r[k] for k in request_keys if k!='request_id'}=={k:original['request'][k] for k in request_keys if k!='request_id'}
                    assert rec['raw_output']==original['response']['raw_output'] and rec['usage']==original['response']['usage'];shared+=1
                else:
                    original=byid[r['request_id']];assert original['request']==r and original['response']=={k:rec[k] for k in ('raw_output','status','usage')}
            assert work==b['work'] and finals==b['finals']
            members={x:answer_score(v,labels[e['id']]) for x,v in finals.items()};v=vote(finals,base+1001)
            first,last=row['initial']['M1']['em'],members['M1']['em']
            row['conditions'][cond]=dict(complete=True,members=members,vote=v,**vote_scores(v,labels[e['id']]),expert_em=last,expert_initial_em=first,expert_harm=int(first==1 and last==0),expert_correction=int(first==0 and last==1))
        prefix=orders[0].index('M1')
        physical += [x['request_id'] for x in t['branches']['B']['records'][:prefix]]
        rotation=(position+rep)%5;order=CONDS[rotation:]+CONDS[:rotation]
        for cond in order:physical += [x['request_id'] for x in t['branches'][cond]['records'][prefix if cond in ('B','B_delay') else 0:]]
        rows.append(row)
assert rows==s['rows'] and shared==67 and reconstructed==3200 and censored==restored==50
assert physical==[x['request']['request_id'] for x in responses]
assert [x['request'] for x in attempts]==[x['request'] for x in responses]
assert [x['attempt_index'] for x in attempts]==list(range(3133))
for group_name,subset in [('coverage',[r for r in rows if r['coverage']]),('mechanism',[r for r in rows if r['mechanism']]),('union',rows)]:
    su=s['summaries'][group_name];assert su['complete_all_five_units']==len(subset)
    for cond in CONDS:
        assert su['conditions'][cond]['team_expected_em']==sum(x['conditions'][cond]['expected_em'] for x in subset)/len(subset)
        assert su['conditions'][cond]['expert_em']==sum(x['conditions'][cond]['expert_em'] for x in subset)/len(subset)
    delta={f'{r["id"]}/r{r["rep"]}':r['conditions']['B_delay']['expected_em']-r['conditions']['B']['expected_em'] for r in subset}
    groups={f'{r["id"]}/r{r["rep"]}':p['groups'][r['id']] for r in subset}
    assert su['primary']['difference']==sum(delta.values())/len(subset) and su['primary']['cluster_ci95']==paired_interval(delta,groups,10000,20261106)
tok=load_tokenizer(c);maximum=0;max_id=None
for x in responses:
    r=x['request'];z=x['response'];u=z['usage'];assert z['status']=='OK' and x['source_kind']=='ACTUAL_LOCAL_MODEL_RESPONSE' and x['fixture'] is False
    assert u['adapter_enabled']==(r['actor']=='M1') and u['disabled_layers']==(0 if r['actor']=='M1' else 252) and u['lora_layers']==252 and u['batch_size']==1
    assert u['finish_reason']=='EOS' and u['ended_with_eos'] is True and len(u['output_ids'])==u['output_tokens']<=r['max_new_tokens']
    assert tok.decode(u['output_ids'],skip_special_tokens=True)==z['raw_output']
    tokens=len(tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs']))
    assert tokens==u['input_tokens'] and tokens+r['max_new_tokens']<=c['max_length']
    if tokens+r['max_new_tokens']>maximum:maximum=tokens+r['max_new_tokens'];max_id=r['request_id']
assert sum(x['response']['usage']['output_tokens'] for x in responses)==result['output_tokens']==366543
assert result['status']=='COMPLETE' and result['incomplete_or_missing_units']==[] and result['calls']==3133
assert before=={str(p):sha(p) for p in RUN.rglob('*') if p.is_file()},'original_run_files_changed'
out=dict(verdict='PASS_RECORDS_REQUESTS_AND_SCORES',reviewer='assistant',independence='none/provisional',new_model_calls=0,questions=25,task_seed_units=50,complete_branches=250,logical_calls=3200,shared_new_upstream=67,physical_attempts=len(attempts),physical_returns=len(responses),independent_requests_reconstructed=reconstructed,censored_first_E_verified=censored,restored_second_E_verified=restored,output_tokens=366543,max_input_plus_cap=maximum,max_request=max_id,context=c['max_length'],official_rows_exact=True,primary_bootstrap_exact=True,all_tokens_decoded_exact=True,freeze_unchanged=True,all_original_run_files_unchanged=True,original_run_file_hashes=before)
(HERE/'POST_RUN_AUDIT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='original_run_file_hashes'}),flush=True)
