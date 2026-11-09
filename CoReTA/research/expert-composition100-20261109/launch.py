import importlib.util,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('batch',HERE/'experiment.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
assert b.freeze()==b.load(HERE/'FREEZE.json')==b.load(HERE/'PREFLIGHT.json')['freeze']
assert b.load(HERE/'PREFLIGHT.json')['result']=='PASS' and 'RUN_ALLOWED' in (HERE/'EXPERIMENT_REVIEW.md').read_text()
assert not (HERE/'LAUNCH.json').exists() and not (b.ROOT/b.load(HERE/'config.json')['run_dir']).exists()
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip();used,util=map(int,gpu.split(','));assert used<100 and util<5
with (HERE/'launcher.log').open('xb') as f:
 p=subprocess.Popen([sys.executable,'-u',str(HERE/'experiment.py'),'run'],cwd=b.ROOT,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
b.write(HERE/'LAUNCH.json',dict(pid=p.pid,started_unix=time.time()));print(b.load(HERE/'LAUNCH.json'))
