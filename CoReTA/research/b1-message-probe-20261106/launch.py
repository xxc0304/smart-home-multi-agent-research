"""Launch the reviewed finite message probe without a wall-clock killer."""
import json,subprocess,sys
from pathlib import Path
from probe import OUT,HERE,sha,load,verify_freeze,atomic
verify_freeze();p=load(OUT/'PREFLIGHT.json');b=load(OUT/'BUDGET.json')
assert p['science']==p['engineering']=='PASS' and b['max_calls']==384 and b['wall_clock_cutoff'] is None
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip();used,util=map(int,gpu.split(','));assert used<100 and util<5
(OUT/'DISPATCHED').touch(exist_ok=False)
atomic(OUT/'APPROVAL.json',dict(verdict='RUN_ALLOWED',science='PASS',engineering='PASS',freeze_sha256=sha(OUT/'FREEZE.json'),reviewer='assistant',independence='none/provisional',gpu_before=gpu))
with (OUT/'run.log').open('x') as log:
    child=subprocess.Popen([sys.executable,str(HERE/'probe.py'),'run'],cwd=HERE.parents[1],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(OUT/'PID').write_text(str(child.pid)+'\n')
print(json.dumps(dict(status='DISPATCHED_NOT_COMPLETE',pid=child.pid,max_calls=384,no_wall_cutoff=True)),flush=True)
