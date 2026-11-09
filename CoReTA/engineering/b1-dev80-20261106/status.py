"""Compact read-only snapshot for the fixed D80 extension."""
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'runs/b1-dev80-20261106-v1'
load=lambda p:json.loads(p.read_text())
result=dict(controller=load(OUT/'STATUS.json') if (OUT/'STATUS.json').exists() else None,cells=[])
for cell in sorted((OUT/'cells').iterdir()):
    state=load(cell/'STATUS.json');result['cells'].append(dict(start=int(cell.name),**state))
rows=[]
for p in (OUT/'cells').glob('*/responses.jsonl'):
    text=p.read_text();parts=text.splitlines()
    if text and not text.endswith('\n'):parts=parts[:-1]
    rows.extend(json.loads(s) for s in parts)
result.update(new_recorded=len(rows),new_generated_returns=sum(r['generated'] for r in rows),statuses=dict(Counter(r['record']['status'] for r in rows)),unknown=sum(isinstance(r['record']['raw_output'],str) and r['record']['raw_output'].strip().lower()=='unknown' for r in rows),inherited_tasks=8,planned_new_calls=3744)
result['failures']=[dict(index=r['item_index'],request=r['record']['request_id'],actor=r['record']['actor'],stage=r['record']['stage'],arm=r['record']['arm'],status=r['record']['status'],tokens=(r['record'].get('usage') or {}).get('output_tokens')) for r in rows if r['record']['status']!='OK']
print(json.dumps(result,ensure_ascii=False),flush=True)
