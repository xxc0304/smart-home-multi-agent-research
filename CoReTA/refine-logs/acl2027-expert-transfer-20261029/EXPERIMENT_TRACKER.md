# 研究计划执行表

更新2026-10-30。A0-assets已做离线资产核对；完整MuSiQue数据/划分/评分与全体分词已完成限定范围R4自审，未训练或运行问答实验，不能视为已授权计算。

用户已确认研究方向；当前工作日程与前置依赖见[WORK_TRACKER](WORK_TRACKER.md)。下列E/R相关配置仍为候选，实际选取由资产、案例及最小验证决定，不因列入表中就视为冻结。

当前优先准备：[MuSiQue单专家最小方案](../../research/expert-task-alignment-20261030/FIRST_EXPERT_PILOT_PLAN.md)，先核能力对象与普通/无消息/聚合对照。下表旧E/R/D确认项保留为历史候选，不是已选的必做主检验。

2026-10-30设计状态更新：[来源/后果操作的开发诊断](../expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md)与[R7审核](STAGE_REVIEWS.md#r7)已保存；当前下一项P1为实际输入/操作核验，不是模型启动。四核心臂加G/N参照，能力校准和完整团队基线是同一开发计划前置块；两候选未确认，工程BLOCKED、DO_NOT_RUN。具体新清单见[TRACKER](../expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER.md)。

| 当前ID | 目的 | 状态 | 依赖/证据 |
|---|---|---|---|
| Q0-inputs | 官方prefix、标签隔离、长度 | CHECKED_PARTIAL | 60条、全为两跳；[实读](../../research/expert-task-alignment-20261030/MUSIQUE_INPUT_INSPECTION.json) |
| Q1-data | 完整数据、分组、别名、长度及暴露排除 | OFFLINE_PREP_PASS | [报告](../../research/musique-data-preparation-20261030/REPORT.md)、[R4](STAGE_REVIEWS.md#r4)；C160/D80/H候选2360/T可选2000，实际交叉和输入隔离已核；非模型实验就绪 |
| Q1a-protocol | 352独答输入、56待初答依赖、七条件生成与官方评分 | OFFLINE_PREP_PASS | [P1包](../../implement-stage/expert-mechanism-inputs-20261030/README.md)、[R8](STAGE_REVIEWS.md#r8)；真实新任务响应/后端预检待完成 |
| Q2-expert | 按实际资源选择现成模型或训练路径，独立校准优势 | NOT_RUN | 数据、实际推理资源/成本与批次审核；不预设4090 |
| Q2a-lora | 有资源时一个LoRA的可控能力构造 | CONDITIONAL_NOT_RUN | 训练资源不保证，非必经步骤；不与现成模型路径混称等价 |
| Q3-team | 首32个D题，身份已知/隐藏、独立/聚合对照 | NOT_RUN | Q2对象成立、实际协议与预算冻结 |
| Q4-decision | 事件/效应区间与主张选择 | NOT_RUN | Q3真实数据；未预填结果 |

以下为先前规划保留的候选矩阵，其中优先级不是本轮冻结运行承诺：

| ID | 阶段 | 目的/比较 | 原规划优先级 | 状态 | 继续条件 |
|---|---|---|---|---|---|
| A0-assets | A0 | 匹配公开独立输出、收件、过程与终答 | MUST | AUDITED / GAP | [资产表](../../research/expert-team-assets-20261029/ASSET_AVAILABILITY.md)：信息过程可用，能力校准与论文完整轨迹尚未匹配 |
| A0-label | A0 | 案例观察/规范与后续必要内容核验 | 按主张安排 | ASSISTANT_ANALYSIS_DONE_HUMAN_SCOPE_TO_PLAN | [8例分析](../../research/expert-case-analysis-20261030/REPORT.md)、[R6](STAGE_REVIEWS.md#r6)；先助手分析，不以人工表为门槛；核验工具保留，0人工完成 |
| A1-calibration | A1 | 独立任务优势及区间 | MUST | PLANNED | 数据/端点就绪、项目审核 |
| A1-drift | A1 | 普通团队与无消息额外思考 | MUST | PLANNED | 同初答/预算可对齐 |
| A1-cross | A1 | 开发E/R/sham、确认可用事件与费用 | MUST | PLANNED | 编辑命题内容保持 |
| B1-baselines | B1 | 团队、初答聚合、强者预算和一个强协议 | MUST | GATED_ON_A | 定义和资源冻结 |
| B2-primary | B2 | D×(R-only−E-only)候选主对比 | MUST | CANDIDATE_NOT_SELECTED | 对象/事件验证后再决定是否选取，不能仅按旧表执行 |
| B3-transfer | B3 | 冻结操作在新团队/第二任务复验 | MUST | GATED_ON_A | 无再次调规则 |
| B3-policy | B3 | 无gold简单选择对比固定最佳操作 | OPTIONAL | DEFERRED | C1支持且有明确实用价值 |
| C-boundary | C | 顺序/匿名、语义核验、成本和正反案例 | MUST subset | GATED_ON_B | 只做主张需要的边界 |

最新R8：P1离线部分完成；P2为实际模型/预算与一题真实技术验收合同。没有模型调用，完整团队与能力校准仍NOT_RUN；此前下一项P1表述为历史状态。

2026-10-30 R9最新顺序覆盖此前默认：C优势校准/D基础比较后增加P4a多环节过程检查，完成后才选P5干预；S/A保留待选。当前只准备资源与基础4＋1技术合同，未运行。见[当前计划](../expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md)与[R9](STAGE_REVIEWS.md#r9)。
