# 检索、覆盖和校正记录

日期：2026-10-28。冻结问题见 BRIEF.md；调查结论见 REPORT.md。本文件记录实际检索方向与范围，不冒充完整数据库导出或 PRISMA 筛选计数。

## 检索工具和顺序

通过网络检索定位 arXiv、ACL Anthology、PMLR、NeurIPS/OpenReview 原始记录；本地 pypdf 用于已有原文。二手网页仅帮助发现线索，技术论断回到原文。没有使用付费研究模型 API、启动复现或获取临床数据。

1. 冻结三个 RQ，明确专长利用是核心，分散信息与选择性修订不是预设唯一解。
2. 三个独立上下文视角并行搜方法、评价、专长/信息，主代理单独核原始论文与读出/核查能力。
3. 每个视角先宽搜，再以新方法名、完整题名和作者收窄；核读相关方法、结果和附录。
4. 合并候选，补查引文链，重点添加初始清单遗漏的正面方法和近期更新。
5. 串行综合，保留不一致条件及已有进展，再提出候选研究问题。

各视角的完整实际关键词、引用链和排除记录见 [METHODS.md](METHODS.md)、[EVALUATION.md](EVALUATION.md)、[EXPERTISE.md](EXPERTISE.md)、[ANCHOR.md](ANCHOR.md)。以下列主代理的补充检索，避免与代理关键词混成单次批量查询：

- 宽搜：Multi-Agent Teams Hold Experts Back expertise leveraging follow up 2026；LLM expertise utilization multi agent；LLM expertise hidden profile。
- 精确核验：When Debate Helps Proposal Supply 2026；From Debate to Decision Conformal Social Choice Wang；Multi-Agent Teams Hold Experts Back Pappu ICML2026。
- 分歧审计盲点：AgentAuditor Anti-Consensus；AgentAuditor reasoning tree Yang2026；LLM multi agent expertise leveraging survey2026 specialist。
- 专长路由盲点：LLM multi agent expertise-aware deference2026；LLM multi agent expert selective deference；multi agent expert identification leveraging2026。
- 历史解释边界：Debate Helps Supervise Unreliable Experts；On scalable oversight with weak LLMs judging strong LLMs；Prover-Verifier Games improve legibility。

## 覆盖结果与补充

核心证据矩阵35篇（ANCHOR7、METHODS9、EVALUATION9、EXPERTISE10）。这个数表示带实际方法/结果阅读范围的记录，不表示35篇全篇逐字阅读或新增35个PDF。原始论文、失败审计、方法改进、专长招募/解释、分散信息、读出/风险控制、弱核查者条件均有多篇证据。文献目录同时保留既有57个本地PDF；新在线全文的本地归档状态不作假定。

盲点补查改变了比较位置：

- DEAR与Demystifying提供同时改善纠错和有害修订的训练方法证据，修正“干预只能让所有人更保守”的概括。
- EMRC已有领域/难度历史表现表、动态招募及协作消融，修正“校准领域能力后组织协作尚无方法”的潜在误报。
- AgentAuditor已有推理树、局部分歧审计和偏好训练，不能把通用“定位争议再检查”当未实现的概念空白。
- HiddenBench本身包含有效的结构化交流干预；Consilience/IMP不是只有失败分析。
- SAT的主贡献是学习组织策略，且有超强单体与匹配控制的正面结果；不能只谈其附录流程与我们的相似性。

## 未进入核心矩阵的线索及原因

- DEALS（arXiv:2609.33768）：核读原摘要，研究任务流队列、负载和历史成功率的去中心化路由。与同题讨论中的意见采用不同，作为范围边界保留在EXPERTISE.md，不用摘要编造方法细节。
- Debate Helps Supervise Unreliable Experts（arXiv:2311.08702）：本轮核原摘要，经典邻近背景；主矩阵采用已读方法的弱judge研究和PVG。摘要阅读不混入35篇方法记录。
- MARS（arXiv:2608.23918/正式EMNLP页面）：通过专业算法库与代码执行组织接力，原始页面已定位；本轮不将尚未精读的机制写入核心结论。
- 另一篇同名 AgentAuditor（NeurIPS2025，安全/安保评估）与本轮推理树聚合论文不是一篇，不能合并出处。
- 一般agent框架survey、企业新闻、预测性博客、二手AI审稿：用于发现词汇或引文，不支撑当前技术结论。医疗tool-expertise等应用边界尚未系统覆盖，不能对其作无人研究断言。
- 其他视角已排除的恶意攻击基准、拟人意见模拟、未核方法的应用论文见各MD；排除是本次范围选择，不等于文献无价值。

## 核验和版本校正

- Hold Experts Back v4 Table2：ML的ALOC是逐题事后参照，部分团队高于最佳固定单体；心理任务的已知信息专家条件另看。
- Free-MAD：正式版和预印本分开；预印本称省略展示单agent结果并做过验证，不改写成没做。
- Flips使用最新v2，ColMAD最新v2有消融、统计和成本附录；不沿用旧摘要/二手缺陷结论。
- DEAR按v2六作者；NeurIPS官方Downloads核准题名，技术阅读为arXiv版。
- Minority Sentinel：作者实验室标AgentSearch workshop展示，无archival proceedings；不称SIGIR主会论文。
- EMRC正文/abs作者顺序为Bao、Peng共同一作；正式venue未核准，写预印本。
- One Axis公开日期与ID月份不一致，仅用可核验版本/内容，不据此判断优先权；Identity中Jerry/Xiaojin为作者别名。
- Conformal Social Choice正式PDF抓取cache miss，已读v2与正式页摘要/元数据，不声称读完正式PDF。

## 综合后的反向检查

没有只保留负面证据：ReConcile、EMRC、DEAR、SAT、ColMAD、AgentAuditor、Consilience和InfoDelphi等正面结果已在主体展开。没有把“更少从众”当唯一目标：来源可靠性、可检查性、候选供给、读出及风险控制分别比较。没有把所测probe/理论条件写成通用不可能性，也没有把未报告的专家实验当作已有方法失败。

本文候选问题都有近邻，结论定位为值得进一步理解的具体条件，而非首创认证。文献调查本身不决定必须做训练、理论、benchmark或复杂架构；后续贡献可以聚焦一个重要环节。
