# 删除重复分类的实现与离线验收

## 修改

新增evidence_review.py平面适配器及evidence_review.schema。C每个issue仅返回original_case_reviews、current_checks、verdict、reason；删除resolution/dependency，不再进行二者的组合校验。U的closure_path仍为程序输入，程序按待核查提案路径派生addressed/dismissed，C若不同意路径必须unresolved/defect并解释，不能偷偷换路径。

三问已进入模型输入：原观察是否被新计算支持；当前方案如何处理旧错误及相关依赖；当前证据是否实际满足完成条件。旧新观察、当前检查、受影响约束、角色/版本、原案例完整性、当前反例优先和预算保持。没有新增Agent、逻辑阶段或工具，也没有修改冻结旧代码。

## 离线验证

新增12项测试，全套260次执行通过。三个人工正例继续可处理；真实当前精确不等、缺新观察/未知句柄/缺必要约束、过期响应、错误角色、新当前反例仍阻止关闭。诚实报告旧依赖仍存在并给unresolved的情况保持open；程序不能识破所有写resolved但理由不真实的响应。

旧真实输出未删字段、未改值，直接输入新schema会被拒绝，不自动迁移。单独标记人工反事实fixture只移除两个字段后，I2确会被程序派生addressed，虽然其定性检查仍错；该测试是记录语义盲区，不是成功证据。原始实验/评分/账本完全不变。

完整当前检查若伪造observed和reason，程序无法代替数学判断；移除枚举也减少了一部分能直接捕捉的结构化声明冲突。不能宣称严格性完全不变或程序能机械验证“不再依赖旧对象”。

同一真实packet的provider输入离线估算21990<32768（尚未发送）。12份已有冻结计划来源hash均一致。本轮API0、无新评分。

## 当前开发入口及下一步

开发适配器选evidence_review.ReviewAdapter；真实packet映射沿用review_packet，传输接口沿用minimal_review_transport。旧minimal/aligned和各Runner作为冻结参考，不再扩展其分支。

下一步冻结一次新字段集合的组件核查，仅评价：是否按契约完成、原/新对象证据是否正确区分、关键数学检查是否正确、状态派生是否合理。必须单列人工语义裁定，不能凭4项addressed宣布成功，也不要求为得到全绿不断重试。不启动6次稳定性或整题对照。
