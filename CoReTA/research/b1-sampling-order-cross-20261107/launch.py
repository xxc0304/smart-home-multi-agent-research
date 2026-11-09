"""Start the frozen finite cross, detached from notebook/SSH."""
import subprocess,sys
from experiment import OUT,HERE,ROOT,load,sha,verify_freeze,atomic,MAX_CALLS
verify_freeze();p=load(OUT/'PREFLIGHT.json');b=load(OUT/'BUDGET.json')
assert p['science']==p['engineering']=='PASS' and b['max_calls']==MAX_CALLS and b['wall_clock_cutoff'] is None
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip();used,util=map(int,gpu.split(','));assert used<100 and util<5
(OUT/'DISPATCHED').touch(exist_ok=False)
atomic(OUT/'APPROVAL.json',dict(verdict='RUN_ALLOWED',science='PASS',engineering='PASS',freeze_sha256=sha(OUT/'FREEZE.json'),reviewer='assistant',independence='none/provisional',gpu_before=gpu))
with (OUT/'run.log').open('x') as log:child=subprocess.Popen([sys.executable,str(HERE/'experiment.py'),'run'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(OUT/'PID').write_text(str(child.pid)+'\n');print(dict(status='DISPATCHED_NOT_COMPLETE',pid=child.pid,max_calls=MAX_CALLS,expected_complete_physical_calls=1133,no_wall_cutoff=True),flush=True)
