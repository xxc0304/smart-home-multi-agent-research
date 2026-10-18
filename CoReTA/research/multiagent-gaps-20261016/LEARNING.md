# 学习、通信、团队持续适应：独立检索结论
检索截止：2026-10-16。问题：训练究竟学到可迁移协作能力还是固定团队共同适应？团队如何把经历变成长期能力？什么信用分配能支持这种学习？只读检索第一方论文/会议页面，未运行实验、未调用模型。

## 已核实的六篇核心工作
1. **MAPoRL: Multi-Agent Post-Co-Training for Collaborative Large Language Models with Reinforcement Learning**，Chanwoo Park、Seungju Han、Xingzhi Guo、Asuman E. Ozdaglar、Kaiqing Zhang、Joo-Kyung Kim，ACL 2025。[会议原文](https://aclanthology.org/2025.acl-long.1459/)。联合训练讨论中的多个LLM，奖励兼顾最终结果与纠正、说服行为，报告未见任务迁移和异质模型协作。因此“训练协作”“跨域迁移”都已有人实现；作者明确局限是3B–8B、提示敏感和最终多数投票，而非声称没有迁移。
2. **Cross-environment Cooperation Enables Zero-shot Multi-agent Coordination**，Kunal Jha、Wilka Carvalho、Yancheng Liang、Simon Shaolei Du、Max Kleiman-Weiner、Natasha Jaques，ICML 2025。[会议原文](https://proceedings.mlr.press/v267/jha25b.html)。传统RL在多环境分布中与单一队友训练，能向新任务、新队友乃至人类迁移。它是“可迁移协作训练”最强相邻反例，但不是LLM语言协作的解决方案。
3. **LLM-Guided Communication for Cooperative Multi-Agent Reinforcement Learning**，Sangjun Bae、Yisak Park、Sanghyeon Lee、Seungyul Han，ICML 2026。[会议原文](https://proceedings.mlr.press/v306/bae26c.html)。LMAC用LLM迭代设计协议，以各agent重建环境状态及知识差距为优化依据，在MARL任务验证收益。注意是LLM辅助设计MARL通信，不等同端到端训练自然语言团队。
4. **The Trace Is the State: Exact Credit Assignment for LLM Agent Teams**，Yanjun Chen、Yirong Sun、Hanlin Wang、Jinghan Wang、Xinming Zhang、Xiaoyu Shen、Wenjie Li、Wei Zhang，2026预印本，[v4原文](https://arxiv.org/html/2603.06859v4)。2026-10-07改版，旧检索标题为Contextual Counterfactual Credit Assignment…。C3恢复trace、替换单条消息、运行后续团队，建立条件无偏估计与独立反事实参考。作者明确：工具、记忆、路由须完整记录/正确重采样；存在未恢复隐状态则保证不适用。
5. **From Interaction Trajectories to Prompt Rules: Credit Assignment for Multi-Agent Prompt Optimization**，Bin Wu、Haoran Xu、Xiang Zhuang、Zonghao Chen、Zhu Li、Emine Yilmaz、Qiang Zhang，ICML 2026。[会议原文](https://proceedings.mlr.press/v306/wu26bp.html)。TRUCE把轨迹证据关联到prompt行为规则、局部修改并跨任务聚合；明确保留既定角色与交互结构。因此“不用参数训练也能从经历更新团队”已成立。
6. **Scaling Teams or Scaling Time? Memory Enabled Lifelong Learning in LLM Multi-Agent Systems**，Shanglin Wu、Yuyang Luo、Yueqing Liang、Kaiwen Shi、Yanfang Ye、Ali Payani、Kai Shu，2026预印本，[原文](https://arxiv.org/html/2604.03295v1)。LLMA-Mem结合episodic、procedural、transactive memory，在MultiAgentBench三个环境研究跨任务累积与团队规模，发现规模收益非单调、局部记忆优于共享方案。作者明确未直接测记忆冗余、过时与检索错误稳健性；最多七agent。

## 三个足够宽的重要未解决问题

**A. 可迁移协作能力：怎样学习“与任何合适队友共同解决新问题”的能力？**
MAPoRL已证明任务迁移，CEC甚至证明传统RL的新队友迁移；LMAC说明可用状态重建约束通信。仍需回答协作知识的可迁移单位：任务分解、证据交接、纠错、承诺与依赖协调中，哪些可以脱离原队友和协议？训练目标怎样抑制私有暗号与共同错误，同时保留互补专业化？这是我的综合推断，不是上述作者直接宣布的空白。值得发表的新结果是建立可识别的协作技能表示/学习原则，并解释何时跨任务、跨队伍迁移成立，何时发生共同适应；相应benchmark应把个体解题进步与团队协作进步分离，而非只收集更多游戏。

**B. 团队持续学习：如何累积集体能力而不把错误与过时分工固化？**
LLMA-Mem已有记忆累积，TRUCE已有规则更新；真正缺口是经验、规则、能力模型三者的持续修订机制：一个agent的错误如何避免进入团队惯例，能力变化时旧分工如何撤回，跨角色知识何时共享/隔离？LLMA-Mem的记忆质量缺测是作者明确局限；“联合修订团队行为”是我的延伸。重要新增结果应说明团队知识如何产生、验证、传播、失效和遗忘，给出稳定性/可塑性边界；仅增加memory模块或把共享改成混合拓扑不够。

**C. 信用分配怎样从“当前团队的一条好消息”走向“值得长期学习的协作行为”？**
C3已解决可恢复trace下的消息价值估计，TRUCE将credit落到规则。仍须区分消息价值来自真实信息、队友的补救能力、或特定协议偶然性；当前团队的边际价值未必等于可迁移技能的训练价值。这个差距是推断；不可恢复隐状态是C3明确边界。重要结果是定义跨任务/跨队伍仍有意义的协作贡献及可靠估计，而非把Shapley或反事实词汇再包装一次。若只做“更细粒度credit”，C3等已构成很强近邻。

## 优先判断
最看好 **A：可迁移协作能力的学习与识别**。它直面多agent训练是否学会协作这一核心命题，方法和benchmark都可承载，语言的证据传递、纠正与协议理解使其适合ACL。最大反方是MAPoRL已经报告跨域迁移，加上CEC已实现新队友迁移；新工作必须证明并解释跨任务迁移与跨队伍迁移为何不同、如何统一，不能把“换几个模型测试”当贡献。B为次选，C竞争最拥挤。

