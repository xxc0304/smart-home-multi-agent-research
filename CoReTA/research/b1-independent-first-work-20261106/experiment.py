"""Five matched branches; only expert first-work peer visibility changes. No training."""
import argparse,copy,hashlib,json,math,os,sys,time
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from b1_controls import Trial,vote,vote_scores
from b1_runtime import validate_runtime
from b1_multi_backend import MultiBackend
from b0_answers import answer_score,paired_interval
HERE=Path(__file__).resolve().parent
OUT=ROOT/'runs/b1-independent-first-work-20261106-v1'
SOURCE=ROOT/'runs/b1-dev80-20261106-v1'
CONDITIONS=('A','B','C','D','B_delay');OFFSETS=(0,100000000);MAX_CALLS=3200
load=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def atomic(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.tmp')
    with tmp.open('w',encoding='utf-8') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)

def append(p,v):
    with Path(p).open('a',encoding='utf-8') as f:f.write(json.dumps(v,ensure_ascii=False,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())

def decode(r,suffix=''):
    text=r['payload']['user'];assert text.startswith('TASK_DATA\n');text=text[10:]
    if suffix and text.endswith(suffix):text=text[:-len(suffix)]
    return json.loads(text)

def options(c,entry,rep):
    assert rep in (0,1)
    return dict(expert_actor='M1',seed=c['seed']+OFFSETS[rep],task_index=entry['index'],fixture=False,answer_tokens=c['answer_tokens'],answer_suffix=c['answer_suffix'],output_contract=c['output_contract'])

def initial_request(t,rep):
    r=t.next_request()
    if r is None or r['stage']!='initial':return None
    t.pending['request_id']=f'{t.task["id"]}/r{rep}/initial/{t.cursor}'
    return copy.deepcopy(t.pending)

class Branch(Trial):
    def __init__(self,entry,c,rep,condition,initial_records):
        assert condition in CONDITIONS
        super().__init__(entry['task'],**options(c,entry,rep))
        self.condition=condition;self.rep=rep;self.arm='B' if condition=='B_delay' else condition
        for rec in initial_records:
            r=initial_request(self,rep)
            assert r is not None and all(rec[k]==v for k,v in r.items())
            self.submit(r['request_id'],rec['raw_output'],status=rec['status'],usage=rec['usage'],source_kind=rec['source_kind'])
        assert len(self.initials)==4 and not self.initial_failed
        self.schedule=self.schedule[:4]+[s for s in self.schedule[4:] if s[1]==self.arm]
        assert len(self.schedule)==16 and self.cursor==4

    def next_request(self):
        r=super().next_request()
        if r is None:return None
        p=self.pending;p['request_id']=f'{self.task["id"]}/r{self.rep}/{self.condition}/{self.cursor-4:02d}'
        if self.condition=='B_delay' and p['stage']=='work' and p['round']==1 and p['actor']=='M1':
            d=decode(p);d['history']=[m for m in d['history'] if m['sender']=='M1']
            assert len(d['history'])==1 and d['history'][0]['phase']=='initial'
            p['payload']['user']='TASK_DATA\n'+json.dumps(d,ensure_ascii=False,indent=2)
        return copy.deepcopy(p)

    @property
    def complete(self):return not self.failed and len(self.finals[self.arm])==4

    def export(self):
        return copy.deepcopy(dict(protocol='B1_FIRST_WORK_EXPOSURE_V1',condition=self.condition,rep=self.rep,arm=self.arm,config=self.config,initial_order=self.initial_order,orders=self.orders,initials=self.initials,work=self.work[self.arm],finals=self.finals[self.arm],records=self.records[4:],complete=self.complete,failed=sorted(self.failed),logical_expected_branch_calls=12))

def length(tok,c,r):
    return len(tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs']))

def verify_pack(pack):
    assert pack['unique_questions']==25 and len(pack['tasks'])==25
    assert len({e['id'] for e in pack['tasks']})==25
    assert sum(e['coverage'] for e in pack['tasks'])==24 and sum(e['mechanism'] for e in pack['tasks'])==8
    assert pack['repeats']==list(OFFSETS) and set(pack['groups'])=={e['id'] for e in pack['tasks']}
    for p,h in pack['source_sha256'].items():assert sha(ROOT/p)==h,('source_changed',p)
    for e in pack['tasks']:assert e['task']==load(ROOT/e['source_path'])['task']

def score():
    pack=load(OUT/'INPUTS.json');labels=load(OUT/'LABELS.json')['targets'];rows=[]
    for e in pack['tasks']:
        for rep in (0,1):
            p=OUT/f'trials/{e["index"]:03d}-r{rep}.json'
            item=load(p) if p.exists() else None
            row=dict(index=e['index'],id=e['id'],rep=rep,coverage=e['coverage'],mechanism=e['mechanism'],conditions={},initial=None)
            target=labels[e['id']]
            if item and len(item['initials'])==4:
                row['initial']={a:answer_score(v,target) for a,v in item['initials'].items()}
            for cond in CONDITIONS:
                b=item['branches'].get(cond) if item else None
                if not b or not b['complete']:row['conditions'][cond]=dict(complete=False);continue
                members={a:answer_score(v,target) for a,v in b['finals'].items()}
                voted=vote(b['finals'],b['config']['seed']+e['index']*10000+1001)
                row['conditions'][cond]=dict(complete=True,members=members,vote=voted,**vote_scores(voted,target),expert_em=members['M1']['em'],expert_initial_em=row['initial']['M1']['em'],expert_harm=int(row['initial']['M1']['em']==1 and members['M1']['em']==0),expert_correction=int(row['initial']['M1']['em']==0 and members['M1']['em']==1))
            rows.append(row)
    result=dict(scope='REUSED_INPUT_SCREENED_DEVELOPMENT_NOT_CONFIRMATORY',rows=rows,summaries={})
    for name,subset in [('coverage',[r for r in rows if r['coverage']]),('mechanism',[r for r in rows if r['mechanism']]),('union',rows)]:
        paired=[r for r in subset if r['conditions']['B']['complete'] and r['conditions']['B_delay']['complete']]
        allfive=[r for r in subset if all(v['complete'] for v in r['conditions'].values())]
        summary=dict(expected_units=len(subset),expected_unique_questions=len({r['id'] for r in subset}),complete_B_pair_units=len(paired),complete_all_five_units=len(allfive),conditions={},primary=None,all_five_common={})
        for cond in CONDITIONS:
            valid=[r for r in paired if r['conditions'][cond]['complete']]
            if valid:summary['conditions'][cond]=dict(n=len(valid),team_expected_em=sum(r['conditions'][cond]['expected_em'] for r in valid)/len(valid),expert_em=sum(r['conditions'][cond]['expert_em'] for r in valid)/len(valid))
        if paired:
            values={f'{r["id"]}/r{r["rep"]}':r['conditions']['B_delay']['expected_em']-r['conditions']['B']['expected_em'] for r in paired}
            groups={f'{r["id"]}/r{r["rep"]}':pack['groups'][r['id']] for r in paired}
            summary['primary']=dict(contrast='B_delay-B',difference=sum(values.values())/len(values),cluster_ci95=paired_interval(values,groups,10000,20261106),gain_units=sum(v>0 for v in values.values()),loss_units=sum(v<0 for v in values.values()),unchanged_units=sum(v==0 for v in values.values()),warning='Two seeds are clustered with task dependency groups, not independent questions; incomplete pairs reported separately.')
        for cond in CONDITIONS:
            if allfive:summary['all_five_common'][cond]=dict(n=len(allfive),team_expected_em=sum(r['conditions'][cond]['expected_em'] for r in allfive)/len(allfive),expert_em=sum(r['conditions'][cond]['expert_em'] for r in allfive)/len(allfive))
        result['summaries'][name]=summary
    atomic(OUT/'scores.json',result);return result

def prepare():
    from b0_training import load_tokenizer
    tests=load(HERE/'TESTS.json')
    assert tests['verdict']=='PASS' and tests['code_sha256']==sha(HERE/'experiment.py') and tests['tests_sha256']==sha(HERE/'test_experiment.py')
    review=(HERE/'EXPERIMENT_REVIEW.md').read_text(encoding='utf-8');assert 'SCIENCE_PASS' in review and 'ENGINEERING_PENDING_PREPARE' in review
    pack=load(HERE/'INPUTS.json');verify_pack(pack)
    c=load(SOURCE/'config.json');q=validate_runtime(c);c['purpose']='DEVELOPMENT_EXPERT_FIRST_WORK_DELAY_FULL_DOWNSTREAM'
    tok=load_tokenizer(c);lengths=[];replays=0;max_history_peers_removed=0
    for e in pack['tasks']:
        old=load(ROOT/e['source_path']);initials=[r for r in old['records'] if r['stage']=='initial']
        # Old task9 is excluded for input semantics; other selected old initials are complete.
        assert len(initials)==4 and all(r['status']=='OK' for r in initials)
        # Re-ID actual initial records to new within-batch shared prefix for interface replay.
        t=Trial(e['task'],**options(c,e,0));recs=[]
        for oldr in initials:
            r=initial_request(t,0);assert r['payload']==oldr['payload'] and r['seed']==oldr['seed']
            recs.append(t.submit(r['request_id'],oldr['raw_output'],status=oldr['status'],usage=oldr['usage'],source_kind=oldr['source_kind']))
        for cond in CONDITIONS:
            b=Branch(e,c,0,cond,recs);arm=b.arm;source=[r for r in old['records'] if r['arm']==arm]
            for oldr in source:
                r=b.next_request();assert r is not None
                altered=cond=='B_delay' and r['actor']=='M1' and r['stage']=='work' and r['round']==1
                if not altered:assert r['payload']==oldr['payload']
                else:max_history_peers_removed=max(max_history_peers_removed,len(decode(oldr)['history'])-len(decode(r)['history']))
                n=length(tok,c,r)+r['max_new_tokens'];assert n<=c['max_length']
                lengths.append(dict(index=e['index'],condition=cond,request_id=r['request_id'],input_plus_cap=n,altered_first_work=altered))
                b.submit(r['request_id'],oldr['raw_output'],status=oldr['status'],usage=oldr['usage'],source_kind=oldr['source_kind']);replays+=1
            assert b.next_request() is None
    # Stress histories using actual full long responses, never sent to model.
    real=[]
    for e in pack['tasks']:real.extend(load(ROOT/e['source_path'])['records'])
    long_work=max((r for r in real if r['stage']=='work' and r['status']=='OK'),key=lambda r:r['usage']['output_tokens'])['raw_output']
    long_initial=max((r for r in real if r['stage']=='initial' and r['status']=='OK'),key=lambda r:r['usage']['output_tokens'])['raw_output']
    pressure=[]
    for e in pack['tasks']:
        t=Trial(e['task'],**options(c,e,0));recs=[]
        for _ in range(4):
            r=initial_request(t,0);recs.append(t.submit(r['request_id'],long_initial,source_kind='ACTUAL_LOCAL_MODEL_RESPONSE'))
        for cond in CONDITIONS:
            b=Branch(e,c,0,cond,recs)
            while (r:=b.next_request()) is not None:
                n=length(tok,c,r)+r['max_new_tokens'];pressure.append(n)
                b.submit(r['request_id'],long_work if r['stage']=='work' else long_initial,source_kind='ACTUAL_LOCAL_MODEL_RESPONSE')
    assert max(pressure)<=c['max_length'],('full_real_response_pressure_over_context',max(pressure))
    largest=max(lengths,key=lambda z:z['input_plus_cap'])
    OUT.mkdir(parents=True,exist_ok=False)
    for n in ('INPUTS.json','LABELS.json','SELECTION_REVIEW.json'):atomic(OUT/n,load(HERE/n))
    atomic(OUT/'config.json',c);atomic(OUT/'LENGTHS.json',dict(real_replay=lengths,full_actual_long_response_history_pressure_max=max(pressure),stress_only_not_model_results=True))
    budget=dict(unique_questions=25,coverage_questions=24,mechanism_questions=8,overlap=7,repeats=2,conditions=list(CONDITIONS),max_calls=MAX_CALLS,max_output_tokens=2355200,wall_clock_cutoff=None,legacy_config_wall_seconds_unused=True,generation_retry=False,physical_calls_may_be_lower='B and B_delay share newly generated prefix before first expert work',execution='ALL_SINGLETON_IDENTICAL_SHAPE',failure_policy='Independent branch isolation for output limit/input length/empty; shared initial failure skips task-seed; any system fault stops batch.')
    atomic(OUT/'BUDGET.json',budget)
    pf=dict(science='PASS',engineering='PASS',real_full_response_replays=replays,selected_questions=25,all_five_conditions=True,max_real_replay_input_plus_cap=largest['input_plus_cap'],full_actual_long_response_history_pressure_max=max(pressure),context=c['max_length'],max_peer_history_entries_removed=max_history_peers_removed,precise_runtime_guard=True,runtime_no_silent_truncation=True,qualification=q['qualification'],new_model_calls=0,reviewer='assistant',independence='none/provisional')
    atomic(OUT/'PREFLIGHT.json',pf)
    files=[HERE/n for n in ('experiment.py','launch.py','test_experiment.py','run_checks.py','TESTS.json','INPUTS.json','LABELS.json','SELECTION_REVIEW.json','EXPERIMENT_REVIEW.md','BRIEF.md')]
    files += [OUT/n for n in ('INPUTS.json','LABELS.json','SELECTION_REVIEW.json','config.json','LENGTHS.json','BUDGET.json','PREFLIGHT.json')]
    files += [ROOT/p for p in pack['source_sha256']]
    # Bind core protocol/runtime/scorer implementations in addition to experiment code.
    files += [ROOT/p for p in ('tools/b1_controls.py','tools/b1_runtime.py','tools/b1_multi_backend.py','tools/b1_stop_status.py','tools/b1_output_contract.py','tools/b0_answers.py','tools/b0_training.py','tools/expert_mechanism_protocol.py','tools/prepare_answer_only_expert.py','tools/prepare_expert_training.py','research/musique-data-preparation-20261030/official_scorer/metrics/answer.py')]
    files += [Path(c['adapter_path'])/n for n in ('adapter_config.json','adapter_model.safetensors','b0_origin.json')]
    files += [SOURCE/'config.json',Path(c['baseline_C_score']),Path(c['expert_C_score']),ROOT/'implement-stage/expert-answer-only-20261101/C_GROUPS.json']
    atomic(OUT/'FREEZE.json',dict(files={str(p):sha(p) for p in dict.fromkeys(files)}))
    atomic(OUT/'STATUS.json',dict(status='PREPARED_NOT_LAUNCHED',calls=0,max_calls=MAX_CALLS))
    print(json.dumps(pf),flush=True)

def verify_freeze():
    for p,h in load(OUT/'FREEZE.json')['files'].items():assert sha(p)==h,('frozen_input_changed',p)

def run():
    import fcntl
    lock=(OUT/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    verify_freeze();a=load(OUT/'APPROVAL.json');assert a['verdict']=='RUN_ALLOWED' and a['freeze_sha256']==sha(OUT/'FREEZE.json')
    (OUT/'STARTED').touch(exist_ok=False)
    c=load(OUT/'config.json');pack=load(OUT/'INPUTS.json');calls=0;begin=time.monotonic();completed=0;error=None
    atomic(OUT/'STATUS.json',dict(status='LOADING_MODEL',calls=0,max_calls=MAX_CALLS))
    try:
        backend=MultiBackend(c)
        def generate(r):
            nonlocal calls
            n=length(backend.tokenizer,c,r)
            if n+r['max_new_tokens']>c['max_length']:
                response=dict(status='INPUT_TOO_LONG',raw_output=None,usage=dict(input_tokens=n,output_tokens=0,host_no_generation=True))
                append(OUT/'host_failures.jsonl',dict(request=r,response=response));return response
            assert calls<MAX_CALLS
            append(OUT/'ATTEMPTS.jsonl',dict(attempt_index=calls,request=r));calls+=1
            response=backend.respond_many([r],math.inf)[0]
            if response['status']=='OK' and (not isinstance(response['raw_output'],str) or not response['raw_output'].strip()):response['status']='EMPTY_OR_NON_TEXT'
            append(OUT/'responses.jsonl',dict(request=r,response=response,source_kind='ACTUAL_LOCAL_MODEL_RESPONSE',fixture=False))
            u=response['usage'];assert u['adapter_enabled']==(r['actor']=='M1') and u['batch_size']==1 and u['lora_layers']==252 and u['disabled_layers']==(0 if r['actor']=='M1' else 252)
            return response
        for position,e in enumerate(pack['tasks']):
            for rep in (0,1):
                t=Trial(e['task'],**options(c,e,rep));item=dict(index=e['index'],id=e['id'],rep=rep,initial_records=[],initials={},branches={},status='RUNNING')
                p=OUT/f'trials/{e["index"]:03d}-r{rep}.json'
                for _ in range(4):
                    r=initial_request(t,rep)
                    if r is None:break
                    z=generate(r);rec=t.submit(r['request_id'],z['raw_output'],status=z['status'],usage=z['usage'],source_kind='ACTUAL_LOCAL_MODEL_RESPONSE')
                    item['initial_records'].append(rec);item['initials']=copy.deepcopy(t.initials);atomic(p,item)
                if len(t.initials)==4 and not t.initial_failed:
                    bs={cond:Branch(e,c,rep,cond,t.records) for cond in CONDITIONS}
                    # True fork: upstream B messages are shared in this new run only.
                    while (r:=bs['B'].next_request()) is not None and not (r['actor']=='M1' and r['stage']=='work' and r['round']==1):
                        rd=bs['B_delay'].next_request();assert rd['payload']==r['payload'] and rd['seed']==r['seed']
                        z=generate(r)
                        for cond,request in [('B',r),('B_delay',rd)]:
                            rec=bs[cond].submit(request['request_id'],z['raw_output'],status=z['status'],usage=z['usage'],source_kind='ACTUAL_LOCAL_MODEL_RESPONSE')
                            if cond=='B_delay':rec['shared_prefix_from']=r['request_id']
                            item['branches'][cond]=bs[cond].export()
                        atomic(p,item)
                    rotation=(position+rep)%len(CONDITIONS);order=CONDITIONS[rotation:]+CONDITIONS[:rotation]
                    for cond in order:
                        b=bs[cond]
                        while (r:=b.next_request()) is not None:
                            z=generate(r);b.submit(r['request_id'],z['raw_output'],status=z['status'],usage=z['usage'],source_kind='ACTUAL_LOCAL_MODEL_RESPONSE')
                            item['branches'][cond]=b.export();atomic(p,item)
                            atomic(OUT/'STATUS.json',dict(status='RUNNING',index=e['index'],question_number=e['index']+1,position=position+1,total_questions=25,repeat=rep,condition=cond,calls=calls,max_calls=MAX_CALLS,completed_task_seed_units=completed,total_task_seed_units=50,elapsed_seconds=time.monotonic()-begin))
                        item['branches'][cond]=b.export();atomic(p,item)
                    item['status']='COMPLETE' if all(b.complete for b in bs.values()) else 'INCOMPLETE_BRANCHES'
                else:item['status']='SHARED_INITIAL_FAILED'
                completed+=1;atomic(p,item)
        state='FINISHED'
    except BaseException as exc:
        state='STOPPED_SYSTEM_FAULT';error=type(exc).__name__+':'+str(exc)
    # Scoring is offline and never used to stop, select or retry generation.
    scored=score();responses=[json.loads(s) for s in (OUT/'responses.jsonl').read_text().splitlines()] if (OUT/'responses.jsonl').exists() else []
    failed_units=[]
    for e in pack['tasks']:
        for rep in (0,1):
            p=OUT/f'trials/{e["index"]:03d}-r{rep}.json';v=load(p) if p.exists() else None
            if not v or v['status']!='COMPLETE':failed_units.append(dict(index=e['index'],rep=rep,status=v['status'] if v else 'MISSING',failed_conditions=[k for k,b in v['branches'].items() if not b['complete']] if v else list(CONDITIONS)))
    if state=='FINISHED':state='COMPLETE' if not failed_units else 'COMPLETED_WITH_INCOMPLETE_BRANCHES'
    result=dict(status=state,error=error,calls=calls,confirmed_returns=len(responses),max_calls=MAX_CALLS,completed_task_seed_units=completed,total_task_seed_units=50,incomplete_or_missing_units=failed_units,elapsed_seconds=time.monotonic()-begin,no_wall_cutoff=True,statuses=dict(Counter(z['response']['status'] for z in responses)),output_tokens=sum(z['response']['usage'].get('output_tokens',0) for z in responses),scope='INPUT_SCREENED_REUSED_DEVELOPMENT',new_training=False)
    atomic(OUT/'RESULTS.json',result);atomic(OUT/'STATUS.json',result);lock.close();print(json.dumps(result),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','run','score']);args=parser.parse_args();{'prepare':prepare,'run':run,'score':score}[args.command]()
