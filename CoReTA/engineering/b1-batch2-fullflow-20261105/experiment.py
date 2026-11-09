"""Full-history serial vs batch2 executor validation, fixed D8, max832."""
import argparse,copy,hashlib,json,os,signal,sys,time
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];os.chdir(ROOT);sys.path.insert(0,str(ROOT/'tools'))
from b0_answers import write_json
from b1_controls import Trial,replay,summarize
from b1_runtime import load_json,development_data,trial_parameters,validate_runtime
from b1_multi_backend import MultiBackend
HERE=Path(__file__).resolve().parent;OUT=ROOT/'runs/b1-batch2-fullflow-20261105-v1'
OLD=ROOT/'runs/b1-dev32-final-20261104-v2';SCREEN=ROOT/'runs/b1-strategy-screen-20261105-v2'
SOFT=6000;CELL_SOFT=1800;CELLS=((0,'batch2'),(0,'serial'),(1,'serial'),(1,'batch2'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

class StopExperiment(Exception):pass
class StopEngine(Exception):pass

def batches(ready,engine,config):
    if engine=='serial':return [[entry] for entry in ready]
    groups={}
    for entry in ready:
        r=entry[1];groups.setdefault((r['actor']==config['expert_actor'],r['max_new_tokens']),[]).append(entry)
    result=[]
    for group in groups.values():
        while group:
            n=2 if len(group)>=2 else 1
            result.append(group[:n]);group=group[n:]
    assert sorted(i for b in result for i,_ in b)==sorted(i for i,_ in ready)
    return result

def execute(config,tasks,indices,backend,engine,emit,attempt):
    trials={i:Trial(tasks[i],**trial_parameters(config,i)) for i in indices}
    start=time.monotonic();failed_items=set()
    try:
        for position in range(52):
            ready=[]
            for i,t in trials.items():
                r=t.next_request()
                if r is not None:
                    cursor=int(r['request_id'].rsplit('|',1)[1]);assert cursor>=position
                    if cursor==position:ready.append((i,r))
            for entries in batches(ready,engine,config):
                requests=[r for _,r in entries]
                assert len({(r['stage'],r['arm'],r['round'],r['max_new_tokens']) for r in requests})==1
                global_remaining=backend.remaining();cell_remaining=CELL_SOFT-(time.monotonic()-start)
                if global_remaining<=0:raise StopExperiment('global_soft_budget')
                if cell_remaining<=0:raise StopEngine('cell_soft_budget')
                remaining=min(cell_remaining,global_remaining)
                attempt(entries,position)
                responses=backend.respond_many(requests,remaining)
                if len(responses)!=len(entries):raise StopExperiment('response_count_mismatch')
                for (i,r),response in zip(entries,responses):
                    status=response['status'];raw=response['raw_output']
                    if status=='OK' and isinstance(raw,str) and not raw.strip():status='EMPTY_OUTPUT'
                    rec=trials[i].submit(r['request_id'],raw,status=status,usage=response.get('usage'),source_kind='ACTUAL_LOCAL_MODEL_RESPONSE')
                    emit(i,rec,trials[i].export(),len(entries),position)
                    if rec['status']!='OK':failed_items.add(i)
                if len(failed_items)>=3:raise StopEngine('three_distinct_failed_items_in_cell')
        assert all(t.next_request() is None for t in trials.values())
    finally:backend.traces={i:t.export() for i,t in trials.items()}
    return backend.traces

def prepare():
    from b0_training import load_tokenizer
    diag=ROOT/'runs/b1-length-diagnostic-20261105-v1/RESULTS.json'
    diagnostic=load_json(diag);diag_audit=ROOT/'engineering/b1-length-diagnostic-20261105/POST_RUN_AUDIT.json'
    assert diagnostic['status']=='COMPLETE' and diagnostic['returned_responses']==72
    assert load_json(diag_audit)['verdict']=='PASS_DIAGNOSTIC_INTEGRITY'
    assert all(next(x for x in t['cases'] if x['cap']==512 and x['engine']=='batch2')['status']=='OK' for t in diagnostic['targets'])
    audit=load_json(ROOT/'engineering/b1-strategy-screen-20261105/POST_RUN_AUDIT.json')
    assert audit['verdict']=='PASS' and audit['calls_attempted_and_returned']==256
    screen=load_json(SCREEN/'RESULTS.json');assert screen['status']=='COMPLETE' and screen['aggregate']['batch2']['ok']==64
    oldfreeze=load_json(SCREEN/'FREEZE.json')
    for name in ('b1_multi_backend.py','b1_runtime.py','b1_controls.py','b1_output_contract.py','b1_stop_status.py','b0_answers.py','b0_training.py','expert_mechanism_protocol.py','prepare_answer_only_expert.py'):
        p=ROOT/'tools'/name;assert sha(p)==oldfreeze['files'][str(p)],'screen-tested_source_changed:'+name
    tasks,groups,_=development_data(8);prior={i:load_json(OLD/f'trials/{i:03d}.json') for i in range(8)}
    c=load_json(OLD/'manifest.json')['config'];c.update(wall_seconds=SOFT,purpose='TECHNICAL_D8_FULL_HISTORY_BATCH2_VS_SERIAL')
    assert c['answer_tokens']==256 and c['work_tokens']==512 and not c.get('output_contract')
    qualification=validate_runtime(c);tok=load_tokenizer(c);max_length=0
    for p in [Path(c[k]) for k in ('baseline_C_score','expert_C_score')]+[p for p in Path(c['adapter_path']).iterdir() if p.is_file()]:
        assert sha(p)==oldfreeze['files'][str(p)],'screen_qualification_or_adapter_changed'
    for i,t in prior.items():
        assert replay(t).export()==t and t['complete'] and t['task']==tasks[i] and t['config']==trial_parameters(c,i)
        for r in t['records']:
            ids=tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs'])
            max_length=max(max_length,len(ids)+r['max_new_tokens']);assert len(ids)+r['max_new_tokens']<=c['max_length']
    class Cached:
        traces={}
        remaining=lambda self:10000
        def respond_many(self,requests,remaining):
            outputs=[]
            for r in requests:
                i=next(i for i,t in prior.items() if r['request_id'].startswith(t['task']['id']+'|'))
                rec=prior[i]['records'][int(r['request_id'].rsplit('|',1)[1])]
                assert all(rec[k]==r[k] for k in r)
                outputs.append({k:copy.deepcopy(rec[k]) for k in ('raw_output','status','usage')})
            return outputs
    coverage={}
    for cohort,engine in CELLS:
        cache=Cached();counts=Counter()
        ts=execute(c,tasks,range(cohort*4,cohort*4+4),cache,engine,lambda i,r,t,n,p:counts.update([n]),lambda *_:None)
        assert ts=={i:prior[i] for i in range(cohort*4,cohort*4+4)}
        coverage[f'{cohort}_{engine}']=dict(counts)
    for failure in ('initial','work','empty'):
        class Failed(Cached):
            def respond_many(self,requests,remaining):
                outputs=super().respond_many(requests,remaining)
                for req,row in zip(requests,outputs):
                    pos=int(req['request_id'].rsplit('|',1)[1])
                    if req['request_id'].startswith(tasks[0]['id']+'|') and pos==(4 if failure=='work' else 0):
                        if failure=='empty':row.update(raw_output='   ')
                        else:row.update(status='OUTPUT_LIMIT')
                return outputs
        failed=Failed();ts=execute(c,tasks,range(4),failed,'batch2',lambda *_:None,lambda *_:None)
        assert all(ts[i]==prior[i] for i in (1,2,3))
        assert not ts[0]['complete'] and replay(ts[0]).export()==ts[0]
        if failure in ('initial','empty'):assert len(ts[0]['records'])==1 and ts[0]['initial_failed']
        else:assert len(ts[0]['records'])==41 and ts[0]['failed']==['A']
    class RepeatedSameItem(Cached):
        def respond_many(self,requests,remaining):
            rows=super().respond_many(requests,remaining)
            for req,row in zip(requests,rows):
                if req['request_id'].startswith(tasks[0]['id']+'|') and int(req['request_id'].rsplit('|',1)[1]) in (4,16,28,40):row['status']='OUTPUT_LIMIT'
            return rows
    same_item=RepeatedSameItem();ts=execute(c,tasks,range(4),same_item,'batch2',lambda *_:None,lambda *_:None)
    assert len(ts[0]['records'])==8 and ts[0]['failed']==list('ABCD') and all(ts[i]==prior[i] for i in (1,2,3))
    class ThreeDistinct(Cached):
        def respond_many(self,requests,remaining):
            rows=super().respond_many(requests,remaining)
            for req,row in zip(requests,rows):
                if int(req['request_id'].rsplit('|',1)[1])==0 and any(req['request_id'].startswith(tasks[i]['id']+'|') for i in (0,1,2)):row['status']='OUTPUT_LIMIT'
            return rows
    distinct=ThreeDistinct()
    try:execute(c,tasks,range(4),distinct,'batch2',lambda *_:None,lambda *_:None)
    except StopEngine:pass
    else:raise AssertionError('three_distinct_failures_did_not_stop_engine')
    assert len(distinct.traces)==4 and sum(len(t['records']) for t in distinct.traces.values())==4
    stopped=set();serial_after_failure={}
    for cohort,engine in CELLS:
        if engine in stopped:continue
        cache=ThreeDistinct() if engine=='batch2' else Cached()
        try:out=execute(c,tasks,range(cohort*4,cohort*4+4),cache,engine,lambda *_:None,lambda *_:None)
        except StopEngine:stopped.add(engine)
        else:
            if engine=='serial':serial_after_failure.update(out)
    assert stopped=={'batch2'} and serial_after_failure==prior
    OUT.mkdir(parents=True,exist_ok=False)
    write_json(OUT/'config.json',c);write_json(OUT/'INPUTS.json',dict(tasks=tasks,groups=groups))
    pre=dict(science='PASS',engineering='PASS',real_complete_traces_replayed=8,each_engine_replay_responses=416,cohort_counterbalanced=True,failed_initial_work_empty_isolated=True,four_failures_same_item_keep_others_running=True,three_distinct_item_failures_stop_only_engine=True,legacy_prompt_and_caps_unchanged=True,backend_matches_passed_256_call_screen=True,max_historical_context_plus_cap=max_length,coverage=coverage,qualification=qualification,max_new_generations=832,soft_seconds=SOFT,per_cell_seconds=CELL_SOFT,hard_seconds=6600,scope='TECHNICAL_FULL_HISTORY_D8_NOT_INDEPENDENT_CONFIRMATION')
    write_json(OUT/'PREFLIGHT.json',pre)
    paths=[Path(__file__),HERE/'launch.py',HERE/'EXPERIMENT_REVIEW.md',OUT/'config.json',OUT/'INPUTS.json',OUT/'PREFLIGHT.json',SCREEN/'RESULTS.json',SCREEN/'FREEZE.json',ROOT/'engineering/b1-strategy-screen-20261105/POST_RUN_AUDIT.json',OLD/'manifest.json',diag,diag_audit]
    paths += [OLD/f'trials/{i:03d}.json' for i in range(8)]
    paths += [ROOT/'tools'/n for n in ('b1_multi_backend.py','b1_runtime.py','b1_controls.py','b1_output_contract.py','b1_stop_status.py','b0_answers.py','b0_training.py','expert_mechanism_protocol.py','prepare_answer_only_expert.py','prepare_expert_training.py')]
    paths += [Path(c[k]) for k in ('baseline_C_score','expert_C_score')]+[p for p in Path(c['adapter_path']).iterdir() if p.is_file()]
    paths += list((ROOT/'research/musique-data-preparation-20261030/official_scorer/metrics').glob('*.py'))
    paths += [ROOT/'data/external/musique-v1.0-20261030'/n for n in ('inputs/D_development.jsonl','scoring/D_development.jsonl','corpus_index.jsonl')]
    paths += [ROOT/'research/musique-data-preparation-20261030/SPLIT_MANIFEST.json',ROOT/'implement-stage/expert-answer-only-20261101/C_GROUPS.json']
    write_json(OUT/'FREEZE.json',dict(files={str(p):sha(p) for p in paths}))
    for p in paths:
        if p.suffix=='.py':dest=OUT/'frozen_sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
    print(json.dumps(pre),flush=True)

def score_engine(engine):
    d=OUT/engine;tasks,groups,targets=development_data(8,targets=True)
    traces=[load_json(p) for p in sorted((d/'trials').glob('*.json'))]
    for t in traces:assert replay(t).export()==t
    score=summarize(traces,targets,[t['id'] for t in tasks],groups)
    score.update(primary_enabled=False,scope='TECHNICAL_FULL_HISTORY_D8_NOT_INDEPENDENT_CONFIRMATION')
    write_json(d/'scores.json',score);return score

def finish(status,error,started,timings):
    scores={};counts={};comparisons=[];attempted=0
    for engine in ('serial','batch2'):
        d=OUT/engine
        if not d.exists():continue
        score=score_engine(engine);scores[engine]={k:v for k,v in score.items() if k!='reports'}
        rows=[json.loads(s) for s in (d/'responses.jsonl').read_text().splitlines()] if (d/'responses.jsonl').exists() else []
        attempts=[json.loads(s) for s in (d/'ATTEMPTS.jsonl').read_text().splitlines()] if (d/'ATTEMPTS.jsonl').exists() else []
        attempted+=sum(len(x['request_ids']) for x in attempts)
        ts=[load_json(p) for p in sorted((d/'trials').glob('*.json'))]
        assert len(rows)==sum(len(t['records']) for t in ts) and len({r['record']['request_id'] for r in rows})==len(rows)
        for t in ts:
            i=t['config']['task_index'];assert [r['record'] for r in rows if r['item_index']==i]==t['records']
        assert all(r['record']['usage']['adapter_enabled']==(r['record']['actor']=='M1') for r in rows)
        counts[engine]=dict(n_expected_tasks=8,n_complete=score['n_complete'],returned=len(rows),statuses=dict(Counter(r['record']['status'] for r in rows)),batch_response_counts=dict(Counter(str(r['batch_size']) for r in rows)),unknown=sum(isinstance(r['record']['raw_output'],str) and r['record']['raw_output'].strip().lower()=='unknown' for r in rows),input_tokens=sum(r['record']['usage']['input_tokens'] for r in rows),output_tokens=sum(r['record']['usage']['output_tokens'] for r in rows))
    serial={r['id']:r for r in load_json(OUT/'serial/scores.json')['reports']} if 'serial' in scores else {}
    parallel={r['id']:r for r in load_json(OUT/'batch2/scores.json')['reports']} if 'batch2' in scores else {}
    for tid in serial.keys()&parallel.keys():
        x,y=serial[tid],parallel[tid]
        comparisons.append(dict(id=tid,serial_complete=x['complete'],batch2_complete=y['complete'],arms={arm:dict(serial_team_em=x['arms'][arm]['expected_em'],batch2_team_em=y['arms'][arm]['expected_em'],serial_expert_em=x['arms'][arm]['expert_em'],batch2_expert_em=y['arms'][arm]['expert_em']) for arm in 'ABCD' if x['arms'].get(arm,{}).get('complete') and y['arms'].get(arm,{}).get('complete')}))
    seconds={e:sum(t['seconds'] for t in timings if t['engine']==e) for e in ('serial','batch2')}
    complete=all(scores.get(e,{}).get('n_complete')==8 for e in ('serial','batch2'))
    if status=='COMPLETE' and not complete:status='COMPLETED_WITH_INCOMPLETE_TRIALS'
    engine_stops=load_json(OUT/'ENGINE_STOPS.json') if (OUT/'ENGINE_STOPS.json').exists() else {}
    result=dict(status=status,error=error,scope='TECHNICAL_FULL_HISTORY_D8_NOT_INDEPENDENT_CONFIRMATION',primary_enabled=False,elapsed_seconds=time.monotonic()-started,attempted_requests=attempted,returned_responses=sum(x['returned'] for x in counts.values()),max_requests=832,timings=timings,counts=counts,scores=scores,seconds=seconds,time_saved_fraction=1-seconds['batch2']/seconds['serial'] if complete and seconds['serial'] and seconds['batch2'] else None,matched_complete_tasks=sum(x['serial_complete'] and x['batch2_complete'] for x in comparisons),paired_comparisons=comparisons,engine_stops=engine_stops,adoption='NO_AUTOMATIC_D32_OR_METHOD_ADOPTION')
    write_json(OUT/'RESULTS.json',result);write_json(OUT/'STATUS.json',dict(status=status,error=error,counts=counts))
    md='# batch2完整D8执行器对照：'+status+'\n\n助手自审none/provisional；非独立质量等价。实际返回'+str(result['returned_responses'])+'/832，尝试'+str(attempted)+'，错误'+str(error)+'。\n\n```json\n'+json.dumps(dict(counts=counts,seconds=seconds,time_saved_fraction=result['time_saved_fraction']),ensure_ascii=False,indent=2)+'\n```\n'
    (OUT/'RESULTS.md').write_text(md);(HERE/'RESULTS.md').write_text(md)
    entry=f"## 2026-11-05 batch2完整D8执行器对照结束：{status}\n\n见runs/b1-batch2-fullflow-20261105-v1/RESULTS.json，engineering/b1-batch2-fullflow-20261105/RESULTS.md。两方式各8题四组52调用上限，总832，实际返回{result['returned_responses']}，错误{error}。原v2较长分析/预算不变、跨题1/2同路由合批、题内即时广播；专家/团队与完整分母分开报告。助手自审none/provisional，完成技术验证才PASS，未自动扩32/训练/新C-H。\n\n"
    (OUT/'FINAL_STAGE_ENTRY.md').write_text(entry)
    for name in ('handoff.md','CURRENT_STATE.md','experiment/results.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md'):
        p=ROOT/name;p.write_text(entry+p.read_text())
    print(json.dumps(dict(status=status,error=error,counts=counts,seconds=seconds,time_saved_fraction=result['time_saved_fraction'])),flush=True)

class TimedBackend(MultiBackend):
    def __init__(self,c,start):super().__init__(c);self.start=start;self.traces={}
    def remaining(self):return SOFT-(time.monotonic()-self.start)

def run():
    freeze=load_json(OUT/'FREEZE.json');approval=load_json(OUT/'APPROVAL.json')
    assert approval['verdict']=='RUN_ALLOWED' and approval['freeze_sha256']==sha(OUT/'FREEZE.json')
    assert all(sha(p)==h for p,h in freeze['files'].items())
    (OUT/'LAUNCHED').touch(exist_ok=False);started=time.monotonic();timings=[];status='RUNNING';error=None
    def interrupted(*_):raise StopExperiment('hard_timeout_or_interrupt')
    signal.signal(signal.SIGTERM,interrupted)
    try:
        import torch
        c=load_json(OUT/'config.json');validate_runtime(c);tasks=load_json(OUT/'INPUTS.json')['tasks'];backend=TimedBackend(c,started)
        write_json(OUT/'BACKEND.json',dict(load_seconds=time.monotonic()-started,effective_generation_config=backend.generation_config.to_dict()))
        total=0;engine_stops={}
        for cell,(cohort,engine) in enumerate(CELLS):
            if engine in engine_stops:continue
            assert all(sha(p)==h for p,h in freeze['files'].items())
            indices=range(cohort*4,cohort*4+4);d=OUT/engine;(d/'trials').mkdir(parents=True,exist_ok=True)
            phase=OUT/f'cell{cell}';phase.mkdir(exist_ok=False)
            write_json(phase/'APPROVAL.json',dict(verdict='RUN_ALLOWED',science='PASS',engineering='PASS',reviewer='assistant',independence='none/provisional',freeze_sha256=sha(OUT/'FREEZE.json'),cohort=cohort,engine=engine,max_new_requests=208,soft_seconds=CELL_SOFT))
            for i in indices:write_json(d/f'trials/{i:03d}.json',Trial(tasks[i],**trial_parameters(c,i)).export())
            torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();begin=time.monotonic();cell_calls=0
            def attempt(entries,position):
                with (d/'ATTEMPTS.jsonl').open('a') as stream:stream.write(json.dumps(dict(cell=cell,position=position,request_ids=[r['request_id'] for _,r in entries]))+'\n')
            def emit(i,record,trace,batch_size,position):
                nonlocal total,cell_calls
                with (d/'responses.jsonl').open('a') as stream:stream.write(json.dumps(dict(cell=cell,item_index=i,batch_size=batch_size,record=record),ensure_ascii=False)+'\n')
                write_json(d/f'trials/{i:03d}.json',trace);total+=1;cell_calls+=1;assert total<=832
                state=dict(status='RUNNING',cell=cell,cohort=cohort,engine=engine,returned_responses=total,cell_responses=cell_calls,position=position,elapsed_seconds=time.monotonic()-started)
                write_json(OUT/'STATUS.json',state);print(json.dumps(state),flush=True)
            try:execute(c,tasks,indices,backend,engine,emit,attempt)
            except StopEngine as exc:
                engine_stops[engine]=str(exc);write_json(OUT/'ENGINE_STOPS.json',engine_stops)
            finally:
                peak={}
                try:torch.cuda.synchronize();peak=dict(peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved())
                except Exception as exc:peak=dict(memory_statistics_error=type(exc).__name__)
                timings.append(dict(cell=cell,cohort=cohort,engine=engine,seconds=time.monotonic()-begin,returned=cell_calls,**peak));write_json(OUT/'TIMINGS.json',timings)
            scored=score_engine(engine)
            phase_traces=[load_json(d/f'trials/{i:03d}.json') for i in indices]
            write_json(phase/'POST_RUN_REVIEW.json',dict(verdict='PASS' if all(t['complete'] for t in phase_traces) else 'REVISE',scope='TECHNICAL_CELL_ONLY',reviewer='assistant',independence='none/provisional',complete_tasks=sum(t['complete'] for t in phase_traces),expected_tasks=4,independent_other_engine_allowed=True,same_engine_continuation_allowed=engine not in engine_stops))
        status='COMPLETE'
    except BaseException as exc:status='STOPPED';error=type(exc).__name__+':'+str(exc)
    finally:finish(status,error,started,timings)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run']);a=p.parse_args();(prepare if a.command=='prepare' else run)()
