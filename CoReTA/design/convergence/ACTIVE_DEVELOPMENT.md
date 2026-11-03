# 当前开发入口

独立检查适配器：src/coreta/evidence_review.py。
输出契约：design/convergence/evidence_review.schema.json。
真实材料映射：src/coreta/review_packet.py。
共享预算及provider封装：沿用既有组件；后续完整调度接入尚未完成。

旧minimal_review.py、aligned_review.py和Runner均为已冻结实验依赖，不修改或删除，不作为新增功能入口。当前规则以CLASSIFICATION_REVIEW_20261020.md及EVIDENCE_REVIEW_IMPLEMENTATION_20261020.md为准，覆盖最初草案中resolution/dependency输出要求。旧设计例子保留为历史，测试删除字段后的版本明确为人工fixture。

程序状态通过与数学正确性必须分别记录。本轮只离线实现，未取得新模型结果。


2026-10-20更新：完整调度接入入口为 src/coreta/converged_flow.py，离线整链路验收已完成（全套267项）。完整真实运行尚未执行。详见 engineering/CONVERGED_FLOW_INTEGRATION_20261020.md。
