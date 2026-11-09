"""Read-only review of D8 serial/batch2 execution and matched scoring."""
import hashlib,json,os,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];os.chdir(ROOT);sys.path.insert(0,str(ROOT/'tools'))
from b1_runtime import load_json,development_data
from b1_controls import replay,summarize
from b0_answers import write_json
HERE=Path(__file__).resolve().parent;OUT=ROOT/'runs/b1-batch2-fullflow-20261105-v1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
before={str(p):sha(p) for p in OUT.rglob('*') if p.is_file()}
f=load_json(OUT/'FREEZE.json');assert all(sha(p)==h for p,h in f['files'].items())
assert load_json(OUT/'APPROVAL.json')['freeze_sha256']==sha(OUT/'FREEZE.json')
tasks,groups,targets=development_data(8,targets=True);reports={};journals={};traces={};counts={}
for engine in ('serial','batch2'):
    d=OUT/engine;ts=[load_json(p) for p in sorted((d/'trials').glob('*.json'))];traces[engine]=ts
    assert len(ts)==8
    for i,t in enumerate(ts):assert replay(t).export()==t and t['task']==tasks[i]
    score=summarize(ts,targets,[t['id'] for t in tasks],groups);score.update(primary_enabled=False,scope='TECHNICAL_FULL_HISTORY_D8_NOT_INDEPENDENT_CONFIRMATION')
    assert score==load_json(d/'scores.json');reports[engine]=score['reports']
    rows=[json.loads(s) for s in (d/'responses.jsonl').read_text().splitlines()];journals[engine]=rows
    attempts=[json.loads(s) for s in (d/'ATTEMPTS.jsonl').read_text().splitlines()]
    assert sum(len(a['request_ids']) for a in attempts)==len(rows)==sum(len(t['records']) for t in ts)
    assert len({r['record']['request_id'] for r in rows})==len(rows)
    for i,t in enumerate(ts):assert [r['record'] for r in rows if r['item_index']==i]==t['records']
    for r in rows:
        u=r['record']['usage'];q=r['record'];assert u['adapter_enabled']==(q['actor']=='M1') and u['disabled_layers']==(0 if q['actor']=='M1' else u['lora_layers'])
        if q['status']=='OK':assert u['finish_reason']=='EOS' and u['ended_with_eos']
        else:assert q['status']=='OUTPUT_LIMIT' and u['output_tokens']==u['output_cap']==512 and not u['ended_with_eos']
    counts[engine]=dict(attempted=len(rows),complete=sum(t['complete'] for t in ts),statuses=dict(Counter(r['record']['status'] for r in rows)))
assert counts['serial']['attempted']==416 and counts['serial']['complete']==8
assert counts['batch2']['attempted']==397 and counts['batch2']['complete']==7
bad=[]
for r in journals['batch2']:
    q=r['record']
    if q['status']=='OK':continue
    s=next(x['record'] for x in journals['serial'] if x['record']['request_id']==q['request_id'])
    bad.append(dict(index=r['item_index'],request_id=q['request_id'],actor=q['actor'],arm=q['arm'],round=q['round'],batch_size=r['batch_size'],output_tokens=q['usage']['output_tokens'],serial_tokens=s['usage']['output_tokens'],same_payload=s['payload']==q['payload'],same_seed=s['seed']==q['seed'],raw_output=q['raw_output']))
assert len(bad)==2 and {r['index'] for r in bad}=={5}
matched=[i for i in range(8) if traces['serial'][i]['complete'] and traces['batch2'][i]['complete']]
matched_scores={}
for arm in 'ABCD':
    matched_scores[arm]={e:dict(expected_em=sum(reports[e][i]['arms'][arm]['expected_em'] for i in matched)/len(matched),actual_correct=sum(reports[e][i]['arms'][arm]['actual_em'] for i in matched),expert_correct=sum(reports[e][i]['arms'][arm]['expert_em'] for i in matched)) for e in ('serial','batch2')}
old=ROOT/'runs/b1-dev32-final-20261104-v2'
serial_matches=0
for i,t in enumerate(traces['serial']):
    prev=load_json(old/f'trials/{i:03d}.json')
    serial_matches+=sum(a['payload']==b['payload'] and a['seed']==b['seed'] and a['raw_output']==b['raw_output'] for a,b in zip(t['records'],prev['records']))
assert all(sha(p)==h for p,h in before.items())
audit=dict(verdict='PASS_RECORDS_REVISE_BATCH2_COMPLETENESS',reviewer='assistant',independence='none/provisional',scope='DEVELOPMENT_TECHNICAL_D8_NOT_QUALITY_EQUIVALENCE',all_original_run_files_unchanged=True,freeze_and_approval_match=True,trace_replay_journal_and_official_scores_recomputed=True,counts=counts,failed=bad,matched_complete_indices=matched,matched_scores=matched_scores,serial_payload_seed_raw_matches_old_of416=serial_matches,unused_dependent_requests=832-813)
write_json(HERE/'POST_RUN_AUDIT.json',audit)
print(json.dumps({k:v for k,v in audit.items() if k not in ('failed','matched_scores')},ensure_ascii=False),flush=True)
