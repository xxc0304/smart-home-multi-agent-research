# 首个专家任务选择

2026-10-30。结论：**优先MuSiQue-Ans的给定上下文多跳问答；HotpotQA distractor作为直接备选；GSM8K只作可选技术检查/后续外推，不作为当前证据机制主任务。** 这是任务适配决定，不是认定该场景本身新颖或已能训练出专家。

## 取舍表

| 维度 | MuSiQue-Ans | HotpotQA distractor | GSM8K |
|---|---|---|---|
| 与主问题的联系 | 能定位跨段组合的依据怎样进入成员答案和团队结果 | 能定位支持句及其传播/使用 | 能测答案与计算修订，但缺外部事实支持标注 |
| 可直接用的监督 | 答案、支持段落、各步问题/答案与对应段落；不是作者自由CoT | 答案和句级supporting_facts；没有官方分解链 | 人工自然语言解题与数值答案；Socratic版不能当全部人工分解 |
| 首个专长 | 从给定多段资料定位、组合证据并正确作答 | 多段证据定位与作答 | 数学应用题求解 |
| 输入负担 | 固定20段；两至四跳，讨论上下文可能较长 | 固定10段，句级标注更细；不是任意题都比MuSiQue短 | 题面较短，技术成本较低 |
| 切分与泄漏 | 原论文按单跳问题/答案/段落控制跨split重叠；自行切train子集仍须分组/清除交叉 | hard样本随机分配，不具有相同成分隔离保证；需要额外近重复/证据检查 | 无单独dev，需另划；公开且常用于模型训练，不能保证底座未见 |
| 资产与状态 | 官方源码、raw train/dev各30条已实际读取，Qwen分词统计已完成 | 官网/官方schema和评分已核；本轮未下载完整数据 | 已有本地train Parquet与历史使用记录，必须排除已用开发题；未新跑模型 |
| 选择 | **优先**：支持标注与分解可帮助区分“答对”和“依据处理正确” | **备选**：若MuSiQue完整输入/数据切分不可承受，按输入条件转入，不按模型成绩临时挑更容易出结果的集 | 推迟：不要因为便宜就把课题换成数学多agent |

## 原始依据

- [MuSiQue官方说明](https://github.com/StonyBrookNLP/musique)、[原论文§5/表2](https://aclanthology.org/2022.tacl-1.31.pdf)：Ans的train/dev/test为19,938/2,417/2,459，20段上下文。CC BY 4.0。原始split的成分控制不代表我们新切的校准/开发集自动无交叉，也不保证Qwen预训练未见。
- [官方转换代码](https://github.com/StonyBrookNLP/musique/blob/main/raw_data_to_official_format.py)：从raw contexts构造`paragraphs[idx,title,paragraph_text,is_supporting]`，从分解问题构造`question_decomposition`。这些金标不能进入任何agent推理输入；只能放训练输出或评分端。[官方评分](https://github.com/StonyBrookNLP/musique/blob/main/evaluate_v1.0.py)分别评答案及支持；Full另有成对可答性指标，第一轮不混入Full。
- [HotpotQA官网](https://hotpotqa.github.io/)、[字段说明](https://github.com/hotpotqa/hotpot#json-format)、[评分](https://github.com/hotpotqa/hotpot/blob/master/hotpot_evaluate_v1.py)：distractor为10段，支持标注为标题/句号；数据CC BY-SA 4.0，不能用代码Apache许可证替代。train和dev公开标签，官方test标签不能当已有可离线评分的数据。
- [GSM8K官方说明](https://github.com/openai/grade-school-math)：`question/answer`，`####`后的最终数值及可选计算注释；MIT。需要固定计算器/注释策略，且旧项目已经看过的训练题不作新留出。

源码访问日快照在[source_snapshots](source_snapshots/)，实际读取与范围见[SOURCE_LOG](SOURCE_LOG.md)。只读源提取来自research-lit分工，不是独立科研评审。

## 本轮确实读取了哪些MuSiQue材料

通过官方`.all_data_information.json`所列作者Drive文件读取raw train/dev各30条完整记录，每文件最多读取2MB前缀；不是完整数据包或代表性随机样本。raw与official字段名不同，不能混写为已下载官方格式完整切分。

60条均含20段且均为两跳。每个分解步骤的支持文本均能在该例20段中唯一对应。已生成分离的`inputs`（只有题目、编号、标题、正文）与`targets`（答案、支持索引等）检查文件；未执行上游脚本、没有LLM合成监督。

用仅下载的Qwen3-4B官方tokenizer测标准任务文本，固定revision `1cfa9a7208912126459214e8b04321603b3df60c`；未下载权重或生成答案：

| 前缀集合 | N | 基础输入token最小/中位/P95/最大 | >4,096 |
|---|---:|---|---:|
| train | 30 | 1,509 / 2,503.5 / 3,507.8 / 4,416 | 1 |
| dev | 30 | 1,585 / 2,427.5 / 2,851.1 / 3,028 | 0 |

这是**不含聊天包装、生成思考、全员初答和讨论历史**的长度，不是总上下文；且没有覆盖三/四跳，不能据此承诺4K/8K服务一定装得下。[实测记录](MUSIQUE_INPUT_INSPECTION.json)、[数据来源与边界](../../data/external/musique-inspection-20261030/README.md)。

已查看的dev题登记为开发暴露集合，以后按题文哈希/原ID对应排除正式确认；不把这30条转成未见测试。完整数据下载、分组可行性、全体长度分布、别名和official ID映射尚待下一步离线准备。

## 与能力优势而非信息特权对齐

首个能力专家要更擅长利用**同一份给定资料**完成多跳问答，而不是在推理时额外得到金标答案、支持标志或问题分解。普通成员与专家使用同一底座、相同资料权限与输出契约；专家的区别是事先SFT，是否真有优势由独立校准决定。

首轮SFT优先直接使用“题目＋全部候选段落→答案＋支持索引”的短结构化目标，避免先生成昂贵CoT。金标分解先用于离线核验和分析，是否增加分解监督由训练可行性决定，不堆成必需模块。原始单题oracle条件保留作对齐诊断，不冒充部署选专家的方法。
