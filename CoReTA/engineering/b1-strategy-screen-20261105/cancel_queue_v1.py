"""Cancel only our not-yet-dispatched queue helper, preserving its artifacts."""
import json,os,signal
from pathlib import Path
root=Path(__file__).resolve().parents[2];run=root/'runs/b1-strategy-screen-20261105-v1'
assert not (run/'DISPATCHED').exists() and not (run/'LAUNCHED').exists()
assert json.loads((run/'STATUS.json').read_text())['status']=='WAITING_FOR_PRIOR'
pid=json.loads((run/'QUEUE_PROCESS.json').read_text())['pid']
argv=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
assert str(Path(__file__).with_name('launch.py')).encode() in argv and b'wait' in argv
os.kill(pid,signal.SIGTERM)
(run/'STATUS.json').write_text(json.dumps(dict(status='SUPERSEDED_BEFORE_GPU',n_generated=0,reason='Fix zero-response interruption export before any model call; frozen v1 sources preserved',next_run='b1-strategy-screen-20261105-v2'),indent=2)+'\n')
print(json.dumps(dict(cancelled_queue_pid=pid,n_generated=0)))
