# 来源与实际核读范围

日期：2026-10-30（Asia/Shanghai）。本轮范围：原始案例核验、3任务选择和一个专家最小方案。不是新一轮全领域综述。

## 本地原始证据

- [8例完整请求/响应摘录](../expert-team-assets-20261029/CASE_SEED_8.json)，对应原始runs中的requests.jsonl及.raw.txt；本轮29个文字事件给具体槽位/请求行号。
- 作者两份hidden_generated原文件对应019：GPT-4.1 conditions[0].runs[104]，Gemini-2.5-Pro conditions[0].runs[100]。本轮核round2收件及round3/5/6核验声称的时序；没有原隐藏事实分配映射和独立工具回执。
- [8篇近邻矩阵](NEAREST_WORK_MATRIX.md)来自其中明确列出的既有核读；只读提取任务没有新通读/联网，不称独立审稿或完整最新查新。

## 官方任务来源

| 来源 | 实际动作 | 文件/限制 |
|---|---|---|
| [MuSiQue README](https://github.com/StonyBrookNLP/musique/blob/main/README.md) | GitHub连接器读全文快照 | source_snapshots/musique_README.md；许可、任务、源单跳泄漏警示 |
| [MuSiQue评分](https://github.com/StonyBrookNLP/musique/blob/main/evaluate_v1.0.py) | 读源码 | musique_evaluate_v1.0.py；未执行上游训练/数据脚本 |
| [下载脚本](https://github.com/StonyBrookNLP/musique/blob/main/download_data.sh)和[raw文件索引](https://github.com/StonyBrookNLP/musique/blob/main/.all_data_information.json) | 读源码/JSON，未执行shell | musique_download_data.sh和musique_all_data_information.json；原脚本的安装/删除命令未运行 |
| [raw转换](https://github.com/StonyBrookNLP/musique/blob/main/raw_data_to_official_format.py) | 读源码核schema/标签过滤 | musique_raw_data_to_official_format.py；本地只实现检查用受限提取，未称完整official转换 |
| [MuSiQue论文](https://aclanthology.org/2022.tacl-1.31.pdf) | 只读源核查任务核§5、表2 | 通过原文核划分、20段和规模；未下载新PDF到论文库 |
| [HotpotQA官网](https://hotpotqa.github.io/)及[官方代码](https://github.com/hotpotqa/hotpot) | 官网＋README/schema/评分核读 | hotpot_README.md、hotpot_evaluate_v1.py；未下载完整Hotpot数据，本轮入口访问失败不等于任务不可用 |
| [Hotpot论文](https://aclanthology.org/D18-1259.pdf) | 源核查任务核Figure1/§3/表1 | 支持句/样例及划分依据，未下载新PDF |
| [GSM8K官方仓库](https://github.com/openai/grade-school-math) | 官方README/格式/评分及首例来源核查 | 已有本地train资产；本轮未新下载全数据，不确认底座预训练无污染 |

GitHub快照为访问日main/master文本，不代表所有文件已统一固定同一commit。后续正式数据/评分必须再冻结版本；不把已保存几个文件称完整复现。

## 真实有限数据与分词

MuSiQue作者raw train文件ID `1X3rJEAofrJ_tI55U2bquCZ-StVeaWnWu`，dev `1TRXU68wveSehVbQrRRtWsUsFkKUF43QS`，均来自官方索引。通过公开usercontent下载端点，每份最多读取2MB前缀，保存30条完整JSONL；不是Google Drive连接器内的私人文件，也未遍历个人Drive。

下载证据：[MUSIQUE_PREFIX_INSPECTION](MUSIQUE_PREFIX_INSPECTION.json)；规范位置[data/external/musique-inspection-20261030](../../data/external/musique-inspection-20261030/README.md)。这些prefix全部两跳，不能估整个题库难度/长度分布；dev已查看题登记为开发暴露。

仅获取Qwen3-4B官方模型metadata和固定revision的tokenizer.json，未下载模型权重。revision `1cfa9a7208912126459214e8b04321603b3df60c`，具体URL/摘要在[data/external/qwen3-4b-tokenizer-20261030/PROVENANCE.json](../../data/external/qwen3-4b-tokenizer-20261030/PROVENANCE.json)。用已有tokenizers库做CPU分词，未运行LLM生成、训练或计费API。结果[MUSIQUE_INPUT_INSPECTION](MUSIQUE_INPUT_INSPECTION.json)只测任务文本，不含聊天/思考/讨论历史。

## 技能与分工

已读research-lit和experiment-plan说明。research-lit的源提取按要求用两个fresh只读子任务分别核官方数据与已有近邻；父助手负责原始8例、实际下载/分词、取舍与写入。experiment-plan用于组织主张—证据—判据，不把尚无方法结果的项目冒充完整确认论文。阶段末是助手自审，不声称独立人类或导师评审完成。
