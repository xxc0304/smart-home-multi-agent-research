"""Read-only opportunity audit of existing mixed-team B; no model generation."""
import importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('composition',HERE.parent/'expert-composition100-20261109/experiment.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
entries=[e for e in b.load(HERE.parent/'expert-composition100-20261109/INPUTS.json')['units'] if e['cohort']=='fresh']
labels=b.load(HERE.parent/'expert-composition100-20261109/LABELS.json')['targets'];cases=[];incomplete=[]
for e in entries:
 idx=b.source(e);finals=[idx.get((a,'final','B',3)) for a in b.ACTORS]
 if any(r is None or r['status']!='OK' for r in finals):incomplete.append(dict(index=e['source_index'],id=e['id'],rep=e['rep']));continue
 target=labels[e['id']];ans={r['actor']:r['raw_output'] for r in finals};em={a:b.answer_score(v,target)['em'] for a,v in ans.items()}
 base=e['trial_config']['seed']+e['trial_config']['task_index']*10000
 v=b.vote(ans,base+1001);sc=b.vote_scores(v,target)
 category='expert_correct_team_lost' if em['M1']==1 and sc['expected_em']<1 else 'expert_wrong_ordinary_correct' if em['M1']==0 and any(em[a] for a in b.ACTORS[1:]) else 'expert_correct_team_correct' if em['M1']==1 else 'expert_wrong_all_wrong'
 cases.append(dict(index=e['source_index'],id=e['id'],rep=e['rep'],group=e['group'],category=category,team_expected_em=sc['expected_em'],member_em=em,finals=ans,question=e['task']['question'],expert_public=[dict(round=r['round'],text=r['raw_output'],request_id=r['request_id']) for r in idx.values() if r['actor']=='M1' and r['arm']=='B' and r['stage']=='work'],source_path=e['source_path']))
from collections import Counter
result=dict(scope='ALL_EXISTING_FRESH56_B_TWO_SEEDS_DEVELOPMENT',no_model_calls=True,complete_units=len(cases),incomplete=incomplete,counts=dict(Counter(c['category'] for c in cases)),cases=cases)
b.write(HERE/'OPPORTUNITIES.json',result)
print(json.dumps({k:v for k,v in result.items() if k!='cases'},ensure_ascii=False))
for c in cases:
 if c['category'] in ['expert_correct_team_lost','expert_wrong_ordinary_correct']:print(json.dumps(c,ensure_ascii=False))
