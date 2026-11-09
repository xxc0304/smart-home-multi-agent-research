"""Prespecified descriptive all11/fresh-flow9 views and process candidate ledger."""
import json
import experiment as e
cfg=e.load(e.HERE/'config.json');out=e.ROOT/cfg['run_dir']
scores=e.load(out/'scores.json') if (out/'scores.json').exists() else []
rows=[json.loads(s) for s in (out/'responses.jsonl').read_text().splitlines() if s.strip()]
tasks=e.load(e.HERE/'tasks.json');labels=e.load(e.HERE/'labels.json');by={(s['task_id'],s['arm']):s for s in scores}
eligible=[t['id'] for t in tasks if all((t['id'],a) in by and by[(t['id'],a)]['complete'] and by[(t['id'],a)]['final_vote'] is not None for a in e.ARMS)]

def describe(ids):
    n=len(ids);means={};contrasts={};table=[]
    for a in e.ARMS:
        ss=[by[(t,a)] for t in ids]
        means[a]={'n_tasks':n,'team_expected_accuracy':sum(s['final_vote']['expected_accuracy'] for s in ss)/n if n else None,
           'M1_final_accuracy':sum(s['expert_final_correct'] for s in ss)/n if n else None,
           'ordinary_individual_accuracy':sum(sum(v==s['gold'] for k,v in s['final_answers'].items() if k!='M1') for s in ss)/(3*n) if n else None}
    for a,b in [('E_facts','B_ordinary'),('F_facts_opinions','B_ordinary'),('E_facts','F_facts_opinions'),('B_ordinary','A_private')]:
        gains=[];losses=[]
        for t in ids:
            delta=by[(t,a)]['final_vote']['expected_accuracy']-by[(t,b)]['final_vote']['expected_accuracy']
            if delta>0:gains.append({'task_id':t,'delta':delta})
            if delta<0:losses.append({'task_id':t,'delta':delta})
        contrasts[a+' minus '+b]={'gains':gains,'losses':losses,'mean_delta':(sum(r['delta'] for r in gains+losses)/n if n else None)}
    m1_private=sum(by[(t,'A_private')]['expert_final_correct'] for t in ids)/n if n else None
    for t in ids:table.append({'task_id':t,'M1_private':by[(t,'A_private')]['expert_final_correct'],
        'M1_initial':by[(t,'A_private')]['expert_initial_correct'],
        'team_expected':{a:by[(t,a)]['final_vote']['expected_accuracy'] for a in e.ARMS},
        'M1_final':{a:by[(t,a)]['expert_final_correct'] for a in e.ARMS}})
    return {'task_ids':ids,'n':n,'means':means,'M1_private_accuracy':m1_private,'contrasts':contrasts,'table':table}

changes=[];correction_candidates=[]
for s in scores:
    if not s['complete']:continue
    subset=[r for r in rows if r['task_id']==s['task_id'] and r['arm']==s['arm']]
    for f in [r for r in subset if r['stage']=='final']:
        work=[r for r in subset if r['stage']=='work' and r['actor']==f['actor']]
        if len(work)==4 and work[-1]['answer']!=f['answer']:
            changes.append({'task_id':s['task_id'],'arm':s['arm'],'actor':f['actor'],
              'last_work':work[-1]['answer'],'final':f['answer'],'initial':s['initial_answers'][f['actor']],
              'last_work_call':work[-1]['call'],'final_call':f['call'],
              'last_work_in_final_payload':work[-1]['text'] in f['payload']['user'],
              'last_work_correct':None if work[-1]['answer'] is None else work[-1]['answer']==s['gold'],
              'final_correct':None if f['answer'] is None else f['answer']==s['gold']})
    private=by.get((s['task_id'],'A_private'))
    if private and private.get('complete') and private['expert_final_correct'] is False and s['arm']!='A_private' and (s['expert_final_correct'] or (s['final_vote'] and s['final_vote']['expected_accuracy']>0)):
        correction_candidates.append({'task_id':s['task_id'],'arm':s['arm'],'requires_semantic_trace_review':True,
            'note':'Do not call this ordinary-member causal correction before evidence and adoption review.'})
status=e.load(out/'STATUS.json')
summary={'status':status,'planned_task_ids':e.IDS,'complete_pair_ids':eligible,
         'all11_view':describe(eligible),'excluding_complete_technical2_view':describe([n for n in eligible if n not in [11,33]]),
         'predeclared_clearer_subset_view':describe([n for n in eligible if n in [9,33,34]]),
         'work_final_changes':changes,'ordinary_correction_candidates':correction_candidates,
         'failed_arms':[s for s in scores if not s['complete']],
         'actual_new_output_tokens':sum(r['output_tokens'] for r in rows if not r.get('inherited')),
         'actual_reused_output_tokens':sum(r['output_tokens'] for r in rows if r.get('inherited')),
         'scope':'Fixed used development tasks, one seed; no population significance, equivalence, psychological mechanism, or efficiency superiority claim.'}
e.write(e.HERE/'SUMMARY.json',summary)
print(json.dumps({k:v for k,v in summary.items() if k not in ['ordinary_correction_candidates','work_final_changes']}))
