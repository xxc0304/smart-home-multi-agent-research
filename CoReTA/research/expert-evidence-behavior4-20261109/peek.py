"""Read-only completed-response preview, not a semantic judge."""
import json,sys
from probe import HERE,ROOT,load
c=load(HERE/'config.json');out=ROOT/c['run_dir'];s=(out/'responses.jsonl').read_text();rows=[json.loads(x) for x in s[:s.rfind('\n')+1].splitlines()]
unit=int(sys.argv[1]) if len(sys.argv)>1 else None
for r in rows:
 if unit is not None and r['unit']!=unit:continue
 print(json.dumps({k:r[k] for k in ['call','unit','index','rep','arm','actor','stage','status','raw_output']},ensure_ascii=False))
