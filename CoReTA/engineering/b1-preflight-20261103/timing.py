"""Freeze and launch only the first two D items, no automatic expansion."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from b0_answers import read_jsonl,write_json
from b1_runtime import load_json,validate_runtime,development_data,run_batch,score_batch
HERE=Path(__file__).resolve().parent
PRE=ROOT/'runs/b1-preflight-v20-20261103-v2'
OUT=ROOT/'runs/b1-timing2-20261103-v2'
FREEZE=HERE/'TIMING_FREEZE.json'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(files):
    for path,digest in files.items():
        if sha(path)!=digest:raise ValueError('frozen_file_changed:'+path)


def freeze():
    previous=load_json(PRE/'FREEZE.json');check(previous['files'])
    result=load_json(PRE/'solo/RESULTS.json')
    assert result['status']=='COMPLETE' and result['actual_generations']==40
    rows=read_jsonl(PRE/'solo/responses.jsonl')
    assert len(rows)==40 and all(r['status']=='OK' for r in rows)
    for i in range(20):
        b,e=rows[i*2:i*2+2]
        assert (b['condition'],e['condition'])==('B','E') and b['id']==e['id']
        assert b['request']['payload']==e['request']['payload'] and b['request']['seed']==e['request']['seed']
        assert b['usage']['adapter_enabled'] is False and e['usage']['adapter_enabled'] is True
    route=load_json(PRE/'solo/ADAPTER_ROUTE_WITNESS.json')
    assert route['active_disabled_max_logit_delta']>0 and route['active_restored_max_logit_delta']<=1e-5
    config=load_json(previous['config_path']);q=validate_runtime(config)
    tasks,groups,_=development_data(2)
    assert [t['id'] for t in tasks]==previous['D_ids']
    files=dict(previous['files'])
    extra=[Path(__file__).resolve(),PRE/'FREEZE.json',PRE/'PREFLIGHT.json',PRE/'solo/RESULTS.json',
        PRE/'solo/responses.jsonl',PRE/'solo/ADAPTER_ROUTE_WITNESS.json',HERE/'TIMING_EXPERIMENT_REVIEW.md']
    extra+=list((ROOT/'research/musique-data-preparation-20261030/official_scorer/metrics').glob('*.py'))
    files.update({str(p):sha(p) for p in extra})
    assert not FREEZE.exists() and not OUT.exists()
    report=dict(files=files,config_path=previous['config_path'],expected_ids=[t['id'] for t in tasks],
        groups=groups,generations_max=104,soft_wall_seconds=1800,hard_wall_seconds=2400,
        independent_C_qualification=q['qualification'],solo_status=result['status'])
    write_json(FREEZE,report)
    print(json.dumps(dict(status='FROZEN_NOT_LAUNCHED',freeze_sha256=sha(FREEZE),n=2,generations_max=104)),flush=True)


def run():
    f=load_json(FREEZE);check(f['files'])
    approved=load_json(HERE/'TIMING_APPROVAL.json')
    assert approved['verdict']=='RUN_ALLOWED' and approved['freeze_sha256']==sha(FREEZE)
    tasks,groups,_=development_data(2)
    assert [t['id'] for t in tasks]==f['expected_ids'] and groups==f['groups']
    config=load_json(f['config_path'])
    started=time.monotonic();error=None;summary=None
    try:
        run_batch(config,tasks,groups,OUT)
    except Exception as exc:
        error=type(exc).__name__+':'+str(exc)
        raise
    finally:
        if (OUT/'manifest.json').exists():
            result=score_batch(OUT) # Only after execution, parse the fixed first2 D labels.
            journal=read_jsonl(OUT/'responses.jsonl')
            usage=[r.get('usage') or {} for r in journal]
            summary=dict(status=result['status'],n_expected=result['n_expected'],n_complete=result['n_complete'],
                recorded_generations=len(journal),generations_max=104,fatal_error=error,
                elapsed_seconds=time.monotonic()-started,
                input_tokens=sum(r.get('input_tokens',0) for r in usage),
                output_tokens=sum(r.get('output_tokens',0) for r in usage),
                max_input_tokens=max((r.get('input_tokens',0) for r in usage),default=0),
                statuses={s:sum(r['status']==s for r in journal) for s in {r['status'] for r in journal}},
                initial_baseline=result.get('initial_baseline'),
                arms={a:{k:v[k] for k in ('expected_em','actual_em','expert_em','expert_harm_n','expert_correction_n')}
                      for a,v in result.get('arms',{}).items()})
            assert len(journal)<=104
            write_json(OUT/'TIMING_SUMMARY.json',summary)
            print(json.dumps(summary),flush=True)
    if summary is None or summary['status']!='COMPLETE':raise SystemExit(2)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['freeze','run']);args=p.parse_args()
    (freeze if args.command=='freeze' else run)()
