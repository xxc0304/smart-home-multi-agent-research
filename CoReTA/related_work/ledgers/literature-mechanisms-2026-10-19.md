# 优势互补机制文献与官方实现核查：分工、局部交付与反馈

日期：2026-10-19。范围：AgentVerse、MetaGPT、ChatDev，以及较新的 Puppeteer。仅核查原论文、作者官方仓库；没有改动 CoReTA 运行代码、调用实验模型或启动实验。

## 阅读边界

- 这里的“互补”要区分：不同职责依次完成子任务、检查纠错、选择更好整解、不同局部推理合成为新解。它们可以共同存在，但不能相互代替作为证据。
- 本次核查的总分与消融没有直接建立我们所需的“同一题上全部独立初稿未通过，而局部联合后通过，且可追溯各贡献连接”的条件统计。借鉴机制有依据，断言机制已证明我们的特定目标没有依据。
- 代码读自当日官方分支。ChatDev 特意使用 `chatdev1.0`，避免把 2026 年主分支 DevAll 当作 ACL 2024 原实现；MetaGPT 当前 main 已有 RoleZero 等后续演化。以下区分论文方法与当日代码，不声称代码精确复现论文版本。
- GitHub tree API 被公共 IP 限流；官方 raw 文件读取成功。未获得提交 SHA，因此正式复现时仍应固定历史提交。

## 1. AgentVerse：异议触发修订，评价反馈进入下一轮配置

**书目信息已核对：** Weize Chen、Yusheng Su 等，*AgentVerse: Facilitating Multi-Agent Collaboration and Exploring Emergent Behaviors*，arXiv:2308.10848；官方仓库确认 ICLR 2024。论文 [摘要与作者](https://arxiv.org/abs/2308.10848)，[全文](https://arxiv.org/pdf/2308.10848)，[作者仓库](https://github.com/OpenBMB/AgentVerse)。

**论文定位：** §2.1–2.4、§3.1–3.2、附录 A。招募者根据任务及评价意见生成角色，solver 提交方案，critics 评价，solver 修订，evaluator 决定反馈。GPT-3.5-Turbo-0613/GPT-4-0613、零样本；任务包括 MGSM 英语子集、逻辑谜题、HumanEval、受约束生成等。论文承认错误批评可伤害数学成绩；GPT-4 HumanEval 增加了生成单测并执行的环节。这不是所有任务都有的工具条件。

**直接读到的实现：**

- [`vertical_solver_first.py`](https://raw.githubusercontent.com/OpenBMB/AgentVerse/main/agentverse/environments/tasksolving_env/rules/decision_maker/vertical_solver_first.py)：`VerticalSolverFirstDecisionMaker.astep` 先运行 solver，再并行运行 reviewers。过滤同意或空意见；有非空异议就广播，并调用 solver 修订。无异议才提前结束；类默认内循环上限 3。这是程序安排的审查与修订，不由 solver 自行决定是否请求第一轮审查。
- [`basic.py`](https://raw.githubusercontent.com/OpenBMB/AgentVerse/main/agentverse/environments/tasksolving_env/basic.py)：`BasicEnvironment.step` 串接 role_assign→decision_making→execute→evaluate；外部轮次由成功标记或 max_turn 截止。
- [HumanEval GPT-3.5 config](https://raw.githubusercontent.com/OpenBMB/AgentVerse/main/agentverse/tasks/tasksolving/humaneval/gpt-3.5/config.yaml)：critic 要给出错误及修正；evaluator 输出分数和修正/招募建议；`executor.type=none`。
- [HumanEval GPT-4 config](https://raw.githubusercontent.com/OpenBMB/AgentVerse/main/agentverse/tasks/tasksolving/humaneval/gpt-4/config.yaml)：`executor.type=code-test`；测试者根据题面自生成测试；evaluator 看代码及执行结果。配置是 4 agents、max_turn 2；辅助招募者/执行者/评价者也占调用，不能把“4”当成总模型调用数。

**对 CoReTA 的借鉴判断（本项目推论）：** 有内容的异议应该成为需要显式处理的对象，不能随一句整体认可消失；评价应明确影响下轮工作。不能照搬 evaluator 的自评分充当真实正确性，也不能把角色描述当作经过验证的专长。其 solver 修订链仍可能靠独自重解，不自动等于局部互补。

## 2. MetaGPT：不同职责对应不同中间交付物，交付物有依赖

**书目信息已核对：** Sirui Hong、Mingchen Zhuge 等，*MetaGPT: Meta Programming for a Multi-Agent Collaborative Framework*，arXiv:2308.00352。论文 [摘要与作者](https://arxiv.org/abs/2308.00352)，[所读 v6 全文](https://arxiv.org/html/2308.00352v6)，[作者仓库](https://github.com/FoundationAgents/MetaGPT)。

**论文定位：** §3.1–3.3、§4、附录 B/C。产品经理产出 PRD，架构师产出接口和调用关系，项目经理产出任务依赖，工程师实现，QA 检查。共享消息池及订阅控制相关交付。执行反馈版写并运行自生成单测，失败后调试，上限 3 次。评估包含 HumanEval、MBPP、SoftwareDev；GPT-4 为主要后端，另有 GPT-3.5、DeepSeek Coder 33B 对比。结果混合了任务分解、专门提示和在线执行收益，不能只归于“互补”。

**直接读到的实现：**

- [`design_api_an.py`](https://raw.githubusercontent.com/FoundationAgents/MetaGPT/main/metagpt/actions/design_api_an.py)：`ActionNode` 明确 `key / expected_type / instruction / example`；字段包含实施方案、文件列表、数据结构和接口、调用流程、未澄清事项。接口与流程应一致。
- [`project_management_an.py`](https://raw.githubusercontent.com/FoundationAgents/MetaGPT/main/metagpt/actions/project_management_an.py)：逻辑分析列出文件与类/函数及依赖；任务列表按依赖排序；另有 API 规范、共享知识。这些字段约束的是可交接的产物，而非仅给三个角色换名字。
- [`design_api.py`](https://raw.githubusercontent.com/FoundationAgents/MetaGPT/main/metagpt/actions/design_api.py)：`WriteDesign` 接收 PRD，保存结构化设计及依赖，生成接口/调用图资源，发布带变更文件名的消息。
- [`project_management.py`](https://raw.githubusercontent.com/FoundationAgents/MetaGPT/main/metagpt/actions/project_management.py)：`WriteTasks` 读取设计、生成并保存任务文档与依赖，发布任务输出。
- [`roles/project_manager.py`](https://raw.githubusercontent.com/FoundationAgents/MetaGPT/main/metagpt/roles/project_manager.py)：当前代码用 RoleZero；固定 SOP 的 `set_actions / _watch` 标注只在启用固定 SOP 时生效。因此不能用 main 这几行直接宣称历史论文始终如此调度。

**对 CoReTA 的借鉴判断（本项目推论）：** 局部贡献应包含“输入前提—输出结论—供哪个后续步骤使用”，共同构造应检查接口、假设和依赖是否连接。对数学题应转成引理/构造/边界条件，不能生硬复制 PRD 或 OpenAPI 字段。引入生成测试会改变当前无在线工具设定，若采用应作为明确的新条件并给对照同等权限。

## 3. ChatDev：工作流规定要完成的子任务，意见和修订分阶段

**书目信息已核对：** Chen Qian、Wei Liu 等，*ChatDev: Communicative Agents for Software Development*，ACL 2024，15174–15186。正式 [论文记录与作者](https://aclanthology.org/2024.acl-long.810/)，[全文](https://aclanthology.org/2024.acl-long.810.pdf)，[原版代码分支](https://github.com/OpenBMB/ChatDev/tree/chatdev1.0)。

**论文定位：** §3.1 chat chain、§3.2 communicative dehallucination、§4.2 消融。设计→编码/补全→静态审查/动态测试，每个子任务由 instructor/assistant 完成交接；缺少信息时先澄清再回答。实验使用 ChatGPT-3.5、temperature 0.2、Python 3.11.4 执行反馈，评估软件完成度、可运行性与需求一致性等。消融支持角色与阶段流程在该设置下有贡献，不等于证明独立初稿全部错时的联合推理。

**直接读到的实现：**

- [`ChatChainConfig.json`](https://raw.githubusercontent.com/OpenBMB/ChatDev/chatdev1.0/CompanyConfig/Default/ChatChainConfig.json)：默认链安排 CodeReviewComment→CodeReviewModification，最多 3 个 cycle；TestErrorSummary→TestModification 最多 3 个 cycle；CodeCompleteAll 最多 10 个 cycle。它没有把是否进入这些阶段全部交给主模型的可选求助动作。
- [`PhaseConfig.json`](https://raw.githubusercontent.com/OpenBMB/ChatDev/chatdev1.0/CompanyConfig/Default/PhaseConfig.json)：审查者针对规则逐项检查，提交最高优先级意见与修正建议；程序员下一阶段消费具体 comments 更新代码。测试修订阶段使用 test_reports 和 error_summary。此处的“局部”主要是具体问题/修改目标，输出仍可能重写全部代码。
- [`composed_phase.py`](https://raw.githubusercontent.com/OpenBMB/ChatDev/chatdev1.0/chatdev/composed_phase.py)：`ComposedPhase.execute` 执行配置循环并写回共享环境；CodeReview 根据完成标记提前退出，Test 根据 bug 标记退出。固定阶段也允许早停，不能描述成强迫无意义交流。
- [`phase.py`](https://raw.githubusercontent.com/OpenBMB/ChatDev/chatdev1.0/chatdev/phase.py)：每阶段填充共享状态、执行对话、提取结论并更新环境；代码产物通过 `update_codes / rewrite_codes` 落盘，阶段交付是下一阶段输入。

**对 CoReTA 的借鉴判断（本项目推论）：** “提出局部问题”和“解决并应用这个问题”应作为可核对交接；借鉴工作流依赖并不意味着必须强制增加求助次数。已有 CoReTA bootstrap 审查本来就是安排好的阶段，仅新增一次 reviewer 可能只重复现有步骤，应先明确新增交付内容。

## 4. Puppeteer：先设计不同操作，再训练调度，而非自由角色聊天

**较新文献检索所得，书目信息已核对：** Yufan Dang、Chen Qian 等，*Multi-Agent Collaboration via Evolving Orchestration*，arXiv:2505.19591（2025）；官方仓库首页注明 NeurIPS 2025。原始 [摘要与作者](https://arxiv.org/abs/2505.19591)，[v1 全文](https://arxiv.org/html/2505.19591v1)，[作者代码](https://github.com/OpenBMB/ChatDev/tree/puppeteer)。

**论文定位：** §2.1–2.2、§3 Implementation Details。中心策略根据当前状态选择下一成员；成员分别执行分解、批评、反思、修正、总结/终止等操作；用 RL 根据终局质量及成本学习调度。GSM-Hard、MMLU-Pro、SRDD、CommonGen-Hard；既有混合模型池，也有同模型 Mono 条件；含代码、搜索、文件等工具，输出还使用多数聚合。其提升需要考虑策略训练和工具条件，并非仅换一段调度提示就能复用。

**直接读到的实现与限制：**

- [`puppeteer/README.md`](https://raw.githubusercontent.com/OpenBMB/ChatDev/puppeteer/README.md)：运行需配置模型策略权重（70B reward-model base）、图探索深度/并行路径、工具与 API；提供训练与评估入口。默认说明与论文实验参数不完全相同，不能互换。
- [`personas/personas.jsonl`](https://raw.githubusercontent.com/OpenBMB/ChatDev/puppeteer/puppeteer/personas/personas.jsonl)：实际注册 planner、reasoner、critic、reflector、questioner、summarizer、concluder、modifier、terminator，以及文件/搜索/Python 成员；各自绑定具体 actions。多数思考成员为 GPT-4o，若干工具/终止成员为 gpt-3.5，与 README“默认 GPT-4o”不能简单等同全员同模型。
- [`main.py`](https://raw.githubusercontent.com/OpenBMB/ChatDev/puppeteer/puppeteer/main.py)：可核验任务入口、personas 文件路径和策略配置；本次未深入训练器全链，也没有复跑，故不提供“作者代码已完整复现论文 RL”判断。

**对 CoReTA 的借鉴判断（本项目推论）：** 借鉴“成员操作有明确功能、调度基于任务状态和历史贡献”；暂不直接引入 RL 或庞大模型池。不同操作是否产生有效局部互补，以及无需训练的调度能否可靠，都是我们需要验证的假设。

## 汇总：哪些做法有文献依据，哪些仍是我们的研究假设

| CoReTA 需要补实的机制 | 已核实先例 | 可以借鉴的实现原则 | 尚不能当作事实的部分 |
|---|---|---|---|
| 不同成员产生不同可用材料 | MetaGPT 交付物；Puppeteer actions | 定义具体操作与产物，而不只定义角色名 | 同一模型按不同提示就必然形成有效多样性 |
| 缺口进入实际后续处理 | AgentVerse 异议→修订；ChatDev 审查意见→修改 | 使问题有明确下游消费者、处置及结果 | 更具体的缺口字段必然提升求助质量 |
| 局部贡献能连接成完整解 | MetaGPT 接口/依赖；ChatDev 阶段交接 | 明确前提、结果、依赖、应用位置和冲突 | 满足结构化接口即可保证语义正确 |
| 新依据经过核验 | MetaGPT 可执行反馈；AgentVerse GPT-4 HumanEval；ChatDev 测试阶段 | 将证据来源和可复核操作与评价分开 | 同模型 reviewer 的认可等于核验；自生成测试等于金标准 |
| 根据结果调整分工 | AgentVerse 评价→下一轮；Puppeteer 学习策略 | 保留未解决问题与历史操作效果，影响下一动作 | CoReTA 无训练调度能达到已训练策略的效果 |

**建议交付顺序（尚未实施）：** 先由主研究笔记对照这些来源修订架构机制表，逐项写清触发、输入、产物、检查、写回、下一动作和对照；然后定稿一个小改版。保留无工具主设定时先不借入在线执行收益；若采用在线生成测试，明确增加公平对照和独立离线评分。最终用同题独立解、协作解与贡献消融来判断联合完成；不要用零求助或总分相同单独判定整套互补机制无效。
