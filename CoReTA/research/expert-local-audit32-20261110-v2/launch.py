import subprocess,sys,time
from experiment import HERE,ROOT,freeze,load,write
assert freeze()==load(HERE/'FREEZE.json')==load(HERE/'PREFLIGHT.json')['freeze']
assert load(HERE/'PREFLIGHT.json')['result']=='PASS' and 'RUN_ALLOWED' in (HERE/'EXPERIMENT_REVIEW.md').read_text()
assert not (HERE/'LAUNCH.json').exists() and not (ROOT/load(HERE/'config.json')['run_dir']).exists()
used,util=map(int,subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).split(','))
assert used<100 and util<5
with (HERE/'launcher.log').open('xb') as log:
 p=subprocess.Popen([sys.executable,'-u',str(HERE/'experiment.py'),'run'],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
write(HERE/'LAUNCH.json',{'pid':p.pid,'started_unix':time.time()});print(load(HERE/'LAUNCH.json'))
