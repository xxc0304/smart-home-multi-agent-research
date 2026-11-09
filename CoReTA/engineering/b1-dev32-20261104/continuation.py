"""Durable bounded 2->8->32 continuation; no repeats or outcome-based gate."""
from collections import Counter
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from b0_answers import read_jsonl,write_json
from b1_runtime import load_json,validate_runtime,development_data,run_batch,score_batch
from b1_controls import replay,Trial
from b0_training import load_tokenizer
HERE=Path(__file__).resolve().parent
RUN=ROOT/'runs/b1-dev32-20261104-v2'
PRIOR=ROOT/'runs/b1-timing2-20261103-v2'
OUT8=ROOT/'runs/b1-tech8-20261104-v2'
OUT32=ROOT/'runs/b1-dev32-final-20261104-v2'
CONFIG8=ROOT/'config/b1_lab3090_tech8_20261104_v2.json'
CONFIG32=ROOT/'config/b1_lab3090_dev32_20261104_v2.json'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now():return datetime.now().astimezone().isoformat()
def check(files):
    for p,h in files.items():
        if sha(p)!=h:raise ValueError('frozen_file_changed:'+p)


def audit(out,prior,n):
    m=load_json(out/'manifest.json');old=load_json(prior/'manifest.json')
    inherited=len(old['expected_ids']);rows=read_jsonl(out/'responses.jsonl')
    exe=load_json(out/'execution.json')
    result=score_batch(out)
    traces=[load_json(out/'trials'/f'{i:03d}.json') for i in range(result['n_recorded'])]
    prefix=all((out/'trials'/f'{i:03d}.json').read_bytes()==(prior/'trials'/f'{i:03d}.json').read_bytes()
               for i in range(inherited))
    routing=all((r.get('usage') or {}).get('adapter_enabled')==(r['actor']=='M1') for r in rows if r['status']=='OK')
    replay_ok=all(replay(t).complete for t in traces)
    expected=list(development_data(n)[0])
    ids=[t['id'] for t in expected]
    statuses=dict(Counter(r['status'] for r in rows))
    # No score or directional effect appears in the advancement predicate.
    ok=(m['expected_ids']==ids and result['status']=='COMPLETE' and prefix and routing and replay_ok
        and len(rows)==52*n and statuses=={'OK':52*n} and exe['fatal_error'] is None
        and exe['new_backend_requests']==52*(n-inherited))
    usage=[r.get('usage') or {} for r in rows]
    record=dict(checked_at=now(),verdict='PASS' if ok else 'REVISE',scope='TECHNICAL_INTEGRITY_DEVELOPMENT_ONLY',
        reviewer='assistant-authored fixed checks, self-review; independence=none/provisional',
        n_expected=n,n_recorded=result['n_recorded'],n_complete=result['n_complete'],
        inherited_items=inherited,inherited_traces_byte_identical=prefix,adapter_routes_match=routing,
        trace_replay_complete=replay_ok,status_counts=statuses,new_requests=exe['new_backend_requests'],
        max_new_requests=52*(n-inherited),cumulative_requests=len(rows),elapsed_seconds=exe['elapsed_seconds'],
        max_input_tokens=max((u.get('input_tokens',0) for u in usage),default=0),
        input_tokens=sum(u.get('input_tokens',0) for u in usage),output_tokens=sum(u.get('output_tokens',0) for u in usage),
        peak_memory=exe.get('peak_memory'),initial_baseline=result.get('initial_baseline'),
        arms={a:{k:v[k] for k in ('expected_em','actual_em','expert_em','expert_harm_n','expert_harm_denominator',
            'expert_correction_n','expert_correction_denominator','expert_correct_but_not_selected_expected')}
            for a,v in result.get('arms',{}).items()},
        scientific_review='PASS only fixed development trajectories; no causal/confirmatory or method-superiority claim; no score-dependent advancement')
    write_json(out/'STAGE_AUDIT.json',record)
    return record


def prepare():
    previous=load_json(ROOT/'engineering/b1-preflight-20261103/TIMING_FREEZE.json')
    check(previous['files'])
    manifest=load_json(PRIOR/'manifest.json')
    assert load_json(PRIOR/'scores.json')['status']=='COMPLETE'
    assert load_json(PRIOR/'execution.json')['new_backend_requests']==104
    for i in range(2):assert replay(load_json(PRIOR/'trials'/f'{i:03d}.json')).complete
    c=manifest['config']
    validate_runtime(c)
    tasks,groups,_=development_data(32)
    tok=load_tokenizer(c)
    lengths=[];stress=[]
    for i,t in enumerate(tasks):
        trial=Trial(t,expert_actor=c['expert_actor'],seed=c['seed'],task_index=i,fixture=True,
            answer_tokens=c['answer_tokens'],answer_suffix=c['answer_suffix'])
        while (r:=trial.next_request()) is not None:
            ids=tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ('system','user')],
                tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs'])
            assert len(ids)+r['max_new_tokens']<=c['max_length'],'stress_overlength:'+t['id']
            stress.append(len(ids))
            if r['stage']=='initial':lengths.append(len(ids))
            cap=r['max_new_tokens']
            text=tok.decode(tok.encode('Reasoning from supplied paragraphs. "Check" \\ scope\n'*512,
                add_special_tokens=False)[:cap],skip_special_tokens=True)
            trial.submit(r['request_id'],text)
        assert trial.complete
    import torch
    free,total=torch.cuda.mem_get_info();assert free>=20*1024**3,'GPU_not_idle'
    RUN.mkdir(parents=True,exist_ok=False)
    for p,wall in ((CONFIG8,3600),(CONFIG32,10800)):
        candidate=dict(c,wall_seconds=wall)
        assert all(candidate.get(k)==c.get(k) for k in set(c)-{'wall_seconds'})
        write_json(p,candidate)
    files=dict(previous['files'])
    extra=[Path(__file__).resolve(),HERE/'PLAN.md',HERE/'EXPERIMENT_REVIEW.md',CONFIG8,CONFIG32,
        PRIOR/'manifest.json',PRIOR/'responses.jsonl',PRIOR/'scores.json',PRIOR/'execution.json',
        PRIOR/'trials/000.json',PRIOR/'trials/001.json']
    files.update({str(p):sha(p) for p in extra})
    freeze=dict(files=files,expected_ids=[t['id'] for t in tasks],groups=groups,
        new_generations_max=1560,total_generations_including_prior=1664,
        stages=[dict(n=8,soft=3600,hard=3900),dict(n=32,soft=10800,hard=11100)],
        outer_hard_seconds=15120,selection='fixed original D32 order, no score gate',created_at=now())
    write_json(RUN/'FREEZE.json',freeze)
    info=dict(status='PREPARED_NOT_LAUNCHED',n=32,n_groups=len(set(groups.values())),
        initial_max_tokens=max(lengths),synthetic_full_history_max_tokens=max(stress),max_length=c['max_length'],
        real_old_trace_replay_requests=104,synthetic_pressure_not_semantic_model_evidence=True,
        configs_changed_only_wall=True,GPU_free_bytes=free,no_D_labels_read_in_prepare=True,
        no_C_H_task_access=True,freeze_sha256=sha(RUN/'FREEZE.json'))
    write_json(RUN/'PREFLIGHT.json',info);print(json.dumps(info),flush=True)


def stage(n):
    f=load_json(RUN/'FREEZE.json');check(f['files'])
    assert load_json(RUN/'APPROVAL.json')['freeze_sha256']==sha(RUN/'FREEZE.json')
    out,prior,cp=(OUT8,PRIOR,CONFIG8) if n==8 else (OUT32,OUT8,CONFIG32)
    if n==32:
        prior_review=load_json(OUT8/'STAGE_AUDIT.json')
        assert prior_review['verdict']=='PASS' and prior_review['n_complete']==8
        (RUN/'STAGE32_EXPERIMENT_REVIEW.md').write_text(
            '# Stage32 checkpoint review\n\nScientific meaning PASS: fixed development prefix, no score-based selection.\n'
            'Readiness PASS: full8 replay/routes/byte-identical first2 prefix/416OK verified; runtime/config freeze unchanged.\n'
            'RUN_ALLOWED remaining24 only,1248 new requests,10800s soft/11100s hard; no retries/C/H/training.\n'
            'This is an assistant-authored predeclared technical review, not independent scientific review.\n',encoding='utf-8')
    tasks,groups,_=development_data(n)
    error=None
    try:run_batch(load_json(cp),tasks,groups,out,resume_from=prior)
    except Exception as exc:
        error=type(exc).__name__+':'+str(exc);raise
    finally:
        if (out/'execution.json').exists():
            report=audit(out,prior,n)
            if error:report['launcher_error']=error;write_json(out/'STAGE_AUDIT.json',report)
            print(json.dumps(report),flush=True)
    if error or report['verdict']!='PASS':raise SystemExit(2)


def record_progress(status,detail):
    value=dict(status=status,updated_at=now(),pid=os.getpid(),detail=detail)
    write_json(RUN/'JOB_STATUS.json',value)
    print(json.dumps(value),flush=True)


def run():
    f=load_json(RUN/'FREEZE.json');check(f['files'])
    approved=load_json(RUN/'APPROVAL.json')
    assert approved['verdict']=='RUN_ALLOWED' and approved['freeze_sha256']==sha(RUN/'FREEZE.json')
    (RUN/'LAUNCHED').touch(exist_ok=False)
    started=time.monotonic()
    record_progress('RUNNING_STAGE8','2 inherited;6 new; then technical checkpoint')
    try:
        for n,hard in ((8,3900),(32,11100)):
            if n==32:record_progress('RUNNING_STAGE32','8 passed;24 new; no old item repeats')
            with (RUN/f'stage{n}.log').open('w') as log:
                result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'stage','--n',str(n)],
                    stdout=log,stderr=subprocess.STDOUT,timeout=hard,check=False)
            if result.returncode:
                record_progress('STOPPED',dict(stage=n,exit_code=result.returncode,
                    reason='stage incomplete or technical review failed; no retries/expansion'))
                finish('STOPPED');return
        record_progress('COMPLETE',dict(n=32,new_generations=1560,elapsed_seconds=time.monotonic()-started))
        finish('COMPLETE')
    except Exception as exc:
        record_progress('STOPPED',dict(reason=type(exc).__name__+':'+str(exc)))
        finish('STOPPED');raise


def finish(status):
    summaries={str(n):load_json(out/'STAGE_AUDIT.json') for n,out in ((8,OUT8),(32,OUT32)) if (out/'STAGE_AUDIT.json').exists()}
    result=dict(status=status,recorded_at=now(),stages=summaries,
        scope='FIXED_D32_DEVELOPMENT_FIRST_PASS',no_C_H_or_training=True)
    write_json(RUN/'RESULTS.json',result)
    entry=f'''## 2026-11-04 B1累计32题接续：{status}

用户要求超过8题，已按冻结的2→8→32计划执行；状态及实际分母见runs/b1-dev32-20261104-v2/RESULTS.json与JOB_STATUS.json。原v2参数不变，仅增分段wall预算；已完成前缀字节原样继承，不按得分筛选。科学解释限开发数据，不作因果/确认性或方法优越性结论。无训练/重跑C/读H/重试。实际技术审核见各阶段STAGE_AUDIT.json；若STOPPED，不得当32题已完成或静默续跑。\n\n'''
    for p in (ROOT/'handoff.md',ROOT/'CURRENT_STATE.md',ROOT/'refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md',
              ROOT/'refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md'):
        old=p.read_text(encoding='utf-8') if p.exists() else ''
        p.write_text(entry+old,encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run','stage']);p.add_argument('--n',type=int,choices=[8,32]);a=p.parse_args()
    if a.command=='stage':
        if a.n is None:p.error('--n required')
        stage(a.n)
    else:(prepare if a.command=='prepare' else run)()
