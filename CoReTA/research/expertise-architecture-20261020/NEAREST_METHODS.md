# CoReTA 最近方法与反证检索

日期：2026-10-20。独立检索两轮；仅写研究笔记，未改实现、未运行实验。采用 research-lit 检索框架。下述“未见”是所读原文中的未见，不是全领域不存在性结论。

## 结论

三同模型的构建/整合/检查，加上 claim 账本，不能构成足够清晰的新机制。最危险的近邻是 SAT，而不只是传统 debate：SAT 已有证书、局部缺陷审计、少数有效依据保护、丢失个体信息恢复。进一步改成“把分歧变成可区分的低难度查询”也不能直接宣称新：VideoHV-Agent 已明确设计区分候选的最小观测，再定向获取证据。

目前尚值得区分的操作对象应是**一条依据在特定子问题上的影响权限**：为什么允许它写入当前解，怎样通过可判定观测获得权限，何时只能局部使用，以及反证后撤销哪些依赖。这里每一点都需要与下列近邻做机制对照；把已有部件装到一起不自动产生创新。

## 第一轮：指定论文与架构邻居

| 原论文 / 阅读范围 | 改变的操作对象、信息与控制 | 对 CoReTA 的反证 |
|---|---|---|
| [Multi-Agent Teams Hold Experts Back, v4](https://arxiv.org/html/2602.01011v4)，全文 | 控制专家信息是否集中/分散、是否揭示专家、团队规模与讨论条件；分析折中与服从。主要是诊断研究。 | 已直接提出专家利用失败及其与抗操纵性的张力。不能把“专家被稀释”本身当方法贡献；揭示专家也不等于可信使用专家。 |
| [SAT, v1](https://arxiv.org/html/2609.22682v1)，§2、附录 A/D | 将组织编码为可变策略语言：角色、参与者、轮数、信息流、综合方式。离线反思搜索并冻结策略库，测试时生成带证书候选，再由 judge 审局部缺陷并选择。 | 已覆盖先独立、挑战修复、逐主张保留、最终审计恢复个体信息；“certificate + checker + minority preservation”重复风险极高。 |
| [ReConcile, ACL 2024](https://aclanthology.org/2024.acl-long.381.pdf)，全文方法/算法 | 改变同伴接收的信息：答案分组、解释、置信度、能纠正其他模型的示例；以重标定置信度加权投票。 | 有异构/领域模型与说服性知识传递。“提高专家权重+解释依据”已不足；其权重仍不是外部检验授予的局部权限。 |
| [DMAD, ICLR 2025](https://openreview.net/forum?id=t6QHYUOQL7)，原论文检索摘要边界 | 不同 agent 使用不同推理方法以打破 mental set，改变候选推理空间。 | “角色不同/路线互补”已有。OpenReview PDF 被验证页阻断，ICLR PDF读取失败；此处不声称核实其具体聚合、证书或控制实现。 |
| [AgentAsk](https://arxiv.org/html/2510.07593)，§4、附录 A/F | 将干预对象降到消息交接边；控制器决定是否问、问谁、问什么最小澄清；SFT/RL学习预算内策略，原编排保持固定。 | “缺什么问什么+定向补充反馈+防错误传播”已被明确方法化。新增问答若没有区别于边澄清的准入规则，很像其轻量实例。 |
| [CoThinker](https://arxiv.org/html/2506.06843)，§4 | 动态思维风格分工、共享 transactive memory、通信 moderator 限制同伴输入并选择连接，最终 synthesizer。 | “共享账本+压缩上下文+局部互补信息流”已有。其优化核心是认知负载/信息路由，不等价于事实正确性担保。 |
| [LASE](https://arxiv.org/html/2610.16343v1)，§3 | 领导者先独立尝试，置信代理触发单个同伴的对抗检查、支持、专家升级；有向星形交互。 | 非对称主线保护、按需局部交流、低成本升级都已有。其纠错增益依赖种子/放大等条件，不能把拓扑变化视为自动保证。 |

### SAT 的最接近处与准确边界

附录 A.2 的 `constructive_challenge_and_preservation`、`final_auditor_claim_recovery`、`minority_evidence_adjudication`，以及逐选项写成立条件、由其他成员给证据并批判，直接压缩了 CoReTA 的创新空间。§2.2 的 certificate 是可逐步检查的短推理，不是机器证明。训练 validation probes 检验策略跨题迁移，不是测试时主动区分当前候选。原文明示没有 test-time controller。未见双边锁定预测、外部观测驱动的硬准入或按依赖撤销；这些是待比较的具体区别。

## 第二轮：针对“独立验证/证书/补充反馈/区分性测试”的强反证

| 原论文 / 阅读范围 | 已实现的关键操作 | 必须避免的虚假新颖性 |
|---|---|---|
| [When Helping Hurts and How to Fix It: Multi-Agent Debate for Data Cleaning](https://arxiv.org/html/2606.02866)，方法与 factorial 分析 | Generator–Critic 分离；Critic可执行 Python/pandas 查询实际数据；evidence-gated Generator 只接受引用具体数据证据的反馈。比较自验证与独立 critic。 | “独立工具验证+有证据才修改”已经出现，并有组件交互分析。仅换成claim账本不够。 |
| [VideoHV-Agent / Think, Then Verify, CVPR 2026](https://arxiv.org/html/2603.04977)，§3.2–3.3、算法1；[会议原页](https://openaccess.thecvf.com/content/CVPR2026/html/Wang_Think_Then_Verify_A_Hypothesis-Verification_Multi-Agent_Framework_for_Long_Video_CVPR_2026_paper.html) | 各候选转可测试假设，Judge产生区分它们的最小观测clue；Verifier定位视频、细粒度取证并给状态；不充分则补取证或重写假设/clue。 | “将候选分歧变成区分性查询”本身高度重叠。尚未见独立专长持有者预承诺预测，以及测得结果授予可迁移的局部权限。 |
| [POPPER, ICML 2025](https://www-cs.stanford.edu/people/jure/pubs/auto-hypothesis-validation-icml25.pdf)，§2–4 | 主假设导出可测蕴含；实验设计 agent预先给零/备择假设，经相关性检查，再由执行agent取数据和统计检验；顺序证据累积控制错误。设计者只看元数据，限制数据窥探。 | “先约定可反驳预测再取证”已有。CoReTA若使用预承诺，需说明其解决团队局部信息接入的不同问题。 |
| [When Debate Helps: Proposal Supply and Verification-Aware Readout](https://arxiv.org/html/2610.04686v1)，§3、附录 A.9 | 将提案覆盖与最终读出区分；LVD给候选特异验证证据建模，固定候选做正确/错误理由干预。 | “验证证据优于票数”已有理论/实证视角。CoReTA须隔离改变候选集和改变证据准入的效应。 |
| [Conformal Social Choice](https://arxiv.org/html/2604.07667)，摘要与方法 | 对代理概率线性汇总后做split conformal，预测集决定自主行动或升级。 | 有校准决策层并不等于推理改善。若CoReTA允许拒答/回退，需要在同coverage下比较风险，不能靠少答证明正确率改善。 |
| [TAIR](https://experts.illinois.edu/en/publications/towards-trustworthy-ai-results-using-evidence-structures-from-cer/)，作者机构页面摘要 | (Q,A,E)证据携带结果，独立验证、缺口检测与反馈修复；证据可为证书或论证结构。 | 泛称“从信任agent转向验证证据”不是新概念。仅摘要核验，不推断其具体控制器实现。 |

## 三个候选机制：最强重复风险与未决区别

### 第二轮补充：进一步压缩创新空间的两个近邻

**[Consilience](https://arxiv.org/html/2608.20564)，全文 §3。** 在 hidden-profile 私有信息团队中，以不确定性、分歧、证据增益等状态选 challenge/clarify/seek-evidence/route，并选发言者。各动作从冻结前状态独立反事实 rollout，只提交接受分支。规则/LLM版本无需模型训练，MLP版需rollout训练，全部校准版需要离线逐轮校准数据。保证针对代理讨论损失的一步 regret，并非答案正确。它直接覆盖“主动补证据+受控局部通信+拒绝不合格动作”，甚至状态分叉与提交也不是空白。

**[Calibration Is Not Verification / C-MoA与CONTRA-MoA](https://arxiv.org/html/2609.25959)，全文方法/讨论。** 原子claim以NLI同伴支持打分并校准保留/丢弃；辅助路径生成互斥near-miss，盲排比较，再加leave-one-agent-out与可用性标志融合。无需所述骨干微调，但有校准集和冻结评分程序。记忆型弱验证器可能伤害有效主信号；“有能力才开辅助门控”在讨论中已明确提出，尚不是被验证的新强方案。它直接覆盖claim局部路由、可证伪对比、无测量不能当阴性、验证器专长边界。由同伴沉默误伤专家真依据也已明确分析。

因此下列A的相对优先仅是研究选择，**不能解读为已找到新颖机制**；B/C的概念空白进一步收缩。若A只是内部judge做near-miss评分再门控，很接近CONTRA-MoA；若只是选seek-evidence再commit分支，很接近Consilience。尚待区分的是双方预承诺与外部新观测是否改变了可判定性，以及结果到局部权限的受限映射。

### 候选 A：双边预承诺的区分性测试，结果授予局部依据准入

操作：冲突双方先对同一个低成本、可判定查询提交不同预测及其与主张的蕴含；观察结果前冻结。执行者取结果，控制器按预登记规则只接入通过的子主张，保留不冲突的其他贡献。

最强重复：VideoHV-Agent 已有区分性观测；POPPER已有先设计检验再执行；Data Cleaning已有执行证据门控；AgentAsk已有局部边干预。**当前只能说组合中的专长接入问题可能尚有区别，不能说概念新。**

未决：双方是否确实对测试结果有不同预测？测试正确是否足以支持上层结论？独立执行结果如何可靠读取？没有可测区分时会不会退化为LLM审稿？控制器如何避免“预测一个简单事实就取得整篇答案权威”？这些是机制定义，不是后加消融。

### 候选 B：依据依赖图上的隔离、准入与撤销

操作：每条依据携带来源、范围、检查状态；修改只对显式依赖生效；反证一个节点就撤销其后继，以未受损子图保留局部互补。

最强重复：SAT已有claim恢复，CoThinker已有共享记忆，TAIR已有证据结构与缺口修复。若图只是日志而最终writer可自由覆盖，贡献接近记录格式。未决区别是**可执行的依赖与写入约束**：能否让错误不能进入受保护状态，且用外部结果实际触发选择性回滚，而不是提示模型自觉遵守。

### 候选 C：学习“何时接入哪类局部依据”的最小策略

操作：用离线干预结果学习范围敏感的接入规则；状态包含证据类型、可验证度、冲突局部性，动作是保留/询问/测试/接入/拒绝；优化净纠错和成本。

最强重复：SAT学习组织，AgentAsk学习边澄清，LASE按置信门控。仅训练一个router无新意。未决区别是训练目标是否直接惩罚“正确主线被错误局部反馈推翻”和“专家局部真理越权扩散”，且独立于agent身份。可先用冻结规则实现机制；训练仅在数据证明规则存在跨域差异后再考虑。

## 给主项目的优先判断

优先 A，但必须把“可区分测试”进一步收窄到**预承诺蕴含、外部判定、范围受限接入**，并承认与 VideoHV-Agent、POPPER、工具证据门控的组合关系。B可作为A执行所需的最小状态机，不宜单独包装为创新。C训练成本更大，且近邻更密集。

研究贡献需要回答：在专家身份已知、但专家不完美且局部知识互补时，协议怎样同时降低错误主张接入率和正确主张丢弃率？不能只报团队平均准确率。至少需区分初始正确被毁、初始错误被救、局部互补新解、纯选择收益，并保持候选集合/调用预算可比。这里是未来验证建议，本次没有执行实验。

## 检索轨迹与边界

第一轮检索固定论文名/ID，读取原版HTML/PDF，抽取操作对象。第二轮用相反假设搜索：独立critic、evidence-gated、discriminative clue、falsification、candidate verification、edge clarification。只有原论文/会议页/作者机构页面用于结论；搜索引擎的第三方摘要仅用于发现入口。

已至少九篇读到原论文方法，DMAD明确停留在原论文索引摘要边界，TAIR明确为作者机构摘要。以上不是穷尽查新：尤其专用程序验证、主动信息获取和多假设实验设计仍可能有更强前置工作，当前不得对候选A/B/C宣布首创。
