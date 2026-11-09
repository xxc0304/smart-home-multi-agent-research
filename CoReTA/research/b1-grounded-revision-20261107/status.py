import json,subprocess
from collections import Counter
from experiment import OUT,load
s=load(OUT/'STATUS.json');raw=(OUT/'responses.jsonl').read_text() if (OUT/'responses.jsonl').exists() else '';rows=[json.loads(z) for z in raw.split('\n')[:-1] if z]
pid=int((OUT/'PID').read_text());live=subprocess.run(['kill','-0',str(pid)],capture_output=True).returncode==0
ts=[load(p) for p in (OUT/'trials').glob('*.json')];print(json.dumps(dict(status=s,pid=pid,process_alive=live,returns=len(rows),statuses=dict(Counter(r['response']['status'] for r in rows)),complete_questions=sum(t['status']=='COMPLETE' for t in ts),finished_questions=sum(t['status'] in ('COMPLETE','INCOMPLETE_BRANCHES','SHARED_INITIAL_FAILED') for t in ts),complete_by_cohort=dict(Counter(t['cohort'] for t in ts if t['status']=='COMPLETE')),expected_physical=load(OUT/'BUDGET.json')['expected_complete_physical_calls'],partial_tail=bool(raw and not raw.endswith('\n')),output_tokens=sum(r['response']['usage'].get('output_tokens',0) for r in rows))),flush=True)
