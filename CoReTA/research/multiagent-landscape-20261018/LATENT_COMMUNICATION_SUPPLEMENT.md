# 潜在通信补查：不能只研究自然语言消息

主执行者在专题合并后发现通信表示覆盖不足，于2026-10-18补查：`LatentMAS arxiv`、`Cache-to-Cache multi agent communication arxiv`、`LLM agents latent communication CIPHER 2025 2026`。以下三项均打开原始论文页；本次只读到原始摘要/元数据，不引用未经全文核验的倍数收益。

| 论文 | 状态、版本与读取层级 | 实际方法 | 范围和边界 |
|---|---|---|---|
| [Latent Collaboration in Multi-Agent Systems](https://arxiv.org/abs/2511.20639v4), Zou et al. | 2026-08-03v4；arXiv作者声明ICML2026 Spotlight；原始摘要 | LatentMAS使用hidden embeddings进行latent生成，借共享latent working memory传递内部表示；作者称端到端training-free | 数学/科学/常识/代码九基准；本次不将理论lossless等同现实所有语义无损，更不将减少文本token当成全部计算为零 |
| [Cache-to-Cache: Direct Semantic Communication Between Large Language Models](https://proceedings.iclr.cc/paper_files/paper/2026/hash/474ada926b331d78f06d95e8913111cc-Abstract-Conference.html), Fu et al. | ICLR2026官方记录；原始摘要 | 神经网络投影融合源/目标KV-cache，learnable gating选择目标层，避免显式中间文本 | 需要模型内部表示与学习映射；不是可直接插入普通封闭文本API的提示技巧 |
| [Enabling Agents to Communicate Entirely in Latent Space](https://aclanthology.org/2026.acl-long.1248/), Du et al. | ACL2026官方记录；原始摘要 | Interlat以last hidden states直接通信，并通过额外学习压缩过程减少开销，含异构模型实验 | 作者定位为可行性研究；不能将探索性结果当跨模型任意互通已解决 |

综合判断：通信优化包括通路、语义内容、可见上下文、跨任务记忆和表示介质。最后一项会把可行性条件从“能调用API”改变为“能访问/操作模型内部状态，必要时训练接口”。这与任务级组织框架有关但不等同，不能将潜在通信论文直接认作跨角色交接与责任管理方法。

CIPHER、DroidSpeak、Latent Cache Flow检出为邻接线索，本轮不再据二手描述写机制细节。三项已核核心足以表明该分支真实存在，不宣称穷尽。
