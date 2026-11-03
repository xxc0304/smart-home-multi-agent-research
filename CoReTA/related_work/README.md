# CoReTA 相关工作

这里集中放 CoReTA 已讨论文献的引用台账、阅读范围和本地论文文件。入口见 [`INDEX.md`](INDEX.md)，人读目录见 [`catalog.md`](catalog.md)，机器可读引用目录见 [`catalog.json`](catalog.json)。

## 现有材料

- `ledgers/`：从项目既有研究目录复制的文献目录与阅读范围记录；原始研究报告仍留在 `research/` 和 `refine-logs/`，不移动、不改写。
- `papers/`：已归档台账中 57 个不同 arXiv ID 的公开论文全文；每篇按论文和版本独立存放 `paper.pdf` 与来源说明，清单见 [`papers/README.md`](papers/README.md)。
- `catalog.json`：由 `build_catalog.py` 从 `ledgers/` 生成，保存标题、链接和出处。

## 本地原文状态

当前本地保存 57 个不同 arXiv ID 的 PDF；累计台账含 70 个不同 arXiv ID，另外13个ID目前记录在线来源。详见 [`INDEX.md`](INDEX.md) 与 [`papers/README.md`](papers/README.md)。其他会议/期刊页面及非论文来源仍由统一台账记录。当前目录有 214 个去重来源 URL，包含论文、代码仓库、基准与评审规范等。归档原文不等于已通读；阅读范围和核验状态见各来源台账。最新35篇分段核读的综合见[专长利用调查](../research/expertise-literature-survey-20261028/REPORT.md)。

## 维护规则

只把论文/基准/官方实现的来源记录到目录中，并区分论文、数据/代码和评审规范。保留原始阅读限制和核验状态；摘要级核验不写成全文阅读，预印本不误标正式发表。每条记录都保留原先讨论它的台账或报告路径。
