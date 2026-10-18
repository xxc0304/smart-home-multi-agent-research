# LLM 多 Agent：组织、任务、拓扑与通信的文献图谱

检索截点：2026-10-18。范围：任务求解型 LLM 多 Agent，兼顾具身协作；不运行实验。本文是总综述的专题证据底稿。16 篇核心方法，另列关键邻接方法与反证。所列“局限”包含本文分析，和作者原文报告明确区分。阅读层级采用：A=原始摘要及元数据；M=阅读原文方法段；E=抽查原文实验设置/结果；不把打开全文页面等同于通读全文。

## 研究问题与分类原则

RQ1：团队由谁组成，任务怎样分解和分配？RQ2：结构在什么时候、根据什么信息改变？RQ3：给定通信边，究竟应传递什么内容、保留哪些上下文？

必须区分五个互相交叉的轴：

| 轴 | 可选项 | 易混淆点 |
|---|---|---|
| 组织与权责 | 固定职能、招聘专家、管理者—执行者、分层团队、对等团队 | 角色提示不等于实际技能互补，也不等于模型异质性 |
| 任务表示 | 对话链、SOP、可执行代码、任务依赖图、有限状态执行 | 任务图的节点是子任务，通信图的节点可能是 Agent、操作或一次调用 |
| 结构适配时机 | 手工设计；离线搜索；逐查询生成；单次执行中反馈调整 | 搜索时改结构，不等于上线执行中改结构 |
| 通信结构 | 谁在何轮向谁发消息；删边/删节点；消息路由 | 稀疏拓扑不自动解决一条消息内部的冗余 |
| 信息表示与生命周期 | 全量文本、结构化工件、状态交接、检索记忆、局部上下文 | 少传消息、短消息、跨任务记忆是三件事 |

## 16 篇核心方法证据卡

### A. 组织模板和角色配置：从人工 SOP 到按任务招聘

**A1. MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework — Hong et al.** [原始版本记录](https://arxiv.org/abs/2308.00352)，[ICLR 2024 正式记录](https://proceedings.iclr.cc/paper_files/paper/2024/hash/6507b115562bb0a305f1958ccc87355a-Abstract-Conference.html)。初稿 2023-08-01；本次方法阅读为 [v7，2024-11-01](https://arxiv.org/html/2308.00352v7)，不是将后续版本日期当录用日期。状态：ICLR 2024；层级 M+E（§3、§4.1）。问题：随意对话造成交接歧义和级联错误。机制：五种软件职能、SOP 顺序、PRD/接口设计等结构化工件、共享消息池与按角色订阅、执行反馈。证据：HumanEval、MBPP 与 SoftwareDev；后者比较实验抽取七项代表任务。局限：软件工程模板主导，不能从此推出其他领域最优组织；pub/sub 解决选择性可见性，不是学得动态通信拓扑。

**A2. ChatDev: Communicative Agents for Software Development — Qian et al.** [ACL 2024 正式记录](https://aclanthology.org/2024.acl-long.810/)，[正式 PDF](https://aclanthology.org/2024.acl-long.810.pdf)。版本：ACL 2024 定稿，pp.15174–15186；状态：ACL 2024 长文；层级 A+M（论文设计/沟通部分抽读，未通读附录）。问题：软件设计、编码、测试流程碎片化。机制：chat chain 把开发划为角色间原子对话，communicative dehallucination 用澄清交流推动交接。证据：软件开发与沟通机制分析。局限：人工流程结构仍很强；“多轮沟通有用”不等于自由对话或全连接沟通最佳。与 A1 相比，核心载体更偏对话，A1 更偏规定格式的文档工件。

**A3. AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation — Wu et al.** [arXiv](https://arxiv.org/abs/2308.08155)，[COLM 2024 正式 PDF](https://openreview.net/attachment?id=BAakY1hNKS&name=pdf)。初稿 2023-08-16；阅读 [v2，2023-10-03](https://arxiv.org/html/2308.08155v2) §2–3；发表状态由正式 PDF/微软研究记录确认，不能沿用早期“under review”。层级 M+E。问题：复用 LLM、人和工具的协作基础设施。机制：conversable agent、统一 send/receive/generate_reply、自动回复、Python 与自然语言联合控制；GroupChatManager 可选择下一发言者。证据：数学、问答、ALFWorld、运筹等六类应用。局限：这是可配置框架，不是一种固定星型架构，也不是默认具备学习最优拓扑的算法；应用实例不能替代架构消融。

**A4. AgentVerse: Facilitating Multi-Agent Collaboration and Exploring Emergent Behaviors — Chen et al.** [arXiv v3，2023-10-23](https://arxiv.org/abs/2308.10848)，[ICLR 2024 正式记录](https://proceedings.iclr.cc/paper_files/paper/2024/hash/578e65cdee35d00c708d4c64bce32971-Abstract-Conference.html)，[正文](https://arxiv.org/html/2308.10848)。初稿 2023-08-21；状态：ICLR 2024；层级 M+E（§2 与实验概览）。问题：预设角色难适配不同目标。机制：Expert Recruitment→Collaborative Decision-Making→Action Execution→Evaluation，recruiter 依据目标生成专家描述，并根据评价反馈调整构成。证据：理解、推理、编码、工具使用及 Minecraft 等案例。局限：专家身份首先是提示描述；其变化不能直接当作真实专业能力提升。A4 的团队组成自适应，与 A3 的可编程发言控制不是同一变量。

### B. 结构发现：离线搜索与逐查询生成

**B1. GPTSwarm: Language Agents as Optimizable Graphs — Zhuge et al.** [ICML 2024 正式记录](https://proceedings.mlr.press/v235/zhuge24a.html)，[arXiv](https://arxiv.org/abs/2402.16823)，[方法](https://arxiv.org/html/2402.16823)。初稿 2024-02-26，v3 2024-08-22；arXiv 最新元数据题名去掉 GPTSwarm 前缀，正式题名如本条。状态：ICML 2024；层级 M+E（§2、benchmark 概览）。机制：Agent 是操作节点构成的计算 DAG，多 Agent 为组合图；优化节点提示与跨 Agent 连边。证据：MMLU、Mini CrossWords、HumanEval、GAIA。局限：图中节点并非都为独立自治 Agent；在本工作 DAG 搜索空间内优化，不等于任意循环/状态协议，也不能统称在线自组织。

**B2. AFlow: Automating Agentic Workflow Generation — Zhang et al.** [ICLR 2025 正式记录](https://proceedings.iclr.cc/paper_files/paper/2025/hash/5492ecbce4439401798dcd2c90be94cd-Abstract-Conference.html)，[v4，2025-04-15 正文](https://arxiv.org/html/2410.10762)。初稿 2024-10-14；状态：ICLR 2025；层级 M+E（§3–5、Algorithm 1）。机制：代码表示调用节点与控制流，MCTS 变体以完整 workflow 为搜索树节点；LLM 改写、运行评分、经验回传；可复用 Ensemble、Review/Revise、Test 等算子。证据：六个推理/代码 benchmark，验证集搜索与测试集评估。局限：依赖任务评分器，搜索成本应单独报告；论文实际简化固定 model/temperature/format，仅搜索提示和代码控制流。其条件分支是发现的程序行为，不意味着每题执行中重新搜索架构。

**B3. Multi-agent Architecture Search via Agentic Supernet (MaAS) — Zhang et al.** [ICML 2025 正式记录](https://proceedings.mlr.press/v267/zhang25bi.html)，[v2，2025-06-09](https://arxiv.org/abs/2502.04180)，[方法 §3](https://arxiv.org/html/2502.04180)。初稿 2025-02-06；状态：ICML 2025；层级 M+E。问题：一个昂贵 workflow 覆盖所有查询会浪费资源。机制：学得 agentic operator 架构分布，controller 按 query 采样子网络，联合优化算子与性能—成本目标。证据：六 benchmark 与跨数据/模型迁移。局限：算子可以包含多个 LLM/工具调用，不能把 supernet 节点数等同 Agent 数。B3 比 B2 多出 query-conditioned 资源分配，但并不因此自动成为逐步骤环境反馈重构。

**B4. Learning to Orchestrate Agents in Natural Language with the Conductor — Nielsen et al.** [原始记录 v5，2026-05-06](https://arxiv.org/abs/2512.04388)，[ICLR 2026 正式 PDF](https://openreview.net/pdf?id=U23A2BUKYt)，[方法 §3](https://arxiv.org/html/2512.04388)。初稿 2025-12-04；状态：ICLR 2026；层级 M+E（§3 与结果概览）。机制：7B Conductor 通过 GRPO 学习，每步生成 subtask、worker id、access list，联合确定分工、模型和前驱消息可见范围；扩展允许自我委派构成递归。证据：LiveCodeBench、GPQA 等推理任务及 agent pool 适配。局限：基础设定先给出整个 workflow，再逐步执行；不要据“动态”一词推断基础版每步都重新规划。其学习对象是编排策略，与 B2 在验证集上搜索单个程序不同。

### C. 执行期协作：选队、状态转移与任务依赖

**C1. A Dynamic LLM-Powered Agent Network for Task-Oriented Agent Collaboration (DyLAN) — Liu et al.** [v2，2024-11-15](https://arxiv.org/abs/2310.02170)，[方法](https://arxiv.org/html/2310.02170v2)。初稿 2023-10-03；原始页面注明 Published in COLM2024；层级 M+E（§3、评测概览）。机制：先经初步试运行，根据反向传播式 peer rating 计算 Agent Importance Score 选队，再以 temporal feed-forward network 求解；执行中去激活低贡献成员并提前停止。证据：代码、决策、通用和算术推理。局限：importance 衡量相对候选池中的试运行贡献，不是能力真值；选队阶段和解题阶段必须分开计费。与 A4 相比，C1 更显式建模跨轮贡献和成员淘汰。

**C2. Improving the Efficiency of Language Agent Teams with Adaptive Task Graphs (LATTE) — Mieczkowski et al.** [v1，2026-05-07](https://arxiv.org/abs/2605.06320)，[方法与实验 §3–5](https://arxiv.org/html/2605.06320v1)。状态：本次仅核实 arXiv 预印本，无已录用主张；层级 M+E。机制：运行中更新子任务依赖 DAG，worker 提议 Discover/Claim/Complete，lead 合并/分配/释放/验证，显式操作前置条件和局部上下文；不是纯去中心化。证据：三个人工构造协作任务，5 人团队、两种基础模型、每条件10次，总300试验。局限：其节点是任务而非 Agent；协议不变量不等于生成内容正确。原文对去中心化基线的准确率差异 p=.16、延迟差异 p=.34，不能说所有对比均显著胜出。

**C3. NeuralFSM: Adaptive Multi-Agent Coordination via Learning Finite-State Execution Policy — Wang et al.** [ACL 2026 定稿](https://aclanthology.org/2026.acl-long.1543/)，[PDF](https://aclanthology.org/2026.acl-long.1543.pdf)。版本：2026-07，pp.33414–33436；状态：ACL 2026 长文；层级 M+E（Figure 2、方法段及成本图抽读，未完整审核全部附录）。机制：finite-state execution、temporal coordination controller 从轨迹学习状态转移和通信权重；训练时图正则、运行时 trust-aware attenuation。证据：数学、代码等 benchmark 和指定攻击设置。局限：依赖训练轨迹及状态表示；攻击下表现不能外推任意恶意代理。它调控下一步状态与路由，分类上应与“先生成整张静态图”区分。

**C4. Organizational Principles Enable Collective Intelligence in Embodied AI (ORCH) — Ji, Hyun, Chen.** [v2，2026-09-20](https://arxiv.org/abs/2609.11737)，[方法与结果](https://arxiv.org/html/2609.11737v2)。初稿 2026-09-10；状态：本次仅核实预印本；层级 M+E（组织层级与闭环执行段、实验概览）。机制：pooled interdependence 对应水平经理并行分工，sequential interdependence 对应垂直经理按阶段推进，可递归组合；上下行汇报与计划反馈。证据：CREW-Wildfire 25任务、最多50异质具身代理、8种 LLM。局限：层级在构造后固定，原文将执行期结构变化留作未来；动态的是计划/阶段/分配，不能称动态拓扑。另有同名 ORCH arXiv:2602.01797（EMA 路由、并行分析后汇总），不是本篇。

### D. 通信与上下文：边、内容和跨任务记忆分别优化

**D1. Cut the Crap: An Economical Communication Pipeline for LLM-based Multi-Agent Systems (AgentPrune) — Zhang et al.** [v1，2024-10-03](https://arxiv.org/abs/2410.02506)，[ICLR 2025 正式记录](https://proceedings.iclr.cc/paper_files/paper/2025/hash/bbc461518c59a2a8d64e70e2c38c4a0e-Abstract-Conference.html)，[正文](https://arxiv.org/html/2410.02506)。状态：ICLR 2025；层级 M+E（图定义、方法概览与实验范围）。机制：把轮内空间边与跨轮时间边纳入时空消息图，学习冗余后一次性剪枝。证据：六 benchmark、token 成本和两类攻击实验。局限：删的是消息通路，不是自动学习每条消息的语义摘要；一次性剪枝不能直接算在线按内容改变拓扑。“恶意消息剪掉后提升”只覆盖给定攻击设置。

**D2. G-Memory: Tracing Hierarchical Memory for Multi-Agent Systems — Zhang et al.** [NeurIPS 2025 正式记录](https://proceedings.neurips.cc/paper_files/paper/2025/hash/136a45cd9b841bf785625709a19c6508-Abstract-Conference.html)，[正式 PDF](https://papers.neurips.cc/paper_files/paper/2025/file/136a45cd9b841bf785625709a19c6508-Paper-Conference.pdf)，arXiv:2506.07398（初稿2025-06-09）。状态：NeurIPS 2025；阅读以正式定稿为准；层级 M+E（§3–5抽读）。机制：interaction/query/insight 三层图，检索相关既往轨迹与经验，向不同角色投影记忆。证据：AutoGen/DyLAN/MacNet，三个基础模型，五 benchmark，覆盖具身、规划、知识推理。局限：跨任务经验管理不同于当前轮消息压缩；增加检索和经验生成开销，不应概括为“必然减少总 token”。需防任务间信息泄漏与失败经验归纳错误，本文未复现审计。

**D3. What Should Agents Say? Action-state Communication for Efficient Multi-Agent Systems (PACT) — Huang, Wu, Zhang.** [v1，2026-06-03](https://arxiv.org/abs/2606.05304)，[方法与实验](https://arxiv.org/html/2606.05304v1)。状态：本次仅核实 arXiv 预印本；层级 M+E（§3–4、设置与结果概览）。机制：将原始输出投影成公开 action/state/result 交接记录；维持上层架构时单独改变消息内容，比较全文、简短生成、结论、摘要、工件等策略。证据：分割证据双人交互与固定四角色流水线、Qwen3 8/14/32B；另迁移 OpenHands/SWE-agent。局限：没有一种简短消息策略在全部设置最优；仅工件会丢失结束信号/证据。其“内容轴”正补充 D1 的“边轴”，不是后者的改名版本。

**D4. Token-Efficient Multi-Agent Collaboration via System One-Guided Computational Division of Labor (S1-MAS) — Zhou et al.** [v1，2026-10-06](https://arxiv.org/abs/2610.08155)，[方法 §3–5](https://arxiv.org/html/2610.08155v1)。状态：截至检索日仅核实预印本；层级 M+E。机制：轻量 controller（Laya）决定检查条件、可行任务和停止，Qwen3-0.6B reader 定位条件相关证据，强 worker 承担开放推理；deterministic compiler 限制可执行任务，任务确定角色与来源。证据：六推理/代码 benchmark，另 WebSRC；GPT-4o 结果三种子。局限：worker 边输入仍为所选来源的完整 response，reader 证据主要服务 controller，因此不应称 worker 消息语义压缩。GPT token 节省不等于全系统 FLOPs/费用等比例下降；需计轻量模型和调度成本。

## 核心之外的必要邻接方法

这些方法补充谱系，但不因数量要求而抬为额外“核心”。

| 方法、准确题名与版本状态 | 本次读到什么 | 作用及边界 |
|---|---|---|
| ADAS, **Automated Design of Agentic Systems**, Hu et al., [arXiv:2408.08435](https://arxiv.org/abs/2408.08435)，[ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/36b7acf6f6010652b3f2a433774a66fe-Abstract-Conference.html) | [原文](https://arxiv.org/html/2408.08435)方法/ARC实验抽读 M+E | meta-agent 写 agent 程序、以不断增长档案及分数引导发现；是 B2/B3 自动设计谱系前驱，但 agentic program 不一定是多人自治协作 |
| MacNet, **Scaling Large Language Model-based Multi-Agent Collaboration**, Qian et al., [v3 2025-03-17](https://arxiv.org/abs/2406.07155)，[ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/66a026c0d17040889b50f0dfa650e5e0-Abstract-Conference.html) | [原文 §2](https://arxiv.org/html/2406.07155)，M+E概览 | 固定DAG、节点与边上角色、拓扑顺序，跨对话仅传播最终工件；应同时列入结构规模与上下文管理。1000+代理并非现实并发自治团队已普遍可用 |
| **AgentDropout: Dynamic Agent Elimination for Token-Efficient and High-Performance LLM-Based Multi-Agent Collaboration**, Wang et al., [ACL 2025 long.1170](https://aclanthology.org/2025.acl-long.1170/) | [PDF](https://aclanthology.org/2025.acl-long.1170.pdf)方法前段 M | 按轮节点/边 dropout，比 D1 多优化成员出现的轮次；“Dynamic”需区分学习好的轮次掩码与逐查询内容触发决策。另有2026 IEEE同名不同副标题论文，不混用 |
| **AgentConductor: Topology Evolution for Multi-Agent Competition-Level Code Generation**, Wang et al., [arXiv:2602.17100](https://arxiv.org/abs/2602.17100)，[ICML 2026 PMLR](https://proceedings.mlr.press/v306/wang26fk.html) | 正式元数据与摘要 A | 代码竞赛领域学习编排/拓扑演进；与 B4 Conductor 是不同论文；本次未精读方法，不能合并其机制或实验数字 |
| **Dynamic Generation of Multi LLM Agents Communication Topologies with Graph Diffusion Models**, [ACL 2026 long.1764](https://aclanthology.org/2026.acl-long.1764/) | 正式元数据与摘要 A | 图扩散生成拓扑，补足生成模型路线；尚未读取训练/测试划分与online属性，不作细节比较 |

## 跨论文综合：哪些演进是真的，哪些是命名造成的错觉

**组织设计不是单线的“固定→动态”。** A1/A2 在任务领域结构已知时编码 SOP；A4/C1 分别通过角色招聘和贡献评估选择成员；C4 根据任务生成组织，却在执行时保留层级。C2 则把未知依赖作为可变任务状态显式维护。它们解决的知识缺口不同：不知道谁适合、不知道任务怎么拆、不知道下一步做什么，不可都归为“动态 topology”。

**结构搜索有三个时间尺度。** B1/B2/ADAS 主要在训练/验证任务上寻找可复用设计；B3 学一个可按 query 选结构的分布，B4 学可写分工与上下文可见范围的编排模型；C1/C2/C3/D4 才各自包含在一条运行轨迹中作成员淘汰、任务发现、状态转移、任务与停止选择。逐查询生成和反馈后调整可以结合，但文献综述应分别标记。

**通信研究至少有三个可组合层。** D1/AgentDropout 限制通路和轮次；A1/D3 约束交接内容；D2 管理跨查询可复用经验。MacNet 的 artifact-only、LATTE 的 scoped context、Conductor 的 access list 进一步说明，上下文工程不是独立附加件，而与任务依赖和权限共同定义。D4 的特征是把协调决策与重型推理解耦，不应简写为“另一个消息剪枝”。

**评价口径应匹配机制。** 选队看候选池与选队成本，图搜索看搜索期总开销与跨任务泛化，运行时协调看反馈延迟和失败恢复，消息方法固定结构与模型以隔离内容收益，跨任务记忆核查经验来源及泄漏。把这些方法的不同 benchmark 分数排成一张绝对排行榜没有因果意义。

## 第二轮反例与适用条件

[**Towards a Science of Scaling Agent Systems**, Kim et al., arXiv:2512.08296v3，2026-04-08](https://arxiv.org/html/2512.08296v3) 是与“规模越大越好”主张对读的必要来源。已读 A+实验概览，细节由总报告评测专题进一步核验：v3 是260配置/六benchmark，而非早期180/四个；比较标准化工具、提示和compute。总体揭示任务可分解性、模型能力、工具开销与组织结构交互，多 Agent 在顺序规划上可明显退化。其架构选择命中率和解释方差是特定评测范围内统计，不能当跨领域定律。与 MacNet 的规模收益不必逻辑矛盾：任务、骨干和预算控制不同，必须先条件化再比较。

[**Why Do Multi-Agent LLM Systems Fail?**, Cemri et al., arXiv:2503.13657](https://arxiv.org/abs/2503.13657) 的原始摘要及检索记录揭示规范/系统设计、代理间错位、验证与终止三组失败。本专题未精读全文，不在此转述其样本量或失败频率。它提示上面的“更灵活结构”仍需可执行协议和验证，结构自由度不自动解决共享目标或完成判定。

## 查询记录与覆盖审计

检索工具：连接的 web search；发现时允许综述、作者网页、代码仓库提示候选，机制与状态回到 arXiv、ACL Anthology、PMLR、ICLR/NeurIPS 正式论文核对。两轮独立视角：先主流组织/搜索脉络，再近期/反例/信息表示补缺；不是仅搜索最初给定候选。

| 轮次 | 实际检索式（多个查询合并展示） | 结果与决策 |
|---|---|---|
| 1 主流 | `LLM multi agent organization task decomposition role assignment AgentVerse MetaGPT ChatDev AutoGen papers` | 找到组织模板和角色配置主干；回原文读取方法 |
| 1 结构 | `LLM multi agent dynamic topology DyLAN GPTSwarm MacNet paper`；`AgentVerse multi agent collaboration framework arxiv ICLR 2024`；`DyLAN Dynamic LLM Agent Network arxiv` | 对齐角色/Agent/操作/任务节点的不同语义；DyLAN新版题名与旧题名并存 |
| 1 自动设计 | `LLM multi agent architecture search AFLOW ADAS MaAS 2025 2026`；`AFLOW Automated Agentic Workflow Generation ADAS Automated Design Agentic Systems ICLR 2025` | 得到offline搜索、supernet及相邻Flow/AutoMaAS线索；未仅按“动态”一词合类 |
| 1 通信 | `LLM multi agent communication message context pruning AgentPrune AgentDropout paper` | 正式ICLR/ACL记录核对；排除2026同名AgentDropout混淆 |
| 2 新近核验 | `"LATTE" "multi-agent" topology`；`"ORCH" "multi-agent" LLM`；`"NeuralFSM" agent`；`"S1-MAS" agent` | 找到2026原文，确认ORCH同名、固定hierarchy，LATTE任务图及S1决策—证据循环 |
| 2 消息/记忆 | `LLM multi agent communication context compression OPTiMACS MAD-M2 2025 2026 arxiv`；`"G-Memory: Tracing Hierarchical Memory" NeurIPS 2025`；`"Agent Communication" "context" "2026" multi agent arxiv` | 补入PACT/G-Memory，发现latent/KV、M2CL、attention steering等候选 |
| 2 学习编排 | `"LLM" "multi-agent" "topology" "2026" Conductor Self-Organizing`；`"Learning to Orchestrate Agents in Natural Language with the Conductor"` | 补入B4，发现AgentConductor/GTD/Graph-of-Agents，与首轮候选不同 |
| 2 反例 | `multi agent LLM architecture cost matched single agent 2025 scaling agent systems Google 2025`；`"Why Do Multi-Agent LLM Systems Fail" paper 2025`；`"Towards a Science of Scaling Agent Systems" arxiv` | Scaling最新版本核正为260/6；2609.04217页面日期与编号冲突，不采纳 |
| 2 状态复核 | `site.proceedings.iclr.cc "MetaGPT" 2024`；`"AutoGen: Enabling" "COLM" 2024`；`"Scaling Large Language Model-based Multi-Agent Collaboration" site.proceedings.iclr.cc`；`"G-Memory" "2506."` | 纠正旧arXiv评论与正式录用不一致；正式出版状态优先 |

主要覆盖：组织/分工至少 A1–A4；离线/学习结构 B1–B4 与 ADAS；执行期调整 C1–C3、D4；通信信息层 D1–D4 并由 A1/MacNet 支撑。细分支（例如latent通信、扩散图、组织经济学）尚未达到各3篇原文深读，不宣称细分领域穷尽。

## 尚未闭合的检索项及最重要遗漏

1. **latent/KV通信**：检索已发现 [Q-KVComm: Efficient Multi-Agent Communication Via Adaptive KV Cache Compression](https://arxiv.org/abs/2512.17914)、[When Less Latent Leads to Better Relay: Information-Preserving Compression for Latent Multi-Agent LLM Collaboration](https://arxiv.org/abs/2604.13349)、LatCom: Cross-Agent Latent Compression for Efficient Multi-Agent Collaboration（候选编号2609.37017）。前两条是待核原站全文，后一条仅二手发现；不要将这些候选当已验证核心文献。这是本专题最重要机制覆盖缺口，涉及模型可访问性、异构隐藏空间与token成本不可比。
2. **去中心化/自组织与组织经济学**：SelfOrg、Self-Organizing Agent Teams Learn to Reason Together（候选2609.22682）、Proxifield（候选2609.20889）待核原文；当前“动态”证据仍偏集中控制。任务市场、竞价和去中心化共享状态不能由LATTE一个混合框架代替。
3. **图生成及RL编排谱系**：G-Designer、GTD、AgentConductor、Graph-of-Agents、AutoMaAS 已有发现线索，但仅对部分正式摘要核实；不能声称本文系统比较了所有2026方法。Conductor与AgentConductor尤其要分开。
4. **运行时/并发系统**：Flow、Magentic-One、AgentScope及Tressoir涉及模块、调度、进度账本或系统支撑，本次没有按系统论文深读。图上“可并行”不等于实测墙钟并发吞吐。
5. **分配与角色能力证据**：现有核心大量依靠persona、贡献分数或控制器；还需检索预算约束专家路由、能力标定及任务—Agent匹配的因果消融，不能把自动生成角色当作产生真实新能力。
6. **发表状态**：LATTE、PACT、S1-MAS、ORCH仅确认公开预印本；后续录用不能由代码README、转载站或“2026”推断。NeuralFSM以ACL正式记录确认，Conductor以ICLR PDF确认。

## 对研究问题的回答

RQ1 的成熟基础是固定工件化流程与可配置对话；近期方案把未知的分工/依赖显式化为可学习或可修改对象。RQ2 不能用“动态”二分，至少应标注离线搜索、逐查询生成、执行期反馈三个时间尺度。RQ3 的答案也不是“越短越好”：需要把通路、交接充分性与经验复用分开，保留足以让下一步正确执行和终止的信息；PACT和LATTE的条件结果尤其限制了万能压缩或万能动态组织的叙事。
