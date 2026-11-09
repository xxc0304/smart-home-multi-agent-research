import hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2];run=root/'runs/b1-batch-speed-20261105-v1'
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
f=load(run/'FREEZE.json');assert all(sha(p)==h for p,h in f['files'].items())
pre=load(run/'PREFLIGHT.json');assert pre['science']==pre['engineering']=='PASS' and pre['n_requests']==16
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
used,util=map(int,gpu.split(','));assert used<100 and util<5
(run/'DISPATCHED').touch(exist_ok=False)
(run/'APPROVAL.json').write_text(json.dumps(dict(verdict='RUN_ALLOWED',science='PASS',engineering='PASS',reviewer='assistant',independence='none/provisional',freeze_sha256=sha(run/'FREEZE.json'),gpu_before=gpu),indent=2)+'\n')
with (run/'run.log').open('x') as log:
    p=subprocess.Popen(['timeout','--signal=TERM','1200',sys.executable,str(Path(__file__).with_name('speed.py')),'run'],cwd=root,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(run/'PID').write_text(str(p.pid)+'\n');print(json.dumps(dict(pid=p.pid,scope='16 calls max; finite batch probe')))
