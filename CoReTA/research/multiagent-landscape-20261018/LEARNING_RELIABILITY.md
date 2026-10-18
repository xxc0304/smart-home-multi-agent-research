# 多 Agent 的学习、记忆、队友建模与可靠性

核查日期：2026-10-18。范围：LLM 驱动的协作系统；按实际改变的对象组织，而不把 ToM、认知负荷、MARL 等理论名称直接当作方法类别。完成两轮联网检索：第一轮找主流机制，第二轮追查新版本、负面结果和遗漏分支。下列 18 篇为核心，另列邻接补漏。

访问层级：**F**＝打开 primary 全文并核查相关方法/实验段落（不代表逐页精读）；**A**＝primary 摘要、版本记录或正式 proceedings 元数据；**S**＝仅检索摘要，不能支撑细节结论。核心全部至少 A；未运行实验，未调用付费模型 API。“局限/判断”如非作者明说，是依据实证范围作出的本报告判断。所有数值均为作者报告，不跨论文比较绝对分数。

## 1. 先分清究竟学了什么

| 改变对象 | 代表工作 | 时间尺度 | 与其他路线的实质差异 |
|---|---|---|---|
| 角色模型权重 | MALT、MAPoRL、DAC、C3、Dr. MAS | 部署前训练；RL 中在线采样不等于部署时在线学习 | 把协作行为固化进参数，依赖可用奖励、训练预算和角色分布 |
| 辅助效用模型权重＋共享提示知识 | LIET | 离线学效用；测试时更新合作知识 | 混合参数学习与外部记忆，不能简单归为“免训练”或“团队 RL” |
| 团队外部记忆 | G-Memory、LLMA-Mem | 跨 episode/跨任务持续更新 | 保留协作经验，不必改底座权重；检索正确不代表经验仍适用 |
| 群体经验库＋排序器 | MATM | 离线构库/训练排序器；增量入库；部署检索 | 不要求生产者与消费者同时协作或联合训练，属于异步经验共享 |
| 关于队友的信念/假设/控制策略 | ProAgent、Hypothetical Minds、A-ToM | 单次互动内在线适应 | 改变的是队友模型与行动选择，不必更新 LLM 权重 |
| 何时澄清的控制器权重 | AgentAsk | 离线示范学习＋RL；运行时局部介入 | 修补消息交接点，而非重新搜索整个团队结构 |
| 有效性、检查、共识协议 | REVISE、Resilience、SAC | 在线执行 | 防止或恢复失败，不等于模型学习；可靠性来自可验证状态或过滤机制 |
| 审计经验与评测集 | AgentAuditor、TAMAS | 离线构造；在线评估 | 评价安全性的工具，不能据此声称执行系统已安全 |

## 2. 把协作训练进参数：监督、奖励与信用分配

### L1. MALT: Improving Reasoning with Multi-Agent LLM Training

- **来源/状态/访问**：[arXiv 2412.01928v3](https://arxiv.org/abs/2412.01928v3)，2025-10-06；primary 记录明确 Published at COLM 2025；**A**。初稿 2024-12-02，不应误写成 ICML 论文。
- **问题与方法**：生成、验证、修订三个角色需要分别学习。多次采样形成搜索树，以最终正误回传角色价值，构造角色条件的离线后训练数据；学习对象是专门化模型权重。
- **实证范围**：MATH、GSM8K、CSQA；摘要报告相对基座的相对增幅分别 15.66%、7.42%、9.40%。这是相对增幅，不是百分点。
- **局限/比较**：角色和流程预先固定；正误标签可得的短程推理不能直接外推到开放工具任务。与 MAPoRL 的共同训练不同，MALT 的关键是离线树搜索产生可归因训练数据。

### L2. MAPoRL: Multi-Agent Post-Co-Training for Collaborative Large Language Models with Reinforcement Learning

- **来源/状态/访问**：[ACL 2025 正式论文](https://aclanthology.org/2025.acl-long.1459/)，2025.7；**A**。这里采用 proceedings 题名，不采纳搜索引擎偶发的“MAPoRL2”。
- **问题与方法**：单独训练强模型未必学会被同伴纠正或说服同伴。多个 LLM 先独立作答再讨论，由 verifier 给最终结果奖励，并加入鼓励纠错与有效说服的奖励塑形；联合更新成员权重。
- **实证范围**：多数据集以及未见领域泛化；primary 摘要支持“单体训练不足以稳定产生协作”与共同训练收益，本文不凭摘要补写具体数据集或收益数。
- **局限/比较**：奖励塑形既定义何为好协作，也可能引入 evaluator 偏差。它证明的是给定讨论协议与反馈的训练效果，不能证明讨论本身在任意预算下优于独立采样。

### L3. Learn as Individuals, Evolve as a Team: Multi-agent LLMs Adaptation in Embodied Environments（LIET）

- **来源/状态/访问**：[arXiv 2506.07232v1](https://arxiv.org/abs/2506.07232v1)，2025-06-08；本轮未核到正式 venue；**F**，[方法全文](https://arxiv.org/html/2506.07232v1)。
- **问题与方法**：规划器缺少环境动作代价知识，沟通经验又无法累积。先以探索数据训练带 LoRA 和 value head 的小 LLM，回归动作环境步数；运行时成员查询效用模型，同时从接收者反馈更新共享合作知识列表。
- **实证范围**：Communicative Watch-And-Help、ThreeD-World Multi-Agent Transport；LLaMA、GPT-4o 实例；以两人机制为主要说明，也报告更多成员。
- **局限/比较**：离线学习的是辅助代价模型；团队在线进化主要是提示知识。环境探索覆盖不足、代价估计失准和反思知识污染是不同失败源，需要分别检验。

### L4. Cross-Agent Learning Signals Enable Coordinated Role-Decomposed LLM Training（DAC）

- **来源/状态/访问**：[arXiv 2606.10684v2](https://arxiv.org/abs/2606.10684v2)，2026-10-07；预印本；**F**，[全文](https://arxiv.org/html/2606.10684v2)。v1 旧题为 *Divide and Cooperate: Role-Decomposed Multi-Agent LLM Training with Cross-Agent Learning Signals*，不应混用题名与版本。
- **问题与方法**：检索充分却回答错，会错误惩罚 searcher；检索不足又会错误惩罚 generator。以外部证据充分性验证＋generator 拒答决定构造角色特定交叉奖励，再用带噪声的充分证据防止过度拒答。
- **实证范围**：两底座、七个一般/多跳 QA；主实验两个角色共用一个模型、分别计算 RL loss；主表推理时关闭拒答。
- **局限/比较**：substring EM 是主要训练充分性信号，证据含答案不等于语义充分。相对 MAPoRL，它把信用分配定位到检索—生成接口；角色分开不等于拥有独立模型权重。

### L5. The Trace Is the State: Exact Credit Assignment for LLM Agent Teams（C3）

- **来源/状态/访问**：[arXiv 2603.06859v4](https://arxiv.org/abs/2603.06859v4)，2026-10-07；预印本；**F**，[全文](https://arxiv.org/html/2603.06859v4)。v1 题为 *Contextual Counterfactual Credit Assignment for Multi-Agent Reinforcement Learning in LLM Collaboration*；v3 已大改题名与论证。
- **问题与方法**：不再仅预测消息的价值，而在相同 trace 前缀替换消息、重跑其下游，以实际终局奖励估计反事实边际贡献。改变的是训练优势估计和进而更新的团队权重。
- **实证范围**：六类流程、2–10 个决策点用于估计器分析；实际训练重点为双 Agent。报告相较 MAPPO 少 37% 训练 token。
- **局限/比较**：“exact”有明确条件：下游可见的一切状态，包括工具、记忆和路由，都被 trace 记录；仍有 Monte Carlo 误差。隐藏状态、不可重置外部副作用会破坏条件。它比简单删掉一个 Agent 更接近消息因果贡献，但须付出续跑成本。

### L6. Dr. MAS: Stable Reinforcement Learning for Multi-Agent LLM Systems

- **来源/状态/访问**：[arXiv 2602.08847v2](https://arxiv.org/abs/2602.08847v2)，2026-09-27；作者记录 NeurIPS 2026，按已接收声明处理，本轮未核正式 proceedings；**A**；[作者代码](https://github.com/langfengQ/DrMAS)支持接收声明。
- **问题与方法**：用全团队 GRPO 归一化，会让不同角色的奖励分布错配，引起梯度尖峰；改为成员各自奖励统计归一化，并提供异构模型编排训练框架。
- **实证范围**：Qwen2.5/Qwen3 的多 Agent 数学与多轮搜索；比较 vanilla GRPO、异构成员配置和效率。
- **局限/比较**：它修复训练数值稳定性，不直接解决跨角色、跨轮的因果信用分配；与 DAC、C3 可组合，但三者并非同一种“多 Agent RL 方法”。

## 3. 保留经验：团队记忆与开放群体经验共享

### L7. G-Memory: Tracing Hierarchical Memory for Multi-Agent Systems

- **来源/状态/访问**：[NeurIPS 2025 正式论文](https://papers.nips.cc/paper_files/paper/2025/hash/136a45cd9b841bf785625709a19c6508-Abstract-Conference.html)；**F**，[arXiv v2 全文](https://arxiv.org/html/2506.07398v2)。
- **问题与方法**：仅保存最终答案会丢失协作过程；组织 insight、query、interaction 三层图，向上取抽象经验、向下取协作片段，再按角色提供记忆提示；跨任务更新外部图，无需改底座权重。
- **实证范围**：五 benchmark、三底座、AutoGen/DyLAN/MacNet 三框架；作者报告 embodied action 最大提升 20.89 个百分点、知识 QA 10.12 个百分点。
- **局限/比较**：图保留了经验与支持轨迹，比平铺摘要更可追溯；仍需面对错误经验、过期结论与检索成本。实证不能推出对医疗等高风险域同样有效，作者亦明确需要更广任务验证。

### L8. Scaling Teams or Scaling Time? Memory Enabled Lifelong Learning in LLM Multi-Agent Systems（LLMA-Mem）

- **来源/状态/访问**：[arXiv 2604.03295v1](https://arxiv.org/abs/2604.03295v1)，2026-03-27；预印本；**F**，[全文](https://arxiv.org/html/2604.03295v1)。
- **问题与方法**：增加人数和重复使用经验是两条扩展轴。结合 episodic、procedural、transactive memory，比较私有、共享、混合拓扑，按任务结果更新可靠性统计并定期巩固经验。
- **实证范围**：MultiAgentBench 的 coding、research、database，各 100 任务；讨论长期表现和成本。受控消融中私有记忆优于共享、混合，作者解释为角色特定经验减少干扰。
- **局限/比较**：这是对“共享越多越好”“人越多越好”的直接反证，但不是私有记忆普遍最优定律。与 G-Memory 关注结构化检索不同，它把记忆拓扑和团队规模的交互作为研究对象。

### L9. Multi-Agent Transactive Memory（MATM）

- **来源/状态/访问**：[arXiv 2606.19911v2](https://arxiv.org/abs/2606.19911v2)，**2026-10-15**；预印本；**F**，[全文](https://arxiv.org/html/2606.19911v2)。最新版本在截止日前三天发布。
- **问题与方法**：不同 Agent 重复发现相同操作过程。生产者向共享轨迹库投稿，消费者按当前状态检索后续步骤；另训练轻量 learning-to-rank 排序器，用注入轨迹相对不检索的边际收益监督，允许生产者/消费者特征参与个性化与信任建模。
- **实证范围**：ALFWorld、WebArena；35–37 生产者、34 消费者；训练/测试隔离，WebArena 为自定义划分。
- **局限/比较**：不要求同步协作和联合训练，因此是“多 Agent 经验基础设施”，不是讨论型团队。当前只索引成功续轨；失败经验利用、恶意投毒与撤销不是已解决问题。底座冻结不等于整个系统无训练，排序器有监督学习。

## 4. 运行时推断队友：信念更新而非心理术语堆叠

### L10. ProAgent: Building Proactive Cooperative Agents with Large Language Models

- **来源/状态/访问**：[AAAI 2024 正式论文](https://ojs.aaai.org/index.php/AAAI/article/view/29710)，2024-03-24；**A**。
- **问题与方法**：面对训练未见过的队友，直接套固定合作策略易失配。由观察推断队友意图，随后以队友真实行为更新信念，再主动规划自己的合作行为；改变的是在线信念与计划。
- **实证范围**：Overcooked-AI，五个 self-play/population-training 基线；human proxy models 的平均收益超过 10%。Human proxy 不应写成真实人类用户实验。
- **局限/比较**：提供了意图推断—行为校验闭环，但证据集中于厨房合作环境；不能把高层语言推断直接当成对队友真实心理状态的测量。

### L11. Hypothetical Minds: Scaffolding Theory of Mind for Multi-Agent Tasks with Large Language Models

- **来源/状态/访问**：[ICLR 2025 正式论文](https://proceedings.iclr.cc/paper_files/paper/2025/hash/12f483f624b378f9f3058d8ecd3c7ff5-Abstract-Conference.html)；**A**。
- **问题与方法**：未知对手使环境非平稳；用自然语言生成多种策略假设，预测他人行为，再根据预测正确程度强化和修订假设，支撑分层规划。
- **实证范围**：Melting Pot 中合作、竞争、mixed-motive，双人及群体环境；包含 hypothesis evaluation/refinement 消融。
- **局限/比较**：相较 ProAgent 的意图推断，显式假设竞争与行为校验更清楚；收益也可能依赖观察可辨识性与 LLM 先验。在线适应来自外部假设管理，不能据此宣称学到了通用 ToM 参数能力。

### L12. Adaptive Theory of Mind for LLM-based Multi-Agent Coordination（A-ToM）

- **来源/状态/访问**：[AAAI 2026 正式论文](https://ojs.aaai.org/index.php/AAAI/article/view/40204)，2026-03-14；**A**。
- **问题与方法**：推理别人、别人如何推理自己的深度不匹配，会过度或不足建模。根据历史交互估计伙伴推理阶次，选相应队友预测并协调行动。
- **实证范围**：重复矩阵博弈、两个网格导航、Overcooked，共四项；包含非 LLM 队友泛化讨论。
- **局限/比较**：它反对“递归越深越好”，强调匹配；但阶次模型是构造的有限假设类，伙伴行为未必由固定阶次生成。需要区分高阶语言提示带来的计算增量与真实预测改进。

## 5. 把错误拦在交接点，或恢复到有效状态

### L13. AgentAsk: Multi-Agent Systems Need to Ask

- **来源/状态/访问**：[ACL 2026 正式论文](https://aclanthology.org/2026.acl-long.1294/)；**F**，[arXiv v2 全文](https://arxiv.org/html/2510.07593v2)，2026-01-19。
- **问题与方法**：遗漏、指代漂移、信号损坏、能力错配在消息交接中扩散。外置边控制器决定问不问、问谁、问什么；示范微调后用 E-GRPO 优化澄清收益与预算，运行时保持原流程而插入最小澄清。
- **实证范围**：五 benchmark，固定编排、预算、边级鲁棒性等；正式摘要报告最多 4.69% 准确率改善、额外成本与时延均小于 10%。早期检索摘要“小于5%”不沿用。
- **局限/比较**：澄清能补信息或指代，但源头没有能力或可信证据时，继续问未必解决。与 Inspector 的普遍检查不同，它学习何时付出局部询问成本。

### L14. REVISE: Validity-Guided Recovery for Online Revisions in Agent Workflows

- **来源/状态/访问**：[arXiv 2609.00643v1](https://arxiv.org/abs/2609.00643v1)，2026-09-01；预印本；**A**。
- **问题与方法**：用户或上游修订到达时，全重跑浪费，直接复用会提交旧状态。记录动态数据/控制依赖，把 revision delta 传播到部分执行 DAG，只停用和重算受影响区域，复用结果提交前再验证；provenance 不足时保守扩大恢复。
- **实证范围**：300 个困难 revision/commit 执行；LangGraph、LLMCompiler 原应用、Qwen3-14B。模型调用相对全重启减少 40.6–56.0%。
- **局限/比较**：解决版本有效性与执行恢复，不保证语义答案正确；依赖结构化依赖和可拦截提交。不能把300次无 stale output 写成“数千次”或无条件正确性保证，也不能把任意单 Agent workflow 自动归作团队协作算法。

### L15. On the Resilience of LLM-Based Multi-Agent Collaboration with Faulty Agents

- **来源/状态/访问**：[ICML 2025 / PMLR 267 正式论文](https://proceedings.mlr.press/v267/huang25ay.html)；**A**。
- **问题与方法**：把错误注入成员输出，比较链式、互联、层级结构；AutoTransform/AutoInject 形成故障，Challenger 允许质疑，Inspector 检查纠正消息。
- **实证范围**：四下游任务、六系统。所测层级结构下降5.5%，其余两类10.5%、23.7%；最高恢复96.4%人为注入错误。
- **局限/比较**：恢复的是特定模拟错误分布，不能解释成抵御96.4%的真实恶意攻击。增加检查者可能也增加共同偏差与成本；层级优点受错误落点和检查权限影响。

## 6. 安全审计、对抗评测与恶意成员过滤

### L16. AgentAuditor: Human-level Safety and Security Evaluation for LLM Agents

- **来源/状态/访问**：[NeurIPS 2025 正式论文](https://papers.neurips.cc/paper_files/paper/2025/hash/3dc85735f6e2fcf093e67b134fa00d21-Abstract-Conference.html)；**A**。
- **问题与方法**：孤立判断单一步骤，可能遗漏风险累积或模糊规则。训练无关的外部经验记忆保存场景、风险、行为等结构特征和历史推理，经多级检索增强 evaluator。
- **实证范围**：ASSEBench 的2293条交互、15风险类型、29应用场景，区分 Strict/Lenient 标准；“human-level”为该标注评测上的作者结论。
- **局限/比较**：这是 agent 安全评估器，不是多 Agent 执行防御。多成员系统可以使用它，但不应把审计准确率当成拦截风险的系统保证。

### L17. TAMAS: Benchmarking Adversarial Risks in Multi-Agent LLM Systems

- **来源/状态/访问**：[ACL 2026 正式论文](https://aclanthology.org/2026.acl-long.1442/)；**A**。
- **问题与方法**：单 Agent 安全基准漏掉角色互动带来的攻击面。五情境、300对抗实例、六攻击类型、211工具，以及100无害任务；ERS 同时衡量安全与任务效果。
- **实证范围**：十底座、AutoGen/CrewAI 三种交互配置；发现所测系统对攻击脆弱。
- **局限/比较**：它补上 Resilience 的非恶意/合成错误局限，但仍是有限威胁模型；指标可避免“一概拒绝看似安全”，不能穷尽跨域权限、持久记忆污染和真实部署副作用。

### L18. Robust Multi-Agent LLMs under Byzantine Faults（SAC）

- **来源/状态/访问**：[arXiv 2605.09076v3](https://arxiv.org/abs/2605.09076v3)，2026-08-30，作者记录 EMNLP 2026 Main Accepted；本轮未核到正式 proceedings，按接收声明处理；**F**，[全文](https://arxiv.org/html/2605.09076v3)。
- **问题与方法**：恶意成员在点对点通信中传播错误。Self-Anchored Consensus 由每个节点本地评价、过滤和修订，保持对自身判断的锚定；讨论通信图的(F+1)-robustness 条件。
- **实证范围**：开源/闭源底座的数学与常识推理，多种通信拓扑与 Byzantine 扰动。
- **局限/比较**：拓扑条件与语言评价器正确性是不同前提；图足够 robust 不等于本地 LLM 能判断语义真伪。它与多数投票最大的差别是过滤、保留自身锚点与可传播性条件，不是简单扩大人数。

## 7. 第二轮补漏与反证：值得跟进，但不扩充核心篇数

| 工作与 primary 状态 | 增加了什么；为什么未与核心混为一谈 |
|---|---|
| [MARTI: A Framework for Multi-Agent LLM Systems Reinforced Training and Inference](https://openreview.net/forum?id=E7jZqo0A50)，ICLR2026；[官方仓库](https://github.com/TsinghuaC3I/MARTI)已打开，A；论文仅primary搜索索引S | 重要工程补漏：集中式多成员交互、分布式策略训练、多轮异步rollout，支持 debate/chain/MoA、规则与生成奖励。正式PDF搜索索引标注 Published as ICLR2026，并称在相同推理预算且训练收敛后数学任务多成员优于单成员；但直接打开OpenReview被浏览器验证拦截，本文不引用二手表格数值。仓库的MARTI-v2/MARS²是后续代码与技术报告，不能把v2代码生成结果归给原ICLR论文。 |
| [Training LLMs for Multi-Agent Collaboration with Verifiable Information Rewards](https://arxiv.org/abs/2610.17893v1)，CoSIR，2026-10-13，预印本，A | 截止前五天的新作；用 Bayesian evaluator 对正确选项的 team surprisal 降幅奖励信息披露与询问潜在价值，再奖励使用收到的信息；三底座自博弈训练、七未见协作任务迁移。把“说有用的话”变为局部可验奖励，补足只看终局正误的路线；尚需全文审阅和独立复现，不据摘要宣称解决开放通信。 |
| [United Minds or Isolated Agents? Exploring Coordination of LLMs under Cognitive Load Theory](https://arxiv.org/abs/2506.06843v3)，CoThinker，2026-06-21版本，预印本，A | 专门化、结构化通信和共同工作记忆；新版明确收益集中于高推理负荷，低内在负荷指令任务的协调开销占优。认知负荷是设计解释，机制仍是分工与上下文管理。 |
| [Taming “Zombie” Agents: A Markov State-Aware Framework for Resilient Multi-Agent Evolution](https://aclanthology.org/2026.acl-long.373/)，AgentRevive，ACL2026，A | Active/Standby/Terminated 软状态转移＋边优化；说明暂时低贡献不应一律永久剪枝。属于成员调度恢复，不是 REVISE 的版本依赖恢复。 |
| [When Agents Go Rogue: Activation-Based Detection of Malicious Behaviors in Multi-Agent Systems](https://proceedings.mlr.press/v306/xu26ax.html)，ICML2026，A | 将恶意检测扩展到 activation 线索，补充只读消息内容的防御；本轮仅核到正式元数据和摘要开头，具体检测效果/架构条件不引用。 |
| [MAS-FIRE: Fault Injection and Reliability Evaluation for LLM-Based Multi-Agent Systems](https://arxiv.org/abs/2602.19843)，预印本，A | 用故障注入系统评估可靠性；可作为方法评价的补充方向，本轮未精读其协议，不写数值或可复现性结论。 |
| [Auditing Multi-Agent LLM Reasoning Trees Outperforms Majority Vote and LLM-as-Judge](https://arxiv.org/abs/2602.09341)，2026预印本，S | 也把方法命名为 AgentAuditor，和 NeurIPS2025 安全 evaluator 是两篇不同论文。检索摘要称审计推理树优于投票，本轮未打开 primary 正文，故不混写其结果。 |

## 8. 当前证据支持的边界

1. **“更会讨论”与“更会协作完成任务”仍需分开验证。** MALT/MAPoRL 的推理、DAC 的检索 QA、LIET 的具身协作使用不同奖励与任务接口，不能凭统一 multi-agent 标签比较效果。训练是否保持原单体能力、能否和未见角色/模型合作，仍是迁移检验的关键。
2. **信用分配正在从整个终局走向接口与消息。** DAC 用任务结构分开检索充分性与回答能力；C3 在 trace 完整时执行反事实；Dr. MAS 则修复归一化。三者针对奖励“对不对人”、估计“准不准”、梯度“稳不稳”，不是互相替代。CoSIR 又把局部信息价值变成可验合成环境奖励。
3. **记忆的组织、所有权和生命周期比“有没有记忆”更有解释力。** G-Memory 证明层级组织有用；LLMA-Mem 显示共享会带来角色干扰；MATM 允许跨团队异步复用。仍应测撤销过时经验、来源可信度、冲突与污染传播，不能把持续追加经验叫作已解决的终身学习。
4. **队友建模的目标应是可检验行为预测。** ProAgent 是意图信念更新，HM 是假设生成—预测—评价，A-ToM 是深度匹配；其有效性依赖可观察行为是否区分候选模型。更长的心理描述、更多递归层次都不是独立目标。
5. **可靠性至少有四个不同对象。** 消息语义交接（AgentAsk）、故障输出扩散（Resilience/SAC）、修订后的状态有效性（REVISE）、安全风险判定（AgentAuditor/TAMAS）。某一层的改善不能推出其他层也已解决。
6. **安全和任务效用必须同时看。** TAMAS 的无害任务与 ERS 值得借鉴；故障模拟、Byzantine 文字攻击、真实工具权限与持久记忆污染是不同分布。当前这组证据不足以宣称面向开放跨组织团队的端到端安全。

以上为跨来源综合判断；对应依据见 L1–L18 与第二轮补漏，不是新的实验证据。

## 9. 建议阅读顺序

- **建立参数学习地图**：MALT → MAPoRL → DAC v2 → C3 v4；需要自己训练时再读 Dr. MAS，最新局部奖励想法跟 CoSIR。
- **建立记忆地图**：G-Memory → LLMA-Mem → MATM v2，分别看结构、团队拓扑、开放群体复用。
- **建立队友适应地图**：ProAgent → Hypothetical Minds → A-ToM，重点比较在线更新对象、行为预测评价、推理预算。
- **建立可靠性地图**：Resilience → AgentAsk → REVISE；再将 TAMAS 的攻击评测与 SAC 的条件防御并读。AgentAuditor 安全版作为评价器补充。

## 10. 查询与核验记录

所有查询于2026-10-18执行；工具为联网 search_service。使用多组查询发现候选，逐篇打开 arXiv/AAAI/ACL/PMLR/NeurIPS/ICLR primary 页面核对，第三方网站仅用于发现，未以其聚合摘要替代核心证据。

| 轮次 | 查询（原始关键字） | 主要产出/核验动作 |
|---|---|---|
| 1 主流训练 | `LLM multi agent learning MALT MAPoRL LIET team training` | MALT v3、COLM2025；MAPoRL ACL2025；打开 LIET 方法核对辅助效用模型训练 |
| 1 队友建模 | `LLM multi agent Hypothetical Minds A-ToM ProAgent teammate modeling` | ICLR2025、AAAI2026、AAAI2024 primary；区分 online belief 与权重训练 |
| 1 可靠性 | `LLM multi agent AgentAuditor REVISE AgentAsk reliability` | 发现两个 AgentAuditor 同名；AgentAsk 正式 ACL版本与旧摘要成本差异 |
| 1 记忆扩展 | `LLM multi agent shared memory team learning MACNET G-Memory 2025 2026` | G-Memory、LLMA-Mem、选择性共享记忆邻接结果；优先 primary 并追读拓扑消融 |
| 2 训练版本 | `"2606.10684"`; `LLM multi agent credit assignment MARS Dr MAS 2026` | 直接打开 DAC v2 纠正旧题；发现 C3 改题到 v4、DrMAS 接收声明 |
| 2 恢复 | `"REVISE" "multi-agent" recovery`; `"REVISE: Validity-Guided Recovery" arxiv` | 直接打开2609.00643；排除其他同名 revision 内容；纠正“数千次”二手摘要为 primary 的300次 |
| 2 记忆与反证 | `"CoThinker" LLM multi agent`; `"MATM" "multi-agent" memory arxiv` | CoThinker v3低负荷负结果；MATM v2在10月15更新，核对只索引成功续轨、排序器有训练 |
| 2 鲁棒与恶意 | `LLM multi agent reliability recovery REVISE malicious agents robustness credit assignment 2026`; `"Robust Multi-Agent LLMs under Byzantine Faults" arxiv` | ICML2025 Resilience、TAMAS ACL2026、SAC v3、ICML2026 activation检测、MAS-FIRE |
| 2 新近补漏 | 搜索结果新作 `Training LLMs for Multi-Agent Collaboration with Verifiable Information Rewards` | 直接打开2610.17893v1，纳入最新观察，未把摘要级证据当成已精读核心 |
| 2 工程训练补漏 | `MARTI A Framework for Multi-Agent LLM Systems Reinforced Training and Inference ICLR 2026 openreview` | 官方代码库核到2026-01-25接收声明与训练结构；primary论文搜索索引有正式出版标记；直接forum/PDF均被browser verification拦截，细节保持S |

未纳入：非 LLM MARL 的经典隐式信用分配论文、名称撞车的 MARS 自动科研与 MARS 策略游戏工作、SSRN“MAPoRL2”转载式候选、仅有二手网页的具体数字；避免主题相近即错误合并。
