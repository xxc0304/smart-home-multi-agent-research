"""Record the completed finite diagnostic while preserving existing history."""
from pathlib import Path
import json

root=Path(__file__).resolve().parents[2]
out=root/'runs/baseline-health-v20-20261103-v1'
result=json.loads((out/'RESULTS.json').read_text())
status=json.loads((out/'PIPELINE_STATUS.json').read_text())
assert result['status']=='COMPLETE_DIAGNOSTIC' and status['exit_code']==0
assert result['conditions']['NF4']['n_valid']==result['conditions']['BF16']['n_valid']==20
entry='''## 2026-11-03 V20底座量化健康诊断完成

见[结果与阶段审核](engineering/baseline-health-20261103/RESULTS.md)。固定V前20题，两组各20/20完整，NF4 EM3/20、BF16 2/20；NF4原始回答与历史20/20相同。共同正确2、仅NF4对1、仅BF16对0、共同错17；40次生成/37.29秒，0截断/技术错误/OOM，GPU已空闲。助手阶段自审PASS限该小批精度敏感性诊断：未见BF16修复低分，不证明量化无影响或BF16普遍更差。不换模型/重跑C；C原资格及边界保留，H未读，团队未启动。下一步匹配团队要求的B/E独答优势及完整历史长度/成本/adapter绑定预检，再按批次审核进入1–2→8→累计32。专用SSH密钥已获用户授权并验证，服务器原有未提交修改保留，无pull/reset。

'''
for name in ('handoff.md','CURRENT_STATE.md'):
    path=root/name
    original=path.read_text(encoding='utf-8')
    if '## 2026-11-03 V20底座量化健康诊断完成' not in original:
        path.write_text(entry+original,encoding='utf-8')
plan=root/'refine-logs/expert-mechanism-pilot-20261030'
stage='''## 2026-11-03 V20 precision health — assistant stage review

Goal/completion: finite first20-V NF4/BF16 sensitivity comparison, complete paired raw outputs, original official scorer, frozen inputs/prompts/runtime, explicit failure/cost export. Actual40/40 valid,37.29s,0 retries/OOM/output-limit; original NF4 answers exactly reproduced20/20. EM15% vs10%, paired2/1/0/17. PASS only bounded sensitivity and execution; not model optimality/general precision or team benefit. No evidence BF16 cures weak baseline in this prefix; retain original settings and C qualification, do not retune on C. Existing uncommitted server work preserved. Next permitted stage: team-prompt-matched independent B/E, full-history/cost/adapter preflight and batch review before1–2 timing items. No B1 launched. Reviewer=assistant self-review, independence=none/provisional. See engineering/baseline-health-20261103/RESULTS.md and runs/baseline-health-v20-20261103-v1/.

'''
for name in ('STAGE_REVIEWS.md','WORK_TRACKER.md'):
    path=plan/name
    original=path.read_text(encoding='utf-8') if path.exists() else ''
    if '## 2026-11-03 V20 precision health' not in original:
        path.write_text(stage+original,encoding='utf-8')
print('COMPLETION_RECORDED; prior history retained')
