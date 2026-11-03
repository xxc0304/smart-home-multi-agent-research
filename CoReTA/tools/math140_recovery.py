"""Frozen five-condition recovery diagnostic on independently adjudicated MATH140."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from coreta.closure import digest
from coreta.scoring import docker_math_records
from coreta.state import write_json

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'engineering/MATH140_RECOVERY_PLAN_20261019.json'
OUT=ROOT/'runs/math140-recovery-20261019'
SCREEN=ROOT/'runs/math-expanded-screen-20261019'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()] if p.exists() else []

def build():
    if PLAN.exists() or OUT.exists(): raise ValueError('Refuse overwrite')
    t=next(t for t in read(ROOT/'engineering/MATH_EXPANDED_SCREEN_PLAN_20261019.json')['tasks'] if t['task_id']=='math_train/intermediate_algebra/140')
    scores=[r['score'] for r in read(ROOT/'engineering/MATH_EXPANDED_SCREEN_SCORES_20261019.json') if r['task_id']==t['task_id']]
    if scores!=[0,0,0]: raise ValueError('Initial failure coverage mismatch')
    jobs=[{'condition':'postcheck','module':'coreta.run_closure','system':'coreta_revision','cap':14},
        {'condition':'precheck','module':'coreta.run_precheck','system':'coreta_revision','cap':14}]
    jobs += [{'condition':s,'module':'coreta.run_closure','system':s,'cap':4 if s=='independent_aggregate' else 10}
        for s in ['independent_aggregate','static_debate','independent_refine']]
    jobs.sort(key=lambda j:digest('math140-recovery-v1|'+j['condition']))
    paths=[ROOT/p for p in ['src/coreta/closure.py','src/coreta/precheck.py','src/coreta/run_closure.py','src/coreta/run_precheck.py','src/coreta/revision.py','src/coreta/model_client.py','src/coreta/schemas.py','src/coreta/state.py','src/coreta/scoring.py','design/closure_prompts.json','design/precheck_prompts.json','design/v0.3/coreta.schema.json','config/deepseek_flash_closure.json','data/tokenizer-v4.1-flash-1017/tokenizer.json','data/math-expanded-screen-20261019/evaluation/math_gold.json','engineering/MATH140_FAILURE_ADJUDICATION_20261019.md','engineering/SCORING_IMAGE_20261019.txt']]
    paths += [Path(t['task_path']),SCREEN/t['job_id']/'events.jsonl',Path(__file__)]+list((SCREEN/'draft-bank').glob('*.json'))
    write_json(PLAN,{'purpose':'single new-to-architecture task recovery diagnostic; no population or equal-cost claim',
        'task':t,'jobs':jobs,'normal_call_caps_sum':52,'maximum_normal_path_sum':50,
        'selection':'only clear all-three-wrong task in entire fixed 32-task pool, mathematically adjudicated before any method run',
        'visibility':'public task, frozen drafts, condition-allowed events; no gold, adjudication or scoring feedback',
        'failure_policy':'retain degraded results; stop on implementation failure; no auto rerun/configuration changes',
        'initial_payload_hashes':[digest(e['payload']) for e in lines(SCREEN/t['job_id']/'events.jsonl')],
        'source_hashes':{str(p):sha(p) for p in paths}})
    print(json.dumps({'conditions':[j['condition'] for j in jobs],'maximum_normal_path_sum':50}))

def verify():
    p=read(PLAN)
    for f,h in p['source_hashes'].items():
        if sha(Path(f))!=h: raise ValueError('Frozen source changed: '+f)
    return p

def run():
    p=verify(); OUT.mkdir(exist_ok=False)
    for j in p['jobs']:
        verify(); print(json.dumps({'starting':j['condition']}),flush=True)
        cmd=[sys.executable,'-m',j['module'],'--task',p['task']['task_path'],'--output',str(OUT/j['condition']),
            '--system',j['system'],'--draft-bank',str(SCREEN/'draft-bank'),
            '--tokenizer',str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'),'--live']
        if subprocess.run(cmd,check=False).returncode: raise RuntimeError('Entry failure; stopped')
        ds=[digest(e['payload']) for e in lines(OUT/j['condition']/'events.jsonl') if e['stage']=='draft']
        if ds!=p['initial_payload_hashes']: raise ValueError('Initial drafts changed')

def score():
    p=verify(); image=(ROOT/'engineering/SCORING_IMAGE_20261019.txt').read_text().strip()
    gold=next(r for r in read(ROOT/'data/math-expanded-screen-20261019/evaluation/math_gold.json') if r['task_id']==p['task']['task_id'])
    inputs=[]; results=[]
    for j in p['jobs']:
        d=OUT/j['condition']; r=read(d/'result.json'); es=lines(d/'events.jsonl')
        if [digest(e['payload']) for e in es if e['stage']=='draft']!=p['initial_payload_hashes']: raise ValueError('Initial mismatch')
        inputs.append({**gold,'artifact':r['artifact']})
        results.append({'condition':j['condition'],**r,'stages':[e['stage'] for e in es]})
    for r,sc in zip(results,docker_math_records(inputs,image)):
        r['score']=sc.get('score'); r['score_detail']=sc
    write_json(ROOT/'engineering/MATH140_RECOVERY_RESULTS_20261019.json',results)
    summary=[{k:r[k] for k in ['condition','status','stop_reason','score','normal_calls','http_attempts','format_repairs','review_status','errors']} for r in results]
    write_json(ROOT/'engineering/MATH140_RECOVERY_SUMMARY_20261019.json',summary); print(json.dumps(summary))

if __name__=='__main__':
    a=argparse.ArgumentParser(); a.add_argument('mode',choices=['build','run','score']); a.add_argument('--live',action='store_true'); args=a.parse_args()
    if args.mode=='build': build()
    elif args.mode=='score': score()
    elif args.live: run()
    else: a.error('Explicit --live required')
