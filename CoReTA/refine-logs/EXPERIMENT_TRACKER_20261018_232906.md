# CoReTA 设计对应的执行跟踪表

日期：2026-10-18。所有运行状态均为 PLANNED，尚未执行。

| Run ID | Milestone | Purpose | System / Variant | Split | Metrics | Priority | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| E0 | 工程核查 | 状态、契约、数据隔离和评分适配 | 全部共享组件 | 构造记录/开发题 | 解析、引用与评分一致性 | MUST | PLANNED | 当前只有设计附件，无运行实现 |
| E1 | 开发试点 | 观察实际交互与工程故障 | independent/static/coreta | GSM8K train10 + MBPP sanitized train10 | 任务分数、交互、故障、资源 | MUST | PLANNED | 先核端点与明确批次 |
| E2 | 主结果 | 数学任务能力 | 5条件×3重复 | MATH-500 test500 | 准确率、配对差和区间 | MUST | PLANNED | 测试前冻结配置 |
| E3 | 主结果 | 代码任务能力 | 5条件×3重复 | HumanEval164/Plus | pass@1 | MUST | PLANNED | 只离线执行评分 |
| E4a | 机制 | 定向请求与显式应用记录 | full/generic/no-application | 每任务族预选100×3 | 配对变化、交互行为 | MUST_FOR_C2 | PLANNED | 不按成功选择题目 |
| E4b | 内容干预 | 实际贡献内容作用 | natural/redundant | 每任务族预选50×3 | 接收后变化与最终结果 | MUST_FOR_C2 | PLANNED | 仅在首个合格帮助前分支 |
| E4c | 离线核对 | 内容新颖性、有效性与应用 | 匿名化轨迹 | 每任务族30，seed17 | 贡献/应用标注 | SUPPORT | PLANNED | 人员资源未知 |
| X1 | 扩展 | 不同模型专长 | 异构/同构/强单体 | 待主张明确 | 能力、机制与边界 | OPTIONAL | NOT_SCHEDULED | 不在当前主结果中宣称 |
| X2 | 扩展 | 相同成本及效率 | 多资源点 | 待定 | 质量—成本 | OPTIONAL | NOT_SCHEDULED | 按用户要求后置 |
