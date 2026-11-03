# 局部工作怎样成为共同解答：依赖发现、接续执行与语义边界

2026-10-27。deep-research 研究报告；只查阅文献和既有本地记录，未新增模型实验、未复现下列论文实现。引用版本限定于实际核验稿，不推断未核实的录用状态。

## 摘要

本报告审查一个具体候选：具有分散知识的成员先完成自己能够完成的局部工作，将尚缺输入留在工作中，其他成员补充后继续求解。文献显示，部分成果、缺口公告、条件补全和程序化依赖执行均已有直接先例；真正困难在于，从开放文本发现任务依赖、确认返回内容与当前操作相匹配，以及在错误输入或规则出现时维持有效的其他工作。现代 LLM 方法对实际产物交接和程序消费提供了较强证据，经典系统提供了精确的条件与依赖更新语义，但二者都没有自动免除这些语义判断。本项目值得探索的变化是把缺口发现放到局部工作的实际开展中，由掌握该操作的成员负责接续，让部分工作无需先变成整题推荐才能被利用。该候选尚未被验证，不把换接口、代码执行或经典机制组合本身视为已成立的贡献。

## 1. 研究问题

- RQ1：谁发现跨成员依赖，谁寻找补足者，返回成果如何参与真实计算？
- RQ2：已有方法怎样处理错误输入、适用范围及依赖失效，依靠什么验证能力？
- RQ3：哪些选择能回应本项目失败，哪些只是重命名已试过的流程？

研究主线是局部知识/能力的实际利用。当前同模型私有资料首先证明信息或上下文互补；不把角色标签当成已校准的技能优势。部分成果既可能是数据、转换或计算，也可能是有条件的自然语言结果，不能强求所有任务变成程序。

## 2. 检索与核验

三个独立视角分别检索现代 LLM 分工/执行、经典黑板/条件推理、失败反证/实验方法。查询包括 multi-agent partial solutions / missing inputs / dependency binding、LLMCompiler / MetaGPT / ADaPT、blackboard / Contract Net / conditional arguments / ATMS，以及 multi-agent failure / scaling / multi-turn recovery；由主代理补查 Parsel、PAL 和任务基准。先广搜，再核读原文方法、附录与提示词。取证限会议/作者/机构原文；未按搜索摘要抄录效果数字。

下列三个机制分支以主要操作对象区分，论文可以跨分支；归属不意味着它只研究该对象。现代方法与经典机制不能因为抽象词相同就被判重复，也不能因为换成 LLM 就自动认定新颖。

## 3. 从实际工作到后续执行：产物交接不是空白

MetaGPT 将开发拆成模型生成的需求、接口和代码产物；LLMCompiler 则把依赖结果实际代入后续调用。前者说明“交付工作产物”已有直接实现，后者说明“返回结果进入操作输入”可通过程序实现；它们的主要依赖分别由预设 SOP 和 Planner 确定，不能据此推断私有知识成员已经能够发现未知的跨域连接。[MetaGPT](https://arxiv.org/html/2308.00352v6)，[LLMCompiler](https://arxiv.org/html/2312.04511v3)。

| 论文、作者与年份 | 核读位置与真实交接 | 对当前候选的启发和边界 |
|---|---|---|
| Hong 等，MetaGPT，ICLR 2024 | §3.1–3.3：SOP、消息池、订阅；模型生成 PRD、接口设计和代码 | 产物对下阶段有实际用途；角色及大部分交付关系预设，不证明开放依赖发现 |
| Kim 等，LLMCompiler，ICML 2024 | v3 §3.1–3.4：Planner 生成 DAG/占位符，Task Fetching Unit 代值，Executor 调工具，必要时重规划 | 调度和传值可机械完成；语义依赖由模型规划，工具定义由用户提供；工具也可以是 LLM Agent，并非只能是固定计算器 |
| Wang 等，Executable Code Actions Elicit Better LLM Agents，ICML 2024 | §2：生成 Python 动作、保留变量、调用工具、接收执行观察 | CodeAct 动作形式可不经训练采用；论文另有需训练的 CodeActAgent，不混为一谈。没有专门证明私有知识协作 |
| Zelikman 等，Parsel，NeurIPS 2023 | §2.1–2.3：层级自然语言函数描述、依赖函数实现与测试组合搜索 | 比单纯“代码作为产物”更近；测试只能验证覆盖的行为，不能充当本项目未提供的真实规则判定器 |

CodeAct 与 Parsel 都使中间工作成为可执行对象，但前者重在动作表示，后者重在分解后的实现与测试搜索；二者没有消除源资料理解的责任。PAL 更直接说明计算交给解释器即可带来收益，因此任何候选都必须让普通协作和强单体使用同样的计算工具，才有资格讨论额外的协作作用。[CodeAct](https://arxiv.org/html/2402.01030v4)，[Parsel](https://arxiv.org/html/2212.10561v3)，[PAL](https://proceedings.mlr.press/v202/gao23f.html)。

LLMCompiler Appendix B 还明确存在 DAG 连接错误、属性/单位错误以及拿到结果后作出错误最终判断。它支持程序保留工作作用的可行性，也直接反对“用了 DAG 就解决采用问题”。本报告不把论文总体提升归因于其中某一项未经隔离的因素。[原文](https://arxiv.org/html/2312.04511v3#A2)。

## 4. 谁发现可以接着做的工作：请求、自选与条件闭合

现代黑板论文把“谁能帮助”的选择交给熟悉本地文件的成员，Contract Net 更早允许响应者在承接任务时提出仍需的输入；条件论证和 DAREC2 则进一步规定补足如何改变原推理状态。它们提供四种不同能力：自选响应、声明缺口、接入支持、继续分布式推导。[黑板系统](https://arxiv.org/html/2510.01285v2)，[Contract Net](https://www.reidgsmith.com/The_Contract_Net_Protocol_Dec-1980.pdf)，[条件论证](https://www.ifaamas.org/Proceedings/aamas2012/papers/4C_2.pdf)，[DAREC2](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ICLP.2011.175)。

| 论文、作者与年份 | 核读位置和具体机制 | 可迁移部分；不可默认的能力 |
|---|---|---|
| Salemi 等，LLM-based Multi-Agent Blackboard System for Information Discovery in Data Science，v2，2026-01-31 | §3–3.2：主 Agent 发请求；文件 Agent 预先熟悉分区，自选响应；交付文件、加载及处理方案、样本 | 可借鉴本地资源熟悉度和自选响应。回复板只对主 Agent 可见，主要代码执行由主 Agent 完成；没有证明 helpers 彼此执行成果 |
| Smith，The Contract Net Protocol，1980 | §II、§IV-A：任务公告、eligibility、自选投标；投标可包含 REQUIRE；承接者可再分包 | 可根据局部能力响应，不要求协调者先知道正确专家；领域词汇和公告内容仍由设计者规定，获选不认证真值 |
| Erman、Hayes-Roth、Lesser、Reddy，HEARSAY-II，1980 | Problem-Solving Model，印刷页218–222：部分假设及其变化触发其他知识源的条件—动作 | 支持从中间状态主动接续，而非等主解题者询问。语音层级、对象和匹配程序预先设计 |
| Sá、Alcântara，Cooperative Dialogues with Conditional Arguments，AAMAS 2012 | §3–4、Example6：同伴证明所缺 L，将剩余条件更新为 (E1−{L})∪E2 并接入支持 | 部分工作可继续有条件；共享本体、通信语言与形式知识已具备，不包含开放文本语义匹配保证 |
| Ma、Russo、Broda、Lupu，DAREC2，ICLP 2011 | §3.1、§4：剩余目标、变量替换、假设/约束、待检查状态；§4.2.2 helpfulness 与§4.2.5黄页 | 有实际路由机制，不能称其不解决路由；但路由发生在预先约定的符号谓词上，名字冲突已被假定解决 |

HEARSAY-II 从部分解变化触发工作，Contract Net 从公告触发响应；二者都启发“做得出哪一步，由掌握局部资源的人参与识别”。本项目可以据此允许成员主动发布工作及其缺口，也允许响应别人的缺口，而不预先生成整张全局任务图。这个选择是设计推论，尚未成为已验证的 LLM 协调算法。[HEARSAY-II](https://mas.cs.umass.edu/Documents/Erman_Hearsay80.pdf)，[Contract Net](https://www.reidgsmith.com/The_Contract_Net_Protocol_Dec-1980.pdf)。

DAREC2 与条件论证都能接续未完工作，但依赖共同符号和指定逻辑语义。它们没有消除我们最难的两个判断：成员是否找对所缺输入，以及两个来源是否在谈同一个对象、范围和时点。为此，设计必须保留原件并让实际使用某输入的成员明确建立连接，不能把字符串相等当成语义成立。

### 补充近邻：交接边上的澄清

Lin 等的 AgentAsk（ACL 2026，§4、Appendix A/F）直接处理消息交接：外部澄清器读取局部上下文，决定是否问、问谁、问什么，并通过监督学习及强化学习优化。因而“把需求判断移到局部交接”“问一个具体缺失量”也不能单独作新颖性。相较这种交接修复，当前候选要检验的是：尚未闭合的局部工作作为持久对象保留，补足结果绑定后继续原操作。相较 LLMCompiler，这项工作和需求从分散资料的局部操作中逐步形成；这些是作用对象和执行流程的差别，是否产生额外价值仍待对照。无训练和无需外部澄清器是资源/实现选择，不能单独证明学术创新。[AgentAsk原文](https://aclanthology.org/2026.acl-long.1294.pdf)，[LLMCompiler](https://arxiv.org/html/2312.04511v3)。

## 5. 错误如何传播，哪些更新具有真实含义

ATMS 为结论维护不同支持环境，错误支持失效时保留其他路径；ADaPT 则在执行者报告失败后改变任务粒度。前者处理给定依赖的维护，后者处理工作分解，但两者都依赖外部提供的关键判断：ATMS 不解释命题语义，ADaPT 的自评也可能误报成功。[ATMS](https://dekleer.org/Publications/An%20Assumption-Based%20TMS.pdf)，[ADaPT](https://aclanthology.org/2024.findings-naacl.264/)。

| 来源 | 实际支持的判断 | 对设计的约束 |
|---|---|---|
| de Kleer，An Assumption-based TMS，1986，§4 | 依赖、支持环境、nogood 传播；结构匹配由 problem solver 完成 | 输入错误、连接错误、规则错误应分开版本化；不把 LLM 怀疑直接升级为永久排除 |
| Prasad 等，ADaPT，Findings NAACL 2024，§3、Appendix F | 失败后递归分解可改变任务难度；WebShop 自评有明显高估 | 实际缺输入可以触发接续，自报“完成/通过”不能独立作为正确性证据 |
| Zhang 等，Chain of Agents，NeurIPS 2024，§3、§5.8、Appendix F.4 | 局部阅读与推理在固定链中接续；自然语言交接也可有效，但错误/无关 CU 会继续传播 | 可组合不要求全部代码化；固定链能否替代按依赖接续，是对照问题，不是理论保证 |
| Cemri 等，Why Do Multi-Agent LLM Systems Fail?，v3，2025 | §4–5、Appendix H：设计、成员错配、验证等多个失败层；干预收益依系统而变 | 不把所有错误归最后接收者；不能从发现失败标签直接推出某个干预有效 |
| Kim 等，Towards a Science of Scaling Agent Systems，v3，2026-04-08 | §4–5：任务结构、模型能力和协调开销相关；版本和统计条件重要 | 固定预算并保留强单体。错误传播指标不是任务失败概率倍率，也不是本候选的因果定律 |
| Laban 等，LLMs Get Lost In Multi-Turn Conversation，v1，2025 | Full/Concat/Sharded 和补救对照：渐进披露与早期承诺可能损害后续处理 | 同时改变旧稿可见性、证据完备度和协作形式时，不能唯一归因给依赖接续 |

MAST 对不同系统干预表现不一，Scaling 对不同任务表现也不同；这些证据共同支持选择具体瓶颈和公平预算，不能据其整体判断多 Agent 必定有效或无效。[MAST](https://arxiv.org/html/2503.13657v3)，[Scaling](https://arxiv.org/html/2512.08296v3)。同样，Lost in Conversation 研究的是用户多轮披露，不等于本项目的多成员机制；其价值是揭示应分开控制的因素。[原文](https://arxiv.org/html/2505.06120v1)。

## 6. 与本地记录交叉后得到什么

1. 直接局部应用70次中普通3/8、应用2/8，实际交付主要是理由/选项替换。因此不能再把“让帮助者应用知识”当作本轮新机制；可检验差别是缺少跨域输入时仍保留操作，并在补全后继续执行。[本地结果](../../runs/local-application-probe-live-20261025-r1/RESULTS.md)
2. 固定贡献整合两组11/12，且两组都能完成核心计算。简单、完整披露的任务并不天然需要新协调；不能禁止基线自行计算来制造差距。[本地结果](../../runs/local-rule-adoption-live-20261025-r1/RESULTS.md)
3. 条件提交历史任务4/6，事后直接执行固定初始表也是4/6。这支持保留可用程序组合，却不支持新增接收者审查的价值；事后回放不是预注册新实验。[分析](../../runs/constraint-commit-live-20261027-r1/FURTHER_ANALYSIS.md)
4. 011 当前未就绪被编码为任务截止前不就绪，说明程序可以稳定执行错误解释。新接口必须避免默认未知为false，但不能承诺结构化就能解决时态语义。[同上](../../runs/constraint-commit-live-20261027-r1/FURTHER_ANALYSIS.md)

## 7. 综合判断及未解决点

对 RQ1，最可借用的执行骨架是：部分工作触发具体缺口、局部成员自选响应、消费方绑定到具体输入、程序传值续算；没有必要再添加一个全局语义裁判。对 RQ2，应区分数据、连接和局部操作的修订，只失效其下游；但原文含义、规则适用性仍须模型/可靠外部工具判断，不能从形式维护取得真值保证。对 RQ3，本轮应研究“从局部工作实际暴露依赖并接续”，而不是增加理由字段、置信度或硬化候选排除。

候选的未解决点有明确范围：隐含输入是否能自然暴露，输入语义能否对齐，错误操作是否会被程序放大，新增交接是否值得成本。黑板、条件论证、数据流与测试都可作基础；研究贡献要由这些组合是否解决上述具体困难来判断。

## 参考来源与阅读范围补充

上述方法链接均为作者/会议/机构原文；并行阅读视角的取证由主代理综合，属于同一助手团队的研究，非独立外部复现。未下载/执行各论文代码，未核对全部论文实验数字。

- CodeAct：Wang 等，2024，[v4 §2–3](https://arxiv.org/html/2402.01030v4)。
- Parsel：Zelikman 等，2023，[v3 §2](https://arxiv.org/html/2212.10561v3)。
- ADaPT：Prasad 等，2024，[正式稿](https://aclanthology.org/2024.findings-naacl.264.pdf)。
- Chain of Agents：Zhang 等，2024，[NeurIPS正式稿](https://papers.nips.cc/paper_files/paper/2024/file/ee71a4b14ec26710b39ee6be113d7750-Paper-Conference.pdf)。
- DAREC2：[正式全文§3–4](https://drops.dagstuhl.de/storage/00lipics/lipics-vol011-iclp2011/LIPIcs.ICLP.2011.175/LIPIcs.ICLP.2011.175.pdf)。
- ATMS：[作者原稿§4](https://dekleer.org/Publications/An%20Assumption-Based%20TMS.pdf)。本轮已取得1986原文，超出此前只读1988修订稿的范围。
- 可比任务候选：Zhu 等，TAT-QA，ACL 2021，[正式记录](https://aclanthology.org/2021.acl-long.254/)。原生表格/段落和数值推理适合考查输入连接；原基准不是多 Agent 专长基准，改成分散资料必须说明构造，不能直接沿用其名义声称已验证专长。
