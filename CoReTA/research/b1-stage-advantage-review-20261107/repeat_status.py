import json,os
from repeat import OUT,load
r={'status':load(OUT/'STATUS.json') if (OUT/'STATUS.json').exists() else None}
if (OUT/'PID').exists():
 p=int((OUT/'PID').read_text());r.update(pid=p,process_exists=os.path.exists(f'/proc/{p}'))
if (OUT/'scores.json').exists():
 s=load(OUT/'scores.json');r['scored_tasks']=sum(not z.get('not_started',False) for z in s['rows']);r['complete_scored_tasks']=sum(z.get('complete',False) for z in s['rows'])
if (OUT/'run.log').exists():r['log_tail']=(OUT/'run.log').read_text()[-700:]
print(json.dumps(r,ensure_ascii=False))
