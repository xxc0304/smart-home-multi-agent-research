"""Record actual running state, never claim completion before results."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
status=json.loads((ROOT/'runs/b1-dev32-20261104-v2/JOB_STATUS.json').read_text())
assert status['status'] in ('RUNNING_STAGE8','RUNNING_STAGE32')
entry=f'''## 2026-11-04 B1累计32题已启动（运行中）

用户明确要求多于8题，已冻结2→8→32首遍：最多新增1560次生成，含旧2题累计1664次。实际启动{status['updated_at']}，监督进程{status['pid']}；当前状态见runs/b1-dev32-20261104-v2/JOB_STATUS.json。先新增6题到8，完整性/字节继承/路由审核通过后才新增24到32，不按得分推进。v2提示/采样/种子/模型/适配器不变，旧题不重跑。阶段wall上限1h+3h，硬保护稍留清理余量；估计新增约2.5h，非保证。全32输入/完整历史压力检查通过，最大4072/9596token（上限16384）；仅输入/关系元数据预检，未提前评分新D标签。无训练/重跑C/读H/重试。此条仅实际启动记录，不宣称8或32已完成。计划及审核见engineering/b1-dev32-20261104/；结束或失败由执行器写结果并更新交接。

'''
for p in (ROOT/'handoff.md',ROOT/'CURRENT_STATE.md',ROOT/'refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md',ROOT/'refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md'):
    old=p.read_text(encoding='utf-8') if p.exists() else ''
    marker='## 2026-11-04 B1累计32题已启动（运行中）'
    if marker not in old:p.write_text(entry+old,encoding='utf-8')
print('ACTUAL_START_RECORDED',status['status'])
