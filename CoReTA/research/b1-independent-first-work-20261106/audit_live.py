"""Read-only early intervention integrity check, never score/stop a run."""
import json
from experiment import OUT,load,decode,verify_freeze
verify_freeze();pack=load(OUT/'INPUTS.json');entry=pack['tasks'][0];p=OUT/f'trials/{entry["index"]:03d}-r0.json'
t=load(p);b=t['branches'].get('B_delay');result=dict(index=entry['index'],task_seed_status=t['status'],freeze_unchanged=True,delayed_branch_recorded=b is not None,first_expert_input_verified=False,second_expert_history_restored=False,peer_downstream_contains_new_work=False)
if b:
    first=next((r for r in b['records'] if r['actor']=='M1' and r['stage']=='work' and r['round']==1),None)
    if first:
        history=decode(first)['history'];assert len(history)==1 and history[0]['sender']=='M1' and history[0]['phase']=='initial'
        result['first_expert_input_verified']=True
        later=[r for r in b['records'] if r['stage']=='work' and int(r['request_id'].rsplit('/',1)[1])>int(first['request_id'].rsplit('/',1)[1])]
        for r in later:
            d=decode(r);assert any(m['sender']=='M1' and m['phase']=='work' and m['text']==first['raw_output'] for m in d['history'])
            if r['actor']!='M1':result['peer_downstream_contains_new_work']=True
            if r['actor']=='M1' and r['round']==2:
                assert {m['sender'] for m in d['history'] if m['phase']=='initial'}=={'M1','M2','M3','M4'}
                result['second_expert_history_restored']=True
print(json.dumps(result),flush=True)
