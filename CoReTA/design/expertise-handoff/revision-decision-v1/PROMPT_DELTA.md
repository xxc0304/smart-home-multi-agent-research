# 待实现的提示增量

状态：仅设计文本，未接入当前HandoffPrompts，未用于模型调用。第一阶段只在实验臂APPLY追加以下片段；对照臂保留当前APPLY。原字段、输出格式和篇幅上限不变。

## APPLY：比较修订前后的依据

```text
When responding to a review, distinguish what the observation establishes about
the current work from what supports a proposed replacement. An objection to an
ordering, premise or step does not by itself establish the opposite or make an
alternative better. Conversely, a valid counterexample or task violation remains
valid even if the reviewer cannot supply a complete repair.

For the consequential decision in this update, briefly explain in applications
what the current task-based support is, what the review actually changes about
that support, and why any adopted replacement addresses the problem. Existing
materials, a corrected calculation, a derivation or a concrete counterexample
can suffice; a new citation or a new fact is not required. A source supporting
two individual facts does not automatically support a comparison between them.

Accept a supported repair, adopt only its supported part, or reject a specific
unsupported proposal with a reason in excluded. Do not change the artifact just
to demonstrate responsiveness. Do not retain a refuted conclusion as established
merely because a complete replacement is unavailable. If a consequential issue
cannot be resolved, keep it in unresolved and submit the best task answer you can
within the existing protocol. An unchanged answer is not certified correct.

When requests are allowed, ask only for an available fact or local check that can
distinguish the live alternatives; do not seek agreement or an authoritative vote.
When requests are not allowed, do not invent a check or claim it was performed.
Keep this comparison concise and local, using the existing response fields.
```

## 第一阶段不改变的内容

不同时修改REVIEW、REPLY、CONTRIBUTE；不提示NASA正确名次，不列出历史具体错误，不要求排序更接近参考。是否保留、修正或反转均由模型依据可见任务内容判断。第一阶段禁用请求是两臂共同的局部对照限制，不是生产架构取消按需求助。
