# 智慧家庭 Agent 文献矩阵

版本：v0.6

说明：本表是综述写作过程中的内部工作表，不是最终论文中的表格。当前记录包括原 Word 中的 19 篇主文献、2 篇背景文献，以及本轮检索补充的历史和代表性论文。v0.6 在 v0.5 的基础上完成了 H21、H27 的公开全文阅读和出处交叉核对，并更新了证据句、局限句和分类；“预印本”仍不等同于正式发表。

## 分类标签

- 核心候选：直接研究智慧家庭 Agent、家庭自动化 Agent、家庭仿真 Agent 或家庭任务执行。
- 相关候选：研究智能环境、家庭物联网、普适计算、家庭能源或照护，与主题有直接联系，但不一定以 Agent 为核心。
- 背景候选：通用 Agent、多智能体规划、调度或实时控制，可用于解释方法来源，但不作为智慧家庭证据。
- 待核验：已从现有 Word 或检索结果发现，但尚未完成正式出版信息、全文方法或评测细节核对。
- 核心候选（预印本）：已核对官方摘要和版本信息，但目前仅有 arXiv 记录。

## 文献矩阵

| ID | 文献 | 年份与来源 | 场景关联 | Agent层级 | 主要问题或任务 | 方法/系统 | 动态或执行因素 | 数据集/评测 | 初步用途 | 状态 |
|---|---|---|---|---|---|---|---|---|---|---|
| H01 | HomeBench: Evaluating LLMs in Smart Homes with Valid and Invalid Instructions Across Single and Multiple Devices | 2025, ACL Long Paper | 直接智慧家庭 | 单 Agent 评测 | 家庭指令执行、设备控制、无效指令识别 | 可配置虚拟家庭、API 操作序列 benchmark | 单/多设备、有效/无效/混合指令、1–10 个设备、错误操作拒绝 | 约 17.36 万条指令、100 个家庭场景、13 个 LLM；Succ、操作级 F1、RAG/ICL/LoRA | 家庭任务执行基准 | 核心候选（正式发表，全文已读） |
| H02 | SimuHome: A Temporal- and Environment-Aware Benchmark for Smart Home LLM Agents | 2025/2026, arXiv v3；页面标注 ICLR 2026 Oral | 直接智慧家庭 | 单 Agent/环境交互 | 动态家庭环境中的任务执行 | Matter 风格设备仿真、时间加速 benchmark | 连续环境变化、工作流调度、可行/不可行请求 | 600 episodes、18 个 Agent、类别成功率 | 动态环境评测 | 核心候选（会议录用标注，已核验） |
| H03 | HomeFlow: A Data Flywheel for Smart Home Agent Training with Verifiable Simulation | 2026, arXiv v1 | 直接智慧家庭 | 单 Agent 训练 | Agent 训练数据生成、可验证轨迹和多轮策略优化 | HomeEnv、HomeMaker、Blueprint、MCTS-Flow、SFT + step-wise RLVE | 部分可观测、连续/离散状态、轨迹验证、逐步奖励、动态用户模拟器 | SmartHome-Bench：1,678 个测试实例、5 类/18 子类；HomeFlow-RL-4B/8B 为 84.60%/87.03% | 可验证训练数据、动态仿真和环境反馈学习 | 核心候选（预印本，全文已读） |
| H04 | SAGE: Smart Home Agent with Grounded Execution | 2023/2024, arXiv v2 | 直接智慧家庭 | 单顶层 LLM Agent + 分层 agent-tools | 家庭任务理解、设备 API 操作、个性化、设备消歧、持久命令和命令链 | 动态提示树；LLM 选择工具和控制流；SmartThings API 文档检索；设备状态反馈；代码写入与轮询 | 离散工具执行、API 异常恢复、设备状态修改；评测中采用初始化状态和自动化测试，不包含连续环境动力学 | 50 个任务、5 个 LLM、每任务 3 次；二元 pass/fail；GPT-4 成功率约 75%，基线约 30% | LLM 家庭 Agent 的 grounded execution、工具层级和任务分类代表作 | 核心候选（预印本，全文已读） |
| H05 | SMH-Bench: Benchmarking LLM Agents for Environment-Grounded Reasoning and Action in Smart Homes | 2026, arXiv v1 | 直接智慧家庭 | 单 Agent 评测 | 家庭环境推理、控制、问答、歧义澄清、自动化、记忆 | HomeEnv 可执行仿真、7 类任务 taxonomy、DR/EIA 双评测 | 部分可观测、状态转移、复杂家庭、对话历史、用户记忆、时间/状态触发自动化 | 1,100 个人工审查任务、7 类、22 个子类、13 个 LLM；简单/中等/复杂家庭最多 135 个设备 | 家庭 benchmark 扩展和环境接地评测 | 核心候选（预印本，全文已读） |
| H06 | PersonalHomeBench: Evaluating Agents in Personalized Smart Homes | 2026, arXiv v3 | 直接智慧家庭 | 单 Agent + 工具箱内专门模块 | 个性化家庭问答、反事实推理、家电功能推荐、主动计划生成 | PersonalHomeBench + PersonalHomeTools；家庭信息/记忆/事件检索、视频理解、40+ 类家电控制；对比 Sole Reasoning 与 Agentic With Tools | 用户偏好、长期记忆、部分可观测、单/多模态观察、设备和情境变化；每任务最多 15 轮工具交互 | 1,100 个家庭、2,000+ 成员画像、9,168 个任务（6,000 文本/3,168 多模态）、100 个家庭真实视频、11 个模型；Accuracy、MAP@1、Role-Playing Judge、计划 validity | 个性化和主动式家庭 Agent 评测；解释工具接地、计划质量与可执行性的差异 | 核心候选（预印本，全文已读） |
| H07 | REALM-Bench: A Benchmark for Real-world Dynamic Planning and Scheduling | 2025, arXiv | 间接相关 | 单/多 Agent 规划 | 动态规划、调度、Job-Shop 任务 | 现实约束规划 benchmark | 截止时间、资源约束、扰动 | 规划质量、鲁棒性 | 可迁移方法背景 | 相关候选 |
| H08 | DynTaskMAS: A Dynamic Task Graph-driven Framework for Asynchronous and Parallel LLM-based Multi-Agent Systems | 2025, arXiv | 间接相关 | 多 Agent | 动态任务图、异步并行执行 | 动态 DAG、任务图管理器 | 异步执行、任务变化、资源约束 | 执行时间、并行效率 | 多 Agent 方法背景 | 背景候选 |
| H09 | MultiAgentBench: Evaluating the Collaboration and Competition of LLM Agents | 2025, ACL Long Paper | 间接相关 | 多 Agent | 协作、竞争、组织和通信 | 多 Agent benchmark | 协作冲突、通信、组织 | 协作 KPI、成功率 | 多 Agent 评测背景 | 背景候选 |
| H10 | SagaLLM: Context Management Validation and Transaction Guarantees for Multi-Agent LLM Planning | 2025, arXiv | 间接相关 | 多 Agent | 上下文管理、事务保证、规划执行 | 事务式 Agent 规划 | 状态一致性、回滚、恢复 | 规划和执行可靠性 | 执行一致性背景 | 背景候选 |
| H11 | ALAS: Transactional and Dynamic Multi-Agent LLM Planning | 2025, arXiv | 间接相关 | 多 Agent | 动态规划、局部修复 | 事务式规划和动态修复 | 执行日志、版本、局部重规划 | 修复效果、成功率 | 计划修复背景 | 背景候选 |
| H12 | SyncPlan: Long-Horizon LLM Coordination with Explicit Synchronization | 2026, arXiv | 间接相关 | 多 Agent | 长时域协调、同步和等待 | 显式同步和计划协调 | 异步执行、等待、计划拒绝 | 长时域成功率 | 多 Agent 协同背景 | 背景候选 |
| H13 | VeraRAN: Pre-Actuation Certification and Event-Causal Synchronization Repair | 2026, arXiv | 间接相关 | 多 Agent/执行系统 | 执行前认证、同步修复 | 版本控制、事件因果同步 | 状态变化、执行安全、截止时间 | 认证和修复指标 | 安全执行背景 | 背景候选 |
| H14 | Agent JIT Compilation for Latency-Optimizing Web Agents | 2026, ICML | 非家庭场景 | 单 Agent | 工具调用、计划编译和延迟优化 | JIT 计划编译、延迟感知 | 延迟分布、并行和 hedging | 延迟、成功率 | 低时延方法背景 | 背景候选 |
| H15 | Speculative Actions: A Lossless Framework for Faster Agentic Systems | 2025, arXiv | 非家庭场景 | 单/多 Agent | 预测式工具调用和加速 | speculative action、预执行验证 | 状态版本、提交和回滚 | 延迟、正确性 | 低风险预执行背景 | 背景候选 |
| H16 | Win Fast or Lose Slow: Balancing Speed and Accuracy in Latency-Sensitive Decisions | 2025, NeurIPS | 非家庭场景 | Agent/决策系统 | 延迟与准确率权衡 | 混合关键性决策 | 截止时间、尾部延迟 | P95、P99、成功率 | 实时性背景 | 背景候选 |
| H17 | HearthNet: Edge Multi-Agent Orchestration for Smart Homes | 2026, ACM CAIS ’26，5 页；同时有 arXiv v2 | 直接智慧家庭 | 多 Agent | 家庭边缘 Agent 编排、冲突处理、授权和故障恢复 | Root/Manager/Librarian 角色 Agent；MQTT 通信；Git 共享状态；root-issued actuation lease；设备薄适配器 | 持久事件驱动、状态新鲜度、权限边界、定时冲突、Agent 崩溃恢复 | 4 个 Agent、约 10 个设备、3 个真实 live scenarios；Scene 1 完成率 4/5，中位延迟 8 秒；冲突 5/5，过期命令/lease 拒绝 5/5 | 家庭多 Agent 架构、可靠执行和边缘部署 | 核心候选（正式会议论文，全文已读） |
| H18 | When Do LLM Agents Help: Deadline-Aware Mixed-Criticality Task Scheduling at the Autonomous-Vehicle Edge | 2025/2026, arXiv | 非家庭场景 | 单/多 Agent | 截止时间调度、混合关键任务 | 形式化约束和 LLM 调度 | 截止时间、任务关键性 | 调度成功率、延迟 | 方法迁移背景 | 背景候选 |
| H19 | Bridging Large-Model Reasoning and Real-Time Control via Agentic Fast-Slow Planning | 2026, arXiv | 间接相关 | 单 Agent/分层 Agent | 大模型推理和实时控制衔接 | Fast-Slow Planning、MPC | 实时控制、设备状态、权限 | 控制延迟、计划安全 | 分层控制背景 | 相关候选 |
| B01 | LLMCompiler | 2024, ICML | 非家庭场景 | 单 Agent/工具调用 | 计划生成、提取和并行执行 | 编译式 Agent 规划 | 工具调用、并行执行 | 计划执行效率 | 规划方法背景 | 背景候选 |
| B02 | Multi-Agent Path Finding with Deadlines | 2018, IJCAI | 非家庭场景 | 多 Agent | 截止时间下的路径规划 | 多 Agent 路径规划 | 空间冲突、截止时间 | 路径规划成功率 | 约束调度背景 | 背景候选 |
| H20 | MavHome: An Agent-Based Smart Home | 2003, IEEE PerCom | 直接智慧家庭 | 家庭整体单 Agent | 居民行为预测、家庭自动化 | 家庭整体 Agent、预测算法 | 家庭状态感知、行为适应 | 智慧家庭数据、预测效果 | 早期历史基础 | 核心候选（正式发表，已核验） |
| H21 | Health Monitoring in an Agent-Based Smart Home by Activity Prediction | 2004, ICOST 2004 会议章节；Assistive Technology Research Series 14，IOS Press，pp. 3–14 | 直接智慧家庭 | 家庭整体/分层 Agent（MavHome） | 活动预测、健康监测、异常检测和提醒辅助 | MavHome 分层 Agent 架构；ED 显著事件挖掘；ALZ 序列预测；异常评分 | 传感器数据、活动噪声、长期趋势、异常事件、提醒与照护者介入 | 合成数据、UTA MavHome 真实数据；6 名参与者的规律活动；20 名学生/50 台设备高噪声数据；ED/ALZ 准确率与处理时间 | 早期家庭 Agent、预测—监测—辅助闭环和健康照护基础 | 核心候选（正式会议章节，全文已读；未在 Crossref 精确题名检索中找到 DOI） |
| H22 | A Mobile-Agent Based Distributed Intelligent Control System Architecture for Home Automation | 2001, IEEE SMC | 家庭自动化 | 多/移动 Agent | 分布式家庭控制 | 移动 Agent、分布式控制 | 设备通信、实时控制 | IEEE SMC 2001，pp. 1599–1605 | 早期多 Agent 基础 | 相关候选（书目已核验，全文待核验） |
| H23 | A Multi-agent Home Automation System for Power Management | 2008, Springer 会议章节 | 家庭自动化 | 多 Agent | 家庭电力资源管理 | 设备/资源 Agent、协商与协调 | 可用功率、舒适度、成本、紧急约束 | 初步仿真；紧急机制与预见机制 | 能源管理基础 | 相关候选（正式章节，已核验） |
| H24 | A Multi-Agent-Based Intelligent Sensor and Actuator Network Design for Smart House and Home Automation | 2013, Journal of Sensor and Actuator Networks | 直接智慧家庭 | 多 Agent | 传感器、执行器和家庭自动化 | BDI、协同策略、Petri-net、JADE | 响应时间、能源、QoS | QoS、计算时间、系统成本；含 testbed | 架构和指标基础 | 核心候选（正式发表，已核验） |
| H25 | Combining a Multi-Agent System and Communication Middleware for Smart Home Control: A Universal Control Platform Architecture | 2017, Sensors | 直接智慧家庭 | 多 Agent | 异构设备协同控制 | IAPhome、多 Agent、中间件 | 异构设备、协同控制、人机交互 | 真实智慧家庭实验室、协同控制效果 | TPCI 高相关基础 | 核心候选（正式发表，已核验） |
| H26 | Modelling an Adjustable Autonomous Multi-Agent Internet of Things System for Elderly Smart Home | 2019 online / 2020 Springer 会议章节 | 直接智慧家庭 | 多 Agent | 老年家庭 IoT 服务 | Adjustable-Autonomous Multi-agent IoT；AAMA-IoT | 用户偏好、时间/日期、老人家庭环境 | 模拟控制 14 类设备；平均活动识别准确率 96.97% | 老年照护和 IoT | 相关候选（正式章节，已核验） |
| H27 | Distributed Multi-Agent Optimization for Smart Grids and Home Automation | 2019, Intelligenza Artificiale 12(2), 67–87 | 家庭自动化/能源 | 多 Agent（每个家庭作为一个协作 Agent） | 智能家居设备调度、需求响应和削峰 | DCOP；Multi-Variable Agent（MVA）分解；GPU 加速；SH-MGM | 实时电价、主动/被动调度规则、设备状态轨迹、邻居协作、局部成本与全局峰值权衡 | 9 类可调设备+5 类传感器；H=12；Raspberry Pi 2/JADE 物理实验；三城市密度合成微电网；峰值、成本、周期收敛 | 家庭能源多 Agent、分布式调度建模和协作收益 | 相关候选（正式期刊，全文已读） |
| H28 | Generating and Evaluating Data of Daily Activities with an Autonomous Agent in a Virtual Smart Home | 2024 online / 2025 TOMM Vol. 21(1), ACM | 直接智慧家庭 | 单 BDI Agent | 虚拟居民活动、合成数据 | Unity 3D 家庭、BDI、调度器 | 自主性、可控性、活动中断 | Orange4Home、C2ST、活动识别和预测 | 仿真和评测基础 | 核心候选（正式发表，已核验） |

## 本轮官方核验记录

以下记录用于防止把搜索摘要、arXiv 预印本和正式出版物混写。作者、题名、出处和摘要证据来自下列官方页面；“会议录用”只在页面明确标注时记录，未把它扩大解释为正式 proceedings 信息。

| ID | 作者/正式出处 | DOI 或官方页面 | 已核对的关键证据 | 当前判断 |
|---|---|---|---|---|
| H01 | Silin Li, Yuhang Guo, Jiashu Yao, Zeming Liu, Haifeng Wang；ACL 2025 Long Paper，页 12230–12250 | [ACL Anthology](https://aclanthology.org/2025.acl-long.597/)；DOI `10.18653/v1/2025.acl-long.597` | HomeBench 将指令分为 VS（有效单设备）、IS（无效单设备）、VM（有效多设备）、IM（无效多设备）和 MM（混合多设备）五类。作者构造 100 个虚拟家庭场景，每个场景至少包含 47 个可操作设备、至少 10 种设备类型，累计约 17.36 万条指令；13 个 LLM 按 API 操作序列评估，指标包括整条指令成功率 Succ 和操作级 F1。 | 论文把“多设备”理解为一条指令涉及多个设备，而不是多个自治 Agent；因此是单 Agent 多设备任务 benchmark。原始 GPT-4o 在 IM 的 Succ 为 0.00%，加入 ICL 后提升到 61.86%，说明该结果是完整无效多设备指令的严格成功定义，不等于模型完全不会识别错误。主要边界是英文虚拟环境、设备品牌差异未建模，以及 API 层功能等价不等同于真实家庭中的连续动力学、时间调度和物理反馈。 |
| H02 | Gyuhyeon Seo, Jungwoo Yang, Junseong Pyo, Nalim Kim, Jonggeun Lee, Yohan Jo；arXiv v3 | [arXiv:2509.24282](https://arxiv.org/abs/2509.24282)；页面 comments 标注 “Accepted at ICLR 2026 (Oral)” | 600 episodes；Matter 风格设备；状态查询、隐式意图、显式控制、工作流调度四类，均含可行/不可行请求；评估 18 个 Agent；工作流调度最难。 | 动态家庭环境 benchmark 核心文献；在正式参考文献中保留 arXiv 版本，同时注明页面的 ICLR 2026 Oral 标注。 |
| H03 | Yi Gu, Huacan Wang, Shuo Zhang, Yuqing Hou, Lei Xue, Weipeng Ming, Chen Liu, Fangzhou Yu, Kuan Li, Ronghao Chen, Sen Hu, Xiaofeng Mou, Yi Xu；arXiv v1，2026-05-31 | [arXiv:2606.01230](https://arxiv.org/abs/2606.01230) | HomeEnv + HomeMaker + Blueprint + MCTS-Flow + SFT/step-wise RLVE 构成可验证数据飞轮；任务被建模为部分可观测家庭环境中的目标导向序列决策。SmartHome-Bench 含 1,678 个测试实例、5 个任务族和 18 个子类，覆盖 Atomic Control、Compositional Control、Ambiguous Intent、Context-Aware Multi-turn Interaction 和 Personalized Memory。 | HomeFlow-RL-4B/8B 的主要成功率为 84.60%/87.03%；Blueprint 将数据生成成功率从 86.33% 提升到 92.43%，MCTS-Flow 后达到 96.48%；step-wise RLVE 比 SFT 和只在最终步骤更新的 RL 更好。限制是确定性仿真、sim-to-real、厂商协议和计算开销；论文代码标注 Coming soon。它是单 Agent 训练/仿真论文，不是多 Agent 协同证据；第 9 页结论中的 84.20% 与表格/正文的 84.60% 存在内部不一致。 |
| H04 | Dmitriy Rivkin, Francois Hogan, Amal Feriani, Abhisek Konar, Adam Sigal, Xue Liu, Gregory Dudek；arXiv v2，2024-01-19 | [arXiv:2311.00772](https://arxiv.org/abs/2311.00772) | SAGE 的顶层 agent-tool 接收用户请求，通过动态构造的 LLM prompt tree 反复选择工具、读取输出并决定下一步或终止。工具分为个性化、设备交互、监测和外部交互四类；设备交互 agent-tool 还包含规划、API 文档检索、属性读取、命令执行和设备消歧等子工具。监测工具可让 LLM 写入 Python 条件检查代码，并由轮询器在条件满足时再次触发 SAGE。 | 50 个测试任务覆盖个性化、意图解析、设备解析、持久性、命令链和直接命令；设备配置包含 2 台电视、1 台冰箱、1 台洗碗机和 4 盏灯；每个任务由 5 个 LLM 各运行 3 次，结果为二元通过/失败；GPT-4 的总体成功率约 75%，基线约 30%，另有 10 个额外测试任务检验提示是否过拟合。 | 全文明确支持“单顶层 Agent + 分层工具/子 Agent”的分类，而不是平级多 Agent 协同。评测依赖固定设备快照和离散状态修改，禁用人工交互工具，未模拟连续环境变量、设备操作依赖或时间调度；提示主要针对 GPT-4 优化，基线也无法获得与 SAGE 相同的信息源。 |
| H05 | Kuan Li, Shuo Zhang, Huacan Wang, Fangzhou Yu, Zecheng Sheng, Yi Gu, Weipeng Ming, Lei Xue, Chen Liu, Sen Hu, Ronghao Chen, Siyue Lin, Yuqing Hou, Xiaofeng Mou, Yi Xu；arXiv v1，2026-06-01 | [arXiv:2606.01912](https://arxiv.org/abs/2606.01912) | SMH-Bench 建立在可执行、可验证的 HomeEnv 上，任务输出可以是设备服务调用、自然语言回答、澄清问题或自动化规则。7 类能力为 Atomic Control、Compositional Control、Ambiguous Intent、Automated Task Scheduling、Context-Aware Multi-turn Interaction、Personalized Memory 和 Environment-Grounded Query，共 22 个子类。数据含 1,100 个经人工审查的任务，家庭复杂度分为 550 个简单、330 个中等和 220 个复杂实例，复杂家庭包含 31 个嵌套房间和 135 个设备。 | 13 个 LLM 在 Direct Reasoning（DR）和 Environment-Interactive Agent（EIA）两种设置下评测；EIA 对多数开源/中等模型有帮助，但交互也会引入级联错误。Gemini-3.1-Pro 的 EIA 平均成功率为 85.2%，TC4 自动化调度是各模型最困难的能力，最高 EIA 成功率为 64.0%；复杂家庭会使所有代表性模型性能下降。预印本页面注明数据和代码“Coming soon”，因此复现实验条件和外部复核仍有限。 |
| H06 | Manasa Bharadwaj, Yolanda Liu, InJung Yang, Sungil Kim, Nikhil Verma, Ko Keun Kim, Kevin Ferreira, Youngjoon Kim；arXiv v3，2026-05-13 | [arXiv HTML](https://arxiv.org/html/2604.16813)；[arXiv 摘要页](https://arxiv.org/abs/2604.16813) | PersonalHomeBench 通过逐步加入成员画像、家电、历史记忆、事件和当前状态，构造 1,100 个家庭和 9,168 个任务；其中 100 个家庭有 Health、Safety、Daily Care 真实家庭视频。五类任务为 IG、CF、MC、FR、PG；PersonalHomeTools 提供家庭/成员/设备/事件检索、长期记忆、视频和音频证据、40+ 类家电的特征级控制。实验评估 11 个模型，每任务最多 15 轮，对比直接提供完整上下文的 Sole Reasoning 与需要自主查找信息的 Agentic With Tools。 | 论文显示工具接入对反应式任务可能带来性能下降，原因是模型不能稳定完成信息检索、调用选择和结果整合；个性化会显著放大 IG/CF 难度，而工具可减小部分下降。PG 中计划偏好分数与工具参数/步骤 validity 并不等价；反思机制将文本设置 validity 从约 0.030 提升到 0.428，多模态设置从约 0.405 提升到 0.496。局限是大量家庭状态为生成数据、只有 100 个家庭有真实视频、计划执行主要在工具接口层验证，且 Role-Playing Judge 具有 LLM-as-a-Judge 偏差。 | 主评测对象仍是单 Agent；Transcriber、Memory Retriever 和 Video Understanding Agent 是工具箱内部专门模块，不能直接当作平级多 Agent 协同证据。适合支撑“家庭 Agent 从设备控制扩展到个性化、主动规划、记忆和多模态接地”，不适合直接证明多 Agent 通信/协商收益。 |
| H17 | Zhonghao Zhan, Krinos Li, Yefan Zhang, Hamed Haddadi；CAIS ’26，2026-05-26，5 页；arXiv v2 | [ACM DOI](https://doi.org/10.1145/3786335.3813188)；[arXiv:2604.09618](https://arxiv.org/abs/2604.09618) | HearthNet 明确部署四类角色：Root Agent Rupert、Manager Agents Jeeves/Darcy、Librarian Agent Dewey 和非 Agent 的设备适配器。Agent 在不同边缘设备上运行，通过 Mosquitto MQTT 协调，以 Git 作为版本化共享状态，root 通过短期 lease 控制状态变化。执行协议为 Ground → Propose → Verify and Grant → Execute and Record；故障恢复依赖 heartbeat、Git 日志、能力匹配和重新授权。 | 4 个 Agent、约 10 个设备、Mac mini/Intel NUC/Pixel 4 三类硬件和 Philips Hue/JBL/Reolink/LG TV 真实设备；3 个场景中，Scene 1 完成率 4/5、延迟 8 秒，Scene 2 冲突检测/解决 5/5，Scene 3 过期命令和 lease 拒绝均 5/5，153/153 事件持久化，lease 验证 p95 <0.01 ms。局限是单 testbed、小规模、托管 API、只考虑 honest-but-crashing 故障，恶意 Agent 和重放攻击不在范围内。 | 这是当前矩阵中最直接的家庭多 Agent 系统论文，但证据属于小规模原型演示；不能据此宣称多 Agent 普遍优于单 Agent，也不能替代大规模 benchmark。 |
| H20 | Diane J. Cook, Michael Youngblood, Edwin O. Heierman III, Karthik Gopalratnam, Sira Rao, Andrey Litvin, Farhan A. Khawaja；IEEE PerCom 2003 | [IEEE Xplore](https://ieeexplore.ieee.org/document/1192783)；DOI `10.1109/PERCOM.2003.1192783` | MavHome 将家庭作为整体 Agent，通过状态感知、预测算法和设备作用形成“感知—预测—控制”闭环。 | 早期家庭整体 Agent 的历史锚点；不能直接等同于今天的 LLM Agent 或多 Agent。 |
| H24 | Qingquan Sun, Weihong Yu, Nikolai Kochurov, Qi Hao, Fei Hu；Journal of Sensor and Actuator Networks 2(3), 2013, 557–588 | [MDPI/JSAN](https://www.mdpi.com/2224-2708/2/3/557)；DOI `10.3390/jsan2030557` | 明确提出 BDI Agent、规则策略驱动的多 Agent 协作、Petri-net/JADE 实现和 MAS 指标；包含 QoS、响应/计算时间、能源和系统成本等评测维度。 | 多 Agent 家庭架构与指标基础；以仿真和 testbed 为主，不能与近期 LLM benchmark 直接横向比较。 |
| H25 | Song Zheng, Qi Zhang, Rong Zheng, Bi-Qin Huang, Yi-Lin Song, Xin-Chu Chen；Sensors 17(9), 2017, 2135 | [MDPI/Sensors](https://www.mdpi.com/1424-8220/17/9/2135)；DOI `10.3390/s17092135` | IAPhome 以多 Agent + 通信中间件处理异构设备连接、协同控制、人机交互和用户自管理；摘要明确说明在真实智慧家庭环境中测试。 | 与 TPCI 普适计算、异构设备和部署问题高度相关的多 Agent 系统论文。 |
| H28 | Lysa Gramoli, Julien Cumin, Jérémy Lacoche, Anthony Foulonneau, Bruno Arnaldi, Valérie Gouranton；ACM TOMM 21(1), Article 13, published 23 Dec 2024 | [ACM DL](https://dl.acm.org/doi/10.1145/3665331)；DOI `10.1145/3665331` | Unity 3D 虚拟家庭中使用带 scheduler 的 BDI occupant agent；以 Orange4Home 真实数据为参照，采用传感器统计、C2ST、活动识别和未来活动预测评估合成数据可信度。 | 仿真家庭、单 Agent 行为建模和评测核心文献；论文末尾明确把多住户/多 Agent 扩展列为后续方向。 |
| H22 | Qinglong Wu, Fei-Yue Wang, Yuetong Lin；IEEE International Conference on Systems, Man and Cybernetics 2001, pp. 1599–1605 | [IEEE Xplore](https://ieeexplore.ieee.org/document/973521)；DOI `10.1109/ICSMC.2001.973521` | 书目页可确认论文题名、SMC 2001 出处、页码和 DOI；题名明确提出 mobile-agent based distributed intelligent control architecture for home automation。 | 早期家庭自动化多/移动 Agent 的历史候选；已完成书目核验，正文引用前仍需阅读全文确认 Agent 角色和实验设置。 |
| H26 | Salama A. Mostafa, Saraswathy Shamini Gunasekaran, Aida Mustapha, Mazin Abed Mohammed, Wafaa Mustafa Abduallah；Springer AHFE 2019 会议章节，2020 书中出版 | [Springer](https://link.springer.com/chapter/10.1007/978-3-030-20473-0_29)；DOI `10.1007/978-3-030-20473-0_29` | Springer 摘要明确提出 AAMA-IoT，用于老年智慧家庭仿真；控制 14 类设备，报告平均活动识别准确率 96.97%；关键词含 autonomous agents、adjustable autonomy、human-agent interaction 和 smart home。 | 老年照护、可调自主性与家庭 IoT 多 Agent 分支的正式章节；不是一般家庭任务执行 benchmark。 |
| H23 | Shadi Abras, Stéphane Ploix, Sylvie Pesty, Mireille Jacomino；Springer LNEE 15, 2008, pp. 59–68 | [Springer](https://link.springer.com/chapter/10.1007/978-3-540-79142-3_6)；DOI `10.1007/978-3-540-79142-3_6` | Springer 摘要明确提出面向功率管理的家庭自动化系统：每个 Agent 嵌入资源或设备，通过协作和协调寻找满足用户舒适度/成本约束的近最优解；包含紧急保护机制、预见机制、协商协议和初步仿真。 | 家庭能源管理多 Agent 的早期正式章节；应作为能源分支，不代表一般家庭任务执行。 |
| H21 | Sajal K. Das, Diane J. Cook；ICOST 2004 会议章节 | [作者公开 PDF](https://eecs.wsu.edu/~cook/pubs/icost04.pdf)；论文集：D. Zhang, M. Mokhtari (eds.), *Toward a Human-Friendly Assistive Environment*, Assistive Technology Research Series 14, IOS Press, 2004, pp. 3–14；ISBN `9781586034573` | 论文摘要明确提出用 agent-based smart home 做居家健康监测和辅助，目标包括安全采集、模式学习、长期趋势、异常检测/响应和提醒自动化。MavHome 架构采用 Physical、Communication、Information、Decision 四层；论文说明一个层级中的物理层可以由另一个 Agent 代表，并支持接口 Agent。 | ED 在合成 MavHome 场景中识别 13 个显著事件；5 个场景平均正确率为 IPAM 41%、IPAM+ED 74%、BPNN 64%、BPNN+ED 86%，ED 平均处理时间 10 秒。ALZ 在无噪声合成数据上趋近 100%，有噪声数据最终约 86%；真实 MavHome 一个月、750 个数据点约 47%；20 名学生、50 台设备的高噪声数据上 ALZ 为 30%，ALZ+ED 为 44%。 | 早期论文主要证明预测、监测和辅助闭环的可行性；不是现代 LLM Agent，也不是以平级多 Agent 通信/协商为核心的实验论文。数据规模小、参与者有限，健康趋势和危机响应仍处于测试/部署前阶段；公开 PDF 未显示 DOI。 |
| H27 | Ferdinando Fioretto, Agostino Dovier, Enrico Pontelli；*Intelligenza Artificiale* 12(2), 2019, 67–87 | [DOI/出版商页](https://doi.org/10.3233/IA-180037)；[作者公开版 PDF](https://users.dimi.uniud.it/~agostino.dovier/PAPERS/FDP2018_DRAFT.pdf) | 论文明确称其“reviews two methods”：用 MVA 分解 DCOP，让每个 Agent 处理本地复杂子问题；用 GPU 并行加速推理型 DCOP；并将方法用于 EDDR 和 Smart Home Device Scheduling（SHDS）。SHDS 把每个家庭映射为 Agent，以设备时序、实时电价、用户舒适度、能源峰值和邻居通信构造协作优化问题。 | SH-MGM 与未协调 greedy 对比：每个 Agent 调度 9 个智能执行器、使用 5 个传感器，H=12，采用 PG&E 七档电价；物理实验使用 7 台 Raspberry Pi 2，通过 JADE 异步消息通信，每台家庭 Agent 运行约束规划求解器。合成实验使用 Des Moines、Boston、San Francisco 三类住房密度；未协调方案峰值 2852 kWh、日成本 $3.84，协调方案在峰值与成本之间呈现可解释权衡。 | 它是分布式优化/能源调度方法论文，不是面向一般家庭任务执行的综述；家庭证据集中在能源削峰和设备调度，不能直接外推到 LLM Agent、长期记忆或多模态交互。作者公开版为 2019-03-04 草稿，正式期刊元数据以 DOI 页面为准。 |

## v0.6 的阶段性统计与解释

- 当前表中共有 **30 条记录**：28 条家庭/相关领域工作，2 条通用方法背景。
- 按当前标签：**核心候选 12 条、相关候选 6 条、背景候选 12 条、待核验 0 条**。核心候选中仍包含预印本和演示型论文，不能把“核心候选”理解为“都已正式发表”。
- 直接智慧家庭记录为 **13 条**；其中近期 LLM/Agent benchmark 或编排工作主要是 H01–H06、H17，早期架构、健康监测与仿真工作主要是 H20、H21、H24、H25、H28。
- 已核验书目或摘要的直接家庭多 Agent 证据主要集中在 **H17、H22、H24、H25、H26、H27**；H21 的分层 MavHome 架构可作为早期层级 Agent 证据，但论文主问题是健康监测，不应写成平级多 Agent 协同实验。这进一步支持“多 Agent 是重点分支，但不宜作为全文唯一主线”的判断。
- 已核验的单 Agent/家庭整体 Agent 证据覆盖 H01–H06、H20、H28。它们不是凑数，而是分别支撑任务评测、动态仿真、个性化、早期家庭闭环和虚拟居民建模。

### 统计口径

以上统计按矩阵中的“场景关联”和“Agent 层级”字段计数；同一篇论文可能同时属于多个方法分支。正式综述还需要基于全文进行去重、纳入/排除筛选，并对每篇论文补充局限性证据句。

## 当前初步结论

### 可以作为综述主体的文献群

- H01—H06：家庭 Agent 任务执行、benchmark 和仿真；
- H17：近期家庭多 Agent 编排，已完成正式出处和全文阅读；证据主要来自小规模真实原型演示。
- H20—H21：早期家庭整体 Agent 和情境感知；
- H24—H25：多 Agent 家庭自动化、异构设备和交互；
- H28：单 Agent、3D 仿真和评测。

### 可以作为专题分支的文献群

- H23、H26、H27：能源管理、IoT 和老年照护；
- H08、H10—H13：多 Agent 规划、状态一致性和恢复；
- H19：分层推理与实时控制。

### 不宜直接作为智慧家庭核心证据的文献

- H07、H09、H14—H16、H18、B01、B02。

这些文献可以用于解释规划、调度、低延迟或多 Agent 协同方法，但必须明确标注为“可迁移方法背景”，不能替代家庭场景论文。

## 下一步筛选动作

1. 为 H02、H20、H22–H26、H28 补充全文层面的“关键证据句”和“局限性证据句”。
2. 对全部记录做去重：预印本/正式版本、会议论文/期刊扩展版、同一系统的不同论文分别标注。
3. 根据全文筛选结果统计单 Agent、多 Agent、分层 Agent、仿真、真实家庭、能源/照护和 LLM Agent 的数量。
4. 用引用追踪补充 2016–2024 年的家庭服务组合、上下文感知、虚拟家庭和多 Agent 协同论文。
5. 以“任务执行闭环”为正文主线，以“单 Agent→多 Agent”为演化轴；多 Agent 协同作为重点分支而非唯一纳入条件。
6. 基于最终候选表设计章节—文献映射，再开始修改原 Word。
