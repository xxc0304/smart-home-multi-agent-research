"""Two independent tasks, complete four-arm comparison, max 208 new calls."""
import argparse,copy,hashlib,json,os,signal,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];os.chdir(ROOT);sys.path.insert(0,str(ROOT/'tools'))
from b1_runtime import load_json,development_data,validate_runtime,trial_parameters
from b1_controls import Trial,replay,summarize
from b1_batch_backend import PairedBackend
from b0_answers import write_json
HERE=Path(__file__).resolve().parent;OUT=ROOT/'runs/b1-parallel-fullflow-20261105-v1'
OLD=ROOT/'runs/b1-timing2-20261103-v2'
SOFT=2500;ENGINE_SOFT=1200
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
FIELDS=('request_id','arm','stage','round','actor','seed','max_new_tokens','payload')

class ProbeFailure(Exception):pass

def execute(config,tasks,backend,engine,emit):
    trials=[Trial(t,**trial_parameters(config,i)) for i,t in enumerate(tasks)]
    assert len(trials)==2
    started=time.monotonic()
    try:
        for position in range(52):
            requests=[t.next_request() for t in trials]
            if any(r is None for r in requests):raise ProbeFailure('unexpected_incomplete_schedule')
            assert len({(r['stage'],r['arm'],r['round'],r['max_new_tokens']) for r in requests})==1
            # Same index-matched order in both engines; each Trial owns its history.
            same_route=len({r['actor']==config['expert_actor'] for r in requests})==1
            batches=[list(enumerate(requests))] if engine=='batch2' and same_route else [[(i,r)] for i,r in enumerate(requests)]
            for entries in batches:
                remaining=min(ENGINE_SOFT-(time.monotonic()-started),backend.remaining())
                if remaining<=0:raise ProbeFailure('soft_budget')
                responses=backend.respond_many([r for _,r in entries],remaining)
                if len(responses)!=len(entries):raise ProbeFailure('response_count_mismatch')
                bad=False
                for (i,r),response in zip(entries,responses):
                    record=trials[i].submit(r['request_id'],response['raw_output'],status=response['status'],usage=response.get('usage'),source_kind='ACTUAL_LOCAL_MODEL_RESPONSE')
                    emit(i,record,trials[i].export(),len(entries),position)
                    bad=bad or record['status']!='OK' or not isinstance(record['raw_output'],str) or not record['raw_output'].strip()
                if bad:raise ProbeFailure('non_EOS_or_empty_response')
        assert all(t.complete for t in trials)
    finally:backend.traces=[t.export() for t in trials]
    return backend.traces

def prepare():
    from b0_training import load_tokenizer
    prior=[load_json(OLD/f'trials/{i:03d}.json') for i in range(2)]
    c=load_json(OLD/'manifest.json')['config'];c.update(purpose='TECHNICAL_EXECUTOR_COMPARISON_V2_CONTRACT',wall_seconds=SOFT)
    assert not c.get('output_contract') and c['answer_tokens']==256 and c['work_tokens']==512
    qualification=validate_runtime(c)
    tasks,groups,_=development_data(2);tokenizer=load_tokenizer(c)
    replay_details={};lengths=[]
    for i,t in enumerate(prior):
        assert replay(t).export()==t and t['complete'] and t['task']==tasks[i]
        assert t['config']==trial_parameters(c,i)
        for r in t['records']:
            ids=tokenizer.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs'])
            assert len(ids)+r['max_new_tokens']<=c['max_length'];lengths.append(len(ids)+r['max_new_tokens'])
    class Cached:
        traces=[]
        remaining=lambda self:10000
        def respond_many(self,requests,remaining):
            result=[]
            for r in requests:
                i=0 if r['request_id'].startswith(tasks[0]['id']+'|') else 1
                record=prior[i]['records'][int(r['request_id'].rsplit('|',1)[1])]
                assert all(r[k]==record[k] for k in FIELDS)
                result.append({k:copy.deepcopy(record[k]) for k in ('raw_output','status','usage')})
            return result
    for engine in ('serial','batch2'):
        cache=Cached();traces=execute(c,tasks,cache,engine,lambda *_:None)
        assert traces==prior;replay_details[engine]=dict(real_historical_records_replayed=104,traces_exact=True)
    class Failing(Cached):
        def respond_many(self,requests,remaining):
            rows=super().respond_many(requests,remaining);rows[0].update(status='OUTPUT_LIMIT');return rows
    f=Failing();emitted=[]
    try:execute(c,tasks,f,'batch2',lambda *x:emitted.append(x))
    except ProbeFailure:pass
    else:raise AssertionError('failed_dependency_not_stopped')
    assert len(emitted)==2 and len(f.traces[0]['records'])==len(f.traces[1]['records'])==1
    stub=PairedBackend.__new__(PairedBackend);stub.config=c
    r0={k:prior[0]['records'][0][k] for k in FIELDS};r1={k:prior[1]['records'][1][k] for k in FIELDS}
    for bad in ([r0,r1],[r0,dict(r0,max_new_tokens=512)]):
        try:stub.respond_many(bad,10)
        except ValueError:pass
        else:raise AssertionError('mixed_route_or_cap_accepted')
    OUT.mkdir(parents=True,exist_ok=False)
    write_json(OUT/'config.json',c);write_json(OUT/'INPUTS.json',dict(tasks=tasks,groups=groups))
    pre=dict(science='PASS',engineering='PASS',scope='TECHNICAL_EXECUTOR_COMPARISON_NOT_QUALITY_EQUIVALENCE',historical_replay=replay_details,failed_dependency_stops=True,mixed_route_cap_rejected=True,max_historical_input_plus_cap=max(lengths),qualification=qualification,new_generations_max=208,order=['batch2','serial'],soft_seconds=SOFT,engine_soft_seconds=ENGINE_SOFT,hard_seconds=2700,CUDA_fullflow_pending=True)
    write_json(OUT/'PREFLIGHT.json',pre)
    paths=[Path(__file__),HERE/'launch.py',HERE/'EXPERIMENT_REVIEW.md',OUT/'config.json',OUT/'INPUTS.json',OUT/'PREFLIGHT.json',OLD/'manifest.json',OLD/'scores.json',ROOT/'runs/b1-batch-speed-20261105-v1/RESULTS.json']
    paths += [OLD/f'trials/{i:03d}.json' for i in range(2)]
    paths += [ROOT/'tools'/n for n in ('b1_batch_backend.py','b1_runtime.py','b1_controls.py','b1_output_contract.py','b1_stop_status.py','b0_answers.py','b0_training.py','expert_mechanism_protocol.py','prepare_answer_only_expert.py')]
    paths += [Path(c[k]) for k in ('baseline_C_score','expert_C_score')]
    paths += [p for p in Path(c['adapter_path']).iterdir() if p.is_file()]
    paths += list((ROOT/'research/musique-data-preparation-20261030/official_scorer/metrics').glob('*.py'))
    paths += [ROOT/'data/external/musique-v1.0-20261030'/n for n in ('inputs/D_development.jsonl','scoring/D_development.jsonl','corpus_index.jsonl')]
    paths += [ROOT/'research/musique-data-preparation-20261030/SPLIT_MANIFEST.json',ROOT/'implement-stage/expert-answer-only-20261101/C_GROUPS.json']
    write_json(OUT/'FREEZE.json',dict(files={str(p):sha(p) for p in paths}))
    for p in paths:
        if p.suffix=='.py':
            dest=OUT/'frozen_sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
    print(json.dumps(pre),flush=True)

class MeasuredBackend(PairedBackend):
    def __init__(self,c,started):super().__init__(c);self.started=started;self.traces=[]
    def remaining(self):return SOFT-(time.monotonic()-self.started)
    def respond_many(self,requests,remaining):
        if len(requests)==2:return super().respond_many(requests,remaining)
        # Capture tokens and actual LoRA flags for legacy serial respond too.
        import torch
        from peft.tuners.lora.layer import LoraLayer
        original=self.model.generate;observed={}
        def capture(*args,**kwargs):
            layers=[m for m in self.model.modules() if isinstance(m,LoraLayer)]
            disabled=sum(bool(m.disable_adapters) for m in layers)
            assert layers and disabled==(0 if requests[0]['actor']=='M1' else len(layers))
            observed.update(lora_layers=len(layers),disabled_layers=disabled)
            output=original(*args,**kwargs);observed['output_ids']=output[0,kwargs['input_ids'].shape[-1]:].tolist();return output
        try:
            self.model.generate=capture;response=self.respond(requests[0],remaining)
        finally:self.model.generate=original
        response['usage'].update(observed,batch_size=1)
        return [response]

def finish(status,error,started,timings):
    tasks,groups,targets=development_data(2,targets=True)
    scores={};traces={};counts={};diff=[]
    for engine in ('batch2','serial'):
        d=OUT/engine
        if not (d/'trials').exists():continue
        ts=[load_json(p) for p in sorted((d/'trials').glob('*.json'))];traces[engine]=ts
        for t in ts:assert replay(t).export()==t
        s=summarize(ts,targets,[t['id'] for t in tasks],groups)
        s.update(primary_enabled=False,scope='TECHNICAL_EXECUTOR_COMPARISON_NOT_QUALITY_EQUIVALENCE')
        write_json(d/'scores.json',s);scores[engine]={k:v for k,v in s.items() if k!='reports'}
        rows=[json.loads(line) for line in (d/'responses.jsonl').read_text().splitlines()]
        assert len(rows)==sum(len(t['records']) for t in ts)
        for i,t in enumerate(ts):assert [r['record'] for r in rows if r['item_index']==i]==t['records']
        assert len({r['record']['request_id'] for r in rows})==len(rows)
        assert all(r['record']['usage']['adapter_enabled']==(r['record']['actor']=='M1') for r in rows)
        counts[engine]=dict(n_calls=len(rows),n_batch2_responses=sum(r['batch_size']==2 for r in rows),n_complete=s['n_complete'],n_unknown=sum(r['record']['raw_output'].strip().lower()=='unknown' for r in rows if isinstance(r['record']['raw_output'],str)),input_tokens=sum(r['record']['usage']['input_tokens'] for r in rows),output_tokens=sum(r['record']['usage']['output_tokens'] for r in rows),format='original_v2_no_new_Unknown_instruction')
    if all(e in traces for e in ('serial','batch2')):
        for i,(a,b) in enumerate(zip(traces['serial'],traces['batch2'])):
            for x,y in zip(a['records'],b['records']):
                diff.append(dict(index=i,request_id=x['request_id'],stage=x['stage'],arm=x['arm'],actor=x['actor'],same_text=x['raw_output']==y['raw_output'],same_tokens=x['usage'].get('output_ids')==y['usage'].get('output_ids'),same_payload=x['payload']==y['payload']))
        write_json(OUT/'CROSS_ENGINE_DIFF.json',diff)
    seconds={x['engine']:x['seconds'] for x in timings}
    result=dict(status=status,error=error,scope='TECHNICAL_EXECUTOR_COMPARISON_NOT_QUALITY_EQUIVALENCE',primary_enabled=False,elapsed_seconds=time.monotonic()-started,timings=timings,counts=counts,scores=scores,cross_engine_compared=len(diff),cross_engine_same_text=sum(x['same_text'] for x in diff),cross_engine_same_tokens=sum(x['same_tokens'] for x in diff),divergence_changes_downstream_inputs=any(not x['same_payload'] for x in diff),engine_time_ratio=seconds.get('serial',0)/seconds['batch2'] if seconds.get('batch2') else None,adoption='NOT_AUTOMATIC; original T4 exact-token adoption gate not relaxed')
    write_json(OUT/'RESULTS.json',result);write_json(OUT/'STATUS.json',dict(status=status,error=error,counts=counts))
    md=f"# 跨题并行完整技术对照：{status}\n\n耗时{result['elapsed_seconds']:.2f}s，错误{error}。新响应{sum(v['n_calls'] for v in counts.values())}/208，逐方式统计见RESULTS.json。完整试点不等于质量等价；未自动切换D32/扩大批次。助手自审none/provisional。\n\n```json\n"+json.dumps(dict(timings=timings,counts=counts,time_ratio=result['engine_time_ratio'],cross_engine_same_text=result['cross_engine_same_text'],compared=len(diff)),ensure_ascii=False,indent=2)+"\n```\n"
    (OUT/'RESULTS.md').write_text(md);(HERE/'RESULTS.md').write_text(md)
    entry=f"## 2026-11-05 原v2合同跨题并行试点结束：{status}\n\n见runs/b1-parallel-fullflow-20261105-v1/RESULTS.json，engineering/b1-parallel-fullflow-20261105/RESULTS.md。固定D前2题×batch2/serial，最多208调用，实际{sum(v['n_calls'] for v in counts.values())}，错误{error}。同旧较长分析提示，无新Unknown指令；每题内部顺序广播不变，四组同执行形状。助手自审none/provisional，PASS仅完成的技术测量，质量等价/正式采用未通过，未扩样/训练/读C-H。\n\n"
    (OUT/'FINAL_STAGE_ENTRY.md').write_text(entry)
    for name in ('handoff.md','CURRENT_STATE.md','experiment/results.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md'):
        p=ROOT/name;p.write_text(entry+p.read_text())
    print(json.dumps(result),flush=True)

def run():
    f=load_json(OUT/'FREEZE.json');a=load_json(OUT/'APPROVAL.json')
    assert all(sha(p)==h for p,h in f['files'].items())
    assert a['verdict']=='RUN_ALLOWED' and a['freeze_sha256']==sha(OUT/'FREEZE.json')
    (OUT/'LAUNCHED').touch(exist_ok=False)
    started=time.monotonic();timings=[];status='RUNNING';error=None;backend=None
    def interrupted(*_):raise ProbeFailure('hard_timeout_or_interrupt')
    signal.signal(signal.SIGTERM,interrupted)
    try:
        import torch
        c=load_json(OUT/'config.json');validate_runtime(c);tasks=load_json(OUT/'INPUTS.json')['tasks']
        backend=MeasuredBackend(c,started);write_json(OUT/'BACKEND.json',dict(load_seconds=time.monotonic()-started,effective_generation_config=backend.generation_config.to_dict()))
        for engine in ('batch2','serial'):
            d=OUT/engine;(d/'trials').mkdir(parents=True,exist_ok=False);(d/'responses.jsonl').touch()
            torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();begin=time.monotonic();n=0
            def emit(i,record,trace,batch_size,position):
                nonlocal n
                with (d/'responses.jsonl').open('a') as stream:stream.write(json.dumps(dict(item_index=i,record=record,batch_size=batch_size),ensure_ascii=False)+'\n')
                write_json(d/f'trials/{i:03d}.json',trace);n+=1
                state=dict(status='RUNNING',engine=engine,engine_calls=n,total_calls=sum(x['calls'] for x in timings)+n,position=position,elapsed_seconds=time.monotonic()-started)
                write_json(OUT/'STATUS.json',state);print(json.dumps(state),flush=True)
            try:execute(c,tasks,backend,engine,emit)
            finally:
                torch.cuda.synchronize();timings.append(dict(engine=engine,seconds=time.monotonic()-begin,calls=n,peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved()));write_json(OUT/'TIMINGS.json',timings)
        assert sum(x['calls'] for x in timings)==208
        status='COMPLETE'
    except BaseException as exc:status='STOPPED';error=type(exc).__name__+':'+str(exc)
    finally:finish(status,error,started,timings)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run']);a=p.parse_args();(prepare if a.command=='prepare' else run)()
