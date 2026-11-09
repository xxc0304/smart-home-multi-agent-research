"""Read-only early real cross-factor/visibility check, never score or stop."""
import json
from experiment import OUT,load,decode,source_trace,verify_freeze
verify_freeze();e=load(OUT/'INPUTS.json')['tasks'][0];f=OUT/f'trials/{e["index"]:03d}-S0O1.json'
t=load(f);src=source_trace(e,0);order=source_trace(e,1)['branches']['B']
assert t['initial_records']==src['initial_records'] and t['initials']==src['initials']
result=dict(index=e['index'],sampling=0,order_setting=1,task_cell_status=t['status'],freeze_unchanged=True,source_initials_exact=True,order_matches_O1=True,first_expert_input_verified=False,second_expert_history_restored=False,downstream_reads_new_work=False)
for cond,b in t['branches'].items():
    assert b['orders']==order['orders'] and b['initial_order']==order['initial_order']
    assert b['config']['seed']==20261102 and b['config']['order_seed']==120261102
    for r in b['records']:
        expected=20261102+e['index']*10000+(1000+r['round']*100 if r['stage']=='work' else 2000)+('M1','M2','M3','M4').index(r['actor'])
        assert r['seed']==expected
b=t['branches'].get('B_delay')
if b:
    first=next((r for r in b['records'] if r['actor']=='M1' and r['stage']=='work' and r['round']==1),None)
    if first:
        h=decode(first)['history'];assert h==[dict(sender='M1',phase='initial',text=src['initials']['M1'])];result['first_expert_input_verified']=True
        for r in b['records']:
            if r['stage']!='work' or int(r['request_id'].rsplit('/',1)[1])<=int(first['request_id'].rsplit('/',1)[1]):continue
            d=decode(r);assert any(m['sender']=='M1' and m['phase']=='work' and m['text']==first['raw_output'] for m in d['history'])
            if r['actor']!='M1':result['downstream_reads_new_work']=True
            if r['actor']=='M1' and r['round']==2:assert {m['sender'] for m in d['history'] if m['phase']=='initial'}=={'M1','M2','M3','M4'};result['second_expert_history_restored']=True
print(json.dumps(result),flush=True)
