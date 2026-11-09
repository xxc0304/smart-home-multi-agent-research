"""Verify archived old sources, then atomically install backward-compatible V6."""
import hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=('b1_output_contract.py','b1_controls.py','b1_runtime.py')
expected=json.loads((HERE/'PRIOR_SOURCE_HASHES.json').read_text())
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
used,util=map(int,gpu.split(','));assert used<100 and util<5,'GPU_busy_no_core_deployment'
for n in names:assert sha(HERE/'prior'/n)==sha(ROOT/'tools'/n)==expected[n],'prior_source_mismatch:'+n
for n in names:
    target=ROOT/'tools'/n;temp=target.with_suffix('.v6.tmp')
    temp.write_bytes((HERE/'candidate'/n).read_bytes());os.replace(temp,target)
    assert sha(target)==sha(HERE/'candidate'/n)
(HERE/'DEPLOYED.json').write_text(json.dumps(dict(prior_verified=True,gpu_before=gpu,files={n:sha(ROOT/'tools'/n) for n in names}),indent=2)+'\n')
print('V6 sources installed; prior byte snapshots verified; no model generation.')
