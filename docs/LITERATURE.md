# 文献记录

状态说明：`已核对` 表示阅读了官方摘要或正文；`会议已核对` 表示官方会议／出版社页面明确记录了发表信息；`预印本` 不等于已录用主会论文。

| 工作 | 状态 | 核心内容 | 与本项目关系 |
|---|---|---|---|
| [HomeBench](https://aclanthology.org/2025.acl-long.597/) | ACL 2025 Long，会议已核对 | 有效／无效指令，单／多设备，Succ 与 F1 | 可借鉴问题分层和完整执行指标；虚拟环境省略机械延迟 |
| [SimuHome](https://arxiv.org/abs/2509.24282) | ICLR 2026 Oral（arXiv 页面标注） | Matter 风格设备、连续环境变化、工作流调度、600 episodes | 最接近智慧家庭动态任务；工作流失败和延迟定义值得复用 |
| [MultiAgentBench](https://aclanthology.org/2025.acl-long.421/) | ACL 2025 Long，会议已核对 | 协作／竞争场景、星／链／树／图拓扑、里程碑 KPI | 提醒不能只报最终成功率；但没有家庭设备生命周期约束 |
| [LLMCompiler](https://icml.cc/virtual/2024/poster/32829) | ICML 2024，会议已核对 | 规划器、任务提取器、并行执行器 | “主 Agent 规划＋多个执行器并行”已有成熟先例 |
| [Agent JIT Compilation](https://mast.stanford.edu/pubs/jit_planner/) | ICML 2026，作者页和会议页已核对 | 计划编译、工具不变量、延迟分布、串行／并行／hedging | 直接覆盖缓存、前后置条件和延迟感知计划选择 |
| [Win Fast or Lose Slow](https://papers.nips.cc/paper_files/paper/2025/hash/ddaec864ba433e8889ab08dcf5c26e55-Abstract-Conference.html) | NeurIPS 2025 Main，会议已核对 | 实时交易／游戏中的延迟—质量权衡，FPX 自适应量化 | “大模型更准但更慢”已有强先例；家庭中还要考虑协同和物理状态 |
| [SyncPlan](https://arxiv.org/abs/2608.01652) | 2026 预印本 | 一次联合规划、等待原语、死锁检测、计划过期检测 | 与本命题高度重叠；不能再把这些机制单独当创新 |
| [VeraRAN](https://arxiv.org/abs/2608.01047) | 2026 预印本 | 请求—接受—生效—完成—观测生命周期，异步同步修复和部分序 | 说明最终状态安全不代表执行过程安全；可借鉴证据和版本门控 |
| [Speculative Actions](https://arxiv.org/abs/2510.04371) | 2025/2026 预印本 | 快模型预测并预取后续动作，确认后提交 | 仅适合可模拟、可撤销或幂等动作，不能直接提前执行危险物理动作 |
| [HearthNet](https://arxiv.org/abs/2604.09618) | CAIS 2026 Demo Track | OpenClaw＋HA＋MQTT，动作租约、版本检查、恢复 | 与项目栈直接相近；单测试床和小样本限制了结论 |
| [Multi-Agent Path Finding with Deadlines](https://arxiv.org/abs/1806.04216) | IJCAI 2018（arXiv 页面标注） | 共享空间、截止时间、无碰撞路径规划 | 证明多 Agent＋期限＋冲突的抽象基础较早已有 |

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
