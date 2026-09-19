# HearthNet：全文阅读笔记

阅读状态：已完成全文阅读  
正式出处：Zhonghao Zhan, Krinos Li, Yefan Zhang, Hamed Haddadi. “HearthNet: Edge Multi-Agent Orchestration for Smart Homes.” Proceedings of the 1st ACM Conference on Agentic and AI Systems (CAIS ’26), May 26, 2026, 5 pages. DOI: `10.1145/3786335.3813188`。  
官方来源：[ACM DOI](https://doi.org/10.1145/3786335.3813188)；[arXiv:2604.09618v2](https://arxiv.org/abs/2604.09618)  
综述用途：家庭边缘多 Agent 编排、持久状态、跨机器通信、执行授权、冲突处理和故障恢复

## 1. 研究问题与核心判断

HearthNet 认为，家庭 Agent 与普通会话式多 Agent 的运行条件不同。家庭控制是持久的、事件驱动的、容易发生设备和网络故障，而且命令可能造成真实的物理、隐私和安全后果。仅靠会话上下文或临时子 Agent，难以处理跨机器状态、重启恢复、过期命令和不同权限域之间的冲突。

论文提出一个部署在家庭边缘节点上的小型多 Agent 系统：多个持久化、角色专门化的 LLM Agent 通过 MQTT 通信，以 Git 作为共享状态和审计记录，并通过 root-issued actuation lease 控制状态变化命令是否可以真正到达设备。

## 2. 系统架构

HearthNet 明确区分四类角色：

| 角色 | 实例 | 职责 |
|---|---|---|
| Root Agent | Rupert，Mac mini | 接收用户请求、拆分任务、协调管理器、仲裁冲突、签发唯一的 actuation lease |
| Manager Agents | Jeeves、Darcy | 分别管理 Home Assistant 设备和手机端专有 IoT 应用，提出领域内具体动作 |
| Librarian Agent | Dewey，Intel NUC | 观察 MQTT 协调流，将任务、状态、冲突和恢复事件写入 Git；不发命令、无设备凭证 |
| Device Adapters | 灯、音箱、摄像头、电视等 | 确定性的设备接口，不属于 Agent |

Manager Jeeves 负责 Home Assistant 暴露的灯、开关、空调和媒体设备；Manager Darcy 运行在 Android 手机上，通过 ADB/UI automation 控制没有外部 API 的专有 IoT 应用，还能访问中心节点无法获得的摄像头、环境光和陀螺仪信息。这是论文主张分布式架构有必要的关键理由。

Agent 之间通过 Mosquitto MQTT broker 通信，包括点对点 inbox、广播频道和审计流；持久共享状态由 Dewey 管理的 Git 仓库保存。消息带有可选的 `base_commit`，状态改变请求还要携带 root 签发的 lease id。

论文特别强调：设备不是 Agent。系统不采用“每个设备一个 Agent”，而是由少量管理 Agent 通过薄适配器控制异构设备。

## 3. 共享状态与授权模型

Git 仓库是协调状态的事实来源，提供三项能力：

1. 版本化共享状态：Agent 重启后可重新同步；
2. 可归因的时间线：记录发送者、时间、结果和冲突解决过程；
3. 过期状态检测：比较消息中的 `base_commit` 与仓库当前 HEAD。

授权由 root Agent 统一执行。版本化 policy file 将管理器角色映射到允许的设备类别、操作类型和参数范围。每个 actuation lease 包含：管理器身份、目标设备/类别、允许的操作和参数范围、批准时的状态 commit、policy commit、过期时间和人类可读的审计理由。

适配器拒绝以下命令：没有 lease、lease 已过期、超出设备或参数范围，或者 lease 绑定的状态 commit 已经过时。这样，授权和状态新鲜度从提示词约定变成了可检查的系统边界。

## 4. 四阶段执行协议

每个用户请求遵循以下流程：

1. Ground：Agent 从 Git 读取当前设备 shadow state、policy 快照和仓库 HEAD；
2. Propose：Rupert 拆分用户意图，Manager 将子任务翻译为具体设备动作，但此时不能直接执行；
3. Verify and Grant：Rupert 检查状态新鲜度、当前意图、冲突规则和权限，批准后签发短期 lease；
4. Execute and Record：Manager 使用 lease 调用适配器，返回结果，Dewey 将提议、授权和执行结果写回 Git。

Agent 是持久进程，但每次消息都会基于当前 Git 状态触发新的推理调用。重启后的 Agent 不依赖旧的隐藏上下文，而是先同步当前状态再重新申请授权。

## 5. 故障处理与恢复

Agent 通过 heartbeat 汇报状态，MQTT 的 Last Will and Testament 用于发布意外断开事件。默认连续两个 60 秒心跳间隔缺失后，root Agent 将管理器标记为无响应。

当管理器在例程中途失效时，Rupert 从 Git 日志把子任务分类为 confirmed、in-flight 或 blocked：

- confirmed：关闭任务；
- in-flight：只有在其他存活管理器具备所需能力，且可以基于当前状态和策略签发新 lease 时才重发；
- blocked：进入带指数退避的重试队列，或交给操作员处理。

如果重启后的 Agent 使用旧 `base_commit` 或旧 lease，root 会拒绝命令；Agent 必须重新同步并申请新的授权。Git 是唯一事实源，单个 Agent 的本地状态不具有权威性。

## 6. 三个真实设备场景与结果

论文在三类商品级硬件上部署原型：Mac mini、Intel NUC 和 Pixel 4；设备包括 Philips Hue 灯、JBL 音箱、Reolink 摄像头和 LG 智能电视。用户通过 Telegram 交互，LLM 推理使用 Anthropic API 的 Claude Opus 4.6 和 Google Vertex AI 的 Gemini 3 Pro。

### Scene 1：模糊意图驱动的协同执行

用户发送“我今天在家工作”。Rupert 将其分解为设备域子任务：Jeeves 调整灯光和音箱，Darcy 通过手机 UI automation 关闭电视。每个 Manager 使用自己的领域知识提出具体动作，Rupert 检查后为每个动作签发 lease。

结果为 4/5 次任务完成，中位端到端延迟 8 秒。唯一失败来自手机端视觉 grounding 误认应用图标；协议正确记录了这一错误，便于事后诊断。

### Scene 2：带时间线的冲突解决

在“居家办公”状态仍然有效时，自动触发的晚间例程试图把灯调暗并改成暖色。Rupert 通过 Dewey 的 Git 时间线发现此前存在明确的用户请求，因此判断定时例程不能覆盖当前意图，维持现有灯光状态并记录决策依据。

冲突检测和解决为 5/5。这里的关键贡献不是某个具体设备控制算法，而是将用户意图、自动化触发和设备状态放在同一条可追溯时间线上。

### Scene 3：新鲜度与授权验证

系统中途重启一个 Agent，并让它尝试使用崩溃前的旧 `base_commit` 和旧 lease 执行命令。Rupert 比较当前 HEAD 后拒绝过期命令，Dewey 记录使其失效的 commit 和 lease，恢复后的 Agent 必须同步并重新授权。

5/5 过期命令被正确拒绝，5/5 过期/无效 lease 被拒绝，误拒绝为 0；153/153 个跨场景事件写入 Git；lease 验证的 p95 开销小于 0.01 ms。端到端延迟主要来自每一跳的 LLM 推理，通常为每跳 1–5 秒，而非 MQTT、Git 或 lease 检查本身。

## 7. 论文的多 Agent 证据强度

HearthNet 是当前矩阵中最直接的家庭多 Agent 证据，因为论文明确给出：

- 独立运行在不同设备上的多个持久化 Agent；
- 明确的角色分工和领域权限；
- MQTT 跨 Agent 通信；
- Git 共享状态、时间线和恢复机制；
- root Agent 的冲突仲裁和授权签发；
- 真实设备上的端到端场景。

但它证明的是“这种架构能够在小规模原型中运行”，不是“多 Agent 普遍优于单 Agent”。论文没有提供大规模家庭、多个系统配置、单 Agent 对照或统计显著性比较，因此不应把 4/5、5/5 等演示结果写成通用性能结论。

## 8. 局限性与安全边界

论文明确承认：

1. 评测只有一个 testbed、4 个 Agent 和约 10 个设备，规模扩展尚未验证；
2. LLM 推理依赖托管 API，端到端延迟会受服务商负载影响；
3. 采用 honest-but-crashing 故障模型，恶意 Agent、重放攻击等对手模型不在范围内；
4. 固定 MQTT trace 的 replay 可以验证安全性质，但不包含真实 LLM 推理，真实设备执行仍需要 testbed；
5. 视觉 grounding 的失败说明多 Agent 编排的安全协议不能自动修复底层感知错误；
6. 设备适配器仍依赖具体生态和 UI automation，跨品牌、跨协议和长期维护成本尚未系统评估。

## 9. 对综述正文的直接用途

HearthNet 适合放在“家庭多 Agent 架构与可靠执行”一节，用来说明多 Agent 相比单 Agent 的新增问题不是简单地增加几个角色，而是需要解决：

- 跨节点共享状态和上下文外化；
- 角色权限与设备作用边界；
- 并发/定时任务冲突；
- 过期状态、lease 和故障恢复；
- 执行历史、审计与安全追责。

它还可以与 HomeFlow 形成互补：HomeFlow 解决“如何在可验证环境中训练单 Agent 的执行能力”，HearthNet 解决“多个持久 Agent 在真实边缘设备上如何安全协调”。两者共同支持“家庭 Agent 研究应从单步调用扩展到感知—规划—授权—执行—恢复闭环”的综述主线。

