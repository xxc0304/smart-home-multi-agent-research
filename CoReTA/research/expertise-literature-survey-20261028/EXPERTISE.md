# 专长、影响力与信息利用：独立检索视角

日期：2026-10-28。冻结问题见 BRIEF.md；10 篇核心证据见 EXPERTISE.json（原9篇加盲点补核EMRC）；DEALS另作摘要级边界记录。仅核读和综合，没有新实验。本视角覆盖稳定能力、给定信息优势、交互影响力和独立候选利用，避免把所有“专家”混成同一对象。

## 1. 从“专家”分出可比较的研究对象

同一个 agent 可以因为底层模型更强、拥有独有材料、被提示扮演专家或恰好该题答对而被称为 expert。这四类条件需要分别理解：[ReConcile](https://aclanthology.org/2024.acl-long.381/)使用异构模型并包含领域模型；[HiddenBench](https://proceedings.mlr.press/v306/li26ej.html)主要操纵信息分持；[Who Becomes an Influencer?](https://arxiv.org/html/2605.25929v2)把真值答案的 belief 作为事后 competence，同时研究 persona、风格与 confidence 如何影响发言权。后者的 competence 对系统不可见，不能据“自称专家”或单题正确认证稳定技能。三种设计都对项目有价值，但结论迁移需说明对象。

这些论文还区分了两条合法路线。[ReConcile](https://aclanthology.org/2024.acl-long.381/)希望通过解释交换改善每个成员；[LLM-Blender](https://aclanthology.org/2023.acl-long.792/)则先保留完整独立候选，再排序和融合。后者并不因没有多轮互动而与专长利用无关，它说明“利用多个模型的优势”可以通过不同操作实现。对我们来说，应先确定希望理解的是谁有优势、优势如何获得影响力，还是如何得到更好的最终输出，不能只用 agent 数量或对话轮数区分贡献。

## 2. 信息探索的失败已经有有效干预

[HiddenBench](https://arxiv.org/html/2505.11556v4)并不只报告失败：其关键18题子集上，机械 Reveal-All 接近恢复完整信息表现，Exchange→Decide 的轻量协议也明显改善；[Consilience](https://arxiv.org/html/2608.20564v1)进一步依据讨论状态选择挑战、澄清、取证或让较少发言者补充；[IMP](https://arxiv.org/html/2610.24718v1)则改变接收者的 inbox，去除重复共享材料而保持私有证据可达。它们共同表明“资料合在团队里但没有被充分利用”已经是可操作、部分已改善的问题。不能因为它们未逐一验证已知能力专家条件，就抹掉这些成果，也不能把三种不同操作合并成一个对所有任务都适用的现成解法。

三者对控制对象的选择尤其不同。HiddenBench 的结构化流程要求成员自行选事实并说明反对领先答案的理由；Consilience 以六维状态和代理讨论损失来选择下一动作，并实际展开候选动作分支；IMP 不判断可信度或相关性，只在已知原句之间作来源匹配、逐接收者去重和转发。Consilience 的校准保证针对一步代理 regret，依固定打分过程和交换性；它与 IMP 的有界重复输入规则都不是终局真值保证。论文的这种限定是清楚的贡献范围，并非否定它们有效性的理由。

## 3. 披露、保留与利用可以反向变化

[Multi-agent discussion gains less when dissent is withheld](https://arxiv.org/html/2609.38324v1)使这个区分更直接：同一批轨迹中，强推理模型可能更有效利用已经共享的证据，却更少共享能推翻自己意见的关键线索；较弱模型反而可能通过更高 pooling 获得更大讨论收益。与 HiddenBench 的“完整披露后可恢复”放在一起看，研究重点不能简单写成“增强推理”或“多分享信息”：关键在于需要的材料是否出现在公共上下文，以及出现后是否改变了相应判断。

这项模型还把私下异议、公开从众、后续内化和重新考虑拆开。其临界 withholding 分析与跨设置估计提供了对讨论收益的解释，且某些外部强制 withholding 干预支持方向性变化；但在 MuSiQue 上关系不清楚、净纠错为负，而且核心通信是受限 PUBLIC/SHARE 行，而非自由长篇论证。我们可以利用其可观测分解，不把临界公式当普适在线控制器。一个具体的待研究问题是：私有优势已被披露时，什么条件下它仍没有获得恰当影响力？这不是断言无人研究，而是由这些论文共同界定的比较位置。

## 4. 为什么交换 reasoning 有时有益、有时有害？

[InfoDelphi](https://arxiv.org/html/2607.01661v1)对375个固定证据池的预测任务，用 BM25 分公共与私有文档、两轮 rationale 交流、在 logit 空间按预测极端度加权；其消融显示去掉 rationale 会损害受测结果。[IMP](https://arxiv.org/html/2610.24718v1)则发现，把 sender 推理与答案重新加回原件 evidence 的 inbox 会降低受测任务表现。[ReConcile](https://arxiv.org/html/2309.13007v3)也用纠错示例和异构解释交换取得收益。这些结果相互约束，不能取一篇推广成“传推理总好”或“总该只传事实”。

条件差异给出了可研究的解释。InfoDelphi 中 rationale 承载对私有文档的有用概括，IMP 的 decoy/hidden-profile 中 sender 的错误立场容易把共享诱饵重新带回上下文；ReConcile 的人类解释示例教成员如何进行纠错性说服。因而内容有效性、立场影响、原件可见性与接收者先验可能共同决定传播收益。当前证据足以支持“研究这些交互条件有意义”，还不足以指定哪个机制一定是我们任务中的主因。

## 5. 接近能力的影响力，与可执行的修复策略

[Who Becomes an Influencer? v2](https://arxiv.org/html/2605.25929v2)是真正的直接近邻：它有实际 FJ 轨迹拟合，而非只有理论；在三个底模的多轮实例中，影响力随题变化、集中于少数成员，同时关联 competence、相对 confidence 和 stubbornness。其解释路由与[AgentAsk](https://aclanthology.org/2026.acl-long.1294/)的操作路由不同：AgentAsk 训练外部澄清器，在消息边上判断是否问、问谁、问什么，并在固定原编排的多框架数学、知识和代码任务中报告改善。前者帮助理解谁支配决策，后者给出局部介入的执行方式。

两者已经覆盖了很重要的思想，不能把“让可信的人影响别人”“精准求助”本身当首创。但问题并未因此封闭：Influencer 的事后 competence 不是部署可直接获得的真值信号，AgentAsk 的 handoff 修复也未以已知专家与团队采用的关系为主变量。若未来研究一个更明确的可见信号、干预对象或失效条件，应与它们逐项比较，而非要求每个模块全新。

## 6. 横向证据矩阵

补核的一篇直接改变缺口判断：[EMRC](https://arxiv.org/html/2508.13754v1)已经先用独立验证集建立模型领域表现表，再根据当前题科室与难度选择成员，融合历史可靠性和实例自信，指定最高领域expertise的成员核查，反馈修订后聚合。其TableIII比较随机/全局Top-N招募和去除融合/对抗核查的变体，TableIV还比较单成员与多成员。因此，**“稳定领域表现+动态选择没有方法”这一空白不成立**，也不能说它只做专家识别而没有尝试利用。它与ReConcile的固定异构组合、Influencer的事后动态解释形成互补：已有工作从识别、选择到协作均有实际方案，剩余研究要进一步落到当前判断可靠性与历史领域表现错配、错误意见的具体传播和采用等位置。

EMRC用1272题MedQA validation建立表现表，在MedQA test及NEJMQA、MMLU-Pro-Health上评估并报告超过所测单体/协作基线；结果有实质价值。它也观察到第五成员和第三交互层会退化，说明条件性收益和额外协作风险并存。分类依赖伪标签，历史表现不保证当前题判断正确；原始“已知专家仍被稀释”的过程干预未专门报告。这些属于可继续研究的具体边界，不能据未测某条件宣布EMRC无效，也不能将其医疗范围视为可忽略差异。元数据以primary为准：Bao与Peng共同一作，顺序Bao在前；本轮只确认arXiv v1，不臆造venue。

表的结论：已有工作改善了信息探索、解释交换、沟通控制和候选利用，剩余空间主要取决于想解释哪一种“优势没有变成团队收益”。

| 工作 | 优势/信息条件 | 实际改变什么 | 已验证的价值 | 仍未建立的范围 |
|---|---|---|---|---|
| HiddenBench | 私有事实分持 | 披露、Exchange→Decide | 子集上主动结构化交换有效 | 潜在信息空间的主动发现、能力型专家迁移 |
| Consilience | hidden-profile + 多控制器 | 讨论动作与speaker | 相对固定组织改善，含消融 | 代理目标与最终可靠采用的关系、已知能力专家 |
| IMP | 原句与持有者可绑定 | receiver inbox | 原件、去重和持有者覆盖有效 | 真伪与过期撤回、不能还原为原句的中间工作 |
| Dissent withheld | 私下/公开答复及分持线索 | 测量、提示和reasoning开关 | 区分pooling/utilization，解释条件差异 | 自由论证、开放任务过程测量 |
| Influencer | 同底模的角色/风格/示例差异 | 影响力建模 | 题目相关路由拟合，社会信号关联 | 可部署可靠性路由带来多大收益 |
| ReConcile | 异构与领域模型 | 解释、纠错示例、confidence投票 | 多基准单体及团队改善 | 错误说服与有效纠错的选择条件 |
| AgentAsk | 有向工作流handoff | 澄清gate/对象/问题 | 固定框架多任务提升 | 正确信息到达后仍被拒绝的利用失败 |
| InfoDelphi | 同模型不同证据视图 | 文档分配、rationale、概率聚合 | 固定检索池预测提升，消融支持 | 跨模型与来源可信度、其他任务迁移 |
| LLM-Blender | 独立完整输出 | 排序、生成融合 | 生成质量改善 | 专家已知时协商的必要性与可靠性 |
| EMRC | 验证集领域/难度表现表 | 动态招募、历史表现+自信融合、领域Judge与反馈修订 | 三医学基准及招募/协作消融支持收益 | 当前判断与历史专长错配、已知专家过程级采用 |

“未建立”是本文阅读范围中的验证边界，不代表方法失效；也不要求任何单篇研究解决表中所有问题。

**DEALS的范围边界（仅原文摘要，未纳核心精读JSON）：** [DEALS](https://arxiv.org/abs/2609.33768)，Huang、Wang、Yin、Velasquez、Liu，arXiv:2609.33768v1，2026-09-27，确实是expertise-aware协调：agent依据本地任务队列backlog与success rate决定就地处理或转交邻居，支持并发任务和部分解接续。其问题是任务流中的能力与负载匹配，不能从摘要直接推断它研究了同一题中专家意见如何被其他成员正确接受。本报告不依据摘要复述算法、效果数字或理论保证。它提醒我们专家路由并非空白，但与同题协商属于不同控制对象。

## 7. 对 RQ 的回答与候选问题

**RQ1。** 证据支持“信息分散、能力差异和角色差异不能混同”；也支持讨论有条件地有用，而非团队普遍无用。HiddenBench、Consilience、IMP 与 InfoDelphi 的正面结果排除了“这条研究线已经没有方法收益”的笼统说法。

**RQ2。** 已有方法分别修复材料出场、消息传播、解释说服、局部handoff和最终候选利用。识别、披露、采用和选择可以处于不同失败位置；改善其中一处是有效贡献，并不需要解决全链条。

**RQ3。** 最有依据的三个候选问题是：（a）把正确材料披露不足与披露后利用不足分开，解释模型和任务何时从一种失效转为另一种；（b）在已有社会信号影响力分析基础上，研究局部可靠性与实际影响力为何错配、什么具体干预有效；（c）解释同伴推理在何种信息条件下帮助传递专长、何种条件下携带错误立场。三者都有直接近邻，不包装成无人涉足，也有明确可继续细化的位置。先用当前文献把对象和差异说清，再决定哪些需要实验。

经EMRC补核，候选（b）必须明确：已有历史专长估计和动态招募/核查，不再提出“建立表现表然后选择专家”作为空白。可问当前个案与历史分组可靠性冲突时如何辨别与利用，或研究已测方法在何种条件下仍有采用错配；仍须后续进一步查证具体增量。

## 8. 检索日志与排除项

实际两轮及引文链：第一轮关键词包括 `multi-agent expertise utilization LLM heterogeneous 2026`、`Multi-Agent Systems are Mixtures of Experts Who Becomes an Influencer`、`LLM distributed knowledge collaboration expert 2026`；第二轮按发现收窄为完整题名及作者、`ReConcile Round-Table ACL 2024 Chen Saha Bansal`、`Diverse Evidence Better Forecasts InfoDelphi`、`LLM expertise routing influence multi-agent 2026`，并访问 AgentAsk/LLM-Blender 正式记录。原台账与本地PDF用于逆向引文补充 HiddenBench、Consilience、withholding 与 IMP。所有9条均核对 primary 元数据并读实际方法，具体范围在JSON；正式页与所读预印本版本分列。

- ICE：现有项目的这个简称是输入歧义的 uncertainty decomposition 工作，不是专家协作路由。未纳本视角核心证据，避免 acronym 搜索误入 Iterative Consensus Ensemble 等不同工作。
- iAgents/InformativeBench：与信息不对称有关，但本轮已有多篇更直接的探索—利用证据，未新精读，不据此作技术结论。
- Perspectra、自动基础设计等：人机研究控制或特定应用专家选择，本轮仅作为发现线索，不用于当前核心结论。
- 网上针对 Influencer 的 AI 二手审稿声称缺少实际验证，与 v2 §3/Table1 不符；不采用。仅以“ICML”关键词或二手论文解读标为 ICML 正式录用也不成立；作者主页列 preprint，报告按预印本处理。
- 高相关待交叉核读引文已告知评价视角：Stop Overvaluing Multi-Agent Debate（2502.08788）、等thinking预算多跳单/多agent比较（2604.02460）。未把未读结果写入上述9条。
- 盲点补充：父视角检得EMRC与DEALS后，本视角直接访问arXiv primary abs/html，精读EMRC §III/IV全部方法与消融，将其追加第10条；DEALS仅摘要级范围检查。未继续扩散新论文。

