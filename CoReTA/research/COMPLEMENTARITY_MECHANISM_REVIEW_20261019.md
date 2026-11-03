# 优势互补怎样落实为架构机制：文献核查与 CoReTA 对照

2026-10-19。定向机制调查，非系统综述或查新认证。对应 [检索简报](COMPLEMENTARITY_RESEARCH_BRIEF_20261019.md) 的三个研究问题。已检查相关方法、案例、限制及部分作者代码；没有复现他人实验。运行协议、原 E1 与模型配置保持原状。

## 1. 先给结论

文献没有一个通用的“优势互补组件”，但提供了可实现的链条：**产生不同材料 → 暴露具体问题 → 让指定操作处理问题 → 核验新增依据 → 接入共同方案 → 根据实际结果继续或停止**。

我们 v0.3 已有独立初稿、固定初审、汇总、可选帮助与应用记录；问题并非完全没有这些模块，而是材料差异、交接依赖和语义检查仍主要依赖提示词自觉完成。再增加 reviewer 或要求“多交流”，不足以补足这条链。

“三个独立初稿均错、合作后对”是合理目标。Du 等明确报告这种案例；但这一现象本身还不能证明多份局部贡献共同构成新解，也可能来自交流后某一成员重新独立求解。我们的目标还需要贡献内容与下游变化的证据。[Du 等，§2、§3、Fig.4/11](https://arxiv.org/html/2305.14325v1)

## 2. 检索与核验范围

并行核查三类来源：分工与交付、协调与融合、失败与反证。旧来源台账只作入口；以原论文、作者项目和官方代码为依据。覆盖 17 项工作，主要年份 2023–2026。按机制选文，不以正面结果或数量填充。

三个详细笔记保留来源、实现入口和阅读边界：

- [分工、局部交付与反馈](literature_mechanisms_20261019.md)：AgentVerse、MetaGPT、ChatDev、Puppeteer。
- [黑板、异构推理与信息过滤](literature_coordination_20261019.md)：Blackboard、ReConcile、DMAD、Free-MAD、MAD-M²。
- [失败机制与证据边界](literature_failures_20261019.md)：Du Debate、Debate or Vote、Voting or Consensus、MAST、When Helping Hurts。
- 本文补充 MoA、Liang MAD、TMAS 的方法与实现边界。下表为核验台账；“已读代码”只表示所列相关文件，非全仓库审计；未固定提交的当前代码不能冒充论文历史版本。

| 工作 | 身份/方法核验与阅读深度 | 代码核验边界 |
|---|---|---|
| Du et al., Improving Factuality and Reasoning…，2023/ICML 2024 | VERIFIED：原文方法、实验、Fig.4/11；[原文](https://arxiv.org/html/2305.14325v1) | 项目身份已核；本轮未读实现 |
| Chen et al., AgentVerse，ICLR 2024 | VERIFIED：方法、任务条件、附录；[论文](https://arxiv.org/pdf/2308.10848) | 已读 solver-first 调度、环境、两种 HumanEval 配置 |
| Hong et al., MetaGPT，2023 | VERIFIED：v6 方法及执行反馈；[全文](https://arxiv.org/html/2308.00352v6) | 已读 ActionNode、设计/任务交接；main 后续版本有 RoleZero |
| Qian et al., ChatDev，ACL 2024 | VERIFIED：[正式记录](https://aclanthology.org/2024.acl-long.810/)、方法/消融 | 已读 chatdev1.0 的链、阶段配置与执行；不是当前 DevAll |
| Dang et al., Multi-Agent Collaboration via Evolving Orchestration（Puppeteer），2025 | VERIFIED：[方法与条件](https://arxiv.org/html/2505.19591v1) | 已读 README、personas、入口；未审计 RL 训练全链 |
| Salemi et al., LLM-based Multi-Agent Blackboard…，2025/v2 2026 | VERIFIED：[方法、附录 C–E](https://arxiv.org/html/2510.01285v2) | 未识别作者代码，不能称代码已核 |
| Chen, Saha, Bansal, ReConcile，2023 | VERIFIED：[方法与 C.4](https://arxiv.org/html/2309.13007) | 已读 run/utils/generation 的分歧触发与输出 |
| DMAD, Breaking Mental Set…，作者仓库标 ICLR 2025 | MINOR ISSUE：身份及官方实现核实；[论文入口](https://openreview.net/forum?id=t6QHYUOQL7) 正文访问受阻 | 已读官方 main_DMAD/reasoning/prompt；本报告仅依其代码描述机制，不归纳未读实验细节 |
| Cui et al., Free-MAD，2025 | VERIFIED：[方法](https://arxiv.org/html/2509.11035) | 未核作者实现，不把社区代码当官方 |
| Tian et al., MAD-M²，2026 | VERIFIED：[方法](https://arxiv.org/html/2603.20215) | 已读记忆裁剪；客观分数方向与论文关系待解，未据此判 bug |
| Choi, Zhu, Li, Debate or Vote，2025 | VERIFIED：[方法、实验与理论假设](https://arxiv.org/html/2508.17536v1) | 作者链接核实，未读代码 |
| Kaesberg et al., Voting or Consensus，Findings ACL 2025 | VERIFIED：[正式论文](https://aclanthology.org/2025.findings-acl.606.pdf) | 作者链接核实，未读代码 |
| Cemri et al., Why Do Multi-Agent LLM Systems Fail?，2025 | VERIFIED：[v3 分类、干预附录](https://arxiv.org/html/2503.13657v3) | 未读实现 |
| Parmar et al., When Helping Hurts…，2026 预印本 | VERIFIED：[方法及限制](https://arxiv.org/html/2606.02866)；部分图表数值不一致，未引用其精确效应值 | 未核官方代码 |
| Wang et al., Mixture-of-Agents…，2024 | VERIFIED：[§2、§3.3](https://arxiv.org/html/2406.04692v1) | 已读官方 [moa.py](https://raw.githubusercontent.com/togethercomputer/MoA/main/moa.py)；当前两层演示不是论文完整配置 |
| Liang et al., Encouraging Divergent Thinking…，EMNLP 2024 | VERIFIED：[方法/案例](https://arxiv.org/html/2305.19118v4) | 已读官方 [interactive.py](https://raw.githubusercontent.com/Skytliang/Multi-Agents-Debate/main/interactive.py) 的反驳、裁决与停止 |
| Wu et al., TMAS，2026 预印本 | VERIFIED：[算法、附录 B/C/D](https://arxiv.org/html/2605.10344v1) | 只核官方 [README](https://github.com/george-QF/TMAS-code)；具体 main.py 获取失败，未称源码实现已核 |

## 3. 机制分类及比较

### 3.1 材料差异从哪里来？

**同模型独立采样**能产生不同推理，但差异可能只是措辞。Du Debate 将同伴上轮推理提供给各成员重解；与此相比，**DMAD 的官方代码**给不同成员分配不同表示操作，例如直接作答、子问题分解、场景图，然后按各自方法修订。它改变实际工作方式，而不只写“你是数学专家”。视觉场景图不宜直接移植给我们的数学/代码任务。[Du](https://arxiv.org/html/2305.14325v1)、[DMAD 官方 reasoning.py](https://raw.githubusercontent.com/MraDonkey/DMAD/main/reasoning.py)

**任务交付不同**是另一条路径。MetaGPT 的设计、接口和依赖进入实现；ChatDev 将评论、修改、测试反馈分阶段交接。它们的互补建立在产物有下游用途上。Puppeteer 进一步区分操作并训练调度，但其 RL 和工具条件不能当作纯提示法的证据。详细代码入口见分工笔记。

**掌握的信息不同**又是另一种机制。Blackboard 将文件分给不同成员，由帮助响应补齐数据位置、结构等信息；我们的成员看同一道题，没有这种天然信息分区。ReConcile 用异构模型及纠正解释示范形成差异；当前单一 DeepSeek 后端也不具备这一条件。借鉴它们的消息格式不等于获得其互补来源。

**对我们的判断：**先定义可观察的推理操作与交付物，再验证同模型是否真的产生有用差异。不宣称角色提示能创造模型原本没有的专长，也不故意限制知识来制造“个人都错”。

### 3.2 缺口如何变成实际工作？

AgentVerse 的 solver-first 代码会让 reviewers 发言，有非空异议再调用 solver 修订；ChatDev 则让评论阶段的产物直接进入修改阶段。它们都给意见安排了消费者与动作。Liang MAD 的反方先读正方解，随后裁决者判断是否继续；这能触发反驳，但固定反对也可能引入错误。[AgentVerse 调度代码](https://raw.githubusercontent.com/OpenBMB/AgentVerse/main/agentverse/environments/tasksolving_env/rules/decision_maker/vertical_solver_first.py)、[ChatDev 原版链](https://raw.githubusercontent.com/OpenBMB/ChatDev/chatdev1.0/CompanyConfig/Default/ChatChainConfig.json)、[Liang MAD](https://arxiv.org/html/2305.19118v4)

相反，ReConcile 官方代码按答案分组，无分歧时可能跳过讨论；一致错误因此没有自动暴露的保证。CoReTA 也不能用“答案一致/没有报告 open_issue”替代检查完成。**但我们已有固定初审**，不能据此推导再强制一次聊天就有效。需要改的是问题处置的内容与后续约束。

### 3.3 局部内容如何接入、如何避免错误扩散？

MoA 的聚合者可综合生成新答案，不只是选择一份候选；论文还区分了 proposer 与 aggregator 的能力。因此完整单解较弱的成员仍可能提供有用内容。但其主要评价是开放回答质量，且当前演示只靠综合提示，没有可执行的事实核验，不能据此认定局部推理已被可靠验证。[MoA 方法与分析](https://arxiv.org/html/2406.04692v1)、[官方演示](https://raw.githubusercontent.com/togethercomputer/MoA/main/moa.py)

TMAS 把低层经验与高层已尝试策略分别供后续轨迹使用，比仅保留整份答案更接近局部复用。其“验证”仍主要依赖模型；另有训练扩展。附录案例先出现一条完整正确轨迹，再传播发现，不能直接当作全员均错时的局部联合证明。CoReTA 不应把“记录局部经验并复用”本身宣称为新颖贡献。[TMAS 算法及附录](https://arxiv.org/html/2605.10344v1)

MAD-M² 会真正裁剪后续可见上下文，区别于只写一句“不采用”却继续传播；但筛选本身会错。执行反馈则可核对部分命题，MetaGPT、ChatDev 与 AgentVerse 的部分代码设置使用它。自生成测试依然有覆盖边界；不能把 reviewer 认可或测试通过等同全面正确。

对 E1 的 799，应当落实具体手算复核并阻止错误示例成为后续依据，而非仅把 application 标成 accepted。当前没有在线工具，不能把工具论文的收益移植为我们已有能力。

## 4. 反证与研究目标边界

讨论可以纠错，也可以把正确思路改错。Debate or Vote 的若干设置中投票已能匹敌/超过讨论；其理论结论依赖特定更新模型，不是对新增推理的普遍不可能性证明。Voting or Consensus 显示决策与信息共享方式会改变效果，单靠要求“批判”不稳定。MAST 将验证、错误终止和成员失配列为不同失效来源。数据清洗的 When Helping Hurts 进一步提供错误批评传播案例，但其领域干预不能无条件推广。

因此我们需要同时看纠错与损伤。不能从零帮助请求推断所有融合均无作用，也不能从日志有请求、引用和 accepted 推断互补已发生。

## 5. 直接回答三个问题

**RQ1：产生和调用局部信息。** 有依据的实现包括不同推理操作、不同阶段交付物、不同数据/工具权限、异构模型，以及保留可复用经验。当前最适配的是前两者；数据分区、异构和训练需另立条件。

**RQ2：检查与连接。** 借鉴意见到修订的控制流、产物依赖与具体反馈；我们需补上局部结果的前提/用途、可核对检查内容、冲突保留及实际应用差异。结构验证只能保证消息可连接，语义正确仍是待验证能力。

**RQ3：证明什么。** “全初稿错→团队对”说明超出初稿整解选择范围，但还需排除追加独立推理；局部引用仅是线索，需与实际新增步骤、独立核查及贡献移除/替换后的表现共同判断。现有文献提供动机与方法先例，尚不足以替我们证明 CoReTA 的机制或新颖性。

## 6. 自我反驳检查

- 已纳入负结果；没有把一致、置信度、自评 resolved 当真值。
- 已区分普通 API、工具、异构、RL 条件；没有混用收益。
- 没把所有初稿错后的恢复自动标成局部组合；没把已有正确整解传播算成该目标的证明。
- 已标出 DMAD 正文访问、TMAS 源码获取及当前分支/历史版本边界。
- 不据 E1 三道有契约疑点的共同失败题调整目标或事后挑题。

下一份交付是 [来源约束下的具体修订稿](CORETA_REVISION_FROM_LITERATURE_20261019.md)。它是待审查设计，不是已验证提升。
