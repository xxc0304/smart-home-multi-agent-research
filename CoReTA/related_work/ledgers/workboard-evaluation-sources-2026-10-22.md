# 数据选型来源核对

2026-10-22。只读论文、官方公开仓库及本地固定快照；下载源码未执行。本轮无新模型实验。

| 来源 | 本轮核对内容 | 如何使用 |
|---|---|---|
| [HiddenBench正式论文](https://proceedings.mlr.press/v306/li26ej.html) | 65任务、分散信息设置、研究目标 | 主评价候选的任务相关性 |
| [HiddenBench v4 §6.3](https://arxiv.org/html/2505.11556v4) | Share-All提示与Reveal-All机械披露不同；干预结果限18题子集 | 保留强制披露基线，不能把原结果外推65题 |
| [HiddenBench作者仓库](https://github.com/Yassellee/HiddenBench_ICML) | 数据入口、HF作者发布、benchmark_short、评分代码 | 确认已有本地HF来源；不混用第三方复现 |
| [官方benchmark.py](https://github.com/Yassellee/HiddenBench_ICML/blob/main/src/hiddenbench/benchmark.py) | 字段、标签与加载约定 | 输入投影必须隔离correct_answer及源name |
| [官方metrics.py](https://github.com/Yassellee/HiddenBench_ICML/blob/main/src/hiddenbench/metrics.py) | 全员平均准确/严格多数规则 | 与我们的单团队答案指标区分，不直接比较原文数值 |
| [Experts Back v4 §3与附录](https://arxiv.org/html/2602.01011v4) | 心理任务、信息分配和团队设置 | 学生会长开发任务的出处，不把一个情景说成大数据集 |
| [InformativeBench论文附录C–D](https://arxiv.org/html/2406.14928) | 日程任务目标与半小时时间格 | 第二类任务的数学目标 |
| [iAgents官方data README](https://github.com/thunlp/iAgents/blob/main/data/README.md) | 三类任务与公开生成pipeline | 采用Schedule，明确数据不是当前已下载的固定大测试集 |
| [Schedule README](https://github.com/thunlp/iAgents/blob/main/data/Schedule/README.md) | 日程、LLM对话、问答生成和可选数据库 | 本实验绕过对话/数据库，标为改编而非原版复现 |
| [Schedule原始生成器](https://github.com/thunlp/iAgents/blob/main/data/Schedule/schedule_generate.py)及[hard问答](https://github.com/thunlp/iAgents/blob/main/data/Schedule/dataset_generate_hard.py) | 六人、48格、全部共同空闲区间；静态源码审查 | 适配三Agent各两日程，生成和评分需另实现与核验 |
| [Einstein Puzzles作者仓库](https://github.com/Roihn/EinsteinPuzzles) | 行动环境、测试资源及模型评测要求 | 暂不扩展，避免双Agent环境硬改三人 |

## 本地证据

HiddenBench原数据快照与来源为`data/task-source-audit-20261021/`；本次65行结构盘点、开发/评价ID与Schedule计划种子为`data/dataset-selection-20261022/SELECTION_MANIFEST.json`。

本次公开源码下载保存于`data/dataset-selection-20261022/source/`，provenance逐文件记录URL和内容摘要；Git commit未解析，所以是内容固定快照，不声称固定上游提交。medium脚本下载失败记录保留，当前选择hard目标，不以未读取的medium代码作依据。

未下载或执行作者完整平台，未调用日程对话生成LLM，未加载官方模型结果来挑选本方法有优势的题。
