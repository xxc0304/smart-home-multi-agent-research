import json
from experiment import OUT,load,decode,entry_order,INSTRUCTIONS,verify_freeze
verify_freeze();pack=load(OUT/'INPUTS.json');e=entry_order(pack)[0];c=load(OUT/'config.json');f=OUT/f'trials/{e["index"]:03d}.json'
t=load(f);raw=(OUT/'responses.jsonl').read_text();rows=[json.loads(x) for x in raw.split('\n')[:-1] if x];by={r['request']['request_id']:r for r in rows}
result=dict(index=e['index'],cohort=e['cohort'],status=t['status'],freeze_unchanged=True,initials=len(t['initials']),conditions={},new_returns=len(rows))
for cond,b in t['branches'].items():
  targeted=[];shared=0;new_after=0;seen=None
  for r in b['records']:
    d=decode(r,c['answer_suffix'] if r['stage']=='final' else '')
    assert d['paragraphs']==e['task']['paragraphs'] and not any(z['phase']=='final' for z in d['history'])
    if 'shared_prefix_from' in r:
      z=by[r['shared_prefix_from']];assert r['raw_output']==z['response']['raw_output'] and r['payload']==z['request']['payload'];shared+=1
    if seen is not None:assert any(z['sender']=='M1' and z.get('round')==2 and z['text']==seen for z in d['history']);new_after+=1
    if cond in INSTRUCTIONS and r['actor']=='M1' and r['stage']=='work' and r['round']==2:
      assert d['work_instruction']==INSTRUCTIONS[cond];targeted.append(r['request_id']);seen=r['raw_output']
    else:assert 'work_instruction' not in d
    u=r['usage'];assert u['adapter_enabled']==(r['actor']=='M1') and u['disabled_layers']==(0 if r['actor']=='M1' else 252) and u['batch_size']==1
  result['conditions'][cond]=dict(records=len(b['records']),complete=b['complete'],shared=shared,target_instruction_observed=bool(targeted),new_downstream_observed=new_after)
print(json.dumps(result),flush=True)
