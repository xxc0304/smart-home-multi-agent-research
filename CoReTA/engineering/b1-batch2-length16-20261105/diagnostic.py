"""Two batch2 target failures and original companions; 4x2x2=16 max."""
import argparse,copy,hashlib,json,os,re,signal,sys,time
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];os.chdir(ROOT);sys.path.insert(0,str(ROOT/'tools'))
from b0_answers import write_json
from b1_controls import replay
from b1_runtime import load_json,validate_runtime
from b1_multi_backend import MultiBackend
HERE=Path(__file__).resolve().parent;OUT=ROOT/'runs/b1-batch2-length16-20261105-v1'
OLD=ROOT/'runs/b1-batch2-fullflow-20261105-v1'
CELLS=((512,'serial'),(512,'batch2'),(1024,'batch2'),(1024,'serial'))
SOFT=900;FIELDS=('request_id','arm','stage','round','actor','seed','max_new_tokens','payload')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def plan(engine):
    n={'serial':1,'batch2':2}[engine]
    return [list(range(g*2+s,g*2+s+n)) for g in range(2) for s in range(0,2,n)]

def repetition(text):
    if not isinstance(text,str):return dict(repeated_8gram_fraction=None,repeated_sentence_fraction=None)
    words=re.findall(r'\w+|[^\w\s]',text.lower());grams=[tuple(words[i:i+8]) for i in range(max(0,len(words)-7))]
    sentences=[re.sub(r'\s+',' ',s.strip().lower()) for s in re.split(r'(?<=[.!?])\s+|\n+',text) if s.strip()]
    return dict(repeated_8gram_fraction=1-len(set(grams))/len(grams) if grams else 0,repeated_sentence_fraction=1-len(set(sentences))/len(sentences) if sentences else 0)

def analyze(rows,inputs):
    lookup={(r['cap'],r['engine'],r['index']):r for r in rows}
    target_results=[];original=inputs['original_records'];targets=inputs['target_indices']
    for i in targets:
        obj=dict(index=i,request_id=inputs['requests'][i]['request_id'],cases=[])
        for cap,engine in CELLS:
            r=lookup.get((cap,engine,i))
            if r is None:obj['cases'].append(dict(cap=cap,engine=engine,status='NOT_RUN'));continue
            item=dict(cap=cap,engine=engine,status=r['status'],finish_reason=r['usage']['finish_reason'],output_tokens=r['usage']['output_tokens'],raw_output=r['raw_output'],**repetition(r['raw_output']))
            if cap==512 and engine=='batch2':item['same_tokens_as_original_failure']=r['usage']['output_ids']==original[i]['usage']['output_ids']
            if cap==1024 and (small:=lookup.get((512,engine,i))):item['same_prefix_as_512']=r['usage']['output_ids'][:len(small['usage']['output_ids'])]==small['usage']['output_ids']
            obj['cases'].append(item)
        target_results.append(obj)
    return dict(returned_responses=len(rows),statuses=dict(Counter(r['status'] for r in rows)),targets=target_results)

def prepare():
    from b0_training import load_tokenizer
    audit=load_json(ROOT/'engineering/b1-batch2-fullflow-20261105/POST_RUN_AUDIT.json')
    assert audit['counts']['batch2']['attempted']==397 and audit['counts']['batch2']['complete']==7 and len(audit['failed'])==2
    freeze=load_json(OLD/'FREEZE.json')
    for n in ('b1_multi_backend.py','b1_runtime.py','b1_controls.py','b1_output_contract.py','b1_stop_status.py','b0_answers.py','b0_training.py','expert_mechanism_protocol.py','prepare_answer_only_expert.py'):
        p=ROOT/'tools'/n;assert sha(p)==freeze['files'][str(p)],'tested_source_changed:'+n
    source_rows=[json.loads(s) for s in (OLD/'batch2/responses.jsonl').read_text().splitlines()]
    source_attempts=[json.loads(s) for s in (OLD/'batch2/ATTEMPTS.jsonl').read_text().splitlines()]
    traces=[load_json(p) for p in sorted((OLD/'batch2/trials').glob('*.json'))]
    assert len(traces)==8 and len(source_rows)==397 and sum(len(x['request_ids']) for x in source_attempts)==397
    assert all(replay(t).export()==t for t in traces)
    records={r['record']['request_id']:r['record'] for r in source_rows}
    failures=[r['record'] for r in source_rows if r['record']['status']=='OUTPUT_LIMIT'];assert len(failures)==2
    assert sorted((r['arm'],r['actor'],r['round']) for r in failures)==[('A','M4',1),('C','M3',1)]
    originals=[];target_indices=[]
    for fail in failures:
        group=next(a['request_ids'] for a in source_attempts if fail['request_id'] in a['request_ids'])
        assert len(group)==2
        for rid in group:
            rec=records[rid]
            if rid==fail['request_id']:target_indices.append(len(originals))
            originals.append(rec)
    requests=[{k:copy.deepcopy(r[k]) for k in FIELDS} for r in originals]
    assert len(requests)==len({r['request_id'] for r in requests})==4 and len(target_indices)==2
    assert all(r['actor']!='M1' and r['stage']=='work' and r['max_new_tokens']==512 for r in requests)
    c=load_json(OLD/'config.json');c.update(purpose='ISOLATED_LENGTH_EXECUTION_DIAGNOSTIC',wall_seconds=SOFT)
    qualification=validate_runtime(c)
    for p in [Path(c[k]) for k in ('baseline_C_score','expert_C_score')]+[p for p in Path(c['adapter_path']).iterdir() if p.is_file()]:assert sha(p)==freeze['files'][str(p)]
    tok=load_tokenizer(c);lengths=[]
    for r in requests:
        ids=tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs'])
        assert len(ids)+1024<=c['max_length'];lengths.append(len(ids))
    for engine in ('serial','batch2'):
        assert [i for b in plan(engine) for i in b]==list(range(4))
        for b in plan(engine):assert len({(requests[i]['max_new_tokens'],requests[i]['actor']=='M1') for i in b})==1
    for r in requests:
        extended=dict(r,max_new_tokens=1024);assert all(extended[k]==r[k] for k in r if k!='max_new_tokens')
    inputs=dict(requests=requests,original_records=originals,target_indices=target_indices,lengths=lengths)
    empty=analyze([],inputs);assert empty['returned_responses']==0 and all(x['status']=='NOT_RUN' for t in empty['targets'] for x in t['cases'])
    stub=MultiBackend.__new__(MultiBackend);stub.config=c
    try:stub.respond_many([requests[0],dict(requests[1],max_new_tokens=1024)],10)
    except ValueError:pass
    else:raise AssertionError('mixed_cap_accepted')
    OUT.mkdir(parents=True,exist_ok=False);write_json(OUT/'config.json',c);write_json(OUT/'INPUTS.json',inputs)
    pre=dict(science='PASS',engineering='PASS',two_original_failed_batches_exactly_recovered=True,partial_and_complete_traces_replayed=8,n_fixed_requests=4,n_targets=2,n_companions=2,max_new_generations=16,cells=CELLS,all_plans_same_inputs_and_seeds=True,only_request_cap_changed=True,empty_result_export_analyzed=True,mixed_cap_rejected=True,max_context_plus1024=max(lengths)+1024,qualification=qualification,soft_seconds=SOFT,per_cell_seconds=300,hard_seconds=1200)
    write_json(OUT/'PREFLIGHT.json',pre)
    paths=[Path(__file__),HERE/'launch.py',HERE/'EXPERIMENT_REVIEW.md',OUT/'config.json',OUT/'INPUTS.json',OUT/'PREFLIGHT.json',OLD/'RESULTS.json',OLD/'FREEZE.json',OLD/'batch2/responses.jsonl',OLD/'batch2/ATTEMPTS.jsonl',ROOT/'engineering/b1-batch2-fullflow-20261105/POST_RUN_AUDIT.json']
    paths += list((OLD/'batch2/trials').glob('*.json'))
    paths += [ROOT/'tools'/n for n in ('b1_multi_backend.py','b1_runtime.py','b1_controls.py','b1_output_contract.py','b1_stop_status.py','b0_answers.py','b0_training.py','expert_mechanism_protocol.py','prepare_answer_only_expert.py','prepare_expert_training.py')]
    paths += [Path(c[k]) for k in ('baseline_C_score','expert_C_score')]+[p for p in Path(c['adapter_path']).iterdir() if p.is_file()]
    write_json(OUT/'FREEZE.json',dict(files={str(p):sha(p) for p in paths}))
    for p in paths:
        if p.suffix=='.py':dest=OUT/'frozen_sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
    print(json.dumps(pre),flush=True)

def finish(status,error,start,timings):
    inputs=load_json(OUT/'INPUTS.json');rows=[json.loads(s) for s in (OUT/'responses.jsonl').read_text().splitlines()] if (OUT/'responses.jsonl').exists() else []
    attempts=[json.loads(s) for s in (OUT/'ATTEMPTS.jsonl').read_text().splitlines()] if (OUT/'ATTEMPTS.jsonl').exists() else []
    assert len(rows)<=16 and len({(r['cap'],r['engine'],r['index']) for r in rows})==len(rows)
    for r in rows:
        expected=dict(inputs['requests'][r['index']],max_new_tokens=r['cap'])
        assert r['request']==expected and not r['usage']['adapter_enabled'] and r['usage']['disabled_layers']==r['usage']['lora_layers']
    result=dict(status=status,error=error,scope='ISOLATED_WORK_LENGTH_DIAGNOSTIC_NOT_TEAM_RESULT',primary_enabled=False,elapsed_seconds=time.monotonic()-start,attempted_requests=sum(len(a['indices']) for a in attempts),max_new_generations=16,timings=timings,**analyze(rows,inputs))
    attempted_keys={(a['cap'],a['engine'],i) for a in attempts for i in a['indices']}
    for target in result['targets']:
        for cell in target['cases']:
            if cell['status']=='NOT_RUN' and (cell['cap'],cell['engine'],target['index']) in attempted_keys:cell['status']='NO_RESPONSE_AFTER_ATTEMPT'
    write_json(OUT/'RESULTS.json',result);write_json(OUT/'STATUS.json',dict(status=status,error=error,returned_responses=len(rows)))
    table='|目标|上限|方式|结束|输出token|8gram重复比例|\n|---|---:|---|---|---:|---:|\n'
    for target in result['targets']:
        for cell in target['cases']:
            metric=cell.get('repeated_8gram_fraction');display=f'{metric:.3f}' if isinstance(metric,(int,float)) else '—'
            table+=f"|{target['request_id']}|{cell['cap']}|{cell['engine']}|{cell['status']}|{cell.get('output_tokens','—')}|{display}|\n"
    md=f"# batch2两条截断请求诊断：{status}\n\n助手自审none/provisional。实际返回{len(rows)}/16，错误{error}。相同原提示/seed，512/1024×serial/batch2；复现2条目标及2同批请求，不是新团队准确率。TOKEN_LIMIT是诊断结果，EOS不表示语义正确。\n\n"+table+'\n原文、原512复现和增cap前缀比较见RESULTS.json。未自动重跑8/32或增加其他cap。\n'
    (OUT/'RESULTS.md').write_text(md);(HERE/'RESULTS.md').write_text(md)
    entry=f"## 2026-11-05 batch2两条截断有限诊断结束：{status}\n\n见engineering/b1-batch2-length16-20261105/RESULTS.md、runs/b1-batch2-length16-20261105-v1/RESULTS.json。原2失败batch共4载荷，512/1024×serial/batch2，上限16，实际{len(rows)}；状态分布{result['statuses']}。错误{error}，EOS不等于正确，固定失败样本不外推；助手自审none/provisional，未自动重跑8/32/训练/C-H。\n\n"
    (OUT/'FINAL_STAGE_ENTRY.md').write_text(entry)
    for name in ('handoff.md','CURRENT_STATE.md','experiment/results.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md'):
        p=ROOT/name;p.write_text(entry+p.read_text())
    print(json.dumps({k:v for k,v in result.items() if k!='targets'}),flush=True)

def run():
    f=load_json(OUT/'FREEZE.json');a=load_json(OUT/'APPROVAL.json')
    assert all(sha(p)==h for p,h in f['files'].items()) and a['verdict']=='RUN_ALLOWED' and a['freeze_sha256']==sha(OUT/'FREEZE.json')
    (OUT/'LAUNCHED').touch(exist_ok=False);start=time.monotonic();timings=[];status='RUNNING';error=None
    def interrupted(*_):raise RuntimeError('hard_timeout_or_interrupt')
    signal.signal(signal.SIGTERM,interrupted)
    try:
        import torch
        c=load_json(OUT/'config.json');validate_runtime(c);backend=MultiBackend(c);inputs=load_json(OUT/'INPUTS.json');n=0
        write_json(OUT/'BACKEND.json',dict(load_seconds=time.monotonic()-start,effective_generation_config=backend.generation_config.to_dict()))
        for cell,(cap,engine) in enumerate(CELLS):
            torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();begin=time.monotonic();cell_n=0
            try:
                for indices in plan(engine):
                    remaining=min(SOFT-(time.monotonic()-start),300-(time.monotonic()-begin))
                    if remaining<=0:raise RuntimeError('soft_budget')
                    selected=[dict(inputs['requests'][i],max_new_tokens=cap) for i in indices]
                    with (OUT/'ATTEMPTS.jsonl').open('a') as stream:stream.write(json.dumps(dict(cell=cell,cap=cap,engine=engine,indices=indices))+'\n')
                    responses=backend.respond_many(selected,remaining);assert len(responses)==len(selected);invalid=False
                    for i,request,response in zip(indices,selected,responses):
                        row=dict(cell=cell,cap=cap,engine=engine,index=i,request=request,**response)
                        if row['status']=='OK' and (not isinstance(row['raw_output'],str) or not row['raw_output'].strip()):row['status']='EMPTY_OR_NON_TEXT_OUTPUT'
                        with (OUT/'responses.jsonl').open('a') as stream:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
                        n+=1;cell_n+=1;assert n<=16
                        invalid=invalid or not isinstance(row['raw_output'],str) or not row['raw_output'].strip() or row['status'] not in ('OK','OUTPUT_LIMIT')
                        state=dict(status='RUNNING',cell=cell,cap=cap,engine=engine,returned_responses=n,elapsed_seconds=time.monotonic()-start)
                        write_json(OUT/'STATUS.json',state);print(json.dumps(state),flush=True)
                    if invalid:raise RuntimeError('non_length_technical_failure')
            finally:
                peak={}
                try:torch.cuda.synchronize();peak=dict(peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved())
                except Exception as exc:peak=dict(memory_statistics_error=type(exc).__name__)
                timings.append(dict(cell=cell,cap=cap,engine=engine,seconds=time.monotonic()-begin,returned_responses=cell_n,**peak));write_json(OUT/'TIMINGS.json',timings)
        assert n==16;status='COMPLETE'
    except BaseException as exc:status='STOPPED';error=type(exc).__name__+':'+str(exc)
    finally:finish(status,error,start,timings)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run']);a=p.parse_args();(prepare if a.command=='prepare' else run)()
