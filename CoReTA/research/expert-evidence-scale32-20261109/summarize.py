"""Read-only score/cost report. Main paired analysis requires both seeds."""
import json,random
from experiment import HERE,ROOT,load,write,jsonlines,ARMS
c=load(HERE/'config.json');out=ROOT/c['run_dir'];rows=jsonlines(out/'responses.jsonl');ss=load(out/'scores.json') if (out/'scores.json').exists() else []
status=load(out/'STATUS.json');usage=[r['usage'] for r in rows if r['origin']=='model']
result=dict(status=status,cost=dict(generated_calls=len(usage),output_tokens=sum(u['output_tokens'] for u in usage),response_seconds=sum(u['elapsed_seconds'] for u in usage),non_ok=sum(r['status']!='OK' for r in rows)),available_units={})
for cohort in ['background','diagnostic']:
 good=[s for s in ss if s['stratum']==cohort and all(s['arms'][a]['complete'] for a in ARMS)]
 result['available_units'][cohort]=dict(n=len(good),seed_counts={str(rep):sum(s['rep']==rep for s in good) for rep in [0,1]},arms={a:dict(team_expected_em=sum(s['arms'][a]['expected_em'] for s in good)/len(good),expert_em=sum(s['arms'][a]['members']['M1']['em'] for s in good)/len(good),ordinary_em=sum(s['arms'][a]['members'][actor]['em'] for s in good for actor in ['M2','M3','M4'])/(3*len(good))) for a in ARMS} if good else {})
fixed=set(load(HERE/'SCORING.json')['fixed_boundary_sensitivity_exclude_indices']);main=[];sensitive=[]
for idx in sorted({s['index'] for s in ss if s['stratum']=='background'}):
 pair=[s for s in ss if s['index']==idx and s['stratum']=='background' and all(s['arms'][a]['complete'] for a in ARMS)]
 if {s['rep'] for s in pair}!={0,1}:continue
 row=dict(index=idx,arms={a:sum(s['arms'][a]['expected_em'] for s in pair)/2 for a in ARMS})
 main.append(row)
 if idx not in fixed:sensitive.append(row)
def paired(data):
 ans=dict(different_tasks=len(data),arms={a:sum(r['arms'][a] for r in data)/len(data) for a in ARMS} if data else {},contrasts={})
 for a,b in [('C','B'),('B','A'),('C','A')]:
  if not data:continue
  differences=[r['arms'][a]-r['arms'][b] for r in data];rng=random.Random(20261109);bs=sorted(sum(rng.choice(differences) for _ in data)/len(data) for _ in range(4000))
  ans['contrasts'][a+'-'+b]=dict(mean=sum(differences)/len(data),descriptive_task_bootstrap95=[bs[100],bs[3899]],tasks_positive=sum(x>0 for x in differences),tasks_negative=sum(x<0 for x in differences),tasks_equal=sum(x==0 for x in differences))
 return ans
result['primary_background_both_seeds']=paired(main);result['fixed19_sensitivity_both_seeds']=paired(sensitive)
result['scope']='Existing development; assistant exploratory analysis. '+('Final completed-run available-case summary; missing scheduled units remain explicit.' if status['status'].startswith('COMPLETED') else 'Available prefix units not a completed primary comparison.')+' Bootstrap descriptive, no population or independent confirmation claim.'
write(HERE/'LIVE_SUMMARY.json',result);print(json.dumps(result,ensure_ascii=False))
