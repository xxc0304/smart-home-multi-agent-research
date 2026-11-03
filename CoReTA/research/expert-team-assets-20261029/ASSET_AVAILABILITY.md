# 专家团队研究：资产与证据可用性核对

核对日期：2026-10-29。任务：执行工作计划W01，顺带整理W04的8条起始案例。结论来自原始文件、官方代码及实际读取的数据；未调用新模型、训练或运行上游实验代码。

## 核对结论

**可以开始有依据的过程分析。当前最完整、最容易追溯的材料，是项目实际请求/响应及HiddenBench作者公开对话；它们主要支持信息利用分析。以能力优势为核心的专家团队研究，仍需补齐“同一成员的独立能力依据—此次贡献—完整交互—结果”的匹配材料。** 这决定证据如何使用，不改变已确认的宽研究方向。

已完成三项工作：

1. 核对三批本地记录共170个请求/响应槽位，覆盖8道基准题；对照progress、实际请求、服务返回与原始文本的关键字段，未发现本次检查范围内的不一致。170是调用记录数，不是170个独立案例。
2. 核对作者两模型各570次HiddenBench记录，均有初始票、15轮对话和终票；每模型仅57个不同场景。既有019摘录20条均与原文件对应位置一致。
3. 下载并读取PBT官方约170MB预处理数据包的10份主Arrow表；区分可读数据、加工偏好样本、完整团队轨迹与代码模板。选出[8条起始案例](CASE_SEED_8.md)，覆盖7道题，保留完整请求与原始输出定位。

## 各来源能做什么

“已读取”不等于“所有权限、隐藏输入或独立能力都已完整记录”。下表按本次实际检查范围报告。

| 来源 | 实际获取和核对 | 独立表现/优势依据 | 收件与过程 | 当前用途及缺口 |
|---|---|---|---|---|
| [Hold Experts Back官方仓库](https://github.com/apappu97/multi-agent-teams-hold-experts-back) | README、根目录/experiments目录、MC/ranking实现、GPQA runner、conversation源码快照 | 代码收集独立输出。MC揭示专家可使用该题答案正确性；ranking有集中/分散信息分配 | 代码保存元数据，并把每名成员的轨迹写入W&B artifact | 可核定义和采集方式；本次未取得论文运行的公开W&B轨迹地址或实际日志，不把“代码能保存”当作“论文日志已可下载” |
| [PBT官方仓库](https://github.com/esteng/persuasion_balanced_training) | 实际下载LFS对象，归档204项，读取10份主Arrow表；核trajectory与preference_factory源码 | 论文研究强弱模型及双向说服；预处理表没有完整的运行/模型配对与节点图 | 有对话上下文、偏好续写、答案/类别等字段；完整强弱团队轨迹不能由这些列直接还原 | 可供纠错/抗误导样例和标签规范参考，暂不能替代专家完整运行数据；字段含义见下节 |
| [HiddenBench官方结果入口](https://github.com/Yassellee/HiddenBench_ICML/blob/main/results/README.md)及[作者数据集](https://huggingface.co/datasets/YuxuanLi1225/HiddenBench-results) | 已有两份hidden_generated原文件完整字段核对，570×2次运行、57场景；另核全信息对照，见补充审计 | 初始投票是分持信息下的独立选择；没有稳定能力校准 | 有逐消息prompt/response、轮次、终票；原始系统输入和随机分配的完整映射未保存在run顶层 | 可做传播、意见变化及正反例分析；不能按数组位置认定谁持有哪条隐藏事实，也不能把prompt字段当成完整上下文 |
| CoReTA两批IMP适配记录 | 64+74=138个实际槽位；任务030/033/007/008 | 有同轮次共享初答和全信息单体对照；主要控制信息分布，模型返回别名deepseek-flash | 可解析PACKET中的原始资料、初答/历史字段与实际请求，匹配原始响应 | 当前最便于追溯实际收件的材料；是内部适配，不是IMP论文忠实复现；别名未固定服务端权重版本 |
| CoReTA局部重建诊断 | 32槽位，8个历史目标、4道题004/009/011/023 | 局部资料与重建稿；historical_work是旧草稿，不是该轮同步独立基线 | 实际请求/局部输出/终答可匹配 | 可研究收到局部贡献后的使用、解释与取舍；条件间局部稿内容也变化，不能孤立归因为“移除草稿”的因果效果 |
| [When Debate Helps官方仓库](https://github.com/Wang-ML-Lab/when-debate-helps) | README、docs/DATA.md及已有本地源码 | 实现profile、候选供给和读出评价 | 实现traces.jsonl，但本次未取得作者科学运行的原始轨迹数据 | 可复用思想/字段定义。DATA.md明确不再分发基准数据；9−4等调试fixture不是科学实验案例 |
| [ICR匿名仓库](https://anonymous.4open.science/r/AgentICR-AA82/)与[When Order Matters匿名仓库](https://anonymous.4open.science/r/personality-MAD-code) | 本次网页访问未成功 | 未完成文件级核对 | 未完成 | 标作访问未核实，不写成没有代码或没有数据；已读论文证据仍保留 |
| [SAT原文](https://arxiv.org/html/2609.22682v1)与作者主页 | 原文策略/案例及主页链接核对 | 论文证据，不是已获取的能力/过程匹配数据库 | 附录展示选择性对话，不等于完整运行集合 | 当前只作已发表方法和机制近邻；尚未验证可下载官方完整代码/轨迹 |

官方源文件快照及访问链接见[source_snapshots/SOURCE_FETCH_RECORDS.json](source_snapshots/SOURCE_FETCH_RECORDS.json)。它们是访问日的main内容快照；本轮未把全部上游仓库固定到提交版本，也未穷尽所有分支和发布页。匿名站访问失败不外推为全网不可用。

**全信息对照补充已实际完成：** 新下载Gemini-2.5-Pro、GPT-4.1两份full_profile文件，分别650次运行、65个场景，完整JSON可读。所有run均num_special=num_agents、1轮讨论；已有hidden_generated则每模型570次、57场景、15轮。它补齐一个可按场景查看的全信息条件，但不是单agent基线，也不是只改变信息可见性的公平单因素对照；不能直接把条件差归因于信息共享。见[来源与实际条件](../../data/external/hiddenbench-results-20261029/README.md)及[完整字段审计](HIDDENBENCH_FULL_PROFILE_AUDIT.json)。

## 原论文的“专家”需要逐条件核对

在MC实现中，`_collect_individual_answers`先收集每题独立答案；`reveal_expert`按当前题gold找到正确成员，多个时抽取，均错时可回退到配置的most_capable_model。**这类揭示包含单题事后正确者口径，不能自动当成事先在留出任务上校准的稳定专家。** ranking的集中/分散资料则明确控制信息优势，也不保证持有更多资料者此次必然推理正确。

可追溯实现：[MC源码快照](source_snapshots/original_multiple_choice.py)、[ranking源码快照](source_snapshots/original_ranking.py)。[GPQA runner](source_snapshots/original_run_gpqa.py)461–476行把轨迹写到W&B；部分独立完整solution的标量日志行被注释。仓库能重新采集材料，与目前可直接复用作者原始运行，是两个结论。

因此下一步定义至少区分：能力有独立依据的成员、掌握相关信息的成员、单题事后答对者、只有角色标签的成员。后续可以研究前两类之间的共同/不同机制；不把已有信息案例删掉，也不把它们升级为能力专家证据。

## PBT数据实际内容与标签语义

规范本地位置：[data/external/pbt-preprocessed-20261029](../../data/external/pbt-preprocessed-20261029/README.md)。压缩包170,222,819字节，实际LFS对象已下载，未把134字节指针当压缩包。只读取归档成员和Arrow，不执行包内代码或加载模型。

| 数据形式 | train行数 | valid行数 | test行数 | 解释 |
|---|---:|---:|---:|---|
| mistral偏好模板 | 3,554 | 744 | 878 | prompt/chosen/rejected/code/分数；valid/test另有答案及type |
| llama偏好模板 | 3,554 | 744 | 878 | 同类样本的另一模型聊天模板；不能直接加倍独立样本量 |
| mistral SFT模板 | 3,554 | 744 | 无单独test表 | text/code等，偏好样本的训练表示 |
| llama SFT模板 | 3,554 | 744 | 无单独test表 | 不作为新的独立对话集合 |

test各含439条两类记录，valid各372条两类。行是经过加工的偏好/训练记录，不保证一行等于一个独立问题；归档cache文件不额外计数。

**标签不能按字面直接当逐步准确率。** [preference_factory](source_snapshots/pbt_preference_factory.py)的`get_sumtree`把节点正确性向祖先累加，`pref_score/dispref_score`来自该分支汇总；`type`按agree_only/resist_only选择赋值。实际test首行两个续写都说Rolling Stones，却仍有2/0分与flip类别。这个例子说明“偏好分=当下答案正确与否”“type=这条真实发生的改答方向”不成立，不能据此宣布数据错误。若使用它测纠错/伤害，应先重新界定当前说话者、当前命题与前后答案，再进行人工核验。完整读取结果见[PBT_ARROW_FIELDS.json](PBT_ARROW_FIELDS.json)。

## 本地核对的覆盖与限制

| 本地记录 | 槽位 | 不同基准题 | 检查结果 |
|---|---:|---:|---|
| imp-adaptation-live-20261026-r1 | 64 | 2 | request/response/raw/progress关键字段对应 |
| imp-confirmation-live-20261026-r1 | 74 | 2 | 同上 |
| local-reconstruction-live-20261026-r1 | 32 | 4 | 同上；8个历史目标不算8道题 |

见[机器可读审计](LOCAL_ASSET_AUDIT.json)及[可重跑脚本](audit_local_assets.py)。检查包含JSON读取、请求资料包解析、provider output与原始JSON对应、progress关键choice/reasoning/text对应；有canonical请求文件时也核instructions。**这不是逐句语义正确性审核、模型能力校准或全协议完整性证明。** 008特定收件比较和8条案例另做定点核读。

排除两类看似可用的材料：搜索命中的`kobe7/repro-multi-agent-teams-hold-experts-back-traces`是第三方复现审计会话，不是原论文团队日志；软件调试fixture也不算研究证据。

## 工作取舍与下一步

保留8条案例作为定义/标注规范的开发材料，不从它们估算失败占比、机制重要性或新方法收益。8条来自7道题，019的两个模型记录不是两道独立题，其他成对分支同样不独立。

接着完成W02研究对象一页稿，并用这8条核验“自身能力/信息产出—分享—接收理解—实际使用—干扰—整合”哪些环节可直接观察，哪些只能提出假设；再制定W05独立标注规范和W06的30–40条采样规则。后续正式能力专家小验证需先冻结优势校准和过程记录口径；当前没有启动付费验证。

本轮助手完成文件/字段核对与目的性案例初筛；尚未完成人类独立复核、盲标、一致性或因果辨别。计划表中W01可标核对完成，W04标已提取待复核。
