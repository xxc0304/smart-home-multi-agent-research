# 设计来源与证据边界

日期：2026-10-22。本轮只做设计、原文核对与审查；没有新能力实验。

| 来源 | 可以借鉴/支持 | 不能据此宣称 |
|---|---|---|
| [LLM-based Multi-Agent Blackboard System, §3](https://arxiv.org/html/2510.01285v2) | 请求广播；持有分区知识的助手自行响应；当轮响应相互隔离 | 无请求时的机会发现已经解决；助手判断必然正确 |
| [LMAD, §3](https://arxiv.org/html/2608.01463v1) | 局部推理定位与修订已有先例；其论文区分协议接受与真值验证 | 局部修订本身是我们的创新；其与我们完整机制完全等同 |
| [AHRQ TeamSTEPPS Pocket Guide, pp6–7](https://www.ahrq.gov/sites/default/files/wysiwyg/teamstepps-program/teamstepps-pocket-guide.pdf) | 闭环沟通与 check-back 用于核对理解 | 发送者确认即可验证知识和解答真值；在人类有效即可推出LLM有效 |
| [Carlile 2002](https://people.bu.edu/carlile/docs/Pragmatic%20View%20of%20Knowledge%20(Carlile).pdf) | 共同工作对象有助于不同知识围绕具体实践建立联系 | 给模型共享一个文档就一定产生专长互补 |
| [本地漏检诊断](../../REVIEW_MISS_DIAGNOSIS_20261021.md) | 正确数值与错误排序共存；检查者确实收到产物和后果核查要求 | 没收到产物是主因；只加一句认真检查就能修复 |
| [本地相同初始输入对照](../sbp-diagnostic-v1/CONTROLLED_COORDINATION_PARTIAL_20261021.md) | 两个错误输入配对中两法均未完全修好；一次 CoReTA 更新数值未同步数组 | 证明CoReTA总体无效；证明普通讨论永远好；证明本候选已有效 |
| [本地阶段比较](../../design/expertise-handoff/application-core-v2/SBP_PROCESS_COMPARISON_AUDIT_20261021.md) | 方法间差异可从初始生成开始，需要隔离该因素 | 端到端差异可以全部归因于下游协调 |

黑板原文的独立回复安排启发“同一快照下独立提交”；本方案后续把已试用贡献及实际结果公开，是我们拟研究的交互选择，不是该论文原有全部流程。check-back扩展为检查实际使用产物，是设计迁移，不是宣称原指南已验证这套LLM机制。

这些来源够支持当前设计动机，但不构成全面查新完成。本轮对已有原文作定点核对；未做新的系统性文献综述。新颖性仍需在固定机制后与最接近方法逐项比较。
