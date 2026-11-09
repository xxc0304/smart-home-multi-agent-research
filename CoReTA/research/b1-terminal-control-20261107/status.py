import json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'runs/b1-terminal-adapter-20261107-v1'
load=lambda p:json.loads(p.read_text())
out={'status':load(OUT/'STATUS.json') if (OUT/'STATUS.json').exists() else None}
if (OUT/'PID').exists():
 p=int((OUT/'PID').read_text());out['pid']=p;out['process_exists']=Path(f'/proc/{p}').exists()
if (OUT/'responses.jsonl').exists():
 rs=[json.loads(x) for x in (OUT/'responses.jsonl').read_text().splitlines()];out['returned']=len(rs)
 out['recent']=[{'id':r['request']['id'],'answer':r['response']['raw_output'],'status':r['response']['status']} for r in rs[-4:]]
if (OUT/'scores.json').exists():
 s=load(OUT/'scores.json');out['scores']={}
 for st in ('original_private_terminal_failure','original_stable_correct_control'):
  out['scores'][st]={route:{'n':len([r for r in s['rows'] if r['stratum']==st and r['adapter']==route]),'em':sum(r['score']['em'] for r in s['rows'] if r['stratum']==st and r['adapter']==route and r['score'] is not None)} for route in ('on','off')}
out['gpu']=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader'],text=True).strip()
if (OUT/'run.log').exists():out['log_tail']=(OUT/'run.log').read_text()[-1200:]
print(json.dumps(out,ensure_ascii=False))
