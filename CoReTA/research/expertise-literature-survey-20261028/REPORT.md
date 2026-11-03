# 多 Agent 专长利用：正确贡献怎样转化为团队判断

核读日期：2026-10-28。本文面向 CoReTA 选题讨论；当前阶段为文献理解与问题界定，未启动新的复现、训练或研究模型实验。

## 摘要

团队中存在更可靠的成员或正确依据，并不意味着最终决策能利用它；同时，许多方法已经通过组织学习、参考关系调节、解释交换和证据读出取得实际收益。本文围绕“已知什么、已有工作解决什么、还有什么值得研究”三个问题，结合本地原文与在线来源，对 35 篇工作核读相关方法、结果及限制段落。综合发现：专长的定义与比较参照不同，是许多表面矛盾的来源；材料披露、意见修订与最终选择是可分开的失效位置；降低从众不等于提高选择性，但已有训练方法在所测条件下同时改善纠错和抗有害影响。较有依据的研究空间在于，可靠性线索、当前论证可检查性和最终读出何时错配，以及如何在具体条件下改善这种错配。这些直接近邻为进一步细化研究对象提供了比较基础。

## 1. 从原始动机确定调查对象

CoReTA 的动机来自《Multi-Agent Teams Hold Experts Back》：即使团队被告知谁具有优势，也未必能把这种优势转成更好的判断。该工作既研究人为分配专家解释的信息优势，也研究不同底层模型在具体题上的差异；它让“专家识别”和“专家利用”成为可以分别讨论的问题。[1](https://arxiv.org/html/2602.01011v4)

调查先分析专长信号、交流内容和最终决策，再选择具体方法。先回答三个问题：

- **RQ1：已知什么？** 哪些条件下优势被稀释，哪些条件下协作已经有益？“专家”“正确”“采用”和“协同”怎样被定义？
- **RQ2：已经解决了什么？** 不同方法实际改变哪些操作，在什么信息、训练和评价条件下有效？
- **RQ3：还有什么值得研究？** 哪些是已经观察到的剩余失效，哪些只是未验证范围，哪些尚缺充分检索？

研究可以在共同问题上提出更明确的解释、更有效的机制、一个有意义的新条件，或发现既有机制的关键交互。本文按这些具体增量比较工作。

## 2. 检索、核验与阅读范围

冻结任务书见 [BRIEF.md](BRIEF.md)。以统一台账和 57 篇本地 PDF 为起点，四个视角分别检索改进方法、反证与评价、专长/信息互补、原始锚点与候选读出；前三个视角由三个分工代理开展，主代理负责第四视角和串行综合；各代理共享项目背景。各视角都有宽搜、按新词/完整题名窄搜，以及引文链补查。覆盖 2023–2026 年，重点检查最近六个月的版本更新。

35 篇进入核心矩阵。每篇记录题名、作者、版本、出处、实际阅读范围、操作、结果、条件与剩余问题；“核读”指相关方法、结果和附录的分段阅读，并非声称逐字通读每篇全部内容。逐篇材料见 [PAPER_MATRIX.md](PAPER_MATRIX.md) 和 [CORPUS.json](CORPUS.json)，原始分视角记录见 ANCHOR、METHODS、EVALUATION、EXPERTISE 四组文件。搜索与排除记录保存在对应 MD 及 [SEARCH_LOG.md](SEARCH_LOG.md)。

使用 arXiv、正式会议/出版社页面及作者来源核对。正式版与预印本不同则分别记录；部分论文正式 venue 未确认时使用预印本身份。Conformal Social Choice 的正式 PDF 抓取遇到 cache miss，技术核读使用已有 v2，并对比正式页面元数据和摘要。One Axis 的公开提交日期与 arXiv ID 月份不一致，内容可核验，但不据日期判断优先权。未把二手 AI 审稿的缺陷指控当作论文证据。

本文覆盖与当前 RQ 直接相关的 LLM 协作研究。应用领域和经典社会科学的系统覆盖留待特定问题确定后补充。新在线原文的本地归档状态见统一 catalog。

## 3. 用四个决策位置组织证据

| 决策位置 | 要弄清的问题 | 主要操作 | 比较时最容易混淆什么 |
|---|---|---|---|
| 优势与失效的识别 | 谁在哪些条件下可靠，损失发生在哪一步？ | 条件操纵、过程审计、影响力建模 | 初答正确、稳定能力、私有资料和角色标签 |
| 材料与帮助的获取 | 需要的事实或推理有没有进入可用上下文？ | 招募、披露、消息路由、澄清 | 披露更多与使用更好 |
| 互动中的影响与修订 | 看谁的意见，何时坚持或改变？ | 提示、过滤、关系策略、组织学习 | 更少改答与更好改答 |
| 最终读出与执行 | 已有贡献怎样变成输出，何时应升级核查？ | 排序、局部审计、融合、集合决策 | 候选中有正确解与实际选中、筛选与推理提升 |

分类依据主要干预或研究对象；SAT、DEAR、Consilience 等横跨多个位置，本文比较其跨层作用。核查者能力作为最后两层的共同条件讨论。

## 4. 专家被拖累的证据成立，但需要保留条件与参照

### 4.1 相似表述背后，比较对象经常不同

原始工作在心理任务上发现已知信息优势未被充分利用；Talk Isn't Always Cheap 则显示固定强弱成员组合可能在讨论后退化，但不同任务也有改善。Debate or Vote 关注初答集成与后续交互的增量，不能与“低于某位专家”互换。[1](https://arxiv.org/html/2602.01011v4) [2](https://arxiv.org/html/2509.05396v2) [3](https://arxiv.org/html/2508.17536v2)

一个必须保留的细节是原始论文 v4 Table 2：公开专家团队在 GPQA、SimpleQA、HLE 和 MATH 上已经高于最佳固定单体，虽然仍低于逐题 ALOC。心理任务的信息专家对照与 ML 上的逐题理想选择是不同参照。Stop Overvaluing 的异质模型池结果主要优于单模型框架平均，这又是第三种比较；它与固定强成员被拖累并不互相否定。[1](https://arxiv.org/html/2602.01011v4) [4](https://arxiv.org/abs/2502.08788v3)

| 参照 | 它回答什么 | 不应推出什么 |
|---|---|---|
| 最佳固定单体 | 这组任务交给一个可事前选定的强模型如何？ | 不等于每题都知道谁会答对 |
| 信息优势单体 | 优势材料独自使用能达到什么效果？ | 不等于训练所得的稳定领域专长 |
| ALOC / proposal-hit oracle | 候选池中是否曾有正确答案？ | 不等于可部署选择器，也非所有新方法必须达到的门槛 |
| 初答投票 / 同预算独立采样 | 交互是否增加了集成之外的价值？ | 不说明正确依据究竟怎样被采用 |
| Full Information | 相同材料集中提供的实测表现 | 并非一般性能上界，格式与额外推理仍会影响表现 |

研究可以推进一个明确目标，例如减少专家信息丢失，或解释何时会丢失。所选参照应对应贡献：强协同关注最佳固定个体，交互增量关注同预算独立采样，候选利用关注已有正确候选的实际转化。

### 4.2 改答与从众的分离，使问题更具体

ICR 固定初始轨迹，按发送与接收双方的初始正确性测量纠错和保留，并加入无消息复查；Not All Flips 进一步用自行重想、只给立场、完整理由条件分解改答来源。两者都说明只看最终正确率或改答率会漏掉机制，但并未要求建设完整专家架构才能形成有效贡献。[5](https://arxiv.org/html/2610.01042v1) [6](https://arxiv.org/html/2606.00820v2)

Easier to Mislead 与 Identity Skews 分别显示模拟同伴的社会线索和来源标记会影响更新；前者的权威标签不是实际能力，后者匿名化降低身份偏差也不保证最终准确率提高。One Axis 所测置信门控、探针和 steering 常同时改变有害与有益采用，但其经验信号不构成所有检索、工具或内容核查的不可能性界限。[7](https://arxiv.org/html/2606.01637v2) [8](https://aclanthology.org/2026.acl-long.650/) [9](https://arxiv.org/html/2609.18998v1)

ColMAD 给出重要的正面补充：在所测错误检测等任务，以补足缺失证据、引文存在性检查、自审和合作激励，改善了协议及匹配预算的部分单体比较。Who Becomes an Influencer? 则把实际轨迹拟合为输入相关的影响路由，发现影响力同时关联事后 competence、相对自信和坚持。二者帮助把问题从“是否妥协”推进到“什么信息和规则改变了有效影响力”；关联仍不能直接当作已隔离的因果。[10](https://arxiv.org/html/2510.20963v2) [11](https://arxiv.org/html/2605.25929v2)

## 5. 信息与专长的获取，已经有可用的方法成果

ReConcile 通过异构模型、解释交换、纠错性示例和置信加权取得收益；EMRC 更直接建立基于验证集的“科室×难度”模型表现表，按问题选择成员，并让历史专长参与自信融合与 Judge 选择。它在受测医学 QA 上有招募、融合、核查消融和单/多成员比较，这构成了领域表现评估、动态招募与协作的完整方法先例。[12](https://aclanthology.org/2024.acl-long.381/) [13](https://arxiv.org/html/2508.13754v1)

EMRC 的价值是把专长从 persona 变成实际历史表现并用于协调；其未解决范围也更具体：历史领域平均可靠性并不认证当前判断，更多成员或层数仍可能退化。这里可以继续研究优势何时没有转成有效影响力，跨领域研究的贡献应落在新的机制条件或发现上。[13](https://arxiv.org/html/2508.13754v1) [11](https://arxiv.org/html/2605.25929v2)

HiddenBench 并不只是失败 benchmark：在其受测子集上，机械 Reveal-All 近乎恢复，而轻量 Exchange→Decide 也改善了结果。Dissent Withheld 则把公开披露、后续内化和利用拆开，显示 pooling 与 utilization 可以反向变化；某些模型更会用已经共享的信息，却更少把反对自己意见的关键线索共享出来。[14](https://proceedings.mlr.press/v306/li26ej.html) [15](https://arxiv.org/html/2609.38324v1)

Consilience、IMP 和 InfoDelphi 分别把干预放在组织动作、接收者 inbox 和证据分配上：前者比较挑战/澄清/取证/路由动作；IMP 绑定原句、按接收方去重并转发缺失材料；InfoDelphi 将公共与私有文档分配给同模型成员后交换 rationale。这些方法分别改善了组织选择、消息可达性和证据互补。[16](https://arxiv.org/html/2608.20564v1) [17](https://arxiv.org/html/2610.24718v1) [18](https://arxiv.org/html/2607.01661v1)

其中最值得解释的张力是：InfoDelphi 的 rationale 消融支持传递推理有益，IMP 所测条件加回推理与答案却损害表现。前者的理由可能传递对独有文档的有用概括，后者的理由可能重新带入共享诱饵或错误立场；这是一种由条件差异支持的解释，不是已经在同一设置中证明的主因。AgentAsk 在另一位置训练边上的澄清器，固定原工作流后决定是否问、问谁和问什么，也表明“有针对性的帮助”已经有可执行先例。[18](https://arxiv.org/html/2607.01661v1) [17](https://arxiv.org/html/2610.24718v1) [19](https://aclanthology.org/2026.acl-long.1294/)

## 6. 从坚持到选择性修订，已有进展也有不同路线

Free-MAD 取消强制共识，以具体错点检查和全轨迹计分保留候选影响；Peacemaker 用 persona 控制合作与反对程度，较好配置通常不是所有人最顽固。两者共同提示应研究适当让步的条件；Free-MAD 部分弱模型任务的固执是真实观察，但不应覆盖其其他任务的正面结果。[20](https://aclanthology.org/2026.findings-acl.1600/) [21](https://arxiv.org/html/2509.23055)

Demystifying 不只是要求模型报置信分，而是训练置信表达与接收使用；CortexDebate 用能力 proxy、差异、置信和参与度调节有向关系；DEAR 则训练选择参考同伴和生成参数的两个控制策略。这些方法已经实际改变更新机制，贡献分别落在可靠度表达、参考关系和生成行为的调节上。[22](https://arxiv.org/html/2601.19921) [23](https://aclanthology.org/2025.findings-acl.495/) [24](https://arxiv.org/html/2608.03648v2)

尤其应更新我们先前的认识：DEAR v2 附录 E.1 在同质 Qwen3-8B 的四任务上，同时报告更高 BCR 和更低 HCR；其指标是有唯一多数时，错误少数转向正确多数、正确少数转向错误多数的相邻轮转移。它提供了选择性改答的正面方法证据，与 ICR、Flips、Easier 的非选择性提示结果共同界定了学习策略和通用提示的差异。它与 ICR 的单跳条件指标不同，数字不宜直接横排。[24](https://arxiv.org/html/2608.03648v2) [5](https://arxiv.org/html/2610.01042v1)

SAT 的贡献路线又不同：从过去协作中离线提出、评估并筛选组织策略，冻结后迁移到新任务。数学/物理套件的结果支持超强成员及匹配控制的协作收益；知识/逻辑中，正确 certificate 覆盖与最终选择之间仍有损失。它的附录流程是学习产物，比较时应同时考察策略如何学得及部署时做了什么。[25](https://arxiv.org/abs/2609.22682) [24](https://arxiv.org/html/2608.03648v2)

CONSENSAGENT 与 MAD-M² 分别通过题意/提示优化和 memory 筛选改善输入：前者训练 prompt optimizer，推理时优化器只看原问题；后者实际删除下一轮可见的整条响应。它们都比“提醒谨慎”更具体，但方法收益依任务和模型变化。输入理解错误、内容冗余和社会压力可以并存，需要分别定位。[26](https://aclanthology.org/2025.findings-acl.1141/) [27](https://arxiv.org/html/2603.20215)

| 路线 | 改变的对象 | 已有证据 | 需要保留的边界 |
|---|---|---|---|
| Free-MAD / persona 控制 | 坚持/让步指令与轨迹权重 | 受测条件改善，过强抗从众也可能有害 | 保持本身不是正确性证明 |
| Demystifying | 置信表达和接收使用 | 训练后可改善更新 | 不等于任意自报置信可靠 |
| CortexDebate / DEAR | 谁参考谁及如何生成 | 动态关系、选择性修订与效率有正面结果 | proxy与当前主张可靠性仍不同 |
| SAT | 整个组织策略的取得方式 | 冻结策略迁移、协作产生与选择 | 产生正确解和认出正确解可分离 |
| CONSENSAGENT / MAD-M² | 原题提示或下一轮上下文 | 题意修复、减少有害/冗余输入 | 不同模型与任务上的效果不同 |

## 7. 正确候选的利用已有具体算法，统计安全是另一合法目标

When Debate Helps 把候选供给与读出分开，用覆盖目标选择互补模型，并通过固定候选的证据干预研究内容影响；AgentAuditor 更直接把轨迹对齐成推理树，在关键分叉处比较局部依据，并可用 ACPO 训练核查者。两者已经为“正确少数存在却未被利用”提供了具体读出机制。[28](https://arxiv.org/html/2610.04686v1) [29](https://arxiv.org/html/2602.09341v2)

两者也保留了明确边界。When Debate Helps 某些模型/任务仍有候选空间却负收益，LVD 的伪计数是读出理论抽象，不是部署时自动知道真值；AgentAuditor 在正确路径缺失或分支不可区分时恢复有限。Minority Sentinel 通过轨迹分类器决定是否推翻末轮多数，LLM-Blender 通过候选排序与生成融合取得收益；它们提供不同于全员改答的路径，历史材料与完整候选的保存也已有操作先例。[28](https://arxiv.org/html/2610.04686v1) [29](https://arxiv.org/html/2602.09341v2) [30](https://arxiv.org/html/2606.29270) [31](https://aclanthology.org/2023.acl-long.792/)

Conformal Social Choice 与 C-MoA 说明，研究贡献也可以是“怎样控制输出风险”。前者用概率聚合、校准集合决定自动执行或升级人工，后者用跨模型支持排序与答案级阈值保留主张；它们并未声称每题推理变强。前者的单元素高准确率包含选择效应，后者空答案也能满足支持性事件，因此自动覆盖、内容保留和准确性应共同解释。[32](https://arxiv.org/html/2604.07667v2) [33](https://arxiv.org/html/2609.25959v2)

C-MoA 的 optional CONTRA 分支还提供具体反例：其 memory-only 反事实与 LOO 信号在所测 FactScore 条件下接近随机，融合后排序更差；且报告中的 Verify/Rescue 只保留并标记，没有执行新的修复。把这个负结果与 AgentAuditor 的正结果放在一起，得到的是核查能力、监督和证据条件的重要性，而非所有反事实核查都无效或所有局部审计都有效。[33](https://arxiv.org/html/2609.25959v2) [29](https://arxiv.org/html/2602.09341v2)

## 8. 跨分支综合：什么才是值得细化的“利用不足”

### 8.1 优势转化有多个位置，原课题可以据此收窄

下列区别得到不同文献的支持，不应合并成单一从众率：

| 可定位的问题 | 对应证据 | 对研究对象的含义 |
|---|---|---|
| 有用材料未被公开或送达 | HiddenBench、Dissent Withheld、IMP | 研究披露、注意和信息可达性 |
| 材料已到达，但不能被正确理解或检查 | ICR、AgentAsk、核查能力工作 | 研究解释、局部证据与接收条件 |
| 原本正确者被错误信息改变 | Free-MAD、Flips、DEAR | 研究更新的选择性 |
| 正确者保持意见，但团队仍选错 | Hold Experts Back、SAT、AgentAuditor | 研究影响权重与最终读出 |
| 所有候选缺少正确答案或关键推理 | When Debate Helps、SAT | 研究互补供给与协作创造，不能只换选择器 |

低成本提示、训练控制器、候选审计、成员招募分别可以改善其中一处。**推进其中一个重要环节，就可以形成清楚的研究贡献。** 反过来，把所有已知操作叠起来并不自动形成更好方法，具体问题应决定要改变哪一步。

### 8.2 核查者不必独立完成全题，但必须得到可用的判断依据

Kenton 等比较弱 judge 与强辩手，信息不对称 QA 上有正面收益，闭卷推理则混合；Kirchner 等通过训练 prover 的可检查表达，提高了所测弱 verifier 与限时人类的判断能力。它们提供了区别于“直接让专家坚持”或“找一个全能裁判”的路线：改变依据怎样被展示和检查。[34](https://arxiv.org/abs/2407.04622v2) [35](https://arxiv.org/abs/2407.13692v2)

这些相邻证据与 SAT 的 demonstrability 相关性、C-MoA 的核查能力边界相互补充：有的任务接收方需要额外知识，有的只需把关键推理变得可核查。解释的价值取决于接收者能否检查关键依据。围绕这种条件差异，可以建立实证解释或具体方法。[25](https://arxiv.org/abs/2609.22682) [33](https://arxiv.org/html/2609.25959v2) [34](https://arxiv.org/abs/2407.04622v2) [35](https://arxiv.org/abs/2407.13692v2)

### 8.3 共享组件不会自动抹去贡献，比较应落在可验证的增量

Conformal Social Choice 明确使用既有 split conformal 理论，其贡献落在多 agent 决策的自动/升级契约与验证；AgentAuditor 用已有偏好优化方法训练局部分支裁决；DEAR 用已有多 agent RL 优化参考关系与行为。这些工作的创新都不是“每个模块从未出现过”，而是针对问题的对象、机制联系与证据。这个标准也应一致用于 CoReTA。[32](https://arxiv.org/html/2604.07667v2) [29](https://arxiv.org/html/2602.09341v2) [24](https://arxiv.org/html/2608.03648v2)

所以，研究相同问题、复用已有模块、做有意义的组合是正常的。真正需要说明的是：加入了什么可识别的增量，解决哪种原来仍困难的情况，以及结果能支持多大范围。缺少某个实验不使整篇论文失效；反之，只因未找到完全同构架构，也不能宣称创新已经成立。

## 9. 值得继续讨论的三个问题及其近邻

以下三个候选问题用于接下来的研究讨论；每项都列出直接近邻和需要澄清的条件。

### 9.1 可靠性线索如何转化为恰当影响力？

**与 CoReTA 现状的区分：** 下文“历史可靠性”来自 EMRC 等相关论文，是一个可供比较的研究条件，不是 CoReTA 已经使用或必须加入的机制。现有项目主要通过当前任务的资料分配产生信息优势；曾有离线独立信息校准，但没有因此形成运行时历史专长档案。当前仍先围绕专家意见与团队折中界定问题。

**问题：当一个成员有可说明的领域或信息优势时，历史可靠性、当前自信与多数压力分别怎样影响它的意见被采用？**

依据是 Hold Experts Back 的揭示专家仍有损失、Influencer 的能力/自信/坚持关联，以及 EMRC 用历史领域表现与实例自信进行融合。已有研究分别做了诊断、解释和实际协调；可继续细化的是这些信号不一致时的行为与作用条件，其比较基础包括现成的专长表、置信融合与影响力模型。[1](https://arxiv.org/html/2602.01011v4) [11](https://arxiv.org/html/2605.25929v2) [13](https://arxiv.org/html/2508.13754v1)

潜在价值在于解释何时历史优势能帮助、何时不足以判断当前贡献，或提出针对某种错配的改进。这些条件之间的关系仍需结合近邻进一步厘清。如果已知专家可以独自解决整题，直接选它是有效参照；团队额外价值需单独说明，但研究减少损失或解释损失不必一开始就声称超强协同。

### 9.2 何种推理交流传递了专长，何种交流只放大了立场？

**问题：同伴传来事实、关键推导、完整理由或只有答案时，什么内容能帮助接收者辨别当前争议，而不是只提高跟随倾向？**

InfoDelphi 的理由交流收益、IMP 的排除理由收益、ICR 的更强影响同时增加纠错和损害，以及 ColMAD 的证据互补正结果，构成真实张力。它们任务和证据条件不同，所以眼下能合理提出一个待解释的问题，不能把跨论文差异当作已控制的因果发现。[18](https://arxiv.org/html/2607.01661v1) [17](https://arxiv.org/html/2610.24718v1) [5](https://arxiv.org/html/2610.01042v1) [10](https://arxiv.org/html/2510.20963v2)

这条问题与原始动机的联系是，专家可能并非没有表达意见，而是表达中的有效依据没有获得足够辨别力。局部比较已经有 AgentAuditor，训练可检查性已经有 PVG；后续增量可以是一个明确条件下的机制解释、内容选择或表达方式，不应把“按证据而非人数”本身当新算法。[29](https://arxiv.org/html/2602.09341v2) [35](https://arxiv.org/abs/2407.13692v2)

### 9.3 正确贡献已经存在，损失发生在修订还是最后选择？

**问题：在同一份协作轨迹中，少数正确依据被改没、被忽略和最终没被选中，各自造成多大损失，哪些现有方法能修复对应位置？**

SAT 的知识/逻辑 certificate 选择损失、When Debate Helps 的 headroom/损害分解与 Minority Sentinel 的末轮翻票，分别把这件事推进到不同粒度；Free-MAD 和 AgentAuditor 也使用更早或更局部的材料。已有工作很多，研究意义应落在一种尚不清楚的转换条件或可验证的改善，而不是再次报告“池中有正确答案但最后错了”。[25](https://arxiv.org/abs/2609.22682) [28](https://arxiv.org/html/2610.04686v1) [30](https://arxiv.org/html/2606.29270) [20](https://aclanthology.org/2026.findings-acl.1600/) [29](https://arxiv.org/html/2602.09341v2)

该问题贴近原始专家利用目标，也能限制工程范围：先明确损失位置，再考虑是否需要改变成员更新、核查输入或最终提交。这为下一阶段精化问题提供了顺序。

## 10. 回答研究问题，并确定当前阶段的交付

**RQ1：** 专长稀释和有害修订有充分的条件性证据，协作收益也有多条正面证据。不同论文中的专家与参照不同；原始 ML 结果不能全部概括为低于最佳固定个体。识别、披露、采用、修订和读出应分开理解。

**RQ2：** 招募、解释交换、消息筛选、关系学习、组织学习、局部审计与风险控制均有已经实现且得到所测结果支持的方法。Free-MAD/ICR 只是其中一部分；DEAR、EMRC、SAT、AgentAuditor 等必须进入核心比较。既有工作没有解决全部专家问题，并不削弱它们各自已建立的贡献。

**RQ3：** 目前更值得细化的是，成员的可靠优势如何在当前判断上变成适当影响力，以及这一步受消息内容、可检查性和最终选择怎样影响。它有明确近邻和剩余现象，值得继续细化。

当前可用的问题陈述是：**成员已经提供与争议有关的正确依据时，团队为什么仍未利用它；损失取决于可靠性线索、依据可检查性，还是最后的选择？** 它保留用户原始动机，将分散知识和专长互补作为可比较条件，尚不指定解决架构。

下一步先围绕这个陈述讨论和精化两三个具体情形，并以原始论文、EMRC、Influencer、SAT、DEAR、AgentAuditor 的实际操作对照。只有确认需要什么新信息，才选择补读、复现或最小验证。本轮交付是检索综合和候选问题地图。

## 参考文献

[1] Aneesh Pappu, Batu El, Hancheng Cao, et al., "Multi-Agent Teams Hold Experts Back," ICML 2026, 2026. 阅读版本：arXiv v4 (2026-05-28); official metadata verified。

[2] Andrea Wynn, Harsh Satija, Gillian K. Hadfield, "Talk Isn't Always Cheap: Understanding Failure Modes in Multi-Agent Debate," arXiv preprint；作者主页确认ICML 2025 MAS Workshop版本, 2025. 阅读版本：v2, 2025-10-13。

[3] Hyeong Kyu Choi, Xiaojin Zhu, Sharon Li, "Debate or Vote: Which Yields Better Decisions in Multi-Agent Large Language Models?," NeurIPS 2025, 2025. 阅读版本：正式会议记录；机制核读arXiv v2, 2025-10-23。

[4] Hangfan Zhang, Zhiyao Cui, Jianhao Chen, et al., "Stop Overvaluing Multi-Agent Debate—We Must Rethink Evaluation and Embrace Model Heterogeneity," arXiv position paper, 2025. 阅读版本：v3, 2025-06-21。

[5] Shixuan Li, Wei Yang, Peiyu Zhang, et al., "Beyond Final Accuracy: Auditing Communication in LLM Multi-Agent Systems," arXiv preprint, 2026. 阅读版本：v1, 2026-10-01。

[6] Xiqi Hao, Zengqing Wu, Yu-Xuan Qiu, et al., "Not All Flips Are Conformity: Decomposing Stance Convergence in Multi-Agent LLM Debate," arXiv preprint, 2026. 阅读版本：v2, 2026-10-18。

[7] Jiaming Qu, Lucheng Fu, Yibo Hu, "Easier to Mislead Than to Correct: Harmful and Beneficial Revision in LLM Conformity," arXiv preprint, 2026. 阅读版本：v2, 2026-06-06。

[8] Hyeong Kyu Choi, Xiaojin Zhu (ACL metadata: Jerry Zhu), Sharon Li, "When Identity Skews Debate: Anonymization for Bias-Reduced Multi-Agent Reasoning," ACL 2026 Long Papers, 2026. 阅读版本：正式版，2026.acl-long.650，pp.14284–14311。

[9] Yibo Hu, "One Axis, No Brake: Self-Knowledge Limits the Filtering of Harmful Peer Conformity in LLMs," arXiv preprint, 2026. 阅读版本：v1；原HTML显示17 Jul 2026，与ID月份不一致，日期不据此做优先权判断。

[10] Yongqiang Chen, Gang Niu, James Cheng, et al., "When and Why Does Multi-Agent Debate Fail and Does It Really Underperform?," arXiv preprint；全文称初步版在ICML 2026 Failure Modes of Agentic AI Workshop报告，未独立核验正式主会身份, 2026. 阅读版本：v2, 2026-07-14。

[11] Franka Bause, Jonas Niederle, Martin Pawelczyk, et al., "Multi-Agent Systems are Mixtures of Experts: Who Becomes an Influencer?," arXiv preprint (author page lists preprint; ICML keyword is not venue verification), 2026. 阅读版本：2605.25929v2 (2026-06-17)。

[12] Justin Chih-Yao Chen, Swarnadeep Saha, Mohit Bansal, "ReConcile: Round-Table Conference Improves Reasoning via Consensus among Diverse LLMs," ACL 2024, 2024. 阅读版本：arXiv:2309.13007v3 (2024-06-21); formal metadata verified。

[13] Liuxin Bao, Zhihao Peng, Xiaofei Zhou, et al., "Expertise-aware Multi-LLM Recruitment and Collaboration for Medical Decision-Making," arXiv preprint, 2025. 阅读版本：2508.13754v1 (2025-08-19)。

[14] Yuxuan Li, Aoi Naito, Hirokazu Shirado, "Systematic Failures in Collective Reasoning under Distributed Information in Multi-Agent LLMs," ICML 2026, 2026. 阅读版本：arXiv:2505.11556v4 (2026-05-13); venue metadata verified。

[15] Chand Sahil Mansuri, Xin (Vision) Wang, Mengying Li, et al., "Multi-agent discussion gains less when dissent is withheld," arXiv preprint, 2026. 阅读版本：2609.38324v1 (2026-09-29)。

[16] Abhijith Babu, Ramneet Kaur, Vishal Pramanik, et al., "Consilience: Conformally Calibrated Communication Control for Hidden-Profile Multi-Agent Reasoning," arXiv preprint, 2026. 阅读版本：2608.20564v1 (2026-08-20)。

[17] Nima H. Siboni, Magdalena Springer, Vahid Rostami, "Neuro-Inspired Inhibitory Message Passing for Accurate and Token-Efficient Multi-Agent Reasoning," arXiv preprint, 2026. 阅读版本：2610.24718v1 (2026-10-17)。

[18] Yuante Li, Yicheng Tao, Kate Zhang, et al., "Diverse Evidence, Better Forecasts: Multi-Agent Deliberation Under Information Asymmetry," arXiv preprint, 2026. 阅读版本：2607.01661v1 (2026-07-02)。

[19] Bohan Lin, Kuo Yang, Zelin Tan, et al., "AgentAsk: Multi-Agent Systems Need to Ask," ACL 2026, 2026. 阅读版本：formal 2026.acl-long.1294。

[20] Yu Cui, Hang Fu, Haibin Zhang, et al., "Free-MAD: Consensus-Free Multi-Agent Debate," Findings of ACL 2026, 2026. 阅读版本：正式版 2026.findings-acl.1600；另核 arXiv:2509.11035v1 的 G.2。

[21] Binwei Yao, Chao Shang, Wanyu Du, et al., "Peacemaker or Troublemaker: How Sycophancy Shapes Multi-Agent Debate," arXiv预印本；ICLR身份本视角未独立确认, 2025. 阅读版本：2509.23055v1，2025-09-27。

[22] Xiaochen Zhu, Caiqi Zhang, Yizhou Chi, et al., "Demystifying Multi-Agent Debate: The Role of Confidence and Diversity," arXiv预印本；本视角未核实正式venue, 2026. 阅读版本：2601.19921v3，2026-06-03。

[23] Yiliu Sun, Zicheng Zhao, Sheng Wan, et al., "CortexDebate: Debating Sparsely and Equally for Multi-Agent Debate," Findings of ACL 2025, 2025. 阅读版本：2025.findings-acl.495；全文核读arXiv:2507.03928v1。

[24] Hao Wu, Shoucheng Song, Chang Yao, et al., "Group Perspective Matters: Regulating Debate Relationships Can Mitigate Blind Conformity in Multi-Agent Debate," NeurIPS 2026录用，官方Downloads题名与作者校主页交叉确认；阅读arXiv版, 2026. 阅读版本：2608.03648v2，2026-10-21。

[25] Aneesh Pappu, Mirac Suzgun, Yongchan Kwon, et al., "Self-Organizing Agent Teams Learn to Reason Together," arXiv预印本, 2026. 阅读版本：2609.22682v1，2026-09-19。

[26] Priya Pitre, Naren Ramakrishnan, Xuan Wang, "CONSENSAGENT: Towards Efficient and Effective Consensus in Multi-Agent LLM Interactions Through Sycophancy Mitigation," Findings of ACL 2025, 2025. 阅读版本：2025.findings-acl.1141正式版。

[27] Hongduan Tian, Xiao Feng, Ziyuan Zhao, et al., "Multi-Agent Debate with Memory Masking," ICLR 2026, 2026. 阅读版本：arXiv:2603.20215v1；阅读版带Published as ICLR2026标记。

[28] Zihao Zhao, Tunyu Zhang, Haizhou Shi, et al., "When Debate Helps: Proposal Supply and Verification-Aware Readout in Multi-Agent Reasoning," arXiv preprint, 2026. 阅读版本：2610.04686v1 (2026-10-03)。

[29] Wei Yang, Shixuan Li, Heng Ping, et al., "Auditing Multi-Agent LLM Reasoning Trees Outperforms Majority Vote and LLM-as-Judge," arXiv preprint, 2026. 阅读版本：2602.09341v2 (2026-09-03)。

[30] Chuan He, Zebin Chen, Zhengyi Yang, et al., "Minority Sentinel: When to Overturn Majority Voting in Multi-Agent LLM Debates," arXiv预印本；作者实验室确认AgentSearch Workshop/SIGIR2026展示，无archival proceedings, 2026. 阅读版本：2606.29270v1，2026-06-28。

[31] Dongfu Jiang, Xiang Ren, Bill Yuchen Lin, "LLM-Blender: Ensembling Large Language Models with Pairwise Ranking and Generative Fusion," ACL 2023, 2023. 阅读版本：formal 2023.acl-long.792。

[32] Mengdie Flora Wang, Haochen Xie, Guanghui Wang, et al., "From Debate to Decision: Conformal Social Choice for Safe Multi-Agent Deliberation," EMNLP 2026, 2026. 阅读版本：arXiv2604.07667v2; formal metadata/abstract compared。

[33] Nada Rahali, Zijia Wang, Zhi-Song Liu, "Calibration Is Not Verification: Answer-Level Conformal Guarantees for Mixture-of-Agents," arXiv preprint, 2026. 阅读版本：2609.25959v2 (2026-10-25)。

[34] Zachary Kenton, Noah Y. Siegel, János Kramár, et al., "On scalable oversight with weak LLMs judging strong LLMs," arXiv (formal venue not verified this run), 2024. 阅读版本：2407.04622v2。

[35] Jan Hendrik Kirchner, Yining Chen, Harri Edwards, et al., "Prover-Verifier Games improve legibility of LLM outputs," arXiv (formal venue not verified this run), 2024. 阅读版本：2407.13692v2。

