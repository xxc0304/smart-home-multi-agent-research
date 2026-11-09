"""Read-only cost estimate; never reads answer scores or changes selection."""
import json,time
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'runs/b1-fixed-prefix-20261106-v1'
raw=(OUT/'responses.jsonl').read_text();lines=raw.splitlines()
if raw and not raw.endswith('\n'):lines=lines[:-1]
rows=[json.loads(s) for s in lines];buckets=defaultdict(list)
for r in rows:
    role='E' if r['request']['actor']=='M1' else 'B'
    buckets[role+'_'+r['request']['stage']].append(r['response']['usage']['elapsed_seconds'])
elapsed=time.time()-(OUT/'STARTED').stat().st_mtime
known=sum(sum(v) for v in buckets.values());overhead=max(0,elapsed-known)
stats={k:dict(done=len(v),planned=96,mean_generate_seconds=sum(v)/len(v)) for k,v in buckets.items()}
remaining=sum(max(0,96-len(v))*sum(v)/len(v) for v in buckets.values())+overhead/max(1,len(rows))*(384-len(rows))
result=dict(status=json.loads((OUT/'STATUS.json').read_text()),confirmed_returns=len(rows),elapsed_seconds=elapsed,buckets=stats,estimated_remaining_seconds=remaining,estimated_total_seconds=elapsed+remaining,method='Observed role/stage generation means plus amortized observed overhead. Future prefixes/output lengths may differ; not a deadline or statistical interval.')
print(json.dumps(result),flush=True)
