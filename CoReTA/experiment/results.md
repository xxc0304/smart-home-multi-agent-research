# CoReTA 实验结果索引

本页汇总近期已完成且对当前问题仍有解释价值的批次，不是全量结果清单。每项链接到 run 和语义/科学复核；失败、无差异和不完整记录都保留。[所有含结果报告的 live 目录](live-results-index.md)可逐项核查；`runs/` 的全部物理目录另见[运行目录索引](run-index.md)，目录数不等于独立实验数。

| 日期 / 批次 | 样本与观察 | 解释边界 | 详细记录 |
|---|---|---|---|
| 2026-10-27 local-work-handoff pilot | 84 次请求、12 条终稿。普通讨论与显式交接组在两道普通题和两道依赖题上均得到正确终稿；普通协作也自然形成跨成员工作组合。 | 显式交接可自然运行，但未显示优于同工具普通协作的质量收益；四道题只支持开发观察。 | [`RESULTS.md`](../research/local-work-handoff-pilot-20261027/RESULTS.md)、[`runs/`](../runs/local-work-handoff-pilot-live-20261027-v1/) |
| 2026-10-27 local-work-handoff confirmation | 168 次请求。普通题：discussion 4/4、ordinary 4/4、local_work 2/4；依赖题各组 2/4，分别报告。 | 样本少且含参考粒度歧义；显示交接可重现，但没有稳定质量优势，显式方案成本较高。 | [`RESULTS.md`](../research/local-work-handoff-confirm-20261027/RESULTS.md)、[`SEMANTIC_REVIEW.json`](../research/local-work-handoff-confirm-20261027/SEMANTIC_REVIEW.json)、[`runs/`](../runs/local-work-handoff-confirm-live-20261027-v1/) |
| 2026-10-27 constraint-commit | 18 次请求。历史主任务参考正确 3/6、提交正确 4/6；事后直接执行初始表的基线也是 4/6。 | 保留小规模观察；未证明提交修订优于更简单的直接执行。 | [`RESULTS.md`](../runs/constraint-commit-live-20261027-r1/RESULTS.md)、[`FURTHER_ANALYSIS.md`](../runs/constraint-commit-live-20261027-r1/FURTHER_ANALYSIS.md) |
| 2026-10-27 inference-link | 24 次请求。两组终稿均与旧稿选择相同。 | 未显示新增指导带来额外终稿收益。 | [`RESULT_REVIEW.md`](../runs/inference-link-live-20261027-r1/RESULT_REVIEW.md)、[`设计走查`](../research/inference-link-walkthrough-20261027-v1/SPEC_AND_WALKTHROUGH.md) |
| 2026-10-26 example adaptation | 72 次请求。无示例 10/16，正例 10/16，正反例 11/16；额外命中没有重复出现。 | 局部候选信号，不支持稳定提升；须与原稿和任务控制分开解释。 | [`RESULTS.md`](../runs/example-adaptation-live-20261026-r1/RESULTS.md)、`research/example-adaptation-analysis-20261026/` |
| 2026-10-26 local reconstruction | 32 次请求。可见旧稿与隔离重建两组均参考命中 5/8。 | 两组分别修复和损害不同样本；没有净增益证据。 | [`RESULTS.md`](../runs/local-reconstruction-live-20261026-r1/RESULTS.md)、`research/isolated-reconstruction-20261026-v1/` |
| 2026-10-26 IMP adaptation | 64 次请求；两道开发题各重复两次，IMP 式路由组 4/4，普通消息组 1/4；全资料单 Agent 4/4。 | IMP 机制适配，非原论文设置复现；样本很小。 | [`RESULTS.md`](../runs/imp-adaptation-live-20261026-r1/RESULTS.md)、[复现状态台账](../reproduction/README.md) |
| 2026-10-26 IMP confirmation | 74 次请求；两道新增开发题各重复两次，IMP 组团队分摊 2/4，普通组 1.5/4，全资料单 Agent 3/4。 | 007 有局部正信号，008 两种多 Agent 条件都失败；没有稳定优势证据。 | [`RESULTS.md`](../runs/imp-confirmation-live-20261026-r1/RESULTS.md)、[复现状态台账](../reproduction/README.md) |
| 2026-10-26 receiver application baseline | 64 次请求；四道开发题、每接收者每条件一次，证据诊断组参考命中 9/16，普通复议组 6/16。 | Re-Ex 风格的接收端适配，不是 Re-Ex 全文复现；诊断本身有对象误述。 | [`RESULTS.md`](../runs/receiver-baseline-live-20261026-r1/RESULTS.md)、[复现状态台账](../reproduction/README.md) |
| 2026-10-26 receiver confirmation | 两道新增开发题每条件一次；公开题普通组 1/6、诊断组 2/6，自编控制题两组各 3/3。 | 只出现一个额外局部正确案例，未确认稳定改善；不与上一批合并。 | [`RESULTS.md`](../runs/receiver-confirmation-live-20261026-r1/RESULTS.md)、[复现状态台账](../reproduction/README.md) |
| 2026-10-19 E1 development pilot | 20 题 × 3 条件。数学各 9/10、代码各 8/10；CoReTA 帮助请求为 0。 | 开发试点；不代表正式效果对照。 | [`PILOT_REVIEW_AND_DIAGNOSIS_20261019.md`](../PILOT_REVIEW_AND_DIAGNOSIS_20261019.md)、[`DEVELOPMENT_PILOT_REPORT_20261019.md`](../engineering/DEVELOPMENT_PILOT_REPORT_20261019.md) |

## 解释规则

- 最近几项批次共同表明：交接流程能运行，但新增提示/字段/修订步骤尚未显示稳定的超额质量收益。
- 不把每次重复当成独立题目，不跨普通题与依赖题或不同任务族合并一个总体优势数字。
- 结论以本索引链接的原始结果、评分文件和 `EXPERIMENT_REVIEW.md` 为准；旧批次保持不可变。
- 全量目录定位见 [`run-index.md`](run-index.md)；含报告的 live 目录清单见 [`live-results-index.md`](live-results-index.md)。本页保留代表性批次的人工解释摘要，其余批次以原始报告为准。
