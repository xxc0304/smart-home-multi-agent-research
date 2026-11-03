# Agent 方法分支：条件发现、局部知识保留与协同补足

核验日期：2026-10-20。只做文献检索与原文操作对齐，未运行模型实验。本文服务于 BRIEF 中的 RQ1–RQ3，不把通用框架的表达能力直接当作已经实现某个算法。排序限定于本分支的三个重点候选；SAVeR 与经典条件推理由其他分支负责，不能据此宣称全局最近邻已经确定。

## 两轮检索与身份核验

第一轮按指定论文 ID 和题名检索，分别打开正式出版页面、原文 PDF 或固定版本 HTML。第二轮从原文暴露的操作收窄到 assumptions、missing conditions、conditional claims、claim recovery、knowledge gaps、clarifying 等词，并读取实际部署的提示词。搜索得到的二手概述只用于找原文，以下判断都落到作者原文。

| 论文 | 身份与版本 | 本次精读位置 |
|---|---|---|
| Lin et al., *AgentAsk: Multi-Agent Systems Need to Ask* | ACL 2026 Long，2026.acl-long.1294，DOI 10.18653/v1/2026.acl-long.1294，正式出版 | §4；Appendix A.1–A.2、Algorithm 1；Appendix F / Figure 7（PDF 第 23 页）；Appendix D 案例 |
| Pappu et al., *Self-Organizing Agent Teams Learn to Reason Together*（SAT） | arXiv:2609.22682v1，2026-09-19 提交，页面明确标为 Preprint；未据此推断录用 | §2.1–2.2；Appendix A 的完整冻结策略；Appendix C 的协作轨迹；Appendix D.1 的最终选择提示词 |
| Wang et al., *VulAgent: Hypothesis-Validation Driven Multi-Agent Architecture for Vulnerability Detection* | Findings ACL 2026，2026.findings-acl.928，DOI 10.18653/v1/2026.findings-acl.928，正式出版 | §3.1–3.4；Appendix D–E；Appendix G 的 TriggerPlanner / AssumptionPruner / FinalValidator 提示词（PDF 第 18–19 页） |

来源：[AgentAsk 正式页面](https://aclanthology.org/2026.acl-long.1294/)、[AgentAsk 原文](https://aclanthology.org/2026.acl-long.1294.pdf)、[SAT 固定版本元数据](https://arxiv.org/abs/2609.22682v1)、[SAT 固定版本全文](https://arxiv.org/html/2609.22682v1)、[VulAgent 正式页面](https://aclanthology.org/2026.findings-acl.928/)、[VulAgent 原文](https://aclanthology.org/2026.findings-acl.928.pdf)。AgentAsk 原文链接的匿名代码站本次无法访问，因此不声称核验了实现代码。

## 按实际算法对齐

### 1. SAT：完整任务中最直接的局部贡献挽救与组合对照

SAT 不能仅作为“可搜索任意流程”的泛框架处理。其冻结部署库中确实有与当前目标直接重叠的协议：先独立求解并声明科学主张或假设；对薄弱处提出缺失条件或修复；保留经支持的个体主张；让其他成员回应并裁定；最后综合存活或修复后的贡献。`final_auditor_claim_recovery` 还专设 auditor，从初解中追回暂定共识遗漏的贡献。`option_conditions_and_absence_audit` 则分工为条件提出、条件证据支持或反驳、证据强度批评；`provisional_consensus_cross_validation` 从候选答案倒推必要条件。这里的相似性来自真实提示词，而非框架潜在表达能力。[SAT Appendix A.2](https://arxiv.org/html/2609.22682v1#A2)

| 对齐轴 | 已实现的操作及边界 |
|---|---|
| 运行时输入 | 同一完整问题；异构模型的完整独立初解；后续局部讨论历史。并非先保证每人只输出有效的局部关系。 |
| 缺口发现 | 明确列出初解中的 claims/assumptions，挑战缺失条件、被忽略效应、遗漏约束及错误步骤；也有由答案倒推必要条件的协议。 |
| 条件表示 | 在自然语言讨论中保存假设、必要条件、未解决分歧和证据；未见统一的条件贡献对象及跨步骤前件解除接口。不能据此断言自然语言无法表达条件关系。 |
| 同伴补足 | 成员分别提出条件、给证据、批评与修复；真实轨迹包含检查失败揭示缺口、另一成员构造所需约束、第三成员验证的协作。 |
| 冲突与更新 | 针对具体步骤裁定修复、弃用或保留；正确少数贡献可进入新共识；最终仍由证书池选择机制选答案。 |
| 真值、judge、工具 | 训练用问题结果指导策略变异与覆盖选择；测试冻结最多十个策略。团队成员担任最终 judge，先逐证书列局部缺陷，再按支持程度选择；无缺陷候选之间使用答案频率平局规则。此 judge 不是形式证明器。 |

**对 CoReTA 的判断。** “全员初始答案都错，但协作产生新解”“提取、保护、修复并组合局部主张”“发现缺失条件，再由同伴提供支持”都不能直接当作新意。可能的区别在于：能否把完整初解中错误的条件赋值与有效的条件关系分离，并在条件未解决时保留后者，随后通过明确的补条件动作重新激活。SAT 已覆盖相当多前后动作；差异必须落在这一中间对象、探测动作和更新规则上。

**证据边界。** 原文 Appendix C 的 AIME 2026 II-08 轨迹报告初始输出均未命中，整数检查暴露缺口后协作得到正确构造；这是新解产生的实例。数学物理平均准确率超过独立答案 routing oracle，也支持“超出挑选初解”的结论。但知识逻辑组的最终选择仍低于该 oracle；产生正确候选与识别它是不同瓶颈。这里没有独立重现实验。[SAT §3–5、Appendix C–D](https://arxiv.org/html/2609.22682v1)

### 2. VulAgent：条件化对象与前件检查最直接的实例

其核心状态为漏洞候选、触发条件集合与触发路径。Planner 从敏感位置反向构造路径，把保护分支和不确定情况记成假设，交给后续角色。Pruner 对每个假设检查可信性和失效影响；Validator 再检查路径是否被防护阻断。因此，“先留条件化候选、后做针对性条件检查”已经是具体流程。[VulAgent §3、Appendix G](https://aclanthology.org/2026.findings-acl.928.pdf)

| 对齐轴 | 已实现的操作及边界 |
|---|---|
| 运行时输入 | 带行号的函数、各检测角色的候选、项目身份与可选项目上下文；成员主要是同一任务的角色分工。 |
| 缺口发现 | 从候选 sink 反向追踪来源与数据变换，列出触发前提；不确定路径先标条件，暂缓过滤。 |
| 条件表示 | 显式保存 CWE、假设集合、触发路径、代码位置；条件检查还输出状态与原因。 |
| 补条件依据 | 项目代码、调用者/被调用者、类型和不变量；可用检索构造的上下文，也允许模型内部领域知识。不是假定每个条件都由可靠工具判真。 |
| 冲突与更新 | 所需前提被反驳可淘汰候选，再做路径防护审查；主要是保留/剔除漏洞假设，未展示把不同成员有效局部关系接成新的通用解。 |
| 真值、judge、工具 | 实验使用公开漏洞数据标签评分；未见该方法要求训练一个条件真值 oracle。Joern 等参与上下文构造，LLM 角色完成核心裁定，不等于 SMT 或执行证明。 |

**必须保留的文本细节。** 主文条件状态写为 valid/plausible/contradicted，提示词则用 plausible/contradicted/unknown，并要求没有明显反证时倾向 plausible；所以不能把“保留”写成“前提已被证实”。主文路径阶段限定候选路径，最终提示词却要求也考虑完整上下文和其他防护；这限制了将其抽象为严格局部验证算法的力度。[VulAgent §3.3–3.4、Appendix G](https://aclanthology.org/2026.findings-acl.928.pdf)

**对 CoReTA 的判断。** 若贡献只是自然语言假设显式化、暂存条件路径、逐条件请求验证并过滤错误，重叠很大。若目标是从不完整且有错的成员知识中恢复可复用关系，再让其他同样不完美成员解除前件、构造新解，VulAgent 尚不能直接视为已经覆盖；其主要能力是上下文证据支持下的候选验证。

### 3. AgentAsk：传播前的定向追问与交接修复

每个交接边的控制器读问题或子目标、发送者、接收者、待交接消息与近期上下文，决定是否问、问谁、问什么。提示词针对缺少细节、错误字段、指代漂移和能力缺口，要求一个最小问题，并可请求必要计算或重定向。回复交给下游，原框架继续运行。[AgentAsk §4、Appendix A/B/F](https://aclanthology.org/2026.acl-long.1294.pdf)

| 对齐轴 | 已实现的操作及边界 |
|---|---|
| 运行时输入 | 已经产生、即将交接的完整消息或子任务消息；不要求它是完整最终答案。 |
| 缺口发现 | 外部 clarifier 根据局部交接状态识别缺失信息或错误传播风险；问最小缺项。 |
| 条件表示 | 输出错误类型、收件人、问题；未给有效条件关系单独的持久表示、解除规则或依赖图。 |
| 同伴补足 | 向原作者或其他相关角色提问，必要时请求计算或重定向；这是实际的 peer clarification。 |
| 冲突与更新 | 修复交接再下传，可以同一边多次问；不是对全体成员条件贡献进行统一组合。 |
| 真值、judge、工具 | 训练有 teacher 生成的问询类型/收件人/问题标签，再用局部奖励及终局成功奖励优化；测试使用学得控制器。工具能力取决于底层 MAS。 |

**对 CoReTA 的判断。** “避免下游猜缺失细节，向合适成员问最小问题，阻断级联”已高度接近。尚未看到“保留已知局部关系、悬置不可靠补全、用他人知识解除前件”的独立算法对象。但这只支持对象与操作上的区别，不能将 AgentAsk 降格为仅仅泛化的错误检测。

**效果数字校准。** 摘要写最高提高 4.69%，Table 1 中该最高框架平均增益属于 +GPT-5 clarifier；轻量 +AgentAsk 的平均提升为约 3.29–3.45 个百分点。比较时必须区分这两种设置。[AgentAsk Table 1](https://aclanthology.org/2026.acl-long.1294.pdf)

## 算法距离排序及可用结论

“最近”取决于比较的动作，不应硬压成单一相似度：

| 比较目标 | 本分支最近者 | 原因 |
|---|---|---|
| 不完美团队保留局部贡献并构造新完整答案 | SAT | 实际部署了缺失条件挑战、证据回应、少数主张挽救、修复后综合；也有全体初解失败后的协作轨迹。 |
| 把不确定结论保留为带前提的对象，再检查必要前提 | VulAgent | 显式假设集合与路径、逐前提检查、状态和证据、条件失败导致候选剔除。 |
| 未获支持的信息交接前，定向问合适成员最小缺项 | AgentAsk | 边级 gate、收件人选择、问题生成与回复下传均为实际操作。 |

综合当前“互补成员组合新解”的任务，**本分支优先强对照为 SAT，其次 VulAgent、AgentAsk**；若最终方法聚焦条件化状态表示，VulAgent 的比较优先级会上升。该排序不是全局排序，SAVeR 和经典分布式条件推理可能改变最终结论。

可以保留的研究缺口表述是：“现有协议分别实现了局部贡献挽救、条件化候选验证和交接追问；还需要明确规定如何在完整作答中的错误补全被否定后，保留同一贡献中的有效条件关系，并依靠互补且不可靠的成员逐步补齐条件。”这是一项待定义、待证据支持的机制目标。不能据本次检索写成从未有人组合部分知识、从未有人探测假设或从未有人保护正确少数。

## 第二轮新增候选与筛选记录

- [SEMA-RAG，Findings ACL 2026.917 原文](https://aclanthology.org/2026.findings-acl.917.pdf)：搜索命中明确的 missing conditions/reasoning steps → follow-up queries → retrieval → evidence-set update → evidence arbiter。它提醒我们把缺口追问闭环单独作为新意很弱。当前只核验了原文检索片段，未完整读取提示词，故不将其列入前三名或据此主张已经完成 peer conditional expertise。
- [Multi-agent Abductive Reasoning with Confidentiality，AAMAS 2011 原文](https://www.ifaamas.org/Proceedings/aamas2011/papers/R36.pdf)：命中 local conditional answers、缺失知识假设和跨成员假设一致性检查，已转给经典分支继续核验。
- [Asking the Right Question: Epistemic Inquiry as a Learnable Reasoning Skill for Scientific Discovery](https://openreview.net/pdf?id=o74e2eQb07)：命中可监督的 epistemic gap 表示，已转给澄清分支；本分支不据搜索片段判断方法重复。

检索没有发现，不等于不存在。上述距离判断只覆盖已读版本与所列具体协议；可执行代码本次未核验。
