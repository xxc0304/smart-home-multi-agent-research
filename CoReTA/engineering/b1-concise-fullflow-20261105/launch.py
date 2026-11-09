"""Launch one separately frozen T3 phase, with no automatic next batch."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('mode',choices=['v','team']);mode=p.parse_args().mode
run=root/('runs/b1-concise-V8-20261105-v1' if mode=='v' else 'runs/b1-concise-tech6-20261105-v1')
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
freeze=load(run/'FREEZE.json');manifest=load(run/'manifest.json')
assert all(sha(p)==h for p,h in freeze['files'].items())
assert manifest['expected_generations']==(16 if mode=='v' else 312) and manifest['primary_enabled'] is False
if mode=='team':assert load(root/'runs/b1-concise-V8-20261105-v1/RESULTS.json')['verdict']=='PASS_TECHNICAL_ONLY'
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert len(gpu.splitlines())==1
used,util=map(int,gpu.split(','));assert used<100 and util<5
(run/'DISPATCHED').touch(exist_ok=False)
(run/'APPROVAL.json').write_text(json.dumps(dict(verdict='RUN_ALLOWED',science='PASS',engineering='PASS',reviewer='assistant',independence='none/provisional',freeze_sha256=sha(run/'FREEZE.json'),launcher_sha256=sha(__file__),gpu_before=gpu),indent=2)+'\n')
with (run/'run.log').open('x') as log:
    proc=subprocess.Popen(['timeout','--signal=TERM',str(manifest['hard_seconds']),sys.executable,str(Path(__file__).with_name('fullflow.py')),'run-'+mode],cwd=root,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(run/'PID').write_text(str(proc.pid)+'\n')
print(json.dumps(dict(mode=mode,pid=proc.pid,manifest=manifest,gpu_before=gpu)))
