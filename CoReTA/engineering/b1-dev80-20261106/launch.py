"""Launch one fixed 72-question extension, without a wall-clock killer."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;OUT=ROOT/'runs/b1-dev80-20261106-v1'
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
f=load(OUT/'FREEZE.json');pre=load(OUT/'PREFLIGHT.json');budget=load(OUT/'BUDGET.json')
assert all(sha(p)==h for p,h in f['files'].items())
assert pre['science']==pre['engineering']=='PASS' and budget['max_new_model_requests']==3744 and budget['wall_clock_cutoff'] is None
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip();used,util=map(int,gpu.split(','));assert used<100 and util<5
(OUT/'DISPATCHED').touch(exist_ok=False)
(OUT/'APPROVAL.json').write_text(json.dumps(dict(verdict='RUN_ALLOWED',science='PASS',engineering='PASS',reviewer='assistant',independence='none/provisional',freeze_sha256=sha(OUT/'FREEZE.json'),gpu_before=gpu,user_requested_no_wall_cutoff=True),indent=2)+'\n')
with (OUT/'controller.log').open('x') as log:
    p=subprocess.Popen([sys.executable,str(HERE/'experiment.py'),'controller'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(OUT/'PID').write_text(str(p.pid)+'\n')
entry=f'''## 2026-11-06 D80开发扩展已启动：新增72题，不设时间硬截止

用户睡眠窗口授权扩大题目覆盖，并明确不需十小时硬截止。见engineering/b1-dev80-20261106/EXPERIMENT_REVIEW.md、runs/b1-dev80-20261106-v1/STATUS.json。固定D80原顺序，继承V6 batch2完整前8原件，新增008–079共72题、3744调用上限；保持四组/两轮、256短答/1024工作、模型/专家/种子和四题分组。无全局/cell/单请求时间截止，EOS/token cap及固定调用数约束；每4题独立进程和持久日志，32/48/64/80前缀汇总。单条截断/长输入/空白隔离依赖，不填Unknown、不重试已尝试请求；协议/路由故障或第二OOM cell停系统，不能为连续运行隐瞒缺失。仅开发，保留不完整和总分母，未改标签/投票/训练、未新C-H/API。助手自审none/provisional，启动不等于完成，PID {p.pid}。

'''
(OUT/'START_STAGE_ENTRY.md').write_text(entry)
for name in ('handoff.md','CURRENT_STATE.md','brainstorm.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md'):
    dest=ROOT/name;prior=dest.read_text()
    if entry.splitlines()[0] not in prior:dest.write_text(entry+prior)
print(json.dumps(dict(status='DISPATCHED',pid=p.pid,new_questions=72,max_new_calls=3744,wall_cutoff=None)),flush=True)
