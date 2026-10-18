# 从人类团队到 Agent 框架：组织有效性的来源、已有实现与可深化空间

日期：2026-10-17（Asia/Shanghai）。状态：文献调查和方法构思，未确定新算法、未启动实验。

当前复核与阅读优先级见 [RESEARCH_REVIEW_20261017.md](C:/Users/QVQ/Documents/ChatGPT/agent-research/RESEARCH_REVIEW_20261017.md)：补查队友建模、团队学习与自适应控制近邻，明确本报告是方向地图，并非方法级查新通过。

后续定向查新见 [UNTAPPED_SYNTHESIS.md](C:/Users/QVQ/Documents/ChatGPT/agent-research/research/human-team-agent-frameworks-20261017/UNTAPPED_SYNTHESIS.md)：补查了关系协调、交叉训练、多团队边界、双环学习和治理机制，新增 AgentAsk、DLMA 等直接近邻；不能据本报告中的构思措辞声称这些理论未被迁移。

## 摘要

本轮调查人类团队与社会组织的协作机制，回答三个问题：哪些机制具有理论或实证依据；哪些已被 LLM 多 Agent 系统实现；哪些问题适合继续构思有广泛意义的方法框架。调查同时覆盖团队科学、现代 Agent 框架与反证，并补查传统分布式人工智能、市场与制度协调。交叉证据支持把组织设计视为独立于成员能力的重要方法来源，但不支持单凭社会类比、更多角色或更多讨论获得收益。现有工作已实现标准流程、动态招募、任务依赖组织、交互记忆、结构化异议、责任配置及合同式委托。更有价值的构思方向，是在共同任务状态、差异化能力与证据、可执行责任之间建立有条件的协调规则，并在变化发生时维持这些关系。本文保留三条框架构思路线及其直接竞争方法；它们是进一步精读和设计的依据，不是查新通过的贡献声明。

## 1. 想从人类团队借鉴什么

本轮不把智慧家庭、专家投票或 benchmark 作为既定边界。研究对象是多个具备语言推理、工具或资料访问能力的 Agent 如何共同完成任务，关注最终质量、资源开销和完成效率。用户要求先充分阅读和思考，因此本轮没有实现、模拟验证或付费模型采样。

- **RQ1：**人类协作有哪些可解释、可操作的机制，各自解决什么问题、在什么条件下失效？
- **RQ2：**已有 Agent 系统把其中哪些内容落实为程序、信息可见性、状态、权限或学习规则？
- **RQ3：**怎样据此构思有实质改进空间的框架，而不是给已有模块换社会学名称？

首先区分研究目标。事实和代码任务要求结果正确；多方偏好任务要求满足约束、体现不同利益；协同执行还要求产物和行动可衔接。ReConcile 的答案共识与 TeamFusion 的偏好代表性并非同一目标；不能把“所有人同意”同时当作正确性、公平性和执行完成。[ReConcile](https://aclanthology.org/2024.acl-long.381/)、[TeamFusion](https://aclanthology.org/2026.acl-long.657/)

## 2. 检索方法与证据边界

三路独立检索分别覆盖人类团队科学、直接 Agent 框架先例、反证与条件；主执行者补查组织信息处理、历史制度、市场、经典共同计划和近期动态任务图。先按机制搜索，再沿发现的方法和引用链回到原始论文。专题材料分别为 [HUMAN_SCIENCE.md](C:/Users/QVQ/Documents/ChatGPT/agent-research/research/human-team-agent-frameworks-20261017/HUMAN_SCIENCE.md)、[AGENT_PRIOR.md](C:/Users/QVQ/Documents/ChatGPT/agent-research/research/human-team-agent-frameworks-20261017/AGENT_PRIOR.md)、[COUNTEREVIDENCE.md](C:/Users/QVQ/Documents/ChatGPT/agent-research/research/human-team-agent-frameworks-20261017/COUNTEREVIDENCE.md)。

人类专题核对 19 篇必要研究；框架专题比较 17 个直接框架/方法和 2 项校准研究；反证专题另列 15 项核心来源及补充。这些材料有交叉，不能相加当作去重文献总数。主执行者对核心新近邻再次打开摘要或方法正文，并补查 ORCH、LATTE、Intelligent AI Delegation、传统团队计划等来源。

| 证据类型 | 可以支持什么 | 不能直接支持什么 |
|---|---|---|
| 人类受控实验 | 给定任务中某种信息或流程干预的影响 | 相同机制在 LLM 上必然有效 |
| 人类组织/纵向研究 | 情境、协作过程与结果的关系 | 自动识别所有因果路径 |
| 理论与元分析 | 机制构念、跨研究趋势及边界 | 每个组件独立有效、所有情境同样有效 |
| Agent 方法实验 | 所测任务、模型与对照下的收益 | 广泛部署效果或普遍最优组织 |
| 形式/协议提案 | 状态、权限和约束的表达及部分保证 | 自动保证语义正确或更高成功率 |
| 诊断研究 | 某类失败及发生条件 | 未干预就确定完整根因或证明解法有效 |

旧论文有部分只能读取作者/机构摘要或原始摘要索引，专题材料明确访问层级。现代核心近邻核对方法或局限段落；不同版本的标题和数字不混用。这是有针对性的跨学科调查，不是穷尽数据库的系统综述，也没有用检索未命中来证明无人研究。

## 3. 先看控制对象，再看社会形式

以下按框架需要改变的控制对象划分设计维度。一篇论文可以同时控制多个维度，不能强行给它唯一“社会类型”。

| 控制对象 | 人类协作机制 | Agent 中应真正改变什么 | 代表先例 |
|---|---|---|---|
| 工作边界与成员 | 专业分工、项目组、模块化 | 子任务边界、能力匹配、招募退出及依赖 | MetaGPT、Captain Agent、AgentInit、ORCH |
| 信息与共同状态 | 共享任务理解、交互记忆、公共工作板 | 谁看到什么、谁知道什么、当前状态与证据来源 | Magentic-One、CoThinker、MATM、LATTE |
| 判断与决策权 | 结构化审议、异议、同行评审、专业权威 | 独立判断、检查对象、采纳和否决、停止规则 | ReConcile、TeamFusion、Catfish、AgentAuditor |
| 承诺与行动接口 | 标准流程、授权、复诵确认、交接、备援 | 可执行验收、责任继承、通知、打断、重新分配 | STEAM、Agent Contracts、LATTE、Magentic-One |
| 组织规则的更新 | 团队复盘、交叉训练、组织学习 | 修改协作规则并限定适用条件 | Organized Teams、LIET、协作训练方法 |

市场与制度是跨维度的组织方式：竞标同时改变成员分配和利益信息；分权制衡同时改变决策权、检查和执行路径。新增社会名称不对应新增控制量，就很难解释它为什么有效。还需要区分模拟社会行为、帮助人类团队协商、提升自主 Agent 任务表现三种研究；对其中一个有效，不能自动代替另两个的效果证据。

## 4. 任务结构决定需要多少组织

Galbraith 的信息处理理论区分两条路：减少跨单元的信息处理需求，或增加组织处理信息的能力；Sanchez–Mahoney 的模块化理论强调接口也可承载协调。与之相对，hidden-profile 研究处理的是独有信息未进入讨论。因此“需要更多讨论”和“应该通过接口减少讨论”可以分别正确，取决于失败来自哪里。[Galbraith](https://pubsonline.informs.org/doi/10.1287/inte.4.3.28)、[Sanchez–Mahoney](https://experts.illinois.edu/en/publications/modularity-flexibility-and-knowledge-management-in-product-and-or-2/)、[Stasser–Titus](https://www.uni-muenster.de/imperia/md/content/psyifp/aeechterhoff/vorlesungkommunikation/stasser_titus_unsharedinfogroupdisc_jpsp1985.pdf)

Agent 方法已在不同层级实现这些思想：MetaGPT 规范软件产物交接，ORCH 将可并行工作和前后依赖组合成任务专属层级，LATTE 让团队运行中共同维护可更新任务图。三者分别强调预设接口、初始组织构造、运行中协调状态，不能统称为“固定多 Agent 讨论”。[MetaGPT](https://arxiv.org/html/2308.00352v6)、[ORCH v2](https://arxiv.org/html/2609.11737v2)、[LATTE](https://arxiv.org/html/2605.06320v1)

ORCH 是本轮贴近用户想法的正面案例：其 25 个野火任务包含异质工种和较大团队，报告组织原则带来的表现与效率收益；但组织树构造后保持为执行支架，改变的是计划、阶段和分派。LATTE 已允许运行时发现、认领、释放和核验任务。因此，不能看到 ORCH 的 future work 就把“运行时动态组织”直接宣布为新方向，必须面对 LATTE、动态招募和架构搜索等近邻。

MaAS 学习查询相关的架构分布，IMACS 将角色、协调和协议解耦，并学习任务级协议路由；它们说明任务匹配与组织选择已有直接方法。两者证据强度不同：IMACS 的主要路由结果依赖合成 oracle，真实模型样本较小；接口解耦也不等于角色和协议在效果上独立。[MaAS](https://proceedings.mlr.press/v267/zhang25bi.html)、[IMACS](https://arxiv.org/html/2607.25446v1)

对应的宽泛机会是组织如何依据工作需求和运行反馈改变，而非单纯比较星形或全连接。方法贡献必须说明相对已有系统新增的状态、决策规则或约束保持机制；只换经理角色、改组织图形状或选择现成协议，不会自动建立新意。

## 5. 共同理解与差异化知识可以同时存在

人类 SMM 研究关心共同的任务与互动理解，TMS 研究关心知识如何分布和调用；前者不要求所有人拥有相同专长，后者不等于共享记忆池。Lim–Klein 还区分共同模型的相似性和准确性，说明“大家理解一致”不能替代“理解符合实际”。[Mathieu et al.](https://pubmed.ncbi.nlm.nih.gov/10783543/)、[Lewis](https://pubmed.ncbi.nlm.nih.gov/12940401/)、[Lim–Klein](https://faculty.wharton.upenn.edu/wp-content/uploads/2012/05/Lim_Klein_Team_mental_models_2006.pdf)

这给框架一个设计分离：目标、任务依赖、接口和完成标准需要共同维护；独有证据、探索路径和不确定性不必立即同化。CoThinker 已维护当前团队贡献者、共同知识与未决问题，MATM 则让异质 Agent 重用种群历史轨迹；两者的记忆对象和使用时机不同，不能用“我们也有团队记忆”概括增量。[CoThinker](https://arxiv.org/html/2506.06843v2)、[MATM](https://arxiv.org/html/2606.19911v1)

HiddenBench v4 已把信息分散转成具体任务，并尝试先交换相关事实、提出反对当前领先方案的理由，再汇总决定。它与人类 hidden-profile 证据共同支持研究信息如何进入决策，却同时否定“首次提出先共享事实再投票”的说法。全信息单 Agent 是信息条件参照，不能误写成同信息同预算下单 Agent 必胜。[HiddenBench v4](https://arxiv.org/html/2505.11556v4)

可深化问题包括：能力目录与证据来源怎样更新；过去信誉何时失效；错误路由后谁重新发起取证；怎样区分新证据与同源复述。其用途覆盖研究、编程和数据分析，但至少要与 CoThinker、MATM、能力匹配选队及 [AgentAuditor v2](https://arxiv.org/abs/2602.09341v2) 比较。本轮没有确认“可校准知识分工”无人研究。

## 6. 共识、异议与市场需要不同前提

人类研究发现异议可以促进信息处理，但真实异议与安排假扮反方并不等价；这不意味着 LLM 需要人的主观信念，而是提醒我们检查异议是否带来不同证据或搜索路径。Agent 领域的 Catfish 已按需打破共识，TeamFusion 已做等额发言与偏好整合，Diversity Collapse 也实测了盲写与子群隔离。[Schulz-Hardt et al.](https://www.psych.uni-goettingen.de/de/ecosop/publikationen/publications-folder/pub-schulz-hardt-et-al-2006)、[Nemeth et al.](https://onlinelibrary.wiley.com/doi/abs/10.1002/ejsp.58)、[Catfish](https://arxiv.org/html/2505.21503v1)、[TeamFusion](https://aclanthology.org/2026.acl-long.657/)、[Diversity Collapse](https://aclanthology.org/2026.findings-acl.13/)

这些来源关注的结果不同：研究构思重覆盖和新颖性，事实题重正确性，偏好协商重代表性。探索时保留独立性有价值，不等于执行时应拒绝必要共享；层级对具身任务有益，也不等于对创意生成同样有益。值得构思的是何时交换哪些信息、怎样影响后续行动，不能只设置固定两轮独立、三轮讨论就宣称解决了这个张力。

市场需要另一组前提。Contract Net 早已实现任务公告和竞标，AgentLance 又将公共信誉、私人成本、支付与受约束分包结合；MarketBench 则直接发现模型可能误估自身成功率与成本。现代两项工作并不互相否定：信誉和反馈可能帮助市场运行，缺少可靠私有信息则会破坏分配信号。[Smith](https://cse-robotics.engr.tamu.edu/dshell/cs631/papers/smith80contract.pdf)、[AgentLance](https://arxiv.org/html/2608.23867v1)、[MarketBench](https://arxiv.org/html/2604.23897v1)

同一底模、共同目标、公开信息的封闭团队需要额外解释虚拟货币的必要性；多提供商且能力与成本分散的开放系统中，机制设计的价值更清楚。这是研究对象选择问题，不能因人类市场有效就默认 Agent 投标可信。

## 7. 责任和领导只有改变行动才有意义

人类领导研究支持按事件新颖性和破坏性决定干预，备援研究也记录帮助的机会成本；并非所有成员每一步都需要领导或复核。传统 STEAM 已用共同意图、成员监控、团队重组及选择性通信处理不确定性，SharedPlans 也为共同活动的计划与承诺提供早期形式基础。[Morgeson](https://pubmed.ncbi.nlm.nih.gov/15910145/)、[Barnes et al.](https://ink.library.smu.edu.sg/lkcsb_research/1746/)、[STEAM](https://arxiv.org/abs/cs/9709101)、[SharedPlans](https://dash.harvard.edu/entities/publication/73120378-7e49-6bd4-e053-0100007fdf3b)

现代方法也有直接近邻：Magentic-One 用任务和进展账本触发重规划，Agent Contracts 为 I/O、资源、时间和成功条件建立生命周期，LATTE 将任务认领、完成和释放设为带前后条件的操作。Intelligent AI Delegation 从概念上明确委托涉及权限、责任与验收，但不能当作已证实高性能的系统。[Magentic-One](https://arxiv.org/html/2411.04468v1)、[Agent Contracts v3](https://arxiv.org/html/2601.08815v3)、[LATTE](https://arxiv.org/html/2605.06320v1)、[Intelligent AI Delegation](https://arxiv.org/html/2602.11865v1)

一个正反对照是 TeamMedAgents 与 Maat：前者把多种团队原则落成医疗推理机制，后者用确定性合同核验拦截交接缺陷；但前者没有前瞻临床证据，后者的误报会使有效任务被提前停止。必须评价最终交付和误干预成本，不能把更多核验、更多停止或更少 token 本身当作成功。[TeamMedAgents v3](https://arxiv.org/html/2508.08115v3)、[Maat](https://arxiv.org/abs/2609.34017)

制度层面也有相同限制：SocialSystemArena 已实现七类历史制度及审查/执行路径，不同模型和任务中的排序会变；IMACS 的责任配置只有在程序真正经过相应责任人时才改变输出。两者说明责任必须连接可观察的决策与执行路径，而不只是标签。[When Agents Evolve, Institutions Follow](https://arxiv.org/html/2604.27691v1)、[IMACS](https://arxiv.org/html/2607.25446v1)

## 8. 团队可以学习，但要明确学到什么

人类复盘元分析支持事件导向、多信息源的 debrief 总体有益，边界研究则提示其价值与既有表现和情境有关；这不证明每步复盘最优，也不意味着反思文本就是策略改进。LLM 中，Organized Teams 已通过轨迹与成本反思组织，LIET 已更新共同协作知识和个体行动效用。[Tannenbaum–Cerasoli](https://cebma.org/assets/Uploads/Tannenbaum-Cerasoli.pdf)、[Schippers et al.](https://doi.org/10.1002/job.1784)、[Organized Teams](https://arxiv.org/html/2403.12482v2)、[LIET](https://arxiv.org/html/2506.07232v1)

框架若引入学习，要说明更新的是事实、个人技能、成员能力估计还是协作协议。失败可能来自工具、任务或组织，不能都总结为“下次多沟通”；成功也可能来自容易样本，不能立即固化组织。知识失效与成员变化后的迁移值得研究，但还必须比较持续学习和训练式协作近邻，不能仅依本轮检索宣布新颖。

## 9. 三条值得继续构思的框架路线

以下是综合后的方法假设，尚未完成机制级新颖性确认。不是三套同时实施的项目，也没有要求立刻做实验。

### 9.1 围绕任务变化重新组织，同时保留有效工作的团队

**宽问题：**初始分工可能合理，但新证据、工具失败或任务依赖变化后，局部计划、责任和其他成员预期不再一致。

人类依据是模块化、事件触发领导与备援。候选框架需要共同表示任务依赖、责任、已验收产物和未满足承诺；正常阶段自主并行，变化时识别受影响关系，进行有范围的通知、接管或重分工，保留不受影响的工作。贡献不能只是加图或重规划，而要落在变化判定和协调状态如何持续有效。

**直接近邻：**ORCH 已有依赖组织，LATTE 已有动态图和重分派，Magentic-One 已有进展监控，REVISE 已有按有效性保留、失效和局部恢复。下一阶段必须逐项比较依赖表示、改变决策和交接保证，才知道具体空间。[REVISE](https://arxiv.org/abs/2609.00643v1)

框架广度较好，实现与比较成本较高。现在适合精读，不适合注册“首次动态团队恢复”。

### 9.2 共同掌握任务状态、分别保持证据专长的团队

**宽问题：**同一上下文容易导致重复劳动，完全隔离又容易遗漏关键知识；历史表现也不能保证当前意见正确。

候选框架把共享协调状态与差异化证据/能力分开维护；围绕当前决策缺口定位能提供帮助的成员，让贡献带可追溯证据或检查结果，按实际反馈更新能力与可靠性判断。核心是信息需求和能力匹配如何决定通信及分工，不是给专家固定权重。

**直接近邻：**CoThinker、MATM、AgentInit、HiddenBench 的交换协议和 AgentAuditor。如果只是专家目录、共享历史和加权投票的组合，新意不足；需要新的需求识别、能力失效更新或错误路由修复机制。

它与知识、语言推理及工具使用直接关联，较适合继续构思 ACL 方法论文；“适合”不是对新颖性或录用竞争力的认证。

### 9.3 有选择地监督、协助和接管的团队

**宽问题：**全员全程审查成本高，只靠中心经理又可能漏掉错误和局部瓶颈。

人类依据是 mutual monitoring、backup 和按事件干预。候选框架按错误影响范围、可检查性和空闲能力分配监控，明确提醒、核验、接管及恢复自主的条件，同时计入协助者自己工作的损失。

**直接近邻：**TeamMedAgents 的监控、Magentic-One 的中心控制、LATTE 的 Verify/Release、ECMR 的预算化干预和 STEAM。新加 critic、checklist 或固定审查节点已有很强近邻；需要新的监控分配、触发或有界恢复机制。[ECMR](https://arxiv.org/abs/2610.17869)

它也可成为前两条的控制机制，不必为追求“整套框架”独立扩成另一项目。

### 三条路线的共同要求

可以复用已有模块，论文不需要每个零件都新；但必须有一条统一的方法原则，解释关键组件怎样共同实现已有方案做不好的行为。不能把三个候选全部堆进框架，靠数量宣称贡献；也不能仅因有人研究同一宽问题就淘汰它。比较对象是具体机制、条件和效果。

## 10. 下一阶段先继续读和设计

先做原文对照，暂不做验证实验。按关系精读，而不是无序读完所有文献：

1. **组织怎样产生收益：**Galbraith → ORCH → Towards a Science of Scaling Agent Systems。区分原理、方法与适用边界。
2. **人类原则怎样变成程序：**TeamMedAgents v3 → CoThinker → IMACS。看状态、输入、可执行动作与证据。
3. **协作怎样在运行中改变：**LATTE → Magentic-One → Intelligent AI Delegation；涉及有效工作保留时同时读 REVISE。
4. **什么情况下不该模仿人类：**HiddenBench v4、Diversity Collapse、MarketBench，与前三组交叉对读。

设计交付应是一份机制比较稿：一个宽问题，至多两套有统一原则的框架草图，最近的强方法，确切不同之处，必要信息和资源，最强替代解释。形成这份稿之前，不以小范围 API 试验替代想法成熟。

研究准备不要求先证明方法必胜，而要知道方法改变什么、为什么可能改善、已有工作已做到哪里。有实质区别后，才进入实现和预算讨论。

## 11. 对三个研究问题的回答

**RQ1：**可迁移机制主要围绕工作依赖、共同任务理解、差异化知识、决策影响、责任交接和经验更新。收益存在情境条件，没有证据要求 Agent 完整模拟人的社会动机。

**RQ2：**现代框架已广泛采用这些原则。重要近邻包括 ORCH、LATTE、TeamMedAgents、CoThinker、MATM、IMACS，以及制度和市场方法。传统 STEAM、SharedPlans、Contract Net 也不能漏掉。人类启发不是空白，已有实现与未解决问题可以同时存在。

**RQ3：**值得深化的是组织机制怎样依据任务、信息和成员状态工作，并在变化中维持可靠协作。候选是持续重组、可校准的知识分工和选择性监督接管。本轮没有确认任一候选已构成独立创新，也没有得出应放弃方法路线的结论。

## 参考文献与复核记录

完整题名、作者、年份、证据类型、原始链接和读取层级见三份专题材料。本文额外补查的核心条目如下；原始入口位于正文，预印本不自动视为已同行评审。

1. Ji, Z., Hyun, J., Chen, B. “Organizational Principles Enable Collective Intelligence in Embodied AI.” arXiv:2609.11737, v2, 2026.
2. Mieczkowski, E., Ku, A., Eisape, T., et al. “Improving the Efficiency of Language Agent Teams with Adaptive Task Graphs.” arXiv:2605.06320, v1, 2026.
3. Tomašev, N., Franklin, M., Osindero, S. “Intelligent AI Delegation.” arXiv:2602.11865, v1, 2026.
4. Tambe, M. “Towards Flexible Teamwork.” Journal of Artificial Intelligence Research, 7:83–124, 1997.
5. Grosz, B. J., Kraus, S. “Collaborative Plans for Complex Group Action.” Artificial Intelligence, 86(2):269–357, 1996.
6. Smith, R. G. “The Contract Net Protocol: High-Level Communication and Control in a Distributed Problem Solver.” IEEE Transactions on Computers, C-29(12):1104–1113, 1980.
7. Elina, U. “Maat: Independent Deterministic Contract-Based Governance for Multi-Agent LLM Workflows.” arXiv:2609.34017, v1, 2026.
8. “REVISE: Validity-Guided Recovery for Online Revisions in Agent Workflows.” arXiv:2609.00643, v1, 2026. 这里只用已核验题名和摘要级机制，不补写未核对作者或实验细节。

本轮作了版本修正：MegaAgent 为 Findings ACL 2025；TeamMedAgents 主报 v3，不混入旧版六组件；ORCH 主报 v2；HiddenBench 主报 v4；Scaling 主报 v3。不把不同版本当作独立研究，也不把某方法的证据边界自动转成我们的创新。
