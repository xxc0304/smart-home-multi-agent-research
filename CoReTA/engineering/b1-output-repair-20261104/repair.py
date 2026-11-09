"""Audit four preserved truncations and test four separately versioned requests."""
import argparse,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from b1_runtime import LocalBackend,load_json
from b0_answers import read_jsonl,write_json
from b1_controls import replay
HERE=Path(__file__).resolve().parent
OLD=ROOT/'runs/b1-dev32-final-20261104-v2'
OUT=ROOT/'runs/b1-output-contract-probe-20261104-v3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def prepare():
    OUT.mkdir(parents=True,exist_ok=False)
    ledger=[];requests=[]
    for p in sorted((OLD/'trials').glob('*.json')):
        t=load_json(p);replay(t)
        bad=[r for r in t['records'] if r['status']!='OK']
        ledger.append(dict(id=t['task']['id'],complete=t['complete'],recorded=len(t['records']),
            skipped_dependency_requests=52-len(t['records']),
            failed=[dict(request_id=r['request_id'],stage=r['stage'],arm=r['arm'],actor=r['actor'],
                status=r['status'],output_tokens=r['usage']['output_tokens'],cap=r['max_new_tokens'],
                confirmed_token_limit=r['usage']['output_tokens']==r['max_new_tokens']) for r in bad]))
        for r in bad:
            assert r['status']=='OUTPUT_LIMIT' and r['usage']['output_tokens']==r['max_new_tokens']
            new={k:r[k] for k in ('request_id','stage','arm','actor','seed','round','payload','max_new_tokens')}
            new['payload']=dict(r['payload'])
            instruction=('Output ONLY your best short answer, at most 20 words, on one line. '
                'Do not explain or repeat the question.' if r['stage']=='initial' else
                'Write at most 120 words. Focus on relevant supplied evidence and your current conclusion. '
                'Do not walk through every paragraph or repeat points. Finish even if uncertain.')
            new['payload']['system']+='\n'+instruction
            new['payload']['user']+='\n\nOUTPUT FORMAT: '+instruction
            new['max_new_tokens']=128 if r['stage']=='initial' else 768
            requests.append(dict(original_request=r,probe_request=new,
                word_limit=20 if r['stage']=='initial' else 120))
    assert len(requests)==4 and sum(x['skipped_dependency_requests'] for x in ledger)==80
    write_json(HERE/'MISSINGNESS_LEDGER.json',dict(n_planned=32,n_recorded=32,n_complete=28,
        all_attempts_preserved=True,n_failed_responses=4,dependency_skips=80,items=ledger))
    write_json(OUT/'REQUESTS.json',requests)
    cfg=load_json(OLD/'manifest.json')['config'];cfg['wall_seconds']=600
    write_json(OUT/'config.json',cfg)
    paths=[Path(__file__),HERE/'EXPERIMENT_REVIEW.md',OUT/'REQUESTS.json',OUT/'config.json',
        ROOT/'tools/b1_runtime.py',ROOT/'tools/b1_stop_status.py',ROOT/'tools/b1_controls.py',
        OLD/'manifest.json',OLD/'responses.jsonl',OLD/'scores.json']
    write_json(OUT/'FREEZE.json',dict(files={str(p):sha(p) for p in paths},new_generations_max=4,
        soft_wall_seconds=600,hard_wall_seconds=900,contract='V3_CONCISE_DIAGNOSTIC_ONLY',no_gold_used=True))
    print(json.dumps(dict(status='PREPARED',freeze_sha256=sha(OUT/'FREEZE.json'))))
def run():
    freeze=load_json(OUT/'FREEZE.json')
    assert all(sha(p)==h for p,h in freeze['files'].items())
    a=load_json(OUT/'APPROVAL.json');assert a['freeze_sha256']==sha(OUT/'FREEZE.json') and a['verdict']=='RUN_ALLOWED'
    (OUT/'LAUNCHED').touch(exist_ok=False)
    started=time.monotonic();backend=LocalBackend(load_json(OUT/'config.json'))
    path=OUT/'responses.jsonl';path.touch();rows=[]
    for request in load_json(OUT/'REQUESTS.json'):
        remaining=600-(time.monotonic()-started)
        if remaining<=0:break
        response=backend.respond(request['probe_request'],remaining)
        row=dict(request_id=request['probe_request']['request_id'],stage=request['probe_request']['stage'],
            word_limit=request['word_limit'],**response)
        row['word_count']=len(row['raw_output'].split())
        row['word_contract_pass']=row['word_count']<=row['word_limit']
        rows.append(row)
        with path.open('a') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
        print(json.dumps(row,ensure_ascii=False),flush=True)
    result=dict(n_planned=4,n_generated=len(rows),n_eos=sum(r['status']=='OK' for r in rows),
        n_word_contract_pass=sum(r['word_contract_pass'] for r in rows),elapsed_seconds=time.monotonic()-started,
        verdict='PASS_TECHNICAL_ONLY' if len(rows)==4 and all(r['status']=='OK' and r['word_contract_pass'] for r in rows) else 'REVISE',
        original32_scores_unchanged=True,not_four_complete_team_reruns=True,no_semantic_accuracy_claim=True)
    write_json(OUT/'RESULTS.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run']);a=p.parse_args()
    (prepare if a.command=='prepare' else run)()
