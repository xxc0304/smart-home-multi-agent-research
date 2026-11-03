"""Frozen matched-config B/C/U diagnostic sharing archived v0.5 drafts."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from coreta.closure import ClosureContracts, digest
from coreta.scoring import score_mbpp
from coreta.state import write_json

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT/'engineering/PRECHECK_CALIBRATION_PLAN_20261019.json'
OUT = ROOT/'runs/precheck-calibration-20261019'
BANK = ROOT/'data/precheck-calibration-20261019/draft-bank'
SOURCE = ROOT/'runs/closure-calibration-20261019'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()] if p.exists() else []

def build():
    if PLAN.exists() or OUT.exists() or BANK.exists(): raise ValueError('Refuse overwrite')
    task=read(SOURCE/'public_task.json'); cfg=read(ROOT/'config/deepseek_flash_closure.json')
    prompts=read(ROOT/'design/closure_prompts.json')
    contracts=ClosureContracts(ROOT/'design/v0.3/coreta.schema.json')
    if cfg!=read(SOURCE/'manifest.json')['config']: raise ValueError('Calibration config changed')
    archived=read(SOURCE/'contract_snapshot.json')['$defs']['Candidate']
    if archived!=contracts.document['$defs']['Candidate']: raise ValueError('Candidate schema changed')
    ds=[e for e in lines(SOURCE/'events.jsonl') if e['stage']=='draft']
    if [e['sent_from'] for e in ds]!=['A0','A1','A2']: raise ValueError('Missing source drafts')
    BANK.mkdir(parents=True)
    for e in ds:
        material={'task':task,'actor':e['sent_from'],'seed':17,'config':cfg,
            'system_prompt':prompts['system'],'draft_prompt':prompts['draft'],'schema':contracts.schema('Candidate')}
        fingerprint=hashlib.sha256(json.dumps(material,sort_keys=True).encode()).hexdigest()
        write_json(BANK/(fingerprint+'.json'),{'fingerprint':fingerprint,'candidate':e['payload']})
    paths=[ROOT/p for p in ['src/coreta/precheck.py','src/coreta/run_precheck.py','design/precheck_prompts.json','src/coreta/closure.py','src/coreta/run_closure.py','src/coreta/revision.py','src/coreta/model_client.py','src/coreta/state.py','src/coreta/schemas.py','src/coreta/scoring.py','config/deepseek_flash_closure.json','design/closure_prompts.json','design/v0.3/coreta.schema.json','data/tokenizer-v4.1-flash-1017/tokenizer.json','data/difficulty-screen-20261019/evaluation/mbpp_tests.json','engineering/SCORING_IMAGE_20261019.txt']]
    paths += [SOURCE/n for n in ['events.jsonl','manifest.json','public_task.json','contract_snapshot.json']]
    paths += list(BANK.glob('*.json'))+[Path(__file__)]
    systems=sorted(['coreta_revision'],key=lambda s:digest(s+'|603|length'))
    write_json(PLAN,{'purpose':'seen-task matched-config B/C/U control diagnostic; not a pure order ablation or population estimate',
        'task_id':task['task_id'],'systems':systems,'normal_call_cap':14,'draft_bank':str(BANK),
        'source_draft_payload_hashes':[digest(e['payload']) for e in ds],
        'source_hashes':{str(p):sha(p) for p in paths},
        'failure_policy':'retain failures; no automatic rerun, replacement, configuration changes or capacity increases'})
    print(json.dumps({'systems':systems,'normal_call_cap':14,'shared_drafts':'archived v0.5 calibration, all three scored zero'}))

def verify():
    p=read(PLAN)
    for path,h in p['source_hashes'].items():
        if sha(Path(path))!=h: raise ValueError('Frozen source changed: '+path)
    return p

def run():
    p=verify(); OUT.mkdir(exist_ok=False)
    for system in p['systems']:
        verify(); print(json.dumps({'starting':system}),flush=True)
        cmd=[sys.executable,'-m','coreta.run_precheck','--task',str(SOURCE/'public_task.json'),
            '--output',str(OUT/system),'--system',system,'--draft-bank',str(BANK),
            '--tokenizer',str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'),'--live']
        if subprocess.run(cmd,check=False).returncode: raise RuntimeError('Entry failure; stop')
        ds=[digest(e['payload']) for e in lines(OUT/system/'events.jsonl') if e['stage']=='draft']
        if ds!=p['source_draft_payload_hashes']: raise ValueError('Shared initial mismatch')

def score():
    p=verify(); test=next(t for t in read(ROOT/'data/difficulty-screen-20261019/evaluation/mbpp_tests.json') if t['task_id']==p['task_id'])
    image=(ROOT/'engineering/SCORING_IMAGE_20261019.txt').read_text().strip(); rows=[]
    for system in p['systems']:
        d=OUT/system; r=read(d/'result.json'); responses=lines(d/'responses.jsonl')
        result=score_mbpp({**test,'artifact':r['artifact']},OUT/'scoring'/system,image)
        outputs=[x['response'] for x in responses if 'response' in x]
        rows.append({'system':system,'status':r['status'],'stop_reason':r['stop_reason'],
            'normal_calls':r['normal_calls'],'http_attempts':r['http_attempts'],'format_repairs':r['format_repairs'],
            'output_truncations':sum((x.get('incomplete_details') or {}).get('reason')=='max_output_tokens' for x in outputs),
            'max_output_tokens_observed':max((x.get('usage',{}).get('output_tokens',0) for x in outputs),default=0),
            'score':result.get('task_score',{}).get('score'),'score_detail':result.get('task_score'),
            'shared_drafts_verified':[digest(e['payload']) for e in lines(d/'events.jsonl') if e['stage']=='draft']==p['source_draft_payload_hashes'],
            'stages':[e['stage'] for e in lines(d/'events.jsonl')], 'errors':r['errors']})
    write_json(ROOT/'engineering/PRECHECK_CALIBRATION_SUMMARY_20261019.json',rows)
    print(json.dumps(rows))

if __name__=='__main__':
    a=argparse.ArgumentParser(); a.add_argument('mode',choices=['build','run','score']); a.add_argument('--live',action='store_true'); args=a.parse_args()
    if args.mode=='build': build()
    elif args.mode=='score': score()
    elif args.live: run()
    else: a.error('Explicit --live required')
