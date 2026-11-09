"""Read-only audit of frozen D32 records; exports new audit artifacts only."""
import json,sys,hashlib
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from b1_runtime import load_json,development_data
from b1_controls import replay,summarize
from b0_answers import write_json
OUT=Path(__file__).resolve().parent
RUN=ROOT/'runs/b1-dev32-final-20261104-v2'
m=load_json(RUN/'manifest.json');saved=load_json(RUN/'scores.json')
traces=[load_json(p) for p in sorted((RUN/'trials').glob('*.json'))]
tasks,groups,targets=development_data(32,targets=True)
rebuilt=summarize(traces,targets,m['expected_ids'],groups)
assert rebuilt==saved,'score_rebuild_mismatch'
checks=[]
for t in traces:
    rt=replay(t)
    assert rt.complete==t['complete']
    for r in t['records']:
        if r['status']=='OK':assert r['usage']['adapter_enabled']==(r['actor']=='M1')
        d=json.loads(r['payload']['user'].split('TASK_DATA\n',1)[1].split('\n\nAnswer the question above.',1)[0])
        if r['stage']!='initial':
            assert ('team_information' in d)==(r['arm'] in ('C','D'))
            if r['arm'] in ('A','C'):assert all(h['sender']==r['actor'] for h in d['history'])
            assert all(h['phase']!='final' for h in d['history'])
    checks.append(dict(id=t['task']['id'],complete=t['complete'],n=len(t['records'])))
complete=[r for r in saved['reports'] if r['complete']]
initial={a:sum(r['initial']['members'][a]['em'] for r in complete) for a in ('M1','M2','M3','M4')}
events={};arms={}
for arm in 'ABCD':
    valid=[r for r in saved['reports'] if r['arms'].get(arm,{}).get('complete')]
    values=[r['arms'][arm] for r in valid]
    harms=[r['id'] for r in complete if r['arms'][arm]['expert_harm']]
    corrections=[r['id'] for r in complete if r['arms'][arm]['expert_correction']]
    lost=[r['id'] for r in complete if r['arms'][arm]['expert_correct_but_not_selected_expected']>0]
    arms[arm]=dict(available_n=len(valid),expected_sum=sum(v['expected_em'] for v in values),
        planned32_expected_bounds=[sum(v['expected_em'] for v in values)/32,
            (sum(v['expected_em'] for v in values)+32-len(valid))/32],
        harm_ids=harms,correction_ids=corrections,readout_loss_ids=lost,
        ordinary_initial_correct=sum(initial[a] for a in ('M2','M3','M4')),
        ordinary_final_correct=sum(r['arms'][arm]['members'][a]['em'] for r in complete for a in ('M2','M3','M4')),
        correct_candidate_but_team_not_correct=[r['id'] for r in complete if r['arms'][arm]['oracle_hit'] and r['arms'][arm]['expected_em']<1])
    for task_id in set(harms+corrections+lost):events.setdefault(task_id,[]).append(arm)
bounds={}
for name,l,r in [('B-A','B','A'),('D-C','D','C'),('D-B','D','B'),('C-A','C','A')]:
    lo=hi=0;paired=0
    for item in saved['reports']:
        a=item['arms'].get(l,{});b=item['arms'].get(r,{})
        if a.get('complete') and b.get('complete'):
            lo+=a['expected_em']-b['expected_em'];hi+=a['expected_em']-b['expected_em'];paired+=1
        else:
            lo+=(a['expected_em'] if a.get('complete') else 0)-(b['expected_em'] if b.get('complete') else 1)
            hi+=(a['expected_em'] if a.get('complete') else 1)-(b['expected_em'] if b.get('complete') else 0)
    bounds[name]=dict(available_pairs=paired,planned32_difference_bounds=[lo/32,hi/32])
cases=[]
for t in traces:
    if t['task']['id'] not in events:continue
    r=next(r for r in saved['reports'] if r['id']==t['task']['id'])
    cases.append(dict(id=t['task']['id'],question=t['task']['question'],paragraphs=t['task']['paragraphs'],
        target=targets[t['task']['id']],initials=t['initials'],score=r,
        messages={a:[dict(actor=x['actor'],round=x['round'],text=x['raw_output'],request_id=x['request_id'])
            for x in t['records'] if x['stage']=='work' and x['arm']==a] for a in 'ABCD'}))
result=dict(recomputed_scores_identical=True,all32_replay_structurally_valid=True,
    private_visibility_and_identity_and_no_final_leak='PASS',initial_correct_complete28=initial,
    arms=arms,missing_bounds=bounds,contrasts=saved['contrasts'],n_case_exports=len(cases),
    scoring_status=saved['status'],primary_enabled=saved['primary_enabled'])
write_json(OUT/'AUDIT.json',result);write_json(OUT/'PROCESS_CASES.json',cases)
print(json.dumps(result,ensure_ascii=False))
