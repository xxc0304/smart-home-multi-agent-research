# 相关工作统一入口

本目录将 CoReTA 过去的文献检索、阅读范围和相关工作讨论集中起来。`catalog.json` 和 `ledgers/` 统一整理现有链接、核验范围及讨论出处；`papers/` 保存已归档的公开全文。`research/` 中的分析报告继续作为原始记录，不搬动，以保留既有时间线和引用。

2026-10-30新增[小模型规模与协作证据核对](ledgers/small-model-expert-collaboration-2026-10-30.md)：8篇原文配置，4B/8B可作正式实证候选，量化/思考预算/训练成本与现象可观察性分别判断。

## 本地已归档全文

2026-10-29 ACL2027规划新增的强近邻先记入[专门台账](ledgers/acl2027-planning-2026-10-29.md)；下段全文和catalog数量为上一版集中统计，不包含这些仅新增链接的条目。

已归档 72 个不同 arXiv ID 的全文及 ACL Anthology 正式版全文，见 [`papers/`](papers/README.md)，各目录保留来源、题名和版本。总台账现有 83 个不同 arXiv ID，其中 11 个目前没有本地 PDF。每条来源是否有本地全文以 catalog 的状态为准。此前35篇相关段落核读及跨论文综合见[专长利用调查](../research/expertise-literature-survey-20261028/REPORT.md)和[逐篇证据矩阵](../research/expertise-literature-survey-20261028/PAPER_MATRIX.md)；[局部依据专题比较](../research/expertise-literature-survey-20261028/LOCAL_EVIDENCE_LITERATURE_COMPARISON.md)、[实验缺口与已有工作](../research/expertise-literature-survey-20261028/GAP_STATUS_AND_PRIOR_ART.md)和[来源可信与最终决策](../research/expertise-literature-survey-20261028/SOURCE_TRUST_PRIOR_ART.md)包含后续近邻。

## 按问题查阅

| 主题 | 集中台账 | 用途 |
|---|---|---|
| 首个能力专家任务与近邻对齐 | [8篇近邻矩阵](../research/expert-task-alignment-20261030/NEAREST_WORK_MATRIX.md)、[MuSiQue/Hotpot/GSM8K比较](../research/expert-task-alignment-20261030/TASK_COMPARISON.md) | 复用已有核读，未新增论文PDF；官方任务字段/评分及60条数据实读，LoRA构造不当已成立创新 |
| 专家研究公开资产与8条真实案例核对 | [资产表](../research/expert-team-assets-20261029/ASSET_AVAILABILITY.md)、[案例卡](../research/expert-team-assets-20261029/CASE_SEED_8.md) | 原论文W&B/独立输出口径、PBT真实LFS/Arrow、HiddenBench全信息补充；访问状态不等于论文方法无效 |
| ACL2027规划的强近邻补查 | [acl2027-planning-2026-10-29.md](ledgers/acl2027-planning-2026-10-29.md) | When Order Matters、OSC、Listening Agents、EDGE、Interaction Tax；含状态和核查范围，未新增PDF |
| 多成员条件组合与019作者轨迹 | [`joint-refutation-019-2026-10-28.json`](ledgers/joint-refutation-019-2026-10-28.json) | HiddenBench作者讨论记录与组合线索的先行研究 |
| 局部反驳与选择性修订 | [`partial-refutation-2026-10-28.json`](ledgers/partial-refutation-2026-10-28.json) | 不给完整替代解的验证、关键条件核查及局部批评正负作用 |
| 来源可信与最终决策 | [`source-trust-decision-2026-10-28.json`](ledgers/source-trust-decision-2026-10-28.json) | ReGround、ECL、证据裁决及上游消息覆盖等直接研究 |
| 项目实验缺口与现有研究 | [`gap-status-check-2026-10-28.json`](ledgers/gap-status-check-2026-10-28.json) | 来源处理、规则执行、事实流失与候选崩塌；区分项目证据与先行成果 |
| 局部依据与建议修订 | [`local-evidence-use-2026-10-28.json`](ledgers/local-evidence-use-2026-10-28.json) | IMP、ICR、InfoDelphi、GDP 以及 ReGround、CoSIR 等近邻；区分实证成果和可发展的问题 |
| 专长利用的系统调查与问题地图 | [`expertise-literature-survey-2026-10-28.json`](ledgers/expertise-literature-survey-2026-10-28.json) | 35篇问题、机制、已解部分及剩余条件；含DEAR、EMRC、AgentAuditor、SAT等正面方法 |
| 专家被拖累、无依据折中与意见修订 | [`expertise-preserving-collaboration-2026-10-28.md`](ledgers/expertise-preserving-collaboration-2026-10-28.md) | 原始研究动机、身份偏差、附和、置信度更新与少数改票近邻 |
| 多 Agent 协调、通信与组织 | [`literature-coordination-2026-10-19.md`](ledgers/literature-coordination-2026-10-19.md)、[`topvenue-entrypoints-2026-10-20.md`](ledgers/topvenue-entrypoints-2026-10-20.md) | 架构、协作与近期顶会案例 |
| 集体推理失败和方法机制 | [`literature-failures-2026-10-19.md`](ledgers/literature-failures-2026-10-19.md)、[`literature-mechanisms-2026-10-19.md`](ledgers/literature-mechanisms-2026-10-19.md)、[`failure-synthesis-literature-2026-10-23.md`](ledgers/failure-synthesis-literature-2026-10-23.md) | 失败类型、验证、纠错与实验边界 |
| 专长、分布式知识和条件化贡献 | [`expertise-architecture-2026-10-20.md`](ledgers/expertise-architecture-2026-10-20.md)、[`conditional-expertise-neighbors-2026-10-20.md`](ledgers/conditional-expertise-neighbors-2026-10-20.md) | 研究问题、机制近邻与核验限制 |
| 局部工作、交接和后续执行 | [`local-work-composition-literature-2026-10-27.md`](ledgers/local-work-composition-literature-2026-10-27.md) | 现代 LLM 交接与经典条件推理/依赖系统 |
| 接收者辨别与应用 | [`receiver-capability-literature-2026-10-28.json`](ledgers/receiver-capability-literature-2026-10-28.json) | 反例、工具核查、外部验证和迁移边界 |
| 任务和评测基准 | [`workboard-evaluation-sources-2026-10-22.md`](ledgers/workboard-evaluation-sources-2026-10-22.md) | HiddenBench、iAgents、InformativeBench 等数据来源与适配限制 |
| 文献驱动的设计修订 | [`coreta-literature-synthesis-2026-10-19.md`](ledgers/coreta-literature-synthesis-2026-10-19.md) | 既有研究如何改变 CoReTA 设计 |

## 原始讨论记录

- `research/expertise-architecture-20261020/` 与 `research/conditional-expertise-neighbors-20261020/`：专长设置和具体近邻审查。
- `research/topvenue-entrypoints-20261020/`：顶会案例及逐项阅读边界。
- `research/local-work-composition-20261027/`：局部成果交接、依赖执行及对本地结果的交叉分析。
- `research/receiver-capability-literature-20261028/`：最近的接收者能力文献核读与来源 JSON。
- `research/competition-selection-review-20261028/`、`research/discussion-audit-20261028/`：候选生成/选择和近期讨论的边界审查。

文献集合与出处详见 [`catalog.md`](catalog.md) 和 [`catalog.json`](catalog.json)。目录里的链接有重复来源时按原台账保留出处；同一论文的正式页、预印本和代码仓库不默认视为同一版本。

