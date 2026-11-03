# 来源与读取范围

日期：2026-10-20。本文献表服务于 REPORT.md。会议身份通过官方记录核验；有作者版本的项目不宣称全文与正式终稿逐字一致。方法未独立复现。

## 主报告十篇主会案例

| 编号 | 论文与正式身份 | 正式一手入口 | 方法依据及阅读范围 |
|---|---|---|---|
| 1 | Multi-Agent Teams Hold Experts Back，ICML 2026 | https://proceedings.mlr.press/v306/pappu26a.html | https://arxiv.org/html/2602.01011v4 ，§3–5、表2、附录信息控制与行为分析；官方所链PDF获取受限 |
| 2 | Systematic Failures in Collective Reasoning under Distributed Information in Multi-Agent LLMs，ICML 2026 | https://proceedings.mlr.press/v306/li26ej.html | https://arxiv.org/html/2505.11556v4 ，任务构造、§6.3–6.4干预；身份与正式摘要核对 |
| 3 | Debate or Vote: Which Yields Better Decisions in Multi-Agent Large Language Models?，NeurIPS 2025主会 | https://proceedings.neurips.cc/paper_files/paper/2025/hash/934252acd87f254d5d4672fbde283bd2-Abstract-Conference.html | 同站 /file/934252acd87f254d5d4672fbde283bd2-Paper-Conference.pdf ，§3–5及定理条件；oracle与多数引导分开 |
| 4 | Multi-Agent Collaboration via Evolving Orchestration，NeurIPS 2025主会 | https://proceedings.nips.cc/paper_files/paper/2025/hash/f1320d2e2842169c6fc89dcbd80e94d0-Abstract-Conference.html | https://proceedings.neurips.cc/paper_files/paper/2025/file/f1320d2e2842169c6fc89dcbd80e94d0-Paper-Conference.pdf ，方法与组织演化分析；不将结构关联说成单模块因果消融 |
| 5 | AgentNet，NeurIPS 2025主会 | https://proceedings.neurips.cc/paper_files/paper/2025/hash/9a379c1b05793d1c42dc832269834515-Abstract-Conference.html | https://papers.nips.cc/paper_files/paper/2025/file/9a379c1b05793d1c42dc832269834515-Paper-Conference.pdf ，§3–4及路由/演化对照 |
| 6 | SYMPHONY: Synergistic Multi-agent Planning with Heterogeneous Language Model Assembly，NeurIPS 2025 | https://papers.nips.cc/paper_files/paper/2025/file/537d89d08145ce0432bdb7e0bc9759e1-Paper-Conference.pdf | 正式PDF §3–4、表5、附录I/J |
| 7 | Multi-Agent Design: Optimizing Agents with Better Prompts and Topologies，ICLR 2026主会 | https://iclr.cc/virtual/2026/poster/10010348 | https://arxiv.org/html/2502.02533v2 ，§2–4、阶段/搜索消融与局限；不以早期预印本日期否认正式届次 |
| 8 | Stochastic Self-Organization in Multi-Agent Systems，ICLR 2026主会 | https://iclr.cc/virtual/2026/poster/10007145 | https://arxiv.org/html/2510.00685v2 ，§2–3与附录F；动态图重构贡献与整体提升分开 |
| 9 | AgentAsk: Multi-Agent Systems Need to Ask，ACL 2026主会 | https://aclanthology.org/2026.acl-long.1294/ | https://aclanthology.org/2026.acl-long.1294.pdf ，§3–5、表1–3、局限；轻量模块和GPT-5澄清器数字分开 |
| 10 | Scaling External Knowledge Input Beyond Context Windows of LLMs via Multi-Agent Collaboration，ACL 2026主会 | https://aclanthology.org/2026.acl-long.468/ | https://arxiv.org/html/2505.21471v2 ，§3–5、图5与局限；正式PDF超工具大小限制 |

## 分支中的补充案例

| 论文与身份 | 正式入口 | 范围 |
|---|---|---|
| VulAgent: Hypothesis-Validation Driven Multi-Agent Architecture for Vulnerability Detection，Findings ACL 2026 | https://aclanthology.org/2026.findings-acl.928/ | 官方PDF方法、验证消融和CWE控制；明确非ACL主会 |
| Why Do Multi-Agent LLM Systems Fail?，NeurIPS 2025 Datasets and Benchmarks Track | https://papers.nips.cc/paper_files/paper/2025/hash/b1041e52d3be19f0a9bc491657488e4a-Abstract-Datasets_and_Benchmarks_Track.html | 正式PDF正文、MAST分类/标注与附录干预；不是主会方法轨道 |
| Benefits and Limitations of Communication in Multi-Agent Reasoning，ICLR 2026 | https://proceedings.iclr.cc/paper_files/paper/2026/hash/e9372abc370b8302459abdce4bdce5a5-Abstract-Conference.html | 正式PDF §1–6、主要命题、附录F/G；未逐项审数学证明 |
| TeamTR: Trust-Region Fine-Tuning for Multi-Agent LLM Coordination，ICML 2026 | https://proceedings.mlr.press/v306/xie26o.html | CONTROL.md补充；作者v2方法，不进入主报告十篇核心综合 |

## 公开评审标准

- NeurIPS 2025 Reviewer Guidelines：https://neurips.cc/Conferences/2025/ReviewerGuidelines 。已读Review Form中Quality/Significance/Originality；明确原始性可来自新见解和有理由的新组合。
- ICLR 2026 Reviewer Guide：https://iclr.cc/Conferences/2026/ReviewerGuide 。已读研究目的、新知识和社区价值标准。

正式录用核验不等于已读取审稿意见，也不等于认定每个具体组件是录用原因。后续引用数值以三份分支笔记标注的模型、子集、版本和指标为准。
