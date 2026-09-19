# 文献记录

状态说明：`已核对` 表示阅读了官方摘要或正文；`会议已核对` 表示官方会议／出版社页面明确记录了发表信息；`预印本` 不等于已录用主会论文。

本轮对话讨论的 19 篇论文如下；表中的“预印本”不等于已录用主会论文。

| 工作 | 状态 | 核心内容 | 与本项目关系 |
|---|---|---|---|
| [HomeBench](https://aclanthology.org/2025.acl-long.597/) | ACL 2025 Long，会议已核对 | 有效／无效指令，单／多设备，Succ 与 F1 | 可借鉴问题分层和完整执行指标；虚拟环境省略机械延迟 |
| [SimuHome](https://arxiv.org/abs/2509.24282) | ICLR 2026 Oral（arXiv 页面标注） | Matter 风格设备、连续环境变化、工作流调度、600 episodes | 最接近智慧家庭动态任务；工作流失败和延迟定义值得复用 |
| [HomeFlow](https://arxiv.org/abs/2606.01230) | 2026 预印本 | 可验证模拟、程序化家庭生成、成功条件编译、MCTS 轨迹合成和逐步强化学习 | 对数据生成、轨迹验证和持续训练很有价值；与在线多 Agent 调度关系较间接 |
| [SAGE](https://arxiv.org/abs/2311.00772) | 2023/2024 arXiv 版本 | Grounded Execution、设备 API、状态反馈和失败分类 | 提供设备接地和工具接口参考；主要是单控制器 |
| [SMH-Bench](https://arxiv.org/abs/2606.01912) | 2026 预印本 | 组合控制、自动化、多轮、记忆、个性化和查询任务 | 提供家庭能力分类；不以异步多 Agent 调度为变量 |
| [PersonalHomeBench](https://arxiv.org/abs/2604.16813) | 2026 预印本 | 个性化家庭、多模态输入、视频理解和长期上下文 | 提醒考虑用户与家庭差异；不等于资源协调算法 |
| [REALM-Bench](https://arxiv.org/html/2502.18836) | 2025 预印本 | 现实动态规划与 Job-Shop 调度，控制并行度、依赖和扰动 | 可借鉴动态调度实验轴和迁移验证 |
| [DynTaskMAS](https://arxiv.org/abs/2503.07675) | 2025 预印本 | 动态任务图、异步并行、Agent 池和工作流管理 | 重要强基线；单纯 DAG 加并行已被覆盖 |
| [MultiAgentBench](https://aclanthology.org/2025.acl-long.421/) | ACL 2025 Long，会议已核对 | 协作／竞争场景、通信拓扑和里程碑 KPI | 提醒报告中间里程碑和失败传播 |
| [SagaLLM](https://arxiv.org/abs/2503.11951) | 2025 预印本 | 上下文管理、验证、检查点、补偿和事务保证 | 事务式执行与恢复基线 |
| [ALAS](https://arxiv.org/abs/2511.03094) | 2025 预印本 | 版本化执行日志、动态扰动、工作流 IR 和局部修复 | 与选择性计划修复高度相关，要求精确定义差异 |
| [SyncPlan](https://arxiv.org/abs/2608.01652) | 2026 预印本 | 联合规划、异步动作链、等待原语、死锁和计划过期检测 | 异步执行和过期拒绝不能单独作为创新 |
| [VeraRAN](https://arxiv.org/abs/2608.01047) | 2026 预印本 | 请求—接受—生效—完成—观测生命周期和过程安全 | 可借鉴证据、版本门控和动作生命周期 |
| [Agent JIT Compilation](https://mast.stanford.edu/pubs/jit_planner/) | ICML 2026 页面 | 计划编译、工具不变量、延迟分布和串行／并行／hedging | 直接覆盖延迟感知计划选择和缓存先例 |
| [Speculative Actions](https://arxiv.org/abs/2510.04371) | 2025/2026 预印本 | 快模型预测并预取后续动作，确认后提交 | 需要风险、状态版本和可逆性门控 |
| [Win Fast or Lose Slow](https://papers.nips.cc/paper_files/paper/2025/hash/ddaec864ba433e8889ab08dcf5c26e55-Abstract-Conference.html) | NeurIPS 2025 Main，会议已核对 | 延迟—质量权衡和实时决策 | “更准但更慢”已有强先例 |
| [HearthNet](https://arxiv.org/abs/2604.09618) | CAIS 2026 Demo Track | OpenClaw＋HA＋MQTT、动作租约、版本检查和恢复 | 与项目工程栈相近；测试规模有限 |
| [When Do LLM Agents Help?](https://arxiv.org/abs/2608.19557) | 2026 预印本 | 混合关键任务截止时间调度，比较强启发式与 LLM 控制层 | 平稳负载下强启发式已近最优；非平稳突变时 LLM 才有增益 |
| [Bridging Large-Model Reasoning and Real-Time Control](https://arxiv.org/abs/2604.01681) | 2026 预印本 | Agentic Fast-Slow Planning，慢语义推理与经典规划、实时 MPC 分层 | 快慢分层已有直接先例，增量需落在多 Agent 状态与安全提交 |

LLMCompiler（ICML 2024）和 [Multi-Agent Path Finding with Deadlines](https://arxiv.org/abs/1806.04216) 作为补充背景文献，不计入上述 19 篇。

## Speculative Actions 对当前方向的进一步启发

该工作最值得借鉴的是“预测—并行准备—状态验证—提交或丢弃”这一临界路径机制，而不是把家庭设备动作全部提前执行。家庭场景增加了物理副作用、共享资源、异步反馈和硬截止时间，因此可研究的增量包括：

- 风险、可逆性、幂等性和资源影响范围感知的 speculation 决策；
- 绑定状态版本、前置条件、资源租约、置信度和有效时间的预测结果；
- 预测失配后仅使受影响的计划子图失效，而不是全局重新规划；
- 用本地预授权策略保证首个安全动作，把大模型从关键路径移到后续计划和恢复过程。

家庭中的“lossless”不宜直接沿用论文的轨迹等价定义。更合适的安全目标是：预测分支不会产生未授权、危险或无法补偿的物理副作用；通过安全门控后，允许内部执行路径不同但任务目标和安全不变量保持。

## 对 HomeBench 与 SimuHome 的具体解读

HomeBench 摘要中的 GPT-4o “无效多设备 0%”采用严格的全请求成功定义；正文表 3 中 ICL 设置可显著提高该类结果。因此应写成“严格完整成功率暴露了问题”，不能写成“GPT-4o 完全不会识别无效指令”。

SimuHome 发现工作流调度是最难类别，并指出立即工具反馈比只返回“工作流已注册”更利于恢复。其时间加速模拟器适合训练和测试，但不能替代真实网络、硬件和反馈延迟测量。
