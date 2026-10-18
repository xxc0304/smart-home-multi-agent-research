# 人类团队如何识别并采用专家判断：机制、干预与迁移边界

检索与核验日期：2026-10-18。定位：为 LLM 多智能体团队提供可操作机制的证据备忘录；不是声称人类组织已经解决专家利用问题。12 篇核心原始研究，另附一篇经典理论源头。

## 研究问题与证据范围

RQ1：成员已有能力差异怎样转化为团队中的影响力？RQ2：哪些受控操作使团队更多采用正确或专家输入，哪些操作失败？RQ3：这些结果如何生成 Agent 协议假设，同时避免把人类发现当作 LLM 效果证据？

关键区分：**拥有专家、识别专家、共享专家信息、给予专家影响力、最终答对**是不同环节。尤其“已知谁更擅长却仍不采用其答案”不能仅用专家发现或角色匹配解释。长期平均专家与当前题目的正确成员也不能互换。在与 *Multi-Agent Teams Hold Experts Back* 对接时，逐题 ALOC oracle 的缺口不等于所有团队都低于固定 best model；应保留该基准区别。

检索分两轮以上：第一轮使用 `Bonner Baumann Dalal member expertise group decision making`、`Littlepage task experience recognition utilization`、`Mahmoodi equality bias Bahrami optimally interacting minds`；第二轮依据结果加入 `member awareness majority wins information weighting`、`separating confident correct knowledge transfer`、`Bunderson specific diffuse status cues`、`revisiting demonstrability`、`social influence protects equality bias`；第三轮定向追查干预方法、DOI、原始摘要与反例，并补 `communication networks selecting members network positions`。通过联网检索及出版社、PubMed/PMC、大学研究库、作者上传原文核验。未使用付费 API，未开展实验。

访问等级：A＝可读原始论文全文或作者稿；B＝出版社/作者机构/原始论文数据库的摘要与元数据；B-index＝出版社页面受阻，检索索引可读其摘要/正文片段；C＝仅二手介绍。核心结论均至少 B，C 只辅助定位。涉及 B/B-index 的研究不补造随机分配、效应量、具体指令或样本细节。这里的“实验支持机制”通常不意味着所有中介路径已被独立随机操纵。

## 核心证据卡

### H1. 经验不是单一变量：能力增长与认识队友要分开

**Littlepage, Glenn; Robison, William; Reddington, Kelly (1997).** *Effects of Task Experience and Group Experience on Group Performance, Member Ability, and Recognition of Expertise.* Organizational Behavior and Human Decision Processes, 69(2), 133–147. DOI [10.1006/obhd.1997.2677](https://doi.org/10.1006/obhd.1997.2677)。[出版社原始记录](https://www.sciencedirect.com/science/article/pii/S0749597897926777)；[摘要镜像与元数据](https://ideas.repec.org/a/eee/jobhdp/v69y1997i2p133-147.html)。访问 B-index；摘要核验。

- 证据：三项研究，分别涉及生存任务、价格估计、知识测验；摘要报告第三项 21 组结果支持，在相关任务上的共同经验促进专家识别和利用。
- 操作/机制：区分任务经验和群体共同经验；前者可提升个人能力，后者可帮助建立谁知道什么的模型。不能把一切团队练习收益都归因于专家利用。
- 条件与限制：相关任务上的经验；不能从摘要得出熟悉队友对任意新领域有效，更不能据此断言团队越熟越好。
- Agent 启发：把个人热身提升与跨成员能力档案建立分开记录；对使用既有专家的任务，共同热身是可选信息来源，而不是解决利用失败的充分条件。

### H2. 人类群体确实能偏重高表现成员，但依赖任务条件

**Bonner, Bryan L.; Baumann, Michael R.; Dalal, Reeshad S. (2002).** *The effects of member expertise on group decision-making and performance.* Organizational Behavior and Human Decision Processes, 88(2), 719–736. DOI [10.1016/S0749-5978(02)00010-9](https://doi.org/10.1016/S0749-5978(02)00010-9)。[出版社](https://www.sciencedirect.com/science/article/pii/S0749597802000109)；[元数据与摘要](https://ideas.repec.org/a/eee/jobhdp/v88y2002i2p719-736.html)。访问 B-index。

- 证据：三人合作组与个体比较，使用不同难度的 Mastermind；专家按先前任务表现定义。摘要报告，群体组合结果更符合事后 expert-weighted 模型，成绩达到等量个体中最好者的水平。
- 机制：可见且有区分度的任务表现有助于有效加权；太容易或太困难都可能缺少识别能力差异的信息。
- 限制：模型拟合不是直接观察内部推理；“等量个体中最好者”不等于有逐题 oracle。该结果也不能保证每组、每题都追随真正正确者。
- Agent 启发：测量实际意见权重和专家答案保留率，而非仅看专家角色标签；校准集要能区分成员能力。

### H3. 对能力分布的预期也会影响利用

**Baumann, Michael R.; Bonner, Bryan L. (2004).** *The effects of variability and expectations on utilization of member expertise and group performance.* Organizational Behavior and Human Decision Processes, 93(2), 89–101. DOI [10.1016/j.obhdp.2003.12.004](https://doi.org/10.1016/j.obhdp.2003.12.004)。[出版社原文记录](https://www.sciencedirect.com/science/article/pii/S0749597803001183)。访问 B-index。

- 证据类型：实验操纵成员预期及组内能力差异。原始摘要报告，其对专家利用的作用主要经由专家识别体现。
- 机制：能力差异够不够清楚，与团队原先是否期待这种差异共同作用；不能只向团队泛泛宣布“存在专家”。
- 限制：未取得完整方法，本文不声称某一种具体预期指令必定改善，也不从统计中介直接推导因果中介。论文讨论还指出，最佳成员依赖与绩效之间在不同任务上并不总是正相关。
- Agent 启发：把真实可靠度分布、告知的可靠度分布、最终影响权重拆开，辨别错误能力信念与明知而不用。

### H4. 身份地位可成为错误的能力代理；组织证据主要是相关

**Bunderson, J. Stuart (2003).** *Recognizing and Utilizing Expertise in Work Groups: A Status Characteristics Perspective.* Administrative Science Quarterly, 48(4), 557–591. DOI [10.2307/3556637](https://doi.org/10.2307/3556637)。[WashU 作者机构原始摘要](https://profiles.wustl.edu/en/publications/recognizing-and-utilizing-expertise-in-work-groups-a-status-chara/)。访问 B。

- 证据类型：高科技企业自主管理生产团队的多层级现场检验；不是去中心化或任职时长的随机干预。
- 结果：任务相关的 specific status cues 在较去中心化、合作较久的组中更能预测能力归因；社会类别等 diffuse cues 在较集中、较新的组中更突出。影响力与任务相关线索对齐和团队绩效正相关。
- 限制：specific cue 也不是无误的实际能力测量；不能把此研究写成“减少层级已被实验证明提高专家利用”。
- Agent 启发：区分任务证据与品牌、模型名、资历角色等身份线索；匿名化身份或延迟显示身份是待检验干预。人类社会类别的作用不能直接移植为模型品牌效应。

### H5. 在回答前生成已有相关知识，能改变群体讨论与加权

**Bonner, Bryan L.; Baumann, Michael R. (2012).** *Leveraging member expertise to improve knowledge transfer and demonstrability in groups.* Journal of Personality and Social Psychology, 102(2), 337–350. DOI [10.1037/a0025566](https://doi.org/10.1037/a0025566)。[PubMed 原始摘要及 Utah 机构信息](https://pubmed.ncbi.nlm.nih.gov/21967008/)；[作者上传全文](https://www.researchgate.net/publication/51688798_Leveraging_Member_Expertise_to_Improve_Knowledge_Transfer_and_Demonstrability_in_Groups)。访问 A（作者稿文本）+B。

- 受控操作：干预组在每道估计题作答前，先生成**两条已有的相关知识**；随后个体再次回答或三人组协商。没有提供正确答案或新的外部证据。
- 结果：干预组讨论更多知识和成员专长，更偏重较好输入，绩效优于未干预组及平均比较个体。
- 限制：这是量值估计和知识迁移；讨论中的“事实陈述”编码包含实际错误的事实主张，不能把陈述量当作事实正确率。该干预并非让专家拥有最终否决权。
- Agent 启发：要求提供两个独立、可核验的支点，再形成/比较答案；但 LLM 生成的流畅理由可能是事后合理化，需把事实准确度与理由数量分开。

### H6. 从 confidence-weighted 转向 accuracy-weighted 的具体干预

**Bonner, Bryan L.; Bolinger, Alexander R. (2013).** *Separating the confident from the correct: Leveraging member knowledge in groups to improve decision making and performance.* Organizational Behavior and Human Decision Processes, 122(2), 214–221. DOI [10.1016/j.obhdp.2013.07.005](https://doi.org/10.1016/j.obhdp.2013.07.005)。[出版社记录](https://www.sciencedirect.com/science/article/pii/S0749597813000745)；[原始摘要镜像](https://ideas.repec.org/a/eee/jobhdp/v122y2013i2p214-221.html)；[Utah 机构成果目录](https://eccles.utah.edu/faculty-research/)。访问 B-index/B；未取得全文。

- 操作：指示参与者搜寻自己已经拥有且与问题相关的信息；个体先估值并报告信心，第二次个体或群体作答，有/无干预比较。
- 结果：干预条件的群体决策更符合较准确成员更有影响力的模型；无干预时更符合较自信成员更有影响力的模型。干预组绩效更好。
- 限制：accuracy-weighted 是事后模型的相对拟合，不表示参与者能直接读出真实正确率；不应把“解释得更多”自动等同于机制生效。
- Agent 启发：提供支撑知识可能比单纯询问信心更值得优先检验，特别适合检验已知专家是否仍被高自信非专家压过。

### H7. 专家身份信息要有足够的共同覆盖

**Baumann, Michael R.; Bonner, Bryan L. (2013).** *Member Awareness of Expertise, Information Sharing, Information Weighting, and Group Decision Making.* Small Group Research, 44(5), 532–562. DOI [10.1177/1046496413494415](https://doi.org/10.1177/1046496413494415)。[出版社原始摘要](https://journals.sagepub.com/doi/10.1177/1046496413494415)。访问 B。

- 受控操作：改变讨论前已经知道成员专长的人数。
- 结果：独有信息的讨论呈 majority-wins 型转变，即超过半数知情时发生变化。信息权重的回归指标可被多个模型解释；自报权重只有 majority-wins 模型拟合；能力评分没有被所检验模型充分解释。
- 限制：不能概括成“只需专家自己知道”或“所有结果都有严格多数阈值”；更不能把这个人数阈值当作任意网络规模的规律。
- Agent 启发：专家卡只给 coordinator 与广播给全员是不同操作。测试公共能力信息是否形成可用的协调基础，但广播仍不保证最终采用。

### H8. 共享信心可以增益，也可以让团队弱于较好成员

**Bahrami, Bahador; Olsen, Karsten; Latham, Peter E.; Roepstorff, Andreas; Rees, Geraint; Frith, Chris D. (2010).** *Optimally interacting minds.* Science, 329(5995), 1081–1085. DOI [10.1126/science.1185718](https://doi.org/10.1126/science.1185718)。[PMC 作者稿](https://pmc.ncbi.nlm.nih.gov/articles/3371582/)；[PubMed](https://pubmed.ncbi.nlm.nih.gov/20798320/)。访问 B-index（原始摘要及作者稿检索文本；本次 open 遇验证码）。

- 受控研究：二人低层视觉判断，改变交流及结果反馈等条件。
- 结果：敏感度相近且可自由交流时，二人能优于个体，且不一定需要结果反馈；能力差异很大时，合作会弱于较好成员。
- 机制解释：weighted confidence sharing 模型解释表现模式，依赖成员信心可比较、正确传达的假设；论文也承认数据不能唯一排除其他信息共享模型。
- Agent 启发：报告信心必须先检验跨模型校准和题型依赖。该论文尤其不能被引用为“多模型只要共享置信度就最优”的依据。

### H9. 反馈和奖励不能保证克服 equality bias

**Mahmoodi, Ali; Bang, Dan; Olsen, Karsten; Zhao, Yuanyuan Aimee; Shi, Zhenhao; Broberg, Kristina; Safavi, Shervin; Han, Shihui; Nili Ahmadabadi, Majid; Frith, Chris D.; Roepstorff, Andreas; Rees, Geraint; Bahrami, Bahador (2015).** *Equality bias impairs collective decision-making across cultures.* PNAS, 112(12), 3835–3840. DOI [10.1073/pnas.1421692112](https://doi.org/10.1073/pnas.1421692112)。[PMC 原文](https://pmc.ncbi.nlm.nih.gov/articles/PMC4378431/)（含 Tehran、Oxford、Aarhus、Peking、UCL 等原文机构信息）。访问 A。

- 操作：二人先私下判断并报信心，分歧时由随机指定一人裁决；四项实验考察能力差距、明确累计表现反馈及金钱激励。
- 结果：丹麦、伊朗、中国样本仍表现近等权倾向：较弱者对较强者相对赋权不足，较强者对较弱者相对赋权过多。偏差以模型最优加权为基准，不等于所有人机械地各投一半。
- 反证价值：知道差距与有动机做对仍不足以保证合理加权；但不能说一切反馈或激励设计均无效。首项样本为成年男性，任务为重复视觉辨别。
- Agent 启发：需要测量“告知可靠度后是否正确改变权重”，不能只检查 agent 是否在文本中承认专家。人类 equality bias 不能仅凭相似性能曲线被诊断为 LLM 内部机制。

### H10. 保留独立初判也不是跨任务普适的最优规则

**Hertz, Uri; Romand-Monnier, Margaux; Kyriakopoulou, Konstantina; Bahrami, Bahador (2016; online 2015-10-05).** *Social influence protects collective decision making from equality bias.* Journal of Experimental Psychology: Human Perception and Performance, 42(2), 164–172. DOI [10.1037/xhp0000145](https://doi.org/10.1037/xhp0000145)。[PubMed 原始摘要，UCL 机构](https://pubmed.ncbi.nlm.nih.gov/26436525/)；[UCL 作者稿](https://discovery.ucl.ac.uk/1470449/1/InfluenceEqualityBias.pdf)。访问 B（作者稿已定位，核心结论以原始摘要核验）。

- 操作：IND 先私人判断，有分歧再讨论；INF 没有先行私人判断，直接协商。第二实验隐蔽地给一人的视觉显示加噪声，扩大能力差异。
- 结果：IND 中不获集体收益的 dyads 在 INF 中改善；异质条件下 INF 让较可靠成员更主导，减轻 equality bias。
- 限制：二人知觉任务，不能推出 LLM 应取消独立求解。任务也不同于多人开放式推理中的群体错误传播。
- Agent 启发：独立初判减少相关错误，却也可能形成承诺或不合理对等协商；这两种效应的取舍应由题型和能力差距决定。

### H11. Demonstrability 是过程条件，而非“正确答案自然获胜”

**Bonner, Bryan L.; Shannahan, Daniel; Bain, Kristin; Coll, Kathryn; Meikle, Nathan L. (2022; online 2021-10-06).** *The Theory and Measurement of Expertise-Based Problem Solving in Organizational Teams: Revisiting Demonstrability.* Organization Science, 33(4), 1452–1469. DOI [10.1287/orsc.2021.1481](https://doi.org/10.1287/orsc.2021.1481)。[出版社原始摘要及作者机构](https://pubsonline.informs.org/doi/10.1287/orsc.2021.1481)（Utah、Northern State、RIT、Notre Dame）。访问 B。

- 类型：理论重构和测量工具开发/效度检验，不能列为“某个干预已经被随机实验确认有效”。
- 贡献：指出原始 task demonstrability 对持续团队、能力异质、多面复杂任务的适用边界，重述条件并建立测量工具。
- Agent 启发：把正确输入能否被表达、能否被其他成员理解和检验，作为中间机制变量；客观有正确答案并不意味着团队能辨明它。
- 不能外推：一份人类自报告量表不是 LLM 推理质量验证器。

### H12. 把合适成员置于通信中心，与单纯找领域最强者不同

**Guo, Jerry; Argote, Linda; Kush, Jonathan; Park, Jisoo (2023).** *Communication networks and team performance: selecting members to network positions.* Frontiers in Psychology, 14, 1141571. DOI [10.3389/fpsyg.2023.1141571](https://doi.org/10.3389/fpsyg.2023.1141571)。[开放原文](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2023.1141571/full)（Frankfurt School、Carnegie Mellon、UMass Dartmouth、Clark）。访问 A。

- 随机实验：41 个三人组，App Inventor 图形编程；练习后投票选通信中心，再随机给予所选者或两个未选者之一。两条件均被告知随机分配，以削弱主观自主权的差异。
- 结果：获得所选中心的组错误更少；训练期间沟通活动解释中心选择与绩效优势。主要对照是“得到所选者”与“排除所选者”，普通随机中心的比较来自补充合成重采样，不能当作第三个直接实验条件。
- Agent 启发：评估协调者的通信/整合技能与角色匹配；不能据此宣称领域专家担任中心本身的独立因果效应，也不支持任意 broadcast 拓扑的最优性。

## 理论源头补充

**Laughlin, Patrick R.; Ellis, Alan L. (1986).** *Demonstrability and social combination processes on mathematical intellective tasks.* Journal of Experimental Social Psychology, 22(3), 177–189. DOI [10.1016/0022-1031(86)90022-3](https://doi.org/10.1016/0022-1031(86)90022-3)。[出版社原始摘要](https://www.sciencedirect.com/science/article/pii/0022103186900223)。访问 B-index。理论把接受某一回应所需的支持人数与回应的可证明性联系起来，提出四项条件。本文未取得该原文完整条件措辞，因此不从记忆逐条复原。H11 是其组织团队情境的后续重构，而非独立的普适干预证明。

## 机制综合：可迁移的究竟是什么

| 环节 | 人类证据给出的判断 | Agent 可操作设计假设 | 不能从人类证据直接推出 |
|---|---|---|---|
| 能力信念 | H1/H2/H3：可区分的经验和正确预期重要；H4：地位可替代真实能力 | 显式、题型相关、带不确定度的可靠度档案；身份信息与任务证据分开 | 挂“专家”标签就会增加正确采用 |
| 能力信息覆盖 | H7：部分结果存在多数知情阈值，专家独知未必够 | 向参与决策的全体广播同一能力证据，并检查其被接收 | 广播本身足以克服利用失败 |
| 证据的可辨明性 | H5/H6：激活已有相关知识改变讨论与加权；H11：理解和辨别不能假设为自动发生 | 结构化列出可核验支点、反驳条件和答案依赖关系；评分针对证据质量 | 更长推理文本、更多理由必然更正确 |
| 赋权 | H9：反馈和激励仍可保留近等权；H6：可从自信线索转向准确线索 | 将讨论发言机会与最终决策权分开；裁决需说明覆盖专家答案的可检验证据 | 对话中尊称专家＝最终决策利用专家 |
| 信心 | H8 的成功有能力相似/信心可比条件；H9 显示大能力差距的代价 | 用经验校准后的题型条件可靠度解释信心；不以语气强弱投票 | 原始 verbal confidence 跨模型可比 |
| 交互与角色 | H10：预先独立承诺在特定任务可能有代价；H12：合适中心是角色匹配问题 | 把独立解题、证据审核、协调通信和终局选择做成明确阶段/角色 | 必须永远独立投票，或必须让最强解题者当协调者 |

H6 与 H8 并不互相否定：前者表明在知识估计中未经审查的自信会成为误导线索，后者表明在某些知觉条件下信心交流可有效整合信息。H2 与 H9 也不能压成“人类会/不会用专家”：任务可辨明性、成员能力差异、信息形式和裁决规则不同。H4 的长期组织相关结果与 H12 的短期实验尤其不可混作同一种去中心化证据。

## 对当前 Agent 研究最有辨识力的推论（均为待验证设计，不是已证实 LLM 效果）

1. **先固定专家已知，单测利用。** 将专家/可靠度信息给全体，让“没有认出专家”不再成为解释；检测专家初始正确时，最终答案被何种证据或无证据改写。若这一设置仍失败，应转向赋权/证据辨别机制。
2. **用可核验支点替代纯粹说服。** 对相互冲突的答案，要求每方给出两个检验支点与一个会使自己撤回的条件；比较的是证据是否改变正确采用，而非文本长度。H5 给出最直接的人类干预原型，LLM 的幻觉支点是新增边界。
3. **把平等发言与等权决策拆开。** 允许所有成员提供异议信息，但不要把每人一票当作可靠度聚合；已知专家答案若被推翻，需要对应的可验证反证。这是由 H7/H9 激发的协议假设，人类文献本身未验证此种 Agent 否决规则。
4. **不要把全部归因押在 confidence sharing。** 先检验信心的题型条件校准；特别区分较弱者固执和较强者过度让步。H9 表明两个方向同时存在，单一“减少自我偏见”提示可能反而扩大强者让步。
5. **Coordinator 与 solver 分开评价。** H12 鼓励测量信息传递与角色匹配；若通信中心不擅长核验正确性，增加中心性仍可能丢失专家输入。

可预先规定的结果变量包括：能力判断准确度、专家信息接收/回忆、专家初始正确条件下的保留率、专家初始错误条件下的纠错率、无证据改写率、最终准确率与成本。以此避免“保护专家”只提升保留率却牺牲专家犯错时的修正能力。ALOC 缺口、固定 best-model 差距和同成本聚合增益须分别报告。

## 仍未被人类文献解决的问题

这些文献提供局部成功干预、机制线索和明确反例，尚不能构成普适组织处方。稳定的平均专长与瞬时题目正确性怎样结合、反馈在何种形式下足以改变赋权、证明能力较弱的正确少数怎样被识别，都有未决条件。跨文化三国实验提高了 H9 的覆盖面，但未覆盖所有文化、性别、组织、任务或激励结构。对于 LLM，还新增训练数据相关性、语言生成的说服力与事实可靠度脱钩、能力随题型变化、上下文污染等问题。因而合理的研究主张是：**把人类已有的过程分解与受控操作迁移为 Agent 可证伪假设**，而不是“人类方案现成，直接照搬即可解决”。

本报告按机制选择核心研究，经典组织与实验文献占主导；截至核验日期的可访问材料不等于穷尽 2024–2026 所有新发表工作。没有把未核验的近期检索命中写成证据。
