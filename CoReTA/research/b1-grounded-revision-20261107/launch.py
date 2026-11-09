import subprocess,sys
from experiment import OUT,HERE,ROOT,load,sha,atomic,verify_freeze
verify_freeze();p=load(OUT/'PREFLIGHT.json');assert p['science']==p['engineering']=='PASS'
assert load(OUT/'BUDGET.json')['wall_clock_cutoff'] is None and load(HERE/'TESTS.json')['verdict']=='PASS'
assert 'ENGINEERING_PASS' in (HERE/'READY_REVIEW.md').read_text()
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip();used,util=map(int,gpu.split(','));assert used<100 and util<5
(OUT/'DISPATCHED').touch(exist_ok=False)
atomic(OUT/'APPROVAL.json',dict(verdict='RUN_ALLOWED',science='PASS',engineering='PASS',freeze_sha256=sha(OUT/'FREEZE.json'),gpu_before=gpu,ready_review_sha256=sha(HERE/'READY_REVIEW.md'),reviewer='assistant',independence='none/provisional'))
with (OUT/'run.log').open('x') as f:child=subprocess.Popen([sys.executable,str(HERE/'experiment.py'),'run'],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
(OUT/'PID').write_text(str(child.pid)+'\n');print(dict(status='DISPATCHED_NOT_COMPLETE',pid=child.pid,no_wall_cutoff=True),flush=True)
