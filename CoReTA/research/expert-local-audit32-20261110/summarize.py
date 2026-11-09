"""Ancillary descriptive summaries; immutable trial scores are never changed."""
from collections import defaultdict
import json
from experiment import HERE,ROOT,load,jsonlines,write
c=load(HERE/'config.json');out=ROOT/c['run_dir'];scores=load(out/'scores.json');rows=jsonlines(out/'responses.jsonl')
arms=('R','S','G','L');sensitivity=set(load(HERE/'SCORING.json')['fixed_boundary_sensitivity_exclude_indices'])
def summary(sample):
 result={'processed_units':len(sample),'eligible_units':sum(s['prefix_complete'] for s in sample),'arms':{},'paired':{}}
 for a in arms:
  good=[s for s in sample if s['arms'][a]['complete']]
  result['arms'][a]={'valid_units':len(good),'different_tasks':len({s['id'] for s in good}),
   'em':sum(s['arms'][a]['metrics']['em'] for s in good)/len(good) if good else None,
   'f1':sum(s['arms'][a]['metrics']['f1'] for s in good)/len(good) if good else None}
 for b in ('G','S','R'):
  eligible=[s for s in sample if s['arms']['L']['complete'] and s['arms'][b]['complete']]
  groups=defaultdict(list)
  for s in eligible:groups[s['id']].append(s)
  full={k:v for k,v in groups.items() if len(v)==2 and {s['rep'] for s in v}=={0,1}}
  deltas=[sum(s['arms']['L']['metrics']['em']-s['arms'][b]['metrics']['em'] for s in v)/2 for v in full.values()]
  result['paired']['L-'+b]={'common_units':len(eligible),'complete_two_seed_tasks':len(full),
   'mean_task_em_difference':sum(deltas)/len(deltas) if deltas else None,
   'positive_tasks':sum(x>0 for x in deltas),'negative_tasks':sum(x<0 for x in deltas),'tied_tasks':sum(x==0 for x in deltas)}
 for a in ('S','G','L'):
  pairs=[s for s in sample if s['arms']['R']['complete'] and s['arms'][a]['complete']]
  wrong=[s for s in pairs if s['arms']['R']['metrics']['em']==0];right=[s for s in pairs if s['arms']['R']['metrics']['em']==1]
  result['arms'][a]['candidate_transitions']={'wrong_opportunities':len(wrong),'wrong_to_right':sum(s['arms'][a]['metrics']['em']==1 for s in wrong),
   'right_opportunities':len(right),'right_to_wrong':sum(s['arms'][a]['metrics']['em']==0 for s in right)}
 return result
usage=[r['usage'] for r in rows if r['origin']=='model']
result={'status':load(out/'STATUS.json'),'background':summary([s for s in scores if s['stratum']=='background']),
 'diagnostic':summary([s for s in scores if s['stratum']=='diagnostic']),
 'fixed_lower_boundary_background':summary([s for s in scores if s['stratum']=='background' and s['index'] not in sensitivity]),
 'auxiliary_mixed_development':summary(scores),
 'new_cost':{'calls':len(rows),'generated':len(usage),'output_tokens':sum(u['output_tokens'] for u in usage),'generation_seconds':sum(u['elapsed_seconds'] for u in usage)},
 'warning':'Development/frozen proposal component study; paired task differences require both seeds. No semantic verification inferred from correctness; incomplete units not zero.'}
write(HERE/'LIVE_SUMMARY.json',result);print(json.dumps(result,ensure_ascii=False))
