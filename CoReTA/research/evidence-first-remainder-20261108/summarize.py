"""Descriptive paired development summary; missing outputs remain missing."""
import json
import experiment as e

cfg=e.load(e.HERE/'config.json');out=e.ROOT/cfg['run_dir']
scores=e.load(out/'scores.json') if (out/'scores.json').exists() else []
by={(r['task_id'],r['arm']):r for r in scores}
tasks=e.load(e.HERE/'tasks.json');labels=e.load(e.HERE/'labels.json')
common=[t['id'] for t in tasks if all((t['id'],a) in by and by[(t['id'],a)]['complete'] and
          by[(t['id'],a)]['final_vote'] is not None for a in e.ARMS)]
means={}
for arm in e.ARMS:
    rows=[by[(n,arm)] for n in common]
    means[arm]={'n_common_tasks':len(rows),'expected_team_accuracy':sum(r['final_vote']['expected_accuracy'] for r in rows)/len(rows) if rows else None,
        'expert_final_accuracy':sum(r['expert_final_correct'] for r in rows)/len(rows) if rows else None,
        'ordinary_individual_mean_accuracy':sum(sum(x==labels[str(r['task_id'])]['correct'] for a,x in r['final_answers'].items() if a!='M1')/3 for r in rows)/len(rows) if rows else None}
contrasts={}
for left,right in [('B_ordinary','A_private'),('E_facts','B_ordinary'),('F_facts_opinions','B_ordinary'),('E_facts','F_facts_opinions')]:
    pairs=[(by[(n,left)],by[(n,right)]) for n in common]
    contrasts[left+' minus '+right]={'n':len(pairs),'mean_team_delta':sum(a['final_vote']['expected_accuracy']-b['final_vote']['expected_accuracy'] for a,b in pairs)/len(pairs) if pairs else None,
        'expert_gains':sum(a['expert_final_correct'] is True and b['expert_final_correct'] is False for a,b in pairs),
        'expert_harms':sum(a['expert_final_correct'] is False and b['expert_final_correct'] is True for a,b in pairs)}
summary={'status':e.load(out/'STATUS.json')['status'],'n_source_tasks':len(tasks),'common_readable_task_ids':common,
         'arms':means,'contrasts':contrasts,'scores':scores,'no_population_significance_claim':True,
         'scope':'Previously used development scenarios, one seed, information advantage adaptation; not held-out method effectiveness.'}
e.write(e.HERE/'SUMMARY.json',summary)
print(json.dumps({k:v for k,v in summary.items() if k!='scores'}))
