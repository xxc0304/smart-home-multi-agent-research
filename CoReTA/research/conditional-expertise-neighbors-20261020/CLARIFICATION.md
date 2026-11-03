# 条件依赖探测与澄清：直接近邻核对

研究日期：2026-10-20。范围：本文件承担澄清、输入条件变动、知识边界三个检索视角；不处理经典假设推理的完整谱系，不运行实验。采用 deep-research 的先广搜、再按原文方法收窄流程。

## 研究问题与比较对象

RQ1：先改变可能缺失的条件、再观察答案变化，已有工作做到哪里？

RQ2：这些变化产生的是歧义信号、知识边界估计、提问价值，还是可保留并交给其他成员补足的条件关系？

RQ3：若所有成员均可能出错，哪些近邻仍可直接成立，哪些依赖完整上下文、正确答案或其他额外信息？

候选机制固定为：完整作答可能把有效局部知识与未获支持的补全绑定；改变未知条件以发现候选依赖；保留条件关系；请互补但不完美的成员为条件提供支持；最后组合完整解。这里的“有效局部知识”是待检验对象，不能由条件敏感性直接推出。

## 检索过程与筛选

第一轮广搜：`2311.08718 ICE ICML2024`、`2603.26233 Ask or Assume`、`LLM discover knowledge boundary uncertainty assumption dependency clarifying questions partial knowledge`；随后补充 `LLM assumption sensitivity clarification` 与 `LLM counterfactual clarifying questions uncertainty`。

第二轮收窄：沿 ICE 的 uncertainty decomposition、ClarifyGPT 的 code consistency check、KBD 的 entropy-based belief，以及 CIGAsk 的 response ablation / gold-answer likelihood 阅读方法。核验顺序为作者原文 → 会议/出版社记录；搜索摘要用于发现，不作为方法判断的唯一依据。

主比较保留四篇：ICE、ClarifyGPT、Ask or Assume、CIGAsk。KBD 与 semi-open-ended QA 经过核验和方法阅读，但作为知识边界的排除项说明：它们覆盖相关问题背景，却没有覆盖当前候选最关键的条件关系交接操作。StateWise 由主报告另行处理。

## 四篇主近邻：同粒度操作比较

| 工作 | 运行时输入 → 核心动作 → 输出 | 支持/更新依据与额外条件 | 与当前候选的交点与缺口 |
|---|---|---|---|
| **ICE** | 含歧义的输入 → 生成多种澄清、分别采样答案 → 集成分布与不确定性分解 | Eq.3 用输出和澄清的互信息估计输入歧义；预测模型固定；澄清器可用提示或监督微调 | 已覆盖“补入不同条件并看输出变化”；尚未提供跨成员保留、验证和组合局部条件规则的流程 |
| **ClarifyGPT** | 自然语言需求 → 采样程序，在生成输入上执行并按输出聚类 → 比较各类程序，生成针对问题，获答后细化需求并生成代码 | 差异行为被用作需求歧义代理；主方法无监督训练；自动评估中的用户模拟器看到 ground-truth 测试 | 已覆盖“从候选完整解差异反推该问什么”；目标产物是澄清后的需求与程序，未把候选关系作为独立的知识贡献交接 |
| **Ask or Assume** | 不完整 issue 与执行历史 → Intent Agent 每轮判断是否缺信息 → 必要时约束 Main Agent 下一步向用户提问 → 继续修复代码 | 二元检测由提示驱动；检测与执行分工；用户模拟器掌握完整原 issue | 已覆盖独立缺口检测、定向求助与继续求解；信息来源有完整上下文，未研究多个不完美知识提供者相互补条件 |
| **CIGAsk** | 歧义问题、上下文与交互历史 → 策略选择 Think / Clarify / Answer → 终局答案 | 训练时冻结 reference 比较保留/删除用户答复后的 gold-answer 对数似然；另用 gold 歧义标签奖励是否提问；用户模拟器可见潜在意图 | 已覆盖“某个回复是否帮助正确作答”的反事实归因；该信号用于训练，既不是未知条件的运行时发现器，也不是局部规则正确性的检验器 |

方法依据分别见：[ICE §3.4–3.6](https://arxiv.org/html/2311.08718v2#S3.SS4)、[ClarifyGPT 正式稿 §3](https://linshi-website.github.io/paper/ClarifyGPT.pdf)、[Ask or Assume §3](https://arxiv.org/html/2603.26233v3#S3)、[CIGAsk §3.1–3.2](https://arxiv.org/html/2609.24290v1#S3)。表中“未提供”的判断限定于已阅读方法的明确操作。

### ICE：最接近当前“条件探测”的已录用方法

ICE 的式子是 `H(Y|X) = I(Y;C|X) + E_C H(Y|X,C)`。条件 C 可以改变，答案 Y 随之改变，已经是明确的方法核心。§3.6 还提出：某个输入成分的不确定性高时，向用户提供澄清选项。因此不能把它描述成只估计一个置信分数、完全不涉及提问的工作。[原文](https://arxiv.org/html/2311.08718v2#S3.SS4)

但据此只能说模型输出受候选澄清影响。作者也限定：把残余熵解释为 epistemic uncertainty 依赖“输入歧义是唯一 aleatoric 来源”的假设，且与传统定义并不相同。对当前候选的推论是：ICE 能成为依赖发现部件的强近邻；它不能替候选机制证明 `C → R` 中 R 正确，更不能证明 C 已成立。[原文 §3.4](https://arxiv.org/html/2311.08718v2#S3.SS4)

### ClarifyGPT：最接近“用解的差异找应补条件”的流程

它的变动对象首先是候选程序及其可执行行为，不是显式逐一干预同一个未知槽。不同输出的程序被分组，每组选代表交给 LLM，比较其功能以定位需求歧义。自动评估使用正确测试辅助模拟用户，真实用户评估也存在；因此不能把整套方法简化成“必须有测试真值才能检测歧义”。检测所用的是生成输入上的行为一致性。[正式稿 §3、§5.2](https://linshi-website.github.io/paper/ClarifyGPT.pdf)

当前候选若只是比较多种完整解、问差异、把答复写回任务，那么与此操作十分接近。潜在增量必须落在“尚未作答完毕时保留的局部条件关系”和“多个不完美成员如何为其提供支持”上。这个分界是本报告的分析，不是 ClarifyGPT 对自身范围的宣称。

### Ask or Assume：最接近“发现缺口后求助”的代理架构

Intent Agent 看到每轮状态历史，仅输出是否需要澄清；随后主代理被约束为询问用户。论文将 uncertainty-aware 明确解释为行为层面的问询适应，而非形式化概率校准。因此其结果不能直接支持“检测器给出的每个知识缺口都是正确缺口”。[原文 §1、§3](https://arxiv.org/html/2603.26233v3#S3)

它在流程分工上提供直接参照。当前候选若只增加一个“找缺口”的角色，增量不足以据此成立；但完整上下文用户与不完美同伴也不应混同：前者主要补回被隐藏的任务信息，后者还必须处理错误支持、条件循环及互相矛盾的贡献。这些是新候选需要定义的操作责任。

### CIGAsk：必须区分“移除反馈”与“探测未知条件”

它保持问题、上下文和之前历史不变，只消融已收到的用户回复，比较同一冻结 reference 对正确答案的支持变化。奖励是模型相对的 pointwise log-likelihood gain；gold answer 与 gold ambiguity label 都属于训练信息。部署时策略按观察历史行动，未维护显式潜在意图 belief。[原文 Eq.3–4](https://arxiv.org/html/2609.24290v1#S3.SS2)

这使它比泛称“反事实方法”更容易准确比较：它解决已发生提问的信用分配；当前候选拟解决在尚未拿到正确条件时，如何产生可交接的依赖关系。前者可以启发帮助价值的训练目标，但原奖励不能在无答案真值的运行时原样使用。

## 知识边界工作为何相关，却不是这里最强的直接近邻

**Knowledge Boundary Discovery for Large Language Models（KBD）** 的作者是 Ziquan Wang、Zhongqi Lu，已正式发表于 **AAAI 2026**，40(40):33791–33799，不能仅列为预印本。它以主题和历史问答为起点，用 token log-probability 估计熵、构造 within/beyond belief，经 Q-learning 选择后续问题，产出边界附近问集。方法的奖励写为相邻熵的绝对差；尽管正文反复用“entropy reduction”解释，公式本身也奖励上升，不能在转述时悄悄改成只奖励下降。[官方记录](https://ojs.aaai.org/index.php/AAAI/article/view/40670)、[正式 PDF §3](https://ojs.aaai.org/index.php/AAAI/article/view/40670/44631)

它支持“自适应提问可探查知识边界”的相关性；没有把一个任务拆成条件规则、让其他成员补规则前件、再组合解。熵阈值定义和校验的是其边界估计，不构成任一具体条件关系的真实性证书。尤其不能把其“黑箱”直接等同于只需文本接口：原方法观察包含 log-probability。

**Perception of Knowledge Boundary for Large Language Models through Semi-open-ended Question Answering**（Zhihua Wen 等，NeurIPS 2024）明确研究“一个问题可以部分答对”，并借开放辅助模型探索目标模型遗漏的答案，再比较自评与 RAG 评价。它确实反对整题二分的粗粒度设定；但部分对象是列表中各答案项，不是可供其他成员补条件的推理关系。因此不列入四篇主要操作近邻。[正式记录](https://proceedings.neurips.cc/paper_files/paper/2024/hash/a1e0d6fa0c30b7d4f75dd9c7ed6189f2-Abstract-Conference.html)、[原文 §3](https://arxiv.org/html/2405.14383v1#S3)

## 对当前候选的精确判断

**本视角下最强最近邻是 ICE，限定在“对输入条件做变化并观察输出分布”这一核心检测操作上。** 若按“产生差异→定位问题→请求信息→生成完成解”的端到端流程比较，ClarifyGPT 更近；若按双代理分工，Ask or Assume 更近。CIGAsk 约束的是反事实帮助价值的训练，KBD 约束的是边界探查的相关背景。不能跨这些比较轴取一个全局“已做过”的结论。

四个逻辑对象必须分开：

1. **依赖候选**：改变条件会改变输出。这是敏感性观察。
2. **条件规则支持**：在给定前件时，该局部关系成立。这需要对关系本身的支持。
3. **前件支持**：另一个成员有理由支持当前任务中该条件成立。补槽文本本身仍可能错。
4. **组合有效性**：上述关系的变量、范围和前提兼容，且能推出任务要求的结论。

当前候选的潜在增量应陈述为：**发现并保留对任务有用的条件化局部贡献，让不完美成员为其前件提供可审查的支持，再按条件关系组合完整解。** 这仍是方法目标，不能用检索结果当成已完成机制或新颖性证明。其未定义部分至少包括：候选条件从何生成、何种变动算语义有效干预、如何避免条件泄露答案、如何保留在多个条件下成立的共同关系、如何检查提供者的支持、条件循环与冲突如何处理、何时允许组合与终止。

这些定义也决定增量会落在哪里：若最终只把澄清答案写回提示后重新完整作答，现有澄清链条已经非常接近；若能形成被独立保留、由不同成员提供前件支持且可追溯组合的局部关系，则比较对象进入条件推理与协作知识组合，需结合主报告其他视角继续判断。

## 来源核验与实际阅读范围

| 编号 | 核验后引文与状态 | 实际阅读 | 证据边界 |
|---|---|---|---|
| S1 | Bairu Hou, Yujian Liu, Kaizhi Qian, Jacob Andreas, Shiyu Chang, Yang Zhang. **Decomposing Uncertainty for Large Language Models through Input Clarification Ensembling**. ICML 2024, PMLR 235:19023–19042. [会议记录](https://proceedings.mlr.press/v235/hou24b.html)；[v2 全文](https://arxiv.org/html/2311.08718v2) | §3.1–3.6；§4.1；A.2；结论与相关工作扫描 | 已核验正式录用与方法；没有重新核对代码或复现数值 |
| S2 | Fangwen Mu, Lin Shi, Song Wang, Zhuohao Yu, Binquan Zhang, ChenXue Wang, Shichao Liu, Qing Wang. **ClarifyGPT: A Framework for Enhancing LLM-Based Code Generation via Requirements Clarification**. PACMSE 1(FSE), Article 103, 2332–2354, 2024. [DOI](https://doi.org/10.1145/3660810)；[作者正式 PDF](https://linshi-website.github.io/paper/ClarifyGPT.pdf) | 正式稿 §3、§5.2、§7；早期稿用于发现后已改以正式稿为准 | arXiv 旧题名为 *Empowering LLM-based Code Generation with Intention Clarification*；正式稿有五个 benchmark，不能混用旧四项结果 |
| S3 | Nicholas Edwards, Sebastian Schuster. **Ask or Assume? Uncertainty-Aware Clarification-Seeking in Coding Agents**. [v3，2026-09-07](https://arxiv.org/html/2603.26233v3)；作者注明 EMNLP 2026 camera-ready，[作者主页](https://nedwards99.github.io/)注明 Findings 录用 | v3 §1、§3；另读 [v1 附录提示](https://eprints.cs.univie.ac.at/8742/1/2603.26233v1.pdf)，未将其模型设置混入 v3；结果/局限扫描 | 截止检索日未找到可独立确认的 Anthology 正式条目；维也纳机构库仍标 Submitted，与作者录用信息有时间差，保留版本依据 |
| S4 | Yunxiang Li, Xixin Wu, Helen Meng. **When and How Should an Agent Clarify? CIGAsk: Teaching LLMs to Clarify via Counterfactual Information Gain**. [arXiv:2609.24290v1](https://arxiv.org/abs/2609.24290)，2026-09-21；作者备注 Accepted EMNLP 2026 Findings | [全文](https://arxiv.org/html/2609.24290v1) §2、§3；实验设置与局限扫描 | 未独立找到 Anthology 正式条目；录用状态按作者原始声明记载，未写成出版社已出版 |
| B1 | Ziquan Wang, Zhongqi Lu. **Knowledge Boundary Discovery for Large Language Models**. AAAI 2026. [DOI](https://doi.org/10.1609/aaai.v40i40.40670) | arXiv §3、§4；与官方 PDF §3 交叉核对 | 只用于边界探查方法的比较，未替其熵估计添加正确性保证 |
| B2 | Zhihua Wen, Zhiliang Tian, Zexin Jian, Zhen Huang, Pei Ke, Yifu Gao, Minlie Huang, Dongsheng Li. **Perception of Knowledge Boundary for Large Language Models through Semi-open-ended Question Answering**. NeurIPS 2024. [会议记录](https://proceedings.neurips.cc/paper_files/paper/2024/hash/a1e0d6fa0c30b7d4f75dd9c7ed6189f2-Abstract-Conference.html) | arXiv 引言与 §3.1–3.3，评价接口扫描 | 用于确认“部分可答”的已有设定；不将其列表答案扩张成条件推理结论 |

所有保留引文均已通过题名、作者和内容核验。最新录用信息采用上述来源层级，不根据搜索引擎的相对日期推定出版日期。报告没有使用二手自动评论对 manuscript mismatch 的判断；当前直接读取的 Ask or Assume v3 确为编码代理论文。
