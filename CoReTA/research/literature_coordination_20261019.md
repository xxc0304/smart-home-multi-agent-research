# 协作机制文献核查：黑板、异构推理、分歧与内容过滤

日期：2026-10-19。范围：primary paper + 作者公开代码；未改运行协议，未做模型调用。代码链接为当日 main 分支，未固定提交，不应直接当复现锁定版本。

## 1. Salemi et al., LLM-based Multi-Agent Blackboard System for Information Discovery in Data Science

- 版本：arXiv:2510.01285v2，2026-01-31；初版 2025-09-30。
- [全文](https://arxiv.org/html/2510.01285v2)，§3、Appendix C–E；未从论文识别到作者实现仓库，代码未核实。
- **实际机制**：数据湖划分给 file agents，各自离线学习文件结构；search agent 有网页检索能力。主 Agent 按 ReAct 选择计划、推理、代码执行、广播求助或回答。Helper 自判断能否回应；其响应独立放入主 Agent 专属 response board，防止彼此影响。主 Agent 用响应继续生成/执行程序。最大 10 个动作，搜索最多 3 步。
- **互补来源**：分区数据与工具访问不同，非同一输入的三个完整答案。Appendix E 的跨分区文件例子中，三个 helper 提供不同文件地址、结构、载入与预处理信息，合起来覆盖所需文件。
- **核验/停止**：代码执行返回真实输出/错误；是否求助与回答仍由主 Agent 判断。无响应时可重述请求、换策略或结束。
- **证据边界**：证明任务中的分布式信息发现/使用有价值，不证明三个同模型、同信息初稿均错后能靠局部推理组合成功。不能只复制广播格式而丢掉其信息互补与执行反馈条件。

## 2. Chen, Saha, Bansal, ReConcile: Round-Table Conference Improves Reasoning via Consensus among Diverse LLMs

- arXiv:2309.13007；[全文](https://arxiv.org/html/2309.13007)，[作者代码](https://github.com/dinobby/ReConcile)。
- **论文机制**：不同模型各出 answer/reasoning/confidence，讨论时按答案分组提供各方解释、置信度，以及能纠正对应模型的 human-explanation demonstrations；各自重解，最后用置信加权投票。
- **互补来源**：不同模型与解释方式；对“如何说服具体成员”的 few-shot 教学，而非只要求角色不同。
- **证据边界**：C.4 说 Bard、Claude2 初始错后纠正，未建立三个成员均错。无运行时外部真值核验；解释说服力和置信度不等于正确。
- [run.py](https://raw.githubusercontent.com/dinobby/ReConcile/main/run.py)：`--round` 默认 2，先三模型初稿，再 `claude_debate/gpt_debate/bard_debate`，每轮清洗与解析。
- [utils.py](https://raw.githubusercontent.com/dinobby/ReConcile/main/utils.py)：`parse_output`（143–174）按答案分组；仅在存在不同答案时构造 `debate_prompt`；`trans_confidence` 是分段映射，非事实检验。
- [generation.py](https://raw.githubusercontent.com/dinobby/ReConcile/main/generation.py)：`*_debate` 仅对非空讨论 prompt 生成，要求解释同意/不同意的观点及原因，输出 `{reasoning, answer, confidence_level}`。因此一致错误可能不进入讨论。不同错误答案有机会继续推理，但代码机制本身不保证组合出新解。

## 3. DMAD, Breaking Mental Set to Improve Reasoning through Diverse Multi-Agent Debate

- 作者仓库标注 ICLR 2025；[官方仓库](https://github.com/MraDonkey/DMAD)；[论文入口](https://openreview.net/forum?id=t6QHYUOQL7)。OpenReview 全文被浏览器验证阻断，本条依据作者代码与说明，不能称已读完整论文。
- **实际机制**：给成员不同计算过程，而非不同身份：IO 直接解；CCoT 先建 scene graph；DDCoT 先列 subquestions/subanswers 再解。后续读其他方法的答案并按自己的方法再生成。
- [main_DMAD.py](https://raw.githubusercontent.com/MraDonkey/DMAD/main/main_DMAD.py)：`construct_message` 明确切换三种方法；主程序固定三成员、三轮，round0 读已有输出；CCoT/DDCoT 后续先更新中间表示、再调用模型作答。MM-Vet 分支最终选一个已有候选，非局部拼接证明。
- [reasoning.py](https://raw.githubusercontent.com/MraDonkey/DMAD/main/reasoning.py)：`create_ddcot_create_subquestions_prompt`、`create_ddcot_answer_with_subquestions_prompt`，及 scene-graph 两步构造。
- [prompt.py](https://raw.githubusercontent.com/MraDonkey/DMAD/main/prompt.py)：显示子问题/子答案与图结构的具体中间表示。
- **证据边界**：作者展示例中 DDCoT 成员已经答对，其他成员受启发；不可说此例证明全员初错后组合成功。Scene graph 适用图像，不能原样移植数学/代码。

## 4. Cui et al., Free-MAD: Consensus-Free Multi-Agent Debate

- arXiv:2509.11035v1，2025-09-14；[全文](https://arxiv.org/html/2509.11035)，§4、Algorithm1、Appendix E。找到社区实现，但未验证为论文作者代码，故不将其当原实现。
- **机制**：初答后单轮讨论，引导只因具体理由改变答案、不追求一致；最终按整个轨迹中保持/放弃/新采用答案进行权重更新，选累计最高答案。
- **互补来源**：独立推理与抑制从众，保留可能正确的少数意见。
- **检查边界**：反从众指令并非外部 verifier；改口被当成更可信的启发式，不是内容正确性的证据。主要是轨迹上的整答案选择；虽然讨论可以产生新答案，它没有定义 CoReTA 所需局部贡献连接机制。
- **可借鉴**：采纳必须明确指出原推理哪里错、新证据如何纠正；保留被拒贡献及理由。不要把其轨迹权重直接当步骤置信度或正确性分数。

## 5. Tian et al., Multi-Agent Debate with Memory Masking (MAD-M²)

- arXiv:2603.20215，2026；[全文](https://arxiv.org/html/2603.20215)，§3、Appendix D；[论文链接的官方代码](https://github.com/tmlr-group/MAD-MM)。
- **机制**：同模型多次 CoT 初答，每次讨论前过滤上轮记忆。Subjective 用 YES/NO/NOT SURE 判断保留，strict 控制未知是否删除；论文 objective 说保留最低 perplexity；过滤后重新推理，最后投票。
- **互补来源**：同模型采样与上下文筛选，重点在减少错误传播；不是不同能力的定向路由。
- **证据边界**：主观过滤仍可能漏/误删；低 perplexity 非真值。没有证明局部组合产生新正确解。论文不同模型、任务的过滤收益并不一致。
- [multi_agent_debate.py](https://raw.githubusercontent.com/tmlr-group/MAD-MM/main/multi_agent_debate.py)：`main` 实例化 `MultiAgentDebate(...prune_strategy, strict)`。
- [src/reasoning_models.py](https://raw.githubusercontent.com/tmlr-group/MAD-MM/main/src/reasoning_models.py)：`__call__` 固定 `max_round`；`_subjective_prune` 真正将被拒响应移出下一轮 context，非仅写审查评价；`prompts_with_format` 在 context 空时回退 CoT。`_objective_prune` 用 `ppl > median`，与论文文字不可直接对照，必须进一步追踪 models.py 数值定义后才判断是否反向；本次未下 bug 结论。

## 对 CoReTA 的可行借鉴（研究建议，非已验证改进）

1. **主动生产可互补的中间材料**：从 DMAD 借“不同解题过程”，而非贴专家标签。数学可候选构造/约束推导/反例与边界检查，代码可算法不变量/实现/性质与边界检查。哪些划分适用必须按任务验证，不能预先保证互补。
2. **请求与可交付物一一对应**：从 Blackboard 借局部需求、可否帮助自评、独立回应及无响应时重述。若同信息设置不设私人数据/工具，就应明确测的是推理过程互补，不能照搬它的信息互补解释。
3. **内容检查必须改变后续状态**：从 MAD-M² 借隔离/过滤错误材料的操作效果；CoReTA 应保留 disputed 状态和检查依据，避免把 accepted/resolved 当正确。机械检查可核验变更步骤、引用与约束；语义核验须具体计算/推导/公开自建测试，不得用隐藏评测答案反馈。
4. **采纳要能解释连接**：从 ReConcile 的 corrective explanations 借鉴“解释原错点与新关系”的示范，但不复制其一致即停规则。CoReTA 的增量价值仍须靠新解的步骤来源、贡献移除/替换对照等证据验证。
5. **不把求助次数当收益**：文献中大量系统默认讨论轮，解决了是否启动的控制问题，但没有保证讨论有效。可把固定一次缺口审查与自适应请求分开，仍允许无有效缺口时结束；这属于待比较设计，不是文献已证明的万能方案。

## 与用户目标的关系

这些论文给出生成不同材料、交换理由、筛掉错误和整合信息的方法。已核查证据不支持宣称它们都证明了“同一题全员独立失败，靠不同局部贡献共同构造出正确新解”。CoReTA 应把该现象作为单独的经验验证对象，排除整答选择、独自重解与隐藏评分反馈三种解释。
