# MuSiQue完整数据准备与评分核验

2026-10-30。为研究“专家优势为何不能转化为团队收益，并保留有益纠错”准备可比较的数据与评价合同。只执行CPU下载、数据处理、分词和评分校验，未调用模型、训练或购买算力。当前无GPU，4090非前提。

- [交付报告与取舍](REPORT.md)：数量、实际交叉、长度、限制和下一步。
- [来源与原始文件哈希](SOURCE_MANIFEST.json)：官方发布的v1.0归档，仅解出Ans train/dev及作者单跳防泄漏黑名单；归档中test/Full成员未打开。
- [全量字段/重复/长度审计](CORPUS_AUDIT.json)。
- [版本化角色、题号、分配及文件哈希](SPLIT_MANIFEST.json)：H是确认候选池，具体科学实验与样本量仍待冻结。
- [实际文件与评分校验](STAGE_CHECKS.json)。所有评分数值是人工构造的核验样例，**不是实验结果**。
- [官方评分文件清单](OFFICIAL_SCORER_MANIFEST.json)、[上游许可](official_scorer/LICENSE)。
- [已暴露dev题的raw→official映射](exposure_mapping.jsonl)。
- [使用与复跑](USAGE.md)。完整原始数据、输入与评分目标存放在项目规范data目录；见[数据目录说明](../../data/external/musique-v1.0-20261030/README.md)。

本阶段是助手自审。人类独立试标、导师判断、专家优势校准、模型端到端预检和团队效应均未完成；不能从数据准备PASS推导它们已成立。
