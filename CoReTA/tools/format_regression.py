"""Frozen same-version retention evaluation plus an explicit seen-task regression."""
import argparse
import concurrent.futures
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from coreta.closure import digest
from coreta.scoring import docker_math_records
from coreta.state import write_json

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'engineering/FORMAT_REGRESSION_PLAN_20261019.json'
OUT=ROOT/'runs/format-regression-20261019'
SCREEN=ROOT/'runs/math-expanded-screen-20261019'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def lines(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()] if p.exists() else []
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def build():
    if PLAN.exists() or OUT.exists(): raise ValueError('Refuse overwrite')
    original=read(ROOT/'engineering/RETENTION_PLAN_20261019.json')
    targets={'number_theory/592','intermediate_algebra/156','intermediate_algebra/1262',
             'counting_and_probability/525','number_theory/643','intermediate_algebra/916'}
    jobs=[{**j,'group':'targeted_regression'} for j in original['jobs']
          if j['task_id'].removeprefix('math_train/') in targets]
    if len(jobs)!=6: raise ValueError('Expected six fixed tasks')
    paths=[Path(f) for f in original['source_hashes']]
    paths += [ROOT/'src/coreta/closure_diff.py',ROOT/'src/coreta/run_closure_diff.py',ROOT/'src/coreta/closure_format.py',ROOT/'src/coreta/run_closure_format.py',Path(__file__)]
    write_json(PLAN,{'protocol_variant':'inspection_format_v1','jobs':jobs,'workers':2,
        'group_order':['targeted_regression'],'normal_call_caps_sum':84,'maximum_normal_path_sum':78,
        'scope':'Same six seen tasks: inspection field guidance and JSON diagnostic regression; no generalization claim',
        'failure_policy':'No reruns or in-batch modifications; retain all failures',
        'source_hashes':{str(p):sha(p) for p in paths}})
    print(json.dumps({'tasks':len(jobs),'maximum_normal_path_sum':78,'workers':2}))

def verify():
    p=read(PLAN)
    for f,h in p['source_hashes'].items():
        if sha(Path(f))!=h: raise ValueError('Frozen source changed: '+f)
    return p

def job_run(j):
    verify(); print(json.dumps({'starting':j['task_id'],'group':j['group']}),flush=True)
    cmd=[sys.executable,'-m','coreta.run_closure_format','--task',j['task_path'],
        '--output',str(OUT/j['job_id']),'--draft-bank',str(SCREEN/'draft-bank'),
        '--tokenizer',str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'),'--live']
    proc=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',check=False)
    if proc.returncode:
        print(json.dumps({'entry_error':j['task_id'],'stderr':proc.stderr[-1500:]}),flush=True)
        raise RuntimeError('Entry failure; stop scheduling')
    d=OUT/j['job_id']; r=read(d/'result.json')
    ds=[digest(e['payload']) for e in lines(d/'events.jsonl') if e['stage']=='draft']
    if ds!=j['initial_hashes']: raise ValueError('Initial payload mismatch')
    print(json.dumps({'finished':j['task_id'],'group':j['group'],'status':r['status'],
        'stop_reason':r['stop_reason'],'normal_calls':r['normal_calls'],
        'http_attempts':r['http_attempts'],'format_repairs':r['format_repairs']}),flush=True)
    return r

def run():
    p=verify(); OUT.mkdir(exist_ok=False)
    for group in p['group_order']:
        jobs=iter(j for j in p['jobs'] if j['group']==group)
        with concurrent.futures.ThreadPoolExecutor(max_workers=p['workers']) as pool:
            active={pool.submit(job_run,j):j for j in [next(jobs,None),next(jobs,None)] if j}
            while active:
                done,_=concurrent.futures.wait(active,return_when=concurrent.futures.FIRST_COMPLETED)
                for f in done:
                    active.pop(f); f.result()
                for _ in done:
                    j=next(jobs,None)
                    if j: active[pool.submit(job_run,j)]=j
        print(json.dumps({'group_finished':group}),flush=True)

def score():
    p=verify(); gold={r['task_id']:r for r in read(ROOT/'data/math-expanded-screen-20261019/evaluation/math_gold.json')}
    image=(ROOT/'engineering/SCORING_IMAGE_20261019.txt').read_text().strip()
    records=[]; rows=[]
    for j in p['jobs']:
        d=OUT/j['job_id']; r=read(d/'result.json'); ds=[digest(e['payload']) for e in lines(d/'events.jsonl') if e['stage']=='draft']
        if ds!=j['initial_hashes']: raise ValueError('Initial payload mismatch')
        records.append({**gold[j['task_id']],'artifact':r['artifact']})
        rows.append({'task_id':j['task_id'],'group':j['group'],'initial_scores':j['initial_scores'],
            'status':r['status'],'stop_reason':r['stop_reason'],'review_status':r['review_status'],
            'normal_calls':r['normal_calls'],'http_attempts':r['http_attempts'],'format_repairs':r['format_repairs'],
            'errors':r['errors']})
    for r,s in zip(rows,docker_math_records(records,image)):
        r['score']=s.get('score'); r['score_detail']=s
    write_json(ROOT/'engineering/FORMAT_REGRESSION_SCORES_20261019.json',rows)
    summary={'groups':{g:{'count':sum(r['group']==g for r in rows),
        'passed':sum(r['group']==g and r['score']==1 for r in rows),
        'score_errors':sum(r['group']==g and r['score'] is None for r in rows)} for g in p['group_order']},
        'retention_losses':[r['task_id'] for r in rows if r['group']!='seen_recovery_regression' and r['score']==0],
        'recovered_seen_regressions':[r['task_id'] for r in rows if r['group']=='seen_recovery_regression' and r['score']==1],
        'normal_calls':sum(r['normal_calls'] for r in rows),'http_attempts':sum(r['http_attempts'] for r in rows),
        'format_repairs':sum(r['format_repairs'] for r in rows),
        'degraded':[r['task_id'] for r in rows if r['status']!='completed'],
        'scope':p['scope']}
    write_json(ROOT/'engineering/FORMAT_REGRESSION_SUMMARY_20261019.json',summary); print(json.dumps(summary))

if __name__=='__main__':
    a=argparse.ArgumentParser(); a.add_argument('mode',choices=['build','run','score']); a.add_argument('--live',action='store_true'); args=a.parse_args()
    if args.mode=='build': build()
    elif args.mode=='score': score()
    elif args.live: run()
    else: a.error('Explicit --live required')
