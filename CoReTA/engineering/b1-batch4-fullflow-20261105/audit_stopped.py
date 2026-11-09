"""Read-only audit of the stopped technical trial; no new inference."""
import hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];os.chdir(ROOT);sys.path.insert(0,str(ROOT/'tools'))
from b0_answers import write_json
from b1_runtime import load_json,development_data
from b1_controls import replay,summarize
OUT=ROOT/'runs/b1-batch4-fullflow-20261105-v1';HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
before={str(p):sha(p) for p in OUT.rglob('*') if p.is_file()}
freeze=load_json(OUT/'FREEZE.json');assert all(sha(p)==h for p,h in freeze['files'].items())
assert load_json(OUT/'APPROVAL.json')['freeze_sha256']==sha(OUT/'FREEZE.json')
rows=[json.loads(s) for s in (OUT/'batch4/responses.jsonl').read_text().splitlines()]
attempts=[json.loads(s) for s in (OUT/'batch4/ATTEMPTS.jsonl').read_text().splitlines()]
assert len(rows)==sum(len(x['request_ids']) for x in attempts)==102
assert len({x['record']['request_id'] for x in rows})==102
traces=[load_json(p) for p in sorted((OUT/'batch4/trials').glob('*.json'))]
for t in traces:
    assert replay(t).export()==t
    assert [x['record'] for x in rows if x['item_index']==t['config']['task_index']]==t['records']
tasks,groups,targets=development_data(8,targets=True)
score=summarize(traces,targets,[t['id'] for t in tasks],groups)
score.update(primary_enabled=False,scope='TECHNICAL_FULL_HISTORY_D8_NOT_INDEPENDENT_CONFIRMATION')
assert score==load_json(OUT/'batch4/scores.json') and score['n_complete']==0
assert all(x['record']['usage']['adapter_enabled']==(x['record']['actor']=='M1') and x['record']['usage']['disabled_layers']==(0 if x['record']['actor']=='M1' else x['record']['usage']['lora_layers']) for x in rows)
failures=[]
for x in rows:
    r=x['record']
    if r['status']=='OK':assert r['usage']['finish_reason']=='EOS';continue
    u=r['usage'];assert r['status']=='OUTPUT_LIMIT' and u['output_tokens']==u['output_cap']==512 and not u['ended_with_eos'] and u['finish_reason']=='TOKEN_LIMIT'
    comparisons=[]
    for engine in ('serial','batch2'):
        t=load_json(ROOT/f'runs/b1-parallel-fullflow-20261105-v1/{engine}/trials/000.json')
        old=next(a for a in t['records'] if a['request_id']==r['request_id'])
        comparisons.append(dict(engine=engine,same_payload=old['payload']==r['payload'],same_seed=old['seed']==r['seed'],output_tokens=old['usage']['output_tokens'],status=old['status']))
    failures.append(dict(item_index=x['item_index'],request_id=r['request_id'],stage=r['stage'],arm=r['arm'],actor=r['actor'],round=r['round'],batch_size=x['batch_size'],input_tokens=u['input_tokens'],output_tokens=512,raw_output=r['raw_output'],prior_comparisons=comparisons))
assert len(failures)==3 and {x['item_index'] for x in failures}=={0}
assert not (OUT/'serial').exists() and all(sha(p)==h for p,h in before.items())
audit=dict(verdict='PASS_RECORD_INTEGRITY_REVISE_EXECUTOR_COMPLETENESS',reviewer='assistant',independence='none/provisional',planned_tasks_per_engine=8,visited_tasks=4,complete_four_arm_tasks=0,attempted_requests=102,returned_responses=102,normal_EOS=99,token_limits=3,failures=failures,freeze_and_approval_match=True,trace_replay_and_scoring_match=True,route_flags_valid=True,all_run_files_unchanged=True,serial_not_started=True,usable_speed_or_complete_team_accuracy=False)
write_json(HERE/'STOP_AUDIT.json',audit)
print(json.dumps({k:v for k,v in audit.items() if k!='failures'}),flush=True)
