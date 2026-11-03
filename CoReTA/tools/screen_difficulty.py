"""Predeclared train-only independent draft screening; never run collaboration."""
import argparse
import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path
import pyarrow.parquet as pq
from coreta.tasks import canonical_prompt, public_task
from coreta.state import write_json
from coreta.schemas import Contracts
from coreta.scoring import docker_math_records, score_mbpp

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / 'data/difficulty-screen-20261019'
PLAN = ROOT / 'engineering/DIFFICULTY_SCREEN_PLAN_20261019.json'
OUT = ROOT / 'runs/difficulty-screen-20261019'

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def lines(p):
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]

def build():
    if BUNDLE.exists() or PLAN.exists() or OUT.exists():
        raise ValueError('Existing frozen screen; refuse overwrite')
    source = ROOT / 'data/source'
    prior_paths = [ROOT/'data/development-20261019/tasks.json', ROOT/'data/complementarity-challenge-20261019/tasks.json']
    excluded, prompts = set(), set()
    for path in prior_paths:
        for row in read(path):
            excluded.add(row['task_id'])
            task = read(path.parent/row['path'])
            prompts.add(canonical_prompt(task['prompt'].split('\nImplement Python function ')[0]))
    for x in lines(source/'math500-test.jsonl'):
        prompts.add(canonical_prompt(x['problem']))
    with gzip.open(source/'HumanEvalPlus-v0.1.10.jsonl.gz','rt',encoding='utf-8') as f:
        prompts.update(canonical_prompt(json.loads(x)['prompt']) for x in f)
    candidates = {'gsm8k': [], 'mbpp': []}
    for family, filename in [('gsm8k','gsm8k-train.parquet'),('mbpp','mbpp-sanitized-train.parquet')]:
        for idx, row in enumerate(pq.read_table(source/filename).to_pylist()):
            tid = f'gsm8k/train/{idx}' if family=='gsm8k' else f"mbpp/train/{row['task_id']}"
            raw_prompt = row['question'] if family=='gsm8k' else row['prompt']
            if tid in excluded or canonical_prompt(raw_prompt) in prompts:
                continue
            if family=='gsm8k' and (row['answer'].count('<<')<5 or len(row['answer'])<400):
                continue
            if family=='mbpp' and len(row['test_list'])<3:
                continue
            try:
                public = public_task(family,row,row_number=idx)
            except (ValueError,SyntaxError):
                continue
            order = hashlib.sha256(('coreta-difficulty-screen-v1|'+tid).encode()).hexdigest()
            key = (order,tid) if family=='gsm8k' else (-len(row['code']),order,tid)
            candidates[family].append((key,public,row))
    BUNDLE.mkdir(parents=True)
    (BUNDLE/'public').mkdir(); (BUNDLE/'evaluation').mkdir()
    tasks, gold, tests, review = [], [], [], []
    contracts = Contracts(ROOT/'design/v0.3/coreta.schema.json')
    for family in ('gsm8k','mbpp'):
        for _, task, row in sorted(candidates[family],key=lambda v:v[0])[:12]:
            contracts.validate('PublicTask',task)
            path = BUNDLE/'public'/(hashlib.sha256(task['task_id'].encode()).hexdigest()[:16]+'.json')
            write_json(path,task)
            tasks.append({'task_id':task['task_id'],'family':family,'task_path':str(path),'sha256':sha(path),
                          'job_id':hashlib.sha256(task['task_id'].encode()).hexdigest()[:16]})
            if family=='gsm8k':
                gold.append({'task_id':task['task_id'],'answer':row['answer'].rsplit('####',1)[1].strip().replace(',','')})
                review.append({'task_id':task['task_id'],'prompt':task['prompt'],'reference':row['answer']})
            else:
                tests.append({'task_id':task['task_id'],'test_imports':row['test_imports'],'test_list':row['test_list']})
                review.append({'task_id':task['task_id'],'prompt':task['prompt'],'reference':row['code'],'test_list':row['test_list']})
    write_json(BUNDLE/'tasks.json',tasks)
    write_json(BUNDLE/'evaluation/math_gold.json',gold)
    write_json(BUNDLE/'evaluation/mbpp_tests.json',tests)
    write_json(BUNDLE/'evaluation/contract_review_material.json',review)
    paths = [ROOT/'src/coreta'/n for n in ('run_revision.py','revision.py','state.py','schemas.py','model_client.py')]
    paths += [ROOT/'design/revision_prompts.json',ROOT/'design/v0.3/coreta.schema.json',ROOT/'config/deepseek_flash.json',
              ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json',Path(__file__),BUNDLE/'tasks.json']
    paths += list((BUNDLE/'evaluation').glob('*.json'))
    paths += [source/n for n in ('gsm8k-train.parquet','mbpp-sanitized-train.parquet','math500-test.jsonl','HumanEvalPlus-v0.1.10.jsonl.gz')]
    write_json(PLAN,{'version':'difficulty-screen/1','tasks':tasks,'normal_call_cap':3*len(tasks),'seed':17,
        'selection':'12 GSM8K train: >=5 equation annotations and >=400 reference characters, hash order; 12 MBPP sanitized train: longest canonical code, >=3 assertions, hash ties; exclude previous bundles and normalized evaluation prompts',
        'purpose':'independent initial-draft difficulty calibration, no collaboration or finalization',
        'adjudication':'Review ALL selected prompt/reference/test contracts with uniform rules; retain scores and classify discrepancies. No selection by local complementary material or subsequent method success.',
        'failure_policy':'retain incomplete drafts; no auto rerun; stop on implementation error',
        'output':str(OUT),'source_hashes':{str(p):sha(p) for p in paths}})
    print(json.dumps({'tasks':len(tasks),'normal_call_cap':3*len(tasks),'ids':[r['task_id'] for r in tasks]}))

def verify():
    plan=read(PLAN)
    for path,h in plan['source_hashes'].items():
        if sha(Path(path))!=h: raise ValueError('Frozen source changed: '+path)
    for task in plan['tasks']:
        if sha(Path(task['task_path']))!=task['sha256']: raise ValueError('Public task changed')
    return plan

def run():
    plan=verify(); OUT.mkdir(parents=True,exist_ok=False)
    for task in plan['tasks']:
        verify()
        command=[sys.executable,'-m','coreta.run_revision','--task',task['task_path'],'--output',str(OUT/task['job_id']),
                 '--tokenizer',str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'),'--draft-bank',str(OUT/'draft-bank'),
                 '--seed','17','--draft-only','--live']
        print(json.dumps({'starting':task['task_id']}),flush=True)
        if subprocess.run(command,check=False).returncode: raise RuntimeError('Entry failure; stopped')
    print(json.dumps({'screened_tasks':len(plan['tasks'])}))

def score():
    plan=verify(); image=(ROOT/'engineering/SCORING_IMAGE_20261019.txt').read_text().strip()
    gold={r['task_id']:r for r in read(BUNDLE/'evaluation/math_gold.json')}
    tests={r['task_id']:r for r in read(BUNDLE/'evaluation/mbpp_tests.json')}
    rows, stats, math_records, math_labels = [],[],[],[]
    for task in plan['tasks']:
        directory=OUT/task['job_id']; result=read(directory/'draft_result.json'); stats.append(result)
        events=lines(directory/'events.jsonl')
        if any(e['stage']!='draft' for e in events): raise ValueError('Unexpected collaboration in screen')
        for event in events:
            label={'task_id':task['task_id'],'actor':event['sent_from'],'event_id':event['event_id']}
            if task['family']=='gsm8k':
                math_records.append({**gold[task['task_id']],'artifact':event['payload']['artifact']}); math_labels.append(label)
            else:
                record={**tests[task['task_id']],'artifact':event['payload']['artifact']}
                job=OUT/'scoring'/(task['job_id']+'-'+event['sent_from'])
                if (job/'launcher_result.json').exists():
                    if read(job/'input/mbpp.json')!=record or read(job/'manifest.json')['image']!=image: raise ValueError('Score cache mismatch')
                    launched=read(job/'launcher_result.json')
                else: launched=score_mbpp(record,job,image)
                detail=launched.get('task_score',{'score':None,'status':'scoring_error'})
                rows.append({**label,'score':detail.get('score'),'detail':detail})
    for label,detail in zip(math_labels,docker_math_records(math_records,image)):
        rows.append({**label,'score':detail.get('score'),'detail':detail})
    write_json(ROOT/'engineering/DIFFICULTY_SCREEN_SCORES_20261019.json',rows)
    summary=[]
    for task in plan['tasks']:
        scores=[r['score'] for r in sorted([r for r in rows if r['task_id']==task['task_id']],key=lambda r:r['actor'])]
        summary.append({'task_id':task['task_id'],'scores':scores,'all_wrong':scores==[0,0,0],
                        'any_wrong':0 in scores,'contract_status':'pending_uniform_review'})
    write_json(ROOT/'engineering/DIFFICULTY_SCREEN_SUMMARY_20261019.json',{'tasks':summary,
        'normal_calls':sum(r['normal_calls'] for r in stats),'http_attempts':sum(r['http_attempts'] for r in stats),
        'format_repairs':sum(r['format_repairs'] for r in stats),'score_count':len(rows),'image':image})
    print(json.dumps(summary))

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('mode',choices=['build','run','score']); parser.add_argument('--live',action='store_true')
    args=parser.parse_args()
    if args.mode=='build': build()
    elif args.mode=='score': score()
    elif args.live: run()
    else: parser.error('Explicit --live required')
