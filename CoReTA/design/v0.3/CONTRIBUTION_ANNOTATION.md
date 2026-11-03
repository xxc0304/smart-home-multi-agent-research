# CoReTA 离线贡献核对规则与空表

日期：2026-10-19。设计补充，尚无真实标注。与 EXPERIMENT_PLAN §5.2 配套，不进入 Agent 输入，不增加模型调用。

## 单位与两阶段判断

单位为预选轨迹的首个 HELP/ALTERNATIVE provided 贡献及其检查、A0应用和最终输出。无此事件保留轨迹，记 no_eligible_help；cannot_help 另记，不替换成其他更有利事件。主应用位置为该贡献后的第一次 A0 更新，Finalizer 的再次利用单独记录。

第一轮看公开任务、匿名化角色和可见轨迹；不看方法名、评分、金标准。为判断贡献相对谁新增，提供贡献者实际收到的上下文、A0帮助前候选和初始候选；不要求标注者猜测模型内部思考。先提交内容类型、可见应用和依据。第二轮才加入参考解/离线评分，记录有效性与成功，修订第一轮判断须保留原记录及理由。

## 内容与应用类型

| 标签 | 可见判定条件 | 不足以判定的情形 |
|---|---|---|
| existing_solution_selection | 采用/保留的完整方案已存在于贡献前可见候选，后续主要是选择、重述或保持 | 只因最终答案与某初稿相同，不能认定过程是选择 |
| new_whole_solution_adoption | 帮助中新出现相对完整、可独立支撑答案的方案，A0主要采用或替换为该方案 | 请求名称是 alternative 不保证实际给了完整解；完整代码字符串也可能只是局部修改后的交付格式 |
| local_joint_completion | 能定位帮助提供的局部内容，同时能定位接收者保留/新增的其他实质内容，并指出两者在后续方案中的连接；该帮助自身未提供被直接采用的完整方案 | 仅拼接措辞、投票、统一格式、简单附和或引用事件id不算；最终正确不替代连接证据 |
| undetermined | 可见材料不足，或上述关系无法可靠区分 | 不强行分配到互补类型 |

先分别记录 contribution_form=local/whole/restatement/undetermined 与 use=applied/rejected/deferred/no_visible_use/undetermined，再判断上述关系标签。局部帮助被拒绝时可记 local 和 rejected，但不记 local_joint_completion。有效性另记 supported/defect/unresolved，不能因失败把实际发生的局部联合补全改成未应用。

不同阶段可有多种关系，逐事件记录，不强制整条轨迹单标签。例如先局部补全、Finalizer再采用另一完整解，须分别定位；不把前者自动认作最终成功原因。主对象标签与后续次级标签分栏。缺少实质文本证据时记 undetermined。

## 空记录模板

每条记录至少包括以下字段；这是离线标注表，不扩充运行时消息 Schema。

```json
{
  "task_id": "",
  "run_id": "",
  "repeat_seed": 17,
  "annotator_id": "",
  "eligible_help": null,
  "contribution_event_id": null,
  "application_event_id": null,
  "contribution_form": null,
  "visible_use": null,
  "primary_relation_labels": [],
  "prior_material_refs_and_quotes": [],
  "contribution_refs_and_quotes": [],
  "recipient_refs_and_quotes": [],
  "connection_explanation": "",
  "secondary_events": [],
  "validity_before_unblinding": null,
  "uncertainty_reason": "",
  "stage1_submitted": false,
  "validity_after_unblinding": null,
  "prefinal_success": null,
  "final_success": null,
  "revision_reason": null,
  "b3_intervention_status": null,
  "b3_natural_success": null,
  "b3_redundant_success": null
}
```

空模板中的 null 表示未填写，不是失败或无效。引用采用原事件/版本引用，附必要短摘录；匿名化展示与原引用的映射只供离线整理。后解盲修改另存一版，不覆盖首轮判断。干预不可构造保持缺失；无合格帮助的B3零差值按实验协议记录，不冒充已运行替代支路。

## 汇总

报告预选60条、合格帮助数、可构造B3配对数、各类型数量和不确定数量。逐类列可见应用、帮助有效性、接收后与最终成功、自然/冗余支路差异；小样本及单人标注只作探索性结果。标签可重叠，各类使用自己的明确分母。内容依赖证据与局部联合补全文本证据应同时展示；不据此宣称已证明全部团队收益来自互补。
