# 步骤变更字段修复与真实回归（2026-10-19）

## 修复内容

独立变体 `closure_diff_v1`，历史运行代码和提示词保持原样。程序计算新增、修改、删除步骤及 artifact 差异，另存 `candidate_diffs.jsonl`，并向检查者提供真实差异。模型原始 `changed_step_ids` 原样留存，但不再作为阻断依据；它不能充当修复证据。每个关闭申请必须提供可见证据引用，仍须覆盖全部异议并经过应用后检查，版本和哈希规则保持。

对于废弃草稿，增加“核对当前候选是否依赖该推理”的提示，没有按引用来源自动删问题。592 实际轨迹中，主 Agent 解释错误链式推理没有被采用、反驳错误三元组，检查者对当前候选独立核验后关闭问题。不能把自动来源过滤当作问题解决。

## 验证

五个真实失败更新离线重放：旧校验全部拒绝，新校验全部进入 pending_check，声明保持原样。证据缺失、异议覆盖遗漏仍被拒绝；步骤新增/删除/修改与仅答案变化均有测试。完整 125 项测试通过（含继承检查重复执行），无模型调用。

真实回归先冻结六题与源码哈希，复用原三份初稿，最多两进程；不改批次、不重跑。固定 Docker 镜像评分，结束后验证冻结哈希无变化。

| 任务 | 最终评分 | 运行结果 |
|---|---:|---|
| math_train/number_theory/592 | 1 | completed/complete |
| math_train/intermediate_algebra/916 | 1 | completed/complete |
| math_train/intermediate_algebra/156 | 1 | degraded/runtime_error |
| math_train/intermediate_algebra/1262 | 1 | completed/complete |
| math_train/counting_and_probability/525 | 1 | completed/complete |
| math_train/number_theory/643 | 1 | completed/complete |

六题均正确、评分异常为零；5 条正常 complete、1 条 degraded。42 次逻辑调用（含18份复用初稿），26 次新增 HTTP，2 次格式修复。原 changed_step_ids 错误零次。

156 的新失败发生于检查阶段：首次输出不是单一 JSON 对象；修复后 closure_reviews 多出未允许的 scope 字段，整条检查被拒绝。其交付答案正确，但当前候选未完成检查。592 的一次格式修复是 checks 多出 check_id，修复后完成。两者说明严格 JSON 契约仍有脆弱性；本批没有通过删除未知字段来假装检查成功。

## 结论与边界

已修复这五题此前共同的步骤元数据阻断，并在五题中使四题正常走完（另外正常对照题也完成）。尚未实现零格式失败。下一项工程工作是改善检查输出的契约遵循，特别是额外字段反馈；应独立设计和验证，不能在本批失败后修改规则再覆盖结果。

这是已见任务的工程回归。六题原初稿均至少一人正确，未新增全员失败恢复；不能据此宣称数学能力提高。没有重跑 MATH140 追求成功，也没有验证新变体完整30题保留能力。

计划、评分、汇总分别为 DIFF_REGRESSION_PLAN、DIFF_REGRESSION_SCORES、DIFF_REGRESSION_SUMMARY_20261019.json。
