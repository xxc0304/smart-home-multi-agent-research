# 人类团队“有专家却用不好”：干预证据与 Agent 可迁移规则

检索日期：2026-10-18。本文是总综述的干预证据分支；精选 12 篇原始研究，区分实验、协议内前后比较、实地关联和归纳案例。研究问题：哪些流程能使分散知识进入共同决定？改变的是知识采样、权重还是表达成本？什么条件下“更多讨论／更听专家”反而无效？

## 检索过程与阅读边界

两轮检索均已执行。第一轮从 structured expert elicitation / IDEA / nominal group / hidden profile / psychological safety / leader inclusiveness / HRO 寻找直接研究。第二轮专门追索反证：社会影响是否必然损害准确率、提醒专家角色是否足够、讨论改进是否普遍、心理安全是否真是随机干预。检索使用公开联网搜索，核对出版方、作者所在大学研究库和公开论文。未运行实验或调用付费 API。

阅读分级：**全文重点段落**表示取得完整文本并核读方法和结果相关段落，并非逐字通读；**摘要**表示仅核读原始摘要或大学研究库转载的原摘要；**索引摘要片段**不用于补全未知效应量或随机化细节。部分出版社拒绝抓取，已明确降级。

## 证据台账：究竟改变什么

| 原始研究 | 干预／比较改变的变量 | 直接结果与效用 | 证据等级、边界、实际阅读 |
|---|---|---|---|
| **1. Gustafson, D. H., Shukla, R. K., Delbecq, A. L., & Walster, G. W. (1973). A comparative study of differences in subjective likelihood estimates made by individuals, interacting groups, Delphi groups, and nominal groups. Organizational Behavior and Human Performance, 9(2), 280–291.** [原文 DOI](https://doi.org/10.1016/0030-5073(73)90052-4) | 比较单人估计、先谈后估、估计—反馈—再估计，以及估计—讨论—再估计。区分先形成独立判断和反馈形式。 | 原始索引摘要确认比较设计；其他检索转载摘要报告 estimate–talk–estimate 更接近正确值，但本次未从原始全文核实结果，**不将该优越性计入确定结论**。 | 早期比较实验候选；随机化、样本量和效应量未核实。原始索引摘要片段，全文访问被拒。 |
| **2. Van de Ven, A. H., & Delbecq, A. L. (1974). The Effectiveness of Nominal, Delphi, and Interacting Group Decision Making Processes. Academy of Management Journal, 17(4), 605–621.** [出版方](https://doi.org/10.2307/255641) | 比较 nominal、Delphi 与常规互动流程。NGT 的经典操作是先默写、轮流列出、澄清、私下排序；但不同研究实现不应视为同一处理。 | 出版方摘要可确认的终点是想法数量和参与者满意度，不能据此推断识别真正专家、客观正确率或最优决策。本次不据二手综述宣称某流程全面胜出。 | 原始比较研究；只读出版方索引摘要，未核读操作细节和结果表。用来限定 NGT 证据的测量范围。 |
| **3. Hemming, V., Walshe, T. V., Hanea, A. M., Fidler, F., & Burgman, M. A. (2018). Eliciting improved quantitative judgements using the IDEA protocol: A case study in natural resource management. PLOS ONE, 13(6), e0198468.** [原文全文](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0198468) | 先独立估计及区间，反馈并澄清题意和证据，私下重估，数学聚合。76 人随机分入八组，58 人完成第二轮；14 个可在未来验证的问题。 | 聚合优于典型单人；讨论后的组级准确度增益较小，八组中六组提高、两组下降。讨论可改善题意理解，不能保证每题改进。 | **真实领域、可验证的协议内前后研究；不是 IDEA 对无协议的 RCT**。随机的是组别，所有组都用协议。全文重点方法／结果段落。 |
| **4. Lorenz, J., Rauhut, H., Schweitzer, F., & Helbing, D. (2011). How social influence can undermine the wisdom of crowd effect. PNAS, 108(22), 9020–9025.** [作者公开全文](https://www.sg.ethz.ch/publications/2011/lorenz2011how-social-influence/PNAS-2011-Lorenz-9020-5.pdf) | N=144；重复数字估计中，控制看到他人估计、聚合信息或无社会反馈。 | 社会反馈使估计趋同且主观信心上升，但集体准确度没有相应改善。效用：保存独立初估，可识别“趋同被误认作证据”。 | **受控估计实验**。不是专业团队、不是所有讨论形式；不能由此推出永久隔离最优。全文重点结果段落。 |
| **5. Becker, J., Brackbill, D., & Centola, D. (2017). Network dynamics of social influence in the wisdom of crowds. PNAS, 114(26), E5070–E5076.** [作者公开全文](https://ndg.asc.upenn.edu/wp-content/uploads/2017/06/PNAS-2017-1615978114-Collective-Intelligence.pdf) | 1,360 人随机进入中心化、去中心化网络或无网络控制；初估后看邻居估计并修改。 | 去中心化网络中准确率提高，尽管意见分散度下降；中心化网络的方向取决于中心者初估是否朝向真值。 | **随机网络实验，构成对“社会影响必坏”的反证**。准确者更坚持初估的关联是机制证据，不等于把自信设高就能改善。全文重点方法／结果段落。 |
| **6. Stasser, G., & Titus, W. (1985). Pooling of unshared information in group decision making: Biased information sampling during discussion. Journal of Personality and Social Psychology, 48(6), 1467–1478.** [原文 DOI](https://doi.org/10.1037/0022-3514.48.6.1467) | 操纵信息分配，使群体合并私有信息后才可能识别优选方案。这里主要是失败机制诊断。 | 讨论偏向共同信息及支持既有偏好的信息。群体拥有全套信息，不意味着成员真的交换并利用它。 | **实验室 hidden-profile 研究**；专家在此是私有信息持有者，不是受训职业专家。原始摘要的数据库索引，未读全文。 |
| **7. Stasser, G., Stewart, D. D., & Wittenbaum, G. M. (1995). Expert Roles and Information Exchange during Discussion: The Importance of Knowing Who Knows What. Journal of Experimental Social Psychology, 31(3), 244–265.** [出版方](https://doi.org/10.1006/jesp.1995.1012)；[大学原摘要](https://experts.umn.edu/en/publications/expert-roles-and-information-exchange-during-discussion-the-impor/) | 公开谁掌握关于哪个嫌疑人的额外线索，比较仅私下告知个人将获得较多信息。 | 公开分工提高私有线索提及和正确嫌疑人选择；只让本人知道自己信息较多，没有同样收益。 | **实验性角色／信息分配干预**。改变的是可搜索的知识位置和讨论责任，不证明贴“专家”标签即可提升真实能力。读大学原摘要。 |
| **8. Stasser, G., Vaughan, S. I., & Stewart, D. D. (2000). Pooling Unshared Information: The Benefits of Knowing How Access to Information Is Distributed among Group Members. Organizational Behavior and Human Decision Processes, 82(1), 102–116.** [出版方](https://www.sciencedirect.com/science/article/pii/S0749597800928905)；[大学原摘要](https://experts.umn.edu/en/publications/pooling-unshared-information-the-benefits-of-knowing-how-access-t/) | 交叉比较 expertise forewarning 与讨论开始时公开 expert-role assignment。 | 公开专家角色减少偏向共同信息的采样；预先提醒并未同样改善采样，但能帮助已提及的私有信息留在书面记录中。 | **实验性重复与扩展**；与 1995 同一研究谱系，不能算完全独立实验室复现。说明采样、记录保留、最终正确性是不同终点。读大学原摘要。 |
| **9. Edmondson, A. (1999). Psychological Safety and Learning Behavior in Work Teams. Administrative Science Quarterly, 44(2), 350–383.** [原文 DOI](https://doi.org/10.2307/2666999)；[作者机构记录](https://dash.harvard.edu/entities/publication/13a7b031-0fdd-45ec-a7e0-2b80e2bc679f) | 51 个制造业团队，测量心理安全、学习行为与绩效等。没有随机分配心理安全干预。 | 心理安全与团队学习行为相关；提示提出问题和承认错误的社会成本可能影响知识进入讨论。 | **实地关联研究**。不能声称“训练心理安全已被该文 RCT 证明能提高决策准确率”。读原始摘要。 |
| **10. Nembhard, I. M., & Edmondson, A. C. (2006). Making it safe: the effects of leader inclusiveness and professional status on psychological safety and improvement efforts in health care teams. Journal of Organizational Behavior, 27(7), 941–966.** [出版方原摘要](https://onlinelibrary.wiley.com/doi/10.1002/job.413) | 23 个新生儿重症监护单位问卷；考察领导邀请、珍视他人贡献与职业地位差异。 | 包容性领导、心理安全和质量改进参与之间的关联支持其假说。候选干预是明确征询低地位成员并认可其贡献。 | **跨团队调查，非随机领导训练**；终点主要是改进参与，不能替换成病死率或专家意见采纳正确率。读原始摘要。 |
| **11. Porter, T., & Schumann, K. (2018). Intellectual humility and openness to the opposing view. Self and Identity, 17(2), 139–162.** [原文 DOI](https://doi.org/10.1080/15298868.2017.1361861)；[大学原摘要](https://www.researchwithrowan.com/en/publications/intellectual-humility-and-openness-to-the-opposing-view/) | 前三项研究主要联系谦逊与异见开放；Study 4 使成长型智力观念显著。 | Study 4 报告谦逊和对异见的开放提高；Study 3 包含接触相反政治观点的行为测量。 | **含实验操纵，但开放性不等于客观正确率**；也不是专家团队正确加权实验。只读原摘要，故不补报样本或中介因果强度。 |
| **12. Bigley, G. A., & Roberts, K. H. (2001). The Incident Command System: High-Reliability Organizing for Complex and Volatile Task Environments. Academy of Management Journal, 44(6), 1281–1299.** [出版方原文](https://doi.org/10.5465/3069401) | 消防部门使用 incident command system 的归纳实地研究；考察正式结构如何容纳灵活可靠的现场组织。 | 为结构与情境调整并存提供机制案例；“权限随局部专业知识移动”可作设计启发。 | **归纳案例，非 deference-to-expertise 的 RCT**。本次只读出版方原摘要；权限迁移具体操作应再读全文后作为文本细节引用，不能据摘要估计效果。 |

## 什么已经较有把握，什么仍未证明

**最直接的可控干预是改变信息进入流程的方式。** 在 hidden profile 中，公开“谁有哪类额外信息”能让团队有目的地询问、让信息拥有者承担报告责任。这比抽象要求“多交流”更具体。1995 与 2000 研究同源，故其跨实验一致性不应被夸大为跨实验室、跨文化和真实职业团队的充分外部复现。[Stasser et al., 1995](https://doi.org/10.1006/jesp.1995.1012)；[Stasser et al., 2000](https://www.sciencedirect.com/science/article/pii/S0749597800928905)

**独立初估值得保存，永久独立则没有普适证据。** Lorenz 的收敛而不增准，与 Becker 的去中心化网络增准并不矛盾：网络结构、任务分布和谁更愿意修正会改变社会影响的方向。不能把分歧减少当作准确性提高，也不能把分歧减少一律当作损害。专家拥有互补线索时，禁止交流还会阻止信息合并。[Lorenz et al., 2011](https://doi.org/10.1073/pnas.1008636108)；[Becker et al., 2017](https://doi.org/10.1073/pnas.1615978114)

**IDEA 是避免过早行为共识的实用流程，但组件作用未被上述单项研究完全分离。** 私下估计、题意澄清、论证交流、重复估计、数学聚合同时存在；第二轮优于第一轮，不能唯一归因于讨论，也不能排除额外思考或选择性退出等解释。数学聚合的目标是得到可评分判断，不是要求成员最终同意一句话。[Hemming et al., 2018](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0198468)

**心理安全、谦逊和 HRO 支持的终点不同。** 心理安全研究主要支持真实团队中表达、学习和改进参与的关联；谦逊研究中存在实验，但主要终点是愿意接触异见；HRO 案例提供组织机制描述。三者均不能直接证明“听更多专家建议就更正确”。在人类团队中害怕丢脸和职业地位是真实机制；迁移到 Agent 应控制通信机会、奖励和覆写规则，不能声称 LLM 具有同样心理状态。[Edmondson, 1999](https://doi.org/10.2307/2666999)；[Nembhard & Edmondson, 2006](https://doi.org/10.1002/job.413)；[Porter & Schumann, 2018](https://doi.org/10.1080/15298868.2017.1361861)；[Bigley & Roberts, 2001](https://doi.org/10.5465/3069401)

## 可证明性需要哪些条件

1. **专家优势可定义。** 必须区分任务相关私有信息、在独立题上的校准表现和头衔标签。只分配专家称号，最多证明社会角色影响；不能证明识别真能力。
2. **证据具有足够独立性。** 多个成员引用同一篇网页、同一个上游模型或转述同一个结论，不能当成多份独立支持。独立初估解决的是暴露时序，并不自动解决共同训练和共同数据造成的相关误差。
3. **任务允许验证。** 应有真值、未来实现值、可执行测试或独立裁判；价值冲突和偏好选择不能直接套用估计准确率。可证明的数学命题还需要共享规则与可检查论证，单纯投票不提供证明。
4. **测量链条分开。** 私有证据被提及、留在记录、被他人理解、进入决定、使结果变好，是五个不同事件。多发言、更多接受、更多共识均非正确性的充分指标。
5. **对照保持信息和预算一致。** 否则不能分清流程收益与多读资料、多想一轮、更多 token 的收益。这里提出的对照是未来设计建议，本文没有执行它们。

## 可迁移到 Agent 的三组可操作规则（设计借鉴，不宣称新颖）

### A. 独立初估 → 交换新证据 → 私下重估 → 聚合

先让每个 Agent 提交答案、区间、证据出处和可改变判断的条件；锁定初稿后才开放交流。中间轮要求新增证据、题意歧义或可验证反例，不要求统一措辞。末轮分别提交，可保留分歧；数值问题按预设规则聚合。主要控制**早期锚定与反馈内容**。适合可评分估计、预测和有独立检查器的任务；并不保证优于单个最强模型。

### B. 公开知识位置，强制覆盖私有证据

维护“问题子域—证据持有者—来源—适用范围”目录。综合前先向每个相关持有者征询其独有证据，把已报告事实写入共享记录；最终决策须注明关键线索是采用、驳回还是尚未解决。角色标签只是路由信息，权重依据任务相关验证。主要控制**信息采样和保留**；这是 hidden-profile 实验最贴近的迁移，不是“专家一票否决”。

### C. 局部且可撤销的专业权限，加异议触发检查

某子任务的执行权可暂时交给有相应工具、数据或留出题表现的 Agent；权限仅覆盖该子域，遇到反证或不确定性上升时回退到独立复核。领导／汇总 Agent 在结束前逐一征询未发言者的冲突证据，认可纠错行为并保留审计轨迹。主要控制**覆写权限、异议机会和责任范围**。这组借鉴 HRO、包容性领导与谦逊研究，直接因果证据弱于前两组；不能把协议文字等同于在人类中建立心理安全。

三组机制都应分别与“独立答案直接聚合”“常规自由讨论”“单个最佳已知成员”比较，并报告专家正确时的保留、专家错误时的纠正及错误专家获权后的损失。需要同时证明系统会用优势、也会拒绝可验证的错误，才能支撑“团队用好了专家”。
