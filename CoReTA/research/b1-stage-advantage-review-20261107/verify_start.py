import json
from repeat import OUT,load,OFFSET
s=load(OUT/'STATUS.json');records=[json.loads(x) for x in (OUT/'responses.jsonl').read_text().splitlines()]
pack=load(OUT/'REPEAT_INPUTS.json');checks=[]
for r in records:
 e=next(e for e in pack['tasks'] if r['request_id'].startswith(e['id']+'/'))
 cursor=int(r['request_id'].split('/')[-1]);base=e['sourceConfig']['seed']+e['index']*10000
 expected=base+(0 if r['stage']=='initial' else 1000+r['round']*100 if r['stage']=='work' else 2000)+['M1','M2','M3','M4'].index(r['actor'])+OFFSET
 assert r['seed']==expected
 assert r['usage']['disabled_layers']==(0 if r['actor']=='M1' else 252)
 checks.append(r['request_id'])
print(json.dumps({'status':s,'actual_requests_checked':len(checks),'seed_and_adapter_routes_pass':True,'first_scoring_checkpoint_exists':(OUT/'scores.json').exists()}))
