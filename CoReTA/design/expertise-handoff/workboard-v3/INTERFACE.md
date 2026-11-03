# 工作板候选：实现接口约定

日期：2026-10-22。状态：独立模块已完成离线工程检查和12项固定schema复制兼容检查；完整解题提示与能力未验证。方法正文见[SPEC.md](SPEC.md)，交付记录见[BUILD_NOTE.md](implement-stage/BUILD_NOTE.md)。

## 1. 输入边界

程序给每次调用绑定run、member、stage、可见资料、当前版本和剩余预算；模型不生成这些ID。新调用只得到明确列出的上下文，不依赖隐式聊天记忆。

首版任务允许成员公开交流所知事实和解答，原始文件仍按成员权限读取。全部原生初稿可读，保留完整解题机会；不做额外摘要。严格禁止知识内容外传的任务不在首版支持范围。

| 阶段 | 必须可见 | 本轮先不可见 |
|---|---|---|
| INITIAL | 原任务、自有资料、公开资料 | 所有他人初稿 |
| OBSERVE | 当前Work、可读候选区、上轮问题和无法应用理由 | 当轮peer新offer |
| TRY | 当前Work、所选offer、候选区、合法证据 | 当轮尚未形成的检查 |
| CHECK_USE | offer、整个前后Work、use_record、自有原资料、合法执行输出 | 本轮另一检查结论 |
| CHECK_EFFECT | 原任务、自有资料、公开证据、trial真实产物和普通解答、目标及diff | use_record中对应用成功的说明、本轮另一检查结论 |
| CHOOSE | 前后产物、两份check、合法执行输出 | 离线评分 |
| FINALIZE | 当前Work、回退F、候选区、未决观察 | 离线评分 |
| 最终双检查 | 收尾版本与F两个真实交付物、各自合法材料，按上述职责分配 | 本轮另一检查结论；后果检查不先读成功声明 |
| FINAL_CHOOSE | 两个候选与检查 | 不允许再生成第三份产物 |

检查输入必须含真实的adapter交付字段，不能只给use_record或把结论摘要代替实际产物。工作解答本身可能含错误解释，不能宣称输入已完全去除锚定。

## 2. 模型输出的最小动作

以下为逻辑契约；服务端JSON schema由后续实施适配，不在这里冒充已验收。

- INITIAL → Work：`artifact, work_text, open_points`。
- OBSERVE → `pass`，或Offer：`target, knowledge, support, proposed_use`。
- TRY → `reuse(candidate_id, use_record)`，或`new(Work, use_record)`，或`unable(reason)`。reuse必须引用真实可读候选，不能只是名字；unable不生成trial。
- CHECK_USE / CHECK_EFFECT → `finding, observation, scope`；finding仅为`issue/no_issue_found/unable`。
- CHOOSE → `candidate_id, reason`；ID枚举仅含旧版与实际trial。
- FINALIZE → `reuse(candidate_id, declared_sources, use_record)`或`new(Work, declared_sources, use_record)`；其后仍要检查该真实版本。纯复用时注明无新应用，不改写原稿；新生成时说明实际使用的来源、条件和操作。
- FINAL_CHOOSE → `candidate_id, reason`；ID枚举仅含符合交付形状的收尾版本与F。

Work内容不可变；程序加ID、作者、基版本、可见来源、交付形状状态。Trial与普通Work共用结构，新增引用用途，不复制维护两套产物。declared_sources只是模型申报的应用来源，不等于已证实因果关系。本次应用声明通过APPLICATION_SOURCE_REFS传给两检查包，不覆盖复用候选创建时的原始声明。检查包能读取原生候选区，以核对offer引用的其他公开原稿。

2026-10-22接口修订：TRY/FINALIZE的`reason`为reuse/new的可选解释（null或非空字符串），不能替代必需的`use_record`；原样响应日志保留解释，不据其改变版本或检查者。reuse仍要求真实候选ID且work=null；new要求work且candidate_id=null；unable仅TRY允许，必须给reason，work/candidate_id/use_record=null且declared_sources=[]。OBSERVE的pass仍不得携带可被误执行的offer。两种方法共用动作契约。旧批次保持中断状态。

2026-10-22来源边界修订：输入`SOURCE_ACCESS`列出`direct_original_refs`（TASK及本人SELF_MATERIALS）、`public_report_refs`（实际可见公开贡献/候选）和`reported_originals`（从公开offer.support及Work历史来源元数据派生的转述编号→公开载体索引）。每个REFERENCE_INDEX条目带access类型。间接索引标为peer_metadata_not_verified，既不证明支持关系也不赋予原件访问权；不检索他人原件、不从自由文本猜来源。两法共用该规则，普通讨论补齐候选后重算索引。declared_sources及offer.support.ref继续只能引用当前REFERENCE_INDEX：使用同伴知识时引用实际读到的公开O/W载体，原资料持有者仍可引用本人原件。引用或核验声明仍可能错误，需对实际使用另行检查。错误引用不会被自动删除或重映射；旧r2保持中断。

Offer.target可为已有段落/行、完整候选ID或whole_goal。support可引用合法资料，也可给明确标识的模型推导。反例不必提供完整修复。

## 3. 确定性规则

1. 编辑者：task_ordinal % N；初稿缺失时按固定成员顺序降级，记录失败。不看gold。
2. 选择offer：当前提出offer者中尝试数最少优先，平局按从指针开始的循环成员顺序。TRY发出即增加计数、指针后移；pass跳过。旧版offer不可自动接到新快照，须重新提交。
3. 普通检查：当前提供者查用法；编辑者和提供者以外的下一位循环成员查后果。
4. 收尾检查：直接采用非编辑作者原稿时，作者查用法；否则先按公开O从新到旧匹配本次申报的非编辑来源作者，再按已有W从新到旧匹配其非编辑作者，不要求该来源先前已进入TRY。无该来源时取编辑者之后第一位非编辑成员，称依据/用法检查者。另一位非编辑成员查后果。多来源各自声明可见范围，不冒充全面确认。N=2两项由一人完成；当前主入口只实现N≥3。
5. 当前可交付版本被替换时F更新到该版本；当前版本不可交付时F不被清空。初始F按规范从已有完整初稿确定。交付形状合法不是正确。
6. 收尾预留最多四调用；过程不得无限挤占预留。无法完成收尾则交付现有F并记录未完成范围；无F则交付失败。
7. 最后原样渲染所选artifact，不能再自由生成一份不同终稿。

无trial时跳过检查和选择；无法应用理由进入下一观察，或标记反馈未完成。选择与检查都不产生真值认证。

## 4. 工具、日志和失败

工具观察由运行器绑定`artifact_id, invocation, input, raw_output, exit_status`；模型自称执行成功不属于工具观察。全部对照享有同等工具；gold scorer只离线使用。

日志保存初次输出、恢复输出、真实调用/token、offer从提出到采用的每个事件、前后产物与检查范围。引用合法性、版本存在性和可交付形状可机械检查；相关性、适用性与正确性不可据字段存在推断。

上下文/token超限不得静默删资料；引用容量随可见资料配置，不沿用旧的固定12项假设。具体token和恢复上限须在实施计划冻结。后续工程核对记录见[VALIDATION_20261022.md](implement-stage/VALIDATION_20261022.md)；正式实验预算仍待冻结。
