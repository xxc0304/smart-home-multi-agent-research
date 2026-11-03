# 方法视角：从抗从众到专长利用，已有方法在哪一层产生收益

日期：2026-10-28。依据 [冻结任务书](BRIEF.md)，本视角核读九篇改进/控制工作。逐篇元数据、实际机制、阅读范围、条件和缺口类型在 [METHODS.json](METHODS.json)。本次仅检索和阅读，不运行实验，也不对 CoReTA 的尚未确定方法给创新性分数。

## 1. 现有方法已经给出实质性进展，研究空间应从剩余问题中找

Free-MAD 的反从众提示与全轨迹计分、Demystifying 的置信表达/使用训练，都已越过“发现从众现象”，进入具体改进；DEAR 又把决策对象移到参考关系和采样行为，并在附录报告降低有害从众的同时提高有益纠错。因此，不能只用 ICR/Flips 的某些干预未取得选择性增益，概括所有改进方法都只能让 agent 更顽固。三者改善的是不同条件下的更新或决策，不能横向比较论文中的绝对数字后宣布哪种方法普遍最好。[Free-MAD](https://aclanthology.org/2026.findings-acl.1600/)、[Demystifying](https://arxiv.org/html/2601.19921)、[DEAR](https://arxiv.org/html/2608.03648v2)。

另一方面，SAT 不只是一个“检查—修复”流程的先例：它学习可复用组织策略，并在数学/物理套件给出超过强成员、匹配推理控制和独立答案 routing oracle 的证据；CortexDebate 与 DEAR 则通过调节谁看谁、输入多少同伴信息来改善关系，而不是先标定某人是专家后始终追随它。可以承认这些贡献成立，同时继续问在特定专长条件下哪些操作真正使优质贡献被利用；不能因为它们没有做本项目设想的每一项实验，就否定其已有收益。[SAT](https://arxiv.org/abs/2609.22682)、[CortexDebate](https://aclanthology.org/2025.findings-acl.495/)、[DEAR](https://arxiv.org/html/2608.03648v2)。

## 2. 按实际干预对象比较，而不是按名字和通用阶段比较

表：方法通过改变不同决策对象取得收益；相同研究目标不等于相同机制。

| 工作 | 实际改变什么 | 已验证的价值 | 对原始专家问题的证据边界 |
|---|---|---|---|
| Free-MAD | 改答指令、全历史答案计分 | 异质团队所测任务提高表现；部分任务反从众过度而固执 | 未展示原论文专家身份干预与强协同的同设置检验，不能据此宣布解决或失败 |
| Demystifying | 初始化候选多样性、训练置信表达与接收使用 | 提高候选覆盖；训练更新改善纠错和正确保持 | 主要同模型采样，数值置信并非天然可靠专长信号 |
| Peacemaker or Troublemaker | 不同成员合作/反对 persona | 混合配置优于一律附和或顽固，尤其所测异质组合 | 最佳网格配置展示条件潜力，不等于未知任务上的自动选择 |
| MAD-M² | 下一轮可见的整条推理 memory | 过滤能在部分模型/任务改善效果，客观方案可减少token | Table1收益不均；整答保留不直接证明局部有效部分被利用 |
| CortexDebate | 有向图、边权及参考对象 | 降上下文负担；以关系有用性改善正确观点修订 | 能力/置信/差异/参与度为proxy，不认证具体领域专家或当前主张真值 |
| DEAR | 学习参考mask与temperature/top_p | 四任务HCR降低、BCR提高；跨模型/跨域有收益 | HCR/BCR实验为同质Qwen3-8B逐轮少数→多数转移；异质性另测，不混作已知专家验证 |
| CONSENSAGENT | 失败触发、训练prompt optimizer、终答置信/一致性计分 | 题意澄清及提示引导提高多种团队效果、触发后收敛更快 | 推理时optimizer只看原问题，不能说它逐题读当前轨迹修正；训练成本和数据集依赖仍在 |
| Minority Sentinel | 末轮2:1改票 | 轨迹分类器可恢复一部分正确少数，优于所比直接LLM裁判 | 标签与阈值校准需求、样本少；未恢复的旧正确答与复杂分歧不在其决策空间 |
| SAT | 离线学习角色/阶段/参与/信息流策略库，部署后产certificate并选答 | 固定异质团队有迁移和超强单体证据；可以生成初始池中没有的解 | 知识/逻辑正确certificate存在而选择失败是实测缺口；demonstrability因果干预未完成 |

Free-MAD、Minority Sentinel 和 CONSENSAGENT 都保留跨轮信息，但处理方式不同：Free-MAD 用意见保持/转移的启发式累积分数，Sentinel 用带标注数据训练决策器，CONSENSAGENT 将置信与跨轮一致性纳入终答。它们说明“保存历史”是一种可用材料，而不是单独足以保证正确性的机制；本项目如果也保留历史，应比较如何利用这份材料，不必因为共享材料就认定整套方法重复。[Free-MAD](https://aclanthology.org/2026.findings-acl.1600/)、[Sentinel](https://arxiv.org/html/2606.29270)、[CONSENSAGENT](https://aclanthology.org/2025.findings-acl.1141/)。

## 3. 三组张力比“有无相似论文”更有研究价值

**独立性与可纠正性需要按条件调节。** Free-MAD 在部分弱模型任务观察到顽固，Peacemaker 的较好配置也不是人人最少附和；Demystifying 训练置信使用、DEAR 学参考关系则给出更具选择性的正面证据。由此提出的具体问题应是“何时、根据什么信号调整谁对谁的影响”，而不只是“能否让agent更坚定”。这个问题已有多种答案，本项目应找其中仍难处理的条件。[Free-MAD](https://aclanthology.org/2026.findings-acl.1600/)、[Peacemaker](https://arxiv.org/html/2509.23055)、[Demystifying](https://arxiv.org/html/2601.19921)、[DEAR](https://arxiv.org/html/2608.03648v2)。

**个体能力与对他人的帮助不同。** CortexDebate 在边权中加入观点差异和参与度，SAT 从历史协作中发现审计/修复角色，均说明只看整题独立准确率可能漏掉有用合作角色。这个认识已有工作，不应宣称首创；但它让“专长”从笼统的强模型称号，转向某类错误识别、局部修复或条件知识能否在团队中发挥作用。候选缺口是这些局部比较优势怎样被可靠地发现、验证并迁移，而不是默认给成员贴专长标签即解决问题。[CortexDebate](https://arxiv.org/html/2507.03928)、[SAT](https://arxiv.org/html/2609.22682)。

**产生正确内容与选中正确内容不是同一能力。** SAT 知识/逻辑团队的certificate覆盖与最终准确率有明显差距，Sentinel 只从末轮仍存在的两派答案中改选；MAD-M²则在更早的可见信息阶段作筛选。三者共同提示应先确认正确内容在哪一步丢失，再决定干预暴露、修订或选择。这里的价值不在重复“不能只看最终准确率”，而在解释一个具体任务/专长条件下，损失为何发生及何种机制能恢复它。[SAT](https://arxiv.org/html/2609.22682)、[Sentinel](https://arxiv.org/html/2606.29270)、[MAD-M²](https://arxiv.org/html/2603.20215)。

## 4. 候选研究问题及缺口性质

| 候选问题 | 文献依据 | 缺口性质 | 哪些表述会过度 |
|---|---|---|---|
| 在领域/局部优势已明确但与多数意见冲突时，参考策略怎样使用优势证据？ | DEAR/Cortex调关系；SAT学角色；Hold Experts Back提供原动机（由其他视角核读） | 需要进一步逐篇确认的特定条件，不是全领域空白断言 | “没人研究动态信任/参考关系”已被上述工作否定 |
| 如何把可生成的正确局部依据变成接收者可辨认、可用的依据？ | SAT知识/逻辑选择差距及demonstrability；MAD-M²过滤依赖接收能力 | 已观察瓶颈与机制推断相结合；具体条件/操作仍待界定 | “只加证据字段即可解决”“提高demonstrability已有因果证据” |
| 已有策略在哪些任务把抗从众变成固执，哪种关系/置信学习缓解这种失配？ | Free-MAD负面条件与Demystifying、DEAR正面条件对照 | 可做解释性实证，也可发展机制，不要求先有宏大新架构 | “所有抗从众方法都会同时抑制有效纠错”不符正面结果 |
| 少数真值恢复能否在独立校准和分布变化下保持净收益？ | Sentinel标注/阈值需求，DEAR跨域效果变化 | 作者明示未验证与已有结果边界 | “分类器正收益意味着部署无风险”或反向“阈值有风险所以方法无用” |

这些问题值得阅读和比较，不是已选课题，也不是必须同时解决的清单。特别是第一项还要与专长识别、路由和信息互补视角合并，才能判断缺口是否真实。当前不建议为了显得新颖继续堆模块；也不要求文献中所有已有操作都被避开。

## 5. 检索与核验日志

第一轮宽搜（2026-10-28）：
- multi agent debate anti conformity expertise preservation methods 2026
- "multi-agent debate" "sycophancy" mitigation 2026
- "Multi-Agent Debate with Memory Masking"

第二轮按回收论文与引文缩窄：
- "Group Perspective Matters" "Hao Wu"
- "CONSENSAGENT" "Pitre"
- "Peacemaker or Troublemaker" "Yao" ICLR 2026
- "Self-Organizing Agent Teams Learn to Reason Together"
- "CortexDebate" multi agent
- "multi agent debate" "expertise" "anti-conformity"
- "Group Perspective Matters" "NeurIPS"

核验路径为正式ACL/OpenReview/NeurIPS元数据或arXiv作者页 → 原文方法/结果/限制；已有本地PDF另用pypdf核读。正文技术论断不使用聚合站、博客或检索摘要的数字。九篇均通过存在性与所用论断核对。Peacemaker和Demystifying正式录用身份未独立核实，记所读预印本；DEAR按v2六作者，不沿用v1七作者。NeurIPS官方Downloads含准确题名并链接poster/154678，详情cache miss，不伪称读到正式排版全文。Minority Sentinel作者实验室明确workshop展示且无archival proceedings，不能标为SIGIR主会。

本视角排除或移交：
- From Debate to Decision / Conformal Social Choice：与安全提交/校准关系大，已发父代理由评价视角核读，本文件不据摘要写机制结论。
- AgentAuditor：Sentinel引文线索提示关键分歧审计，但本视角未读原论文，已移交；不将二手描述当证据。
- 同名社区Free-MAD实现：不作为论文作者实现或复现结果。
- 人类/AI共决策及对抗说服：分别属相邻与反证视角，本视角不扩展成另一个综述。

