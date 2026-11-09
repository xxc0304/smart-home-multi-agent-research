import importlib.util,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;s=importlib.util.spec_from_file_location('probe',HERE/'probe.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
assert p.freeze()==p.load(HERE/'FREEZE.json')==p.load(HERE/'PREFLIGHT.json')['freeze']
assert p.load(HERE/'PREFLIGHT.json')['result']=='PASS' and 'RUN_ALLOWED' in (HERE/'EXPERIMENT_REVIEW.md').read_text()
assert not (HERE/'LAUNCH.json').exists() and not (p.ROOT/p.load(HERE/'config.json')['run_dir']).exists()
used,util=map(int,subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).split(','));assert used<100 and util<5
with (HERE/'launcher.log').open('xb') as log:c=subprocess.Popen([sys.executable,'-u',str(HERE/'probe.py'),'run'],cwd=p.ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
p.write(HERE/'LAUNCH.json',dict(pid=c.pid,started_unix=time.time()));print(p.load(HERE/'LAUNCH.json'))
