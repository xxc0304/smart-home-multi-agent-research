"""Read-only compact status, without importing or loading a model."""
import json
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'runs/b1-fixed-prefix-20261106-v1'
def rows(name):
    p=OUT/name
    if not p.exists():return []
    raw=p.read_text();parts=raw.splitlines()
    if raw and not raw.endswith('\n'):parts=parts[:-1]
    return [json.loads(s) for s in parts]
state=json.loads((OUT/'STATUS.json').read_text());attempts=rows('ATTEMPTS.jsonl');responses=rows('responses.jsonl')
confirmed={r['request']['request_id'] for r in responses}
print(json.dumps(dict(state=state,attempts=len(attempts),confirmed_returns=len(responses),unconfirmed_attempts=[r['request']['request_id'] for r in attempts if r['request']['request_id'] not in confirmed],response_statuses=dict(Counter(r['response']['status'] for r in responses)),route_records_valid=all(r['response']['usage']['adapter_enabled']==(r['request']['actor']=='M1') and r['response']['usage']['batch_size']==1 for r in responses),output_tokens=sum(r['response']['usage'].get('output_tokens',0) for r in responses))),flush=True)
