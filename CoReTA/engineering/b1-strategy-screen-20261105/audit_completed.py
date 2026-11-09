"""Post-run read-only audit; no generation and no mutation of run artifacts."""
import hashlib,json,os,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];os.chdir(ROOT);sys.path.insert(0,str(ROOT/'tools'))
from b1_runtime import load_json,development_data
from b1_controls import replay
from b0_answers import answer_score,write_json
HERE=Path(__file__).resolve().parent;OUT=ROOT/'runs/b1-strategy-screen-20261105-v2'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
before={str(p):sha(p) for p in OUT.rglob('*') if p.is_file()}
f=load_json(OUT/'FREEZE.json');a=load_json(OUT/'APPROVAL.json');result=load_json(OUT/'RESULTS.json')
assert a['freeze_sha256']==sha(OUT/'FREEZE.json')
assert all(sha(p)==h for p,h in f['files'].items())
assert result['status']=='COMPLETE' and result['error'] is None
requests=load_json(OUT/'REQUESTS.json');plan=load_json(OUT/'PLAN.json')
rows=[json.loads(s) for s in (OUT/'responses.jsonl').read_text().splitlines()]
attempts=[json.loads(s) for s in (OUT/'ATTEMPTS.jsonl').read_text().splitlines()]
assert len(rows)==sum(len(x['indices']) for x in attempts)==256
assert len({(r['engine'],r['repeat'],r['index']) for r in rows})==256
tasks,_,targets=development_data(8,targets=True)
old=ROOT/'runs/b1-dev32-final-20261104-v2'
traces=[load_json(old/f'trials/{i:03d}.json') for i in range(8)]
assert all(replay(t).export()==t and t['complete'] for t in traces)
for req in requests:
    t=next(t for t in traces if req['request_id'].startswith(t['task']['id']+'|'))
    rec=next(r for r in t['records'] if r['request_id']==req['request_id'])
    assert all(req[k]==rec[k] for k in req)
eos=load_json(OUT/'BACKEND.json')['effective_generation_config']['eos_token_id']
if not isinstance(eos,list):eos=[eos]
for r in rows:
    u=r['usage'];q=r['request'];assert q==requests[r['index']]
    assert r['status']=='OK' and u['finish_reason']=='EOS' and u['ended_with_eos']
    assert u['output_ids'][-1] in eos and len(u['output_ids'])==u['output_tokens']
    assert u['adapter_enabled']==(q['actor']=='M1') and u['disabled_layers']==(0 if q['actor']=='M1' else u['lora_layers']) and u['lora_layers']>0
    if u['batch_size']>1:assert u['rng_seed']==q['seed'] and u['rng_before']!=u['rng_after']
    assert u['input_tokens']==plan['lengths'][r['index']]
lookup={(r['engine'],r['repeat'],r['index']):r for r in rows};vectors={}
for cell in result['cells']:
    engine,rep=cell['engine'],cell['repeat'];rs=[lookup[engine,rep,i] for i in range(32)]
    assert [x['indices'] for x in attempts if x['engine']==engine and x['repeat']==rep]==plan['batches'][engine]
    finals=[r for r in rs if r['request']['stage']=='final']
    scores=[answer_score(r['raw_output'],targets[r['request']['request_id'].rsplit('|',1)[0]]) for r in finals]
    assert len(scores)==16 and sum(s['em'] for s in scores)/16==cell['final_EM']
    assert abs(sum(s['f1'] for s in scores)/16-cell['final_F1'])<1e-12
    assert cell['output_tokens']==sum(r['usage']['output_tokens'] for r in rs)
    vectors[engine,rep]=[s['em'] for s in scores]
repeats={e:sum(lookup[e,0,i]['usage']['output_ids']==lookup[e,1,i]['usage']['output_ids'] for i in range(32)) for e in result['aggregate']}
final_differences={e:[dict(index=i,serial=lookup['serial',0,i]['raw_output'],candidate=lookup[e,0,i]['raw_output']) for i in range(32) if requests[i]['stage']=='final' and lookup['serial',0,i]['raw_output']!=lookup[e,0,i]['raw_output']] for e in result['aggregate'] if e!='serial'}
assert all(sha(p)==h for p,h in before.items())
audit=dict(verdict='PASS',reviewer='assistant',independence='none/provisional',scope='FIXED_HISTORY_SCREEN_NOT_TEAM_QUALITY_EQUIVALENCE',all_run_files_unchanged=True,freeze_and_approval_match=True,calls_attempted_and_returned=256,all_EOS=True,all_payloads_match_real_history=True,route_flags_and_sampling_seeds_valid=True,conditional_final_scores_recomputed=True,within_engine_token_stable_pairs_of32=repeats,final_correctness_vectors={e:{str(rep):vectors[e,rep] for rep in (0,1)} for e in result['aggregate']},final_answer_differences_vs_serial=final_differences,aggregate=result['aggregate'])
write_json(HERE/'POST_RUN_AUDIT.json',audit)
print(json.dumps(dict(verdict='PASS',calls=256,repeats=repeats,final_answer_differences=final_differences,all_final_correctness_vectors_same=all(v==vectors['serial',0] for v in vectors.values())),ensure_ascii=False),flush=True)
