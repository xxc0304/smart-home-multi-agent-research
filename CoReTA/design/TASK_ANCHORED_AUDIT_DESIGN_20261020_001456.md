# CoReTA：任务约束审计与反例保留机制（v0.2 设计稿）

状态：独立复核后的设计候选；尚未编码、尚未运行。日期：2026-10-20（+0800）。本稿回应 MATH140 中可观察到的失败链，并给出可直接转成接口/状态机规格的边界。它不声称已证明机制有效。

## 1. 问题锚点与范围

目标仍是提升三 Agent 团队的问题解决与协调能力，特别是让成员发现的有效贡献被检查、整合并用于修正候选。当前只处理一类已定位故障：检查输出中出现可核对的候选冲突，后续却在同一输出中把它消解并关闭。

MATH140 的证据链是：A0 在 (1,-1) 处把 x²y、xy² 的符号写反，得到非法基；A1 沿用；A2 在检查文本里先算出基函数值 −3，随后改写成 0 并关闭问题。诊断没有证明检查者总能发现错误，也没有证明新状态门控会改善答案。待检验假设是：把已提交的检查证据不可覆盖地入账，并让其进入后续修复或反驳复核，能提高矛盾被处理的比例；这是否带来全员初稿失败题的恢复，必须由新题实验回答。

非目标：不写 140 特例；不增 Agent；不接入 CAS/代码执行器；不读取 gold 或隐藏测试；不把模型自报的“正确”或“完成”当真值。工具执行可另作后续独立条件。

## 2. 设计决策

推荐做一个**任务事实约束的审计记录 + 现有 issue 注册表中的不可覆盖证据 + 双路径关闭门控**。复用当前三 Agent、候选版本/hash、有限工作轮和 issue 状态；不再造平行的 Finding 数据库。程序只约束证据保存、引用和状态迁移，不负责证明一般数学或代码主张。

仅强化检查提示不足以处理 MATH140 暴露的“写出反例后又自行否定”。新结构化记录可让程序发现有明确字段的数值矛盾，但仍不保证模型会发现或如实提交反例。CAS 对这个问题可能更强，却会混入外部求解能力，不纳入这一机制版本。

## 3. 组件与调用流程

保留三个 Agent 和当前 `synthesize → build/work → inspect → apply → final` 调用体系，只增加一个 task-only 阶段和审计数据契约。

1. **独立初稿**：A0、A1、A2 各自解题，彼此不可见；按现有实现保存三份草稿。
2. **TaskFacts（新增 1 次调用）**：在候选尚未暴露给提取者之前，仅给一位 Agent 公共题面，提取约束清单、目标、定义域和歧义。每条事实附原文片段及偏移/JSON Pointer。程序核对引用片段与公共题面完全一致。若无法证明清单穷尽，必须标为非穷尽；其他 Agent 可在审计时指出漏掉的原文条件。
3. **综合**：A0 基于三份初稿生成当前候选与 issue。
4. **建设/工作 B**：按现有轮次，由非当前候选主张作者生成建设贡献或修复建议；贡献要引用候选步骤、TaskFact 和待处理 issue。B 可提出检查案例，但不拥有关闭权限。
5. **检查 C**：由不同于本轮 B、也不同于后续应用者 U 的成员审计当前候选及 B 的贡献。C 对不超过六条关键主张尝试反驳，提交结构化 `AuditRecord`。首轮保持现有 `build → inspect → apply` 次序；后续工作轮继续使用当前运行器的阶段与预算规则。
6. **入账先于裁决**：原始响应先写追加式事件日志。结构合法的 `AuditRecord` 一经接受，立刻写入 issue 的不可覆盖证据列表；随后程序根据案例派生有效结果及阻塞状态。若案例显示矛盾但模型 verdict 写 `match/supported/resolved`，保留原始 verdict、拒绝该关闭动作并记录冲突，不得回滚证据或要求模型重写整份检查来“解决”冲突。纯 JSON/结构错误可沿用有限格式修复，但每次原始响应仍留日志；结构错误不等于已接纳审计记录。
7. **应用 U**：A0 应用贡献和开放 finding，逐条选择 repair、rebuttal 或暂不处理，并引用 finding ID。A0 不能单独关闭 finding。
8. **复核 C**：另一成员对照原始 finding 和当前候选复核处理。C 若在本次首次发现新反例，该发现当次入账并保持开放，不能在同一响应中关闭；留给下一轮。最终一轮仍有开放 finding 时，以 `budget_exhausted/unresolved` 交付当前完整候选，不标 verified/complete。

角色由本轮候选来源和既有轮换确定，不宣称角色切换就是认知独立。三个成员可能共享同一模型及盲点。若具体轮次排不出不同的 B、U、C，必须显式记录角色重叠，并把该轮标为非独立复核，不能悄悄当作满足门控。

## 4. 数据契约与状态

### 4.1 TaskFact

`fact_id`, `source_locator`, `quoted_text`, `normalized_fact`, `kind`（constraint/objective/domain/ambiguity），以及 `coverage_status`（complete_for_explicit_list / partial / unknown）。`source_locator` 为题面 Unicode 左闭右开偏移；结构化字段用 JSON Pointer。原文匹配可程序核验，转述语义不能程序证明。

### 4.2 AuditRecord

每个记录绑定 `candidate_hash/version`, `auditor`, `target_refs`, `task_fact_ids`, `claim_text`, `attempted_falsification`, `cases[]`, `coverage`, `model_verdict`, `submitted_at`。每个 case 至少含 `case_id`, `fact_id`, `input`, `expected_value`, `observed_value`, `model_outcome`（counterexample/match/unable）。`expected_value` 与 `observed_value` 用可解析的有理数/标量文本；任一缺失、不可解析则记为模型审计，不声称程序验证。程序可将明确可解析且不相等的 expected/observed 强制转成 finding，即使 `model_outcome=match`。对双方都填错、漏报 observed 或模型在提交前已改写的情况，仍不能自动发现。

程序派生 `effective_outcome`，不得覆盖 `model_verdict`：

- 任一 case 明确 counterexample，或精确标量比较不一致：`finding_open`。
- 只要 correctness-critical case 为 unable：`needs_check`，不得作为“已验证”关闭。
- 其他情况：`not_refuted_within_recorded_scope`。这不等于正确，也不能单独关闭既有 finding。

### 4.3 复用 issue 作为 finding 容器

新建 finding 时由程序分配稳定 `issue_id`；issue 追加 `evidence_records`，记录原始 AuditRecord、首次候选 hash/version、报告者、关联事实、每次处理与复核事件。后续事件不得删除或覆盖原记录；状态可以变化但历史可追溯。引用失效、版本不匹配或结构错误可阻止应用，但不能抹掉已有有效证据。

### 4.4 两条关闭路径

- **Repair**：U 提交实质变更并引用 finding；新候选 hash 必须变化，但 hash 变化本身不算修复。C 要复查原始反例、相关题面事实及受影响候选步骤，确认冲突被消除后才关闭。
- **Rebuttal**：候选 hash 可以不变。U 提交可检查的理由，说明原反例为何不成立；另一成员 C 独立复算/复核同一个原始反例，确认反驳成立后关闭。不得通过改 issue 名称、删步骤或多数投票关闭。

两条路径都要求绑定 `issue_id`、原始证据记录 ID、当前候选 hash 和复核事件。C 不能是 U；条件允许时也不应是 finding 的报告者。若三 Agent 角色约束造成无法安排，明确降级为 unresolved。

## 5. 预算与停止规则

按现有 `revision.py` 调用预算核算：3 份初稿 + 1 次 TaskFacts + 1 次综合 + 最多 3 个建设/检查/应用循环（首个 bootstrap 循环加最多 2 个后续循环）= 最多 14 次 pre-final 逻辑调用。当前非 final 调用会为最终输出保留 1 个槽位，因此配置 cap 为 15；最终调用最多 1 次。格式修复是同一逻辑调用内有界的 HTTP 重试，不额外计入逻辑调用上限，但 HTTP 次数和修复次数单列报告。最后一个 C 新建的 finding 只入账并保持开放，不能越过预算再加一次 U/C。

只有无开放 correctness-critical finding，且完成所需的独立复核时，才允许流程状态 `complete`；`not_refuted` 不等于 verified。预算耗尽、运行降级或角色未独立时如实记录，不清理未解决 issue。最终 artifact 仍须独立离线评分。

## 6. 验证与实验顺序

### 阶段 0：本地接口/状态机 fixture（不发模型请求）

用 140 旧轨迹构造已知输入：A2 的 `expected=0, observed=-3, model_outcome=match` 应被确定性规则入账为开放 finding；同响应 `resolved` 不能关闭；格式重试不能删除已入账记录；repair 路径要求实质变化和复核，rebuttal 可保持 hash 不变但必须独立复核；最后一轮 C 新发现进入 unresolved/budget_exhausted。另测错误引用、未解析数值、漏掉 TaskFact、预算耗尽及角色重叠。旧轨迹 fixture 只能验证门控行为，不能证明新提示会让模型真实发现 −3。

### 阶段 1：MATH140 已见工程回归

重用既有三份错误初稿、只给公开题面，不给 gold、精确正确推导或旧诊断。报告最终答案、finding 的产生/留存/处理和运行状态。这是工程回归，不计入新题能力证据，也不保证成功。

### 阶段 2：新题整体机制小试点

固定新的公开训练题池、题面/评分契约、去重规则和共同初稿银行；每题先由相同三份初稿进入各条件，纳入规则在任何协作输出前冻结。两条件（旧 `inspection_format_v1` 对新完整机制包）能回答“整个方案相对现状怎样”，不能单独把差异归因于持久门控。若研究问题要归因门控，应预先加第三条件：同样 TaskFacts 与审计案例，但不启用硬门控。题目筛选保留完整记录，不按是否存在互补线索、协作是否成功来挑题。

对每题用官方/预先冻结的评分规则判定最终成功。仅当三份初稿均不满足预设正确标准时计入 all-initial-fail 子集；至少一份正确的任务单独统计退化。若任一共享初稿缺失，则按预先资格规则在分配协作条件前排除并报告；任务分配后发生运行失败或无最终 artifact，在 intention-to-treat 主分析中记失败，另报流程完成率。部分分数另行报告，不临时改成 pass。

主结果（对同一完整题集定义）：令 `U_i=1` 表示至少一份初稿正确，`D_i=1` 表示三份初稿全错，`F_im=1` 表示方法 m 最终正确。`G_m=Σ D_i F_im`；`L_m=Σ U_i(1−F_im)`；`net_m=G_m−L_m`。另分别报告恢复率 `G_m/ΣD_i` 与损失率 `L_m/ΣU_i`，不把不同分母的百分率相减。方法间配对净收益差为 `(G_new−L_new)−(G_old−L_old)`，同时报原始分母和区间；小试点只作描述，不据此宣称稳定能力提升。

机制过程指标：

- finding 入账率：结构合法且提交的反例中进入不可覆盖 issue 证据的比例；
- 后续处理率：除最后一轮新发现外，已入账 finding 中获得 repair/rebuttal 的比例；
- 独立复核率：已处理 finding 中由合格不同角色完成复核的比例；
- 审计召回：盲态事后裁定的关键错误/约束中，预先定义的审计范围内被提交 finding 的比例；分母按任务和候选版本记录，不跨条件混为一组；
- 错误 finding/无必要阻塞率、有效贡献被采纳率及其对相关步骤的影响；区分独立重解、有效互补组合、错误传播和正确候选被误改。

Token、延迟、HTTP、成本为次要指标。机制轨迹能定位改进落在“发现、保留、处理、复核”哪一环；只有最终配对结果与过程证据一致时，才讨论能力提升。正式确认性样本量要在先导数据估计筛选后全员失败率后另行功效规划。

## 7. 剩余局限与决策

本设计对程序承诺的范围是：**已提交的结构化矛盾不能被后续 verdict 抹去，必须处理或保留为 unresolved**。如果模型没有生成该反例、提交前在自由文本中自行撤销、expected/observed 同时填错，程序无法弥补；对此测审计召回和错误报告率。TaskFacts 的原文定位能验引用，不能自动验语义解释或穷尽性。角色轮换和独立复核不消除同模型共同错误。

文献参考沿用已核查材料：AgentVerse 的 solver/critic 修订流程（https://arxiv.org/pdf/2308.10848）、ChatDev 的 review comments 进入 modification 流程（https://aclanthology.org/2024.acl-long.810/）、MAST 对核验与过早终止失效模式的分类（https://arxiv.org/html/2503.13657v3）。它们为“批评要送入后续修改/核验”提供流程先例，不证明 CoReTA 机制有效，也不等同于这里的不可覆盖审计账本。

下一步顺序：先冻结本规格的状态和字段；再实现纯本地 schema/state-machine fixture；通过后跑 140 已见工程回归；随后冻结新题、对照条件与评分计划。当前产物仅是设计稿，没有改运行代码、没有跑新实验。
