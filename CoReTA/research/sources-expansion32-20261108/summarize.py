"""Read-only descriptive paired results; seeds bound to source-task bootstrap."""
import collections, json, random
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def load(p):return json.loads(p.read_text())
cfg=load(HERE/'config.json');out=ROOT/cfg['run_dir'];scores=load(out/'scores.json') if (out/'scores.json').exists() else []
arms=['B_ordinary','E_facts','S_same_sources_m1'];index={(s['task_id'],s['unit_seed'],s['arm']):s for s in scores}
task_ids=load(HERE/'SELECTION.json')['selected_ids'];units=[]
for n in task_ids:
    for seed in cfg['seeds']:
        rows={a:index.get((n,seed,a)) for a in arms}
        if all(r and r['complete'] and r.get('score') is not None for r in rows.values()):
            units.append({'task_id':n,'seed':seed,**{a:rows[a]['score'] for a in arms},
                 'E_M1':rows['E_facts']['M1_correct'],'S_M1':rows['S_same_sources_m1']['M1_correct']})
complete_tasks=[n for n in task_ids if sum(u['task_id']==n for u in units)==2]
main=[u for u in units if u['task_id'] in complete_tasks]
def means(rows):return {a:sum(r[a] for r in rows)/len(rows) if rows else None for a in arms}
def contrast(target):
    by_task={n:[r['E_facts']-r[target] for r in main if r['task_id']==n] for n in complete_tasks}
    values=[sum(v)/len(v) for v in by_task.values()]
    rng=random.Random(2026110832);boot=[]
    if values:
        for _ in range(10000):boot.append(sum(rng.choice(values) for _ in values)/len(values))
        boot.sort()
    return {'mean_difference':sum(values)/len(values) if values else None,
        'task_cluster_descriptive_interval':[boot[249],boot[9749]] if boot else None,
        'gained_task_seed_units':[(r['task_id'],r['seed']) for r in main if r['E_facts']>r[target]],
        'lost_task_seed_units':[(r['task_id'],r['seed']) for r in main if r['E_facts']<r[target]]}
raw_text=(out/'responses.jsonl').read_text();raw=[json.loads(s) for s in raw_text[:raw_text.rfind('\n')+1].splitlines() if s.strip()]
cost=collections.defaultdict(lambda:{'logical_calls':0,'new_calls':0,'logical_input_tokens':0,'logical_output_tokens':0,'new_generation_seconds':0})
for r in raw:
    c=cost[r['arm']];c['logical_calls']+=1;c['new_calls']+=not r['shared_within_run'];c['logical_input_tokens']+=r['input_tokens'];c['logical_output_tokens']+=r['output_tokens']
    if not r['shared_within_run']:c['new_generation_seconds']+=r['elapsed_seconds']
result={'status':load(out/'STATUS.json'),'n_source_tasks_planned':32,'n_seeds':2,'n_joint_readable_units':len(units),
     'n_source_tasks_with_both_seeds_joint_readable':len(complete_tasks),'main_n_units':len(main),
     'means_both_seed_complete_tasks':means(main),'means_all_joint_readable_units':means(units),
     'per_seed':{str(s):{'n_units':len(v:=[u for u in units if u['seed']==s]),'means':means(v)} for s in cfg['seeds']},
     'E_minus_B':contrast('B_ordinary'),'E_minus_S':contrast('S_same_sources_m1'),
     'incomplete_arms':[s for s in scores if not s['complete']],
     'unknown_score_arms':[{'task_id':s['task_id'],'seed':s['unit_seed'],'arm':s['arm']} for s in scores if s['complete'] and s['score'] is None],
     'per_unit':units,'cost_by_record_family':dict(cost),
     'cost_note':'Standalone B/E28 calls, S13 including4 initials+4 selectors+5 M1 steps. Shared families counted once in actual run; logical inherited usage not new generation.',
     'limitations':'Development expansion, historical split unknown, related scenarios. Two seeds/three arms bound to same task. Bootstrap descriptive, not confirmation/equivalence/semantic annotation.'}
(HERE/'SUMMARY.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['per_unit','cost_by_record_family']}))
