"""Launch this reviewed finite diagnostic independently of client connection."""
import json,subprocess,sys
from runner import ROOT,HERE,OUT,load,sha,atomic,verify_freeze
verify_freeze();p=load(OUT/'PREFLIGHT.json');assert p['science']==p['engineering']=='PASS'
ready=load(HERE/'READY_REVIEW.json');assert ready['verdict']=='RUN_ALLOWED' and ready['freeze_sha256']==sha(OUT/'FREEZE.json')
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip();used,util=map(int,gpu.split(','));assert used<100 and util<5
(OUT/'DISPATCHED').touch(exist_ok=False)
atomic(OUT/'APPROVAL.json',dict(verdict='RUN_ALLOWED',freeze_sha256=sha(OUT/'FREEZE.json'),science='PASS',engineering='PASS',gpu_before=gpu,reviewer='assistant',independence='none/provisional'))
with (OUT/'run.log').open('x') as log:
    child=subprocess.Popen([sys.executable,str(HERE/'runner.py'),'run'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(OUT/'PID').write_text(str(child.pid)+'\n')
print(json.dumps(dict(pid=child.pid,status='DISPATCHED_NOT_COMPLETE',max_calls=48)),flush=True)
