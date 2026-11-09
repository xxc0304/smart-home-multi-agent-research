"""One bounded detached technical comparison; duplicate dispatch refused."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'runs/b1-parallel-fullflow-20261105-v1'
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
f=load(OUT/'FREEZE.json');pre=load(OUT/'PREFLIGHT.json')
assert all(sha(p)==h for p,h in f['files'].items())
assert pre['science']==pre['engineering']=='PASS' and pre['new_generations_max']==208
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
used,util=map(int,gpu.split(','));assert used<100 and util<5
(OUT/'DISPATCHED').touch(exist_ok=False)
write=lambda p,x:p.write_text(json.dumps(x,indent=2)+'\n')
write(OUT/'APPROVAL.json',dict(verdict='RUN_ALLOWED',science='PASS',engineering='PASS',reviewer='assistant',independence='none/provisional',freeze_sha256=sha(OUT/'FREEZE.json'),gpu_before=gpu))
with (OUT/'run.log').open('x') as log:
    p=subprocess.Popen(['timeout','--signal=TERM','--kill-after=30','2700',sys.executable,str(Path(__file__).with_name('probe.py')),'run'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(OUT/'PID').write_text(str(p.pid)+'\n')
entry=f"## 2026-11-05 跨题并行完整流程技术对照已启动\n\n见engineering/b1-parallel-fullflow-20261105/EXPERIMENT_REVIEW.md，runs/b1-parallel-fullflow-20261105-v1/STATUS.json。原v2较长分析/256短答512工作，无新Unknown指令；固定D前2题，各完整batch2/serial四组104调用，共208上限。每题内部顺序广播不变，四组同跨题批形状；软2500/硬2700秒+30s宽限，无重试或自动扩样。原16小探针改变输出，故本次仅诊断、不自动正式采用。PID {p.pid}，助手自审none/provisional，启动不等于完成。\n\n"
(OUT/'START_STAGE_ENTRY.md').write_text(entry)
for name in ('handoff.md','CURRENT_STATE.md','brainstorm.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md'):
    dest=ROOT/name;dest.write_text(entry+dest.read_text())
print(json.dumps(dict(pid=p.pid,status='DISPATCHED_NOT_COMPLETE',new_generations_max=208,hard_seconds=2700)))
