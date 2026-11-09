"""Read progress only; inherited cells are not counted as new work."""
import json,subprocess
from collections import Counter
from experiment import OUT,load
s=load(OUT/'STATUS.json');p=OUT/'responses.jsonl';raw=p.read_text() if p.exists() else ''
rows=[json.loads(x) for x in raw.split('\n')[:-1] if x]
attempts=sum(1 for _ in (OUT/'ATTEMPTS.jsonl').open()) if (OUT/'ATTEMPTS.jsonl').exists() else 0
trials=[load(p) for p in (OUT/'trials').glob('*.json')] if (OUT/'trials').exists() else []
complete=[t for t in trials if t['status']=='COMPLETE'];finished=[t for t in trials if t['status'] in ('COMPLETE','INCOMPLETE_BRANCHES')]
counts=Counter(t['index'] for t in complete)
pid=int((OUT/'PID').read_text());live=subprocess.run(['kill','-0',str(pid)],capture_output=True).returncode==0
result=dict(status=s,pid=pid,process_alive=live,new_attempts=attempts,new_confirmed_returns=len(rows),complete_new_crossed_cells=len(complete),finished_new_crossed_cells=len(finished),fully_complete_questions=sum(v==2 for v in counts.values()),planned_new_crossed_cells=50,expected_new_complete_physical_calls=1133,statuses=dict(Counter(x['response']['status'] for x in rows)),output_tokens=sum(x['response']['usage'].get('output_tokens',0) for x in rows),inflight_partial_tail=bool(raw and not raw.endswith('\n')),last_returns=[dict(id=x['request']['request_id'],actor=x['request']['actor'],stage=x['request']['stage'],status=x['response']['status'],tokens=x['response']['usage'].get('output_tokens'),adapter=x['response']['usage'].get('adapter_enabled'),disabled_layers=x['response']['usage'].get('disabled_layers'),batch_size=x['response']['usage'].get('batch_size')) for x in rows[-5:]])
print(json.dumps(result),flush=True)
