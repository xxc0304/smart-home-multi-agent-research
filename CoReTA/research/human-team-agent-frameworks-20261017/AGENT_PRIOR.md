# 人类协作启发的 LLM 多 Agent 框架：直接先例与机制边界

检索日：2026-10-17。角度：BRIEF 的 RQ2 为主，并服务 RQ3。只检索阅读，没有调用模型 API 或实现实验。核心表含 17 个框架/方法，另纳入 2 项校准性研究；选择依据是直接覆盖组织、协作控制、团队认知或讨论协议，不按引用量凑数。本文所称“已有覆盖”只指某种设计已经被明确提出/实现，不等于它已在广泛环境中被证明有效。

## 1. 检索与核查范围

检索词分三轮：框架名称与 SOP/leader/topology；team cognition/transactive memory/organizational theory；Delphi/nominal group/structured dissent/mutual monitoring。经综述与搜索定位后，回到 arXiv 全文、ACL/PMLR 原始论文页面、出版商原文和作者官方仓库；二手页面只用于发现，不支持机制结论。2025—2026 文献优先，但保留形成设计基线的早期工作。

证据标签：**B**=有任务实验的 LLM 方法；**P**=以形式模型/示例为主的提案；**E**=诊断/比较研究。全文可读项核对了方法及评估/局限；DelphiAgent 读取出版商摘要、引言与作者 README，可确认其工作流，但未取得完整评估细节。会议身份按原始会议页面确认者写明，其余称预印本，不把搜索引擎自动日期当发表时间。

## 2. 分类：组织设计要改变什么

用控制对象区分四支，而非把所有方法都叫“专家讨论”：

1. **任务与责任组织**：谁负责哪些依赖任务，按何种交接规范推进。
2. **团队与连接适配**：谁加入/退出、谁领导、哪些消息可见、何时停止。
3. **集体认知基础设施**：谁知道什么、共享什么状态、经验如何跨团队复用。
4. **意见产生与决策程序**：何时保持独立、何时提出异议、如何综合分歧。

这种分类使新框架必须指出自己的实际控制量。把“董事会/研究所/专家组”写进 prompt 只改变角色描述；它不自动带来权限检查、可靠性估计、共同承诺或闭环执行。

## 3. 直接框架先例

### A. 任务、责任与动态团队

| 来源与证据 | 可执行机制 | 实验支持到哪里 | 对新想法的直接约束 |
|---|---|---|---|
| [1] MetaGPT，2023 首发 / ICLR 2024，B | 软件公司角色通过 SOP 推进；结构化文档交接，共享消息池与角色订阅，执行测试反馈。 | HumanEval/MBPP 与小规模软件任务；适合验收产物清楚的工程流程。 | “人类团队分工+SOP+共享黑板+检查”已直接覆盖；不能据此推及动态开放组织。 |
| [2] ChatDev，2023 首发 / ACL 2024，B | Chat chain 把开发分阶段，角色对话完成子任务；仅传阶段解；通过角色反转追问具体信息来修补不清晰指令。 | 软件生成、可执行性及组件消融。 | “虚拟公司”“澄清—执行—测试交接”已有；与 MetaGPT 的关键差别是对话 vs 结构化产物接口。 |
| [3] AgentVerse，2023 首发 / ICLR 2024，B | 招募→共同决策→独立执行→反馈；未完成时按反馈调整成员描述/组成；支持 solver/reviewer 垂直与水平协作。 | 推理、编码、受限生成、工具使用/Minecraft。论文实验中成员数仍人工预设，且数学中更多 reviewer 会错误批评。 | “任务反馈驱动动态专家团队”已有；不能把“动态组成”理解成已解决自治扩缩容。 |
| [4] DyLAN，2310.02170 v2，B | 时间展开网络，多轮中按输出质量保留 Agent 并早停；同伴评分反传为 Agent Importance Score，用于团队优化。 | 推理、代码与决策任务；部分比较复用已有论文结果并以 API 次数估成本。 | “按实际贡献选成员、推理时裁剪团队”已有；角色标签并不保证真实专长。 |
| [5] Embodied LLM Agents Learn to Cooperate in Organized Teams，2403.12482 v2，B | 将组织说明注入 Actor/Communicator；指定/选举领导；Criticize-Reflect 用轨迹与环境成本改组织 prompt。 | VirtualHome；有动态领导/双领导/链结构，以及新任务转移；主环境与团队规模有限。 | “领导不是固定的”“反思优化组织结构”在 2024 已有；效果不能泛化成层级总优。 |
| [6] MegaAgent，2408.09955 v3 / Findings ACL 2025，B | Boss→admin 递归拆任务并招下属，同级并行，组内/组间交流，文件 todo 与层级监控。 | 代码/数学基准、五子棋开发及约 590 Agent 的政策文本生成。后者主要用 LLM 判合理性。 | “自动生成人类式组织图、层层委派与监督、大规模团队”已有；规模不等于社会决策有效或质量因果收益。 |
| [7] Magentic-One，2411.04468 v1，B | Orchestrator 外环 task ledger 记事实/猜测/计划，内环 progress ledger 判完成/循环/进展并派工；停滞触发反思重规划。 | GAIA、AssistantBench、WebArena；同一核心团队跨任务使用。 | “共享态势账本+进度监测+错误恢复”已有强直接先例；中心协调仍是关键瓶颈/失误源。 |

这些方法并非一条“层级越深越先进”的线：MetaGPT 预先规范交接；AgentVerse 改成员；DyLAN 过滤参与者；MegaAgent 扩展任务树；Magentic-One 修订执行计划。它们解决不同控制问题，不能只因都出现 leader 就作等价比较。

### B. 按输入选择结构与组织接口

| 来源与证据 | 可执行机制 | 证据与边界 | 已有覆盖 |
|---|---|---|---|
| [8] MaAS，ICML 2025，B | 学习 agentic supernet 的结构分布；controller 按 query 采样 operator DAG；联合性能/成本优化，支持早退。 | 六基准及跨模型/跨数据集转移。它是受 operator 空间约束的架构搜索，不能自动等同于长期组织适应。 | “不同问题用不同协作组织/推理预算”已经直接学习实现。 |
| [9] AMAS，EMNLP 2025 Industry，B | 从图优化 checkpoint 提取候选图，用真实训练表现构造排序数据，LoRA selector 按样本为候选图打分选择。 | QA、数学、编码等；依赖训练集、候选图及 selector，非无训练的运行时任意重组织。 | “按任务特征自适应拓扑”已有；增量须说明比候选图选择多控制了什么。 |
| [10] IMACS / Toward an Organizational Science…，2607.25446 v1，预印本，B/P | Belbin 角色、Mintzberg 协调、RACI 责任配置与六类协议解耦；LinUCB 按质量—调用成本选协议。 | 真实模型每格 N=10；路由主要可控结果来自合成 oracle，真实在线仅小样本可行性。RACI 只在协议实际读取时生效。 | “把组织理论变为可换配置”“组织与协议解耦”“学任务级组织路由”已有。其接口正交不证明各种组合效果正交。 |
| [11] TB-CSPN / An organizational theory…，Discover Computing 2025，P | 人类 supervisor、LLM consultant、专用 worker 的三层 Petri net；语义 topic 权重过阈值激活/解散组，含滞回与新主题授权。 | 急救、研究、金融为形式化例子；实践实现仍列 future pathways，没有广泛对照实验。 | “按主题自组织+阈值招募+人类监督”已有形式先例；其有效性待实证，而非思想无人提出。 |

IMACS 和 TB-CSPN 尤其需要分清**设计表达能力**与**效果证据**。前者能把多个组织变量变成配置，后者能把参与条件变成形式规则；都不意味着其组织理论标签已经被独立验证为提升任务效果的原因。

### C. 团队认知、知识分工与监控

| 来源与证据 | 可执行机制 | 证据与边界 | 已有覆盖 |
|---|---|---|---|
| [12] CoThinker / United Minds or Isolated Agents?，2506.06843 v2，2025 预印本，B | 任务化 thinking styles；TMS Manager 维护贡献者目录、共同知识、未解分歧；固定入度+语义相近邻居/随机重连，最后 synthesis。 | 三种 Gemini、LiveBench 与 CommonGen-Hard；instruction following 可下降。认知负荷是解释类比，未证明 LLM 具有人类心理同构。 | “who-knows-what+共享心理模型+小世界动态交流”已有相当直接实现。 |
| [13] Multi-Agent Transactive Memory (MATM)，2606.19911 v1，2026 预印本，B | 异质生产者贡献轨迹，消费者按当前状态检索；LTR 以实际任务增益监督，含生产者元数据/消费者特征。 | ALFWorld/WebArena，34 模型消费者；跨 benchmark reranker 迁移、恶意生产者、生产者福利未测。 | 跨 Agent 经验库/程序知识重用已有；其 population memory 不同于单次团队内谁掌握当前证据。 |
| [14] TeamMedAgents，2508.08115 **v3**，2026 预印本，B | Salas 团队理论落实为领导、共同任务/团队模型、团队导向、信任网络、相互监控；独立判断后讨论，信任/专长加权 Borda。 | 八医疗 QA/VQA，Gemma/MedGemma/GPT-4o；主配置固定全部组件，组件消融小子集；无充分统计检验与前瞻临床验证。 | “系统整合 Big Five 团队机制”“共享心智+监控+信任+角色权重”已有；自适应组件选择仍未充分解决。 |

CoThinker 与 MATM 都使用 transactive memory，但对象不同：前者让一个当前团队知道伙伴贡献与悬而未决的问题，后者让开放种群重用历史轨迹。新“团队记忆”必须先说明它记的是能力、证据、承诺还是技能，以及更新失败由谁检测。

**版本核对：**TeamMedAgents v1（2025-08）旧题为 *Enhancing Medical Decision-Making of LLMs Through Structured Teamwork*，含六组件、closed-loop communication 独立模块；v3 更名 *Pareto-Efficient Multi-Agent Medical Reasoning Through Teamwork Theory*，正文为五组件，重心转向小模型效率。不可把 v1 的配置结论与 v3 的样本、效率结果混写。v3 表中有未完成对照/估计，不能从作者的 deployment-ready 措辞推断临床效果。

### D. 独立意见、异议与开放决策

| 来源与证据 | 可执行机制 | 证据与边界 | 已有覆盖 |
|---|---|---|---|
| [15] DelphiAgent，IP&M 2025，B（部分全文） | 证据挖掘/精炼后，多种 personality Agent 独立判断，再反馈/综合多轮达共识；作者明确采用 Delphi。 | RAWFC/LIAR-RAW 事实核查；未在本轮获得完整统计与资源控制详情。 | “匿名/独立专家+反馈多轮共识”的 Delphi 式框架已有；改领域或改名字不构成机制创新。 |
| [16] Catfish Agent / Silence is Not Consensus，2505.21503 v1，2025 预印本，B | Moderator 按难度决定批评者权限/团队层次，Catfish 监测无根据共识，按共识程度调整异议强度。 | 医疗 hard QA 与 VQA，多数是离线问答；多模型基线/调用预算不全相同，不能把全部增益归因于异议。 | “devil’s advocate+按需介入+动态异议强度”已直接覆盖。 |
| [17] TeamFusion，ACL 2026 / 2604.19589 v1，B | 以人的偏好证据实例化 proxy，round-robin 等额发言，显化异同，Remix 出可编辑产物，再让人或代理批评迭代。 | 公民评论综合、视觉设计与用户评价；现实现假设平级，不处理资历/正式权力。 | “开放任务多元偏好协商、保留少数观点再收敛”已有；并非只做标准答案投票。 |

同称 NGT 不代表同样的协议：TeamFusion 主要以等额顺序发言引用 NGT；[19] 的 NGT 则明确首轮盲写、再让非领导者讨论、后引入领导。后者改变信息可见性和影响顺序，机制比一个“轮流发言”标签更强。DelphiAgent 的事实正确性目标与 TeamFusion 的偏好代表性目标也不应混为“共识越高越好”。

## 4. 两项必须用于校准的直接研究

**[18] Voting or Consensus? Decision-Making in Multi-Agent Debate（Findings ACL 2025，E）**保持其余因素尽可能一致比较七种决策协议。推理与知识任务偏好不同；增加讨论轮数并不保证提高结果，作者另用 All-Agents Drafting 与 Collective Improvement 促进答案多样性。因此，“讨论之后再投票”的默认终局本身也应是待选择的制度变量，而不是协作的普遍终点。

**[19] Diversity Collapse in Multi-Agent LLM Systems（Findings ACL 2026 / 2604.18005 v2，E）**在科学研究构思中检验模型、角色/层级、通信结构造成的耦合；盲写 NGT 与子群隔离提高多样性。质量主要由模型 judge 判、人工验证主要针对多样性，且任务是研究 proposal，故不能把其结果外推为层级组织在所有任务上有害。它与 [5] 的层级效率收益并不矛盾：一个重执行协调，一个重探索覆盖。

## 5. 人类理论参考链：已经被谁实际调用

下表只声称**已在上述原始 Agent 论文中核对到引用及对应机制**；人类理论原著的独立核查由团队科学角度另行完成，不能把 Agent 论文的引用当作人类因果效应证明。

| 人类理论/技术链 | Agent 论文明确连接 | 应继续追查的原始问题 |
|---|---|---|
| Belbin 团队角色；软件 SOP/Agile 与团队工程实践 | MetaGPT；IMACS 另把 Belbin 角色设为配置 | 人类角色互补在相同底模角色 prompt 中是否仍产生互补能力？ |
| Mintzberg 五种协调机制、RACI | IMACS | 责任标签是否真的改变执行路径和问责，而非只改措辞？ |
| 人类 group dynamics、团队多样性 | AgentVerse 引 Woolley et al. 2015、Phillips & O’Reilly 1998 | 成员数量与能力/信息多样性应分离；更多 reviewer 可更坏。 |
| Wegner 1987；Hollingshead 2001；Lewis 2003 的 TMS | CoThinker；MATM 明确引 Wegner | 谁知道什么的定位准确性、过时能力信息、信誉校准与错误修复。 |
| Sternberg 1997 thinking styles；Kirschner 的 collaborative cognitive load；Watts–Strogatz 小世界；弱连接/结构洞 | CoThinker 的风格、消息预算与重连 | 语义距离是否代表对任务有用的新信息，而非仅文字差异？ |
| Salas, Sims & Burke 2005 团队 Big Five；SMM、monitoring、trust | TeamMedAgents | 行为可执行定义与测量是否相符；backup/adaptability 如何在持续协同执行中真正产生作用？ |
| Delphi（作者引 Thangaratinam & Redman 2005） | DelphiAgent | 匿名、独立性、反馈统计、共识标准是否逐项实现，还是只保留多轮反馈？ |
| NGT / Delbecq–Van de Ven–Gustafson；divergence–convergence | TeamFusion；Diversity Collapse | 独立产生、等额表达、分组隔离、最后综合各自的作用。 |
| devil’s advocate、Socratic inquiry、diagnostic timeout | Catfish Agent | 如何区分有证据的异议与为反对而反对；何时应停止异议？ |

## 6. 创意去重与值得继续深化的条件

### 已有直接覆盖，不能单独用作贡献

| 可能的框架口号 | 最接近直接方法 | 需要避免的误判 |
|---|---|---|
| 模仿公司分工与标准流程 | MetaGPT、ChatDev | 角色名称/部门数量不是方法增量。 |
| 自动建组织、动态招募、领导轮换 | AgentVerse、MegaAgent、Organized Teams | “动态”有不同对象：成员、规模、领导、计划。 |
| 任务决定拓扑、预算或协作协议 | DyLAN、MaAS、AMAS、IMACS | 输入自适应已拥挤；需要比较训练成本与可用反馈。 |
| 共享团队状态、谁知道什么、复用经验 | Magentic-One、CoThinker、MATM | 共享上下文不自动产生可靠事实、可靠能力目录。 |
| 共享心智、信任、相互监督的团队框架 | TeamMedAgents | 人类理论整合本身已有；需要具体控制目标与行为证据。 |
| 防群体迷思、保留少数观点、独立思考再讨论 | Catfish、TeamFusion、DelphiAgent、Diversity Collapse、Voting or Consensus | 讨论形式、信息可见性、何种最终目标必须明确。 |

### 可继续深化的机制问题（尚非创新性结论）

**A. 从“描述组织”到“依赖变化时重配责任与承诺”。**现有方法大多把组织视为图、角色或调度策略。值得深化的是，执行中某个前提失效后，哪些任务/团队必须被通知，承诺怎样撤回，谁临时接管，何时恢复原组织。最近邻至少包括 Magentic-One、MegaAgent、Organized Teams，根侧另读的 ORCH（2609.11737）直接研究任务互依与组织，不能宣称 task-interdependence 视角空白。增量必须发生在状态变化和协调义务上，不能只是再选一张图。

**B. 具有可校准失效的“谁知道什么”。**CoThinker 已有专家目录，MATM 已有生产者/消费者特征与基于增益的排序。仍可追查：能力目录遇到模型更新、陌生工具、证据过期时如何自我纠错；把“某 Agent 曾贡献过内容”当“现在应信任谁”容易错误。必须比基于共识/角色的信誉更接近真实可用能力，并处理误路由后怎样修复；本轮尚不足以断言未有人完成。

**C. 保留独立性与及时整合之间的自适应控制。**NGT 盲写、子群隔离、Catfish 介入与 TeamFusion 迭代都已有。值得深化的是执行时什么可观测信号能区分“必要协调”与“过早耦合”，从而有针对性地开放证据、合并团队或重新隔离。若只设置固定几轮独立/固定几轮辩论，或从现有协议中换路由器，增量会接近已有拓扑与协议选择。

**D. 有实际行动和可恢复结果的 mutual monitoring / backup。**TeamMedAgents 已把 monitoring 落成 peer review，但它主要回答离线题；Magentic-One 已有中央进展监控。可以继续查组织层面的监控覆盖分配、监控者失效、有限注意力、协助接管与恢复成本。新机制应说明“观察者怎么得到独立证据、什么时候有权打断、交接何种状态”，而不是简单加一个 reviewer。它广泛关联软件、研究和业务任务，未必绑定医疗或家庭场景。

这些方向都应先用最近邻的机制级对照判断是否有实质变化，再确定研究对象；目前没有足够证据冻结其中一个，也没有证据要求必须做 benchmark。

## 7. 来源核查表（原始 URL 与读取层级）

| # | 完整题名 / 原始入口 | 核对层级 |
|---|---|---|
| 1 | Hong et al., *MetaGPT: Meta Programming for a Multi-Agent Collaborative Framework*. https://arxiv.org/html/2308.00352v6 | 全文 §3、§4、附录局限；ICLR 身份另见作者论文记录。 |
| 2 | Qian et al., *ChatDev: Communicative Agents for Software Development*. https://arxiv.org/html/2307.07924v5 ; https://aclanthology.org/2024.acl-long.810/ | 全文 §3.1–3.2、§4；ACL会议页核对。 |
| 3 | Chen et al., *AgentVerse: Facilitating Multi-Agent Collaboration and Exploring Emergent Behaviors*. https://arxiv.org/html/2308.10848v2 | 全文方法、实验设置与 reviewer/人数限制。 |
| 4 | Liu et al., *A Dynamic LLM-Powered Agent Network for Task-Oriented Agent Collaboration*（早期题名 Dynamic LLM-Agent Network…）. https://arxiv.org/html/2310.02170v2 | 全文团队优化、Agent Importance Score、附录 B/C；作者仓库 https://github.com/SALT-NLP/DyLAN 。 |
| 5 | Guo et al., *Embodied LLM Agents Learn to Cooperate in Organized Teams*. https://arxiv.org/html/2403.12482v2 | 全文 §3、§4.4、§5，动态组织与泛化范围。 |
| 6 | Wang et al., *MegaAgent: A Large-Scale Autonomous LLM-based Multi-Agent System Without Predefined SOPs*（早期题名 A Practical Framework…）. https://arxiv.org/html/2408.09955v3 ; https://aclanthology.org/2025.findings-acl.259/ | 全文 §2、§3.3、Limitations，政策 judge/规模/成本；Findings ACL会议页核对。 |
| 7 | Fourney et al., *Magentic-One: A Generalist Multi-Agent System for Solving Complex Tasks*. https://arxiv.org/html/2411.04468v1 | 全文 §4.1/4.2、实验摘要。 |
| 8 | Zhang et al., *Multi-agent Architecture Search via Agentic Supernet*. https://proceedings.mlr.press/v267/zhang25bi.html ; https://arxiv.org/html/2502.04180v1 | PMLR会议信息；全文 §3/4，搜索空间/训练/转移。 |
| 9 | Leong et al., *AMAS: Adaptively Determining Communication Topology for LLM-based Multi-agent System*. https://aclanthology.org/2025.emnlp-industry.144/ ; https://aclanthology.org/2025.emnlp-industry.144.pdf | 原始 PDF §3.3、§4，候选图、LoRA 排序 selector 与数据切分。 |
| 10 | Huan Chen et al., *Toward an Organizational Science of Multi-Agent LLM Systems: Decoupling Who, How, and Which Algorithm*. https://arxiv.org/html/2607.25446v1 | 全文配置、真实/合成试验及 Discussion and Limitations。 |
| 11 | Borghoff, Bottoni & Pareschi, *An organizational theory for multi-agent interactions integrating human agents, LLMs, and specialized AI*. https://link.springer.com/article/10.1007/s10791-025-09667-2 | 出版商全文 §4、§6–9；2025-07-03 发表；形式例子与未来实现分开。 |
| 12 | Shang et al., *United Minds or Isolated Agents? Exploring Coordination of LLMs under Cognitive Load Theory*. https://arxiv.org/html/2506.06843v2 | 全文 §4/5，附录 D.3–D.6（TMS 模板、风格与图构造）。 |
| 13 | To Eun Kim et al., *Multi-Agent Transactive Memory*. https://arxiv.org/html/2606.19911v1 | 全文 §3、实验、Limitations；原始作者库 https://github.com/kimdanny/matm 。 |
| 14 | Mishra, Arvan & Zalake, *TeamMedAgents: Pareto-Efficient Multi-Agent Medical Reasoning Through Teamwork Theory*. https://arxiv.org/html/2508.08115v3 | v3 §3、表1、§5.1；v1 https://arxiv.org/html/2508.08115v1 用于版本差异核对。 |
| 15 | Xiong et al., *DelphiAgent: A trustworthy multi-agent verification framework for automated fact verification*. https://www.sciencedirect.com/science/article/pii/S0306457325001827 ; DOI https://doi.org/10.1016/j.ipm.2025.104241 | 出版商摘要/引言/结论与作者 README https://github.com/zjfgh2015/DelphiAgent/blob/main/README.md ；全文细节有限。 |
| 16 | Wang et al., *Silence is Not Consensus: Disrupting Agreement Bias in Multi-Agent LLMs via Catfish Agent for Clinical Decision Making*. https://arxiv.org/html/2505.21503v1 | 全文 §3/4/5；无微调，多 agent 使用 o3-mini，离线医疗评估。 |
| 17 | Liu et al., *TeamFusion: Supporting Open-ended Teamwork with Multi-Agent Systems*. https://aclanthology.org/2026.acl-long.657/ ; https://arxiv.org/html/2604.19589v1 | 全文 §3、两任务设置、Limitations；Microsoft原始作者页 https://www.microsoft.com/en-us/research/publication/teamfusion-supporting-open-ended-teamwork-with-multi-agent-systems/ 。 |
| 18 | Kaesberg et al., *Voting or Consensus? Decision-Making in Multi-Agent Debate*. https://aclanthology.org/2025.findings-acl.606/ | 原始会议页完整摘要与方法比较范围；未据摘要推测具体七协议实现细节。 |
| 19 | Chen et al., *Diversity Collapse in Multi-Agent LLM Systems: Structural Coupling and Collective Failure in Open-Ended Idea Generation*. https://aclanthology.org/2026.findings-acl.13/ ; https://arxiv.org/html/2604.18005v2 | 全文 §5.2、NGT附录、Limitations，模型 judge/人工验证轴分开。 |

## 8. 自我反证检查与待补查

- 组织有用还是只是更多计算？本轮框架的成本定义、底模、任务差异很大，不能横向拼一张胜负榜。
- 人类理论究竟解释还是实施？本文把 topic-Petri 的形式约束、RACI 的程序读取、TMS 的模板记忆、NGT 的信息屏蔽分开，避免靠名称认定落地。
- 框架中有未验证引用？TeamMedAgents 等论文的参考表包含多个概括性条目；这里只把参考表当追链种子，未独立核验的人类文献不计入已验证核心语料。
- 尚需精读而不作空白断言：ORCH（2609.11737，根侧负责）；持续执行下的 backup/临时接管；分布式知识下组织记忆失真；真实多人偏好冲突与权力差异。

最后回答本角度的 RQ2：人类团队启发已经从角色命名扩展到可执行 SOP、消息可见性、成员选择、领导控制、共享知识结构、批评介入与偏好综合。可继续深化的 RQ3 是这些机制在动态互依、异质能力和有限监控下如何**知道何时需要改变，以及改变后如何维持可验证协调**；单纯把更多人类协作术语装入一个新框架，已有先例十分接近。
