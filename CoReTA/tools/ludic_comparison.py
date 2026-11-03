"""Frozen four-condition diagnostic reusing screened MBPP603 drafts."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from coreta.revision import REVISION_SYSTEMS
from coreta.scoring import score_mbpp
from coreta.state import write_json

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT/'engineering/LUDIC_COMPARISON_PLAN_20261019.json'
OUT = ROOT/'runs/ludic-comparison-20261019'
SCREEN = ROOT/'runs/difficulty-screen-20261019'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def events(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]
def fp(x): return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def build():
    if PLAN.exists() or OUT.exists(): raise ValueError('Refuse overwrite')
    screen = read(ROOT/'engineering/DIFFICULTY_SCREEN_PLAN_20261019.json')
    task = next(t for t in screen['tasks'] if t['task_id']=='mbpp/train/603')
    draft_events = events(SCREEN/task['job_id']/'events.jsonl')
    paths = [ROOT/'src/coreta'/n for n in ['revision.py','run_revision.py','model_client.py','schemas.py','state.py']]
    paths += [ROOT/'design/revision_prompts.json',ROOT/'design/v0.3/coreta.schema.json',ROOT/'config/deepseek_flash.json',ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json',Path(task['task_path']),ROOT/'data/difficulty-screen-20261019/evaluation/mbpp_tests.json',Path(__file__)]
    paths += list((SCREEN/'draft-bank').glob('*.json'))
    paths += [SCREEN/task['job_id']/'events.jsonl']
    jobs = [{'system':s,'job_id':s} for s in sorted(REVISION_SYSTEMS,key=lambda s:fp(task['task_id']+'|17|'+s))]
    write_json(PLAN,{'task':task,'jobs':jobs,'seed':17,'conditions':REVISION_SYSTEMS,
        'selection':'MBPP603, screened all-three-wrong; retained lucid/ludic typo; algorithm diagnostic only',
        'visibility':'original public task and frozen drafts only; no tests, reference or screening feedback',
        'failure_policy':'retain degraded runs; stop on entry failure; no automatic reruns or protocol changes',
        'initial_payload_hashes':[fp(e['payload']) for e in draft_events],
        'normal_call_upper_bound':sum(REVISION_SYSTEMS.values()),
        'source_hashes':{str(p):sha(p) for p in paths}})
    print(json.dumps({'jobs':jobs,'normal_call_upper_bound':sum(REVISION_SYSTEMS.values())}))

def verify():
    p=read(PLAN)
    for f,h in p['source_hashes'].items():
        if sha(Path(f))!=h: raise ValueError('Frozen source changed: '+f)
    return p

def run():
    p=verify(); OUT.mkdir(exist_ok=False)
    shutil.copytree(SCREEN/'draft-bank',OUT/'draft-bank')
    for j in p['jobs']:
        verify()
        print(json.dumps({'starting':j['system']}),flush=True)
        cmd=[sys.executable,'-m','coreta.run_revision','--task',p['task']['task_path'],'--system',j['system'],'--seed','17','--output',str(OUT/j['job_id']),'--draft-bank',str(OUT/'draft-bank'),'--tokenizer',str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'),'--live']
        if subprocess.run(cmd,check=False).returncode: raise RuntimeError('Entry failure; stopped')
        es=events(OUT/j['job_id']/'events.jsonl')
        if [fp(e['payload']) for e in es if e['stage']=='draft']!=p['initial_payload_hashes']: raise ValueError('Screened initial drafts not reused')

def score():
    p=verify(); image=(ROOT/'engineering/SCORING_IMAGE_20261019.txt').read_text().strip()
    test=next(r for r in read(ROOT/'data/difficulty-screen-20261019/evaluation/mbpp_tests.json') if r['task_id']==p['task']['task_id'])
    rows=[]; traces=[]
    for j in p['jobs']:
        folder=OUT/j['job_id']; r=read(folder/'result.json'); es=events(folder/'events.jsonl')
        if [fp(e['payload']) for e in es if e['stage']=='draft']!=p['initial_payload_hashes']: raise ValueError('Initial mismatch')
        for label,artifact in [('prefinal',r['prefinal_artifact']),('final',r['artifact'])]:
            scored=score_mbpp({**test,'artifact':artifact},OUT/'scoring'/(j['job_id']+'-'+label),image)
            rows.append({'system':j['system'],'label':label,'detail':scored.get('task_score'),'score':scored.get('task_score',{}).get('score')})
        traces.append({**r,'stages':[e['stage'] for e in es],'initial_hashes':[fp(e['payload']) for e in es if e['stage']=='draft']})
    write_json(ROOT/'engineering/LUDIC_COMPARISON_SCORES_20261019.json',rows)
    write_json(ROOT/'engineering/LUDIC_COMPARISON_TRACES_20261019.json',traces)
    summary={'task_id':p['task']['task_id'],'shared_initials_verified':True,'initial_scores':[0,0,0],'scores':rows,'normal_calls':sum(r['normal_calls'] for r in traces),'http_attempts':sum(r['http_attempts'] for r in traces),'format_repairs':sum(r['format_repairs'] for r in traces),'image':image}
    write_json(ROOT/'engineering/LUDIC_COMPARISON_SUMMARY_20261019.json',summary)
    print(json.dumps(summary))

if __name__=='__main__':
    a=argparse.ArgumentParser(); a.add_argument('mode',choices=['build','run','score']); a.add_argument('--live',action='store_true'); args=a.parse_args()
    if args.mode=='build': build()
    elif args.mode=='score': score()
    elif args.live: run()
    else: a.error('Explicit --live required')
