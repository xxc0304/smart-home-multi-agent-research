# 如何把团队收益归因到成员互补：证据与配对干预

核验日期：2026-10-18。范围：定向核验六篇 primary sources；未运行实验。下文把论文已有证据与建议实验明确区分。

## 1. 六篇原始文献及其证据边界

| 文献（已核验原文） | 对本课题有用的证据 | 不能据此声称什么 |
|---|---|---|
| Pappu et al., **Self-Organizing Agent Teams Learn to Reason Together**, arXiv:2609.22682v1, 2026-09-19；[原文](https://arxiv.org/html/2609.22682v1) §2–4、Appendix D | SAT离线搜索组织策略并冻结策略bank；包含同模型linearization、homogeneous team、独立答案routing oracle；明确承认胜过linearization同时可能反映交互与模型异质性。 | 胜过有限独立样本oracle，不代表胜过任何可能独立推理；案例中的补步骤链条不能代替随机干预。 |
| Zhao et al., **When Debate Helps: Proposal Supply and Verification-Aware Readout in Multi-Agent Reasoning**, arXiv:2610.04686v1, 2026-10-03；[原文](https://arxiv.org/html/2610.04686v1) §5、A.3、A.10 | 固定proposal后替换证据，含答案剥离、等长正确/错误理由；同一finalizer读初始proposal与后续轮状态。支持分开测量proposal供给与读出转化。 | LVD是accounting model，不是已观测内部计数器；证据干预影响读出不等于整条自然团队轨迹的纯中介效应。 |
| Choi, Zhu & Li, **Debate or Vote: Which Yields Better Decisions in Multi-Agent Large Language Models?**, NeurIPS 2025；[正式论文页](https://proceedings.neurips.cc/paper_files/paper/2025/hash/934252acd87f254d5d4672fbde283bd2-Abstract-Conference.html) | 七个NLP benchmark中多数收益可由majority voting解释，使独立采样投票成为必备基线。 | martingale结论有其模型假设；不能推广成“任何交互都不可能帮助”。 |
| Zhu et al., **MultiAgentBench: Evaluating the Collaboration and Competition of LLM agents**, ACL 2025；[正式论文页](https://aclanthology.org/2025.acl-long.421/)、[官方代码](https://github.com/ulab-uiuc/MARBLE) | 除任务成功率，还用milestone指标；比较star、chain、tree、graph等拓扑，适合作为协作过程和架构覆盖依据。 | milestone完成/拓扑排名本身不能排除多计算、更多信息或最终writer能力。 |
| Kim et al., **Towards a Science of Scaling Agent Systems**, arXiv:2512.08296v3, revised 2026-04-08；[原文摘要](https://arxiv.org/abs/2512.08296) | 260配置、六个agentic benchmark、五种架构、三模型族；标准化工具、prompt及compute，支持把任务性质与架构共同控制。 | 跨配置预测和相关模式不能替代针对具体贡献的因果干预；最新v3统计与初版报道应分开。 |
| Wang et al., **Mixture-of-Agents Enhances Large Language Model Capabilities**, arXiv:2406.04692v1, 2024-06-07；[原文](https://arxiv.org/abs/2406.04692) | 多层agent将上一层输出作为辅助输入；适合作为“多proposal经强模型聚合”架构对照。 | 聚合提升不自动证明相互修复；原论文的模型/数据集结果不能直接当作本设置的预期效应。 |

## 2. SAT到底学了什么？baseline分层

这里的SAT是 **Self-Organizing Agent Teams**，不是另一篇同缩写的 **Sequential Agent Tuning**（2605.05216）。前者 §2 将学习对象定义为角色prompt、参与集合、轮数、信息流和phase顺序；由固定成员反思历史执行，提议策略，评估后冻结最多十个策略。其 §6 明确归入non-weight artifacts的reflective search。故应写“无权重微调、但有离线学习/搜索和训练题标签”，不能笼统称“完全无需训练”。每题部署执行策略bank并由judge选择，因此不仅有组织变量，也有多策略推理与选择成本。[SAT §2、§6](https://arxiv.org/html/2609.22682v1)

**When Debate Helps** A.3明确说不train/fine-tune backbone；但其agent由预训练权重小扰动形成，并离线profile和选择pool。严格主比“冻结原始权重、无离线数据优化的架构”时，完整方法应放扩展组；其fixed-proposal干预和same-finalizer方法可直接借鉴。[WDH §1、A.3](https://arxiv.org/html/2610.04686v1)

建议分三层报告，不混成一个冠军表：

1. **主比较：无需离线学习的架构。** 同一backbone roster/固定prompt，单模型直接答、预算匹配单模型反思/采样投票、独立成员proposal→同一finalizer、静态debate、静态MoA、chain/star/tree等所选代表。不必把所有框架包都列入；按信息流覆盖即可。
2. **机制控制。** 同一策略的homogeneous team、单模型linearization、禁止peer信息的相同调用数、等长伪消息、贡献内容干预。这组服务归因，不作为新方法排行榜。
3. **离线优化扩展。** SAT策略搜索、coverage-selected agents等，单列搜索数据、标签访问、搜索预算、超参选择和权重是否变化。可另给所有方法相同离线调参budget的公平版本。

## 3. 建议的最小配对干预矩阵

所有条件在同一题、同一预先采样proposal、同一finalizer版本/prompt、相同可见题目信息下配对。随机化干预分配并重复采样；“同seed”有助于减少方差，但不能保证不同prompt共享相同潜在随机轨迹。

| 控制/干预 | 具体实现 | 能支持的结论 | 仍需防止的替代解释 |
|---|---|---|---|
| 独立proposal → same finalizer | 冻结R0成员proposal；让团队的同一finalizer读R0，对比读交互后消息；另给非交互支路等预算独立续写/反思 | 后续交互状态相对直接聚合提供额外价值 | R0支路调用更少时仍混有多计算；长上下文差异也需预算或长度敏感性分析 |
| Finalizer题目单独重解 | 只给题，或给等长度中性材料；同一模型相同输出budget | 量化finalizer独立求解可解释的收益 | “请勿重解”只是指令，不是行为保证；正确答案不同也不能直接证明引用了成员 |
| 真实贡献删除 vs 等长替换 | 预先定义信息单元（引理、错误定位、约束、反例）；在接收节点用等长无关/冗余文本替换；与直接删除都做 | 特定可见内容对该接收节点及后续结果有可测影响 | 删除同时改变长度、显著性与连贯性；不等同自然间接效应。不要只挑最终成功例来定义贡献 |
| 正确贡献 → 匹配错误贡献 | 保持格式、长度、角色身份、结论字符串暴露尽量一致；改变关键推理步骤；可另剥离最终答案 | 检验系统是否对证据正确性敏感，是否真正检查而非跟随权威 | 错误替换可能更不自然/更难；需独立审核流畅度，报告损害和恢复而不只报净收益 |
| 同题冗余贡献/跨题理由替换 | 用同题无新增信息消息和跨题等长理由分别替换 | 区分“更多文字/更多赞同”与题目相关的新信息 | 跨题文本太明显，效应也可能是困惑；同题冗余对照更接近自然分布 |
| 消息顺序/身份扰乱 | 对可交换的同轮独立消息随机排序；身份标签打乱另作为独立因子 | 检查顺序、身份锚定与内容依赖 | 把后续修复置于其所修复错误前会破坏因果依赖；这不能称纯顺序效应。保留DAG依赖的合法排序最干净 |
| Homogeneous team | 同一backbone占据所有成员，保留角色、独立上下文、拓扑与budget | 异质成员是否提供超出多实例的价值 | 性能差异同时包含不同模型能力/价格；要匹配成本并列强模型版本 |
| 单模型linearization | 一模型按相同角色/phase依次调用并读先前输出；记录独立上下文与共享上下文两个版本 | 单个模型能否在同一组织结构和预算下复制收益 | 与异质团队的差异不是纯交互效应；能力、上下文隔离、并行顺序仍不同 |
| 成员leave-one-out | 整个成员移除，分别用空位、等调用同模型、替补成员填位 | 系统对该成员/槽位的依赖与冗余 | 改变了计算、角色覆盖和组织适配；重新运行的总效果不等于原自然轨迹上“该成员的纯贡献” |

若要支持“互补”，最有说服力的联合证据是：交互胜过同预算独立proposal+同finalizer；真实有用内容的匹配替换导致损害；合法依赖链上观察到接收者修复；同模型重复不能复制全部收益。任何单一消融都不足以独立承担完整归因。

## 4. 指标与可宣称结论

建议按初始proposal correctness分层，同时报告：初始coverage、vote accuracy、正确少数被恢复率、原来正确被破坏率、初始全错后来正确率、最终accuracy及成本。这避免把“已有正确答案被识别”与“出现新正确解”混为一谈。初始全错→最终正确依然可能来自finalizer重解或额外采样，需要上述控制。

Routing oracle严格定义为 **对指定有限独立样本集合的完美选择coverage**；它是该集合上纯选择器的上限，不是独立推理、更多采样或所有单agent系统的绝对上限。团队超过它可证明输出不只是从该集合中挑出正确项，不能独立证明语义互补。增加相同成本独立样本后oracle会变；应给coverage–budget曲线。

配对统计以题目为基本单位，重复seed应保留题目聚类；预注册主对比并报告置信区间。证据干预若按最终成功挑选，只能称成功案例条件分析；应对完整预定样本或预先定义的mixed-proposal子集报告，并说明目标总体。

## 5. 成本核算与最终措辞

离线成本单独报告：策略/架构搜索调用、候选验证、标签和训练题数量、pool profiling、失败搜索、GPU时数/费用；“未更新权重”不等于这项成本为零。推理成本逐题报告所有成员、重试、通信摘要、judge的输入/输出及可得的reasoning tokens、LLM calls、工具成本、时延；跨模型再给货币成本与硬件条件。相同token不保证相同FLOPs或价格，主比较选一种预算约束，其他口径做敏感性分析。

可报告摊销成本 `C_total(N)=C_offline+N·C_inference`，同时展示原始offline与每题inference，不能只给一个任意N的摊销数字。

主张建议：“在固定成员与预算、共享finalizer的配对条件下，交互提供超出独立候选聚合的收益；匹配证据干预表明部分收益依赖成员提供的正确且非冗余信息。” 只有完成这些实验后才使用这句话；本文件是设计依据，没有新增实证结果。
