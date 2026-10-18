# 定向反向查新：交叉训练、双环学习、使命式指挥、专家授权

日期：2026-10-17。范围：经典人类机制→LLM Agent→传统 MAS／人机团队。两轮检索；不运行实验。以下“未见完整闭环”仅指本轮可访问材料。

## 结论先行

四个名称都不能直接宣称无人做过。较值得保留的是**异质职能的交叉训练与有代价的动态互助闭环**，以及**可核验、可撤回的临时专家决策权**。双环组织学习已有明确同名 LLM 工作 DLMA，组织规则改写也已有 Organized Teams 和 LIET 的不同程度覆盖。使命式指挥的意图分解和自主执行既有传统 MAS，又有新近 LLM 军事规划工作；完整“通信失联／命令过时→有界自主偏离→恢复联系后的交代”可能更窄，但本轮不足以宣称首次。

| 候选 | 人类完整机制的关键变量 | LLM／其他 AI 已覆盖 | 尚可研究的精确边界 | 判断 |
|---|---|---|---|---|
| Cross-training + backup | 执行别人的职能→学到其信息、约束、成本→互相预测与监测→负荷／失败时主动帮助 | CORY 真有换岗；人机交叉训练已明确实现；传统 STEAM 已监测与重组 | 异质工具权限和局部观测下，以角色间知识改善互助，并计入接管成本与干扰 | 四者中较可保留，但不能把角色轮换本身当新颖 |
| Double-loop learning | 失败反馈可修正行动，也可改组织的规范、假设、评价标准 | DLMA 同名直接迁移；Organized Teams 改组织 prompt；LIET 更新合作知识；传统 MAS 早有组织规范变更 | 让“事实／规则／目标冲突”可区分，控制何时修行动、何时修规范，验证跨任务保留 | 宽泛方向高度覆盖，需窄化后再查 |
| Mission command | 目的、终态、边界、风险授权共享；下属在旧命令失效时主动调整；再同步 | 传统意图／政策形式化；LLM commander-intent 规划与验证 | 命令陈旧检测、失联期间受约束偏离、局部信息触发升级、事后意图一致性审计 | 不能称空白；更像可靠自治问题 |
| Deference to expertise | 异常时让最相关的现场专家取得决策权，随事件改变；保留质疑、恢复、问责 | 专家选择／动态领导／动态网络已多；LLM 团队压制专家的实证问题已直接研究 | 将认知建议权变成临时行动控制权，依据任务局部证据授权并撤销，兼顾错误／恶意专家 | 广义拥挤；完整授权闭环仍值得二次专门检索 |

## 1. 人类交叉训练：不是“任何轮换”

核心原始实证是 Marks, Sabella, Burke & Zaccaro (2002), *The impact of cross-training on team effectiveness*, JAP 87(1), 3–13，DOI 10.1037/0021-9010.87.1.3。两项计算机模拟实验分别为45和49支团队，支持交叉训练促进共享团队交互模型，协调中介了共享模型和团队表现之间的关系；对训练深度的结果不完全一致。因此不能从人类研究推出“轮岗越深越好”。原文区分 positional clarification、positional modeling、positional rotation，关键是学习其他职位如何影响协作。[PubMed 原始摘要](https://pubmed.ncbi.nlm.nih.gov/11916213/)

**CORY 核对后的边界。** NeurIPS 2024 *Coevolving with the Other You* 将同一 LLM 复制成 pioneer 和 observer：前者看问题独立生成，后者额外看前者输出；训练中交换两种输入角色，缓解 observer 对参考输入的依赖，使任一模型能独立推理。它确实覆盖“轮流经历两角色”，但没有测试人类交叉训练所强调的异质岗位限制、对队友负荷的理解、监测后主动接管及接管成本。准确定位应是**部分机制近邻**，不能因名称 cross-training 判作完整等价，也不能说它“根本没轮岗”。[论文方法 §3.1](https://arxiv.org/html/2410.06101v1)

更强的非 LLM 先例是 Nikolaidis & Shah (HRI 2013), *Human-robot cross-training: computational formulation, modeling and evaluation of a human team training strategy*。人和机器人反复交换角色来学习共享计划，明确以人类团队训练为源头；这是人机团队的直接计算迁移，不能忽略。[CMU 原始论文页面](https://www.ri.cmu.edu/publications/human-robot-cross-training-computational-formulation-modeling-and-evaluation-of-a-human-team-training-strategy/)

传统 MAS 里，Tambe (1997) STEAM 已将联合承诺、监测、修复和团队重组变成可执行规则。因此“发现队友失败就重分配”也不是新增机制。[Towards Flexible Teamwork](https://arxiv.org/abs/cs/9709101)

**相对可保留的研究对象（推断）**：先固定不同工具／权限／可见信息的岗位，再让智能体经历别人的决策约束；测试是否更准确预测队友完成时间与信息需求，并在能力退化／突发负荷时以更低干扰接管。必须比较：相同经验量但不轮岗、只读队友轨迹、直接共享所有信息、普通负荷均衡／故障重分配。否则效果可能只是更多训练数据或更多观测。

## 2. 双环组织学习：已有直接迁移

原始理论起点：Argyris (1976), *Single-Loop and Double-Loop Models in Research on Decision Making*, ASQ，DOI 10.2307/2391848；不能仅把“外层循环+内层循环”叫双环。需区分组织行为的 governing variables／规范与规则内的行动修正。[原始文献记录](https://eric.ed.gov/?id=EJ144734)

**直接 LLM 先例**：Zhang et al., *Evolving and Executing Research Plans via Double-Loop Multi-Agent Collaboration*，arXiv:2510.06761，2025-10-08。论文显式引用 Argyris；leader loop 用研究方案种群、改进及整合会议优化计划，follower loop 通过执行前后会议适应执行。它是组织学习同名直接迁移，不能列为“尚无人将双环用于 Agent”。但其形式化主要是研究计划与行动序列的双层优化；不能自动视作已经完整解决组织规范、评价标准与防御性习惯的改变。[全文 §1、§3](https://arxiv.org/html/2510.06761v1)

三个必须比较的邻居：

- **Organized Teams**：批评者读取轨迹，协调者结合成本生成新组织 prompt，并运行新 episode 验证，已覆盖“根据失败改变组织规则”。单纯提出“组织反思／可学习组织结构”不成立为新颖性。[全文 §3.2](https://arxiv.org/html/2403.12482v1)
- **LIET**：环境成本效用模型＋接收方反思消息有用性＋全队共享合作知识清单；已覆盖跨交互改进沟通规范。它不是岗位交叉训练，也没有显式重设任务目标或评价函数。[全文 §3](https://arxiv.org/html/2506.07232v1)
- **MAPoRL**：多个 LLM 先生成答案、再讨论，用 verifier 对最终输出评分作多智能体 RL 奖励。它是协同后训练，不能仅因共同训练就视作人类交叉训练，也不自动等同修改组织治理变量。[原始论文](https://arxiv.org/abs/2502.18439)

传统 MAS 反例也存在：da Silva (2005), *A Formal Model for the Fifth Discipline* 在 §5.6 清楚讨论早期 MAS 中个体／组织、单环／双环四种学习，并将组织双环对应到组织规范改变。但该篇自身偏理论形式化，不是 LLM 系统能力实证；所引1999工作本轮未逐页核验，不能用它主张具体算法性能。[原始 JASSS 全文](https://jasss.soc.surrey.ac.uk/8/3/6.html)

**可做的窄问题（推断）**：在固定用户任务约束下，维护显式可变的组织规范，使用重复反事实失败证据决定行动修补或规范修订，并做跨任务回归测试；应把 DLMA、Organized Teams、LIET 当实质基线而非名称背景。

## 3. 使命式指挥：授权边界与过时命令比“领导者派活”更关键

人类原始依据是美国陆军 ADP 6-0 (2019) 的使命式指挥教义，属于规范性制度来源，不能当作随机实验的因果证据。七项原则包含能力、互信、共享理解、指挥官意图、使命命令、有纪律主动性、风险接受。核心场景是没有命令、当前命令不再适用或出现机会／威胁时，下属仍按意图采取行动。[官方陆军解释及2019教义链接](https://www.armyupress.army.mil/Journals/NCO-Journal/Archives/2020/May/Mission-Command/)

传统 AI 已有 Chin, Muccio, Older & Vestal (2010), *Policy-Based Design and Verification for Mission Assurance*，用政策和多智能体模态逻辑约束自主系统符合 commander intent。这是意图+权限+形式化验证的先例，本轮打开原始 PDF；因此这些机制不能声称首次从军事组织借入 AI。[作者托管论文 PDF](https://ecs.syr.edu/faculty/chin/papers/conops.pdf)

LLM 近邻：2026 IFPV 把 commander intent 分解成多平台行动计划，由多视角层次 agents 与模拟验证耦合；可见摘要足以证明意图分解与验证已有实现，但不支持它已包含失联时的授权调整。[原始摘要](https://arxiv.org/abs/2605.14851)

**剩余边界（推断）**：把目的／终态和行动方法分离，给智能体受资源、权限与风险上限约束的自主调整权，测试通信延迟、指令陈旧、局部新事实三类扰动；比较固定指令、中心重规划、纯去中心计划和有界自主方案。意图提示或分层任务分解本身已太宽，完整闭环的新颖性仍需跟可调整自治／BDI／授权政策／intent-based control 对查。

## 4. 高可靠组织的专家授权：不能缩成“选最强模型”

人类理论来源是 Weick, Sutcliffe & Obstfeld (1999), *Organizing for High Reliability: Processes of Collective Mindfulness*；较可读的作者书章节 *Managing the Unexpected*, Principle 5: Deference to Expertise，说明随挑战调动专家知识的组织机制。核心是现场情境所需专长，而非固定资历或职位。这一条并非独立于失败关注、操作敏感性、韧性等其余 HRO 原则的万能开关。[作者书章节／出版方](https://onlinelibrary.wiley.com/doi/10.1002/9781119175834.ch07)

LLM 领域不是空白：*Multi-Agent Teams Hold Experts Back* (2026, arXiv:2602.01011) 直接研究专长不对称，发现讨论中的折中可能稀释专家意见；专家服从率与团队效果关系得到测量。该工作是直接问题实证，不能当成已建立可靠专家授权算法。[全文](https://arxiv.org/html/2602.01011v3)

异名机制上，DyLAN 已依据任务表现优化团队及计算 agent importance；Organized Teams 也出现基于任务专长轮换领导的 prompt。故“动态选专家／动态leader／贡献评分”必须视作已有邻居。[DyLAN 原始论文](https://arxiv.org/abs/2310.02170)

**较窄空间（推断）**：将局部专长证据映射成临时决策权，定义可覆盖的行动范围、有效期、异议通道和撤权条件；在异常／危机结束时恢复常态。与静态专家路由相比，真正不同的控制变量是“谁有权决定行动”随事件切换，而非只给专家答案更高投票权。需同时测专家正确和专家失误／恶意的情况，以免退化为权威偏误。现有证据未允许宣称这是无人实现的完整机制。

## 两轮检索记录与访问边界

第一轮检索词：`Marks Sabella Burke Zaccaro cross-training positional rotation`；`LLM cross-training CORY`；`double-loop LLM agents`；`mission command LLM agents`；`LIET agents team training`；`Organized Teams LLM`；`MAPoRL agents`；`deference to expertise multi-agent LLM`；`Argyris single double loop governing variables`；`STEAM SharedPlans joint intentions`。

第二轮机制近义词：`LLM positional rotation`；`LLM cross training backup`；`multi-agent backup behavior learning agents cross training`；`LLM role rotation training`；`multi-agent commander intent mission autonomy`；`multi-agent double-loop learning organization`；`human-robot cross-training Nikolaidis Shah`；`DyLAN Agent Importance Score`；`policy-based design verification mission intent`。也检出大量工程博客／GitHub 项目，但未将名称宣传当成论文机制证据。

访问等级：Marks 使用 PubMed 原始摘要；CORY、Organized Teams、LIET、DLMA、专家团队论文访问 arXiv HTML 方法；MAPoRL、DyLAN、IFPV以原始摘要为主；STEAM原始论文摘要；人机训练用作者机构页面；Argyris为原始书目及可读作者论文副本线索；HRO原始书章页面可见范围有限，未完成1999章节全文审读；传统意图控制访问作者PDF。没有付费接口调用，没有实验。这里提供的缺失组件是可检验的研究假设，不是已证明的新颖性或有效性。

