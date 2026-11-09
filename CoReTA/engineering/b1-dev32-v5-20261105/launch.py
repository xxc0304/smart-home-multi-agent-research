"""Dispatch the complete, bounded staged job; no repeated user intervention."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'runs/b1-dev32-20261105-v5'
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
f=load(OUT/'FREEZE.json');pre=load(OUT/'PREFLIGHT.json')
assert all(sha(p)==h for p,h in f['files'].items())
assert pre['science']==pre['engineering']=='PASS' and pre['expected_new_generations']==1664
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
used,util=map(int,gpu.split(','));assert used<100 and util<5
(OUT/'DISPATCHED').touch(exist_ok=False)
(OUT/'APPROVAL.json').write_text(json.dumps(dict(verdict='RUN_ALLOWED',science='PASS',engineering='PASS',reviewer='assistant',independence='none/provisional',freeze_sha256=sha(OUT/'FREEZE.json'),gpu_before=gpu),indent=2)+'\n')
with (OUT/'supervisor.log').open('x') as log:
    p=subprocess.Popen(['timeout','--signal=TERM','--kill-after=30','8400',sys.executable,str(Path(__file__).with_name('pipeline.py')),'supervise'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(OUT/'PID').write_text(str(p.pid)+'\n')
entry=f'''## 2026-11-05 同合同完整D32已启动（2→8→32）

用户本轮授权先一次加速测试后完整32题。T4 16/16完成，小样本时间比约1.27，但1/4载荷跨执行文本/token改变，故按冻结门槛采用既有串行V5。runs/b1-dev32-20261105-v5由监督器自动2→8→32、当批复核、评分和保存；最多新增1664请求，总硬8400s（强杀宽限30s），阶段不完整即停后续，无重试/改cap。原C已完成资格复用，无新C/H/训练/付费API；旧28和技术6不拼接，本批仍开发诊断。实际进度看STATUS.json与phase*/run.log，结束看PIPELINE_RESULT.json、stage32/scores.json。PID {p.pid}。助手自审none/provisional；已启动不等于完成。

'''
(OUT/'START_STAGE_ENTRY.md').write_text(entry)
for name in ('handoff.md','CURRENT_STATE.md','brainstorm.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md'):
    dest=ROOT/name;dest.write_text(entry+dest.read_text())
print(json.dumps(dict(pid=p.pid,status='DISPATCHED_NOT_COMPLETE',output=str(OUT),new_generations_max=1664,hard_seconds=8400)))
