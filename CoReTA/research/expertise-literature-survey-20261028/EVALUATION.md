# 反证与评价视角：讨论是否有用，取决于保留什么和怎样读出

核读日期：2026-10-28。按冻结 BRIEF 的 RQ1–RQ3，独立宽搜后以新机制词窄搜；9 篇进入证据矩阵，详见 EVALUATION.json。所有机制描述均核读原文方法、对应结果或附录；未运行实验。

## 1. 跨论文综合

[Talk Isn't Always Cheap](https://arxiv.org/html/2509.05396v2) 观察异质强弱成员讨论仍可退化，[Debate or Vote](https://arxiv.org/html/2508.17536v2) 则把收益分解为初答集成与后续交互；二者一起支持“更多讨论不自动增加收益”，并不支持“讨论永远无用”。前者在不同任务/组合有正负结果，后者的中性漂移定理依赖同质信念与更新/拓扑条件，其可部署多数引导也可优于 vanilla。金标锁定的 MAD-oracle 只能说明保留正确候选的潜力。

[ColMAD](https://arxiv.org/html/2510.20963v2) 提供了相反方向的具体正面证据：把赢辩论/追共识改为补足缺失证据，并结合context引文检查、自审和置信表达，在其错误检测任务与匹配预算下优于原协议和部分 SA 比较。这与上述反证并不矛盾：任务从开放解题转为给定输出的错误检查，支持证据可引用，协议与读出也发生变化。引用的 exact-match 只检查出现性，不能当成语义真值证明；但这不抹去方法已报告的经验贡献。v2已有组件消融、成本与统计附录，旧评论不能代替当前原文。

[ICR](https://arxiv.org/html/2610.01042v1) 与 [Not All Flips](https://arxiv.org/html/2606.00820v2) 共同把分析从最终正确率推进到改答事件；前者冻结初始轨迹并按双方初始正确性分层，后者加入匹配的无同伴重想/立场/理由条件，避免把自行不稳定当peer影响。ICR的完整理由同时增加纠错和损害，Flips最新部署干预则同时抑制两者，说明“影响更强”与“采用更有选择性”是不同目标。两者是有价值的审计进步，不能因其未建设完整专家团队而否定其贡献，也不能把单跳初答正确直接当稳定专长。

[Identity Skews Debate](https://aclanthology.org/2026.acl-long.650.pdf) 去除自我/同伴标记，重点解决身份敏感；[Easier to Mislead](https://arxiv.org/html/2606.01637v2) 操纵六个模拟peer的答案与权威角色，重点比较伤害和纠错方向。两者都提示“谁说的”会影响更新，却不能互换为真实能力校准：前者附录J明确准确率总体大体不变，后者权威仅是标签。对专家研究而言，应区分无根据的身份偏好与有依据的能力来源；匿名化不必消除一切可用专家信息。

[One Axis, No Brake](https://arxiv.org/html/2609.18998v1) 的置信门控、探针和steering结果，与 Easier/Flips 的非选择性干预结果方向一致；但它的经验探针分数是所测信号的 lower bounds，且社会信号不含新论证，不能推广成所有工具、检索、内容核查都不可能。它的预承诺 warrant 仅暴露与先前改答条件不符的现象，尚未降低flip；这为“改变判断的依据”提供线索，尚非已验证解决方案。

## 2. 条件矩阵：评价进展已有，但目标并不相同

[Stop Overvaluing](https://arxiv.org/abs/2502.08788v3) 的正面异质性结果与 Talk Isn't Always Cheap 的弱模型拖累结果也不相互否定：前者每次生成随机从两模型池取模型，主要比较单模型框架平均与 CoT 平均；后者固定强弱成员配置并比较初答投票/讨论后。相对平均收益、超过最佳固定个体和可靠利用某个专长是三个层次。前者明确留下“专门利用异质性的机制”未作设计，但这只是方向空间，不能直接认证我们的未来方法新颖。该文原 HTML 正文缺失，方法实际核读本地 v3 PDF 第1–12页。

| 论文 | 主要比较单位 | 已解决或推进 | 有依据的剩余问题 |
|---|---|---|---|
| ICR | 固定轨迹的单跳有向事件 | 分开纠错/保留与无消息额外推理 | 所测结构化策略仍有tradeoff；完整专家团队迁移未验证 |
| Not All Flips v2 | 单轮相同初答的三个条件 | 区分重想、立场采用、理由采用 | 部署干预压低两类采用；多轮异质未测 |
| Easier to Mislead v2 | 模拟peer线索干预 | 有害/有益影响方向与强度比较 | 普通推理提示未选择性改善；真实专长未验证 |
| Identity Skews | 自我/peer标记改变 | IBC与匿名化去身份偏差 | 准确率大体不变，质量权重有待研究 |
| Debate or Vote | 初答投票与多种讨论 | 分解集成/互动；多数引导 | 正确少数保留的非oracle机制仍需具体方法 |
| ColMAD v2 | 不同激励协议、SA/成本 | 所测错误检查收益、互补证据操作 | 专家明示和局部采用未以该目标检验 |
| One Axis | 无论证社会信号、内部信号/群体 | 所测信号的可分性限制 | 独立信息来源、完整内容推理不能据此否决 |
| Talk Isn't Always Cheap v2 | 讨论前后、强弱组合 | 弱成员拖累的条件性实证 | 可靠专家明示/验证机制未检验 |
| Stop Overvaluing v3 | 多框架/强SA与随机模型池 | 标准化评价与异质性平均收益 | 未设计针对性专长利用机制；不保证胜最强成员 |

## 3. 对 RQ 的回答和适合继续阅读的问题

RQ1：团队损失已有多种证据，同时存在明确的正面任务与协议条件。群体低于初答投票、低于最佳固定单体、低于逐题 oracle、个体改错和最终丢失正确候选是不同结果，不能混作一个“专家没用好”的数值。父代理另核原始 Hold Experts Back 的 Table 2；本视角不替代其专家定义。

RQ2：已解决部分子问题的方法有真实贡献：匿名化去身份偏差、受控审计分离通信影响、ColMAD改善特定任务的证据互补；这些贡献不需要覆盖全部专家利用问题才成立。它们的共同限制更具体：改善意愿、表达或偏差，不总带来改善最终决策的有效信息。

RQ3：值得研究的候选问题是，**什么信息使团队有依据地接受一个不占多数的可靠贡献，并在贡献出错时仍能纠正？** 现有论文分别提供社会线索、内容、内部信号和核查协议的条件证据；在决定新机制前，应继续区分“能力先验”“当前贡献的可检验依据”和“最终读出”各自承担什么。这里是跨文献问题定位，不是无人做过或方法新颖性认证，也不要求所有组件首创。

## 4. 搜索与验证日志

第一轮宽搜：
- multi-agent debate expertise evaluation conformity beneficial harmful revision benchmark 2026
- “When and Why Does Multi-Agent Debate Fail”
- “Debate or Vote” “NeurIPS” 2025

第二轮按线索窄搜：
- “One Axis, No Brake” self knowledge warrant
- “When and Why Does Multi-Agent Debate Fail” “ColMAD”
- “Talk Isn’t Always Cheap” Wynn Satija Hadfield
- 精确题名检索 ICR、Not All Flips、Identity Skews、Talk Isn't Always Cheap，随后转原文方法与附录。

引用链补查：Debate or Vote 的 oracle/多数引导差异；Identity 附录J的任务准确率；ColMAD v2 的补充消融/同预算结果；One Axis 的 warrant 与经验界限；Flips v2 的诊断/部署分离。

候选排除或交接：
- MADBench（2609.39146）：检索发现，为恶意攻击安全基准，非当前自然专家利用主问题，未据其摘要作机制结论。
- DEBATE（2510.25110）：目标是拟真人类意见动态，非客观解题专长利用，未纳核心矩阵。
- MABPD（2026.emnlp-main.1777）：应用特定偏差检测正面线索，尚未核读方法，暂不用于推论。
- 引文链补核 Stop Overvaluing 的v3本地全文并纳第9篇；Why Do Multi-Agent LLM Systems Fail 属更广系统失效分类，本视角未以未核读资料补结论。
- 二手 Pith/Lacuna 等仅提供发现线索，未用其评论和数字支撑报告。

元数据注意：Identity 正式PDF使用 Xiaojin Zhu，Anthology使用 Jerry Zhu，为别名表示；One Axis 原HTML日期与arXiv ID月份不一致，保留版本与年份、不据日期做优先权判断。Talk workshop身份由作者主页核实。ColMAD主会身份未独立证实，因此标预印本并记录全文自述workshop，不擅标主会录用。

