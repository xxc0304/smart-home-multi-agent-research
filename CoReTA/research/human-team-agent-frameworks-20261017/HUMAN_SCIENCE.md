# 人类团队科学：可迁移机制、条件与失效

检索日期：2026-10-17。范围依照同目录 BRIEF.md，主要回答 RQ1，为 RQ2–RQ3 提供机制约束。这里只整理人类研究，不判断某一 LLM 框架是否新颖，也不把迁移设想当作已验证方法。全程使用免费网页检索，未调用付费 API、未开展实验。

## 1. 机制综合

最值得借鉴的不是“模拟一家有领导和专家的公司”，而是组织如何处理**依赖、知识位置、证据分布、例外事件和经验更新**。五簇机制对应不同干预对象，不能用增加一轮对话相互替代。

| 机制簇 | 人类研究支持的核心关系 | 条件、失效或反证 | 对 Agent 的可操作迁移设想（本报告推论） |
|---|---|---|---|
| 任务结构与组织信息处理 | 任务互依性和结果互依性是不同构念；结构应匹配需要处理的信息及依赖。模块化可以把一部分协调预先嵌入接口。 | 混合任务/奖酬设计在 Wageman 的组织样本中表现差；模块独立性需要接口承载真实依赖；Galbraith 与 Sanchez–Mahoney 是理论，不能称为普遍因果规律。 | 按依赖图组织任务和通信；接口声明输入、输出、假设、失效条件；把例外升级作为额外通道。单纯“多角色”不构成此机制。 |
| 共享任务理解与差异化专业知识 | SMM 解释共同的任务/协作结构；TMS 解释差异化知识如何被定位和调用，两者相补。 | 相似与准确不能混淆；TMS 测量中的可信度是成员信念，未必是客观可靠性。改变人员、工具或模型后，旧能力目录可能失效（后者为迁移推论）。 | 只同步必要的任务状态、依赖和协调规则；保留独有信息；维护有证据与有效期的“谁能解决什么”目录。 |
| 分布式证据与审议 | hidden profiles 说明自由讨论可能反复强化共同信息及初始偏好；前置异议可促进更充分的信息处理。 | 全体观点多样并不必然优于少数异议；“假扮反方”未复现真实异议的全部收益；人类的真实性效应不能直接套到 LLM。 | 在结论汇总前采集独有证据与独立判断；让异议改变证据采样和候选检查，而非仅增设反驳角色。 |
| 事件触发领导与备援 | 领导干预的有效性依事件新颖性/破坏性改变；备援取决于真实需要和负荷分布。 | 主动干预与领导满意度负相关，但在更具破坏性的事件中与有效性正相关；备援会挤占提供者自己的工作，且人类受援者可能在后续任务减少努力。 | 为停滞、冲突、工具失败、能力不足设计可观测触发器，按净收益选择接管、协助或继续自主；控制接管成本。不能把人类“偷懒”当成 LLM 必有心理属性。 |
| 团队复盘与经验更新 | 结构化、聚焦具体事件、多信息源的复盘总体有效；成功经验也值得分析。 | 复盘对先前表现较低的团队更有帮助；既有研究没有证明每轮、每任务都应复盘。反思文字本身不等于学习发生。 | 由执行轨迹和外部结果定位失败/成功原因，更新协作规则、能力目录和升级阈值；记录修改后的适用条件，避免把一次成功固化为通则。 |

### 跨簇比较

**共享与独立并不矛盾，关键在共享什么。** Mathieu 等人的 SMM 研究关注任务与团队互动结构的相似性；Liang 和 Lewis 的 TMS 研究关注专业知识分化及其调用。因此不能从“共享心智模型有益”推出“所有成员应看同一上下文并达成同一结论”。Lim–Klein 还把相似性和准确性拆开测量；Stasser–Titus 则展示了共识讨论如何保留初始信息偏差。对 Agent 更有用的假设是：共同维护协调状态，同时保留独立证据路径，汇总时再处理冲突。

**增加沟通与降低沟通需求，是两种不同的组织解法。** Galbraith 把自包含任务、纵向信息系统和横向联系放在同一个信息处理框架；Sanchez–Mahoney 进一步指出标准接口可以承载协调，使持续的权威指挥不再必要。与之相比，hidden-profile 干预针对的是“本应出现的信息没出现”。因此应先判断缺口来自接口/任务设计，还是证据未进入决策，不能统一处方为全连接讨论。

**团队控制应有事件和成本条件。** Morgeson 的领导研究、Porter 的备援需要研究和 Barnes 的备援成本研究共同反对无条件多管、多帮；Tannenbaum–Cerasoli 的复盘综述及 Schippers 等人的边界研究也反对把复盘频率当作学习强度。迁移到 Agent 时，值得深化的是“何时重组或升级”的判据及其可观测状态，而不是一个始终介入的 manager。

## 2. 必要文献与来源核查

证据类型：**理论**为概念解释，不是人类干预实验；**实验**为受控任务研究；**组织/纵向研究**主要支持关联和时序，不能自动证明因果；**元分析**汇总既有研究，也继承其测量和设计限制。核查深度 **F** = 读到可解析全文的有关段落；**A** = 读到出版社、作者或机构完整摘要；**I** = 原文页面/摘要的搜索索引片段，具体主张限制在可见内容。以下题名、作者、年份均核对；没有将元数据不足的材料用于额外方法细节。

### A. 任务互依性、信息处理与模块化

**A1. Ruth Wageman (1995). “Interdependence and Group Effectiveness.” Administrative Science Quarterly, 40(1), 145–180.** DOI: 10.2307/2393703。

- 主张与证据：组织现场研究区分任务和结果互依性；纯个人和纯团队设计在该研究中较好，混合设计表现较差。不能据此断言所有混合结构均无效。
- 必要性：纠正“共同目标”“互相交流”“任务相互依赖”是同一件事的混淆。
- 限制：特定组织背景；本轮未读到全文，不报告样本细分、随机化或效应量。将奖励机制迁移到共享权重的 LLM 时，必须另说明训练/选择目标如何真正影响行为。
- 来源与核查：I；[作者提供的摘要入口](https://harvard.academia.edu/RuthWageman?swp=tc-au-42940832)，[ERIC 题录与摘要](https://eric.ed.gov/?id=EJ506550)。后者用于交叉核对出版信息，机制不依赖第三方生成摘要。

**A2. Stephen H. Courtright, Gary R. Thurgood, Greg L. Stewart & Abigail J. Pierotti (2015). “Structural Interdependence in Teams: An Integrative Framework and Meta-Analysis.” Journal of Applied Psychology, 100(6), 1825–1846.** DOI: 10.1037/apl0000027。

- 主张与证据：元分析覆盖 107 个独立样本、7,563 个团队，区分任务互依性偏向任务过程的路径、结果互依性偏向关系过程的路径。
- 必要性：给 A1 的单组织结果提供构念层面的跨研究背景；并不把 A1 的所有“纯/混合”结论升级为普遍规律。
- 限制：元分析路径关系并不等同把依赖随机施加后的因果效果；人类凝聚力等中介不能直接视为 LLM 状态。
- 来源与核查：I（原始摘要已核对）；[PubMed 原文题录与摘要](https://pubmed.ncbi.nlm.nih.gov/25938722/)，[APA 官方补充材料](https://supp.apa.org/psycarticles/supplemental/apl0000027/apl0000027_supp.html)。

**A3. Jay R. Galbraith (1974). “Organization Design: An Information Processing View.” Interfaces, 4(3), 28–36.** DOI: 10.1287/inte.4.3.28。

- 主张与证据：理论文章，用信息处理需求与认知容量的关系解释任务不确定性为何对应不同组织形式；作者页面明确列出自包含任务、纵向信息系统和横向联系。
- 必要性：把“降低跨单元依赖”和“增加协调容量”放在可比较的设计空间中。
- 限制：不能把此文当作证明某通信拓扑总是更优的实验。接口稳定性、任务不确定性如何估计，仍需在 Agent 中操作化。
- 来源与核查：A；[出版社摘要与准确题录](https://pubsonline.informs.org/doi/10.1287/inte.4.3.28)，[作者机构说明及原文入口](https://jaygalbraith.com/organization-design-an-information-processing-view/)，[作者存档 PDF](https://jaygalbraith.com/wp-content/uploads/2024/03/infoprocess1974.pdf)（本轮 PDF 无可解析正文，未据此补写细节）。

**A4. Ron Sanchez & Joseph T. Mahoney (1996). “Modularity, Flexibility, and Knowledge Management in Product and Organization Design.” Strategic Management Journal, 17(S2), 63–76.** DOI: 10.1002/smj.4250171107。

- 主张与证据：理论分析提出，标准化组件和组织接口可以嵌入协调，以松耦合支持适应与不同层级的知识学习。
- 必要性：解释“模块化”为什么不仅是分工标签，还需要可共同理解的接口。
- 限制：这里的收益依赖可近似分解及可标准化接口；“隐藏了真实依赖的接口可能失败”是由其理论条件导出的迁移判断，本文不提供 LLM 因果证据。
- 来源与核查：A；[作者所在机构完整摘要与题录](https://experts.illinois.edu/en/publications/modularity-flexibility-and-knowledge-management-in-product-and-or-2/)，[作者存档 PDF](https://josephmahoney.web.illinois.edu/Publications/SMJ_Sanchez%20and%20Mahoney.pdf)。核对为 1996 SMJ 原文，未误用同名 1997 重印版。

### B. 共享心智模型与 transactive memory

**B1. John E. Mathieu, Tonia S. Heffner, Gerald F. Goodwin, Eduardo Salas & Janis A. Cannon-Bowers (2000). “The Influence of Shared Mental Models on Team Process and Performance.” Journal of Applied Psychology, 85(2), 273–283.** DOI: 10.1037/0021-9010.85.2.273。

- 主张与证据：56 个本科生二人组的飞行战斗模拟；任务模型和团队模型的共享程度与后续团队过程、表现正相关，过程在统计模型中起中介作用。
- 必要性：共享的对象包含任务及互动结构，不能简化为答案一致。
- 限制：小规模、受限模拟；共享程度与表现的中介关系不等同对所有任务的因果保证。
- 来源与核查：A；[PubMed 完整摘要](https://pubmed.ncbi.nlm.nih.gov/10783543/)。

**B2. Beng-Chong Lim & Katherine J. Klein (2006). “Team Mental Models and Team Performance: A Field Study of the Effects of Team Mental Model Similarity and Accuracy.” Journal of Organizational Behavior, 27(4), 403–418.** DOI: 10.1002/job.387。

- 主张与证据：71 个真实行动团队；任务/团队模型相似性及准确性分别预测表现，准确性和相似性不是冗余构念。
- 必要性：为“共识即正确”提供直接的测量反约束。原文讨论指出此前准确性结果并不一致，本研究不是所有相关研究的终结。
- 限制：现场关联研究；专家模型作为准确性参照有情境限制。不能把设定的“专家 Agent”当作真值。
- 来源与核查：F；[作者 Wharton 存档全文](https://faculty.wharton.upenn.edu/wp-content/uploads/2012/05/Lim_Klein_Team_mental_models_2006.pdf)，尤其摘要、准确性讨论及方法段。

**B3. Diane Wei Liang, Richard Moreland & Linda Argote (1995). “Group Versus Individual Training and Group Performance: The Mediating Role of Transactive Memory.” Personality and Social Psychology Bulletin, 21(4), 384–393.** DOI: 10.1177/0146167295214009。

- 主张与证据：受控装配任务中，共同训练的成员在一周后对程序的回忆和收音机装配质量更好；原摘要把主要作用归于 transactive memory 的发展。
- 必要性：团队知识的收益可能来自知道如何共同调用专长，而不只是每个人知道更多内容。
- 限制：训练和装配任务边界明确；摘要中的中介解释不证明任何共同训练都能提高开放式推理。
- 来源与核查：I；[出版社原文摘要与题录](https://journals.sagepub.com/doi/10.1177/0146167295214009)，[ERIC 交叉核对](https://eric.ed.gov/?id=EJ507907)。

**B4. Kyle Lewis (2003). “Measuring Transactive Memory Systems in the Field: Scale Development and Validation.” Journal of Applied Psychology, 88(4), 587–604.** DOI: 10.1037/0021-9010.88.4.587。

- 主张与证据：构建并验证 TMS 的 15 项量表，含 specialization、credibility、coordination；覆盖实验室、MBA 咨询团队与技术公司团队样本。
- 必要性：把 TMS 分为知识分化、对专长的可信判断及协调调用，防止将其误写成共享数据库。
- 限制：主要是测量验证，部分变量为自报告；可信判断不是客观准确率，不能用 LLM 自述“信任同伴”充当已校准可靠性。
- 来源与核查：I；[原始摘要](https://pubmed.ncbi.nlm.nih.gov/12940401/)，[作者上传原文入口](https://www.researchgate.net/publication/10597070_Measuring_Transactive_Memory_Systems_in_the_Field_Scale_Development_and_Validation)；维度另以 [UC San Diego 研究工具页](https://psychiatry.ucsd.edu/research/programs-centers/instep/tools-resource/definitions/emergent-states/cognitive-emergent-states/tms.html) 交叉核对。

**B5. Michelle A. Marks, Mark J. Sabella, C. Shawn Burke & Stephen J. Zaccaro (2002). “The Impact of Cross-Training on Team Effectiveness.” Journal of Applied Psychology, 87(1), 3–13.** DOI: 10.1037/0021-9010.87.1.3。

- 主张与证据：两项计算机模拟实验（45、49 个团队）；交叉训练改善共享互动模型，协调在共享模型与表现之间起中介作用。但所需训练深度的结果存在不一致。
- 必要性：为“成员理解别人的角色”提供干预证据，同时说明更深的角色轮换不是无条件收益。
- 限制：受控模拟的外部有效性；训练深度的不一致必须保留。LLM 是否通过提示就获得其他角色的执行知识须另验证。
- 来源与核查：A；[UCF 官方存档摘要](https://stars.library.ucf.edu/facultybib2000/3347/)，[PubMed 题录](https://pubmed.ncbi.nlm.nih.gov/11916213/)。UCF 页面 DOI 排版有误，标准 DOI 以 PubMed/出版题录核对。

### C. Hidden profiles、结构化审议与异议

**C1. Garold Stasser & William Titus (1985). “Pooling of Unshared Information in Group Decision Making: Biased Information Sampling During Discussion.” Journal of Personality and Social Psychology, 48(6), 1467–1478.** DOI: 10.1037/0022-3514.48.6.1467。

- 主张与证据：随机分配信息的学生四人组候选人选择实验；讨论容易由已共享且支持现有偏好的信息支配，使群体未能利用其共同拥有的全部信息。
- 必要性：独有证据未进入讨论是可识别的失败模式，不能用更多发言或最终投票直接修复。
- 限制：原文明确“最好”是相对于实验所给总体信息，不是现实世界真值；主要针对缺少公认唯一推导规则的判断任务。
- 来源与核查：F；[Münster 大学原文 PDF](https://www.uni-muenster.de/imperia/md/content/psyifp/aeechterhoff/vorlesungkommunikation/stasser_titus_unsharedinfogroupdisc_jpsp1985.pdf)，读到摘要、模型和方法；页码核为 1467–1478，而非有些二手引用中的 1476–1478。

**C2. Stefan Schulz-Hardt, Felix C. Brodbeck, Andreas Mojzisch, Rudolf Kerschreiter & Dieter Frey (2006). “Group Decision Making in Hidden Profile Situations: Dissent as a Facilitator for Decision Quality.” Journal of Personality and Social Psychology, 91(6), 1080–1093.** DOI: 10.1037/0022-3514.91.6.1080。

- 主张与证据：135 个三人组的人员选择实验；讨论前有异议的组更易解决 hidden profile，即使没人最初偏好正确方案；有正确方案支持者更好。少数异议与完全多样的异议强度未表现出决策质量差别；效果主要经讨论强度、部分经偏差减少体现。
- 必要性：异议的作用可以是让搜索更深入，不要求反对者一开始已正确。
- 限制：预置证据和封闭候选任务；不支持“反方越多越好”或“无须有新证据的争论就会有效”。
- 来源与核查：A；[作者 Göttingen 大学页面完整摘要](https://www.psych.uni-goettingen.de/de/ecosop/publikationen/publications-folder/pub-schulz-hardt-et-al-2006)，[原始题录](https://pubmed.ncbi.nlm.nih.gov/17144766/)。

**C3. Charlan Nemeth, Keith Brown & John Rogers (2001). “Devil's Advocate versus Authentic Dissent: Stimulating Quantity and Quality.” European Journal of Social Psychology, 31(6), 707–720.** DOI: 10.1002/ejsp.58。

- 主张与证据：人类受控研究比较真实少数异议与三种 devil's advocate 条件，真实少数意见产生的方案数量与质量更好。
- 必要性：提供对“只需指定一个挑刺者”的反证；不要与同年另一篇 “Improving Decision Making by Means of Dissent” 混成同一文献。
- 限制：不能由人类对真实/扮演立场的反应，推出 LLM 需要主观信念；迁移对象应是证据独立性、异议产生原因和采样路径。
- 来源与核查：A；[出版社完整摘要和作者顺序](https://onlinelibrary.wiley.com/doi/abs/10.1002/ejsp.58)。

### D. 事件触发领导与备援

**D1. Frederick P. Morgeson (2005). “The External Leadership of Self-Managing Teams: Intervening in the Context of Novel and Disruptive Events.” Journal of Applied Psychology, 90(3), 497–508.** DOI: 10.1037/0021-9010.90.3.497。

- 主张与证据：组织团队的事件情境研究；准备和支持性指导与感知领导有效性正相关，准备在事件更新颖时更重要；积极指导/意义解释与满意度负相关，但事件更具破坏性时与有效性正相关。
- 必要性：支持研究条件化的协调干预，而非固定的“强 manager”与“完全自治”二选一。
- 限制：结果包括团队对领导的感知，不应改写成客观任务分数上的随机试验证明；满意度和有效性需要区分。
- 来源与核查：I；[原始摘要和题录](https://pubmed.ncbi.nlm.nih.gov/15910145/)，[作者原文存档](https://www.morgeson.com/downloads/morgeson_2005.pdf)（直接读取失败，采用索引中的原摘要，不补写样本和设计细节）。

**D2. Christopher O. L. H. Porter, John R. Hollenbeck, Daniel R. Ilgen, Aleksander P. J. Ellis, Bradley J. West & Henry Moon (2003). “Backing Up Behaviors in Teams: The Role of Personality and Legitimacy of Need.” Journal of Applied Psychology, 88(3), 391–403.** DOI: 10.1037/0021-9010.88.3.391。

- 主张与证据：71 个四人组的计算机战术决策任务；备援的真实任务需要影响成员互相帮助的程度，并与施援、受援者特征交互。
- 必要性：先识别瓶颈和需要，再决定帮助；不能把帮助次数直接当成团队质量。
- 限制：人类人格交互并非可直接复制的 LLM 机制；本报告主要迁移负荷/能力是否需要协助的条件。
- 来源与核查：A；[作者机构完整摘要与作者表](https://experts.azregents.edu/en/publications/backing-up-behaviors-in-teams-the-role-of-personality-and-legitim/)。

**D3. Christopher M. Barnes, John R. Hollenbeck, David T. Wagner, D. Scott DeRue, Jennifer D. Nahrgang & Kelly M. Schwind (2008). “Harmful Help: The Costs of Backing-Up Behavior in Teams.” Journal of Applied Psychology, 93(3), 529–539.** DOI: 10.1037/0021-9010.93.3.529。

- 主张与证据：人类团队的实证反证；备援提供者会忽视自己的工作，在负荷均匀时尤其突出；收到大量备援的成员在后续任务中减少自身工作。
- 必要性：补上 D2 没有覆盖的提供方成本与跨阶段代价，禁止“有余力就永远复核所有人”的默认推断。
- 限制：人类依赖/努力变化需与计算资源机会成本分开；Agent 没有人格或动机上的等价性保证。
- 来源与核查：A；[SMU 作者机构存档、完整摘要](https://ink.library.smu.edu.sg/lkcsb_research/1746/)。

### E. 团队复盘与条件化学习

**E1. Scott I. Tannenbaum & Christopher P. Cerasoli (2013). “Do Team and Individual Debriefs Enhance Performance? A Meta-Analysis.” Human Factors, 55(1), 231–245.** DOI: 10.1177/0018720812448394。

- 主张与证据：46 个独立样本的元分析，总体效应 d = .67；报告 N = 2,136，包含个人/团队等独立分析单位，不能写成 2,136 人。复盘被定义为主动学习、改进导向、聚焦具体事件、含多个信息源。仅收到反馈或独写日记不符合其操作定义。
- 必要性：为 debrief 提供较强的总体证据，同时界定其与自由自我反思的差别。
- 限制：不同干预与任务的平均效果不能直接承诺 LLM 获得同样提升；参与者、复盘重点和测量层级的匹配很重要。“结构越多越好”的调节证据不确定：无结构比较仅一项；无引导者的研究也少，不能把总体效果当作各组成部分已独立识别。论文 2012 年在线，按正式卷期记 2013 年。
- 来源与核查：F；[原文 PDF](https://cebma.org/assets/Uploads/Tannenbaum-Cerasoli.pdf)，读到摘要、定义及调节讨论；[原始题录](https://pubmed.ncbi.nlm.nih.gov/23516804/)。

**E2. Shmuel Ellis & Inbar Davidi (2005). “After-Event Reviews: Drawing Lessons from Successful and Failed Experience.” Journal of Applied Psychology, 90(5), 857–871.** DOI: 10.1037/0021-9010.90.5.857。

- 主张与证据：士兵连续导航训练的准现场实验；同时复盘成功与失败，比仅复盘失败的表现改善更多。
- 必要性：阻止将经验更新缩减为错题本；成功轨迹中哪些条件使协调有效同样有价值。
- 限制：特定训练任务，不能推断无论何种成功都值得保存为规则；迁移仍需区分能力作用、环境便利与偶然成功。
- 来源与核查：A；[Tel Aviv 大学作者记录与完整摘要](https://cris.tau.ac.il/en/publications/after-event-reviews-drawing-lessons-from-successful-and-failed-ex/)，[原文 PDF](https://cebma.org/assets/Uploads/Ellis-2005.pdf)。

**E3. Michaéla C. Schippers, Astrid C. Homan & Daan van Knippenberg (2013). “To Reflect or Not to Reflect: Prior Team Performance as a Boundary Condition of the Effects of Reflexivity on Learning and Final Team Performance.” Journal of Organizational Behavior, 34(1), 6–23.** DOI: 10.1002/job.1784。

- 主张与证据：73 个团队的纵向研究；反思经学习关联后续表现的关系，在较差初始表现下更有利。
- 必要性：对“每一步都反思”给出条件约束；已有表现和改进空间会改变反思价值。
- 限制：不能把高表现条件下关系较弱写成已证明复盘有害；纵向中介也不是随机干预因果识别。
- 来源与核查：A；[出版社完整摘要](https://doi.org/10.1002/Job.1784)，[作者机构记录](https://repub.eur.nl/pub/31357)。2012 在线、2013 正式卷期。

**E4. Michaéla C. Schippers, Michael A. West & Jeremy F. Dawson (2015). “Team Reflexivity and Innovation: The Moderating Role of Team Context.” Journal of Management, 41(3), 769–788.** DOI: 10.1177/0149206312441210。

- 主张与证据：英国 98 个基层医疗团队现场研究；反思与创新相关，其关系随工作需求和物理工作环境改变。
- 必要性：将 E3 的既有表现边界扩展到环境需求，说明 reflexivity 不是脱离情境的万能团队品质。
- 限制：关联研究，创新指标不等同一般正确率；不能把高负荷促进反思价值写成“应增加负荷”。
- 来源与核查：A；[出版社完整摘要与题名](https://journals.sagepub.com/doi/10.1177/0149206312441210)，[作者机构存档](https://eprints.whiterose.ac.uk/id/eprint/114585/)。注意同名 2010 会议版本不是本条，2012 在线、2015 卷期也不是三篇独立证据。

## 3. 值得继续深化的框架问题（未验证假设）

1. **任务与组织能否共同调整？** 将任务依赖、接口缺口和通信需求一起表示；当反复出现跨模块错误时，允许修改任务边界及协调方式，而不只给原拓扑加边。人类依据是 A1–A4，Agent 增量必须与动态编排、图优化和组织设计现有方法比较。
2. **能否同时维护共同任务状态与可校准的差异化专长？** 区分“共同知道什么”和“谁有独有证据/工具能力”；能力信任由可追溯表现和任务条件支持，模型或工具变动时可以失效。人类依据是 B1–B5；目录、记忆路由和专家选择都已有直接技术先例，迁移名称本身不构成创新。
3. **如何让异议真正改变证据流？** 在初始解答前保持必要的证据独立性，汇总时明确尚未进入决策的独有证据、支持关系和关键反事实。C1–C3 支持研究这个缺口，但不证明任一“独立—辩论—投票”流程有效。
4. **何时升级、备援、复盘，何时继续执行？** 将协助成本、其他任务损失和可预期收益纳入条件化控制；复盘修改团队运行规则，而不仅生成一句经验。D1–E4 提供条件约束；与动态领导、反思记忆及预算控制框架比较后，才能判断具体新意。

这些问题覆盖较广的知识工作，不依赖智慧家庭或专家投票等狭窄场景；本轮不冻结任务、实验协议或 benchmark。

## 4. 自我反证与检索边界

- **最强的反对解释**：许多团队收益来自互补知识、训练与外部反馈，若多个 Agent 同模型、同信息、同工具，仅赋予社会角色，未必具备产生收益的前提。人类证据无法替代这一实现检查。
- **最容易偷换的概念**：相似性变正确性、可信感变校准可靠性、异议台词变独立证据、共享存储变 TMS、自述反思变真正策略更新、领导满意度变任务绩效。
- **不能声称的结论**：人类团队必然优于个人；沟通越多越好；集中或去中心结构普遍最优；心理属性可原样迁移；上述理论迁移尚无人做过。
- **遗漏边界**：这里未系统覆盖多团队系统、临时跨组织协作、制度/激励设计与市场协调；不将未覆盖写成研究空白。来源以经典原始证据为主，目的在机制校准，不是最新团队科学全景综述。
- **访问限制**：若干旧论文网页解析间歇失败；I 级条目只使用原始摘要可见陈述，没有补写全文中的实验细节。理论与人类效应均不构成 Agent 效果证据。
