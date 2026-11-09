"""Immutable 32-request screen of four execution policies, max 256 outputs."""
import argparse,hashlib,json,os,signal,sys,time
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];os.chdir(ROOT);sys.path.insert(0,str(ROOT/'tools'))
from b0_answers import write_json,answer_score
from b1_runtime import load_json,development_data,validate_runtime
from b1_controls import replay
from b1_multi_backend import MultiBackend
HERE=Path(__file__).resolve().parent;OUT=ROOT/'runs/b1-strategy-screen-20261105-v1'
OLD=ROOT/'runs/b1-dev32-final-20261104-v2';PRIOR=ROOT/'runs/b1-parallel-fullflow-20261105-v1'
ENGINES=('serial','batch2','batch4','batch4_sorted');SOFT=2400
FIELDS=('request_id','arm','stage','round','actor','seed','max_new_tokens','payload')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def plans(requests,lengths,engine):
    size=1 if engine=='serial' else 2 if engine=='batch2' else 4
    pools={}
    for i,r in enumerate(requests):pools.setdefault((r['stage'],r['actor']=='M1',r['max_new_tokens']),[]).append(i)
    batches=[]
    for indices in pools.values():
        if engine=='batch4_sorted':indices=sorted(indices,key=lambda i:(lengths[i],i))
        batches += [indices[start:start+size] for start in range(0,len(indices),size)]
    flat=[i for b in batches for i in b]
    assert sorted(flat)==list(range(len(requests))) and len(set(flat))==len(requests)
    for b in batches:assert len(b)==size and len({(requests[i]['actor']=='M1',requests[i]['max_new_tokens'],requests[i]['stage']) for i in b})==1
    return batches

def prepare():
    from b0_training import load_tokenizer
    tasks,groups,_=development_data(8)
    c=load_json(OLD/'manifest.json')['config'];c.update(wall_seconds=SOFT,purpose='FIXED_HISTORY_EXECUTOR_SCREEN_ONLY')
    assert not c.get('output_contract') and c['answer_tokens']==256 and c['work_tokens']==512
    qualification=validate_runtime(c);tok=load_tokenizer(c);requests=[];sources=[]
    for i,task in enumerate(tasks):
        p=OLD/f'trials/{i:03d}.json';t=load_json(p);sources.append(p)
        assert t['complete'] and replay(t).export()==t and t['task']==task
        for actor in ('M1','M2'):
            for stage in ('work','final'):
                r=next(r for r in t['records'] if r['stage']==stage and r['actor']==actor and r['arm']=='ABCD'[i%4] and (stage!='work' or r['round']==1))
                requests.append({k:r[k] for k in FIELDS})
    assert len(requests)==32 and len({r['request_id'] for r in requests})==32
    lengths=[]
    for r in requests:
        ids=tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs'])
        assert len(ids)+r['max_new_tokens']<=c['max_length'];lengths.append(len(ids))
    matrix={e:plans(requests,lengths,e) for e in ENGINES}
    # Compare actual callback mapping to frozen requests, and independent-failure bookkeeping.
    for engine,bs in matrix.items():
        recovered={}
        for b in bs:
            for i in b:
                source=load_json(sources[next(j for j,t in enumerate(tasks) if requests[i]['request_id'].startswith(t['id']+'|'))])
                old=next(r for r in source['records'] if r['request_id']==requests[i]['request_id'])
                assert all(old[k]==requests[i][k] for k in FIELDS);recovered[i]=old['raw_output']
        assert len(recovered)==32
    stub=MultiBackend.__new__(MultiBackend);stub.config=c
    bads=([],[requests[0]]*3,[requests[0],requests[2]],[requests[0],requests[1]])
    for bad in bads:
        try:stub.respond_many(bad,10)
        except ValueError:pass
        else:raise AssertionError('invalid_batch_accepted')
    assert sum(s!='OK' for s in ('OK','OUTPUT_LIMIT'))==1 and sum(s!='OK' for s in ('OUTPUT_LIMIT',)*3)==3
    OUT.mkdir(parents=True,exist_ok=False)
    write_json(OUT/'config.json',c);write_json(OUT/'REQUESTS.json',requests);write_json(OUT/'PLAN.json',dict(lengths=lengths,batches=matrix))
    pre=dict(science='PASS',engineering='PASS',launch_requires_previous_complete_and_audited=True,n_requests=32,real_traces_replayed=8,full_payloads_recovered_each_policy=True,all_plans_same_requests=True,invalid_batches_rejected=True,qualification=qualification,max_input_plus_cap=max(n+r['max_new_tokens'] for n,r in zip(lengths,requests)),new_generations_max=256,soft_seconds=SOFT,hard_seconds=2700,per_cell_seconds=600,methods=ENGINES,conditional_final_answers_per_cell=16)
    write_json(OUT/'PREFLIGHT.json',pre)
    paths=[Path(__file__),HERE/'launch.py',HERE/'EXPERIMENT_REVIEW.md',OUT/'config.json',OUT/'REQUESTS.json',OUT/'PLAN.json',OUT/'PREFLIGHT.json',OLD/'manifest.json',PRIOR/'config.json',PRIOR/'FREEZE.json']+sources
    paths += [ROOT/'tools'/n for n in ('b1_multi_backend.py','b1_runtime.py','b1_controls.py','b1_output_contract.py','b1_stop_status.py','b0_answers.py','b0_training.py','expert_mechanism_protocol.py','prepare_answer_only_expert.py')]
    paths += [Path(c[k]) for k in ('baseline_C_score','expert_C_score')]+[p for p in Path(c['adapter_path']).iterdir() if p.is_file()]
    paths += list((ROOT/'research/musique-data-preparation-20261030/official_scorer/metrics').glob('*.py'))
    paths += [ROOT/'data/external/musique-v1.0-20261030'/n for n in ('inputs/D_development.jsonl','scoring/D_development.jsonl','corpus_index.jsonl')]
    paths += [ROOT/'research/musique-data-preparation-20261030/SPLIT_MANIFEST.json',ROOT/'implement-stage/expert-answer-only-20261101/C_GROUPS.json']
    write_json(OUT/'FREEZE.json',dict(files={str(p):sha(p) for p in paths}))
    for p in paths:
        if p.suffix=='.py':dest=OUT/'frozen_sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
    print(json.dumps(pre),flush=True)

def summarize_result(status,error,started,timings):
    requests=load_json(OUT/'REQUESTS.json');rows=[json.loads(s) for s in (OUT/'responses.jsonl').read_text().splitlines()] if (OUT/'responses.jsonl').exists() else []
    assert len(rows)<=256 and len({(r['repeat'],r['engine'],r['index']) for r in rows})==len(rows)
    assert all(r['request']==requests[r['index']] and r['usage']['adapter_enabled']==(r['request']['actor']=='M1') for r in rows)
    _,_,targets=development_data(8,targets=True);cells=[]
    for t in timings:
        rs=[r for r in rows if r['engine']==t['engine'] and r['repeat']==t['repeat']]
        finals=[r for r in rs if r['request']['stage']=='final'];scored=[]
        for r in finals:
            task_id=r['request']['request_id'].rsplit('|',1)[0]
            score=answer_score(r['raw_output'],targets[task_id]) if r['status']=='OK' else None
            scored.append(dict(index=r['index'],score=score))
        valid=len(finals)==16 and all(r['score'] is not None for r in scored)
        cells.append(dict(**t,n_generated=len(rs),statuses=dict(Counter(r['status'] for r in rs)),final_n=len(finals),final_EM=sum(r['score']['em'] for r in scored)/16 if valid else None,final_F1=sum(r['score']['f1'] for r in scored)/16 if valid else None,unknown=sum(r['raw_output'].strip().lower()=='unknown' for r in finals if isinstance(r['raw_output'],str)),output_tokens=sum(r['usage']['output_tokens'] for r in rs),input_tokens=sum(r['usage']['input_tokens'] for r in rs),padded_input_tokens=sum(r['usage'].get('padded_input_tokens',r['usage']['input_tokens']) for r in rs)))
    comparisons=[];repeats=[]
    lookup={(r['engine'],r['repeat'],r['index']):r for r in rows}
    for e in ENGINES:
        for i in range(32):
            a,b=lookup.get((e,0,i)),lookup.get((e,1,i))
            if a and b:repeats.append(dict(engine=e,index=i,same_tokens=a['usage']['output_ids']==b['usage']['output_ids'],same_text=a['raw_output']==b['raw_output']))
            if e=='serial':continue
            for rep in (0,1):
                a,b=lookup.get(('serial',rep,i)),lookup.get((e,rep,i))
                if a and b:comparisons.append(dict(engine=e,repeat=rep,index=i,same_tokens=a['usage']['output_ids']==b['usage']['output_ids'],same_text=a['raw_output']==b['raw_output']))
    aggregate={}
    for e in ENGINES:
        cs=[x for x in cells if x['engine']==e]
        if cs:aggregate[e]=dict(seconds=sum(x['seconds'] for x in cs),output_tokens=sum(x['output_tokens'] for x in cs),generated=sum(x['n_generated'] for x in cs),ok=sum(x['statuses'].get('OK',0) for x in cs),final_EM=sum(x['final_EM'] for x in cs)/2 if len(cs)==2 and all(x['final_EM'] is not None for x in cs) else None,padding_input_fraction=1-sum(x['input_tokens'] for x in cs)/sum(x['padded_input_tokens'] for x in cs),peak_allocated_bytes=max(x['peak_allocated_bytes'] for x in cs))
    for e,v in aggregate.items():
        v['time_ratio_vs_serial']=aggregate.get('serial',{}).get('seconds',0)/v['seconds'] if v['seconds'] else None
        v['eligible_for_fullflow_validation']=e!='serial' and v['generated']==v['ok']==64 and v['time_ratio_vs_serial']>=1.15
        v['observed_final_quality_decreased']=v['final_EM'] is not None and aggregate.get('serial',{}).get('final_EM') is not None and v['final_EM']<aggregate['serial']['final_EM']
    attempts=[json.loads(s) for s in (OUT/'ATTEMPTS.jsonl').read_text().splitlines()] if (OUT/'ATTEMPTS.jsonl').exists() else []
    if status=='COMPLETE' and any(r['status']!='OK' for r in rows):status='COMPLETED_WITH_NON_EOS'
    result=dict(status=status,error=error,primary_enabled=False,scope='FIXED_HISTORY_TECHNICAL_SCREEN_NOT_TEAM_QUALITY_EQUIVALENCE',n_generated=len(rows),n_attempted_requests=sum(len(x['indices']) for x in attempts),n_expected=256,elapsed_seconds=time.monotonic()-started,cells=cells,aggregate=aggregate,within_engine_repeats=repeats,cross_engine_comparisons=comparisons,adoption='NO_AUTOMATIC_FULL_TEAM_ADOPTION')
    write_json(OUT/'RESULTS.json',result);write_json(OUT/'STATUS.json',dict(status=status,error=error,n_generated=len(rows)))
    md='# 执行策略筛选：'+status+'\n\n助手自审none/provisional。固定32历史载荷×4策略×2遍，非完整团队质量实验。原v2提示/预算不变，无新增Unknown指导。实际生成'+str(len(rows))+'/256，错误'+str(error)+'。\n\n```json\n'+json.dumps(aggregate,ensure_ascii=False,indent=2)+'\n```\n\n候选只允许进入后续有限完整流程验证，不代表质量等价或稳定最优。\n'
    (OUT/'RESULTS.md').write_text(md);(HERE/'RESULTS.md').write_text(md)
    entry=f"## 2026-11-05 四种执行策略固定载荷筛选：{status}\n\n见engineering/b1-strategy-screen-20261105/RESULTS.md与runs/b1-strategy-screen-20261105-v1/RESULTS.json。serial/batch2/batch4/batch4长度分组，原v2完整历史32载荷、各2遍，实际{len(rows)}/256。错误{error}；条件终答分不冒充团队质量。助手自审none/provisional，完成技术筛选才PASS，未自动采用/全32/训练/C-H。\n\n"
    (OUT/'FINAL_STAGE_ENTRY.md').write_text(entry)
    for name in ('handoff.md','CURRENT_STATE.md','experiment/results.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md'):
        p=ROOT/name;p.write_text(entry+p.read_text())
    print(json.dumps(dict(status=status,n_generated=len(rows),aggregate=aggregate,error=error)),flush=True)

def run():
    f=load_json(OUT/'FREEZE.json');a=load_json(OUT/'APPROVAL.json')
    assert all(sha(p)==h for p,h in f['files'].items()) and a['verdict']=='RUN_ALLOWED' and a['freeze_sha256']==sha(OUT/'FREEZE.json')
    assert sha(PRIOR/'RESULTS.json')==a['prior_result_sha256']
    (OUT/'LAUNCHED').touch(exist_ok=False);started=time.monotonic();timings=[];status='RUNNING';error=None
    def interrupted(*_):raise RuntimeError('hard_timeout_or_interrupt')
    signal.signal(signal.SIGTERM,interrupted)
    try:
        import torch
        c=load_json(OUT/'config.json');validate_runtime(c);backend=MultiBackend(c)
        write_json(OUT/'BACKEND.json',dict(load_seconds=time.monotonic()-started,effective_generation_config=backend.generation_config.to_dict()))
        requests=load_json(OUT/'REQUESTS.json');matrix=load_json(OUT/'PLAN.json')['batches'];n=0
        for repeat,order in enumerate((ENGINES,tuple(reversed(ENGINES)))):
            for engine in order:
                torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();begin=time.monotonic();failures=0;cell_calls=0
                try:
                    for indices in matrix[engine]:
                        remaining=min(SOFT-(time.monotonic()-started),600-(time.monotonic()-begin))
                        if remaining<=0:raise RuntimeError('soft_budget')
                        selected=[requests[i] for i in indices]
                        with (OUT/'ATTEMPTS.jsonl').open('a') as stream:stream.write(json.dumps(dict(engine=engine,repeat=repeat,indices=indices))+'\n')
                        responses=backend.respond_many(selected,remaining)
                        assert len(responses)==len(indices)
                        invalid_output=False
                        for i,r,response in zip(indices,selected,responses):
                            row=dict(engine=engine,repeat=repeat,index=i,request=r,**response)
                            with (OUT/'responses.jsonl').open('a') as stream:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
                            n+=1;cell_calls+=1;failures+=row['status']!='OK'
                            invalid_output=invalid_output or not isinstance(row['raw_output'],str) or not row['raw_output'].strip()
                            state=dict(status='RUNNING',engine=engine,repeat=repeat,n_generated=n,elapsed_seconds=time.monotonic()-started)
                            write_json(OUT/'STATUS.json',state);print(json.dumps(state),flush=True)
                        if invalid_output:raise RuntimeError('empty_or_nontext_output')
                        if failures>=3:raise RuntimeError('three_nonEOS_in_cell')
                finally:
                    torch.cuda.synchronize();timings.append(dict(engine=engine,repeat=repeat,seconds=time.monotonic()-begin,calls=cell_calls,peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved()));write_json(OUT/'TIMINGS.json',timings)
        assert n==256;status='COMPLETE'
    except BaseException as exc:status='STOPPED';error=type(exc).__name__+':'+str(exc)
    finally:summarize_result(status,error,started,timings)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run']);a=p.parse_args();(prepare if a.command=='prepare' else run)()
