# 评测、成本与边界：主执行者检索记录

截止2026-10-18。本文件支撑总览的评测及范围部分，不是实验结果或创新性批准。

## 检索

首轮：`LLM multi agent collaboration survey 2026 architecture aggregation communication learning evaluation`；`multi agent LLM collaboration evaluation fair compute majority voting single agent baselines 2025 2026`；`multi agent systems failure MAST Why Do Multi-Agent LLM Systems Fail MAS-ProVe 2026`；`2026 benchmark multi agent collaboration distributed information dynamic asynchronous evaluation COCOBench DESBench`。

第二轮：精确题名核验及原始来源打开；补查 DESBench / TickingCollabBench / Gaia2 / CoCoBench；补查 NegotiationArena、SOTOPIA、AgentLance，防止将共同目标团队泛化到多主体利益博弈。

## 原始证据条目

| 论文/来源 | 核验状态与读取层级 | 对总览可用的结论 | 不可外推的结论 |
|---|---|---|---|
| [Multi-Agent Collaboration Mechanisms: A Survey of LLMs](https://arxiv.org/abs/2501.06322), Tran et al., 2025 | arXiv原始摘要、作者题名匹配 | 用actors/types/structures/strategies/protocols区分协作维度；作索引 | 2025综述不是2026所有近邻已覆盖的证明 |
| [Beyond Self-Talk: A Communication-Centric Survey of LLM-Based Multi-Agent Systems](https://journal.hep.com.cn/fcs/EN/10.1007/s11704-026-50857-y), Yan et al., FCS accepted online 2026-05-29 | 官方页题名、作者、接受/上线日期与摘要 | 通信包括系统架构/目标/协议及内部策略/对象/内容，不等于拓扑 | 页面未提供全文，不编造其具体文献统计 |
| [Beyond More Agents: A Survey of Collaboration Mechanisms in Multi-Agent LLM Systems](https://research.aston.ac.uk/en/publications/beyond-more-agents-a-survey-of-collaboration-mechanisms-in-multi-/), Li et al., SSRN working paper, 2026-08-10 | 作者机构原始记录与摘要；类型明确Preprint | 协调、通信、协商、记忆、学习之间相互作用，收益和开销共同重要 | 记录的E-pub字段不能当期刊已录用 |
| [Why Do Multi-Agent LLM Systems Fail?](https://proceedings.neurips.cc/paper_files/paper/2025/hash/b1041e52d3be19f0a9bc491657488e4a-Abstract-Datasets_and_Benchmarks_Track.html), Cemri et al., NeurIPS2025 D&B | 官方摘要；另打开arXiv全文 | 14类失败聚为设计、成员错位、核验；轨迹数据支持诊断 | 失败标签不是自动得到的因果根因，也不是所有系统真实生产故障率 |
| [MAS-ProVe: Understanding the Process Verification of Multi-Agent Systems](https://proceedings.mlr.press/v306/venkataramani26a.html), Venkataramani et al., ICML2026 | 官方原始摘要 | 比较judge/RM/PRM、成员/迭代粒度、上下文策略；核验不稳定改善 | 不能推导所有过程核验无效或现有judge可靠 |
| [MultiAgentBench: Evaluating the Collaboration and Competition of LLM agents](https://aclanthology.org/2025.acl-long.421/), Zhu et al., ACL2025 | 官方原始摘要与元数据 | 多场景、里程碑指标、星/链/树/图及策略比较 | 图在research场景有优势不等于任意任务全连接最好 |
| [Systematic Failures in Collective Reasoning under Distributed Information in Multi-Agent LLMs](https://arxiv.org/html/2505.11556v4), Li et al., 2026v4 | 全文打开、摘要与方法/消融结构 | HiddenBench控制信息分散，已含结构化交换/决策协议 | 全信息单体与分布信息团队不是同信息公平对照；不能说论文只是诊断没有解法 |
| [Towards a Science of Scaling Agent Systems](https://arxiv.org/html/2512.08296v3), 2026v3 | 全文，主要设计与统计/局限段；作者信息在原页 | v3为260配置、6任务；收益依赖任务/架构/预算；87%是留出配置架构选择 | 不将87%当绝对性能预测；R²=.373/.413，不能把45%阈值写成普适定律；未复现其因果解释 |
| [Do More Agents Help? Evaluating Accuracy and Cost in LLM Multi-Agent Workflows](https://arxiv.org/abs/2606.05670v2), Fu et al., 2026-10-09预印本 | 原始摘要与版本历史 | 统一底模和接口比较，架构收益随任务不同，同时记录token开销 | 相同步数上限不等于相同token/dollar；不称单一横评已确定全领域最优 |
| [Multi-Agent Teams Hold Experts Back](https://arxiv.org/html/2602.01011v4), Pappu et al., ICML2026 | 官方页另核；全文表2、附录E/F | 心理任务专家稀释；ML部分比较ALOC逐题oracle，上界未完全回收 | ML侧不能说团队普遍输给固定最佳单体：表2中GPQA 83>78，HLE36>29，MATH75>73.5。6.3–41.1%相对ALOC，不是固定最佳单体下降幅度 |

## 动态环境：已有评测做到哪里

| 来源 | 状态/访问 | 实际关注 |
|---|---|---|
| [DESBench: When Does Hierarchy Help?](https://arxiv.org/abs/2605.13172), Wang et al. | 2026-05-13v1预印本；原始摘要 | 离散事件工业调度，部分观测、耦合约束；比较不同权力/信息/冲突处理，并分析效率与鲁棒性 |
| [Multi-agent Framework for Time-Sensitive Complementary Collaboration in Minecraft](https://arxiv.org/abs/2606.15684), Yi et al. | 2026-06-14v1预印本；原始摘要 | TickingCollabBench异质性、必须协作、动态事件和实时限制；可行性筛选使用近似约束 |
| [Gaia2: Benchmarking LLM Agents on Dynamic and Asynchronous Environments](https://arxiv.org/abs/2602.11964), Froger et al. | 原始摘要；检出ICLR2026正式PDF，未以未读取内容断言具体设置 | 环境独立演化、时间约束、噪声和协作；是一般Agent基准，不是全部任务都专评多Agent |
| [CoCoBench: A Cooperative Coordination Benchmark for Embodied Multi-Agent Task Planning](https://arxiv.org/abs/2608.28266) | 2026预印本；原始摘要 | 可执行家庭任务中的具身协作构念；与法律领域同名CoCoBench区分 |

## 相邻但不同的多Agent目标

| 来源 | 原始核验 | 与共同任务的不同 |
|---|---|---|
| [SOTOPIA: Interactive Evaluation for Social Intelligence in Language Agents](https://proceedings.iclr.cc/paper_files/paper/2024/hash/b3075b88e583a0e98d8b24338a613060-Abstract-Conference.html), Zhou et al., ICLR2024 | 官方摘要 | 协作/竞争/交换的社会目标，评价多维社会表现；不是客观答案聚合 |
| [SOTOPIA-π](https://aclanthology.org/2024.acl-long.698/), Wang et al., ACL2024 | 官方页摘要 | 通过交互学习社会能力；不等同工程任务的团队协作策略 |
| [How Well Can LLMs Negotiate? NegotiationArena Platform and Analysis](https://arxiv.org/abs/2402.05863), Bianchi et al., 2024v1 | 原始摘要 | 个体收益、资源分配和交易，不能用全员共识等同正确性 |
| [Markets, Not Planners: Decentralized Orchestration of LLM Agents with Private Information](https://arxiv.org/abs/2608.23867), Liu et al., 2026-08-24 working paper | 原始摘要 | AgentLance以私人成本、竞标、公共信誉、支付和分包组织工作；有策略主体假设，虚拟市场不是同目标封闭团队的必需模块 |

## 方法学综合（本报告判断）

1. 至少区分最强可部署单体、同预算独立采样、可部署路由、真实交互团队、逐题oracle；名称相似不等于比较条件相同。
2. 不只看accuracy：交付完整性/约束/安全，token与dollar，关键路径wall-clock，通信及返工，恢复和误干预均可能重要。不同任务不可直接混一个均值定优劣。
3. 实际API耗时、工具/环境时间和人为控制时间应分别说明。受控条件支持机制分析，真实时间支持部署相关性，任何单层都不自动严谨。
4. 计算预算匹配不唯一：token、dollar、模型调用、并发、训练费用有不同含义；须说明取舍。需要报告所有角色及核验者的成本，不能只算worker。
5. 底模、工具、资料、采样次数、训练数据和人工规则都可带来收益，方法消融应排除这些替代解释；LLM judge和轨迹标签不是无误真值。
6. 本轮未运行复现实验；若论文仅摘要核验，只用对应层级支持的方法概述。没有全面数据库去重和饱和证明，不声称穷尽或所有最新方法都已覆盖。
