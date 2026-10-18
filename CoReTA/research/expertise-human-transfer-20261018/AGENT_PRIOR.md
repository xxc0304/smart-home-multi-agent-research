# 人类专家利用机制的 Agent 先例反查

检索截止：2026-10-18。用途：支持方法选题与近邻比较，不是创新性认证。本稿使用 research-lit 的来源核验思路；未运行实验、未调用付费模型 API、未执行论文代码。网页原文仅定点阅读，下列“已实现”表示论文描述了相应操作，不代表本次独立复现有效性。

## 1. 最需要修正的前提

**“首次把人类专家利用机制迁移到 LLM 多 Agent”不宜成立为宽泛贡献。** 权重、校准、TMS、Delphi、隐藏信息引出、少数正确证据审计、非对称领导和学习协作程序均已有直接先例。更值得比较的是：哪个具体状态触发什么行动，权力如何授予及撤回，局部知识如何转为可验证且能影响决策的证据。

### 原论文 v4 的口径

[Pappu et al., Multi-Agent Teams Hold Experts Back, arXiv:2602.01011v4，2026-05-28](https://arxiv.org/html/2602.01011v4) 已读 §2–5、表2/5、附录A/F/G/J相关内容。原文把人类理论用于区分专长识别与利用，并测试显式揭示专家、GEPA 优化揭示提示、opt-out、debate、独立 CoT+多数票及 full-information 控制。

**表2的6.3%–41.1%是 ENM 相对逐题 ALOC 的缺口，不是固定最强个体的下降比例。** Reveal Expert 在 GPQA、SimpleQA、HLE、MATH 的准确率高于固定 Best Individual，MMLU略低；五项均未达到 ALOC。这里 ALOC 是从讨论前成员答案作理想逐题选择的参照；不能作为允许产生新解的一切协作系统的绝对上界。原作心理任务的已知专家利用不足更直接；其对话行为相关分析仍不等于随机操纵“折中倾向”的因果证据。

### 2026年9月同作者后续改变了结论边界

[Pappu et al., Self-Organizing Agent Teams Learn to Reason Together, arXiv:2609.22682v1，2026-09-19，预印本](https://arxiv.org/html/2609.22682) 与原作共享 Pappu、El、Cao、Zou。SAT 离线从先前协作搜索策略库，冻结后迁移；组织角色、交流阶段、参与及综合，能拼接和修复局部推理。作者报告数学物理集合66.7%，最强成员48.8%，匹配计算量58.7%，初始答案完美路由59.0%。这是作者实验结果，不是本稿复现。

尤其附录D已用 **proof-of-work certificate、逐候选 audit、named_defects、先证据审计再选择**；无缺陷候选之间仍有频率破同分规则。因此“证明随答案传递”“必须指出局部缺陷才能反对”“保护正确少数”均已有很近实现。§5/附录E的 demonstrability 是跨8基准的关联；作者明确将“在同任务内提升 demonstrability 是否导致改进”留作后续，不能写成其已完成的因果干预。

## 2. 两轮检索及阅读透明度

第一轮：原作全文相关段落与点名近邻；关键词 expertise recognition/utilization、ReConcile、CoThinker、HiddenBench、LASE、MARCH、AgentAuditor。

第二轮：机制同义词及反例；检索 equality bias/unequal influence、transactive memory/who knows what、demonstrability/certificate、Delphi/IDEA、calibrated confidence、task-conditioned weighting/model routing、自组织团队2026更新。由此补到 SAT、MATM、Scalable Delphi、ConfMAD、Demystifying MAD，以及固定最强与逐题路由之间的区别。

阅读层级：A=primary正文/方法/相关附录定点读；B=primary摘要及出版元数据；C=primary页面搜索摘要或二手定位，未读全文。下表12篇主近邻均至少B；原作单列，不计入12篇。并非每篇全篇精读，代码均未核。仅搜索摘要命中的其他工作不升级为已验证实现。

## 3. 十二篇主近邻：已做与尚未核实

| 工作、出版/版本、阅读层级 | 已实现的机制 | 尚未确认／不能据此声称首次迁移的原因 |
|---|---|---|
| [ReConcile — Chen et al., ACL 2024](https://aclanthology.org/2024.acl-long.381/)，arXiv 2309.13007；B+方法PDF定位 | 异构模型、多轮说服、置信度加权投票 | 早已打破一人一票；但权重不等于可转移的真实专长估计，也不等于独立证据证明。未核其逐题能力校准保证。 |
| [CoThinker — Shang et al., arXiv:2506.06843v3](https://arxiv.org/html/2506.06843v3)，2026-06-21；A；未核正式录用 | 任务适配思考风格、TMS压缩共享记忆、通信moderator、synthesizer。v2附录D.4明确“who knows what”目录 | 人类认知机制和TMS已被明确迁移。v3更强调上下文压缩；不要把v2强类比写成最新机制实证。目录由贡献总结产生，不自动证明真实能力或可信度校准。 |
| [HiddenBench / Systematic Failures… — Li, Naito & Shirado, arXiv:2505.11556v4](https://arxiv.org/html/2505.11556v4)，2026-05-13；A；[作者仓库声明ICML 2026](https://github.com/Yassellee/HiddenBench_ICML)，本轮未独立核官方proceedings | Hidden Profile；机械Reveal-All、Secretary控制；两轮Exchange再Decide，要求关键事实及反驳当前领先选项 | 新版已超出benchmark。18任务Reveal-All接近full-profile，结构交流也明显改善；因此“强制分享／交换后决策”不能称首次。其主要诊断是未披露信息的探索，不能混为已知专家被忽略。 |
| [LASE — Yoa et al., ICML 2026 / PMLR306](https://proceedings.mlr.press/v306/yoa26a.html)，[2610.16343v1](https://arxiv.org/html/2610.16343v1)，2026-10-12；A | leader先独解；答案token低logprob或高熵触发，按对抗检查→支持→可选专家升级；定向星形信息流、早停 | 非对称领导与按需升级已实现。leader权威来自设计，未等于在线识别当下正确专家；token置信也不是可证明正确。会议出版早于arXiv上传，不能据编号推断10月才出现。 |
| [MARCH — Li et al., ACL 2026](https://aclanthology.org/2026.acl-long.1828/)，[2603.24579v1](https://arxiv.org/html/2603.24579v1)，2026-03-25；A | Solver→命题拆解Proposer→对原答及其提取答案盲态的Checker；MARL优化证据一致性 | 独立复核和阻断确认偏差已有实现。是同一基础policy的分工，非天然异构专家；基于检索文档一致性，不是一般真实性或形式证明保证。 |
| [AgentAuditor — Yang et al., arXiv:2602.09341v1](https://arxiv.org/html/2602.09341v1)，2026-02-10；A；预印本 | 把轨迹构成推理树，在Critical Divergence Points局部审计；ACPO以多数错误案例训练审计者 | 少数正确、局部冲突验证、anti-consensus已覆盖。仍依赖审计模型能力；未证明任意未知专家下识别与利用的统一保证。注意不要与名称相近的安全审计产品混淆。 |
| [SAT — Pappu et al., arXiv:2609.22682v1](https://arxiv.org/html/2609.22682v1)，2026-09-19；A；预印本 | 学习协作策略库、互审修复、组合部分推理、证书及具名缺陷审计 | 原作同作者直接推进；证书/保护少数/自组织都不能再作宽泛首次。demonstrability为关联，未完成同任务内的该机制因果操纵。 |
| [Scalable Delphi — Lorenz & Fritz, arXiv:2602.08889v2](https://arxiv.org/html/2602.08889v2)，2026-10-01；A；预印本 | 独立专家persona估计、匿名汇总反馈、迭代更新与聚合；可对证据及假设重跑 | 已明确迁移完整Delphi。与人类专家接近是支持性参照，人类判断非ground truth；对潜在风险量的验证主要依赖可验证proxy及证据敏感性，非直接证明其真实准确。 |
| [MATM — Kim et al., arXiv:2606.19911v2](https://arxiv.org/html/2606.19911v2)，2026-10-15；A；预印本 | 群体轨迹仓库、按当前状态检索；reranker使用producer/consumer元数据及注入轨迹的边际效用监督 | TMS、可信producer条件化、跨Agent经验复用已有直接实现。其对象是可复用轨迹而非当场对话决策权；不能把shared memory或“按历史有用性查专家”单独称首次。 |
| [Demystifying Multi-Agent Debate — Zhu et al., Findings ACL 2026](https://aclanthology.org/2026.findings-acl.1694/)，[2601.19921](https://arxiv.org/html/2601.19921)；A | 多样初始答案、显式校准置信交流、接收者按他人置信调整；理论/训练修改更新动态 | 已明确从人类审议迁移，且区分表达与真正使用置信。其理论依赖置信与正确性关系等假设；不能外推任意非独立错因及分布迁移。 |
| [ConfMAD — Lin & Hooi, Findings EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.343/)，[2509.14034](https://arxiv.org/html/2509.14034)；A | 独立初答；口头或答案概率置信；Platt/histogram/temperature校准；置信进入讨论及最终选择 | 独立集校准与选择高置信成员已存在。初始轮拟合的校准器能否跨讨论轮及任务迁移需另核，不能把表达强硬等同于证据质量。 |
| [RouteLLM — Ong et al., ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/5503a7c69d48a2f86fc00b3dc09de686-Abstract-Conference.html)；B | 从偏好数据学何时用强/弱模型，优化质量—成本 | 任务条件下选择模型已有成熟先例，但调用前路由和调用后证据加权是不同功能；未因此实现共享信息下的知识互补或协作生成新解。 |

## 4. 人类理论到可观察Agent操作的映射

| 人类机制与primary依据 | 可以迁移的操作 | 已有覆盖与仍应验证的边界 |
|---|---|---|
| recognition ≠ utilization：[Bunderson 2003, Administrative Science Quarterly](https://journals.sagepub.com/doi/10.2307/3556637)，B（publisher摘要）；[Bonner, Baumann & Dalal 2002, OBHDP88:719–736](https://www.sciencedirect.com/science/article/pii/S0749597802000109)，C（publisher搜索摘要，正文打开失败） | 分开记录“谁被判断有能力”与“其有效证据最后是否影响决策”；控制身份标签与真实能力 | 原作本身已区分两阶段。不能把role/persona当真实expertise；Bonner研究有诊断反馈和任务难度边界，不能概括成一切人类团队均能利用已知专家。 |
| demonstrability：[Laughlin & Ellis 1986, JESP22:177–189](https://www.sciencedirect.com/science/article/pii/0022103186900223)，C（publisher摘要）；[Laughlin et al. 2002](https://www.sciencedirect.com/science/article/abs/pii/S0749597802000031)，C（作者后续原研究摘要） | 为决定性主张提供可检查中间步骤；让错误者也能检查；明确前提和反例 | 条件包括共享概念体系、充分信息、错误成员能识别正确解、正确成员有展示能力/时间/动机。SAT及AgentAuditor已做证书/局部检查。LLM“愿意相信”不等于“确实验证”。 |
| equality bias：[Mahmoodi et al. 2015, PNAS112:3835–3840](https://pmc.ncbi.nlm.nih.gov/articles/PMC4378431/)，A | 将参与机会与决策影响分开；依据任务能力/证据而非人数设影响力 | ReConcile/ConfMAD/校准MAD/LASE已打破等权。人类跨文化感知决策结果不能直接解释LLM为追求公平；必须测其更新规则、提示敏感性和错误相关性。 |
| TMS：[Wegner 1987, Theories of Group Behavior](https://link.springer.com/chapter/10.1007/978-1-4612-4634-3_9)，B（publisher章节元数据） | 维护“谁知道什么”、可检索产物、适用范围、可靠度及访问路径 | CoThinker及MATM已明确迁移；“共享摘要”与准确的能力目录并非同一概念。还需区分声明专长、观察到的贡献及验证后的有用性。 |
| 独立征询/Delphi/IDEA：[Hemming et al. 2018, Methods in Ecology and Evolution](https://besjournals.onlinelibrary.wiley.com/doi/full/10.1111/2041-210X.12857)，B+方法片段；[Hanea et al. 2017, IJ Forecasting33:267–279](https://www.sciencedirect.com/science/article/abs/pii/S0169207016300450)，B | 独立初估→讨论解释歧义/交换证据→再次私下估计→数学聚合；不强迫全员同意 | Scalable Delphi已直接覆盖。原作也有独立初答，故只增加“先独立回答”不够。匿名persona不会消除同基础模型的相关错误。 |
| 隐藏信息与探索 | 必须征询尚未披露证据；对领先假设提出可定位反例；确认覆盖后再投票 | HiddenBench新版的Exchange/Decide已覆盖最直接版本。新系统需证明不靠oracle告诉它缺什么，且信息量大时仍有预算效率。 |

### 反证与补充近邻

[The Confident Liar — Keramati et al., ACL 2026 Student Research Workshop](https://aclanthology.org/2026.acl-srw.121/)，B：研究token logprob、judge评分与最终准确性之间的关系。不能把“置信”无条件充作专长或正确性的可迁移标尺；本次未读其完整结果，不给更具体效果结论。

[Adaptive heterogeneous multi-agent debate…，Journal of King Saud University Computer and Information Sciences](https://link.springer.com/article/10.1007/s44443-025-00353-3)，B+publisher方法片段：已描述用讨论结果学习角色权重及在少数专家意见下改变结果。本轮未核全部数据及跨任务权重细节，但足以要求对“学专家权重”的首次主张继续反查。另[The Crowd Without People](https://link.springer.com/article/10.1007/s10726-026-09993-w)，Group Decision and Negotiation 2026，B+方法片段，也有独立评价→facilitator匿名反馈的单轮Delphi实现。

## 5. 权重、路由、权力与证明应分开

1. **调用前路由**：按题目决定请谁；可以省成本，可能错过协作生成新答案。
2. **调用后加权**：看到初答及置信后给成员权重；能保护正确少数，但有校准/相关错误问题。
3. **主张级验证**：核对决定性分歧，权重随具体证据改变；与“这个Agent通常很强”不同。
4. **知识引出**：大家还不知道对方掌握什么；要发问/覆盖检查，不只是加权已出现意见。
5. **决策权管理**：谁能使某个主张进入最终状态、谁能撤回、凭什么证据撤回；与让谁多说话不同。

前三项及第四项的直接版本都有先例。第五项与前三项的组合仍可能值得做，但目前检索不能证明它没有近邻。

## 6. 两个可继续研究的功能草图（均未认证创新）

### 草图A：按主张授予并可撤回的局部决策权

输入先独立提议，系统识别决定性冲突，候选专家提交“主张—证据—适用条件—可推翻条件”。盲态检查者对局部关键断言执行独立检查；通过后授予该主张有限范围的决策权。后来出现可验证反证，撤销该授权并只重开受影响的下游决策。保留每次接受/拒绝的理由与状态依赖。

**预期功能差异**：不只从最终证书中选一个；显式维护可撤回的主张权限与依赖，能力声明不直接带来全局权威。**最近邻必须比较**：SAT证书+具名缺陷、AgentAuditor分歧树、MARCH盲检、LASE领导制。即使最终只是它们的组合，也需要在“正确专家被多数覆盖”和“伪专家/过期专家获得权威”两类压力下证明更好的权衡。

最小可检验假说：固定识别准确率及预算时，验证后有界授权能降低正确少数被覆盖，并在专家局部失误时较固定领导/永久权重更快恢复。把“授权”去掉、替换为普通反馈是必要消融，否则可能只是多做了验证。不要使用测试答案授予权威。

### 草图B：针对未知知识缺口的主动专家征询

以“需要支撑哪些决定性主张”维护开放义务，Agent同时申报“已知事实/未知范围/可取证能力”；控制器区分缺少事实、缺少证明、专家冲突、共同盲点四种状态。按预期减少关键不确定性的收益及成本选择下一次询问/工具取证，并将新证据归因到来源。只有相关义务得到支持或明确保留不确定性后才综合。

**预期功能差异**：核心输出是“下一步向谁问什么/取哪项证据”，不是按题目选强模型或压缩共享记忆。**最近邻必须比较**：HiddenBench Exchange/Decide、CoThinker目录与moderator、MATM边际效用检索、Scalable Delphi重估。信息增益、active questioning、blackboard/argumentation也需单独扩检，不能据本轮称首次。

最小可检验假说：同token/工具预算下，在大信息空间及专家专长随子问题切换时，主动征询较share-all、轮流发言、静态权重和普通router获得更好的关键事实召回及决策准确率。分别测披露、辨别、利用、纠错四阶段，避免只看最终分数而无法说明改进来自何处。

## 7. 对研究定位的建议

可以使用“受人类专长利用启发”作设计动机；贡献应落在具体计算过程、可观察失效条件、可对照的功能收益上。最有价值的研究问题不是预设“让Agent尊重专家”，而是：**何时应接受已验证局部专长，何时应主动寻找未知知识，何时应撤回原有影响力？** 这需要分别比较固定最强成员、计算量匹配单Agent、初始答案完美路由、强证书/审计近邻，而不是只超过多数票。

本稿未完成：代码实现核对、所有会议版本逐句对照、历史全部active elicitation/argumentation/trust-in-MAS文献检索，也未估计任何候选框架效果。上述不足用于约束新颖性判断，不妨碍将两个草图收窄为后续可复现研究。
