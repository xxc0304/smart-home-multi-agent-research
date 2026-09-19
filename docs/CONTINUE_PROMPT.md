# 跨设备继续讨论提示词

请读取这个项目仓库的 `README.md`、`docs/PROJECT_CONTEXT.md`、`docs/RESEARCH_HANDOFF.md`、`docs/LITERATURE.md`、`docs/SMART_HOME_AGENT_SURVEY.md` 和 `docs/EXPERIMENT_PLAN.md`，再继续讨论智慧家庭多 Agent 研究。

当前背景：我负责智慧家庭项目中多 Agent 协同编排方向。项目采用主调度 Agent、专业 Agent／Skill、Home Assistant 确定性执行器和云边端分层。实际部署强调本地实时控制、断网可用和安全优先。第一篇论文暂定为 HomeCoord-Bench，核心问题是：多个专业 Agent 异步作用于动态共享家庭环境时，协调机制减少动作冲突需要付出多少响应时延和任务效用？选择性修复、模型路由和预测执行保留为后续方法方向。

当前验证进度：已经实现 4 条种子 episode、11 条参数化变体、C1–C4 确定性评测器、CentralSingleAgent／IndependentMultiAgent／RuleCoordinator 三种闭环和 DeepSeek API 适配。6 个关键配置各重复 5 次后，发现共享策略提示不能稳定消除冲突，低优先级 Agent 先返回会破坏简单优先级规则。规则协调器增加待决高优先级检查后，在直接冲突配置中复测 5/5 过程有效、0 次 C1；相比独立架构，首动作中位数约增加 129 ms，任务服务率从 100% 降至 50%。这些仍是校准结果，不是论文统计结论。请先读 `docs/VALIDATION_LOG.md` 和 `homecoord_bench/results/`。

当前文献清单已整理为本轮讨论的 19 篇论文。除 HomeBench、SimuHome、SMH-Bench、PersonalHomeBench、SAGE、HomeFlow 等家庭工作外，还包括 DynTaskMAS、REALM-Bench、SagaLLM、ALAS、SyncPlan、VeraRAN、Agent JIT Compilation、Speculative Actions、Win Fast or Lose Slow、HearthNet、When Do LLM Agents Help? 和 Agentic Fast-Slow Planning。LLMCompiler 与 Multi-Agent Path Finding with Deadlines 作为补充背景，不计入 19 篇。

目前另行保留低延迟方向 HomeSpec：面向多 Agent 家庭自动化的风险与截止时间感知预测式协同执行。它借鉴 Speculative Actions 的“预测—并行准备—状态验证—提交／丢弃”机制，但不直接提前执行危险物理动作。研究重点是低风险工具预取、状态版本和资源租约、预测分支动态选择，以及预测失配后的受影响子图局部修复。建议采用“本地预授权策略保证首个安全动作＋快速 Speculator 准备后续步骤＋慢速主 Agent 权威确认”的三层架构。

请遵循这些边界：

1. HomeBench、SimuHome 说明垂直场景可以承载一般 Agent 问题，但不要把它们的录用原因说成已知事实。
2. SyncPlan 已覆盖一次联合规划、异步执行、等待、死锁检测和计划过期重规划；Agent JIT、LLMCompiler 已覆盖计划编译和并行工具执行；因此不要把这些单独包装成新颖性。
3. 当前真正待验证的增量是“有限截止时间、部分动作已执行、跨 Agent 干扰下的选择性计划修复和思考预算分配”。把它称为候选问题或假设，除非新检索证明更强结论。
4. 区分事件检测、首次有效物理动作和完整任务完成；项目方案中的毫秒／秒级数字是目标，不是实测。
5. 给出强规则基线、跨场景或抽象仿真验证、P95/P99 延迟、过程安全和错误拒绝率，避免只比较一个朴素 ReAct 基线。

优先帮助我回答：现有强基线是否已经解决 MVP；局部修复如何形式化；哪些动态冲突能稳定暴露现有方法的缺陷；以及该工作更适合 benchmark、方法论文还是部署系统论文。
