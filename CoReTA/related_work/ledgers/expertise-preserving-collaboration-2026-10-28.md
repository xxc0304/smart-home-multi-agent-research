# 专长保护与意见修订：本轮来源

核查日期：2026-10-28。读取原文/原论文页面，不使用二手摘要的效果数字。新增条目目前为在线来源，是否有本地全文以 catalog 的 archived/link_only 字段为准。

| 工作 | 来源 | 本轮读取范围 |
|---|---|---|
| Multi-Agent Teams Hold Experts Back，Pappu 等，ICML 2026 | [正式记录](https://proceedings.mlr.press/v306/pappu26a.html)；[作者全文 v4](https://arxiv.org/html/2602.01011v4) | §3 实验专长定义；§4.4/4.5；§5；Table 2；相关附录。折中相关性不作对齐因果结论。 |
| When Identity Skews Debate，Choi 等，ACL 2026 | [正式页面](https://aclanthology.org/2026.acl-long.650/) | 官方元数据及摘要；匿名化机制，未据摘要复述具体效果数字。 |
| Peacemaker or Troublemaker: How Sycophancy Shapes Multi-Agent Debate | [预印本全文](https://arxiv.org/html/2509.23055) | 引言、§3 定义/指标、persona 干预及结果说明；本轮未独立核实正式录用身份。 |
| Easier to Mislead Than to Correct: Harmful and Beneficial Revision in LLM Conformity，Qu 等，2026 | [预印本 v2](https://arxiv.org/html/2606.01637) | 摘要、§3 实验及指标：模拟同伴、角色权威、两类修订分母；不声称真实专家能力干预。 |
| Demystifying Multi-Agent Debate: The Role of Confidence and Diversity，Zhu 等，2026 | [预印本 v3](https://arxiv.org/html/2601.19921) | §3/4，多样化初始化、置信度表达及使用的 RL 机制；没有把提示置信度等同已校准置信度。 |
| Minority Sentinel: When to Overturn Majority Voting in Multi-Agent LLM Debates，He 等，2026 | [预印本 v1](https://arxiv.org/html/2606.29270) | §3，三成员末轮 2:1 分歧、轨迹特征、外部语义审计、LightGBM；正文自述 workshop 身份，未独立核验。 |

对应项目分析：`research/expertise-preserving-collaboration-20261028/REVIEW.md`。

## 同一问题是否已被直接研究：补充查新

本节回应用户“有没有单篇完全研究我提出的问题”，区分同问题、已有解决方法与具体方法整体重复。Free-MAD 的预印本早已在 coordination 台账，本轮补核正式发表版；ICR 和 Not All Flips 是本轮新增的直接近邻。未下载新增 PDF，不把在线核读写成本地归档。

| 工作及元数据 | 原始来源 | 本轮核读范围与比较边界 |
|---|---|---|
| Beyond Final Accuracy: Auditing Communication in LLM Multi-Agent Systems；Shixuan Li、Wei Yang、Peiyu Zhang、Anzhe Cheng、Heng Ping、Paul Bogdan；arXiv:2610.01042v1，2026-10-01，预印本 | [ICR 全文](https://arxiv.org/html/2610.01042) | 引言、§2–3、§4.1/4.4、附录 A.3：直接问能否纠错同时保留正确答案；冻结初始轨迹、单跳方向事件、双方初始正确性分层、无消息复查对照；结构化策略按原题检查外部主张和自身推理，再以存活主张作答。核查提高保留同时降低纠错，选择性效果依任务与通道变化。属于直接问题研究和审计协议，不能说只讨论通信格式；未证明解决该权衡，也不以独立校准专长差异为主实验变量。 |
| Free-MAD: Consensus-Free Multi-Agent Debate；Yu Cui、Hang Fu、Haibin Zhang、Licheng Wang、Cong Zuo；Findings of ACL 2026 | [正式记录](https://aclanthology.org/2026.findings-acl.1600/)；[正式 PDF](https://aclanthology.org/2026.findings-acl.1600.pdf) | 正式 PDF §4.2–4.4、Algorithm 1、§5.1、§6.1、附录 E（PDF 第15页）：反从众提示、具体错误识别、允许有依据改答、不能判断时保留初答、全轨迹计分。正文讨论反从众造成固执，实验使用异质模型。直接方法近邻，不能把“异质团队”“不能只让成员顽固”作为它未涉及的差异；它也不等于已解决全部内容正确性判别。 |
| Not All Flips Are Conformity: Decomposing Stance Convergence in Multi-Agent LLM Debate；Xiqi Hao、Zengqing Wu、Yu-Xuan Qiu、Chuan Xiao、Ruiqi Xu、Shuyuan Zheng、Jianbin Qin；arXiv:2606.00820v2，2026-10-18，预印本 | [v2 全文](https://arxiv.org/html/2606.00820v2) | 最新摘要/引言、§3、§6.2–6.3：自省、立场、完整论证配对条件；区分改答来源、方向和群体收益。部署干预压低有害与有益采用，未检测到准确率收益；带真值筛选的诊断收益不得写成部署效果。没有沿用 v1 二手摘要。 |

本轮结论：核心问题已有直接研究，且已有方法；不能以“避免折中并保留纠错”声称新问题，也不能以“指定具体错点才改答”声称操作首创。当前草案尚未明确足以比较的算法增量，因此不认证方法新颖，也不凭相似阶段判定未来完整方法已被单篇覆盖。详见 `research/expertise-preserving-collaboration-20261028/NOVELTY_COVERAGE.md`。
