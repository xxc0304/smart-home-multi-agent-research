"""Fixed D80 extension: 8 inherited +72 new, no elapsed-time cutoff."""
import argparse,copy,hashlib,importlib.util,json,math,os,signal,subprocess,sys,time
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];os.chdir(ROOT);sys.path.insert(0,str(ROOT/'tools'))
from b1_controls import Trial,replay,summarize
from b1_runtime import load_json,trial_parameters,validate_runtime,SOURCE,SPLIT,selected_rows,prefix_rows
from expert_mechanism_protocol import validate_task
from prepare_expert_training import dependency_groups
from b1_multi_backend import MultiBackend
HERE=Path(__file__).resolve().parent;OUT=ROOT/'runs/b1-dev80-20261106-v1'
PRIOR=ROOT/'runs/b1-longwork1024-fullflow-20261105-v1'
PRIOR_SCRIPT=ROOT/'engineering/b1-longwork1024-fullflow-20261105/experiment.py'
spec=importlib.util.spec_from_file_location('frozen_v6_scheduler',PRIOR_SCRIPT);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
MAX_NEW=72*52

def atomic(p,value):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_name(p.name+'.tmp')
    with temp.open('w',encoding='utf-8') as s:s.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n');s.flush();os.fsync(s.fileno())
    os.replace(temp,p)

def append(p,value):
    with Path(p).open('a',encoding='utf-8') as s:s.write(json.dumps(value,ensure_ascii=False,allow_nan=False)+'\n');s.flush();os.fsync(s.fileno())

def lines(p):
    return [json.loads(s) for s in Path(p).read_text().splitlines()] if Path(p).exists() else []

def data(n=80,labels=False):
    assert n in (8,12,16,20,24,28,32,36,40,44,48,52,56,60,64,68,72,76,80)
    all_ids=load_json(SPLIT)['roles']['D_development']['ids'];assert len(all_ids)==80
    ids=all_ids[:n];tasks=[validate_task(t) for t in prefix_rows(SOURCE/'inputs/D_development.jsonl',ids)]
    buckets=dependency_groups(selected_rows(SOURCE/'corpus_index.jsonl',all_ids))
    groups={k:b[0] for b in buckets for k in b if k in ids}
    targets={r['id']:r for r in prefix_rows(SOURCE/'scoring/D_development.jsonl',ids)} if labels else None
    assert len(tasks)==n and len(groups)==n
    return tasks,groups,targets

def length(tok,c,r):
    ids=tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs'])
    return len(ids)

def execute(c,tasks,indices,backend,emit,attempt,check_length,existing=None):
    trials={i:replay(existing[i]) if existing and i in existing else Trial(tasks[i],**trial_parameters(c,i)) for i in indices}
    backend.traces=trials
    for position in range(52):
        ready=[]
        for i,t in trials.items():
            r=t.next_request()
            if r is not None and int(r['request_id'].rsplit('|',1)[1])==position:ready.append((i,r))
        valid=[]
        for i,r in ready:
            size=check_length(r)
            if size+r['max_new_tokens']>c['max_length']:
                response=dict(raw_output=None,status='INPUT_TOO_LONG',usage=dict(input_tokens=size,output_tokens=0,output_cap=r['max_new_tokens'],host_failure=True,response_origin='HOST_LENGTH_CHECK_NO_MODEL_GENERATION'))
                rec=trials[i].submit(r['request_id'],**response,source_kind=getattr(backend,'source_kind','ACTUAL_LOCAL_MODEL_RESPONSE'));emit(i,rec,trials[i].export(),0,position,False)
            else:valid.append((i,r))
        for entries in old.batches(valid,'batch2',c):
            requests=[r for _,r in entries];attempt(entries,position)
            # No per-call, per-cell or global wall clock limit. Tokens bound work.
            responses=backend.respond_many(requests,math.inf)
            assert len(responses)==len(entries),'response_count_mismatch'
            for (i,r),response in zip(entries,responses):
                status=response['status'];raw=response['raw_output']
                if status=='OK' and not isinstance(raw,str):status='NON_TEXT_OUTPUT'
                elif status=='OK' and not raw.strip():status='EMPTY_OUTPUT'
                rec=trials[i].submit(r['request_id'],raw,status=status,usage=response.get('usage'),source_kind=getattr(backend,'source_kind','ACTUAL_LOCAL_MODEL_RESPONSE'))
                emit(i,rec,trials[i].export(),len(entries),position,True)
    assert all(t.next_request() is None for t in trials.values())
    return {i:t.export() for i,t in trials.items()}

def verify_freeze():
    f=load_json(OUT/'FREEZE.json');assert all(sha(p)==h for p,h in f['files'].items()),'frozen_input_changed'
    a=load_json(OUT/'APPROVAL.json');assert a['verdict']=='RUN_ALLOWED' and a['freeze_sha256']==sha(OUT/'FREEZE.json')

def prepare():
    from b0_training import load_tokenizer
    assert load_json(HERE/'TESTS.json')['verdict']=='PASS'
    pf=load_json(PRIOR/'FREEZE.json');assert all(sha(p)==h for p,h in pf['files'].items())
    assert load_json(ROOT/'engineering/b1-longwork1024-fullflow-20261105/POST_RUN_AUDIT.json')['verdict']=='PASS_RECORDS_AND_D8_COMPLETENESS'
    tasks,groups,_=data();c=load_json(PRIOR/'config.json');qualification=validate_runtime(c);tok=load_tokenizer(c)
    history={i:load_json(PRIOR/f'batch2/trials/{i:03d}.json') for i in range(8)}
    for i,t in history.items():assert t['complete'] and replay(t).export()==t and t['task']==tasks[i] and t['config']==trial_parameters(c,i)
    class Cached:
        source_kind='ACTUAL_LOCAL_MODEL_RESPONSE'
        def respond_many(self,requests,remaining):
            assert math.isinf(remaining)
            result=[]
            for r in requests:
                t=next(t for t in history.values() if r['request_id'].startswith(t['task']['id']+'|'))
                q=t['records'][int(r['request_id'].rsplit('|',1)[1])];assert all(q[k]==v for k,v in r.items())
                result.append({k:copy.deepcopy(q[k]) for k in ('raw_output','status','usage')})
            return result
    for start in (0,4):
        cache=Cached();traces=execute(c,tasks,range(start,start+4),cache,lambda *_:None,lambda *_:None,lambda r:length(tok,c,r))
        assert traces=={i:history[i] for i in range(start,start+4)}
    lengths=[];pressure=[]
    for i,task in enumerate(tasks):
        t=Trial(task,**trial_parameters(dict(c,fixture=True),i));maximum=0
        while (r:=t.next_request()) is not None:
            size=length(tok,c,r);maximum=max(maximum,size+r['max_new_tokens'])
            if r['stage']=='initial':lengths.append(dict(index=i,id=task['id'],input_tokens=size,total_with_cap=size+r['max_new_tokens']))
            t.submit(r['request_id'],'word '*1023 if r['stage']=='work' else 'answer '*255,source_kind='SYNTHETIC_PRESSURE_NOT_MODEL_EVIDENCE')
        pressure.append(dict(index=i,total_with_cap=maximum))
    assert max(x['total_with_cap'] for x in lengths)<=c['max_length']
    assert max(x['total_with_cap'] for x in pressure)<=c['max_length'],'synthetic_pressure_overflow_requires_review'
    disk=__import__('shutil').disk_usage(ROOT);assert disk.free>10*2**30,'need_10GiB_free_for_durable_logs'
    OUT.mkdir(exist_ok=False,parents=True)
    atomic(OUT/'config.json',c);atomic(OUT/'INPUTS.json',dict(tasks=tasks,groups=groups))
    atomic(OUT/'BUDGET.json',dict(n_expected=80,inherited=8,new_questions=72,max_new_model_requests=MAX_NEW,work_cap=1024,answer_cap=256,wall_clock_cutoff=None,per_request_wall_cutoff=None,deadline_policy='USER_REQUEST_NO_TIME_CUTOFF',finite_bound='FIXED_IDS_REQUEST_COUNT_AND_TOKEN_CAPS',legacy_config_wall_seconds='UNUSED_BY_THIS_RUNNER',failure_policy='ISOLATE_DEPENDENT_ARM; NO_GENERATION_RETRY; STOP_ON_PROTOCOL_FAULT_OR_SECOND_OOM_CELL'))
    for i,t in history.items():atomic(OUT/f'trials/{i:03d}.json',t)
    for start in range(8,80,4):
        cell=OUT/f'cells/{start:03d}';cell.mkdir(parents=True)
        atomic(cell/'STATUS.json',dict(status='PENDING',indices=list(range(start,start+4))))
    pre=dict(science='PASS',engineering='PASS',scope='D80_DEVELOPMENT_NOT_CONFIRMATORY',new_model_generations=0,historical_actual_traces_replayed=8,historical_responses_replayed=416,no_wall_timer=True,prior_eight_not_regenerated=True,max_new_calls=MAX_NEW,n_D_ids=80,no_new_C_H_reads=True,initial_max_context_plus_cap=max(x['total_with_cap'] for x in lengths),synthetic_pressure_max_context_plus_cap=max(x['total_with_cap'] for x in pressure),pressure_is_not_arbitrary_output_upper_bound=True,qualification=qualification,disk_free_bytes=disk.free)
    atomic(OUT/'LENGTHS.json',dict(initials=lengths,synthetic_pressure=pressure));atomic(OUT/'PREFLIGHT.json',pre)
    paths=[Path(__file__),HERE/'launch.py',HERE/'test_runner.py',HERE/'run_checks.py',HERE/'TESTS.json',HERE/'TESTS.log',HERE/'EXPERIMENT_REVIEW.md',PRIOR/'FREEZE.json',ROOT/'engineering/b1-longwork1024-fullflow-20261105/POST_RUN_AUDIT.json',PRIOR_SCRIPT,SPLIT,SOURCE/'inputs/D_development.jsonl',SOURCE/'scoring/D_development.jsonl',SOURCE/'corpus_index.jsonl']
    paths += [PRIOR/f'batch2/trials/{i:03d}.json' for i in range(8)]
    paths += [OUT/n for n in ('config.json','INPUTS.json','BUDGET.json','PREFLIGHT.json','LENGTHS.json')]
    paths += [Path(p) for p in pf['files'] if '/tools/' in p or '/metrics/' in p or '/adapter/' in p or p==c['baseline_C_score'] or p==c['expert_C_score']]
    paths=list(dict.fromkeys(paths));atomic(OUT/'FREEZE.json',dict(files={str(p):sha(p) for p in paths}))
    for p in paths:
        if p.suffix=='.py':dest=OUT/'frozen_sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
    print(json.dumps(pre),flush=True)

def recover(start):
    c=load_json(OUT/'config.json');tasks=load_json(OUT/'INPUTS.json')['tasks'];cell=OUT/f'cells/{start:03d}'
    trials={i:Trial(tasks[i],**trial_parameters(c,i)) for i in range(start,start+4)}
    rows=lines(cell/'responses.jsonl');seen=set()
    for row in rows:
        i=row['item_index'];q=row['record'];assert q['request_id'] not in seen;seen.add(q['request_id']);r=trials[i].next_request();assert r and all(q[k]==v for k,v in r.items())
        trials[i].submit(q['request_id'],q['raw_output'],status=q['status'],usage=q['usage'],source_kind=q['source_kind'])
    # An interrupted in-flight request is never regenerated or pretended complete.
    for a in lines(cell/'ATTEMPTS.jsonl'):
        for i,rid in a['requests']:
            if rid in seen:continue
            r=trials[i].next_request();assert r and r['request_id']==rid
            q=trials[i].submit(rid,None,status='INTERRUPTED_UNCONFIRMED',usage=dict(host_failure=True,response_origin='NO_CONFIRMED_MODEL_RESPONSE_NO_RETRY'),source_kind='ACTUAL_LOCAL_MODEL_RESPONSE')
            row=dict(item_index=i,record=q,batch_size=0,generated=False,position=int(rid.rsplit('|',1)[1]))
            append(cell/'responses.jsonl',row);seen.add(rid)
    for i,t in trials.items():atomic(OUT/f'trials/{i:03d}.json',t.export())
    return {i:t.export() for i,t in trials.items()}

def worker(start):
    verify_freeze();cell=OUT/f'cells/{start:03d}';c=load_json(OUT/'config.json');tasks=load_json(OUT/'INPUTS.json')['tasks'];existing=recover(start)
    status='RUNNING';error=None;begin=time.monotonic()
    atomic(cell/'STATUS.json',dict(status=status,indices=list(range(start,start+4))))
    try:
        import torch
        backend=MultiBackend(c)
        def attempt(entries,pos):
            append(cell/'ATTEMPTS.jsonl',dict(position=pos,requests=[[i,r['request_id']] for i,r in entries]))
        def emit(i,record,trace,n,pos,generated):
            row=dict(item_index=i,record=record,batch_size=n,position=pos,generated=generated)
            append(cell/'responses.jsonl',row);atomic(OUT/f'trials/{i:03d}.json',trace)
            rows=lines(cell/'responses.jsonl')
            atomic(cell/'STATUS.json',dict(status='RUNNING',indices=list(range(start,start+4)),recorded=len(rows),generated_returns=sum(x['generated'] for x in rows),position=pos,elapsed_seconds=time.monotonic()-begin))
            print(json.dumps(dict(cell=start,item=i,request=record['request_id'],status=record['status'],returned=len(rows))),flush=True)
        ts=execute(c,tasks,range(start,start+4),backend,emit,attempt,lambda r:length(backend.tokenizer,c,r),existing)
        status='COMPLETE' if all(t['complete'] for t in ts.values()) else 'COMPLETE_WITH_INCOMPLETE_TRIALS'
    except BaseException as exc:
        status='OOM' if 'OutOfMemory' in type(exc).__name__ else 'FATAL';error=type(exc).__name__+':'+str(exc)
    rows=lines(cell/'responses.jsonl');ts=[load_json(OUT/f'trials/{i:03d}.json') for i in range(start,start+4)]
    review=dict(status=status,error=error,n_complete=sum(t['complete'] for t in ts),n_expected=4,recorded=len(rows),generated_returns=sum(x['generated'] for x in rows),elapsed_seconds=time.monotonic()-begin,statuses=dict(Counter(x['record']['status'] for x in rows)),reviewer='assistant',independence='none/provisional')
    atomic(cell/'STATUS.json',review);atomic(cell/'POST_RUN_REVIEW.json',review)
    print(json.dumps(review),flush=True)
    return 0 if status.startswith('COMPLETE') else 2 if status=='OOM' else 3

def checkpoint(n):
    tasks,groups,targets=data(n,labels=True);c=load_json(OUT/'config.json')
    traces=[load_json(p) for p in sorted((OUT/'trials').glob('*.json')) if int(p.stem)<n]
    for t in traces:
        i=t['config']['task_index'];assert t['task']==tasks[i] and t['config']==trial_parameters(c,i) and replay(t).export()==t
    score=summarize(traces,targets,[t['id'] for t in tasks],groups)
    score.update(primary_enabled=False,scope='D80_SEQUENTIAL_DEVELOPMENT_NOT_CONFIRMATORY')
    atomic(OUT/f'checkpoints/{n:03d}/scores.json',score)
    # Explicitly report expert gains/losses and readout separately from team score.
    diagnostic=dict(n_expected=n,n_complete=score['n_complete'],initial=score.get('initial_baseline'),arms=score.get('arms'),contrasts=score.get('contrasts'),initial_correctness_strata={},complete_indices=[t['config']['task_index'] for t in traces if t['complete']])
    strata=Counter()
    for r in score['reports']:
        if not r['initial']:continue
        e=bool(r['initial']['members']['M1']['em']);b=any(r['initial']['members'][a]['em'] for a in ('M2','M3','M4'))
        strata[f'E{int(e)}_anyB{int(b)}']+=1
    diagnostic['initial_correctness_strata']=dict(strata)
    atomic(OUT/f'checkpoints/{n:03d}/SUMMARY.json',diagnostic)
    return diagnostic

def controller():
    import fcntl
    lock=(OUT/'controller.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    verify_freeze();started=time.monotonic();oom_cells=0;fatal=None
    atomic(OUT/'STATUS.json',dict(status='RUNNING',expected_tasks=80,inherited_tasks=8,max_new_calls=MAX_NEW,no_wall_clock_cutoff=True))
    try:
        for start in range(8,80,4):
            verify_freeze();cell=OUT/f'cells/{start:03d}';state=load_json(cell/'STATUS.json')
            if state['status'].startswith('COMPLETE'):continue
            if state['status']=='FATAL':raise RuntimeError('previous_fatal_cell_requires_audit')
            with (cell/'worker.log').open('a') as log:
                proc=subprocess.Popen([sys.executable,str(Path(__file__)),'worker','--start',str(start)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
                atomic(OUT/'STATUS.json',dict(status='RUNNING',cell_start=start,worker_pid=proc.pid,expected_tasks=80,inherited_tasks=8,max_new_calls=MAX_NEW,no_wall_clock_cutoff=True,elapsed_seconds=time.monotonic()-started))
                code=proc.wait()
            state=load_json(cell/'STATUS.json')
            if code not in (0,2):raise RuntimeError(f'worker_failed_code_{code}:'+str(state.get('error')))
            if code==2:
                oom_cells+=1;recover(start)
                if oom_cells>=2:raise RuntimeError('two_OOM_cells_stop_systemic_fault')
            summary=checkpoint(start+4)
            attempts=sum(len(a['requests']) for p in (OUT/'cells').glob('*/ATTEMPTS.jsonl') for a in lines(p));assert attempts<=MAX_NEW
            atomic(OUT/'STATUS.json',dict(status='RUNNING',processed_through=start+4,n_complete=summary['n_complete'],attempted_requests=attempts,no_wall_clock_cutoff=True,elapsed_seconds=time.monotonic()-started))
        summary=checkpoint(80)
        state='COMPLETE' if summary['n_complete']==80 else 'COMPLETED_WITH_INCOMPLETE_TRIALS'
    except BaseException as exc:state='STOPPED_SYSTEM_FAULT';fatal=type(exc).__name__+':'+str(exc)
    rows=[x for p in (OUT/'cells').glob('*/responses.jsonl') for x in lines(p)]
    attempts=sum(len(a['requests']) for p in (OUT/'cells').glob('*/ATTEMPTS.jsonl') for a in lines(p))
    result=dict(status=state,error=fatal,expected_tasks=80,inherited_tasks=8,new_tasks_planned=72,attempted_requests=attempts,confirmed_generated_returns=sum(r['generated'] for r in rows),host_records=sum(not r['generated'] for r in rows),max_new_calls=MAX_NEW,statuses=dict(Counter(r['record']['status'] for r in rows)),unknown=sum(isinstance(r['record']['raw_output'],str) and r['record']['raw_output'].strip().lower()=='unknown' for r in rows),elapsed_seconds=time.monotonic()-started,no_wall_clock_cutoff=True,primary_enabled=False,scope='DEVELOPMENT_NOT_CONFIRMATORY',oom_cells=oom_cells)
    atomic(OUT/'RESULTS.json',result);atomic(OUT/'STATUS.json',result)
    (OUT/'RESULTS.md').write_text('# D80 extension: '+state+'\n\n```json\n'+json.dumps(result,ensure_ascii=False,indent=2)+'\n```\n\nScores and expert/communication/readout diagnostics are stored separately at checkpoints/*/scores.json and SUMMARY.json.\n')
    print(json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','controller','worker']);p.add_argument('--start',type=int);a=p.parse_args()
    if a.command=='worker':sys.exit(worker(a.start))
    (prepare if a.command=='prepare' else controller)()
