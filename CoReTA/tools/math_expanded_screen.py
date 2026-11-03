"""Train-only, predeclared Level-5 difficulty screen; no collaboration."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
import pyarrow.parquet as pq
from coreta.schemas import Contracts
from coreta.scoring import docker_math_records
from coreta.state import write_json

ROOT=Path(__file__).resolve().parents[1]
BUNDLE=ROOT/'data/math-expanded-screen-20261019'
PLAN=ROOT/'engineering/MATH_EXPANDED_SCREEN_PLAN_20261019.json'
OUT=ROOT/'runs/math-expanded-screen-20261019'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()] if p.exists() else []
def norm(s): return ''.join(c.lower() for c in s if c.isalnum())
def boxed(s):
    start=s.rfind('\\boxed{')
    if start<0: raise ValueError('No boxed answer')
    start+=7; depth=1
    for end in range(start,len(s)):
        depth+=(s[end]=='{')-(s[end]=='}')
        if depth==0: return s[start:end]
    raise ValueError('Unbalanced boxed answer')

def build():
    if BUNDLE.exists() or PLAN.exists() or OUT.exists(): raise ValueError('Refuse overwrite')
    source=ROOT/'data/source/math-train-21a5633'
    excluded={norm(r['problem']) for r in lines(ROOT/'data/source/math500-test.jsonl')}
    for bundle in ['development-20261019','complementarity-challenge-20261019','difficulty-screen-20261019','math-train-screen-20261019']:
        for r in read(ROOT/'data'/bundle/'tasks.json'):
            path=Path(r['task_path']) if 'task_path' in r else ROOT/'data'/bundle/r['path']
            excluded.add(norm(read(path)['prompt']))
    BUNDLE.mkdir(); (BUNDLE/'public').mkdir(); (BUNDLE/'evaluation').mkdir()
    tasks=[]; review=[]; gold=[]; seen=set(excluded)
    for sub in ['algebra','intermediate_algebra','number_theory','counting_and_probability']:
        candidates=[]
        for idx,r in enumerate(pq.read_table(source/(sub+'.parquet')).to_pylist()):
            if r['level']!='Level 5' or norm(r['problem']) in seen: continue
            if any(x in r['problem'].lower() for x in ['[asy]','includegraphics','[tikz']): continue
            try: answer=boxed(r['solution'])
            except ValueError: continue
            tid=f'math_train/{sub}/{idx}'
            candidates.append((hashlib.sha256(('coreta-math-train-screen-v1|'+tid).encode()).hexdigest(),tid,r,answer))
        count=0
        for _,tid,r,answer in sorted(candidates):
            if norm(r['problem']) in seen: continue
            seen.add(norm(r['problem'])); count+=1
            task={'task_id':tid,'task_type':'math','prompt':r['problem'],'entry_point':None}
            Contracts(ROOT/'design/v0.3/coreta.schema.json').validate('PublicTask',task)
            job=hashlib.sha256(tid.encode()).hexdigest()[:16]; path=BUNDLE/'public'/(job+'.json')
            write_json(path,task); tasks.append({'task_id':tid,'task_path':str(path),'job_id':job,'sha256':sha(path)})
            gold.append({'task_id':tid,'answer':answer})
            review.append({'task_id':tid,'subject':sub,'level':r['level'],'prompt':r['problem'],'reference':r['solution'],'answer':answer})
            if count==8: break
        if count!=8: raise ValueError('Insufficient eligible tasks')
    write_json(BUNDLE/'tasks.json',tasks); write_json(BUNDLE/'evaluation/math_gold.json',gold)
    write_json(BUNDLE/'evaluation/review.json',review)
    paths=[ROOT/p for p in ['src/coreta/closure.py','src/coreta/run_closure.py','src/coreta/revision.py','src/coreta/model_client.py','src/coreta/schemas.py','src/coreta/state.py','src/coreta/scoring.py','config/deepseek_flash_closure.json','design/closure_prompts.json','design/v0.3/coreta.schema.json','data/tokenizer-v4.1-flash-1017/tokenizer.json','data/source/math500-test.jsonl','engineering/SCORING_IMAGE_20261019.txt']]
    paths+=list(source.glob('*'))+list((BUNDLE/'public').glob('*'))+list((BUNDLE/'evaluation').glob('*'))+[BUNDLE/'tasks.json',Path(__file__)]
    write_json(PLAN,{'purpose':'train-only model difficulty screening, no collaboration','tasks':tasks,'normal_call_cap':96,
        'selection':'8 further Level-5 per four subjects, fixed hash order, text diagrams retained unless external asy/image/tikz; exclude normalized formal500 and prior development prompts',
        'failure_policy':'retain incomplete; no auto rerun, replacement, limit changes or stopping on first success',
        'review':'uniform whole-pool contract review; retain all scores, do not select by complementarity or later outcomes',
        'source_hashes':{str(p):sha(p) for p in paths}})
    print(json.dumps({'tasks':tasks,'normal_call_cap':96}))

def verify():
    p=read(PLAN)
    for path,h in p['source_hashes'].items():
        if sha(Path(path))!=h: raise ValueError('Frozen source changed: '+path)
    return p

def preflight():
    verify(); image=(ROOT/'engineering/SCORING_IMAGE_20261019.txt').read_text().strip()
    gold=read(BUNDLE/'evaluation/math_gold.json')
    scored=docker_math_records([{**r,'artifact':'\\boxed{'+r['answer']+'}'} for r in gold],image)
    write_json(ROOT/'engineering/MATH_EXPANDED_SCREEN_PREFLIGHT_20261019.json',scored)
    if any(r.get('score')!=1 for r in scored): raise ValueError('Gold roundtrip failed; no model run')
    print(json.dumps({'gold_roundtrip_passed':len(scored)}))

def run():
    p=verify(); check=read(ROOT/'engineering/MATH_EXPANDED_SCREEN_PREFLIGHT_20261019.json')
    if len(check)!=32 or any(r.get('score')!=1 for r in check): raise ValueError('Preflight required')
    OUT.mkdir(exist_ok=False)
    for t in p['tasks']:
        verify(); print(json.dumps({'starting':t['task_id']}),flush=True)
        cmd=[sys.executable,'-m','coreta.run_closure','--task',t['task_path'],'--output',str(OUT/t['job_id']),
            '--draft-bank',str(OUT/'draft-bank'),'--draft-only','--tokenizer',str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'),'--live']
        if subprocess.run(cmd,check=False).returncode: raise RuntimeError('Entry failure; stopped')

def score():
    p=verify(); image=(ROOT/'engineering/SCORING_IMAGE_20261019.txt').read_text().strip()
    gold={r['task_id']:r for r in read(BUNDLE/'evaluation/math_gold.json')}; inputs=[]; labels=[]; stats=[]
    for t in p['tasks']:
        d=OUT/t['job_id']; stats.append(read(d/'draft_result.json'))
        for e in lines(d/'events.jsonl'):
            if e['stage']!='draft': raise ValueError('Unexpected collaboration')
            inputs.append({**gold[t['task_id']],'artifact':e['payload']['artifact']})
            labels.append({'task_id':t['task_id'],'actor':e['sent_from']})
    rows=[{**label,'score':s.get('score'),'detail':s} for label,s in zip(labels,docker_math_records(inputs,image))]
    write_json(ROOT/'engineering/MATH_EXPANDED_SCREEN_SCORES_20261019.json',rows)
    summary={'tasks':[{'task_id':t['task_id'],'scores':[r['score'] for r in rows if r['task_id']==t['task_id']]} for t in p['tasks']],
        'normal_calls':sum(r['normal_calls'] for r in stats),'http_attempts':sum(r['http_attempts'] for r in stats),
        'format_repairs':sum(r['format_repairs'] for r in stats)}
    write_json(ROOT/'engineering/MATH_EXPANDED_SCREEN_SUMMARY_20261019.json',summary); print(json.dumps(summary))

if __name__=='__main__':
    a=argparse.ArgumentParser(); a.add_argument('mode',choices=['build','preflight','run','score']); a.add_argument('--live',action='store_true'); args=a.parse_args()
    if args.mode=='build': build()
    elif args.mode=='preflight': preflight()
    elif args.mode=='score': score()
    elif args.live: run()
    else: a.error('Explicit --live required')
