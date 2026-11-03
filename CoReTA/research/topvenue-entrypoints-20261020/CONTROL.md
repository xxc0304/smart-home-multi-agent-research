# 顶会控制与组织机制切口：独立检索笔记

检索日期：2026-10-20。纳入窗口按正式会议届次/发表时间为 2025-10-20 至 2026-10-20；不以 arXiv 首发时间筛掉后续正式录用的论文。RQ1：已有 MAS 组件相似时，论文实际改变哪个控制对象？RQ2：哪项消融能把机制增益与模型/算力增益分开？RQ3：据此可学到什么可发表贡献形态？以下“发表价值”均为方法与证据的研究判断，不推测真实审稿理由。

## 检索与核验

- 第一轮宽搜：NeurIPS 2025 / ICLR 2026 / ICML 2026 的 LLM、multi-agent、communication、coordination、routing、topology。第二轮按 AgentNet、SelfOrg、MASS、SYMPHONY、TeamTR 查原文、消融及官方记录。
- 正式身份只用 NeurIPS proceedings、ICLR 官方 poster、PMLR。第三方 Paper Notes 只作发现线索，未作方法/结论依据。
- ICLR 2025 的 AgentPrune、MacNet 等不在窗口内；ICLR 2026 “Submitted/Under review”不算接受；2026 arXiv 拓扑预印本未因标题相关而纳入。

## 四个可直接讲清楚的正式案例

| 论文与录用核验 | 读到哪里 | 真正变化的控制层 |
|---|---|---|
| [AgentNet — NeurIPS 2025 Main Conference](https://proceedings.neurips.cc/paper_files/paper/2025/hash/9a379c1b05793d1c42dc832269834515-Abstract-Conference.html) | [正式 PDF](https://papers.nips.cc/paper_files/paper/2025/file/9a379c1b05793d1c42dc832269834515-Paper-Conference.pdf)：§3、§4、路由/演化消融 | 各节点的 forward/split/execute 决策及经验驱动的邻接关系 |
| [SYMPHONY — NeurIPS 2025](https://papers.nips.cc/paper_files/paper/2025/file/537d89d08145ce0432bdb7e0bc9759e1-Paper-Conference.pdf) | 正式 PDF §3–4、Table 5、Appendix I/J | MCTS 每次扩展/评价由哪个异构模型执行 |
| [MASS — ICLR 2026 Poster](https://iclr.cc/virtual/2026/poster/10010348) | [作者全文 v2](https://arxiv.org/html/2502.02533v2)：§2–4、阶段消融与限制；[ICLR 下载目录](https://iclr.cc/Downloads/2026)交叉核验 | 离线联合设计中，prompt 与 topology 的条件优化顺序 |
| [SelfOrg — ICLR 2026 Poster](https://iclr.cc/virtual/2026/poster/10007145) | [作者全文 v2](https://arxiv.org/html/2510.00685v2)：§2–3、Appendix F；官方目录交叉核验 | 每轮实际 response 决定信息流方向与接收对象 |

### AgentNet：把路由操作下放到节点

集中控制和固定角色是其出发瓶颈。每个 agent 同时有 router/executor 和各自 RAG 经验；本地选 forward、split 或 execute，合作成功率更新边权并剪边。ReAct、RAG、指数移动平均均可复用；组合的研究对象是分布式任务流与专长演化。BBH 测试 full 为 86%，随机操作 71%、随机下一节点 82%、global router 83%；去 evolution 后 BBH 为 76%。这说明“做什么操作”比只选下一人更敏感。但测试仅 100 道 BBH，扩展实验约 3–9 agents；隐私和大规模容错的动机不能当成已验证保证。异构也非总好：3 agents 同构 .86，高于双异构 .81；5 agents 时趋势反转。源见表中正式 PDF §3、§4.2–4.4。

### SYMPHONY：把异构性嵌入搜索的每个动作

瓶颈是同一 LLM 反复采样使 MCTS 分支重复。方法保留 MCTS/UCB/反思等组件，将异构模型池用于扩展、评价与共享失败反思，并用置信熵调整节点值。其可区分增量是“模型级多样性如何进入搜索及预算分配”。固定宽度 4 时，MBPP 四分支全异比例由单模型低于 20% 增至三模型高于 80%；Table 5 的小模型系统 HotpotQA 为 .59，去调度 .51、去共享记忆 .45、去 EMCS .51。Appendix I 对比温度/对抗提示。局限是依赖结构化环境和可靠反馈，参数手调；多样性与准确率相关不等于普遍因果保证。源见正式 PDF §3、§4.5–4.7、Appendix I/J。

### MASS：把“搜索什么、先优化谁”作为贡献

瓶颈是 prompt 与拓扑相互依赖，直接组合搜索稀疏且昂贵。三阶段是局部模块 prompt 优化→按模块增益裁剪拓扑空间→最优 workflow 全局 prompt 优化；沿用 MIPROv2、debate、reflect、aggregate。可发表增量在优化分解和搜索空间设计，而非声称这些组件新颖。作者阶段实验报告局部模块优化比单 agent APO 平均约增 6 个百分点，拓扑阶段再增约 3，最后全局 prompt 再增约 2；另做“不裁剪/不先优化 prompt”的对照。其拓扑顺序预设，仍是有标签验证集上的离线搜索，不能称任意在线组织学习。源见作者全文 §2–4，Fig.5–6 及 Algorithm 1。

### SelfOrg：把控制条件细化到随机生成后的实际状态

瓶颈是同一 query 的不同生成也需要不同协作图。方法先独立回答；用 response embedding 与群体均值的 cosine 近似贡献，再据相似性与贡献定向构建 DAG，每轮重构。Shapley、句向量、DAG 都是已有工具；增量是 response-conditioned 控制粒度与无额外图训练的轻量估计。Qwen-1.5B 七任务平均 single 41.24、SelfOrg 45.05，若干 MAS 低于 single；然而重构图本身的消融仅 GSM8K 73.8 vs 73.2、MMLU 52.8 vs 51.4。不能把全部收益说成动态图贡献。正确性理论要求独立响应、错误分散和正确 embedding 聚类；共享系统性错误可能使一致性代理失效。源见全文 §2、Table 1、Appendix F.2。

## 补充：更接近“训练目标变化”的已接受案例

[TeamTR: Trust-Region Fine-Tuning for Multi-Agent LLM Coordination — ICML 2026，PMLR 306:139507–139546](https://proceedings.mlr.press/v306/xie26o.html)。正式录用已由 PMLR 核验；正式 PDF 的 raw GitHub 地址在 web 工具中返回不支持的 application/octet-stream，本地下载受网络权限限制，因此方法细读来自[作者全文 v2](https://arxiv.org/html/2605.15207v2)，不能声称逐页核验正式 PDF。

瓶颈是顺序更新某个 agent 后，共享 context 分布变化，使下一 agent 在旧 rollout 上优化失配。变化不是再找图，而是每次在部分已更新的 team 下重新采样，并约束每 agent token 分解的 behavior-to-updated KL。继承 trust region/GRPO/顺序更新，新增对团队 occupancy shift 的控制。全文 AIME24 消融 full 88.1±1.2，no resampling 71.1±2.8、no trust region 68.3±3.5，并记录 stale mismatch 与协调指标。分析仅覆盖每时刻一个 active agent、固定 router；每次重采样有额外成本，实用 certificate proxy 不是样本级严格认证。对引用数值，请明确来自该作者 v2；正式 PMLR 摘要确认中间团队采样和 token KL 的核心机制。

## 交叉结论：为何组件相似仍有贡献空间

AgentNet 改的是控制权所在位置与本地操作，SYMPHONY 改的是搜索时的模型调度，MASS 改的是离线设计变量的优化分解，SelfOrg 改的是在线图构造所观察的状态，TeamTR 改的是训练采样分布与更新约束。这些轴不同，不能因都用了 graph/router/memory 而视为同一机制。

可迁移的判断法是：先指认旧机制在哪种条件下失败，再指定一个可操作的控制变量，最后用只移除该变量的对照验证。总体 SOTA 表、漂亮系统框图和“动态/协同”标签单独不足。SelfOrg 的小幅图重构消融及 AgentNet 的小团队异构反例也表明：应按直接证据给每个新模块分配功劳。本文未读取审稿意见，不将上述解释写成“因这些原因而被顶会接受”。
