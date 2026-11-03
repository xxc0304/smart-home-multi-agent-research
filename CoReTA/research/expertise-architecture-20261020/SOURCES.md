# 来源与核验台账

共35项研究来源，分支笔记记载具体阅读边界。VERIFIED表示存在及本表所用陈述核对通过，不表示全文复现。PAYWALL项只限摘要级陈述。

|编号|分支|原始来源|核验|阅读/限制|
|---|---|---|---|---|
|S1|专长设置|[Multi-Agent Teams Hold Experts Back](https://arxiv.org/html/2602.01011v4)|VERIFIED|方法/附录/官方代码；集中/分布信息、异构能力；区分资料持有者与逐题正确者|
|S2|专长设置|[Systematic Failures in Collective Reasoning under Distributed Information in Multi-Agent LLMs / HiddenBench](https://arxiv.org/html/2505.11556v3)|VERIFIED|方法及6.2–6.3；强制披露与被动摘要不同；Reveal-All结果限受检子集|
|S3|专长设置|[iAgents / InformativeBench](https://arxiv.org/html/2406.14928)|VERIFIED|方法与附录C–D；私有资料检索与信息导航，不等于能力专家|
|S4|专长设置|[Communication and Verification in LLM Agents towards Collaboration under Information Asymmetry](https://arxiv.org/html/2510.25595)|VERIFIED|方法3–4、5.1；约束/行动权限/环境验证；原设置非三人|
|S5|专长设置|[Stop Overvaluing Multi-Agent Debate—We Must Rethink Evaluation and Embrace Model Heterogeneity](https://arxiv.org/pdf/2502.08788)|VERIFIED|方法及互补分层；异构随机混合不等于已校准专长|
|N1|近邻机制|[Self-Organizing Agent Teams Learn to Reason Together](https://arxiv.org/html/2609.22682v1)|VERIFIED|方法2、附录A/D；学习策略、证书审计、少数依据恢复；预印本|
|N2|近邻机制|[ReConcile: Round-Table Conference Improves Reasoning via Consensus among Diverse LLMs](https://arxiv.org/html/2309.13007)|VERIFIED|方法/实现附录；异构、解释、置信加权，不是外部事实判定|
|N3|近邻机制|[Breaking Mental Set to Improve Reasoning through Diverse Multi-Agent Debate](https://proceedings.iclr.cc/paper_files/paper/2025/hash/3de667dab3b3d812583abc0a786139a0-Abstract-Conference.html)|VERIFIED|正式题录摘要/官方幻灯片；PDF未读；只据核实范围谈不同推理操作，不推断全部实现|
|N4|近邻机制|[AgentAsk](https://arxiv.org/html/2510.07593)|VERIFIED|方法4、附录A/F；消息边的最小澄清，SFT/RL训练预算策略|
|N5|近邻机制|[CoThinker](https://arxiv.org/html/2506.06843)|VERIFIED|方法4；认知分工、transactive memory与信息流管理|
|N6|近邻机制|[LASE](https://arxiv.org/html/2610.16343v1)|VERIFIED|方法3；主答先行、置信触发局部同伴与专家升级；预印本|
|N7|近邻机制|[Think, Then Verify: A Hypothesis-Verification Multi-Agent Framework for Long Video Understanding](https://arxiv.org/html/2603.04977)|VERIFIED|方法3.2–3.3/算法1；候选假设→区分线索→视频取证→再检验|
|N8|近邻机制|[Automated Hypothesis Testing with Agentic Sequential Falsifications / POPPER](https://github.com/snap-stanford/POPPER)|VERIFIED|原论文2–4及官方仓库；先生成可测蕴含和检验、执行及顺序证据；统计假设不能直接迁到语言裁决|
|N9|近邻机制|[Consilience: Conformally Calibrated Communication Control for Hidden-Profile Multi-Agent Reasoning](https://arxiv.org/html/2608.20564)|VERIFIED|方法3、校准限制、训练/留出说明；反事实动作/发言选择与逐轮校准；保证代理一步损失而非最终正确|
|N10|近邻机制|[Calibration Is Not Verification: Falsifiability-Aware Conformal Routing for Mixture-of-Agents](https://arxiv.org/html/2609.25959)|VERIFIED|方法/实验/限制；盲near-miss、LOO及可用性融合；弱判定器可能有害，预印本|
|N11|近邻机制|[When Debate Helps: Proposal Supply and Verification-Aware Readout in Multi-Agent Reasoning](https://arxiv.org/html/2610.04686v1)|VERIFIED|方法3、附录A.9；区分候选供给与读出，正确/错误证据干预；按预印本使用|
|N12|近邻机制|[Conformal Social Choice](https://arxiv.org/html/2604.07667)|VERIFIED|摘要/方法；选择性输出与升级；coverage和风险同时报告|
|N13|近邻机制|[Towards Trustworthy AI Results Using Evidence Structures](https://experts.illinois.edu/en/publications/towards-trustworthy-ai-results-using-evidence-structures-from-cer/)|PAYWALL|作者机构摘要；仅支持证据结构/缺口反馈的摘要级先例，不作实现排重|
|V1|反证与评价|[When Helping Hurts and How to Fix It: Multi-Agent Debate for Data Cleaning](https://arxiv.org/html/2606.02866)|VERIFIED|方法/factorial；独立工具critic+证据门控已有；不引用有版本疑点精确效应值|
|V2|反证与评价|[MAS-ProVe: Understanding the Process Verification of Multi-Agent Systems](https://arxiv.org/html/2602.03053)|VERIFIED|方法/结果/可解性；评估中间轨迹仍不稳定，不支持加judge自动变强|
|V3|反证与评价|[Debate Helps Supervise Unreliable Experts](https://arxiv.org/html/2311.08702)|VERIFIED|方法/consultancy/错误分析；人类读者信息不对称与对抗监督，不能原样外推LLM合作|
|V4|反证与评价|[On scalable oversight with weak LLMs judging strong LLMs](https://arxiv.org/html/2407.04622)|VERIFIED|方法/closed与extractive任务；弱监督条件，部分给专家解释是受控辅助条件|
|V5|反证与评价|[Multi-agent discussion gains less when dissent is withheld](https://arxiv.org/html/2609.38324)|VERIFIED|方法/信息池化与利用；披露、内化、重新考虑与纠错分开；特定模型/任务结果|
|X1|跨域迁移|[Bayesian Active Learning for Classification and Preference Learning](https://arxiv.org/html/1112.5745)|VERIFIED|方法2、4；选择可消除模型分歧，LLM票数非后验|
|X2|跨域迁移|[Representative, Informative, and De-Amplifying: Requirements for Robust Bayesian Active Learning under Model Misspecification](https://proceedings.mlr.press/v300/tang26d.html)|VERIFIED|正式题录+arxiv2506.07805方法；失配下信息性可放大误差|
|X3|跨域迁移|[Modeling Probability Forecasts via Information Diversity](https://arxiv.org/html/1406.2148)|VERIFIED|方法3–4/期刊存档；重叠信息聚合；高斯校准假设不自动适用LLM|
|X4|跨域迁移|[Prover-Verifier Games improve legibility of LLM outputs](https://arxiv.org/html/2407.13692v1)|VERIFIED|方法3–6；有标签对抗训练、易检查性与正确性不同|
|X5|跨域迁移|[Mitigating Legibility Tax with Decoupled Prover-Verifier Games](https://arxiv.org/html/2602.23248)|VERIFIED|方法2–4；solver/translator分离；答案保真不等于推理正确，真标签训练|
|X6|跨域迁移|[Near-Optimal Machine Teaching via Explanatory Teaching Sets](https://proceedings.mlr.press/v84/chen18g.html)|VERIFIED|方法3–4；真教师/learner先验前提；正式页1970–1978|
|X7|跨域迁移|[A rational account of pedagogical reasoning: Teaching by, and learning from, examples](https://web.stanford.edu/~ngoodman/papers/shaftogg14.pdf)|VERIFIED|方法2–3；helpful teacher与选例推断，不能保证教师正确|
|X8|跨域迁移|[Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/html/2306.05685)|VERIFIED|方法3.3–3.4；位置/文风/自偏好，偏好评估非事实真值|
|X9|跨域迁移|[Large Language Models Cannot Self-Correct Reasoning Yet](https://arxiv.org/html/2310.01798)|VERIFIED|方法3–5；intrinsic self-correction条件限制，不外推所有未来模型|
|X10|跨域迁移|[A Bayesian Truth Serum for Subjective Data](https://nel.mit.edu/wp-content/uploads/2016/10/bts.pdf)|VERIFIED|原文机制；诚实激励均衡不等于事实真；三同源Agent不满足假设|
|X11|跨域迁移|[AI Safety via Debate is Compromised by Cognitive Biases](https://arxiv.org/html/2610.05461)|VERIFIED|方法/限制；特定侦探任务修辞干预，预筛偏差，预印本|
|X12|跨域迁移|[Query by Committee](https://collaborate.princeton.edu/en/publications/query-by-committee/)|VERIFIED|机构题录/摘要；仅作历史概念定位，不据此描述证明|
