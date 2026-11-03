# 条件知识组合：CoReTA 的近邻与尚未解决的提取问题

日期：2026-10-20。范围：四个核心机制近邻，另将指定的 2601.15077 作为近期边界对照；没有运行模型、实验或代码。

## 研究问题与检索范围

本报告研究的对象是：成员被要求回答整题时，可能把有效的局部推理与未被支持的猜测混在一起；团队需要保留可成立的条件关系，识别未满足依赖，让其他同样不完美的成员补足这些条件，最终构造无人事先掌握的新解。

- RQ1：条件关系的保留、对外求助和跨成员补条件，有哪些直接算法先例？
- RQ2：已有保证建立在什么输入和推理能力上，是否包括从错误的自然语言整解中抽取有效条件关系？
- RQ3：CoReTA 还能提出什么可辨识的研究贡献？

采用 `deep-research` 方法，两个检索轮次后补查父任务发现的近邻。第一轮分别检索 `DAREC abductive reasoning agents`、`Multi-agent Confidential Abductive Reasoning ICLP 2011`、`assumption based truth maintenance system de Kleer 1986`、`Multi-Agent Constraint Factorization 2601.15077`。第二轮定位 DAREC2 的原始状态转移与协调协议、ATMS 的 PROPAGATE/WEAVE/NOGOOD、Cobleigh 等人的 L* assumption learning 与双 oracle；并检索近期算子论文的完整理论和限制。补查 `Cooperative dialogues with conditional arguments` 后读官方全文，发现其比一般性的协作论述更接近当前目标。只用论文原文、作者站点、会议或 NASA 官方资料支持技术判断；搜索摘要用于定位，不代替算法阅读。

## 四个核心近邻的机制比较

| 核心近邻 | 输入与表示 | 条件/假设从哪里来 | 成员间如何补足 | 更新、冲突与保证 | 已覆盖与尚未覆盖 |
|---|---|---|---|---|---|
| Sá & Alcântara, **Cooperative Dialogues with Conditional Arguments**, AAMAS 2012 | 各成员已有 abductive logic program；条件论证 `(E,F,Hyp,G)` | 在允许假设集合内，用 extended abduction 求添加 E、撤去 F 后支持 G 的解释 | 同伴证明待补条件 L，用其论证替换 L；新条件可继续留给后续成员 | attack、constraint attack、rewrite；群体接受需 E 为空并满足论证接受规则；有限语言与对话限制支持结束，接受集与 stable extension 相联系 | **最强概念邻居**：已有跨成员补条件、递归组合、群体可推而个人不可推。未处理原始 LLM 整解中真推理与猜测混杂的抽取。[原文 §3–4](https://www.ifaamas.org/Proceedings/aamas2012/papers/4C_2.pdf) |
| Ma 等，**Multi-agent Confidential Abductive Reasoning / DAREC2**, ICLP 2011 | 分布 normal logic programs、预定义 abducibles、integrity constraints、askables | 本地目标驱动溯因生成假设与未解子目标，算术/否定生成约束 | transitional state 携带局部答案和剩余目标，按 helpfulness 路由；待检假设另带 agent tags | CLP、一致性检查与同步回溯；三值 completion 语义下 soundness；completeness 需有限全局推导树 | **最强直接算法邻居**：局部做尽、暴露缺口、找能接续者、检查全局约束。输入规则与推理步骤已形式化，未解决自然语言规则真实性。[原文 §4](https://drops.dagstuhl.de/storage/00lipics/lipics-vol011-iclp2011/LIPIcs.ICLP.2011.175/LIPIcs.ICLP.2011.175.pdf) |
| de Kleer，**ATMS**，1986；算法阅读用 1988 修订原文 | 节点、assumptions、Horn justifications；label 是支持结论的最小条件集合族 | inference engine 指定假设并提交推导；ATMS 维护依赖 | 本体没有选同伴或请求协议；可作为协作状态的条件账本 | 合并前提 labels、删被包含环境；矛盾环境及其超集成为 nogoods 并从 labels 排除；保证相对于给定规则的 sound、consistent、complete、minimal labels | 已覆盖保留条件结论、替代支持与冲突传播。它需要上游产生可信规则，不能凭账本识别幻觉。[原始条目](https://www.sciencedirect.com/science/article/abs/pii/0004370286900809)，[可读算法 §2–3](https://dekleer.org/Publications/Corrected%20AAAI88.pdf) |
| Cobleigh、Giannakopoulou、Păsăreanu，**Learning Assumptions for Compositional Verification**, TACAS 2003 | 有限状态组件 M1、M2，安全性质 P，环境假设自动机 A | L* 向 model-checking teacher 查询，学习让 M1 保证 P 所需的环境行为 | 检查 `A ⊢ M1:P`，再让环境 M2 discharge A；这是组件契约，非 LLM 对话 | 前者失败则加强 A；后者失败须判断真实反例或 A 过强，再削弱；在论文有限状态设定下正确且终止 | 已覆盖**自动发现和反例精化条件**，所以“以往全靠人工给前提”不成立。其可靠 teacher 来自可枚举模型，而 CoReTA 的候选规则与成员回答也可能错。[NASA 原稿 §3–5](https://ntrs.nasa.gov/api/citations/20030017771/downloads/20030017771.pdf) |

这些保证都不是现实世界真值保证：形式系统对提供给它的程序、规则、模型和语义负责；错误的输入建模不因推导有效而变正确。

## 关键原始算法核对

**2012 条件论证比一般“互相批评”更近。** Definition 7 的 rewrite 明确把同伴证明 L 的支持接入原论证，待补条件更新为 `(E1 − {L}) ∪ E2`。Example 6 是三成员递次补 `b,d`，最终得到个人无法独立推导的群体论证；这直接覆盖“没有任何成员预先答对，但能联合补全”的概念。其 §4 假设成员诚实、共享本体与通信语言；接受和对话终止是协议内性质，不证明不完美 LLM 能提出真实规则。[官方全文](https://www.ifaamas.org/Proceedings/aamas2012/papers/4C_2.pdf)

**DAREC2 不是只传问题的空壳。** §4.1 状态包含 remaining goals、hypotheses、constraints、denials 和待检查 tags；§4.2 在本地无法继续时传状态，helpfulness 统计候选成员能接手的 askables、denials 和假设检查。失败进入回溯，收束还要求无残余目标、无待检 tags。算法可以留下全局 abductive hypotheses：它们的一致性已检查，并不等于这些假设被证明为真实事实。[官方全文](https://drops.dagstuhl.de/storage/00lipics/lipics-vol011-iclp2011/LIPIcs.ICLP.2011.175/LIPIcs.ICLP.2011.175.pdf)

**ATMS 的关键是多种支持环境，而非单一置信分。** 1988 算法 §3 的 WEAVE 对前提环境取并集，UPDATE 保持最小支持，NOGOOD 清除冲突集合及超集。这样某条路径失效时，结论仍可能保留另一条支持；这是一种适合借鉴的状态语义。[算法原文](https://dekleer.org/Publications/Corrected%20AAAI88.pdf)

**assume-guarantee 提醒我们不能把“前提学习”留作笼统新颖性。** 原稿 §4.2 的两个 oracle 分开问：假设是否足以使组件满足性质，以及环境是否真能满足该假设；第二步失败还要辨别假设过强与系统真的出错。因此“寻找缺口”与“检查补足者”本来就可以交替驱动前提修订。[算法原稿](https://ntrs.nasa.gov/api/citations/20030017771/downloads/20030017771.pdf)

## 指定近期对照：Multi-Agent Constraint Factorization，2601.15077

Scofield 的 2026 预印本把成员表示为约束集 Ai 上的算子 Ti，共享状态按算子顺序组合更新；投影结论要求闭凸约束集和非空交集，近端版本另要求特定凸函数与步长。它与 CoReTA 共享“局部能力经组合产生更强整体”的解释，但没有给出从混合真假输出中提取条件、发现缺口和定向询问的操作算法；§8 的文本对应是抽象映射，§9 明确限制有限时间与真实噪声更新的保证。[原文 §3–9](https://arxiv.org/html/2601.15077v1)

阅读时还发现 §7.3 的固定步长示例需要核对：按 §7.2 公式取 λ=1，令三次更新依次作用于 `(2/3,2/3)`，手算结果是 `(11/18,11/18)`，与其声称该点为循环固定点不一致。这是原文公式的代入核对，未跑代码；本报告的近邻判断不依赖此问题。即使完全接受其理想定理，也不能直接移植为 LLM 正确性保证。[原文 §7](https://arxiv.org/html/2601.15077v1#S7)

## 对 CoReTA 的结论与可研究剩余问题

RQ1 的答案相当明确：条件保留、递归补前提、定向接续和群体构造新解均有先例。2012 条件论证最直接覆盖研究概念，DAREC2 提供最完整的分布式执行近邻。ATMS 提供依赖和冲突账本，assume-guarantee 提供自动条件发现与反例修订的成熟视角。它们应成为方法设计资源和相关工作，年代本身不构成否定 NLP 新方法的理由。

RQ2 的边界是**条件关系的可靠获得**。当前设想的输入是被整解任务诱发的混合文本，某一步可能来自知识，也可能是在填补不知道的部分。把“我猜 u，所以 v”机械转换成 `u ⇒ v` 并不能自动保住有效知识：错误也可能发生在蕴含关系、适用域、量词、变量对应或隐含条件上。上述原文均未建立对此类 LLM 输出的可靠提取保证；这一结论限于本报告实际阅读的作品，不能扩写成全领域无人做过。

RQ3 因而应围绕下列可区分的机制命题展开，而不把共享状态或条件组合本身作为首创：

1. **有效片段抽取**：从完整但错误的回答里恢复哪些局部关系，以及它们的真实条件；允许“关系本身尚待核对”，不能把它和“前提尚未知”混为一类。
2. **条件转请求**：把影响目标的未满足依赖转为可回答的局部问题；同伴可以返回条件答案，继续引入依赖，直到支持闭合或显式保留未知。
3. **保留多种支持与修订传播**：一个补充被反驳时，沿依赖边撤回其后果；保留不依赖该补充的替代路线。证明 A 不能仅靠一个又依赖 A 的未落地条件循环。
4. **证明是组合起作用**：分别检查最终正确、所用局部关系正确、条件真实满足，以及答案对这些材料的因果依赖。应区分新解的组合与最终成员额外独立重解；这是未来评价要求，本轮没有进行实验。

该剩余问题足以支持继续精化 NLP 方法，但目前只是从邻居边界推导出的研究定位，尚不是已证实的有效性或新颖性结论。

## 来源、核验与阅读范围

| 来源 | 状态 | 实际阅读范围与限制 |
|---|---|---|
| [Sá & Alcântara 2012，官方会议 PDF](https://www.ifaamas.org/Proceedings/aamas2012/papers/4C_2.pdf) | VERIFIED，全文可达 | §3 conditional argument / rewrite / constraint attack；§4 接受、群体对话、有限性与个体策略；重点 Definitions 5、7、9，Example 6，Theorems 1–2。非仅摘要。 |
| [Ma 等 ICLP 2011，正式条目](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ICLP.2011.175)，[12 页 PDF](https://drops.dagstuhl.de/storage/00lipics/lipics-vol011-iclp2011/LIPIcs.ICLP.2011.175/LIPIcs.ICLP.2011.175.pdf) | VERIFIED，全文可达 | §3 表示；§4.1 本地规则、§4.2 路由/回溯、Theorems 5–6 与实现。隐私性质未做独立证明审计。 |
| [DAREC AAMAS 2010 官方 extended abstract](https://www.ifaamas.org/Proceedings/aamas2010/pdf/02%20Extended%20Abstracts/Red/R-07.pdf) | VERIFIED，2 页可达 | 用于核对前身名称和年份；与 DALT 同题长文区分，长文未全文阅读。本报告详细算法归于 2011 DAREC2。 |
| [de Kleer 1986 原始期刊条目](https://www.sciencedirect.com/science/article/abs/pii/0004370286900809)，[作者书目](https://dekleer.org/bib.htm) | VERIFIED；1986 PDF 未成功提取 | 核对题名、作者、卷页、DOI `10.1016/0004-3702(86)90080-9`。没有声称读完 1986 全文。 |
| [de Kleer 1988 修订算法 PDF](https://dekleer.org/Publications/Corrected%20AAAI88.pdf) | VERIFIED，作者原文可达 | §2–3 基础表示与 PROPAGATE/UPDATE/WEAVE/NOGOOD；扩展算法只作背景，未独立证明审计。 |
| [Reiter & de Kleer 1987 foundations](https://dekleer.org/Publications/Foundations%20of%20Assumption-Based%20Truth%20Maintenance%20Systems.pdf)，[de Kleer 1993 回顾](https://dekleer.org/Publications/A%20Perspective%20on%20Assumption-based%20truth%20maintenance.pdf) | VERIFIED，作者原文可达 | 前者部分形式基础与支持集合，后者 §1–2 条件追踪起源；辅助确认，未增加核心近邻数量。 |
| [TACAS 2003 DOI](https://doi.org/10.1007/3-540-36577-X_24)，[NASA 原稿元数据](https://ntrs.nasa.gov/citations/20030017771)，[原稿 PDF](https://ntrs.nasa.gov/api/citations/20030017771/downloads/20030017771.pdf) | VERIFIED，版本需区分 | 读 NASA 原稿 §3–5：规则、L*、teacher、oracle、correctness/termination。NASA 元数据列 2002 技报并多列 Clancy；不把其元数据作者表直接套到 TACAS 2003。 |
| [Scofield 2026 arXiv](https://arxiv.org/abs/2601.15077)，[v1 全文](https://arxiv.org/html/2601.15077v1) | VERIFIED，预印本全文可达 | §3–9，含投影与近端假设、文本映射和限制；未检索到本文实证验证，未把理论类比写成 LLM 实测结论。 |

局限：本报告是父任务中“组合机制近邻”的定向子报告，并非完整 LLM 协作文献综述。已完成两轮原始来源检索和关键算法阅读；没有用形式先例的存在替代对 NLP 提取算法、经验增益或最终新颖性的评估。
