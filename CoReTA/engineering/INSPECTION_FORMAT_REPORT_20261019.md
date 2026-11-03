# 检查输出格式修复与固定回归（2026-10-19）

## 原因核验

156 上轮首次输出 JSON 在 offset 2677 缺少分隔符，原反馈只有“Output must be one JSON object”。第二次输出语法合法，但 closure_reviews 多出 scope。现有契约中 checks.scope 必填，closure_reviews.scope 不允许，存在相近记录字段混淆。592 上轮另有 checks.check_id 多余字段。

## 实现

独立变体 inspection_format_v1：src/coreta/closure_format.py 与 run_closure_format.py。从现有 ClosureInspection schema 自动生成根对象、checks、issues、closure_reviews 的准确字段清单，在检查阶段提供，并明确 scope 的使用位置。客户端在 JSON 语法错误时反馈解析器消息及行、列、offset，原文记录在 json_diagnostics.jsonl 和响应日志。

没有放宽 schema、删除输出字段、自动修正语义、增加重试或改变问题关闭规则。没有修改此前冻结实现、提示词、配置或 Candidate schema，原初稿可以复用。

## 离线验证

完整 134 项测试通过（含既有继承检查重复执行）。新测试覆盖生成字段清单、真实156/592多余字段仍被拒绝、真实156语法定位及原文留存、一次脚本化修复保留异议、第二次错误后停止。脚本修复仅为测试夹具，不能当作模型真实成功。

## 真实回归

先冻结同样六题、初稿与全部运行源码哈希；最多两进程，不重跑、不改批次。固定 Docker 镜像评分；结束时冻结哈希验证通过，六题初稿哈希一致。

| 任务 | 最终评分 | 运行结果 | 格式修复 |
|---|---:|---|---:|
| math_train/number_theory/592 | 1 | completed/complete | 1 |
| math_train/intermediate_algebra/916 | 1 | completed/complete | 0 |
| math_train/intermediate_algebra/156 | 1 | completed/complete | 0 |
| math_train/intermediate_algebra/1262 | 1 | completed/complete | 0 |
| math_train/counting_and_probability/525 | 1 | completed/complete | 0 |
| math_train/number_theory/643 | 1 | completed/complete | 0 |

总计六题均正常 complete、最终评分全部1、评分异常0、降级0。42次逻辑调用（含18份复用初稿），25次新增HTTP、1次格式修复。所有当前交付候选均经过检查。

592 首次检查仍出现 JSON 分隔符错误，新的反馈明确指出 offset 4785；同一阶段允许的一次修复后成功。没有再出现 scope/check_id 字段混用错误。156 本次无修复正常完成。

对照上轮同六题：正常完成5→6，评分通过均6/6，新增HTTP26→25、格式修复2→1。这是单次已见任务的工程回归，模型有随机性，不能把差值解释为严格因果效应或稳定失败率估计；新的位置反馈确实已在592真实修复请求中使用。

## 下一步

此局部缺陷已有离线与真实回归覆盖，可冻结当前版本，在新的固定困难题样本上做基线对照，继续同时计入初稿已对题的保留损失L与全员失败题的恢复G。六题本来均至少一份初稿正确，新增恢复G=0；此次不能宣称互补能力提升。尚未验证该版本完整30题的保留能力，也未重跑MATH140。

证据：FORMAT_REGRESSION_PLAN、FORMAT_REGRESSION_SCORES、FORMAT_REGRESSION_SUMMARY_20261019.json；runs/format-regression-20261019/。
