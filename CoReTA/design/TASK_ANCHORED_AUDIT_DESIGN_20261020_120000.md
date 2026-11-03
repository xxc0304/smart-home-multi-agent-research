# CoReTA：任务约束审计与反例保留机制（v0.1 设计稿）

状态：待审查，未实现。目标是把 140 诊断中的“题面事实—候选主张—具体反例—后续修复—独立复核”做成可执行闭环；不改写已冻结运行版本。

## 1. 研究锚点

> 提高多 Agent 团队的协调与问题解决能力，让成员已有知识及协作中新产生的有用贡献得到实际利用；先把定向帮助、贡献检查、整合与应用反馈落实为三 Agent 可执行协议，再用已有论文采用的任务检验整体能力与互补作用。优先借鉴公开方法和官方代码，清楚区分复用接口与本项目的机制假设。能力与机制优先，成本如实记录，同成本优势与节约成本后置。

当前诊断中的瓶颈：检查报告中已经出现可核对的约束冲突，但它没有约束关闭状态；多个 Agent 沿用了同一个错误消元式，未稳定地回到题面原始条件。

非目标：不为 140 写特判；不增加 Agent 或训练路由器；不读取 gold/隐藏测试；不把更多对话当作互补；不宣称模型手算或字段标签等于真值。

## 2. 证据与可证伪假设

140 的主 Agent 把 (1,-1) 处 x²y、xy² 的符号写反，导出非法基函数。A1 沿用。A2 在同一次检查中算出 g1(1,-1)=-3，随后又把代入写成 0，并关闭问题。更早轨迹中，检查者把几个非零乘积误报为零，围绕非法基函数继续修补秩证明。

假设：独立提取题面事实、逐条尝试反驳候选关键主张，并让结构化反例自动进入持久问题状态，可以提升“发现的矛盾进入后续修复/复核”的比例，进而可能提升全员初稿失败题的恢复率。纯模型检查仍可能共同算错；本机制不保证推理正确。

## 3. 机制选择

比较三条路线：

- 只强化提示：实现最小，但本例已显示检查者会在同一段文字里算出反例又自行否定，缺少状态约束。
- 任务事实清单＋反例账本＋状态门控（推荐）：复用三 Agent、Candidate、问题状态、版本哈希、有限工作轮，只扩展审计产物和关闭规则。程序约束证据关系和流程，不判断数学真值。
- CAS/代码执行器：可能直接查出算术错误，但会加入任务族专用工具，混入协调机制效果。先不纳入；以后可作为独立工具条件。隐藏评分器只离线使用。

本稿的机制是“反例不能在提交它的同一条检查响应里被关闭”，并由下一工作轮处理它；不是自动验证器。

## 4. 流程

1. 三名成员独立起草。
2. A2 在看任何候选前，仅根据 PublicTask 生成 TaskFacts，附题面原文片段与位置。程序核对每个片段与原文精确一致。
3. A0 汇总初稿。
4. A1 审计 A0 当前候选：引用 TaskFacts，挑选关键主张，尝试构造反例，记录测试输入、题目要求的预期、候选观察值及覆盖范围。
5. 若任一关键检查报告 counterexample 或 unable，控制器固化 AuditFinding 并保持阻塞；同一 inspection 不得同时关闭对应问题。
6. 下一工作轮派给未写该候选主张的成员，基于题面与完整 finding 独立核验、修复或给出逐步反驳。A0 应用并说明是否采用。
7. 由非修复者检查新候选和原 finding。只有新版本的具体处理经独立复核后才允许关闭；预算耗尽则保留 unresolved 并交付最后候选。

反例本身不自动当真，它只阻止同轮关闭。后续成员可以给出可检查的反驳，但不能靠投票。not_refuted 仅表示在记录范围内没有找到反例，不是正确性证明。

## 5. 数据契约草案

检查对象新增 task_facts、claim_audits；保留现有 checks、issues、closure_reviews。

TaskFact 字段：

- fact_id
- source_locator：PublicTask.prompt 的左闭右开 Unicode 字符偏移；结构化题面字段使用 JSON Pointer
- quoted_text：原文
- normalized_fact：对原文的简短转述
- kind：constraint / objective / domain / ambiguity

程序验证原文片段严格匹配 source_locator。TaskFact 单独调用生成，确保当时模型看不到候选。对离散条件（如题目列出的点）必须逐项列出；不完整的条件清单不允许宣称 exhaustive。

ClaimAudit 字段：

- claim_id、claim_kind（candidate_object / derived_result / final_answer / code_behavior）
- target_refs、task_fact_ids、claim_text
- attempted_falsification
- cases：fact_id、input、expected、observed、outcome（counterexample / match / unable）
- coverage（exhaustive_for_listed_facts / sampled / unable）
- verdict（counterexample / not_refuted / unable）、scope

每轮最多审计六条关键主张，优先检查候选对象是否合法、关键不变量/维数、最终答案是否满足目标和已有阻塞异议。每一条都必须说明检查范围。

程序可以验证：题面引用确实存在、候选/步骤引用可见、fact_id合法、候选版本/hash一致、反例与关闭状态绑定。v1 不解析任意自然语言算式，也不独立验证模型填写的 observed 数值。

## 6. 状态门控

AuditFinding 由程序分配稳定 ID，追加记录首次候选版本、主张目标、TaskFacts、原始反例、提交者和处理历史；后续响应不能覆盖原始发现。

| 审计结果 | 程序状态 | 关闭条件 |
|---|---|---|
| counterexample | 自动生成或关联 blocking issue；拒绝同一 inspection 的 resolved | 新候选版本＋修复/具体反驳＋非修复者复核 |
| unable 且影响正确性 | blocking / needs_check | 补出可检查推导或明确标预算耗尽 |
| not_refuted | 记录“所列范围未发现反例” | 不能单凭此关闭阻塞问题；有限约束若称 exhaustive，须覆盖全部相关 TaskFacts |
| 原文、引用、版本或哈希无效 | 拒绝整份检查；按现有上限做格式修复 | 不改写原始响应 |
| 预算耗尽仍有 finding | unresolved / budget_exhausted | 交付最后完整候选，不得报 complete/verified |

若一次 inspection 中有任何 case 标为 counterexample，对应 finding 优先于同响应的 resolved。下一轮修复后进入 needs_recheck；新的复核者必须查看原始反例，而不是只看整合者的总结。只改 changed_step_ids 不构成修复证据。

局限：如果模型完全漏报反例，或把 observed 本身填错，纯模型版本仍会漏检；这要用审计召回衡量，不能声称程序已证明答案正确。

## 7. 角色与预算

角色按候选来源轮换，不假设固定专长。A0 负责整合，不能单独关闭自己的 blocking finding；审计者不应是被审主张的作者；修复者与最终复核者必须不同。TaskFacts 提取者在提取时只见题面，后续事实清单对其他成员可见且带原文引文。

TaskFacts 增加一次 task-only 调用；三份初稿＋提取＋综合＋最多三轮 build/apply/inspect 上限为 14 次逻辑调用。因此运行 cap 从14调整到15（原实现保留一个非 final 预算位）。无反例时不增加后续轮；有反例使用现有工作轮，不做无限辩论。格式修复沿用原限制，成本照常记录。

## 8. 验证计划

阶段0，纯本地契约测试：用旧 140 轨迹做 fixture；核对八个点的原文跨度；当某行提交反例 -3 时，同响应 resolved 必须被状态机拦住；只有新候选版本、非修复者复核后才能关闭；not_refuted、错引用、漏约束、预算耗尽都不能伪装为 verified/complete。加一份代码题公共规格 fixture，不使用隐藏测试。

阶段1，140 已见回归：复用三份原错误初稿，仅给公开题面，不输入本地 gold、P/Q 推导或旧轨迹诊断。只作工程回归，不作确认性效果证据。

阶段2，新题配对试点：从未调用过的公开数学/代码训练题预抽样，冻结题面与初稿筛选规则，使用共同初稿银行比较 inspection_format_v1 与新机制。正式题单需在任何处理条件的协作结果出来前冻结。旧筛选中只有一道全员失败题，不能只靠140做效果结论。

主指标同时报告：
- G：三份独立初稿都错、最终改对；
- L：至少一份初稿正确、最终被协作改错；
- net_gain = G - L，并分别报告分母；
- 审计召回：事后裁定的关键错误/约束中，多少被提交为 finding；
- 反例保留率：结构化反例中多少进入下一轮处理/复核，而非同轮关闭；
- 来源与整合轨迹：谁提出有效部分、是否被接入、是否经另一成员复查，区分互补组合与单个 Agent 独立重解。

运行完成率、HTTP、token、延迟为次指标。若 finding 留存提高但无修复，问题在 resolver/应用；若 finding 未出现，问题在事实提取/审计；若经确认的反例已修复但答案仍错，再查推导整合。小规模试点用于验证机制路径，不发布能力结论；确认性样本量待盲筛估计全员失败率后再做功效规划。

## 9. 风险及处理

- TaskFacts 漏项/误读：task-only 生成、精确原文定位；另一审计者仍需读完整题面并可报告事实遗漏。
- 错误反例：作为待核验问题，不自动替换候选；由非原作者逐步反驳并由第三成员检查。
- 同模型共同盲点：角色切换不等于模型独立性，明确记录。
- 题面歧义：保留原句、记录解释，不擅自制造唯一答案。
- 上下文膨胀：当前材料只带未解决 finding 与必要来源；完整账本保留在日志。
- 不可机器核验的数学/代码 claim：标为模型手工检查，不谎称 executed/formally_verified。

## 10. 决策顺序

1. 独立审查本稿字段、状态门控和预算。
2. 审查后冻结规格，再做 schema/state-machine 本地 fixture 测试，不发模型请求。
3. 通过后在 140 做一次已见工程回归。
4. 复查轨迹后冻结新题抽样与对照，才进入小规模新题试点。
5. 只有 G、L、net_gain 和机制轨迹共同支持，才讨论能力提升。

参考已核查项目材料：engineering/MATH140_FORMAT_DIAGNOSIS_20261020.md、engineering/MATH140_FORMAT_EXACT_CHECK_20261019.json、research/COMPLEMENTARITY_MECHANISM_REVIEW_20261019.md、research/CORETA_REVISION_FROM_LITERATURE_20261019.md。AgentVerse 提供 solver-first 异议转修订先例（https://arxiv.org/pdf/2308.10848）；ChatDev 将 review comment / test error 送入明确 modification 阶段（https://aclanthology.org/2024.acl-long.810/）；MAST 区分错误核验、流程偏离和过早终止（https://arxiv.org/html/2503.13657v3）。这些支持流程设计选择，不证明 CoReTA 会提高数学能力或恢复率。

当前只完成设计候选，不表示已编码或实验有效。
