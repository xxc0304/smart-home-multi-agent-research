# 最新实测进展（2026-11-03）

Qwen3-4B/NF4仅答案LoRA首轮1796题训练完成。V200：底座EM13.5%，微调45.0%；独立C160：13.75%→51.25%，配对提升37.5pp，139组bootstrap95%区间[28.93,46.05]pp。两组均完整；任务优势资格通过，尚无团队效果证据。

- [训练及V结果](engineering/b0-first-run-20261103/RESULTS.md)
- [C160资格及边界](engineering/b0-first-run-20261103/C160_RESULTS.md)
- [低底座分数审核](TRAINING_VALIDATION_LOW_BASELINE_REVIEW_20261103.md)
- [当前交接](handoff.md)

当前待办：在V做有限基线健康诊断（尚未运行），再核团队条件中的独答优势、长度和成本。C已使用且关闭调参，H未读。以下旧条目保留历史，以顶部交接为准。模型权重、adapter、数据集及完整runs原件未纳入Git；已同步小型评分/训练状态证据及运行配置。

---
# CoReTA

**Complementary Reasoning through Targeted Assistance**。通过定向帮助、贡献检查与实际应用反馈，发挥成员互补能力，提升多 Agent 团队的协调与问题解决能力。当前能力与机制优先，同成本优势及成本节约后置。

研究起点是《Multi-Agent Teams Hold Experts Back》中的专长稀释与团队折中：怎样保留有依据的专长，同时接受有效纠错。分散知识和局部工作组合是后续检验设置。用户最新澄清与方向建议见[研究定位复核](research/expertise-preserving-collaboration-20261028/REVIEW.md)。

截至 2026-10-28：项目已有多轮开发与诊断运行，但近期交接、修订和验证候选尚未显示稳定的额外任务质量收益。用户将当前优先级调整为充分理解文献、界定具体问题，再选择方法。已完成35篇相关方法与结果的分段核读及[综合调查](research/expertise-literature-survey-20261028/REPORT.md)，逐篇比较见[证据矩阵](research/expertise-literature-survey-20261028/PAPER_MATRIX.md)。没有待续跑批次。详见[工作交接](handoff.md)和[当前状态记录](CURRENT_STATE.md)。v0.3.1 原型的早期评分链路记录保留在 [Linux评分就绪记录](engineering/LINUX_SCORING_READY_20261019.md)。

投稿目标为 ACL 2027；主会最迟 ARR 投稿为北京时间 2027 年 1 月 5 日 19:59。日期、官方来源及待公布事项见 [ACL 2027 投稿信息](submission/ACL_2027.md)。

## 阅读顺序

1. [当前工作交接](handoff.md)
2. [详细状态与历史](CURRENT_STATE.md)
3. [当前文献综合与问题地图](research/expertise-literature-survey-20261028/REPORT.md)；[历史架构候选](research/constraint-collaboration-design-20261027-v1/ARCHITECTURE.md)
4. [统一相关工作目录](related_work/INDEX.md)
5. [实验结果索引](experiment/results.md) 与 [评测约定](experiment/evaluation.md)
6. [基线复现状态](reproduction/README.md) 与 [运行目录索引](experiment/run-index.md)

设计附件包括消息 Schema、固定提示词、建议配置及人工构造协议示例。数学主评价为 MATH-500，代码主评价为 HumanEval/Plus；任务、对照与机制诊断的具体设置见实验协议。

## 研究归档

- [v0.2 历史草案](research/complementary-help-design-20261018/ARCHITECTURE_V0_2.md)
- [前期讨论复审](DISCUSSION_REVIEW_AND_PLAN_20261018.md)
- `research/multiagent-gaps-20261016/`：早期方向探索。
- `research/human-team-agent-frameworks-20261017/`：人类组织与 Agent 框架。
- `research/multiagent-landscape-20261018/`：架构、通信与聚合。
- `research/expertise-human-transfer-20261018/`：专长利用与迁移边界。
- `research/complementary-help-design-20261018/`：定向互助的原设计依据与证据计划。
- `SOURCE_MANIFEST.json`：原始材料归档的来源及初始 SHA-256 对照。
- [本轮输出清单](MANIFEST.md)

模型审查是辅助意见，不能代替有效性实验或新颖性核验。本项目不将 [HomeCoord-Bench](https://github.com/xxc0304/homecoord-bench) 的历史结果作为 CoReTA 方法证据。


## 2026-10-19 真实联调更新

最新状态以 [准备修复与真实联调](engineering/PREPARATION_FIXES_20261019.md) 为准：52项本地检查通过；停批和tokenizer批量接入已修复；数学、代码各1题完成13次真实生成请求及Docker评分，结果分别1/0。未开展效果对照，帮助请求分支尚无真实验证。


## 2026-10-19 E1开发试点已完成

详见 [完整试点报告](engineering/DEVELOPMENT_PILOT_REPORT_20261019.md)。20题×三条件共60条轨迹、120条前后评分记录齐全。三条件逐题得分相同：数学9/10、代码8/10。59条正常完成，1条引用绑定错误降级；CoReTA实际帮助请求0。三道共同失败题存在评价一致性疑点，保留原分。先诊断任务适配与未求助原因，再决定是否修订并冻结新配置；未启动正式主实验。


## 2026-10-19 E1审核与诊断

详见 [完整审查](PILOT_REVIEW_AND_DIAGNOSIS_20261019.md)。20条轨迹逐案复核、60份初稿离线评分和100题开发池静态检查已完成，无新增模型生成。A0初稿已通过17/20，现有初稿整解选优同为17/20，未出现A0失败但同伴通过的题；实际决策输入均还有2轮且提供五动作。零请求不能直接视为协调失败。引用修复反馈和一条预算理由需改进；任务契约裁定与下一轮辨识条件待冻结。原E1结果保留。


## 项目工作流入口

- [工作交接](handoff.md)：当前研究状态、未解决问题和下一步。
- [讨论与假设](brainstorm.md)：按日期记录的假设、证据和暂缓方向。
- [相关工作统一目录](related_work/INDEX.md)：集中入口、文献台账和原始阅读记录索引。
- [实验结果索引](experiment/results.md) 与 [评测约定](experiment/evaluation.md)：汇总已完成批次并映射各任务的冻结评分文件。
- [数据说明](dataset.md)：说明 `data/` 中来源、任务包和处理记录。
- [基线复现状态](reproduction/README.md)：区分论文原设置复现、论文机制适配与项目内对照。
- [运行目录索引](experiment/run-index.md)：定位 `runs/` 下全部版本化记录。

CoReTA 已有的 `research/`、`refine-logs/`、`runs/` 和 `data/` 保持原位；工作流入口链接到这些详细记录，不搬动历史证据。

