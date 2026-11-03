# 已传达证据的有效应用：相关方法定向核查

核查日期：2026-10-26。衔接DECISION.md；本轮查阅论文原文，不新增模型实验。不是完整系统综述，不以未检索到完全相同实现断言无人研究。

## 结论

该问题有实质相关研究及改善方法。需要区分证据保持可见、证据与旧答案的冲突解释、上游结果对下游的适用检验、实际动作过滤，以及训练信息使用行为。它们不是同一种机制，也没有共同证明自然语言局部知识的应用已普遍解决。

## 五项重点方法

### Re-Ex：证据先转成具体错误解释，再修改回答

Kim等，Re-Ex: Revising after Explanation Reduces the Factual Errors in LLM Responses。原文标注ICLR 2024 Workshop on Reliable and Responsible Foundation Models，不写成ICLR主会。

外部取证→解释回答中哪些内容有事实错误→按解释修订。Table 3在外部证据存在时，有无解释步骤的Correction Acc.：GPT-3.5为25.4%/52.2%，GPT-4为45.2%/50.2%。这是事实纠错率，不是团队任务正确率；额外解释步骤也增加推理工作量，不能断言排除了全部计算量解释。

对我们最直接的启发是检查“证据支持什么、旧判断哪里与它不一致”，而非接收意见后直接重写整份答案。不是分散私有信息协作实验证据，不保证解释总正确。

来源：https://arxiv.org/pdf/2402.17097 ，§2、Table 3。

### VeriMAP：将全局需求变成局部交付及验证标准

Xu等，Verification-Aware Planning for Multi-Agent Systems，EACL 2026。

规划者分解依赖图，制定命名结构化输入输出及Python/自然语言验证函数；执行结果不满足标准时反馈修正，必要时重规划。不是仅校验JSON：语义、任务适用和交接也是目标。Table 1相对普通语言验证MAP-V，多跳检索77.6%→78.2%、HumanEval88.96%→93.92%、BigCodeBench-Hard28.38%→40.54%；不同任务收益幅度不同，不能把全系统差值归给单个模块。§3.3也报告误通过和误拒绝，验证标准可能过严。

对我们的启发：判断交付结果是否满足后续求解需要，而非泛问“对不对”。但依赖规划者能提出好标准；并非隐藏信息证据采用的专门验证，不能假定规划者已知道所有缺失条件。

来源：https://aclanthology.org/2026.eacl-long.353/ 与 https://aclanthology.org/2026.eacl-long.353.pdf ，§2、Tables 1/4。

### Communication and Verification：检查参与实际动作选择

Peng等，Communication and Verification in LLM Agents towards Collaboration under Information Asymmetry，核查arXiv v2。

双Agent持有互补约束，在Einstein桌面谜题执行动作。基础Agent经监督微调；推理时检查器采样过滤候选动作，使用物理可行性、交流历史与推断约束。Table 1/5，Llama3.1-8B CoT Provide & Seek成功率58.67%→89.33%。不能写成对任意现成API模型仅加提示的收益。检查器不额外训练不等于整个方法没有训练。

启发是已知约束实际影响执行，而非只进入一段报告。其符号约束环境与开放语言资料不同，不能解决我们所有条件转译错误，也不支持强制服从可能错误的报告。

来源：https://arxiv.org/html/2510.25595v2 ，§3–4、Table 5、附录C。

### IMP：原文证据路由，控制重复与错误结论传播

Siboni等，Neuro-Inspired Inhibitory Message Passing for Accurate and Token-Efficient Multi-Agent Reasoning，2026-10-17预印本。

按接收者已有资料去重，发送消息所指向的原始证据，不传发送者推理与答案；无需训练或额外路由模型调用。HiddenBench开发消融、16成员、Qwen3-8B，原文路由88%，重新加入推理和答案44%。这是特定开发设置的消融，不是我们四成员的预期收益。

启发是收到“事实+他人解释”不同于收到忠实原文，应用困难可能部分来自上下文污染。它未直接验证已清楚理解某条事实后仍不修正的所有问题。§7明确不判断证据可信度，也不撤回已过时或被纠正的证据。

来源：https://arxiv.org/html/2610.24718v1 ，§2、§4.4、§7、附录H.4。

### CoSIR：把信息使用作为学习目标

Chen等，Training LLMs for Multi-Agent Collaboration with Verifiable Information Rewards，2026-10-13预印本。

在分散评分表环境中训练分享、请求、接收信息后的私有选择和计算。评分不仅看消息是否存在，还根据已获得信息检验选择与汇总。Table 1，Qwen3-8B HiddenBench Base64.23%、Outcome-RL67.31%、CoSIR75.00%。Table 3跨模型任务池judge标注“忽视同伴输入”26.3%→22.8%。没有单独移除信息使用奖励的消融，整体收益不能全归于这一项。

这是直接研究“信息分享后还需使用”的工作。训练依赖可计算环境与开放模型，不是当前官方API直接可部署组件；启发可用于评价或轨迹设计，但不能未经验证把奖励方案换成提示后宣称等效。

来源：https://arxiv.org/html/2610.17893 ，§3.3、Tables 1/3、Limitations。

## 对本项目的取舍

最贴近当前设计动作的是Re-Ex的证据—错误定位桥接，以及VeriMAP的针对下游需要的验证。IMP作为输入处理强对照；Communication and Verification作为执行约束的参照；CoSIR证明使用行为本身已有训练研究，保留为能力学习路线。

这不是要求拼装五个模块。下一步应只选一个机制假设，说明它怎样改善010的事实丢失、023的范围/例外误用，并允许011那类错误检查被拒绝。先用原始案例走查，不立刻联网试验。

这些相关工作支持该问题值得研究，同时限制“没人处理过已传达知识的使用”的创新性表述。我们的贡献应落在明确的机制与可重复改善上；只有增加贡献池、检查员、反馈字段或流程轮数不足以确定区别，也不要求所有基础思想都全新。
