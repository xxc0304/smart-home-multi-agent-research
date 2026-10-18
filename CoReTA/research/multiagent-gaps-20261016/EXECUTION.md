# 执行与组织视角：从可运行工作流到可靠共同执行

检索截止：2026-10-16。问题冻结为：自动组织何时帮助真实执行？局部修复何时破坏全局目标？现有评测能否区分调度收益与语义正确性？下列六篇均核过第一方标题、作者与摘要；关键边界进一步读原文。仅检索，无实验和付费调用。

## 证据底座与反方

| 核实的论文 | 原文发现及边界 |
|---|---|
| Junwei Yu, Yepeng Ding, Hiroyuki Sato，2025，[DynTaskMAS: A Dynamic Task Graph-driven Framework for Asynchronous and Parallel LLM-based Multi-Agent Systems](https://ojs.aaai.org/index.php/ICAPS/article/view/36130) | 动态任务图、异步执行与自适应管理已存在；报告执行时间降低21–33%，扩到16代理接近线性吞吐。故“动态分工/异步编排”本身不是空白。这里只把这些当作者实验范围内结论。 |
| Abubakarr Jaye 等，2026，[CORPGEN: Simulating Corporate Environments with Autonomous Digital Employees in Multi-Horizon Task Environments](https://arxiv.org/html/2602.14229v1) | 并发长程任务已有问题定义、隔离子代理和层级规划。§5.4承认应用状态误判、重复失败、持久员工开销；部分跨应用设置没有改善。作者明确定位为受控合成研究环境。 |
| Kou Shi, Ziao Zhang, Shiting Huang, Avery Nie 等，2026，[AsyncTool: Evaluating the Asynchronous Function Calling Capability under Multi-Task Scenarios](https://arxiv.org/html/2605.27995v3) | 延迟反馈评测已存在；正确切换比频繁切换重要。主要组合是2/3任务，每个子任务有独立隐藏状态；正文称4任务难度显著上升。作者局限为来源工具覆盖与生成标注成本。 |
| Shuaike Shen, Wenduo Cheng, Shike Wang, Mingqian Ma, Jian Ma，2026，[AgentCo-op: Retrieval-Based Synthesis of Interoperable Multi-Agent Workflows](https://arxiv.org/html/2605.20425v1) | 已组合独立代理、类型化产物和有界局部修复。§5明确：只做两项基因组案例；中间产物难验证；局部修复不保证全局最优。因此“异构代理可组合”不能充作新颖性。 |
| Neeraj Bholani，2026，[Graph-Based Self-Healing Tool Routing for Cost-Efficient LLM Agents](https://arxiv.org/pdf/2603.01548) | 工作论文，以确定性最短路径处理工具故障；19场景控制面调用比ReAct少93%。关键作者限定在p15：验证的是控制流性质，未验证真实工具输出下部分故障或畸形响应的语义正确性；p9也区分静态权重实验与尚未验证的生产设计。 |
| Zehao Wang, Shilong Jin, Zhao Cao, Lanjun Wang，2026，[When Planning Fails Despite Correct Execution: On Epistemic Calibration for LLM-Based Multi-Agent Systems](https://arxiv.org/html/2605.23414v1)（[ICML原始出版页](https://proceedings.mlr.press/v306/wang26ct.html)） | EPC-AW已处理执行无报错但计划知识判断错误，六类QA/GAIA任务平均提高9.75个百分点。§5.3的局部一致性选择在2Wiki反而退化，必须加跨轮约束才能改善，说明保守核验与必要探索存在条件冲突。 |

## 三个仍值得追的问题

**1. 团队能否在执行中识别真正的依赖，决定哪些工作应拆开、合并或重新分配？** 实际文档、代码和数据工作里，依赖常在执行后才暴露：两名代理都认为任务独立，最后发现用了不同口径、版本或共同资源。DynTaskMAS已经会生成/调整任务图，AgentCo-op已经会检索组织，因此不能再提“自动分解”。更有力的问题是：当初始依赖判断不可靠，系统如何从结果发现错误分解，并以最小返工调整责任边界？【我的推断】现有执行增益未建立“发现隐藏依赖”与最终成功之间的因果关系。可做方法：用产物消费与验证证据更新依赖，联合决定继续、合并、重派；可做评测：保持任务内容相同，只控制实际依赖是否可由初始描述判断。避免把问题变成再搜索一张拓扑。

**2. 局部故障发生后，团队应重做什么、保留什么，才能修复目标而不制造新的全局错误？** 这是最看好的问题。例：分析代理纠正了数据过滤条件，已经完成的图表、结论和邮件草稿哪些失效？重启全部昂贵，只重跑报错节点又会留下看似正确的旧结果。最近反方非常实在：AgentCo-op已有局部修复，Self-Healing Router已有自动重路由，EPC-AW已有rollback与规划校准。因此切入点应是**基于语义依赖的修复范围选择及已完成工作的有效性判断**。【作者边界】Router直接排除了真实部分故障语义；AgentCo-op承认中间产物验证难。【我的推断】多代理共享产物时，执行成功和结果仍然有效之间的断裂尚缺统一验证。贡献可以是可核验的产物依赖与失效传播方法，加真实可执行任务基准；核心指标用修复后全局成功率、被遗漏的失效产物、重复副作用和返工成本，而非修复次数。

**3. 如何证明“并行团队更好”来自协作，而不是更大算力、独立任务拼接或宽松成功判定？** DynTaskMAS的吞吐收益与AsyncTool的准确率下降并不矛盾：前者测试系统并行收益，后者测试模型延迟状态维护。CorpGen又指出状态检查与产物评判影响结论。问题不是再加一个benchmark名字，而是建立同一底层任务在串行/并行、共享/隔离状态下的配对评价，明确哪些错误由团队交互造成。【我的推断】尤其需要评测“每人局部完成、全局产物冲突”的情况；AsyncTool的独立子任务隐藏状态不足以单独回答这一问题。必须同时控制总推理/工具预算，并用实际环境状态和产物验证，而非只看最终文本与调用路径。

## 判断

优先做问题2，并把问题3作为证明方法有效的实验设计。它触及所有有共享产物的代理团队，直接决定用户能否放心复用已完成工作；相较再比较树、环、星拓扑，研究对象从“怎样连人”推进到“怎样判断共同工作仍然正确”。ACL契合点在自然语言目标、假设与中间结论的语义依赖；若只实现数据库事务、任务重试或工具schema校验，就会退化为工程组合。当前证据支持“明确且重要的未充分解决问题”，尚不能支持“从无人研究”，立项前应对DoVer/COCO等修复谱系做一次定向查新。
