# CoReTA：任务约束审计与反例保留机制（v0.3 设计稿）

状态：修订后可进入本地接口与状态机实现；尚未编码、尚未运行。日期：2026-10-20（+0800）。本稿依据 MATH140 诊断和对 `inspection_format_v1` 实际运行器 `closure.py` 的核对，明确事件次序、状态转换和预算。它不声称机制有效。

## 1. 问题锚点与范围

目标仍是提升三 Agent 团队的问题解决与协调能力，特别是让成员发现的有效贡献被检查、整合并用于修正候选。当前只处理一类已定位故障：检查输出中出现可核对的候选冲突，后续却在同一输出中把它消解并关闭。

MATH140 的证据链是：A0 在 (1,-1) 处把 x²y、xy² 的符号写反，得到非法基；A1 沿用；A2 在检查文本里先算出基函数值 −3，随后改写成 0 并关闭问题。诊断没有证明检查者总能发现错误，也没有证明新状态门控会改善答案。待检验假设是：把已提交的检查证据不可覆盖地入账，并让其进入后续修复或反驳复核，能提高矛盾被处理的比例；这是否带来全员初稿失败题的恢复，必须由新题实验回答。

非目标：不写 140 特例；不增 Agent；不接入 CAS/代码执行器；不读取 gold 或隐藏测试；不把模型自报的“正确”或“完成”当真值。工具执行可另作后续独立条件。

## 2. 设计决策

推荐做一个**任务事实约束的审计记录 + 现有 issue 注册表中的不可覆盖证据 + 双路径关闭门控**。复用当前三 Agent、候选版本/hash、有限工作轮和 issue 状态；不再造平行的 Finding 数据库。程序只约束证据保存、引用和状态迁移，不负责证明一般数学或代码主张。

仅强化检查提示不足以处理 MATH140 暴露的“写出反例后又自行否定”。新结构化记录可让程序发现已提交字段中的明确等式矛盾，但仍不保证模型会发现或如实提交反例。CAS 对这个问题可能更强，却会混入外部求解能力，不纳入这一机制版本。

## 3. 组件与调用流程

复用 `inspection_format_v1` 的实际调用顺序：`drafts → TaskFacts → synthesize → [build/work (B) → apply (U) → inspect (C)]×最多3 → 导出当前候选`。当前 closure runner 在 C 后直接导出当前候选；不调用 `revision.py` 旧通用流程中的 `final` 阶段。

1. **独立初稿**：A0、A1、A2 各自解题，彼此不可见；保存三份初稿。
2. **TaskFacts（新增 1 次调用）**：候选尚未暴露前，仅给一位 Agent 公共题面，提取约束、目标、定义域和歧义。每条事实附原文片段及定位。程序核对引用片段与题面完全一致。一次最多输出 32 条事实，且有单独配置的输出 token 上限；超限必须标 `partial`，不能声称穷尽。其他 Agent 在后续审计时可指出事实遗漏。
3. **综合**：A0 根据三份初稿产生候选和已有 issue。
4. **B 建设/工作**：按当前轮次由 A1 或 A2 产生构造、独立检查建议或修复贡献。B 可附审计线索，但不产生可关闭状态；所有候选主张引用当前版本和 TaskFact。
5. **U 应用**：A0 接收 B 的贡献，提交候选及对已有 issue 的 repair、rebuttal 或暂不处理提案。A0 不能单独关闭 issue。
6. **C 检查**：由与本轮 B、U 不同的 Agent 检查应用后的当前候选、B 的贡献及待复核处理；最多审计六条关键主张，提交结构化 `AuditRecord`。C 既可复核旧 issue，也可报告新反例。新反例在本轮 C 后入账，供下一轮 B/U 处理。
7. **先入账，再派生状态**：C 的原始响应先追加写入响应日志。结构合法的审计记录被接受后，程序先保存到事件日志和现有 issue 的不可覆盖证据列表，再做关系比较及关闭判定。若 C 同时报告 counterexample，U 在此前提出的 `resolved` 不得生效；程序记录冲突、保持 issue 开放，不拒绝整份 C 响应、不要求整份重写。纯语法/JSON 结构错误可按现有上限做格式修复，但每次原始响应留存；已接受的审计证据不能被后续重试覆盖。
8. **轮次结束**：只有 C 已复核 U 的处理、没有开放 correctness-critical issue 且下一步无需继续时才可 `complete`。最后一轮 C 新发现的 issue 留在 `unresolved/budget_exhausted`，导出当前完整候选并离线评分；不再追加第四轮。

角色按当前轮换确定：U 固定 A0；B 为 A1/A2 之一，C 为另一位成员。TaskFacts 提取者只见题面；提取完成后事实清单可共享。角色轮换不等于认知独立，三个成员可能共享同一模型及盲点。

## 4. 数据契约与状态

### 4.1 TaskFact

`fact_id`, `source_locator`, `quoted_text`, `normalized_fact`, `kind`（constraint/objective/domain/ambiguity），以及 `coverage_status`（complete_for_explicit_list / partial / unknown）。文本定位采用 Python Unicode code point 索引的左闭右开 `[start,end)`；结构化题面字段用 JSON Pointer。原文匹配可程序核验，语义转述与穷尽性不能由该检查证明。

### 4.2 AuditRecord 与 AuditCase

每条 `AuditRecord` 绑定 `record_id`, `candidate_hash/version`, `auditor`, `target_refs`, `task_fact_ids`, `claim_text`, `attempted_falsification`, `cases[]`, `coverage`, `model_verdict` 和事件时间。每个 `AuditCase` 至少含 `case_id`, `fact_id`, `input`, `comparison_kind`, `quantity_key`, `expected_value`, `observed_value`, `model_outcome`（counterexample/match/unable）。

确定性数值门控**仅用于 `comparison_kind=exact_equality`**：expected/observed 必须声明为同一 `quantity_key` 的同语义量，并使用规范整数或有理数文本（如 `0`、`-3`、`5/19`）。程序仅能据此判定“模型记录的两个值违反了所声明的等式”；它不能证明 TaskFact 解读正确，也不能证明 observed 的计算过程正确。不同单位、区间、不等式、近似量以及不可解析表达式不触发数值不等门控，保留为模型审计。模型若漏报 observed、在提交前自行改写，或两侧都填错，仍可能漏过。

程序派生 `effective_outcome`，不得覆盖 `model_verdict`：

- 任一 case 明确报告 counterexample，或精确等式的可解析数值不相等：`finding_open`。
- correctness-critical case 为 unable：`needs_check`，不能标为已验证或关闭。
- 其他情况：`not_refuted_within_recorded_scope`。这不等于正确，也不能单独关闭既有 issue。

### 4.3 复用 issue 作为 finding 容器

新反例由程序分配稳定 `issue_id`；现有 issue 追加 `evidence_records`，保存原始 AuditRecord、首次候选 hash/version、报告者、关联事实、每次处理和复核事件。后续响应不能删除或覆盖原始记录；状态可以变化，历史必须可追溯。若已有 issue 被 C 再次反驳，附加证据并重开；若为新问题，新增 issue。对业务状态冲突不能抛出让整个 C 调用重试的 `ProtocolError`。

### 4.4 两条关闭路径

- **Repair**：U 提交针对 issue 的实质候选变更；候选 hash 必须变化，但 hash 变化本身不算修复。后续 C 对照原始反例、相关 TaskFacts 和受影响候选步骤复核，确认矛盾已消除才关闭。
- **Rebuttal**：候选 hash 可以不变。U 提交可检查理由，说明原反例为何不成立；之后另一成员 C 独立复核同一个原始反例和该反驳，确认反驳成立才关闭。

两条路径均绑定 `issue_id`、原始证据记录 ID、当前候选 hash 与复核事件。C 若在复核响应中发现新的反例，该证据先入账，相关 issue 保持开放；不能在该响应里自我关闭。不得通过改 issue 名称、删步骤或投票关闭。

## 5. 预算与停止规则

调用上限按当前 closure runner 计算：`3 drafts + 1 TaskFacts + 1 synthesis + 最多 3×(B→U→C) = 14 次逻辑调用`。当前 `call()` 对非 `final` 阶段为一个未调用的 final 保留槽，因此实现时需将 cap 设为 15 才能允许 14 次逻辑调用；该 closure runner 不调用 final，**总逻辑调用最多 14 次；实际 HTTP 请求次数另计格式修复与传输重试**。格式修复是在同一逻辑阶段内有界重试，不增加逻辑调用数。最后一次 C 新发现的 issue 只入账为 unresolved，不增加第四轮。

符合停止条件且不存在开放 correctness-critical issue 才可标 `complete`；`not_refuted` 不等于 verified。预算耗尽、运行降级或过程未完成复核时如实记录，不清理开放 issue。最终候选仍需独立离线评分。

## 6. 验证与实验顺序

### 阶段 0：本地接口/状态机 fixture（不发模型请求）

用 MATH140 旧轨迹构造输入：A2 的 `comparison_kind=exact_equality, quantity_key=g1(1,-1), expected=0, observed=-3, model_outcome=match` 必须被记录为开放 issue；同轮已有 `resolved` 提案不能覆盖它；C 的原始响应及有效 AuditRecord 不得因状态冲突被整包重试或覆盖。Repair 要求实质候选变化和后续复核；Rebuttal 可保持 hash 不变但需独立复核；最后一轮 C 新反例进入 `unresolved/budget_exhausted`。另覆盖不等式/近似量不触发精确比较、错误引用、格式错误保留原响应、漏掉 TaskFact、预算耗尽和角色重叠。此 fixture 证明状态机行为，不证明新提示会让模型真实发现 −3。

### 阶段 1：MATH140 已见工程回归

重用既有三份错误初稿，只给公开题面，不给 gold、正确推导或旧诊断。记录最终答案、finding 的发现/留存/处理、运行状态。这是工程回归，不计入新题能力证据，也不保证成功。

### 阶段 2：新题整体机制小试点

固定新的公开训练题池、题面/评分契约、去重规则和共同初稿银行；每题先由同样三份初稿进入各条件，纳入规则在任何协作结果出现前冻结。两条件（旧 `inspection_format_v1` 与新完整机制包）只能回答“整个方案相对现状如何”，不能单独把差异归因于硬门控。若研究问题要归因持久门控，预先加第三条件：TaskFacts 与审计格式相同，但不启用硬门控。保留完整筛选记录，不按协作是否成功或是否看到互补线索挑题。

每题用官方或预先冻结的评分规则判定最终成功。仅当三份初稿均未达预设正确标准时计入 all-initial-fail 子集；至少一份初稿正确的任务单独统计退化。共享初稿缺失者在协作条件分配前按预设规则排除并报告；分配后运行失败或无最终候选，在 intention-to-treat 主分析中记失败，另报流程完成率。部分分数另行报告，不临时改成 pass。

主结果（同一完整题集）：令 `U_i=1` 表示至少一份初稿正确，`D_i=1` 表示三份初稿全错，`F_im=1` 表示方法 m 最终正确。`G_m=Σ D_i F_im`；`L_m=Σ U_i(1−F_im)`；`net_m=G_m−L_m`。另分别报告恢复率 `G_m/ΣD_i` 与损失率 `L_m/ΣU_i`，不把不同分母的百分率相减。配对净收益差为 `(G_new−L_new)−(G_old−L_old)`，同时报分母和不确定区间；小试点只作描述，不据此宣称稳定能力提升。

机制过程指标：

- 入账率：结构合法且提交的反例中进入不可覆盖 issue 证据的比例；
- 后续处理率：除最后一轮新发现外，已入账 issue 中获得 repair/rebuttal 的比例；
- 独立复核率：已处理 issue 中由合格不同角色完成复核的比例；
- 审计召回：盲态事后裁定的关键错误/约束中，预先定义的审计范围内被提交为 issue 的比例；分母按任务和候选版本记录；
- 错误 issue/无必要阻塞率、有效贡献采纳率及其对相关步骤的影响；区分独立重解、有效互补组合、错误传播和正确候选被误改。

Token、延迟、HTTP 和成本是次要指标。过程轨迹定位改进发生在发现、保留、处理或复核哪一环；只有最终配对结果与过程证据一致时，才讨论能力提升。确认性样本量待先导数据估计全员初稿失败率后另做功效规划。

## 7. 剩余局限与下一步

程序承诺范围是：**已提交的结构化矛盾不能被后续 verdict 抹去，必须进入后续处理或保留为 unresolved**。模型没生成反例、提交前在自由文本中自行撤销、expected/observed 同时填错时，程序无法弥补；对此测审计召回和错误 issue 率。题面原文定位不能证明语义解释正确或 TaskFacts 穷尽。相同模型的 Agent 可能共享盲点。

文献参考沿用已核查材料：AgentVerse 的 solver/critic 修订流程（https://arxiv.org/pdf/2308.10848）、ChatDev 的 review comments 进入 modification 流程（https://aclanthology.org/2024.acl-long.810/）、MAST 对核验与过早终止失效模式的分类（https://arxiv.org/html/2503.13657v3）。这些支持“批评应进入后续修改/核验”的流程选择，不证明 CoReTA 机制有效，也不等同于这里的不可覆盖审计记录。

下一步：冻结该规格字段和状态转换，实施纯本地 schema/state-machine fixture；通过后跑 MATH140 已见工程回归；随后冻结新题、对照条件和评分计划。当前只完成设计，没有改运行代码或跑新实验。

