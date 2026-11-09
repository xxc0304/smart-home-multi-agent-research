import importlib.util, subprocess, sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('batch',HERE/'experiment.py');e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
assert e.freeze()==e.load(HERE/'FREEZE.json')==e.load(HERE/'PREFLIGHT.json')['freeze']
assert e.load(HERE/'PREFLIGHT.json')['result']=='PASS'
assert 'RUN_ALLOWED' in (HERE/'EXPERIMENT_REVIEW.md').read_text()
assert not (HERE/'LAUNCH.json').exists() and not (e.ROOT/e.load(HERE/'config.json')['run_dir']).exists()
with (HERE/'launcher.log').open('xb') as log:
    child=subprocess.Popen([sys.executable,'-u',str(HERE/'experiment.py'),'run'],cwd=e.ROOT,
         stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
e.write(HERE/'LAUNCH.json',{'pid':child.pid,'started_unix':time.time()});print(e.load(HERE/'LAUNCH.json'))
