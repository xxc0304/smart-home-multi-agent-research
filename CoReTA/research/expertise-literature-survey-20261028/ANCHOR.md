# 原始锚点、最终利用与核查能力：第四视角核读

本视角按 BRIEF.md 的 RQ1–RQ3，重新核读原始论文，并补入正确候选读出、集合决策和弱核查者三类证据。逐篇操作和阅读边界见 ANCHOR.json。

## 条件决定结论，不能把所有“专家”当同一个参照

Hold Experts Back 的心理任务通过专家解释控制信息优势，ML任务的专家则按逐题结果确定；后者报告的 ALOC 是逐题理想选择，不是一个固定模型。v4 Table2 中，公开专家团队在 GPQA/SimpleQA/HLE/MATH 的准确率已高于最佳固定单体，虽仍未达到 ALOC。因此不能把“在已知信息专家条件下有损失”和“在ML上未达到逐题oracle”合成“所有团队始终不如最佳单体”。会话折中与表现相关；训练/对齐导致折中和对抗保护共用同一机制仍属解释假说。与 When Debate Helps 的 headroom 分解对照，二者都提示已有正确候选并不保证被利用，但后者同时给出覆盖选队和实质交互收益的正面结果。

## 供应、读出与统计安全是不同操作

When Debate Helps 用覆盖目标选择权重扰动形成的互补模型，LVD是候选读出层的理论记账，部署是讨论指令和 vote-then-judge；固定候选证据干预检验了内容敏感性，不能当部署时的真值识别。AgentAuditor 则真正把轨迹合并成推理树，在局部分叉比较，并可用ACPO训练auditor；因此“局部争议+依据比较”已有具体方法成果。两者的积极结果均应保留，其剩余边界分别包括候选供给、实际转化率与审计能力，不能要求它们给出全能保证才算价值。

Conformal Social Choice 与 C-MoA 共同说明另一种合法贡献：在给定风险约束下控制可执行输出。前者用多选候选集决定自动/人工升级，后者用答案级阈值筛掉低支持原子事实；两者并非自动提高每题推理能力。C-MoA 所测仅靠记忆的近似反事实未改善排序，是可定位的负面证据；这与 AgentAuditor 的局部审计正结果不冲突，因为任务、监督、核查者与可用证据不同，不能推出所有自评或所有局部核查必然有效/无效。

## 核查能力不是只能接受的常数

Kenton等在弱judge/强辩手条件下看到信息不对称QA的积极收益与闭卷条件的混合结果；Kirchner等通过训练helpful/sneaky prover改变输出可检查性，在所测数学任务改善了弱核查者和人类的判断。这说明专家利用可以从供应者表达、接收者能力和可用证据共同研究。它既不同于简单身份服从，也不要求每名同伴独立重解整个任务。将来若聚焦可展示性，应明确同这些已有监督/训练路线的关系。

## 本视角检索日志

宽搜：Multi-Agent Teams Hold Experts Back expertise leveraging follow up 2026；LLM expertise utilization multi agent；LLM expertise hidden profile。
窄搜：When Debate Helps Proposal Supply 2026；From Debate to Decision Conformal Social Choice Wang；Multi-Agent Teams Hold Experts Back Pappu ICML2026。
盲点补查：AgentAuditor Anti-Consensus；AgentAuditor reasoning tree Yang2026；LLM multi agent expertise leveraging survey2026 specialist。由此定位推理审计AgentAuditor，与NeurIPS2025同名安全评估AgentAuditor区分。泛系统survey和应用新闻仅用作检索线索未纳技术证据。
引文链补查：weak LLMs judging strong LLMs、Prover-Verifier Games、Debate Helps Supervise Unreliable Experts（后一篇本轮只核摘要，未纳主要方法矩阵）。

Conformal正式PDF工具抓取cache miss，核读已有v2正文并对比正式页元数据和摘要；没有把读取v2写成通读正式PDF。所有新在线论文的本地归档状态另由catalog记录，不在此假定下载完成。

