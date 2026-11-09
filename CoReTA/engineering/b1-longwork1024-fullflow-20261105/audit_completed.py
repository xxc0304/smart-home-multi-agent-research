"""Read-only verification of the completed V6 D8 run; no model calls."""
import hashlib,json,os,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];os.chdir(ROOT);sys.path.insert(0,str(ROOT/'tools'))
from b1_runtime import load_json,development_data,trial_parameters
from b1_controls import replay,summarize
from b1_output_contract import LONG_WORK_VERSION
from b0_answers import write_json
HERE=Path(__file__).resolve().parent;OUT=ROOT/'runs/b1-longwork1024-fullflow-20261105-v1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
before={str(p):sha(p) for p in OUT.rglob('*') if p.is_file()}
f=load_json(OUT/'FREEZE.json');assert all(sha(p)==h for p,h in f['files'].items())
assert load_json(OUT/'APPROVAL.json')['freeze_sha256']==sha(OUT/'FREEZE.json')
result=load_json(OUT/'RESULTS.json');config=load_json(OUT/'config.json')
assert result['status']=='COMPLETE' and result['error'] is None and result['attempted_requests']==result['returned_responses']==832
assert config['output_contract']==config['answer_policy_version']==LONG_WORK_VERSION and config['work_tokens']==1024 and config['answer_tokens']==256
tasks,groups,targets=development_data(8,targets=True);scores={};journals={};counts={};traces={}
for engine in ('serial','batch2'):
    d=OUT/engine;ts=[load_json(p) for p in sorted((d/'trials').glob('*.json'))];traces[engine]=ts
    assert len(ts)==8
    for i,t in enumerate(ts):
        assert replay(t).export()==t and t['task']==tasks[i] and t['config']==trial_parameters(config,i)
        assert t['complete'] and t['protocol']=='B1_TWO_ROUND_FOUR_ARM_V6' and not t['config']['fixture']
    score=summarize(ts,targets,[t['id'] for t in tasks],groups)
    score.update(primary_enabled=False,scope='TECHNICAL_FULL_HISTORY_D8_NOT_INDEPENDENT_CONFIRMATION')
    assert score==load_json(d/'scores.json');scores[engine]=score
    assert {k:v for k,v in score.items() if k!='reports'}==result['scores'][engine]
    rows=[json.loads(s) for s in (d/'responses.jsonl').read_text().splitlines()];journals[engine]=rows
    attempts=[json.loads(s) for s in (d/'ATTEMPTS.jsonl').read_text().splitlines()]
    assert sum(len(a['request_ids']) for a in attempts)==len(rows)==sum(len(t['records']) for t in ts)==416
    assert Counter(q for a in attempts for q in a['request_ids'])==Counter(r['record']['request_id'] for r in rows)
    assert len({r['record']['request_id'] for r in rows})==416
    for i,t in enumerate(ts):assert [r['record'] for r in rows if r['item_index']==i]==t['records']
    for row in rows:
        q=row['record'];u=q['usage'];cap=1024 if q['stage']=='work' else 256
        assert q['status']=='OK' and u['finish_reason']=='EOS' and u['ended_with_eos']
        assert q['max_new_tokens']==u['output_cap']==cap and u['output_tokens']<=cap
        assert q['source_kind']=='ACTUAL_LOCAL_MODEL_RESPONSE' and not q['fixture']
        assert u['adapter_enabled']==(q['actor']=='M1') and u['lora_layers']==252 and u['disabled_layers']==(0 if q['actor']=='M1' else 252)
        assert row['batch_size'] in ((1,) if engine=='serial' else (1,2))
    counts[engine]=dict(complete=8,attempts_and_returns=416,statuses=dict(Counter(r['record']['status'] for r in rows)),unknown=sum(r['record']['raw_output'].strip().lower()=='unknown' for r in rows))
    assert counts[engine]['unknown']==0
    assert result['counts'][engine]['input_tokens']==sum(r['record']['usage']['input_tokens'] for r in rows)
    assert result['counts'][engine]['output_tokens']==sum(r['record']['usage']['output_tokens'] for r in rows)
old=ROOT/'runs/b1-batch2-fullflow-20261105-v1'
old_traces={e:[load_json(old/e/f'trials/{i:03d}.json') for i in range(8)] for e in ('serial','batch2')}
comparisons={}
for engine in ('serial','batch2'):
    previous={r['request_id']:r for t in old_traces[engine] for r in t['records']}
    pairs=[(q['record'],previous[q['record']['request_id']]) for q in journals[engine] if q['record']['request_id'] in previous]
    comparisons[engine]=dict(shared_requests=len(pairs),same_payload_and_seed=sum(a['payload']==b['payload'] and a['seed']==b['seed'] for a,b in pairs),same_raw_output=sum(a['raw_output']==b['raw_output'] for a,b in pairs))
rescued=[]
current={r['record']['request_id']:r['record'] for r in journals['batch2']}
for t in old_traces['batch2']:
    for previous in t['records']:
        if previous['status']=='OK':continue
        now=current[previous['request_id']]
        assert now['status']=='OK'
        rescued.append(dict(request_id=now['request_id'],actor=now['actor'],arm=now['arm'],old_cap=512,old_tokens=previous['usage']['output_tokens'],new_tokens=now['usage']['output_tokens'],same_payload=now['payload']==previous['payload'],same_seed=now['seed']==previous['seed'],new_finish_reason=now['usage']['finish_reason']))
assert len(rescued)==2 and all(x['same_payload'] and x['same_seed'] for x in rescued)
for cell in range(4):assert load_json(OUT/f'cell{cell}/POST_RUN_REVIEW.json')['verdict']=='PASS'
times={e:sum(t['seconds'] for t in result['timings'] if t['engine']==e) for e in ('serial','batch2')}
assert times==result['seconds'] and abs(result['time_saved_fraction']-(1-times['batch2']/times['serial']))<1e-12
paired=[]
for i,task in enumerate(tasks):
    arms={}
    for arm in 'ABCD':
        a,b=(scores[e]['reports'][i]['arms'][arm] for e in ('serial','batch2'))
        if a['expected_em']!=b['expected_em'] or a['actual_em']!=b['actual_em']:
            arms[arm]=dict(serial_expected_em=a['expected_em'],batch2_expected_em=b['expected_em'],serial_actual_em=a['actual_em'],batch2_actual_em=b['actual_em'])
    if arms:paired.append(dict(index=i,id=task['id'],arms=arms))
assert all(sha(p)==h for p,h in before.items()),'original_run_artifact_mutated'
audit=dict(verdict='PASS_RECORDS_AND_D8_COMPLETENESS',reviewer='assistant',independence='none/provisional',scope='REPEATED_DEVELOPMENT_D8_NOT_QUALITY_EQUIVALENCE',all_original_run_files_unchanged=True,freeze_and_approval_match=True,trace_replay_journal_and_official_scores_recomputed=True,all_832_actual_EOS_cap_and_adapter_routes_verified=True,all_four_cell_reviews_pass=True,counts=counts,comparison_with_previous_512_run=comparisons,rescued_requests=rescued,changed_team_outcomes=paired,seconds=times,time_saved_fraction=result['time_saved_fraction'],max_new_generations=0,new_C_H_reads=False)
write_json(HERE/'POST_RUN_AUDIT.json',audit)
print(json.dumps(audit,ensure_ascii=False),flush=True)
