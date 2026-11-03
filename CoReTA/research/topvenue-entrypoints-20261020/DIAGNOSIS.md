# 近一年顶会多智能体协作：失败诊断如何形成贡献

检索日：2026-10-20。窗口：2025-10-20 至 2026-10-20，以正式会议届次、录用和出版状态为准；不要求 arXiv 初稿也落在窗口内。本笔记采用 deep-research 的先广后窄检索，负责失败诊断与问题定义分支，供主报告合并。

## 研究问题与检索范围

RQ1：近期正式录用论文把“多智能体不稳定”收窄成了什么可检验瓶颈？RQ2：常见组件或相邻学科概念如何经由新问题定义、控制设计和证据成为贡献？RQ3：这些论文究竟占用了哪一层新颖性，哪些泛化不能从其证据推出？

第一轮围绕 multi-agent failure / failure attribution / collaboration limitations / expertise / communication，搜索 NeurIPS 2025、ICLR 2026、ICML 2026、ACL 2026 的官方记录；第二轮围绕 MAST、expert identification versus leveraging、ALOC、Transformer expressivity、depth–communication trade-off 检索并阅读方法与实验。正式身份优先用 proceedings 核验；博客和论文解读只作定位线索。本文没有运行代码或复现实验。

## 1. Multi-Agent Teams Hold Experts Back — ICML 2026

**正式身份。** Aneesh Pappu、Batu El 等，ICML 2026，PMLR 306:96478–96515。[正式 proceedings](https://proceedings.mlr.press/v306/pappu26a.html)。方法与结果读自[作者最新全文](https://arxiv.org/html/2602.01011)，并与正式摘要核对。阅读深度：§1–5、Table 1–2、相关附录的提示和对话编码说明；未复现。

**真正收窄的问题。** 研究对象是允许自由讨论的异质 LLM 团队。它把知识利用失败拆成两段：不知道谁更懂，以及已经知道后仍不能采用其知识；通过 Expert Not Mentioned / Reveal Expert 对照隔离后一段。组织心理学的 strong synergy 给出了明确评价对象：协作应当保留或超过成员中的最佳表现。

**实际设计与证据。** 受控团队任务中操纵知识分布；五个 ML benchmark 中比较讨论、debate、majority voting、opt-out。增大团队规模和对话行为编码进一步追踪专家意见如何被折中稀释。行为与成绩的相关性支持这种解释，但“alignment 导致过度妥协”仍是作者承认的相关性假说，未做 base / aligned 因果比较。

**数字必须这样读。** Table 2 的 6.3%–41.1% 为 `(ALOC − Team Expert Not Mentioned) / ALOC`；ALOC 是逐题至少一名成员答对的 oracle 聚合上界，区别于最强固定单模型。Reveal Expert 后，GPQA 的团队 83% 高于 Best Individual 78%，SimpleQA 为 60% 对 52%。因此不能把标题扩写成“所有协作配置、所有任务均不及最强单模型”。

**熟悉概念如何形成贡献（本笔记判断）。** 专家角色、群体讨论、synergy 都已有；新增价值来自“专家识别与专家利用”的可分离问题、受控 reveal 操作以及跨设置证据。仅因一个新方案也使用专家或加权机制，就判其与本文实质重复，证据不足。需要比较该方案是否也解决同一个条件下的知识保留问题、改变了什么决定过程、能否解释同一个 gap。

## 2. Why Do Multi-Agent LLM Systems Fail? — NeurIPS 2025 Datasets and Benchmarks Track

**正式身份。** Mert Cemri 等，NeurIPS 2025 Datasets and Benchmarks Track；[正式 proceedings](https://papers.nips.cc/paper_files/paper/2025/hash/b1041e52d3be19f0a9bc491657488e4a-Abstract-Datasets_and_Benchmarks_Track.html) 与[正式 PDF](https://papers.nips.cc/paper_files/paper/2025/file/b1041e52d3be19f0a9bc491657488e4a-Paper-Datasets_and_Benchmarks_Track.pdf)。阅读深度：正文 §1–5、Table 1–2、Appendix H 干预案例与 Table 5；不是把 workshop 引用当作主会录用证明。

**真正瓶颈。** 总成功率无法说明失败发生在哪种系统机制，跨框架的“失败”定义也不统一。其主要介入是测量基础设施：从真实轨迹归纳 MAST 分类，再校准标注器并扩展成可比较的数据集。

**证据。** 150 余条轨迹的深入人工分析形成 14 类、3 大组失败；1642 条标注轨迹覆盖 7 个框架。人工一致性 κ=0.88；few-shot o1 标注器对人工 κ=0.77，在新系统/任务上的验证 κ=0.79。Appendix H 用角色提示和拓扑修改展示分类可指导调试；例如 ChatDev ProgramDev-v0 从 25.0 提升到 34.4 / 40.6，但这是具体案例，不能当成通用算法收益。

**熟悉组件如何形成贡献（本笔记判断）。** Grounded Theory、LLM judge、role prompt、cyclic workflow 都不是新原语；贡献在经验归纳的操作定义、标注可靠性和跨系统诊断资产。本文覆盖“存在 information withholding、verification 等现象”的证据，却不等于覆盖所有针对这些现象的检测、定位和纠正方法。

**边界。** 失败类型出现与最终失败之间未必是唯一根因关系；数据与评审模型存在覆盖限制，作者也不声称分类穷尽。若新方案的贡献只是重新命名这些类别，重叠直接；若提出可识别的传播机制或有反事实验证的干预单元，应比较机制和证据后再判断。

## 3. Benefits and Limitations of Communication in Multi-Agent Reasoning — ICLR 2026

**正式身份。** Michael Rizvi-Martel 等，ICLR 2026；[正式 proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/e9372abc370b8302459abdce4bdce5a5-Abstract-Conference.html)、[正式 PDF](https://proceedings.iclr.cc/paper_files/paper/2026/file/e9372abc370b8302459abdce4bdce5a5-Paper-Conference.pdf)。其 arXiv 初稿为 2025-10-14，但正式 ICLR 2026 在本窗口内。阅读深度：§1–6、主要命题与 Table 1、Appendix F 实验、G 多 token 扩展；没有逐项审核全部数学证明。

**真正瓶颈。** “多通信能否加速”缺少把 agent 能力、总计算量、并行深度和消息量区分开的分析。论文用 UHAT Transformer 表达 agent，以带 CoT / communication 边的 DAG 表达协作，输入分块给各 agent。

**实际贡献与证据。** 它构造并比较三个任务族的可行协议和下界：recall 的深度及通信可为常数；state tracking 可用 parallel scan 获得 `O(N/w + log w)` 深度但需 `Θ(w)` 通信；k-hop 的跨块依赖使通信随 hop 增长，最坏情况难靠加 agent 消除串行深度。Llama 70B/8B 的受控合成任务检验协议趋势。这里的贡献是资源边界和任务依赖结构，不能概括为一条“通信越少越好”的经验规则。

**熟悉组件如何形成贡献（本笔记判断）。** DAG、parallel prefix sum、迭代查询和复杂度分析都是成熟工具；新价值来自用 Transformer 表达能力建立对 LLM 有区分力的模型，使三个表面相近任务落入不同资源区间。因此“用了图”“用了树形聚合”本身不能证明与本文实质重复；复现其相同模型、相同资源定义和同类界限才构成更直接重叠。

**边界。** 结论受分块输入、UHAT 表达模型与任务族约束，depth 是墙钟时间代理，不是部署延迟保证；也未证明对话中的信念冲突、可信度判断或修复策略受到同一套界限完全刻画。

## 交叉比较与创新判断

| 论文 | 已占据的具体贡献 | 不能据此直接否定的内容 |
|---|---|---|
| Experts Back | 揭示专家身份后仍可能丢失知识收益，测量识别/利用差距 | 一切 role / expertise / reliability weighting |
| MAST | 经验失败分类、可靠标注流程、跨框架轨迹资产 | 分类中每种失败的新定位机制、新干预和可验证修复 |
| Communication | Transformer 多 agent 的任务相关资源界与协议 | 一切图结构、节省 token、选择性通信或动态协作 |

三篇文章分别研究**意见进入决策时的知识损失、失败观察的可比较性、任务结构导致的资源约束**。它们共享“协作可能失败”的背景，但被解释的变量和实验操作不同；不能以背景相同把它们合并成同一个问题。

对新方案，更有区分力的核对顺序是：①失败现象及成立条件是否同一；②被操纵的因果或控制单元是否同一；③运行时可用信息是否同一；④与最近方案相比改变的机制是什么；⑤证据是否能排除增加计算、换强模型等替代解释。只有关键词或公共组件相同，属于需要引用和比较的联系；若问题、信息条件、决策机制和验证结论都近似，才形成更强的实质重叠判断。

据此，近期正式录用论文能支持的选题启发是：**可隔离的新失败条件、与瓶颈对应的设计、能区分替代解释的证据，可以共同构成贡献，即便组件本身熟悉。** 这不意味着任意拼装都能发表；也不能只凭“并非每个组件都新”就把方案判死。

## 范围说明

这是主报告的诊断分支，集中精读三篇；不是完整文献综述，也未声称穷尽近一年 MAS 新问题。OpenReview forum 曾触发访问挑战，因此最终使用可直接访问的官方 proceedings 核验身份。所有数值来自论文所报告实验，本文未独立复现；不同模型、任务与计算条件之间不作数值排名。
