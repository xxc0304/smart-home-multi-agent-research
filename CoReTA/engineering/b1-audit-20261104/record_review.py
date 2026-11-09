from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
audit=json.loads((Path(__file__).parent/'AUDIT.json').read_text())
assert audit['recomputed_scores_identical'] and audit['all32_replay_structurally_valid']
entry='''## 2026-11-04 B1设计/结果/过程审核完成

见[审核报告](engineering/b1-audit-20261104/REPORT.md)。全部32轨迹结构重放、评分复算及私人可见性/身份/终答隔离通过；32计划/28完整，原primary=false不改。2×2开发设计保留，完整性及语义损害解释REVISE，助手自审none/provisional。重点核读7个过程案例：B所有3个专家EM1→0涉及表述/粒度或题意解释问题，不等同已确认的3次语义损害；027母亲题私人工作两轮正确但终答变父亲，024正确答案只在私有终答出现仍被3票丢失，018公开理由称不足而最终四人正确。区分初答/工作/终答/投票，不把终答正确当已分享采用。完整28中普通三人初答23题一致，不能当独立三证据。B−A点差+12.5pp但分组95%区间跨0；加入可用部分臂后固定32题缺失界限B−A[+1.56,+14.06]pp，仅有限样本算术界非总体CI。原评分/gold/失败保留，无新生成。下一步先事先定义语义分类并复核关键事件、检查终答与读出/截断合同，再另立版本测完整性和加速；不自动换题/清洗/扩跑。

'''
for name in ('handoff.md','CURRENT_STATE.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md'):
    p=ROOT/name;old=p.read_text(encoding='utf-8')
    if '## 2026-11-04 B1设计/结果/过程审核完成' not in old:p.write_text(entry+old,encoding='utf-8')
p=ROOT/'brainstorm.md';old=p.read_text(encoding='utf-8') if p.exists() else ''
marker='## 2026-11-04 过程候选：工作到终答、证据到读出'
if marker not in old:p.write_text(marker+'\n\n既有D32审核观察：有私人工作正确而终答关系翻转、工作称信息不足但终答正确、正确终答未被投票选用。仅为可检验候选，不能统一归因社会从众/接收失败；EM损失有语义歧义。先按明确标准审核已有案例，不新增机制或实验。见engineering/b1-audit-20261104/REPORT.md。\n\n'+old,encoding='utf-8')
print('REVIEW_RECORDED_NO_MODEL_RUNS')
