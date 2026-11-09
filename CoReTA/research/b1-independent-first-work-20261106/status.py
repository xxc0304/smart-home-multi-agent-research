"""Read-only compact progress; no inference, scoring or resume."""
import json,subprocess
from collections import Counter
from experiment import OUT,load
s=load(OUT/'STATUS.json');p=OUT/'responses.jsonl'
rows=[json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []
attempts=sum(1 for _ in (OUT/'ATTEMPTS.jsonl').open()) if (OUT/'ATTEMPTS.jsonl').exists() else 0
pid=int((OUT/'PID').read_text());live=subprocess.run(['kill','-0',str(pid)],capture_output=True).returncode==0
items=[load(p) for p in (OUT/'trials').glob('*.json')] if (OUT/'trials').exists() else []
report=dict(status=s,pid=pid,process_alive=live,attempts=attempts,confirmed_returns=len(rows),completed_task_seed_units_actual=sum(x['status'] in ('COMPLETE','INCOMPLETE_BRANCHES','SHARED_INITIAL_FAILED') for x in items),fully_complete_task_seed_units_actual=sum(x['status']=='COMPLETE' for x in items),statuses=dict(Counter(x['response']['status'] for x in rows)),output_tokens=sum(x['response']['usage'].get('output_tokens',0) for x in rows),last_returns=[dict(id=x['request']['request_id'],actor=x['request']['actor'],stage=x['request']['stage'],status=x['response']['status'],tokens=x['response']['usage']['output_tokens'],adapter=x['response']['usage'].get('adapter_enabled'),disabled_layers=x['response']['usage'].get('disabled_layers'),batch_size=x['response']['usage'].get('batch_size')) for x in rows[-5:]])
print(json.dumps(report,ensure_ascii=False),flush=True)
