# 反证、成立条件与社会机制近邻

检索与核验日期：2026-10-17。范围遵循 BRIEF.md；本轮仅检索、阅读、比较，不运行模型或实验。本文是总报告的反证视角输入，主要回答 RQ2、RQ3，并约束 RQ1 向 Agent 的迁移。

## 1. 核心判断

检索支持“社会协作机制值得借鉴”，但不支持“照搬一种人类组织形式即可形成新框架”。证据形成三个层次：成员差异可能只是文本差异，交流可能损害独立判断，制度复杂性可能消耗有限预算。成功研究则表明，当新增成员提供互补能力、任务允许分解、交接和验证确实被协议执行时，协作可以产生收益。

最需要避免的创新误判是：把动态组队、能力和多样性平衡、团队反思、拍卖分工、分包预算、独立审查、历史制度类比当作未开发机制。下面已有直接先例；真正值得深化的是其失效条件及可执行的改动，而非名称迁移。这里的“值得深化”均为研究假设，不是已证明空白。

## 2. 原始来源核查表：15 项核心来源

“核验”指已打开原始摘要页、正式论文页面或全文，核对题名、作者/出处以及所引用主张。只核验 arXiv 的条目标为预印本；不据此断言其没有后来发表。

| 编号、来源与状态 | 已核验机制/发现 | 对新框架的直接约束与适用边界 |
|---|---|---|
| C01 [Kim et al., Towards a Science of Scaling Agent Systems](https://arxiv.org/abs/2512.08296v3)，2025 初稿、2026-04 v3，预印本；[全文](https://arxiv.org/html/2512.08296v3) | v3 为 260 配置、6 个 agentic 基准、5 类架构、3 模型族，控制工具、提示和算力。相对单 Agent，金融推理可达 +80.8%，序列规划可降至 −70.0%。架构相对优劣比绝对分数更稳定。 | 组织形式必须随可分解性、工具负担、模型能力选择。87% 是留出配置的最优架构选择准确率；绝对预测的 CV R² 仅 .373/.413。不能把旧版 180 配置、4 基准或 45% 阈值写成普遍定律。 |
| C02 [Yang et al., Understanding Agent Scaling in LLM-Based Multi-Agent Systems via Diversity](https://arxiv.org/abs/2602.03794)，2026，预印本；[全文](https://arxiv.org/html/2602.03794v1) | 在投票/辩论设置中研究有效信息渠道；异质配置可用较少成员达到同质扩容效果，提出无标签 K*。 | K* 是嵌入语义差异代理，不是真实任务信息；全文明确只有正确推理路径的多样性才可靠获益。理论依赖理想证据独立与覆盖假设，主要实验为 7B–8B 模型，不能视为长程工具协作定理。 |
| C03 [E. M. Kim et al., Correlated Errors in Large Language Models](https://proceedings.mlr.press/v267/kim25e.html)，ICML 2025 | 350 多个模型的评估发现显著错误相关；一个排行榜上，两模型同时出错时，错误答案相同约 60%。更强模型即使跨提供商/架构也可高度相关；涉及 LLM-as-judge 与招聘后果。 | 模型品牌多样性不足以保证独立证据；60% 不能写成所有模型/任务的通用错误率。对“多个审查员投票即可可信”的论证构成直接限制。 |
| C04 [Cemri et al., Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657v3)，2025 v3；[NeurIPS 2025 论文索引](https://mlanthology.org/neurips/2025/cemri2025neurips-multiagent/) | 当前 v3 数据为 7 框架、1600+ 标注轨迹；14 类失败归入系统设计、Agent 间失配、任务验证。分类体系由 150 轨迹构建，报告 κ=.88。 | 单纯增加 reviewer 不等于解决验证/终止。版本变化较大，不能混用早期 workshop 的 18 类、4 大类与最新版 14 类、3 大类。此为失败诊断，不是所有 MAS 无效的因果结论。 |
| C05 [Huang et al., On the Resilience of LLM-Based Multi-Agent Collaboration with Faulty Agents](https://proceedings.mlr.press/v267/huang25ay.html)，ICML 2025 | 六系统、四任务，以 AutoTransform/AutoInject 注入错误；层级结构 A→(B↔C) 的损失较低；Challenger 和 Inspector 能修复大量注入错误。 | 这是“协作机制确能防错”的正面反例，也说明挑战权与检查员已有先例。注入故障与自然同源盲点不同，最高 96.4% 修复不能外推至未知真实错误。 |
| C06 [Song et al., Adaptive In-conversation Team Building for Language Model Agents](https://arxiv.org/abs/2405.19425v3)，2024 初稿、2025 v3，本轮核验预印本；[全文版本](https://arxiv.org/html/2405.19425v2) | Captain Agent 按任务步骤动态形成和管理团队，以嵌套群聊和反思调整专家组合；六类现实场景验证。 | “像项目经理一样实时招募并调整专家”已有直接先例。要提出增量，应改变能力估计依据、重组触发条件或跨任务持续学习机制。 |
| C07 [Tian et al., AgentInit: Initializing LLM-based Multi-Agent Systems via Diversity and Expertise Orchestration for Effective and Efficient Collaboration](https://arxiv.org/abs/2509.19236)，2025，预印本；[全文](https://arxiv.org/html/2509.19236v1) | 多轮生成/反思候选角色，规范化描述，使用 Pareto 原则平衡任务相关性和团队多样性。相关性由角色描述与问题嵌入相似度估计，多样性使用 Vendi Score，再由 Selector Agent 选队。 | “能力相关性+互补性选队”并非新概念；但这里的操作量主要是描述语义。用实际轨迹、条件成功率、交接兼容性替代描述匹配，是可深化的机制差异，尚需验证。 |
| C08 [Zhang et al., Multi-agent Architecture Search via Agentic Supernet](https://proceedings.mlr.press/v267/zhang25bi.html)，ICML 2025 | MaAS 优化架构分布，按查询采样不同 Agent 系统并分配推理资源；六基准上报告在其对照下更低推理成本及更高表现。 | “按任务动态选组织拓扑且考虑成本”已有学习式架构搜索先例。社会理论若只是限定搜索空间，应解释新增的约束、目标或可迁移结构。 |
| C09 [Li et al., Learn as Individuals, Evolve as a Team: Multi-agent LLMs Adaptation in Embodied Environments](https://arxiv.org/abs/2506.07232)，2025，预印本；[全文](https://arxiv.org/html/2506.07232v1) | LIET 由探索数据训练局部行动成本 utility（LoRA+value head），团队根据接收方对消息的反思共同更新 cooperation knowledge list；在 C-WAH、TDW-MAT 测试。 | “团队一起复盘形成共享协作知识”已有可执行实现，且有个体学习/团队演化消融。开放问题可定位为知识的因果归因、跨成员迁移及失效撤回；不能把其具身任务结果直接当通用知识工作结论。 |
| C10 [Liu et al., Markets, Not Planners: Decentralized Orchestration of LLM Agents with Private Information](https://arxiv.org/abs/2608.23867)，2026-08，工作论文；[全文](https://arxiv.org/html/2608.23867v1) | AgentLance 使用私人成本、反思笔记、公共信誉、VCG 式支付；获胜者可分解任务并在预算内转包。评估数学、代码、QA 与 agentic 任务。 | 市场、信誉、学习和层级分包的组合已存在。所谓去中心化仍有 allocator：分数为估计成功率减成本敏感系数×投标，不能描述成完全无中心。自估成本及次优投标仍是实测瓶颈。 |
| C11 [Fradkin & Krishnan, MarketBench: Evaluating AI Agents as Market Participants](https://arxiv.org/abs/2604.23897)，2026-04，预印本；[全文](https://arxiv.org/html/2604.23897v1) | 六模型、SWE-bench Lite 的 93 项子集，考察成功率与 token 成本自估；二者均失准，自报驱动的拍卖偏离完全信息分配；提供历史能力信息仅部分改善。 | 人类市场理论的“参与者掌握有用私有能力/成本信息”在 LLM 中不能默认成立。不是市场必然失败，而是投标应有可校准基础；与 C10 的正面结果共同限定成立条件。 |
| C12 [Ye & Tan, Agent Contracts: A Formal Framework for Resource-Bounded Autonomous AI Systems](https://arxiv.org/abs/2601.08815v3)，2026，预印本（v3 标示 workshop 接收）；[全文](https://arxiv.org/html/2601.08815v3) | 合同明确 I/O、资源、期限、成功条件及生命周期；分层委托满足预算守恒。70 题代码审查比较中 token 约降 90%，成功率 60.0%→52.9%，p=.13。 | “合同式交接和资源承诺”已有形式机制；省成本不等于质量等价。现有执行在调用间可硬限制、调用内主要软约束，不能声称任意单次生成都严格不超预算。 |
| C13 [Fei, Guo & Xiao, When Agents Evolve, Institutions Follow](https://arxiv.org/abs/2604.27691)，2026-04，预印本；[全文](https://arxiv.org/html/2604.27691v1) | SocialSystemArena 把七种历史制度实现为治理协议：提案、权限、审查、执行和纠错；3 模型、PinchBench/ClaweBench。制度选择随任务与能力变化；高密度审查门可形成 gate-loop。 | “借鉴人类历史制度/分权制衡做 MAS”是非常直接近邻。57–61 个百分点差距主要在 PinchBench；更难的 ClaweBench 缩至 8.2–11.8 点并发生排序反转。元治理动态选择是作者提出的后续方向，不能当作本文已解决。 |
| C14 [Tomašev, Franklin & Osindero, Intelligent AI Delegation](https://arxiv.org/abs/2602.11865)，2026-02，预印本/概念框架；[全文](https://arxiv.org/html/2602.11865v1) | 委托被定义为任务分配同时转移权限、责任、问责，明确意图、角色边界和信任，并随环境和失败调整。 | 交接协议、问责、授权范围、适应性委托的概念覆盖已很广。它是框架提案，不能当成已证实高性能系统；新工作可以把其中原则转为具体可执行不变量。 |
| C15 [Chen et al., Scoring, Reasoning, and Selecting the Best! Ensembling Large Language Models via a Peer-Review Process](https://arxiv.org/abs/2512.23213v4)，2025 初稿、2026-08 v4，预印本；[全文](https://arxiv.org/html/2512.23213v4) | LLM-PeerReview 复用候选生成模型作评分者，采用平均或图模型真值推断汇总评分，再选最佳回答；四数据集验证。 | “同行评审式评分/综合裁决”已有直接方法。它是响应选择 ensemble，不是外部事实验证；结合 C03 可知，评审者数量与意见一致性不足以证明正确。 |

## 3. 反证与成功条件：跨来源比较

### 3.1 从角色多样性转向任务相关的互补能力

C07 按描述构造团队，C02 按输出嵌入估计有效渠道，二者使“多样性”可计算，但都不能把语义差异直接等同于正确能力互补。C03 更进一步表明，跨模型提供商也可能共享错误。因此，框架必须回答谁补足谁的什么盲点、这种补足在哪种任务上成立，以及交互会不会破坏它。C06 的动态专家招募是成立的工程先例，仍需要区分角色声称的 expertise 与轨迹证明的 competence。

可深化假设：团队组成依据应包括任务条件下的成功覆盖、失败相关性与交接兼容性，而不只相关角色名称或语言风格。该假设的技术近邻至少包括 C07、C02、C08，不能只声称“首次考虑互补性”。

### 3.2 从交流数量转向可保持的信息与约束

C01 的序列任务反例说明信息压缩与协调开销会抵消并行收益；C04 显示交互失配与终止验证属于反复出现的失败来源。相对地，C09 不把每次消息当作一次性交流，而学习接收方更需要的信息；C12 把预算与成功条件放入合同执行层。两条成功路径都修改可执行信息状态，而非仅增加“合作、反思、负责”的提示词。

可深化假设：交接产物应该携带可检查的状态、尚未满足的义务、证据依赖与不确定性，使后续行动能够继承并挑战上游决定。概念近邻 C14 已覆盖广义智能委托，资源契约近邻 C12 已覆盖预算与生命周期；新贡献需落在语义约束怎样随任务变化继续有效、怎样定位失效并恢复，而非“引入交接表单”。

### 3.3 从更多审查转向有能力且有停止规则的纠错

C05 是有价值的正面证据：挑战与检查协议能使故障传播显著缓解。C13 则显示审查密度过高或执行模型过弱时，相同检查思想会变成 gate-loop。C15 的同行评分在其响应选择任务上有效，却与 C03 的共错风险并存。这些研究没有相互推翻：它们测量的错误来源、任务结构与反馈来源不同。

可深化假设：需要估计审查的边际价值，以外部可执行检查、证据新增与异议是否已被处理决定继续审查、提交或退回重做。贡献不能仅为增加反对者/审稿人；C05 已有 Challenger/Inspector，C13 已有提案审查与退回结构。

### 3.4 从社会形式迁移转向条件化组织选择

C01 从定量架构研究发现任务结构的重要性，C13 从历史制度编译得到类似的条件性；C08 已让架构随查询变化。因此“哪种人类组织最好”不足以形成普遍研究主张。更实质的问题是组织需要什么可观测信号才能知道当前结构正在失效，以及何时改变控制权、组队或协议才划算。

这里必须区分已实现与推论：C13 已实现多种制度并对比其表现，但文末的实时元治理仍是自然扩展；C08 已经实现查询依赖的架构搜索。提出运行中制度切换时，应与这两者逐项比较选择粒度、切换状态、约束保持和决策依据，不能把“动态”二字当作差异。

### 3.5 从市场隐喻转向可校准的私有信息

C10 的多任务正面结果与 C11 的自估失败并不矛盾：前者加入公共信誉、反思策略及受约束转包，后者直接测试市场参与所需的自知能力。二者都承认成本自估是瓶颈。更一般地，VCG 的理论性质不能自动迁移到会错误估计成本、错误解释规则、由 LLM 估计成功率的实际协议。

可深化假设：选择市场而非统一经理，需要有分散且有价值的私有信息、真实能力/成本异质性，以及可执行的任务验收；在同一模型复制体、共同目标、公共信息的封闭团队中，虚拟货币是否提供额外效用是待检验问题。这里不能用人类经济学的有效性替代对代理信息质量的证明。

## 4. 最小创新判别表

| 拟借鉴人类机制 | 直接近邻 | 仅改名或叠模块的风险 | 可继续研究的具体差异（未验证） |
|---|---|---|---|
| 团队/专家组成 | Captain Agent、AgentInit | 角色生成+相关性+多样性 | 基于可校准的条件能力与交接兼容性选择，允许成员退出/撤销授权 |
| 团队复盘与学习 | LIET | 共享笔记+反思 | 学习协议失败的归因、成员变化后的知识迁移/撤回与遗忘 |
| 分权、制衡与制度 | SocialSystemArena、MaAS | 历史组织名+固定审查拓扑 | 依据可观测失效信号调整决策权，切换时保持义务和证据依赖 |
| 市场、招标与信誉 | AgentLance、MarketBench | 投标+信誉+分包 | 自估误差下的可靠分配与契约验收；不能直接宣称首次市场 MAS |
| 承诺与交接 | Agent Contracts、Intelligent AI Delegation | 任务表+预算表 | 语义约束继承、失效定位、局部恢复；把原则转成可执行协议 |
| 同行评审、异议 | MAS Resilience、LLM-PeerReview | 再加一名 critic/judge | 审查独立性、证据新增、边际收益及有界停止的联合机制 |

## 5. 人类机制不能直接迁移的原因：推论与证据分开

以下是跨来源推论，而非本文声称已被一项实验全部证明的定律：

1. 人类分工建立在训练经历、专长、信息和行动资源的实际差异上；同一 LLM 的不同 persona 未必产生这种差异。C03、C07 为这一担忧提供相关证据，而非证明 persona 永远无效。
2. 人类责任、地位、声誉与激励涉及持续身份及真实后果；只要求模型“像领导一样负责”不等于建立问责。C10、C12、C14 的价值在于把其中部分内容变成可观测记录或执行约束。
3. 人类团队的共同理解可能包含默认知识和长期互动；Agent 的消息是有损且有成本的接口。C01、C09 支持研究这种接口，但不支持断言 LLM 必须复制人类认知状态。
4. 人类组织有时为治理正当性、利益平衡而牺牲效率。若封闭 MAS 只共享一个任务目标，社会制度的某些功能可能不需要；开放多方系统中的私有信息与权限冲突则可能重新使之必要。C10、C14 的问题设定更接近后者。

## 6. 补充核验与后续交叉检查

- 主执行者补充并经本分支核验：[Li, Naito & Shirado, Systematic Failures in Collective Reasoning under Distributed Information in Multi-Agent LLMs](https://arxiv.org/abs/2505.11556v4)，v4 2026-05，标示 ICML 2026 接收；[全文](https://arxiv.org/html/2505.11556v4)。HiddenBench 已把 hidden-profile 理论转成 65 任务、15 模型的诊断：分散信息条件平均 30.1%，全信息单 Agent 80.7%。更直接的协议先例是先交换决策相关事实并反对当前领先选项，再总结证据/不确定性后决定；18 任务、3 模型取得改善。故“主动挖掘同伴未说信息”和“先探索后共识”均需纳入近邻。全信息基线是信息条件诊断，不能写成公平资源下单 Agent 必胜；简单异议的收益也明显依赖模型。
- 历史基础：[Smith, The Contract Net Protocol: High-Level Communication and Control in a Distributed Problem Solver](https://doi.org/10.1109/TC.1980.1675516)，IEEE Transactions on Computers 1980；[论文 PDF](https://cse-robotics.engr.tamu.edu/dshell/cs631/papers/smith80contract.pdf)。任务公告、投标和互选式分配远早于 LLM，因此“引入合同网”本身不能视为机制创新。
- 机制设计边界：[Dütting et al., Mechanism Design for Large Language Models](https://research.google/pubs/mechanism-design-for-large-language-models/)，WWW 2024；[原稿](https://arxiv.org/abs/2310.10826)。其 token auction 处理多方偏好下的联合内容生成，与 AgentLance 的任务劳动力分配是不同问题，不应统称为同一个“市场框架”。
- 身份偏差：[Choi, Zhu & Li, When Identity Skews Debate: Anonymization for Bias-Reduced Multi-Agent Reasoning](https://aclanthology.org/2026.acl-long.650/)，ACL 2026。匿名化身份以缓解自偏/迎合是直接协议先例；故“匿名同行审查”也需仔细比较，不能只依靠人类双盲类比。
- 已知专家抑制来源本轮发现正式发表版本：[Pappu et al., Multi-Agent Teams Hold Experts Back](https://proceedings.mlr.press/v306/pappu26a.html)，ICML 2026。总报告可使用正式版本替代只标预印本的旧记录。

## 7. 结论与仍需谨慎的部分

对 RQ2：团队组成、团队学习、市场协调、预算合同、同行审查和制度组织均有从隐喻走向可执行协议的实例。对 RQ3：更值得深化的是在任务变化、成员能力变化和错误暴露时，怎样保持正确的授权、约束、证据与恢复过程，并控制组织自身成本。

本轮没有证明哪一个新框架优于强单 Agent，也没有完成所有相关文献的穷尽查新。诊断证据、理想化理论、少数基准正面结果和概念框架在表中分开保留；对尚未报告的实验，不据此推断方法必然失败。尤其不能把“社会机制尚有未解决边界”替换成“这一边界从无人研究”。
