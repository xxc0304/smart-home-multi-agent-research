"""Start one detached run on Linux; no time-based termination or restart."""
import importlib.util, subprocess, sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('same_sources',HERE/'experiment.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
assert e.frozen()==e.load(HERE/'FREEZE.json')==e.load(HERE/'PREFLIGHT.json')['freeze']
assert e.load(HERE/'PREFLIGHT.json')['result']=='PASS'
assert 'RUN_ALLOWED' in (HERE/'EXPERIMENT_REVIEW.md').read_text()
cfg=e.load(HERE/'config.json');assert not (e.ROOT/cfg['run_dir']).exists()
assert not (HERE/'LAUNCH.json').exists(),'already_launched_no_automatic_restart'
with (HERE/'launcher.log').open('xb') as log:
    child=subprocess.Popen([sys.executable,'-u',str(HERE/'experiment.py'),'run'],cwd=e.ROOT,
          stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
e.write(HERE/'LAUNCH.json',{'pid':child.pid,'started_unix':time.time(),'run_dir':cfg['run_dir']})
print(e.load(HERE/'LAUNCH.json'))
