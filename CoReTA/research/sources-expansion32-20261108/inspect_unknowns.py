"""Read-only final-name format inspection, without rescoring or alias repair."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
cfg=json.loads((HERE/'config.json').read_text());out=ROOT/cfg['run_dir']
raw=(out/'responses.jsonl').read_text();rows=[json.loads(s) for s in raw[:raw.rfind('\n')+1].splitlines() if s]
result=[]
for n in sorted({r['task_id'] for r in rows if r['stage']=='final' and r['answer'] is None}):
    group=[r for r in rows if r['task_id']==n and r['stage']=='final']
    tasks=json.loads((HERE/'tasks.json').read_text());t=next(t for t in tasks if t['id']==n)
    result.append({'task_id':n,'allowed_choices':list(t['options']),
        'finals_checked':len(group),'unreadable_count':sum(r['answer'] is None for r in group),
        'unique_raw_finals':sorted({r['text'] for r in group})})
(HERE/'UNKNOWN_FINAL_INSPECTION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result))
