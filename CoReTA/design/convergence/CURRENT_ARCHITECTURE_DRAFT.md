# CoReTA 当前架构收敛规格（待实现）

日期：2026-10-20。状态：设计交付，不是已启用协议；旧运行器、原始结果和冻结规格不覆盖。当前运行代码仍是v7及其冻结前身。此文作为下一轮收敛实现的唯一设计入口。

## 1. 目标与变更边界

保留三成员、同模型、独立初稿、主动建设性补充、实际整合、应用后独立复核、有限轮次和无在线求解工具。目标仍是协调与解题能力及有用贡献利用；成本作为记录项，不以压缩输出本身宣称能力贡献。

本次只收敛检查输入/输出和问题关闭。暂不改变TaskFacts阶段、模型、温度、角色数量、B/U顺序、轮数或评分条件。TaskFacts失败仍可能阻断现有运行，这是明确未解决的入口问题；本规格不通过静默跳过它掩盖故障。之后是否将其改为辅助材料须另行设计和比较。

## 2. 六个组件

|组件|模型职责|程序职责|
|---|---|---|
|候选与公共材料|独立解题、解释任务约束、综合候选|保存公开题面、初稿、版本和源内容|
|定向贡献|完成局部工作/修复/替代，说明条件与接入位置|分发具体请求、保存原交付和角色|
|整合|产生完整新候选，说明采用/拒绝及剩余问题|提交版本、算hash/diff、登记关闭提案|
|检查|核查当前对象、重做必要旧案例、提供新观测与理由|提供足够内容和预分配句柄；校验角色与引用|
|证据账本|选择已提供句柄，提交新计算；不复制旧记录|原证据不可变，新增观察追加存储，生成全部记录身份|
|状态与调度|给出修复/反驳判断和下一工作建议|逐问题派生状态、处理预算和停止，不充当数学裁判|

## 3. 调用流程和预算

D0/D1/D2 → TaskFacts → S → [B/W → U → C]最多3轮 → 直接导出当前完整候选。

A0为整合者；每轮B为A1/A2之一，C为另一位。每次独立上下文，不依赖会话记忆。最多14逻辑调用、全局2次格式修复；检查输出8192、输入32768沿用当前配置。实际HTTP含格式修复与传输重试另计。不新增final、不增加Agent。超预算保留记录并停止，不静默删反例。

## 4. 检查输入：程序生成ReviewPacket

包含完整公开题面、TaskFacts（保持model_asserted）、本轮贡献、当前/前一候选及必要历史原文；packet元数据含候选版本/hash、实际角色、期望关闭提案。模型无需回写元数据，程序把响应绑定到唯一在途packet；这仍然只约束数据归属，不能防止模型在语义上检查错对象。

程序提前生成简短的issue_handle、target_handle、case_handle、task_ref。每个句柄只在该packet有一个映射；映射到原issue/记录/版本/实际原文。模型只选已提供句柄，不生成event_id/record_id，不填写输出后才存在的数组位置。当前target与历史target明确分栏。

每个待复核issue输入包含：关闭路径repair/rebuttal、完成条件、全部活动异议、原审计记录（只读）、required_case_handles、可见当前步骤和候选。原历史case必须提供被测对象定义、输入、声明预期、原观测及来源。确实无法获得完整含义时标unavailable，禁止声称已独立重查。

发送前预检：角色独立；packet候选与pending版本一致；每个活动异议与原案例均可追溯；所引用内容实际提供；输入预算通过。原输入缺失则停止或修正packet后重新冻结，不发明原文。

## 5. 最小输出：逐问题组织，引用由结构承担

根字段仅issue_reviews和new_findings。issue_reviews以输入提供的issue_handle为键。每个review包含：

- original_case_reviews：case_handle、新observed_value、original_assessment（supported/refuted/uncertain）、简短计算或理由。只提交新观测，不回写旧expected/old_observed或复制旧payload。
- current_checks：target_handle、task_refs、input、quantity、expected_value、observed_value、comparison_kind、outcome与推导。每个check在其issue之内，程序直接绑定issue并分配record_id，不需要current_record_indexes。
- resolution：same_object_repaired / replaced / rebutted / unresolved。
- dependency：仍依赖(still_used) / 已移除(removed) / 不适用(not_applicable) / 不明(unknown)。same_object_repaired使用not_applicable，不能要求它移除整个对象。
- verdict：resolved/unresolved/defect；reason说明修复或反驳如何满足完成条件。

new_findings用于当前新缺陷，绑定当前target和相关issue（如有），并给具体检查。程序生成新issue身份，不能在同一响应里自动关闭新异议。

动态schema按packet约束issue/case/target/task句柄允许值和required issues；外加程序校验唯一case与归属。语义仍由模型/人工判断。一个字段错误影响对应issue；JSON无法解析、角色错误、packet身份错误等整包错误阻止全部关闭。原始响应始终保存，无效部分单独保留为诊断而不成为有效语义证据。

## 6. 三类问题关闭

### A. 同对象修复

旧版本F_v1失败仍保留。新观察重查F_v1及其原输入；current_checks检查F_v2的受影响条件，不能以F_v1的输入句柄冒称F_v2。旧反例支持、当前检查无反例、修复及完成条件获独立支持，才派生addressed。对象名称相同不等于版本相同。

### B. 替换错误对象

旧G仍失败不是当前失败。重查G保留其错误；current_checks实际核查替代H；dependency=removed且reason提供不再依赖G的连接理由，覆盖原受影响条件及新增依赖；若仍依赖G、不明、H失败或桥梁缺失，则open。程序不从一段文字机械证明removed，必须标明该判断由检查者承担。

### C. 反驳错误异议

新观察可与旧观测不同，两者都保存。检查者须说明为何原反例不成立（算错、对象/版本错、任务条件误解等），并实际核对当前相关主张。候选可不变；完成条件得到独立支持后派生dismissed。不得因为账本原值不可变而要求新观测也不可变。

共同条件：全部原必需案例被真实重查或说明无法核查；活动异议完整处理；无当前冲突；不得靠投票、hash变化或“旧证据已加载”冒充复核。一个旧案例uncertain便不能关闭受其影响的问题。当前精确不等可派生finding，但“数值相等”不自动证明主张正确。

## 7. 状态与有效性

原记录保持原effective_outcome；新增独立ReviewObservation关联原case。程序另派生当前问题的active_effect（historical_only/current_conflict/needs_review），不改写原事实。pending_check → addressed/dismissed需要上述条件；否则open。候选后续变化沿用原needs_revalidation规则。

分别记录schema_valid、references_valid、review_complete、issue_resolved和离线semantic_assessment。reviewed不等于正确，resolved不等于金标准正确，not_refuted不等于数学证明。禁止合并成一个“检查有效率”而省略口径。

## 8. 不把复制当核查的三个不变量

1. 加载旧记录仅证明能追溯，不产生新的独立观察。
2. 新observed必须来自检查者本次实际推导；与旧值不同不覆盖旧值，而触发解释与差异记录。
3. 程序只自动生成身份和确定的结构关系，不自动声明已移除错误依赖或修复成立。

## 9. 实现与验收顺序

先实现一个独立最小review适配器与状态投影，不再追加多层Runner继承。复用既有候选/账本存取；旧入口冻结不改。第一轮只实现本目录契约，禁止同时改TaskFacts策略或加入工具。

离线覆盖：三正例及反例；历史值被修正、替代方案失败、虚假弃用有当前反证、原对象定义缺失、角色重叠、引用缺失、旧packet响应、未知句柄、部分issue失败、输入/输出超限、修复额度耗尽。历史所有真实错误保留且不得自动转换为成功记录。

验收后先一组冻结组件检查；再一次完整开发回归；再新题共享初稿对照。沿用恢复/损失/流程失败及互补来源的分开统计。当前不启动付费调用，不作能力结论。
