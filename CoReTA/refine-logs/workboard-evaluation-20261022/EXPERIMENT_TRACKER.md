# 实验准备跟踪

2026-10-22。本文件是计划，不是已执行结果；本轮模型调用0。

| ID | 阶段 | 内容 | 当前状态 | 完成条件 |
|---|---|---|---|---|
| P01 | 选型 | 学生会长开发、HiddenBench主评价、Schedule第二类任务 | DONE_SELECTION | 来源和用途写入DATASET_SELECTION |
| P02 | 数据隔离 | HiddenBench开发12/评价53清单、名字/答案字段禁入模型 | DONE_MANIFEST_ONLY | 运行投影和泄漏检查尚待实现 |
| P03 | 数据生成 | Schedule开发10/评价40个六人世界 | TODO_NOT_GENERATED | 固定种子、记录改编、盘点空解及退化情况 |
| P04 | adapter | 选择题和区间产物及精确评分 | TODO | 新runtime不读gold；空区间合法、无效答案不伪修复 |
| P05 | baseline | 强普通讨论、请求式黑板、机械全披露讨论 | TODO | 相同原生初答与资料/工具、足够有效求解机会 |
| P06 | M1a | 学生会长两分配×两法×两重复 | NOT_RUN | 输入/提示/token总预算冻结，最多216请求 |
| P07 | M1b | 开发HiddenBench4题+Schedule4世界，四法各1次 | BLOCKED_P03_P04_P05 | 最多573请求；首技术异常停批 |
| P08 | M2 | 53+40题/世界，四法三重复 | BLOCKED_NOT_EXECUTABLE | 方法/数据/基线/预算完全冻结后才开始 |
| P09 | B2/B3 | 贡献机会、使用反馈诊断 | PLANNED_ONLY | 每块≤8开发快照，人工构造与自然产生分开 |

PLANNED_EVALUATION_MATRIX.json已列1116个未来方法单元，每行都标明阻断状态。数据尚未生成或adapter尚未完成的行不是phantom结果；该文件无任何启动器或自动执行权限。
