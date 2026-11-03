# Motivation与贡献增量定点复核

2026-11-01。范围：回答当前方向是否值得继续，不重开大规模方向探索/实验设计。使用aris:novelty-check，复用2026-10-29本地两份查新报告，补查2024–2026公开索引并核原始论文。不是穷尽所有文献；无实验、训练、付费批次或C/H正文读取。

## 判断

PROCEED：问题有明确研究意义，存在合理且值得验证的贡献空间。当前还没有实证贡献成立。最有价值的潜在增量是：在真实任务优势成员的完整团队协作中，定位哪些可观测障碍阻断优势转化，检验其受控响应及边界，解释怎样改善团队利用而保留有效纠错。无需将总问题再缩为很多特殊条件，也不预设新架构或所有任务显著增益。

独立校准、同底座LoRA、交流×身份四组、两轮讨论本身是研究设计，不自动成为主要创新。仅再次发现团队低于专家、再列失败类型或只区分正确保留/纠错，增量较弱；把已知工具用于得到可推广的新发现，可以形成研究贡献。最低有竞争力证据：可信专家对象；匹配私人复议/完整团队对照；一种有解释力且经受控操作检验的瓶颈或边界；新题复验及正反纠错/成本。负结果若稳定解释重要现象或现有方法边界，也可以有价值。

## 核验的近邻与差异

- [Hold Experts Back v4](https://arxiv.org/html/2602.01011v4)：已研究识别/利用、折中相关性、行为及消融。不能声称其只发现现象而未分析原因。项目增量须为具体受控发现或改进。
- [Understanding Communication Failures](https://arxiv.org/html/2610.32060v1)：失败语料分类、动态与少数信号等，正文明确标签不等于单一因果真值。专家条件本身不足以证明差异，优势损失的验证性解释才有价值。
- [ICR](https://arxiv.org/abs/2610.01042)：固定初始轨迹/无消息控制/纠错与保留，已排查额外思考并比较接收政策。项目不能把这些指标和控制称首次。
- [PBT, NAACL2025](https://aclanthology.org/2025.naacl-long.412/)：训练平衡有益/有害说服，并验证强弱模型合作。双向平衡目标已有成果，不等于专家完整团队瓶颈全部被解决。
- [SAT](https://arxiv.org/abs/2609.22682)：学习组织策略并研究可展示性与团队收益，挑战/修复/综合流程已有先例。
- [MedAgentAudit v3](https://arxiv.org/abs/2510.10185)：医疗角色协作的证据审计/虚假共识，与独立校准的实际优势成员不同；不据阶段术语相似判定完全重合。

额外摘要核验（未据此给全文覆盖结论）：[Easier to Mislead](https://arxiv.org/abs/2606.01637)为模拟同伴共识/权威线索及正负改答；[One Axis No Brake](https://arxiv.org/abs/2609.18998)为自知正确性限制与同伴从众；[Narrowing the Collaboration Gap](https://arxiv.org/abs/2610.19215)为私有信息下校准概率交流。它们约束泛泛的“选择性坚持/改善沟通”原创宣称，未直接建立本项目的完整贡献是否重复。后续若拟议干预落入这些具体方法，应再做定点全文对照。

## 核心claim检索覆盖

1. 校准专家与完整团队损失定位：expert/calibrated expert/causal intervention；expert+self-reflection；expertise+causal。
2. 贡献分享/接收/整合：expertise preservation+evidence uptake；expert+communication+retention；expert+sharing+uptake。
3. 有害影响与有效纠错：expert team individual revision aggregation；resisting+accepting persuasion；expert+harmful+correction。

覆盖近6个月arXiv，兼用ACL Anthology/原始会刊入口及既有本地文献。来源不同版本以正文链接为准，不用搜索摘要把近邻判为完全覆盖。

## 下一步与阶段自审

fresh同家族评审亦建议PROCEED，原文见001-review.response.md；强调当前薄弱处是尚无超出已知现象的受控实证结果，而不是近邻存在。其最低证据建议与本轮主助手判断一致；same-family/provisional，不当作新颖性保证或接收承诺。

保留当前主线与v0.9执行顺序：实机→有限B0/V/C→B1成本/技术/开发→选最多1–2机制。本次PASS限意义/贡献定位咨询，不增加实验组、运行门槛或新架构。新证据若显示某具体机制/操作已被直接验证，则改变贡献表述或操作，而非凭邻近研究否定总问题。
