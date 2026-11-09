"""Record explicit user cancellation without overwriting the raw executor status."""
import datetime,json,subprocess
from experiment import HERE,ROOT,load,write,sha
c=load(HERE/'config.json');out=ROOT/c['run_dir'];pid=load(HERE/'LAUNCH.json')['pid']
check=subprocess.run(['ps','-p',str(pid),'-o','args='],capture_output=True,text=True)
assert check.returncode!=0 and not check.stdout.strip(),'process_still_present'
status=load(out/'STATUS.json');assert status['failure']['type']=='KeyboardInterrupt'
rows=[json.loads(x) for x in (out/'responses.jsonl').read_text().splitlines()]
attempts=[json.loads(x) for x in (out/'attempts.jsonl').read_text().splitlines()]
trials=[load(p) for p in sorted((out/'trials').glob('*.json'))]
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader'],text=True).strip()
result=dict(status='CANCELLED_BY_USER',client_date='2026-11-09',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reason='Explicit user request: stop this batch and preserve existing records; experiment priority reconsidered before viewing quality outcomes.',pid=pid,process_exited=True,raw_executor_status_preserved=status['status'],raw_exception=status['failure']['type'],complete_units=status['complete_units'],planned_units=status['total_units'],trial_snapshots=len(trials),responses=len(rows),new_returned_calls=sum(not r['reused'] for r in rows),reused_returned_calls=sum(r['reused'] for r in rows),attempts=len(attempts),inflight_attempts_without_response=len(attempts)-len(rows),complete_arm_snapshots=sum(len(t['finals'][a])==4 and a not in t['failed'] for t in trials for a in ['A','B']),gpu_snapshot=gpu,raw_sha256={n:sha(out/n) for n in ['responses.jsonl','attempts.jsonl','scores.json','manifest.json','STATUS.json']},automatic_resume=False,scope='STOPPED_DEVELOPMENT_PREFIX_NOT_COMPLETED_EXPERIMENT')
write(out/'CANCELLATION.json',result);write(HERE/'CANCELLATION.json',result);print(json.dumps(result),flush=True)
