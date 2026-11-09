"""Read-only completed probe audit; no model initialization/generation."""
import importlib.util,json,sys
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('frozen_probe',ROOT/'research/b1-message-probe-20261106/probe.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
OUT=m.OUT;load=m.load
m.verify_freeze();pack=load(OUT/'PREFIXES.json');ps=m.validate_pack(pack)
assert load(OUT/'APPROVAL.json')['freeze_sha256']==m.sha(OUT/'FREEZE.json')
cases=load(OUT/'CASES.json');result=load(OUT/'RESULTS.json')
attempts=[json.loads(s) for s in (OUT/'ATTEMPTS.jsonl').read_text().splitlines()]
responses=[json.loads(s) for s in (OUT/'responses.jsonl').read_text().splitlines()]
assert len(cases)==192 and len(attempts)==len(responses)==384
assert len({a['request']['request_id'] for a in attempts})==384
actual_by_id={r['request']['request_id']:r for r in responses};expected=[]
for pi,p in enumerate(ps):
    for rep in (0,1):
        rot=(pi+rep)%3;order=m.CONDITIONS[rot:]+m.CONDITIONS[:rot]
        for cond in order:
            c=cases[f'{p["id"]}/{cond}/{rep}'];w=m.work_request(p,cond,rep)
            assert c['status']=='OK' and c['work_request']==w
            f=m.final_request(p,cond,rep,c['work_response']['raw_output'])
            assert c['final_request']==f and c['final_output']==c['final_response']['raw_output']
            for req,resp in [(w,c['work_response']),(f,c['final_response'])]:
                expected.append(req);saved=actual_by_id[req['request_id']]
                assert saved['request']==req and saved['response']==resp
                assert saved['source_kind']=='ACTUAL_LOCAL_MODEL_RESPONSE' and saved['fixture'] is False
                u=resp['usage'];assert resp['status']=='OK' and u['finish_reason']=='EOS' and u['ended_with_eos']
                assert len(u['output_ids'])==u['output_tokens']<=req['max_new_tokens']
                assert u['output_cap']==req['max_new_tokens'] and u['adapter_enabled']==(req['actor']=='M1')
                assert u['lora_layers']==252 and u['disabled_layers']==(0 if req['actor']=='M1' else 252) and u['batch_size']==1
                assert isinstance(resp['raw_output'],str) and resp['raw_output'].strip()
assert [a['request'] for a in attempts]==expected==[r['request'] for r in responses]
assert [a['attempt_index'] for a in attempts]==list(range(384))
# Capture the scorer write in memory; do not overwrite the original score file.
original_sha=m.sha(OUT/'scores.json');writes={}
m.atomic=lambda p,v:writes.update({str(p):v})
scored=m.score();assert scored==load(OUT/'scores.json') and m.sha(OUT/'scores.json')==original_sha
cost=Counter();by_stage={}
for r in responses:
    q,u=r['request'],r['response']['usage'];role='E' if q['actor']=='M1' else 'B'
    key=role+'_'+q['stage'];b=by_stage.setdefault(key,dict(calls=0,input_tokens=0,output_tokens=0,generation_seconds=0))
    b['calls']+=1;b['input_tokens']+=u['input_tokens'];b['output_tokens']+=u['output_tokens'];b['generation_seconds']+=u['elapsed_seconds']
    cost['input_tokens']+=u['input_tokens'];cost['output_tokens']+=u['output_tokens']
assert cost['output_tokens']==result['output_tokens']==30453
audit=dict(verdict='PASS_ALL_RECORDS_REQUESTS_ROUTING_AND_OFFICIAL_SCORING',reviewer='assistant',independence='none/provisional',new_model_calls=0,freeze_verified=True,approval_verified=True,original_scores_unchanged=True,scorer_exact_recomputation=True,source_prefixes=32,questions=16,cases=192,attempts=384,confirmed_returns=384,all_eos=True,request_sequence_exact=True,matched_three_condition_units=64,cost=dict(cost),by_role_stage=by_stage,elapsed_seconds=result['elapsed_seconds'],semantic_correctness_not_certified_by_technical_audit=True)
(HERE/'POST_RUN_AUDIT.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(audit),flush=True)
