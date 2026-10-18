# 错误信息下的多 Agent 识别、纠正与任务恢复：定向文献核查

日期：2026-10-18。用户提出：向多 Agent 系统提供错误信息，检查是否能识别、纠正并解决任务。当前尚无具体算法与设置，故本文件是问题层面的文献核查，不作完整方法查新、独立评审或录用评分；未启动实验。

后续修订见 [RESEARCH_REVIEW_20261018.md](C:/Users/QVQ/Documents/ChatGPT/agent-research/RESEARCH_REVIEW_20261018.md)：补查验证/修复方法近邻，并明确“注入被采用”只作过程分层，不应据此筛掉主分析样本，以避免选择偏差。

## 判断

有实际研究价值，但原始表述已有非常直接的工作，不能以“首次注入错误看团队能否纠正”主张创新。近邻存在不意味着整个方向不值得做；下一步应比较具体错误条件、可用证据和已有纠错方法，而不是为了避开重叠不断缩小场景。

## 错误条件需要区分

| 轴 | 需要明确什么 |
|---|---|
| 来源 | 用户背景材料、检索/工具输出、成员消息、共享记忆；用户偏好和虚构世界设定不能轻率判为事实错误 |
| 性质 | 无意事实/数字错误、过期信息、推理错误、伪造证据、恶意指令；错误事实和prompt injection不是同一问题 |
| 暴露 | 一名成员收到、局部传播、全体收到；多份独立来源和同一来源被反复转述不同 |
| 可验证性 | 任务内存在矛盾/独立证据，能够重查/运行工具，或信息不足需澄清；证据不足时不能要求凭空恢复指定真值 |
| 注入有效性 | clean/noisy配对、保持其余任务可解、确认错误被接收且影响决策，不把无效攻击下的成功当纠错 |

## 原始来源核验与覆盖

| 论文、状态与访问层级 | 实际问题/方法 | 与用户想法的关系与边界 |
|---|---|---|
| [On the Resilience of LLM-Based Multi-Agent Collaboration with Faulty Agents](https://proceedings.mlr.press/v267/huang25ay.html), Huang et al., ICML2025；官方摘要 | AutoTransform/AutoInject修改成员输出，比较结构；Challenger质疑、Inspector检查并纠正消息 | 最直接的设置及方法先例。所报恢复结果属于指定任务和模拟错误，不是现实任意错误可恢复率。官方PDF本轮抓取失败，不冒称新增全文精读 |
| [MAS-FIRE: Fault Injection and Reliability Evaluation for LLM-Based Multi-Agent Systems](https://arxiv.org/html/2602.19843v1), Jia et al., 2026-02-23预印本；正文§3与相关评测段 | 15类故障，提示修改、输出重写、消息路由操纵；同时看系统成功与过程检测/修复 | 不仅注入错误，还已区分局部修复和最终成功；不能以增加过程指标作为当然增量。正文残留出版模板，不据模板宣称正式会议接收 |
| [When Truth Is Distributed: Misinformation Derails Collective Fact Recovery in LLM-Based Multi-Agent Systems](https://arxiv.org/html/2608.03421v3), Yan et al., 2026-08-13v3预印本；摘要、任务构造与结构段 | 在部分观测物体移动任务中对照诚实/欺骗信息，追踪证词采纳、来源谱系与退出后影响 | 已研究错误证据如何变成集体错误，不能说传播和溯源无人做过；特定五人事实恢复任务不同于开放长程工具执行 |
| [DRNOISE: Benchmarking Deep Research Agents in Misleading Evidence Environments](https://arxiv.org/abs/2607.17291v2), Nie et al., 2026-10-11v2预印本；原始摘要/版本 | 两条支持正确答案的间接记录链，与一份直接声称错误答案的可信外观假文档配对 | 直接覆盖外部错误材料和答案恢复，但不是专门的多Agent协作框架；从单体换多人不自动是方法贡献 |
| [MisinfoBench: A Multi-Dimensional Benchmark for Evaluating LLMs' Resilience to Misinformation](https://aclanthology.org/2025.findings-emnlp.540/), Yang et al., Findings EMNLP2025；官方摘要 | 多轮误导信息、辨识/抵抗/原则拒绝与强制错误前提 | 用户输入/错误前提鲁棒性已有单LLM工作，不应混写为多Agent新发现 |
| [AgentAsk: Multi-Agent Systems Need to Ask](https://aclanthology.org/2026.acl-long.1294/), ACL2026；官方摘要及既有v2方法核查 | 控制是否澄清、问谁、问什么，处理交接的信息和能力问题 | 不能只加一个追问或审查角色就主张新纠错机制；源头无法提供可靠证据时澄清也有边界 |
| [Which Agent Causes Task Failures and When? On Automated Failure Attribution of LLM Multi-Agent Systems](https://proceedings.mlr.press/v267/zhang25cq.html), Zhang et al., ICML2025；官方摘要 | Who&When失败日志和成员/步骤归因方法 | 已研究错误在哪里；离线归因准确不等于执行中发现并恢复，标签亦非无条件因果真值 |
| [Robust Multi-Agent LLMs under Byzantine Faults](https://arxiv.org/abs/2605.09076v3), 2026v3，作者声明EMNLP2026接收；原始摘要/既有方法核查 | 过滤消息、自锚定共识与鲁棒通信条件 | 若走恶意成员路线需比较，不能把恶意成员和所有普通数据错误混为一谈 |

相邻线索：[Multi-agent Systems for Misinformation Lifecycle: Detection, Correction And Source Identification](https://arxiv.org/abs/2505.17511)，2025，提供角色化事实核查/纠正流程；本轮只核原始页，不用它推断已得到强实证。事实核查新闻真假与在错误材料下完成原任务是不同目标。

## 可深化的问题，而非已通过查新的贡献

可把宽问题表述为“受污染信息下的证据驱动团队协作与任务恢复”。它比只测抗干扰更关注完整工作，但完整闭环本身也有近邻，仍需具体机制。

候选系统循环：发现可疑依据→定位信息来源→选择独立核验或重查→修正主张→撤回/更新受影响产物→继续任务。可能的技术贡献须落在核验选择、来源相关性处理或恢复控制等具体原则上；目前未选定，也未确认其新颖性。来源追踪与下游失效分别要面对TIDE和REVISE，不能包装成已有研究都没做。

例：供应商额度被误报→采购方案和财务预算均采用→执行前由库存/账户核对揭示矛盾。方法要做到的不能只是最后说数字不对，还要修改相应方案并完成剩余可完成工作。此例仅用于说明功能，不是新任务数据或实验结论。

## 有意义的验证应看什么

- 检测准确性与误报：有错能识别，无错不乱改。
- 证据纠正与下游更新：局部文本改对不等于消除团队中的残留错误。
- 最终任务表现：清洁条件、错误条件配对报告；只拒绝全部任务不是一般完成能力。
- 可解性与证据条件：足够可查证据应能恢复，确实不足时合理澄清/保留不确定性；不同条件不可混评分。
- 代价：额外核验、调用、时间、返工；包含检测者和修复者。
- 对照：强单体、同预算独立采样、普通多Agent、检查/质疑方法及与机制最贴近的强近邻。不给某方法额外独立证据却把收益称为协作优势。
- 因果口径：最终答对可能来自模型先验、错误未被采用或任务本身不依赖该信息。需核查干预是否真正触达决策；不能仅凭成功推断已识别并纠错。

## 阅读与下一步

先读Resilience→MAS-FIRE→When Truth Is Distributed，再按外部材料路径读DRNOISE、按方法路径读AgentAsk、按归因路径读Who&When。然后写清已有方法的具体限制与我们拟改变的决策规则；目前不建议仅凭宽描述启动付费实验。

## 检索记录和能力边界

采用research-lit的定向检索方式。复用已有总览笔记，另作两轮以上联网反查：`multi agent LLM incorrect information error detection correction faulty agents benchmark resilience 2025 2026`；`multi agent LLM misinformation false premise evidence correction tools benchmark 2025 2026`；`multi agent LLM fault injection recovery corrupted tool outputs memory 2026`；`Which Agent Causes Task Failures and When ICML 2025`；`multi agent misinformation source lineage correction independent evidence recovery benchmark 2026`；`multi agent erroneous task premise input corruption repair benchmark 2026`。最终引用仅用原始页；二手工具失败案例和未核出版物不当证据。

本机papers/与literature/目录不存在，资料来源是项目已有文献笔记和联网原文；没有宣称覆盖用户所有私人文库。未开展独立外部评审、完整方法查新或实验。当前结论是问题有价值且已有直接先例，不是ABANDON，也不是PROCEED认证。
