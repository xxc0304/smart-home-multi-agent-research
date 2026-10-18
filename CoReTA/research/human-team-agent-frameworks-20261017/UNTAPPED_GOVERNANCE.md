# 治理机制定向查新：同意制、可生存系统与例外授权

检索日期：2026-10-17。结论：**本分支没有通过“人类有效性成熟 + Agent 机制尚少覆盖”双门槛的候选。** 三条线都值得作为设计来源，但不足以直接提出“首次把经典组织机制用于 Agent”的论文主张。以下把已实现、提案、传统 MAS 和人类组织证据分开。

## 1. 机制与判定

| 人类机制 | 真正应比较的控制变量 | 人类证据判断 | Agent 覆盖及结论 |
|---|---|---|---|
| Sociocracy：consent + circles + double linking | 目标/权限域明确的自治圈；带理由的异议触发修案；上下圈由领导与选举代表双向联结；政策制定与日常执行分离 | 有长期实践和同行评审案例，但本轮未核到足以认定普遍增效的因果证据 | 同名 consent gate 已有公开 LLM 协议；双链接也与已知 holacracy 先例重叠。**排除“未用的成熟机制”候选** |
| Beer Viable System Model（VSM） | S1运营、S2协调、S3内控及S3*独立审计、S4外部环境/未来、S5身份政策；递归自治和各环路平衡，而非五种角色命名 | 有量化调查支持，不仅是理论隐喻；但调查不能证明必要充分条件或移植后的因果效果 | 明确 VSM 命名的 LLM 工程与早期传统 MAS 均存在。**排除首次迁移主张** |
| Policy/exception-based dynamic delegation | 预设目标和授权边界；常规事项自治；偏离、风险或信息不足才升级；可撤回/缩减权限；升级成本与误决成本联合控制 | Galbraith 的信息处理解释成熟；本轮未把该宽泛组合核实为独立、普遍增效的组织干预 | LLM intelligent delegation 已明确提出权限约束、监控、动态更换、撤权；传统 adjustable autonomy 已有决策模型和部署。**机制覆盖广，不能靠管理学名称构造新颖性** |

## 2. 人类经典机制及“真有效”的证据边界

**Sociocracy。** Romme (1996) 将圈层用于政策制定、将实施保留给经理/主管，核心是将组织反馈接入管理层级，而非取消层级。[原作者所在大学的正式记录及摘要](https://research.tue.nl/en/publications/making-organizational-learning-work-consent-and-double-linking-be/) 可核题名、DOI、年份与上述区分。摘要中的 Netherlands “experiments”不能自行解释成随机对照实验。

更近的 King & Griffin (2023) 是一个共居非营利组织的探索案例，使用观察、档案和16次访谈；论文承认已有决策质量证据大多为轶事。它确实研究 consent、双链接、明确域及发声，但也讨论参与不平等。可支持机制可实施及现实取舍，不能支持“成熟普适增效”。[Governing for the Common Good, DOI 10.1007/s11266-023-00627-2](https://link.springer.com/article/10.1007/s11266-023-00627-2)

**VSM。** Schwaninger & Scheef (2016) 用调查和量化分析检验 VSM 假设，报告支持结果；此前主要证据为案例。这使它比单纯的组织隐喻更有依据，但本轮只核到作者机构存档摘要，未核完整研究设计/效应量，不把作者的“necessary and sufficient”理论描述当已证定理。[A Test of the Viable System Model: Theoretical Claim vs. Empirical Evidence, DOI 10.1080/01969722.2016.1209375](https://alexandria.unisg.ch/entities/publication/0562da96-5b13-408a-97c1-b1e19a7f78f3)

**例外授权。** Galbraith (1974) 的信息处理观点将任务不确定性与组织的信息处理需求联系，解释规则、层级及横向联系等设计选择。[作者网站原文 PDF：Organization Design: An Information Processing View, DOI 10.1287/inte.4.3.28](https://jaygalbraith.com/wp-content/uploads/2024/03/infoprocess1974.pdf)。这是清晰的组织设计理论来源，不能把它扩写成“动态授权+撤权+风险升级整套在人类团队已被实验证实”。

## 3. 两轮 Agent 查新：同名与机制近邻

### 第一轮：直接名称迁移

**Sociocratic consent gating 已有公开先例。** Astrid 的 2026-04-09 页面明确定义：接收者根据总体目标、上下文充分性及可预见失败选择接受或提出有理由异议，派发者必须修案；还提出以 consent 选领导。[原页](https://astridsolveig.substack.com/p/relational-coordination-in-multi)。这是**公开协议提案**。标题和摘要虽然写 empirical evaluation/实现及结果，正文却主要是实验设计、统计计划、expected outcomes 和提示模板；本轮未见实际结果表、运行日志或可验证代码链接。因此不能把它列作已验证方法，也不能再称 consent gate 从无人想到。

**VSM 已直接进入 LLM 编排。** [Dark Factory 原仓库](https://github.com/machinemates-ai/dark-factory) README 明列 S5=SPEC、S4=Lead Planner、S3=调度器、S3*=质量门、S2=Event Bus、S1=Codex workers，并包含源码、测试及工作流目录。判定为**公开工程实现声明及可访问仓库**，本轮未运行，也未确认递归和各反馈回路是否完整实现或有效；尤其“把组件贴 S1–S5 标签”不等于完整 VSM 验证。

补充交叉核验：[Eoin Hurrell, 2025-03-06](https://www.eoinhurrell.com/posts/20250306-viable-systems-ai/) 已明确讨论 VSM+LangGraph 代码审查，且诚实写出当时只集中实现 S1，完整层级属于未来方向。其价值在于排除 VSM 首次命名移植，而非证明全机制实现。

### 第二轮：异名机制与传统 MAS

**动态授权不能与普通任务分解混同，但已不是空白。** Tomašev、Franklin、Osindero (2026) 的 [Intelligent AI Delegation, arXiv:2602.11865](https://arxiv.org/html/2602.11865v1) 明确区分任务分解与权力/责任/问责转移，并涵盖监控、适应、更换受托者、受限权限、权限衰减和撤销。它是**框架/协议建议**，不能当成某个性能结果；但以“边界授权+异常处理”作为新的概念贡献已明显重叠。

**传统 MAS 的 adjustable autonomy 更早给出了等价控制变量。** [Towards Adjustable Autonomy for the Real World, JAIR 17:171–228 (2002), DOI 10.1613/jair.1037](https://arxiv.org/abs/1106.4573) 根据不确定性、个体与团队成本决定控制权转移，以条件策略而非一次性升级协调人机团队，并在真实研究组的代理系统中评估。注意 arXiv 入库为2011，期刊论文为2002；它是**非 LLM、人机团队/传统 MAS**，但足以否定“Agent 从未做过动态授权/例外升级”的宽泛说法。

VSM 传统系统补充线索：[Long-Term Adaptivity in Distributed Intelligent Systems: Study of ViaBots in a Simulated Environment (2019)](https://www.mdpi.com/2218-6581/8/2/25)，搜索摘要明确是 VSM、多机器人及适应性；本轮出版页抓取失败，故只作为后续核全文线索，不承担关键论断。

## 4. 仍可研究的窄问题，但不是本轮确认的空白

- 对 sociocracy：不是再加“反对”消息，而是比较**基层选举代表具有实质政策影响、跨圈双向约束和日常执行分离**是否有额外价值。需要先逐控制变量核对已知 CareerAgent/holacracy 等实现；本轮未逐条核全文，不能宣称完整双链接未用。
- 对 VSM：可以研究**审计独立性、S3/S4当下与未来冲突、递归自治、告警旁路**的可识别增益；普通 planner/worker/critic 与角色映射不足以构成贡献。本轮未确认这些联合机制在 LLM 中覆盖少，也未证明组合合理。
- 对授权：可研究**异常升级的决策成本、权限动态调整与任务效用联合优化**，但需与 adjustable autonomy、授权安全及2026智能委托框架直接比较；这已经是算法/协议问题，不能用管理理论名称代替技术差异。

建议本分支在主报告中列为“**反例/排除项：理论启发明确，但成熟证据或新颖性门槛未满足**”，不进入优先实验候选。

## 5. 检索记录与访问范围

第一轮关键词：`sociocracy empirical study consent double linking effectiveness Romme Endenburg`；`Viable System Model empirical effectiveness systematic review organizations Beer`；`sociocracy LLM agents`；`Viable System Model LLM agents`；`sociocracy agent consent github`；`viable system model multi-agent architecture`。

第二轮关键词：`dynamic delegation LLM policy exception`；`management by exception multi agent delegation policy`；`Intelligent AI Delegation Tomasev 2026 arxiv`；`delegation adjustable autonomy agents 2002 Scerri Pynadath Tambe`；`Galbraith 1974 organization design information processing exceptions hierarchy lateral relations`；`sociocracy empirical performance evidence Romme 2023 organizations`。

核心原始来源8项：Romme 1996、King & Griffin 2023、Schwaninger & Scheef 2016、Galbraith 1974、Astrid协议页、Dark Factory仓库、Intelligent AI Delegation、JAIR adjustable autonomy；另两项仅交叉核验/线索。读取了可公开页面、机构摘要、作者PDF与 arXiv HTML；Taylor & Francis 全文403，VSM量化研究未核完整正文，MDPI ViaBots访问失败。没有访问付费API、运行实验或调用子代理。所有“未核到”只限本轮检索。
