"""Dispatch exactly one bounded full-history technical comparison."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'runs/b1-batch4-fullflow-20261105-v1'
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
f=load(OUT/'FREEZE.json');pre=load(OUT/'PREFLIGHT.json')
assert all(sha(p)==h for p,h in f['files'].items())
assert pre['science']==pre['engineering']=='PASS' and pre['max_new_generations']==832
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip();used,util=map(int,gpu.split(','))
assert used<100 and util<5
(OUT/'DISPATCHED').touch(exist_ok=False)
(OUT/'APPROVAL.json').write_text(json.dumps(dict(verdict='RUN_ALLOWED',science='PASS',engineering='PASS',reviewer='assistant',independence='none/provisional',freeze_sha256=sha(OUT/'FREEZE.json'),gpu_before=gpu),indent=2)+'\n')
with (OUT/'run.log').open('x') as log:
    p=subprocess.Popen(['timeout','--signal=TERM','--kill-after=30','6600',sys.executable,str(Path(__file__).with_name('experiment.py')),'run'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(OUT/'PID').write_text(str(p.pid)+'\n')
entry=f"## 2026-11-05 batch4完整协作D8对照已启动\n\n见engineering/b1-batch4-fullflow-20261105/EXPERIMENT_REVIEW.md、runs/b1-batch4-fullflow-20261105-v1/STATUS.json。固定D前8题，serial/batch4各完整8×52，共832调用上限；两组4题交替执行顺序，原v2较长分析/256短答512工作不变，无新增Unknown或弃权规则。题内依赖/即时广播与四组保留，仅同路由跨题1/2/4合批。软6000/硬6600秒+30s宽限，无重试/改cap/自动扩32。助手自审none/provisional，技术验证非独立质量等价；PID {p.pid}，启动不等于完成。\n\n"
(OUT/'START_STAGE_ENTRY.md').write_text(entry)
for name in ('handoff.md','CURRENT_STATE.md','brainstorm.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md'):
    dest=ROOT/name;dest.write_text(entry+dest.read_text())
print(json.dumps(dict(status='DISPATCHED_NOT_COMPLETE',pid=p.pid,max_new_calls=832,hard_seconds=6600)))
