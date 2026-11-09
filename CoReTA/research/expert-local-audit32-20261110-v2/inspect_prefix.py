"""Read-only console view; writes an ancillary timing snapshot, never scoring/model inputs."""
import json
from experiment import HERE,ROOT,load,jsonlines,write
c=load(HERE/'config.json');out=ROOT/c['run_dir'];rows=jsonlines(out/'responses.jsonl')
print(json.dumps(load(out/'STATUS.json')))
for r in rows:
 if r['unit'] in (39,0):
  print(json.dumps({k:r[k] for k in ('call','unit','index','actor','arm','stage','slot','status','raw_output')},ensure_ascii=False))
usage=[r['usage'] for r in rows if r['origin']=='model']
timing={'responses':len(rows),'generated':len(usage),'output_tokens':sum(u['output_tokens'] for u in usage),
 'generation_seconds':sum(u['elapsed_seconds'] for u in usage),'non_ok':sum(r['status']!='OK' for r in rows)}
write(HERE/'PREFIX_TIMING.json',timing);print(json.dumps(timing))
