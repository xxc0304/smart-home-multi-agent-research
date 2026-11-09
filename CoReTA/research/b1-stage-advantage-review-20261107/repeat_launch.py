import subprocess,sys
from repeat import OUT,HERE,ROOT,load,sha,atomic,verify_freeze
verify_freeze();ready=load(HERE/'REPEAT_READY.json');assert ready['verdict']=='RUN_ALLOWED' and ready['freeze_sha256']==sha(OUT/'FREEZE.json')
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip();used,util=map(int,gpu.split(','));assert used<100 and util<5
(OUT/'DISPATCHED').touch(exist_ok=False)
atomic(OUT/'APPROVAL.json',ready)
with (OUT/'run.log').open('x') as log:p=subprocess.Popen([sys.executable,str(HERE/'repeat.py'),'run'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(OUT/'PID').write_text(str(p.pid));print(p.pid,flush=True)
