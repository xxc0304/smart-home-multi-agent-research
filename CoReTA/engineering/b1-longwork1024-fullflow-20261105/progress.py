"""Read-only live snapshot. No model calls or score mutation."""
import collections,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'runs/b1-longwork1024-fullflow-20261105-v1'
result={'status':json.loads((OUT/'STATUS.json').read_text()),'engines':{}}
for engine in ('serial','batch2'):
    d=OUT/engine
    if not d.exists():continue
    # A trailing line being appended is excluded from this live snapshot.
    text=(d/'responses.jsonl').read_text()
    lines=text.splitlines()
    if text and not text.endswith('\n'):lines=lines[:-1]
    rows=[json.loads(line) for line in lines]
    records=[r['record'] for r in rows]
    trials=[json.loads(p.read_text()) for p in (d/'trials').glob('*.json')]
    failures=[dict(request_id=r['request_id'],stage=r['stage'],status=r['status'],output_tokens=(r.get('usage') or {}).get('output_tokens')) for r in records if r['status']!='OK']
    result['engines'][engine]=dict(returned=len(rows),complete=sum(t['complete'] for t in trials),statuses=dict(collections.Counter(r['status'] for r in records)),unknown=sum(isinstance(r['raw_output'],str) and r['raw_output'].strip().lower()=='unknown' for r in records),failures=failures)
if (OUT/'RESULTS.json').exists():result['final_results']=json.loads((OUT/'RESULTS.json').read_text())
print(json.dumps(result,ensure_ascii=False))
