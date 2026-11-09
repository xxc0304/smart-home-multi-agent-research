"""Read-only progress and timing breakdown; no GPU/model initialization."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
run=ROOT/'runs/b1-concise-readable-tech6-20261105-v1'
rows=[];partial=0
for line in (run/'responses.jsonl').read_text().splitlines():
    try:rows.append(json.loads(line))
    except json.JSONDecodeError:partial+=1
stages={}
for stage in ('initial','work','final'):
    rs=[r for r in rows if r['stage']==stage];u=[r['usage'] for r in rs]
    seconds=sum(v['elapsed_seconds'] for v in u);tokens=sum(v['output_tokens'] for v in u)
    stages[stage]=dict(n=len(rs),generate_seconds=seconds,output_tokens=tokens,aggregate_output_tokens_per_generate_second=tokens/seconds if seconds else None,mean_input_tokens=sum(v['input_tokens'] for v in u)/len(u) if u else None)
tasks={r['task_index']:sum(x['task_index']==r['task_index'] for x in rows) for r in rows}
result=dict(n_requests=len(rows),n_complete_52_request_tasks=sum(n==52 for n in tasks.values()),task_request_counts=tasks,format_warnings=sum(bool((r.get('usage') or {}).get('format_warning')) for r in rows),technical_non_ok=sum(r['status']!='OK' for r in rows),partial_lines_skipped=partial,stages=stages,results=json.loads((run/'RESULTS.json').read_text()) if (run/'RESULTS.json').exists() else None)
if '--final' in sys.argv:
    assert result['results'] is not None and not partial
    (HERE/'TIMING.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
