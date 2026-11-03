# 知识利用、传递、澄清与验证：已录用论文切入口核查

检索日：2026-10-20。范围按会议正式发表时间落在 2025-10-20—2026-10-20 判定；预印本首发可以早于窗口。研究问题：哪些具体失效被隔离出来？方法在哪个操作点干预？实验排除了哪些替代解释？以下核验公开论文与录用身份，不推断审稿人录用原因。

## 检索与证据范围

独立两轮检索：第一轮以 expertise / knowledge / clarification / verification + multi-agent 检索 NeurIPS、OpenReview、ACL 官方来源；第二轮以 ExtAgents / AgentAsk / Expert Not Mentioned / Reveal Expert / GKS / KAR / hypothesis validation 收窄，回到方法、控制实验和局限。采用四篇，其中三篇主会、一篇 Findings。没有把 under-review 的 WaAgents、IWSDS 的 MAC、LREC 的 R2L 冒充指定顶会主会。

| 论文 | 正式身份与一手入口 | 已读范围 |
|---|---|---|
| Scaling External Knowledge Input Beyond Context Windows of LLMs via Multi-Agent Collaboration（ExtAgents） | [ACL 2026 主会长文官方条目](https://aclanthology.org/2026.acl-long.468/) | 官方元数据与摘要；[作者预印本 v2 全文](https://arxiv.org/html/2505.21471v2) §3–5、Fig.5、Limitations、附录成本。官方 PDF 10.6MB 超过检索器大小限制，未声称逐字核过终稿。 |
| AgentAsk: Multi-Agent Systems Need to Ask | [ACL 2026 主会长文官方条目](https://aclanthology.org/2026.acl-long.1294/) | [官方 PDF](https://aclanthology.org/2026.acl-long.1294.pdf) §3–5、Tables 1–3、Limitations。 |
| Multi-Agent Teams Hold Experts Back | [ICML 2026 / PMLR 306 正式论文](https://proceedings.mlr.press/v306/pappu26a.html) | 官方录用元数据与摘要；[作者全文 v4](https://arxiv.org/html/2602.01011v4) §3–5、Table 2、附录 D–G/K。PMLR 所链 PDF 抓取失败，不把预印本等同于逐字终稿。 |
| VulAgent: Hypothesis-Validation Driven Multi-Agent Architecture for Vulnerability Detection | [ACL 2026 Findings 官方条目](https://aclanthology.org/2026.findings-acl.928/) | [官方 PDF](https://aclanthology.org/2026.findings-acl.928.pdf) 方法、Tables 1/2/4/6、§5.5、case study、Limitations。明确属于 Findings。 |

## 四个可以学习的贡献单元

### 1. ExtAgents：信息分布以后，怎样真正汇入推理

瓶颈分为局部消息交换带宽不足和一次塞入过多摘要导致推理过载。操作是全局消息按相关性排序后同步，以及推理阶段逐轮引入 top-2^s 消息并检查可回答性。Fig.5 分别去掉 GKS 和 KAR；两者均退化，KAR 去除的损失随输入增加更明显。这个例子的贡献是把“更多知识”落实为两个可干预瓶颈。[方法与消融](https://arxiv.org/html/2505.21471v2)

边界：其最优设置表含不同输入量，不能直接当等 token 预算的证明；全局同步增加成本，排序可能失真，错误摘要也会全局传播。预印本 Table4 的 HotpotQA .534（1024k）对 DRAG .482（128k）属于各自最优设置，若讲公平性应优先讨论同输入曲线及组件消融，不能只引用这对数字。[实验与限制](https://arxiv.org/html/2505.21471v2)

### 2. AgentAsk：在消息交接点决定是否澄清

824 条执行日志形成四类边错误；方法将动作拆成是否问、问谁、问什么，以 SFT 后的 E-GRPO 平衡下游正确性与提问成本。固定已有 orchestration，Qwen3-4B 澄清器跨四框架的五任务均分增加 3.29–3.45 个百分点。Table3 的 MBPP 消融：完整 83.55，去掉有效性奖励 80.05，仅终局奖励 79.66；因而“会提问”和“学会何时不问”成为可检查的主张。[官方全文](https://aclanthology.org/2026.acl-long.1294.pdf)

数字校正：摘要的 up to 4.69% 在 Table1 对应 +GPT-5 强澄清器均分，不能移植给轻量 AgentAsk。边澄清也无法修复全部 agent 内在能力错误。[官方结果及局限](https://aclanthology.org/2026.acl-long.1294.pdf)

### 3. Experts Hold Back：先把“专家没被识别”与“被识别却没被采用”拆开

这篇主要贡献是诊断。隐藏/揭示专家身份、集中/分布知识、全部成员持有专家信息等对照，将利用失败从身份识别与通信噪声中分离。心理学任务的 full-information 对照中，四专家团队接近单专家；换成一专家三非专家后明显退化。对话中的折中倾向与差距相关，但不能据此证明 alignment 的因果作用。恶意成员实验还提示权威服从与抗操纵之间存在张力。[全文与附录 D](https://arxiv.org/html/2602.01011v4)

必须校正比较口径：Table2 的 6.3%–41.1% 是相对逐题 oracle ALOC 的差距。HLE：隐藏专家团队 28、揭示专家团队 36、最佳固定单模型 29、ALOC 47.5。41.1%=（47.5−28）/47.5，绝不能写成“比最佳固定单模型差 41.1%”；揭示后在若干 ML 基准已超过最佳固定单模型。摘要的宽泛措辞需要由表格限定。[正式身份](https://proceedings.mlr.press/v306/pappu26a.html)，[详细结果 Table2/E](https://arxiv.org/html/2602.01011v4)

### 4. VulAgent：把风险描述改造成可以逐项反驳的触发假设

操作对象是触发前提、路径、guard 和项目上下文；先提出候选，再剪除不可触发路径并作最终验证。PrimeVul 去掉最终验证，FPR 从 36.70 升至 65.00、ACC 从 58.60 降至 51.81。更有辨识力的是 oracle-CWE 控制：给各方法同样真实 CWE 与上下文后，验证仍能降低误报。[官方全文 Tables2/6](https://aclanthology.org/2026.findings-acl.928.pdf)

这里的取舍必须保留：oracle-CWE 下 FPR 20.48 对 direct 49.40，但 F1 52.94 对 65.95，ACC 61.45 对 62.05；并非所有指标都提升。输出 token 约为 VulTrial 的 2.3 倍，且缺失上下文可能错误否决真漏洞。它展示的是验证与 triage 的有限收益，身份是 Findings。[官方结果与局限](https://aclanthology.org/2026.findings-acl.928.pdf)

## 从案例能推导出的贡献标准

ExtAgents 改“知识怎样进入上下文”，AgentAsk 改“消息怎样获准传递”，VulAgent 改“主张怎样获得证据支持”；Experts Hold Back 则说明，仅宣布谁是专家并不能保证其知识被有效采用。四者的对象、干预点与比较口径不同，把它们统称“更好协作”会丢掉研究内容。

对我们最有用的做法，是把候选想法写成一个可被否定的句子：在某个已测到的失效条件下，改变某项操作，会改善某个中间变量，并在固定模型、信息和预算后改善结果。随后找最近工作究竟已经覆盖了条件、操作、中间变量还是仅覆盖了总体任务。只有“加专家、共享记忆、再问一句、加验证器”的描述容易被已有工作的功能层覆盖；若能明确同样信息下哪些正确知识仍会丢失、为何会丢失、我们的操作保住了什么，并用对照定位原因，就有可评估的增量。

这些是从论文证据结构归纳的研究标准，不能推出某种包装保证录用，也不能在尚未核对 CoReTA 的完整设计和证据前断言“我们没有创新”。需要警惕的真实问题是：我们的想法若停留在模块名称，便还没有达到这些案例展示的、可独立验证的贡献粒度。
