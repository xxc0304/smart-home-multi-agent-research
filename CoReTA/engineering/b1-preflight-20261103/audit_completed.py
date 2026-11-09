"""Post-run audit only; no generation and no extra task labels."""
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from b0_answers import read_jsonl,write_json
from b1_runtime import load_json,score_batch
from b1_controls import replay
OUT=ROOT/'runs/b1-timing2-20261103-v2'
manifest=load_json(OUT/'manifest.json')
execution=load_json(OUT/'execution.json')
rows=read_jsonl(OUT/'responses.jsonl')
scored=score_batch(OUT)
assert len(rows)<=104
route_ok=all((r.get('usage') or {}).get('adapter_enabled')==(r['actor']=='M1') for r in rows)
assert route_ok
by_phase={}
for phase in ('initial','work','final'):
    selected=[r for r in rows if r['stage']==phase]
    usage=[r.get('usage') or {} for r in selected]
    by_phase[phase]=dict(n=len(selected),status_counts=dict(Counter(r['status'] for r in selected)),
        max_input_tokens=max((r.get('input_tokens',0) for r in usage),default=0),
        max_output_tokens=max((r.get('output_tokens',0) for r in usage),default=0),
        total_output_tokens=sum(r.get('output_tokens',0) for r in usage),
        generation_seconds=sum(r.get('elapsed_seconds',0) for r in usage))
items=[]
for report in scored['reports']:
    i=manifest['expected_ids'].index(report['id'])
    trace=load_json(OUT/'trials'/f'{i:03d}.json')
    t=replay(trace)
    assert t.complete==report['complete']
    items.append(dict(id=report['id'],complete=report['complete'],
        initial={a:dict(answer=report['initial']['members'][a]['answer'],
            em=report['initial']['members'][a]['em']) for a in report['initial']['members']}
            if report['initial'] else None,
        arms={a:dict(expected_em=r.get('expected_em'),actual_em=r.get('actual_em'),
            expert_em=r.get('expert_em'),vote=r.get('vote'),
            expert_harm=r.get('expert_harm'),expert_correction=r.get('expert_correction'),
            member_answers={k:dict(answer=v['answer'],em=v['em']) for k,v in r.get('members',{}).items()})
            for a,r in report['arms'].items()}))
audit=dict(completed_at=datetime.now().astimezone().isoformat(),
    planned_items=2,complete_items=scored['n_complete'],recorded_generations=len(rows),
    statuses=dict(Counter(r['status'] for r in rows)),adapter_routes_match=route_ok,
    trace_replay_scoring_match=True,by_phase=by_phase,execution=execution,items=items,
    continuation_ready=scored['status']=='COMPLETE' and len(rows)==104 and route_ok,
    interpretation='Two development items are technical/descriptive only; no mechanism/effect claim.')
write_json(OUT/'POST_RUN_AUDIT.json',audit)
print(json.dumps({k:v for k,v in audit.items() if k!='items'}),flush=True)
print(json.dumps(items,ensure_ascii=False),flush=True)
