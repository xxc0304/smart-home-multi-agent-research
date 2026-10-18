# 共同解题、辩论与聚合：LLM 多 Agent 文献分支

检索截止：2026-10-18。本文是总览的独立分支；不覆盖所有组织框架。研究问题：RQ1，多次采样、异质专家和交互分别贡献什么？RQ2，如何将正确少数意见转化成答案，且避免同源错误与专家稀释？RQ3，何时应付出辩论成本，何时停止？

## 范围与阅读标记

三个互相独立的区分必须保留：

1. **同模型多采样**：相同权重重复回答，差异来自随机数或提示。可以有 Agent 实例，却不等于不同知识源。
2. **异质 Agent**：不同模型、工具、专长或私有信息。异质性有可能增加互补证据；模型名称不同不自动意味着错误独立。
3. **训练型集成/协作**：训练 ranker、fuser 或共同更新 Agent。必须把训练数据和训练预算与推理预算分开。

本分支主要研究同一题的候选答案、论证和证据聚合。软件工程里按模块分工后合并代码、研究里不同子题报告的集成，具有依赖、接口与一致性约束，不能直接套用单题多数票结论。开放文本融合也不能仅靠答案字符串投票。

阅读层级：L1=已读原始摘要与元数据；L2=已读原始正文的相关机制/实验/限制段落，非声称逐字通读；L3=复现，本次没有 L3。会议状态取出版社正式记录；仅 arXiv 作者声明的接收状态会注明。以下 17 篇均核对 primary 来源，未将搜索结果摘要当作最终引用来源。

## 核心证据卡

### A1. Self-Consistency Improves Chain of Thought Reasoning in Language Models

- Primary：[arXiv:2203.11171v4](https://arxiv.org/abs/2203.11171v4)。2023-03-07 camera-ready；ICLR 2023。L1。
- 机制：同一模型采样多条推理路径，边缘化路径后选最一致答案；没有 Agent 间交互。
- 证据：算术和常识推理多个基准上优于 greedy CoT。意义是建立强的采样聚合对照，而非证明社会互动有效。
- 边界：答案须可规范化；系统性相同错误不会因更多重复而消失。报告提升依赖当时模型与任务。

### A2. Improving Factuality and Reasoning in Language Models through Multiagent Debate

- Primary：[ICML 2024 正式版](https://proceedings.mlr.press/v235/du24e.html)；初版 arXiv:2305.14325，2023。L1。
- 机制：多个模型实例先独立答，再读同伴答案和推理，逐轮修订形成最终答案；不要求每个实例为不同模型。
- 证据：建立训练外多轮讨论提升数学、策略与事实回答的早期实证路线。
- 边界：优于单次回答不等于优于同预算 self-consistency；更多轮数在原研究部分设置有效，不能推广成轮数单调增益。

### A3. LLM-Blender: Ensembling Large Language Models with Pairwise Ranking and Generative Fusion

- Primary：[arXiv:2306.02561v3](https://arxiv.org/abs/2306.02561v3)，2023-06-30；ACL 2023 main，元数据注明。L1。
- 机制：PairRanker 学习成对比较候选，GenFuser 融合高排名候选。属于异质 LLM 输出的**训练型排序与生成融合**，不是多轮辩论。
- 证据：MixInstruct 等显示例题级最佳模型不同，选择和融合可超过固定单模型。
- 边界：与 ChatGPT 排名相关不等于事实真实性；ranker/fuser 训练数据、评判偏好和训练成本必须单列。

### A4. ReConcile: Round-Table Conference Improves Reasoning via Consensus among Diverse LLMs

- Primary：[ACL 2024 正式版](https://aclanthology.org/2024.acl-long.381/)，2024-08；arXiv 起源2023。L1。
- 机制：真正 multi-model；讨论提示包含分组答案、解释、置信度与人类修正示例，最后置信度加权投票。
- 证据：七推理基准；消融支持跨模型多样性的重要性，并可加入领域模型。
- 边界：同时改变模型池、提示、讨论和聚合，不能把全部增益归因于辩论；自报置信度也不天然跨模型可比。

### A5. More Agents Is All You Need

- Primary：[arXiv:2402.05120v2](https://arxiv.org/abs/2402.05120v2)，2024-10-11；TMLR 2024。L1。
- 机制：Agent Forest，sampling-and-voting，可叠加其他方法；核心不依赖相互通信。
- 证据：多基准发现增加实例数量可带来性能提升，受任务难度等因素调节。
- 边界：应归入多采样集成基线。标题不是“任意任务无限加 Agent 都有效”的规律，也不证明分工协作收益。

### A6. Mixture-of-Agents Enhances Large Language Model Capabilities

- Primary：[ICLR 2025 正式版](https://proceedings.iclr.cc/paper_files/paper/2025/hash/5434be94e82c54327bb9dcaf7fca52b6-Abstract-Conference.html)；[arXiv:2406.04692v1](https://arxiv.org/abs/2406.04692v1)，2024-06-07为初版。L1。
- 机制：层状异质 LLM，后一层将前一层所有回答作为辅助上下文，最终生成综合答案；推理时组合，不是参数级 MoE。
- 证据：AlpacaEval 2.0、MT-Bench、FLASK 上显示开放回答综合收益。
- 边界：主要是偏好/回答质量证据，不能直接等同精确推理或事实核验；层数增加带来上下文、成本与延迟开销。

### A7. Voting or Consensus? Decision-Making in Multi-Agent Debate

- Primary：[Findings ACL 2025 正式版](https://aclanthology.org/2025.findings-acl.606/)，2025-07。L1。
- 机制：控制其他讨论参数，比较七种决策协议；提出 All-Agents Drafting、Collective Improvement。
- 证据：推理任务更适合 voting，知识任务部分更适合 consensus；论文发现投票前更多讨论轮数可能降低性能。
- 边界：是协议与任务类型的条件性差异，不支持“投票总优”或“共识总优”；原文13.2%等指标不可脱离其统计定义跨论文比较。

### A8. Debate or Vote: Which Yields Better Decisions in Multi-Agent Large Language Models?

- Primary：[arXiv:2508.17536v2](https://arxiv.org/abs/2508.17536v2)，2025-10-23；[NeurIPS 2025 正式记录](https://proceedings.neurips.cc/paper_files/paper/2025/hash/934252acd87f254d5d4672fbde283bd2-Abstract-Conference.html)，Spotlight。L2：正文理论§4、附录D与实验解释。
- 机制/证据：拆开独立采样投票与交互；七 NLP 基准中多数收益可由投票解释。
- 边界：martingale 是 Dirichlet-categorical 更新模型下的条件结果；同质全连接是充分情形，另有异质集体信念条件。它约束信念期望，**不是最终 majority-vote accuracy 恒定定理，更不是所有辩论不可能有益**。oracle 锁定正确答案只是机制干预，不是可部署算法。

### A9. Talk Isn't Always Cheap: Understanding Failure Modes in Multi-Agent Debate

- Primary：[arXiv:2509.05396v2](https://arxiv.org/abs/2509.05396v2)，2025-10-13；元数据为 ICML MAS Workshop 2025，不能称 ICML main。L1。
- 机制/证据：研究强弱模型混合后的改答案轨迹；即使强模型占多数，交流也可能造成 correct→incorrect，性能随轮数下降。
- 边界：说明异质性不会自动转成互补收益，错误论证的说服力可能压过能力；并非证明所有异质组合均有害。

### A10. MAPoRL: Multi-Agent Post-Co-Training for Collaborative Large Language Models with Reinforcement Learning

- Primary：[ACL 2025 正式版](https://aclanthology.org/2025.acl-long.1459/)，2025-07。L1。
- 机制：Agent 先独立生成再讨论；verifier 评分作为多 Agent RL 奖励，额外奖励纠正与说服，联合训练合作能力。
- 证据：报告相对于训练前团队的多数据集提升与未见领域泛化，并发现只训练单模型不足以充分改善合作。
- 边界：这是共同训练的协作能力，不应与 frozen LLM 的提示型 MAD 排同一预算榜；收益依赖 verifier 与奖励设计。

### A11. Demystifying Multi-Agent Debate: The Role of Confidence and Diversity

- Primary：[Findings ACL 2026 正式版](https://aclanthology.org/2026.findings-acl.1694/)，2026-07；正文读取采用[arXiv:2601.19921v3](https://arxiv.org/abs/2601.19921v3)，2026-06-03。L2：§3–7，表1、附录入口。
- 机制：同模型候选池从10选5增加答案多样性；另用 GRPO+LoRA 训练数值置信度表达和对同伴置信度的使用。
- 证据：两个7–8B模型、多 QA 基准上若干组合超过 vanilla MAD 与多数票。
- 边界：**只有多样性初始化无训练，置信度方法有训练**；初始化也增加采样预算。表1不是所有变体每列皆胜；置信度正相关是理论改善条件，不能用未校准自报数值替代。

### A12. Multi-Agent Teams Hold Experts Back

- Primary：[arXiv:2602.01011v4](https://arxiv.org/abs/2602.01011v4)，2026-05-28；arXiv 注明 ICML 2026 accepted。L2：§3–4、表2、附录E–G。
- 机制：自组织团队，控制集中/分布专家信息，比较隐藏与告知专家身份；观察 integrative compromise。
- 证据：经典团队任务上存在专家知识被稀释；ML 基准显示未充分回收逐题正确成员的潜力。
- **关键口径**：ML 表2的6.3–41.1% gap 相对 **At Least One Correct（逐题 oracle）**，不是固定最佳模型。告知专家时 GPQA83%高于固定最佳78%；HLE36%高于29%。不可写成“所有团队都不如最佳固定单模型”。每基准只取100题，需看方差与抽样限制。

### A13. Understanding Agent Scaling in LLM-Based Multi-Agent Systems via Diversity

- Primary：[arXiv:2602.03794v1](https://arxiv.org/abs/2602.03794v1)，2026-02-03；未独立确认 venue，预印本。L2：摘要、§1、结构与理论范围说明。
- 机制：用有效信息通道而非原始 Agent 数解释 scaling；提出无标签代理量 K*，考察模型、提示和工具异质性。
- 证据：同质 scaling 边际递减，一些设置2个多样 Agent 可匹配或超过16个同质 Agent。
- 边界：这是特定基准和配置结果；K* 是代理指标，不等于知道真实正确性，也不能推出异质性在任意弱模型混入时都更优。

### A14. EMS: Multi-Agent Voting via Efficient Majority-then-Stopping

- Primary：[arXiv:2604.02863v2](https://arxiv.org/abs/2604.02863v2)，2026-06-13；未确认 venue，预印本。L2：§3、方法概述。
- 机制：历史相似题共识估计 Agent 顺序，逐个调用；领先答案已不可能被剩余票推翻时停止。
- 证据：五基准报告保持完整投票准确率，同时平均调用数减少35%、tokens减少44%。
- 边界：证书保证与**全体预定票的赢家一致**，不是保证答案为真。历史共识不是正确性标签；顺序调用的 tokens 节省也不自动意味着较并行投票更低 wall-clock latency。

### A15. Sequential Consensus for Multi-Agent LLM Debates: A Wald-SPRT compute governor with calibration-based failure detection

- Primary：[arXiv:2605.19193v1](https://arxiv.org/abs/2605.19193v1)，2026-05-18；预印本。L1。
- 机制：judge 给出每轮 consensus 分数，用校准 Beta likelihood 的 SPRT 控制停止/继续/封顶。
- 证据：200道尝试 GSM8K，约3.7倍调用减少，准确率损失2个百分点；MMLU 校准分离度接近零，99.5%封顶且成本增加。
- 边界：小样本、特定模型组合；SPRT错误率保证依赖 i.i.d. 等假设。强项是公开失败域，不能宣称一般统计保障已解决真实相关辩论停止。

### A16. Efficient Multi-Agent Reasoning via Confidence-Guided Adaptive Debate（LASE）

- Primary：[ICML 2026 正式版](https://proceedings.mlr.press/v306/yoa26a.html)，2026-07，PMLR306。L1。
- 机制：Leader-Adaptive Structured Engagement，非对称 leader–supporter 信息流；只在适合纠正的情形展开交互，其他情形用简单聚合。
- 证据：正式摘要报告多推理基准取得接近单 Agent token 成本的多 Agent 级性能，并胜静态辩论/投票效率基线。
- 边界：本次读到正式摘要，未提取模型级表格，不给未经读表的百分比。其价值是**选择性、非对称辩论**的正面对照，不是所有任务都应独立投票。

### A17. When Debate Helps: Proposal Supply and Verification-Aware Readout in Multi-Agent Reasoning

- Primary：[arXiv:2610.04686v1](https://arxiv.org/abs/2610.04686v1)，2026-10-03；预印本，前沿线索。L2：§2–5、Appendix C。
- 机制：拆为提案供给与验证感知 readout；neural-thicket 权重扰动池按互补覆盖选专家，LVD 用候选级验证证据建模读出。
- 证据：Qwen3-4B、OLMo3-7B；固定提案干预、预算对齐和重复随机评估，区分恢复正确少数、初始无正确提案后的新正确、破坏原先正确投票。
- 边界：扰动异质性仍来自同一 backbone；LVD伪计数是解释模型，不是已发现神经网络内部计数器。开放文本语义聚类和跨模型泛化仍受限；尚不能用该新预印本给领域下定论。

## 横向综合：已经做到哪里

| 主要瓶颈 | 已有代表处理 | 必须保留的限制 |
|---|---|---|
| 独立答案是否足够多 | A1/A5 多采样投票 | 不能将采样量收益冒充互动收益 |
| 候选中有没有正确解 | A4异质模型；A11多样初始化；A13有效通道；A17覆盖选择 | 差异多不等于正确互补多；更大候选池有成本 |
| 正确少数如何被采用 | A3排序/融合；A4加权；A10训练纠正；A11置信度使用；A17验证读出 | 说服力、置信度、同伴共识均不等于真值 |
| 多轮是否值得 | A7/A8/A9揭示无增益和损害；A16选择性非对称交互 | 应报告 correction与subversion，且对齐预算 |
| 专家如何被利用 | A12区分识别和利用；A16定向传递 | 固定最佳、逐题oracle、平均成员是三个基准 |
| 何时停止 | A14不可逆转票数；A15序贯校准；A16条件触发 | 保持投票结果、判定有用收敛、保证答案正确是三种不同目标 |

早期 A2 的“讨论提高回答质量”与 A8 的“投票解释主要增益”并不逻辑冲突：二者的对照、模型与预算不同。A7 进一步显示决策协议和任务类型可改变结论。A9说明即使跨模型引入能力差异，理由交换仍可能伤害正确意见；A12把问题从“能否识别专家”推进为“会不会服从真正有用的专家证据”。因此，A4/A6 对异质模型的正面结果不能外推为“加入任意 Agent 即提升”。

到2026年，前沿重心已从单纯堆角色、轮数和人数，转向三个可以拆开测量的对象：**互补提案覆盖、对正确性的选择性读出、按题分配交互预算**。A10/A11表明其中部分能力可以通过训练获得；A16提供正式会议中的选择性交互正面路线；A17提供较新的机制分解。它们是不同证据层次，不应合成一个无条件排行榜。

## “辩论一定胜过投票”的直接反证与正确表述

- A8 是最直接的多基准拆分证据；A7显示增加投票前讨论轮数可能下降；A9提供 correct→incorrect 的交互轨迹。
- 不能将其反转成“辩论必然无效”：A16选择性非对称交互，A10协同训练，以及A11经过训练的置信度使用，均在不同条件下报告收益。
- 合理判断是：**有益互动需要引入超出重复计票的纠错信号，且被回收的正确意见必须超过互动破坏的正确答案。**A17把这一点做成显式收益分解；这也解释只看最终准确率会遗漏机制。

## 未解决的问题与研究机会

1. **无真值时识别有用多样性**：不同答案可能只是多种错误。无标签共识历史、K*或聚类覆盖是代理信号，尚不能可靠替代逐题正确性。
2. **相关性与同源错误**：同 backbone、多提示及权重局部扰动引入的是不同程度的相关分布；对外部知识来源的去重、证据溯源和相关性修正仍不足。
3. **可信验证与专家路由**：需要区分“出现正确答案”“知道谁通常更强”“在当前题识别并保留正确论证”。专家身份告知不解决采用过程中的稀释。
4. **开放产物集成**：多数工作以可归一答案衡量覆盖与恢复；对长报告、证明、跨文件代码，如何维护来源、接口约束、矛盾消解与局部验证仍需另一套评价。
5. **停止与校准迁移**：一致性停止可能锁定共同错误；序贯测试的独立同分布假设会被交互破坏；从一个域校准到另一个域可直接失效。
6. **公平预算**：Agent数、轮数、总tokens、prefill、训练数据、verifier调用、并行wall-clock和金额不是同一个预算。要与最佳单模型、多采样投票、相同finalizer直接读初始提案，以及工具增强单Agent共同对照。

以上机会是跨文献推断，不是声称已被某篇论文证明的开放问题排名。

## 检索记录与核验边界

执行两轮以上检索，工具为联网 search_service；最终引用只落到 arXiv、ACL Anthology、PMLR、NeurIPS proceedings 原始页。检索过程中出现的二手聚合、博客、Reddit仅用于发现关键词，不作为证据。

| 轮次/视角 | 实际查询字符串（合并展示） | 后续动作 |
|---|---|---|
| 1 主流共同推理 | `multi agent debate majority vote does not improve reasoning 2025 2026 arxiv`; `ReConcile round-table conference multi agent consensus reasoning arxiv`; `Mixture of Agents LLM Blender Agent Forest arxiv` | 找到ReConcile/MoA/Blender和debate-vote分歧，打开primary |
| 2 奠基/反证 | `site.arxiv.org "More Agents Is All You Need"`; `site.arxiv.org "Improving Factuality and Reasoning" "Debate"`; `site.arxiv.org multi agent debate 2025 expert minority conformity` | 核对AgentForest、Du、Talk Isn't Always Cheap |
| 2 停止/最新 | `site.arxiv.org multi agent debate 2026 expert dilution stopping early budget`; `site.arxiv.org "multi-agent" "stopping" "2026"` | 找到EMS/SPRT/HCP/ARMOR等，选择前两者作不同停止机制对照 |
| 3 专家/训练补盲 | `site.arxiv.org multi agent "expert" "dilution"`; `site.arxiv.org "self-consistency improves chain"`; `site.aclanthology.org "multi-agent" "MAPoRL"` | 打开2602.01011全文核对表2；确认MAPoRL训练机制 |
| 3 定向核验 | 直接打开2601.19921v3、2602.03794v1、2610.04686v1 HTML；接收主调查补充的LASE正式链接 | 发现置信度分支需要训练；校正专家gap的oracle口径；将10月论文限制为前沿线索 |
| 4 venue补核 | `"Mixture-of-Agents Enhances" "ICLR 2025"`; `"Understanding Agent Scaling" "ICML" 2026`; `"Demystifying Multi-Agent Debate" accepted conference 2026` | 正式proceedings确认MoA为ICLR2025、DMAD为Findings ACL2026；未以作者主页检索片段认定Scaling的venue |

为控制核心数，未纳入候选 Free-MAD、DynaDebate、HCP-MAD、ARMOR-MAD、graph topology、ChatEval 的独立证据卡；不据此断言这些分支缺乏工作。训练与停止仍是重点补充方向。本次未下载/运行代码，未复现实验，L1卡不承担超过原始摘要的细粒度数值主张。
