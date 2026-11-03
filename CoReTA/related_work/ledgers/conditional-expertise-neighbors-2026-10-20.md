# 来源核验与阅读范围

日期：2026-10-20。以下为主报告使用的十五项机制来源、两项问题锚点和一项边界对照。均以原始论文/正式记录确认存在与题名。没有复现实验或核验代码。状态描述限于实际确认，不将 arXiv 版本当作无录用证明。

| 编号 | 论文与确认身份 | 原始链接及实际阅读范围 |
|---|---|---|
| 1 | Pappu et al., Multi-Agent Teams Hold Experts Back，ICML 2026 | [正式记录](https://proceedings.mlr.press/v306/pappu26a.html)；本次复核记录，方法依据前轮 [v4 §3–5](https://arxiv.org/html/2602.01011v4)，见 topvenue-entrypoints-20261020/SOURCES.md |
| 2 | Li, Naito, Shirado, Systematic Failures in Collective Reasoning under Distributed Information in Multi-Agent LLMs，ICML 2026；HiddenBench | [正式记录](https://proceedings.mlr.press/v306/li26ej.html)；本次复核记录，方法阅读沿用前轮 [v4](https://arxiv.org/html/2505.11556v4) |
| 3 | Hou et al., Decomposing Uncertainty for Large Language Models through Input Clarification Ensembling，ICML 2024 | [正式记录](https://proceedings.mlr.press/v235/hou24b.html)，[v2 §3.1–3.6](https://arxiv.org/html/2311.08718v2)，含 Eq.3 与澄清策略 |
| 4 | Mu et al., ClarifyGPT: A Framework for Enhancing LLM-Based Code Generation via Requirements Clarification，PACMSE 1(FSE) Article103，2024 | [作者正式稿](https://linshi-website.github.io/paper/ClarifyGPT.pdf)，[DOI](https://doi.org/10.1145/3660810)；§3、§5.2、§7。旧 arXiv 题名不同，比较使用正式稿 |
| 5 | Edwards, Schuster, Ask or Assume? Uncertainty-Aware Clarification-Seeking in Coding Agents，2026 | [v3 §1/3](https://arxiv.org/html/2603.26233v3)，[作者页](https://nedwards99.github.io/)；作者声明 EMNLP Findings 录用，未独立找到 Anthology 条目；早期附录仅辅助，不混合不同版本设置 |
| 6 | Li, Wu, Meng, When and How Should an Agent Clarify? CIGAsk: Teaching LLMs to Clarify via Counterfactual Information Gain，2026 | [v1 元数据](https://arxiv.org/abs/2609.24290)，[§2–3](https://arxiv.org/html/2609.24290v1)；作者备注 EMNLP Findings 录用，未独立找到正式 Anthology 条目 |
| 7 | Wang, Lu, Knowledge Boundary Discovery for Large Language Models，AAAI 2026 | [正式 DOI](https://doi.org/10.1609/aaai.v40i40.40670)；原文 §3–4，熵与问题策略，非仅摘要 |
| 8 | Pappu et al., Self-Organizing Agent Teams Learn to Reason Together（SAT），2026 预印本版本 | [v1 元数据](https://arxiv.org/abs/2609.22682v1)，[全文](https://arxiv.org/html/2609.22682v1)；§2、Appendix A冻结协议/C轨迹/D最终选择；不推断正式录用 |
| 9 | Lin et al., AgentAsk: Multi-Agent Systems Need to Ask，ACL 2026 Long | [正式记录](https://aclanthology.org/2026.acl-long.1294/)，[PDF](https://aclanthology.org/2026.acl-long.1294.pdf)；§4、Algorithm1、Appendix A/D/F、Figure7提示词 |
| 10 | Wang et al., VulAgent: Hypothesis-Validation Driven Multi-Agent Architecture for Vulnerability Detection，Findings ACL 2026 | [正式记录](https://aclanthology.org/2026.findings-acl.928/)，[PDF](https://aclanthology.org/2026.findings-acl.928.pdf)；§3、Appendix D/E/G，核对主文与提示词条件状态差异 |
| 11 | Yuan et al., Verify Before You Commit: Towards Faithful Reasoning in LLM Agents via Self-Auditing（SAVeR），ACL 2026 Long | [正式记录](https://aclanthology.org/2026.acl-long.1440/)，[PDF](https://aclanthology.org/2026.acl-long.1440.pdf)；§3、Table3、Appendix A–C，区分局部编辑与条件扰动 |
| 12 | Peng et al., StateWise: Diagnosing and Repairing Persistent Operational State Before Agent Actions，2026 预印本版本 | [v1 全文](https://arxiv.org/html/2610.05241v1)；§3–4，记录干预、行动比较、证据核查及持久修订 |
| 13 | Jiang et al., Collaborative Chain-of-Agents for Parametric-Retrieved Knowledge Synergy（CoCoA），2025 预印本版本 | [v1 全文](https://arxiv.org/html/2508.01696v1)；§2、Algorithm1、§3.1；本次未另核后续录用，conditional induction是按候选答案生成知识 |
| 14 | Sá, Alcântara, Cooperative Dialogues with Conditional Arguments，AAMAS 2012 | [官方全文](https://www.ifaamas.org/Proceedings/aamas2012/papers/4C_2.pdf)；§3–4，Definition7、Example6、接受与共同本体前提 |
| 15 | Ma, Russo, Broda, Lupu, Multi-agent Confidential Abductive Reasoning（DAREC2），ICLP 2011 | [正式记录](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ICLP.2011.175)，[全文](https://drops.dagstuhl.de/storage/00lipics/lipics-vol011-iclp2011/LIPIcs.ICLP.2011.175/LIPIcs.ICLP.2011.175.pdf)；§3–4、路由/回溯及定理语义，不与 AAMAS 前身版本混用 |
| 16 | de Kleer, An Assumption-based TMS，Artificial Intelligence 1986；算法采用1988修订原文 | [1986条目](https://www.sciencedirect.com/science/article/abs/pii/0004370286900809)，[1988算法](https://dekleer.org/Publications/Corrected%20AAAI88.pdf)；1986全文未成功提取；读修订稿 §2–3 的依赖、支持集合与nogood传播 |
| 17 | Cobleigh, Giannakopoulou, Păsăreanu, Learning Assumptions for Compositional Verification，TACAS 2003 | [正式 DOI](https://doi.org/10.1007/3-540-36577-X_24)，[NASA原稿](https://ntrs.nasa.gov/api/citations/20030017771/downloads/20030017771.pdf)；§3–5，L*与teacher；NASA元数据为2002技报且多列Clancy，未将技报作者表套入正式版 |
| 18 | Scofield, Multi-Agent Constraint Factorization，2026 预印本版本 | [v1 全文](https://arxiv.org/html/2601.15077v1)；§3–9，形式假设与文本对应；不作为LLM正确性的实证来源 |

## 未作为主报告方法证据的来源

EPRAG：出版条目可定位，正文获取失败，不据摘要断言方法覆盖。Corollary：项目仓库，不是已确认学术论文。SEMA-RAG 与 CoQ：只定位候选片段，未完成方法阅读，留在分支检索记录。NeurIPS 2024 semi-open-ended QA 边界感知：在澄清分支作补充，主报告不将其当条件组合方法。

## 版本纠正

- Ask or Assume、CIGAsk 在作者原始来源已有 Findings 录用声明，应保留该信息；尚未独立确认正式条目，与仅核验预印本的状态区分。
- KBD 已有 AAAI 2026 正式 DOI，不再只标 arXiv。
- SAVeR、AgentAsk 属 ACL 主会，VulAgent 属 Findings。
- 公开原文案例、形式推导与本项目实验分开，本轮没有产生新实验结果。
