"""Dispatch a single bounded 72-response diagnostic."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'runs/b1-length-diagnostic-20261105-v1'
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
f=load(OUT/'FREEZE.json');pre=load(OUT/'PREFLIGHT.json')
assert all(sha(p)==h for p,h in f['files'].items()) and pre['science']==pre['engineering']=='PASS' and pre['max_new_generations']==72
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip();used,util=map(int,gpu.split(','));assert used<100 and util<5
(OUT/'DISPATCHED').touch(exist_ok=False)
(OUT/'APPROVAL.json').write_text(json.dumps(dict(verdict='RUN_ALLOWED',science='PASS',engineering='PASS',reviewer='assistant',independence='none/provisional',freeze_sha256=sha(OUT/'FREEZE.json'),gpu_before=gpu),indent=2)+'\n')
with (OUT/'run.log').open('x') as log:
    p=subprocess.Popen(['timeout','--signal=TERM','--kill-after=30','2100',sys.executable,str(Path(__file__).with_name('diagnostic.py')),'run'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(OUT/'PID').write_text(str(p.pid)+'\n')
entry=f"## 2026-11-05 三条截断请求的长度/执行形状诊断已启动\n\n见engineering/b1-length-diagnostic-20261105/EXPERIMENT_REVIEW.md、runs/b1-length-diagnostic-20261105-v1/STATUS.json。原3失败请求及各自同批9条共12固定真实载荷，保持提示/seed/模型，512/1024×serial/batch2/batch4，共72上限。仅显式诊断cap覆盖，不改原B1合同/停止分数。软1800/硬2100秒+30s宽限，token触顶记录继续独立请求、异常停止，无重试/新cap搜索/自动重跑8或32/训练/C-H。PID {p.pid}，助手自审none/provisional，启动不等于完成。\n\n"
(OUT/'START_STAGE_ENTRY.md').write_text(entry)
for name in ('handoff.md','CURRENT_STATE.md','brainstorm.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md'):
    dest=ROOT/name;dest.write_text(entry+dest.read_text())
print(json.dumps(dict(pid=p.pid,status='DISPATCHED_NOT_COMPLETE',max_new_responses=72,hard_seconds=2100)))
