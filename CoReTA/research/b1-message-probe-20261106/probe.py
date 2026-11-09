"""Finite single-receiver continuation from frozen real histories. No training."""
import argparse,copy,hashlib,json,math,os,sys,time
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from b1_runtime import LocalBackend,validate_runtime
from b1_multi_backend import MultiBackend
from b1_controls import FINAL,replay
from b0_answers import answer_score,paired_interval
HERE=Path(__file__).resolve().parent;SOURCE=ROOT/'runs/b1-dev80-20261106-v1';OUT=ROOT/'runs/b1-fixed-prefix-20261106-v1'
CONDITIONS=('P0','P1','P2');SEED_OFFSETS=(0,100000000)
CHECK='Before concluding, check which entity and relation the question asks about, and verify your judgment against the supplied paragraphs. Treat agreement in the history as a claim to check, not as additional evidence. Accept corrections when the supplied material supports them.'
load=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def atomic(p,value):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_name(p.name+'.tmp')
    with temp.open('w',encoding='utf-8') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    os.replace(temp,p)

def append(p,value):
    with Path(p).open('a',encoding='utf-8') as f:f.write(json.dumps(value,ensure_ascii=False,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())

def decode(request,suffix=''):
    raw=request['payload']['user'];assert raw.startswith('TASK_DATA\n')
    raw=raw[len('TASK_DATA\n'):]
    if suffix and raw.endswith(suffix):raw=raw[:-len(suffix)]
    return json.loads(raw)

def work_request(prefix,condition,repeat):
    assert condition in CONDITIONS and repeat in (0,1)
    r=copy.deepcopy(prefix['request']);d=decode(r)
    if condition=='P0':d['history']=[m for i,m in enumerate(d['history']) if i not in prefix['remove_history_indices']]
    r['payload']['user']='TASK_DATA\n'+json.dumps(d,ensure_ascii=False,indent=2)
    if condition=='P2':r['payload']['system']+='\n\n'+CHECK
    r.update(request_id=f'{prefix["id"]}/{condition}/{repeat}/work',seed=r['seed']+SEED_OFFSETS[repeat])
    return r

def final_request(prefix,condition,repeat,work):
    if not isinstance(work,str) or not work.strip():raise ValueError('work_text_required')
    r=work_request(prefix,condition,repeat);d=decode(r)
    d['history'].append(dict(sender=r['actor'],phase='work',round=r['round'],text=work))
    return dict(request_id=f'{prefix["id"]}/{condition}/{repeat}/final',actor=r['actor'],arm=r['arm'],round=3,stage='final',seed=r['seed']+700000000,max_new_tokens=256,payload=dict(system=FINAL,user='TASK_DATA\n'+json.dumps(d,ensure_ascii=False,indent=2)+prefix['answer_suffix']))

def length(tok,c,r):
    return len(tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs']))

def validate_pack(pack):
    ps=pack['prefixes'];assert len(ps)==32 and len({p['id'] for p in ps})==32
    assert Counter(p['role'] for p in ps)==dict(E=16,B=16) and len({p['task_id'] for p in ps})==16
    assert all(sha(ROOT/p)==h for p,h in pack['sources'].items())
    for p in ps:
        t=load(ROOT/p['source_path']);assert replay(t).export()==t and t['complete']
        r=t['records'][p['source_record_index']]
        assert p['request']=={k:r[k] for k in p['request']}
        assert r['arm']=='B' and r['stage']=='work' and r['max_new_tokens']==1024
        d=decode(r);removed=p['remove_history_indices']
        assert len(set(removed))==len(removed) and all(0<=i<len(d['history']) and d['history'][i]['sender']!=r['actor'] for i in removed)
        assert 'team_information' not in d and d['own_actor']==r['actor']
        assert 'target' not in d and 'answer_aliases' not in d and d['paragraphs']==t['task']['paragraphs']
        assert (p['role']=='E')==(r['actor']=='M1')
        assert decode(work_request(p,'P1',0))==d and work_request(p,'P1',0)['payload']==r['payload']
    return ps

def prepare():
    from b0_training import load_tokenizer
    assert load(HERE/'TESTS.json')['verdict']=='PASS'
    prior=load(SOURCE/'FREEZE.json');assert all(sha(p)==h for p,h in prior['files'].items())
    pack=load(HERE/'PREFIXES.json');ps=validate_pack(pack);c=load(SOURCE/'config.json');validate_runtime(c)
    labels=load(HERE/'LABELS.json')['labels'];assert set(labels)=={p['id'] for p in ps}
    c['purpose']='DEVELOPMENT_LOCAL_MESSAGE_REMOVAL_AND_GENERIC_CHECK';tok=load_tokenizer(c)
    lengths=[]
    for p in ps:
        t=load(ROOT/p['source_path']);response=t['records'][p['source_record_index']]['raw_output']
        assert response==labels[p['id']]['source_original_work']
        for cond in CONDITIONS:
            w=work_request(p,cond,0);f=final_request(p,cond,0,response)
            assert decode(f,p['answer_suffix'])['history'][:-1]==decode(w)['history']
            lengths.append(dict(prefix=p['id'],condition=cond,work_plus_cap=length(tok,c,w)+1024,real_replay_final_plus_cap=length(tok,c,f)+256,synthetic_final_plus_cap=length(tok,c,final_request(p,cond,0,'word '*1023))+256))
    assert max(v[k] for v in lengths for k in ('work_plus_cap','real_replay_final_plus_cap'))<=c['max_length']
    OUT.mkdir(parents=True,exist_ok=False)
    atomic(OUT/'config.json',c);atomic(OUT/'PREFIXES.json',pack);atomic(OUT/'LABELS.json',load(HERE/'LABELS.json'));atomic(OUT/'LENGTHS.json',lengths)
    atomic(OUT/'BUDGET.json',dict(prefixes=32,questions=16,conditions=3,seeds=2,max_calls=384,max_output_tokens=245760,wall_clock_cutoff=None,execution='SERIAL_SINGLETON_ALL_CONDITIONS_REGENERATED',generation_retry=False,labels_only_offline=True,final_policy='IMMEDIATE_PRIVATE_FINAL_AFTER_ONE_NEW_WORK_TURN_NO_FUTURE_PEER_MESSAGES',legacy_config_wall_seconds_unused=True))
    pre=dict(science='PASS',engineering='PASS',scope='PURPOSEFUL_D16_32PREFIX_DEVELOPMENT_NOT_CONFIRMATORY',real_histories_validated=32,real_work_response_replays=96,role_routes=dict(E=16,B=16),max_calls=384,length_max=max(v[k] for v in lengths for k in ('work_plus_cap','real_replay_final_plus_cap')),synthetic_max=max(v['synthetic_final_plus_cap'] for v in lengths),context=c['max_length'],runtime_precise_length_guard=True,reviewer='assistant',independence='none/provisional',new_model_calls=0)
    atomic(OUT/'PREFLIGHT.json',pre)
    files=[HERE/n for n in ('probe.py','launch.py','test_probe.py','PREFIXES.json','LABELS.json','EVENT_REVIEW.json','EXPERIMENT_REVIEW.md','TESTS.json')]
    files += [OUT/n for n in ('config.json','PREFIXES.json','LABELS.json','LENGTHS.json','BUDGET.json','PREFLIGHT.json')]
    files += [Path(p) for p in prior['files']]
    files += [ROOT/p for p in pack['sources']]
    atomic(OUT/'FREEZE.json',dict(files={str(p):sha(p) for p in dict.fromkeys(files)}))
    atomic(OUT/'STATUS.json',dict(status='PREPARED_NOT_LAUNCHED',max_calls=384,new_model_calls=0))
    print(json.dumps(pre),flush=True)

def verify_freeze():
    assert all(sha(p)==h for p,h in load(OUT/'FREEZE.json')['files'].items())

def score():
    ps=load(OUT/'PREFIXES.json')['prefixes'];labels=load(OUT/'LABELS.json')['labels'];cases=load(OUT/'CASES.json')
    results=[]
    for p in ps:
        for rep in (0,1):
            row=dict(prefix=p['id'],task_id=p['task_id'],role=p['role'],kind=p['kind'],repeat=rep,primary_semantic_subset=p['primary_semantic_subset'],neutral_control=p['neutral_control'],pre_state_correct=labels[p['id']]['pre_state_correct'],conditions={})
            for cond in CONDITIONS:
                c=cases.get(f'{p["id"]}/{cond}/{rep}')
                row['conditions'][cond]=dict(status=c['status'],metrics=answer_score(c['final_output'],labels[p['id']]['target']) if c['status']=='OK' else None) if c else dict(status='MISSING',metrics=None)
            row['complete']=all(v['metrics'] is not None for v in row['conditions'].values());results.append(row)
    result=dict(scope='EXPLORATORY_SELECTED_LOCAL_PROBES_NOT_TEAM_EM_OR_POPULATION',expected_prefix_seed_units=64,complete_all_three=sum(r['complete'] for r in results),primary_enabled=False,rows=results,summaries={})
    groups=load(SOURCE/'INPUTS.json')['groups']
    for name,subset in [('all',results),('semantic_primary',[r for r in results if r['primary_semantic_subset']]),('expert',[r for r in results if r['role']=='E']),('ordinary',[r for r in results if r['role']=='B']),('correct_before',[r for r in results if r['pre_state_correct']==1]),('wrong_before',[r for r in results if r['pre_state_correct']==0]),('neutral',[r for r in results if r['neutral_control']])]:
        valid=[r for r in subset if r['complete']];n=len(valid)
        if not n:continue
        summary=dict(expected_units=len(subset),complete_units=n,conditions={c:{k:sum(r['conditions'][c]['metrics'][k] for r in valid)/n for k in ('em','f1')} for c in CONDITIONS},contrasts={})
        for l,r in [('P1','P0'),('P2','P1')]:
            values={f'{q["prefix"]}/{q["repeat"]}':q['conditions'][l]['metrics']['em']-q['conditions'][r]['metrics']['em'] for q in valid}
            mapping={f'{q["prefix"]}/{q["repeat"]}':groups[q['task_id']] for q in valid}
            summary['contrasts'][l+'-'+r]=dict(difference=sum(values.values())/n,cluster_ci95=paired_interval(values,mapping,10000,20261106))
        result['summaries'][name]=summary
    atomic(OUT/'scores.json',result)
    return result

def run():
    import fcntl
    lock=(OUT/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    verify_freeze();a=load(OUT/'APPROVAL.json');assert a['verdict']=='RUN_ALLOWED' and a['freeze_sha256']==sha(OUT/'FREEZE.json')
    (OUT/'STARTED').touch(exist_ok=False)
    c=load(OUT/'config.json');ps=load(OUT/'PREFIXES.json')['prefixes'];cases={};begin=time.monotonic();calls=0;error=None
    atomic(OUT/'STATUS.json',dict(status='LOADING_MODEL',calls=0,max_calls=384))
    try:
        backend=MultiBackend(c)
        def generate(req):
            nonlocal calls
            size=length(backend.tokenizer,c,req)
            if size+req['max_new_tokens']>c['max_length']:return dict(status='INPUT_TOO_LONG',raw_output=None,usage=dict(input_tokens=size,output_tokens=0,response_origin='HOST_LENGTH_CHECK_NO_GENERATION'))
            assert calls<384
            append(OUT/'ATTEMPTS.jsonl',dict(request=req,attempt_index=calls));calls+=1
            response=backend.respond_many([req],math.inf)[0]
            if response['status']=='OK' and (not isinstance(response['raw_output'],str) or not response['raw_output'].strip()):response['status']='EMPTY_OR_NON_TEXT'
            append(OUT/'responses.jsonl',dict(request=req,response=response,source_kind='ACTUAL_LOCAL_MODEL_RESPONSE',fixture=False))
            u=response['usage'];assert u['adapter_enabled']==(req['actor']=='M1') and u['batch_size']==1 and u['lora_layers']==252 and u['disabled_layers']==(0 if req['actor']=='M1' else 252)
            return response
        for pi,p in enumerate(ps):
            for rep in (0,1):
                rotation=(pi+rep)%3;order=CONDITIONS[rotation:]+CONDITIONS[:rotation]
                for cond in order:
                    key=f'{p["id"]}/{cond}/{rep}';w=work_request(p,cond,rep);wr=generate(w)
                    case=dict(prefix=p['id'],condition=cond,repeat=rep,work_request=w,work_response=wr,status='WORK_'+wr['status'],final_output=None)
                    if wr['status']=='OK':
                        f=final_request(p,cond,rep,wr['raw_output']);fr=generate(f);case.update(final_request=f,final_response=fr,final_output=fr['raw_output'],status='OK' if fr['status']=='OK' else 'FINAL_'+fr['status'])
                    cases[key]=case;atomic(OUT/'CASES.json',cases)
                    atomic(OUT/'STATUS.json',dict(status='RUNNING',prefix=p['id'],prefix_position=pi+1,cases_completed=len(cases),expected_cases=192,calls=calls,max_calls=384,elapsed_seconds=time.monotonic()-begin,statuses=dict(Counter(v['status'] for v in cases.values()))))
            # No scores are examined for stopping or selection.
        state='COMPLETE' if all(v['status']=='OK' for v in cases.values()) else 'COMPLETED_WITH_INCOMPLETE_CASES'
    except BaseException as exc:
        state='STOPPED_SYSTEM_FAULT';error=type(exc).__name__+':'+str(exc)
    atomic(OUT/'CASES.json',cases);scored=score()
    responses=[json.loads(s) for s in (OUT/'responses.jsonl').read_text().splitlines()] if (OUT/'responses.jsonl').exists() else []
    result=dict(status=state,error=error,calls=calls,confirmed_returns=len(responses),expected_cases=192,recorded_cases=len(cases),complete_paired_units=scored['complete_all_three'],max_calls=384,no_wall_cutoff=True,elapsed_seconds=time.monotonic()-begin,statuses=dict(Counter(r['response']['status'] for r in responses)),output_tokens=sum(r['response']['usage'].get('output_tokens',0) for r in responses),scope='DEVELOPMENT_LOCAL_RECEIVER_NOT_TEAM_EXPERIMENT',reviewer='assistant',independence='none/provisional')
    atomic(OUT/'RESULTS.json',result);atomic(OUT/'STATUS.json',result)
    print(json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run','score']);args=p.parse_args()
    {'prepare':prepare,'run':run,'score':score}[args.command]()
