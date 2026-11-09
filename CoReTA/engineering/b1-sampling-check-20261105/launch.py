"""Dispatch the reviewed, frozen 24-call probe with a hard process timeout."""
import hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
run=root/'runs/b1-sampling-check-20261105-v2'
load=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
pre=load(run/'PREFLIGHT.json');freeze=load(run/'FREEZE.json')
assert pre['science']==pre['engineering']=='PASS'
assert pre['requests']==24 and 20<pre['max_input_tokens']<16128
assert all(sha(p)==h for p,h in freeze['files'].items())
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert len(gpu.splitlines())==1
used,util=map(int,gpu.split(','));assert used<100 and util<5,(used,util)
approval=dict(verdict='RUN_ALLOWED',science='PASS',engineering='PASS',reviewer='assistant',independence='none/provisional',freeze_sha256=sha(run/'FREEZE.json'),launcher_sha256=sha(__file__),gpu_before=gpu,scope='24 fixed V sampling diagnostics only; no C/H/training')
(run/'DISPATCHED').touch(exist_ok=False)
(run/'APPROVAL.json').write_text(json.dumps(approval,indent=2)+'\n')
with (run/'run.log').open('x') as log:
    p=subprocess.Popen(['timeout','--signal=TERM','900',sys.executable,str(Path(__file__).with_name('sampling_check.py')),'run'],cwd=root,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(run/'PID').write_text(str(p.pid)+'\n')
print(json.dumps(dict(pid=p.pid,gpu_before=gpu,preflight=pre,approval=approval)))
