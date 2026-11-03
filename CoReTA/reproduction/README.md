# CoReTA 基线复现与对照台账

本台账把三类证据分开：论文原设置复现、论文机制适配、项目内对照。下载论文或跑通相似组件，都不自动算作论文复现。

## 已有基线证据

| 方法 / 对照 | 来源和版本 | 项目内证据 | 当前状态 |
|---|---|---|---|
| IMP 原件路由 | [arXiv:2610.24718v1](../related_work/papers/arxiv-2610.24718v1/paper.pdf)；未找到作者公开代码 | [64 次适配小试](../runs/imp-adaptation-live-20261026-r1/RESULTS.md)；[74 次新增开发题确认](../runs/imp-confirmation-live-20261026-r1/RESULTS.md)；[复现边界审查](../research/decision-test-design-20261026/IMP_REPRODUCTION_ASSESSMENT.md) | **机制适配已测试，非原论文复现。** 任务、模型、原件单位和投票设置均有差异；保留为当前最重要的论文方法参照。 |
| Re-Ex 风格的解释后修订 | [Re-Ex arXiv:2402.17097](../related_work/papers/arxiv-2402.17097v3/paper.pdf) | [四接收者应用诊断](../runs/receiver-baseline-live-20261026-r1/RESULTS.md)；[新增题确认](../runs/receiver-confirmation-live-20261026-r1/RESULTS.md)；[规格](../research/receiver-baseline-20261026-v1/SPEC.md) | **接收端适配已测试，非 Re-Ex 全文复现。** 现有结果为小规模开发题，诊断文本也出现目标稿误述。 |
| 普通协作（内部对照） | 项目任务协议；不对应单一外部论文 | [自然交接小试](../research/local-work-handoff-pilot-20261027/RESULTS.md)；[168 次确认](../research/local-work-handoff-confirm-20261027/RESULTS.md) | **已多批次比较。** 普通协作也能自然形成跨成员组合；显式交接没有显示稳定的额外质量收益。 |
| 全资料单 Agent（内部能力参照） | 项目任务协议；不是严格性能上界 | [IMP 64 次适配](../runs/imp-adaptation-live-20261026-r1/RESULTS.md)；[IMP 74 次确认](../runs/imp-confirmation-live-20261026-r1/RESULTS.md) | **已纳入对照。** 结果随任务变化；不得当作无成本参照或一般能力上界。 |
| 其他文献方法 | 见 [`related_work/INDEX.md`](../related_work/INDEX.md) 与本地论文清单 | 当前检索到的项目内复现记录尚未逐篇登记 | **文献已集中，方法级复现状态未逐篇核完。** 不把引用、机制借鉴或局部工程相似写成已复现。 |

## 下一轮复现应记录什么

对选择的关键基线，记录论文版本、作者代码/提交、模型和提示、任务与数据切分、指标、预算、运行环境、相对原文的适配差异、原文数字及项目内结果，并链接完整请求/响应和审核。不能忠实复现时，明确写为适配并逐项列差异。

## 当前可执行结论

- 项目已有可用的内部比较条件和两种重要论文机制适配，无须把历史工作说成“尚未做过任何 baseline”。
- 现有证据不足以声称完成了 IMP 或 Re-Ex 的论文级复现，也没有一份统一的跨方法、同任务复现矩阵。
- 下一步可以先做离线证据归档和方法差异对照。任何新付费运行仍须按 `EXPERIMENT_CHARTER.md`、`EXPERIMENT_PREFLIGHT.md` 审核，并取得该批次授权。
