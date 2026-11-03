# CoReTA 数据与任务说明

`data/` 是本项目的规范数据目录。任务来源、候选集、适配任务和冻结任务包分开保存；不把任务开发数据、诊断样本和留出评价集混作一个集合。

## 目录导航

| 目录 | 用途 |
|---|---|
| [data/expert-mechanism-inputs-20261030-v0.2/](data/expert-mechanism-inputs-20261030-v0.2/README.md) | C160/D8真实题面352独答输入、56待真实初答接收依赖；7条件手写演示/旧响应适配与private_scoring严格分开；0新模型输出。v0.1保留过长草案。[离线审核](implement-stage/expert-mechanism-inputs-20261030/EXPERIMENT_REVIEW.md)。 |
| `data/source/` | 外部来源的代码或数据快照及来源记录。快照不自动代表上游提交已固定，也不代表其中代码已执行。 |
| [data/expert-transfer-annotation-20261030-v0.1/](data/expert-transfer-annotation-20261030-v0.1/README.md) | 8例/7题独立核验包：77本地+128作者事件，A事实/B过程/C参考；输入原文/源映射核对、两份空表，0人工提交。[规范与说明](research/expert-annotation-pilot-20261030/REVIEWER_START.md)，非模型训练数据或机制占比样本。 |
| [data/external/musique-v1.0-20261030/](data/external/musique-v1.0-20261030/README.md) | 官方完整Ans train19,938/dev2,417；原件/输入/评分分离；C160/D80/H内部候选2360/T可选2000，交叉剔除与暴露排除见[报告](research/musique-data-preparation-20261030/REPORT.md)。0模型调用，非官方test或科学结果。 |
| [data/external/musique-inspection-20261030/](data/external/musique-inspection-20261030/README.md) | 官方作者raw train/dev各30条有界前缀；输入/目标分离、已暴露题哈希，非完整数据或冻结切分，全为两跳。 |
| [data/external/qwen3-4b-tokenizer-20261030/](data/external/qwen3-4b-tokenizer-20261030/README.md) | 固定官方revision的分词器，仅读长度，无模型权重或生成；后续上下文需另计讨论历史。 |
| [data/external/pbt-preprocessed-20261029/](data/external/pbt-preprocessed-20261029/README.md) | PBT官方170MB预处理归档，实际读取10主Arrow表；偏好/SFT材料不等于完整专家团队轨迹，模板和缓存不重复计样本。 |
| [data/external/hiddenbench-results-20261029/](data/external/hiddenbench-results-20261029/README.md) | 新下载两模型full-profile原结果，每模型650运行/65场景；全员知情团队、1轮，非单agent或与15轮hidden的纯信息对照。 |
| `data/task-source-audit-20261021/` | 原始任务来源、许可、哈希和改编审计。 |
| `data/task-candidates/` | 候选任务与筛选资料；不能把候选池结果当作留出测试。 |
| `data/task-packs/` | 输入权限、任务实例与参考答案分离后的可用任务包；各任务 README 说明具体构造和评分。 |
| `data/dataset-selection-20261022/` | 任务选型、种子和数据集清单。 |
| `data/task-packs/hiddenbench-grounded-dev-20261024-v1/`、`data/task-packs/hiddenbench-local-contribution-dev-20261025-v1/`、`data/task-packs/hiddenbench-workboard-dev-v1/` | HiddenBench 派生的开发/诊断实例；属于适配数据，不称作原基准的完整复现。 |
| `data/task-packs/moon-survival-v1/`、`data/task-packs/student-president-dev-v1/` | 月球生存与学生会长任务包；以各自 README、权限矩阵和冻结文件为准。 |

## 当前可追溯任务族

- Moon Survival：`data/task-packs/moon-survival-v1/README.md` 说明任务来源、分散 / 集中信息条件、可见权限和排序评分。原始答案与索引保存在离线评估侧。
- HiddenBench 衍生任务：按项目内的源审计、选择清单和版本化开发目录追溯。任何改编必须标明与原始基准的差异，且隔离答案、来源名和其他成员私有资料。
- 学生会长与日程等早期开发任务：以各自数据包和 run 的冻结文件为准；单一情景不称为大型通用数据集。
- MATH / HumanEval 的历史实现和评分链路：见 `scoring/`、`engineering/` 和对应的 `runs/`；它们不自动成为当前主实验任务。

## 处理约定

1. 每个新批次引用具体的任务包版本、来源、数据划分和标签权限；优先使用 run manifest 中的文件哈希。
2. 原始材料只读保留；改编副本放进版本化任务包，记录来源、许可、变换和 SHA-256。
3. 标签与参考答案只对评分脚本可见，不放入 Agent 请求、公开数据或提示元数据。
4. 按预定任务子集报告结果。不同任务族不直接池化；重复采样不当作新的独立任务。
5. 数据审计与任务选择记录见 `data/task-source-audit-20261021/`、`data/dataset-selection-20261022/` 和各任务包 README。
