# 现有复核输入审核与最小替换设计

日期：2026-10-23。状态：实际请求审核和候选设计完成；运行架构未修改，候选未做自然调用。

## 实际接口已经有什么

`runtime.py:run_checks`向两位检查者提供相同的BEFORE、AFTER、TARGET_OFFER、DIFF、APPLICATION_SOURCE_REFS，并分别保留各自SELF和SELF_MATERIALS。CHECK_USE还收到USE_RECORD；CHECK_EFFECT不收到该自述，以保持对实际产物后果的独立判断。两份输入在两次检查调用前就构造好，第二位看不到第一位刚生成的意见。两位都能看公开候选和贡献；D0还有焦点及历史反馈。

因此，“没有提供前后版本或diff”不是这次失败的原因。DIFF是整个artifact/work_text/open_points的JSON文本差异；不少work_text为一整段，差异本身没有把独立主张逐条对齐。检查者需在大量自然语言中自己定位改动。此处尚未测定上下文长度是否造成失败，不能由输入长直接推断原因。

复核职责也并非只要求查引用：CHECK_USE已要求检查对象、条件、操作；CHECK_EFFECT已要求重建变化后果。当前缺口是这些要求没有稳定转化成原文、被改主张与实际后果的逐项比较。输出只有finding/observation/scope，允许长篇重述建议，却不要求展示哪条原句支持了哪项判断。

## 资料视角的实证核对与更正

审核8次真实复核请求，提取证据见 `REVIEW_INPUT_AUDIT.json`，可由 `review_input_audit.py` 重新生成。它只记录实际输入、输出、文件哈希，不自动判语义正确。

|单元/阶段|实际身份及原文|输出表现|判断|
|---|---|---|---|
|034 D0 CHECK_USE|A2，SELF_MATERIALS含S02|说“我没有直接访问S02或S03”，不能核实“A2对S02的复述”|把自己当成了其他成员，直接访问陈述错误。|
|004 D0 CHECK_EFFECT|A1，SELF_MATERIALS含S01|scope说S01/S02/S03都只能通过公开报告看到，没有原文|对自己S01的访问陈述错误。|
|034 v3 CHECK_USE|A2，SELF_MATERIALS含S02|承认SOURCE_ACCESS列S02为自己的原文，却又称本轮只能通过O5使用、尚未由自己核实|混淆“编辑者间接获知”和“检查者本人直接可读”；O5本身就是A2的贡献。|

以上是人工确认的具体视角错误，不能当作一般化发生率。仅说“本次未核实某来源”也不等于否认访问，未将所有保留性说明都判成错误。

上一份 `PROCESS_EVIDENCE_ALIGNMENT_AUDIT.md` 对034“可访问原文”的表述需要精确化：S01是编辑者A1的原文，TRY和CHOOSE确实直接收到它；A2和A3复核时只收到各自S02/S03，没有S01原件。他们可以从公开W4看到“使Pine危险”的来源报告并发现版本差异，但不能声称已核验S01原件。A1自己的TRY/CHOOSE同样漏掉了直接可读的S01危险陈述。这既是修改者保留证据的问题，也涉及检查者对自己视角的维持。

## 候选机制：在原有两次检查中展示支持关系

设计目标是让复核以“哪条具体主张被改动、谁能看到什么依据、该改动受到什么支持”为判断单位。继续使用现有两位成员、两次调用和finding/observation/scope接口；不是新设判断者。历史版本和完整产物仍可用于检查新增或被删除内容，不能只看选中贡献涉及的句子。

CHECK_USE负责核对贡献的解释是否忠于证据，同时核对修改者有没有把一条局部提醒扩大到其他主张；CHECK_EFFECT负责独立检查实际版本中的关键主张和后续结论。允许发现未变选项下的理由损害，也允许认可正确修改。两者在observation中用简短自然语言展示一至三项有决定意义的对齐；发现更多影响交付的严重错误时继续报告，不强行凑满或截断。

候选CHECK_USE完整替换该阶段的职责文字如下；通用身份、来源指导和D0焦点说明继续生效，不再叠加原CHECK_USE职责段：

> Evaluate the actual revision, not compliance with the offer. First establish your own identity from SELF and which originals you can read in SELF_MATERIALS; do not inherit the editor's access limits. In observation, show the decisive alignments: the exact claim or condition being changed; a short exact supporting or conflicting passage from your own original or a named visible public carrier; and what AFTER actually says or does. Distinguish a report's explicit content, an inference drawn from it, and whether the report itself is reliable. Check whether a local suggestion was generalized to a different object or claim, and whether useful supported content was removed. Use USE_RECORD only as the editor's account, not as evidence the revision is correct. You may reject or narrow your own previous offer. If an original is unavailable, assess consistency with the visible report and state that boundary; do not claim original verification. Report a concrete issue, no issue found within the checked scope, or inability with reasons. Do not invent quotations or require all uncertainty to be resolved.

候选CHECK_EFFECT完整替换该阶段的职责文字如下：

> Independently compare BEFORE and AFTER using the actual artifact, changed reasoning, task requirements and evidence available to you. Establish your own identity and direct source access from SELF and SELF_MATERIALS. Reconstruct the decisive changed relation and its consequence for the task. In observation, show the relevant before/after claim and the short original passage, named public report, counterexample, calculation or supplied tool result that supports your judgment. Check for unsupported strengthening, loss of explicit reported information, changes to a different object than the evidence supports, and downstream inconsistencies, even when the final option is unchanged. A more cautious statement is not automatically more faithful; a quoted report is not automatically true. Distinguish what you directly verify from what is only reported. Do not grade whether the editor followed the offer, invent missing evidence, or claim unexecuted tools. If the evidence cannot distinguish alternatives, state the limit and inspect the consequence rather than manufacturing a verdict.

这只是待验证的工作分解，尚不能声称提高正确性，也不构成已证明的论文创新。它保留了旧复核检查实际后果的能力；其潜在风险是证据引文占用预算、过度关注文字一致而忽略任务推理、以及检查者仍可能选错或误读引文。

## 034与004上的预期判据

034：合格检查应分开处理Pine危险与Cedar当前安全。公开W4已报告S01明确指出Pine危险；W6把它只写成方向推断，至少应标为与该公开报告不一致，并要求由持有S01的A1核对。A2/A3不能认证S01原件。对Cedar位置/当前安全的谨慎可以合理保留，不能据此否定Pine的明确报告。通信设施信息有用，应保留其“成员回忆”的依据与范围。道路段须区分S02的“报告无法到达”和模型额外设想的替代路线。

004：合格检查应认可汽车线索对Mr.Z摩托车解释的约束，同时保留儿子驾驶、110km/h以及owner/driver用词的真实局限，不能为否定新稿而强行改变正确选项。A1应明确自己能直接检查S01，A2能直接检查S02。识别一处未决不等于要求整稿作废。

这些都是开发用判据，不作为在线提示中的题目专用答案，也不能当作泛化结果。

## 最小受控验证方案

先冻结本轮4个实际BEFORE/AFTER复核输入；每个来自旧v3或D0的产物对作为一个分层条件。A为该输入原有复核指令，B仅替换上述两段复核职责。成员、可见资料、公开历史、schema、输入数据、模型配置和3072输出上限全部匹配，不能向A2/A3补发A1私有原文。A、B均重新调用，不能拿历史A与新B直接当匹配重复；两项检查继续相互独立。

按4输入对×2指令条件×2检查×2重复，最多32真实请求、98304输出token；尚未冻结运行清单或执行。交替A/B顺序；首技术错误停批，完整保存中断和原始用量。两题上的重复及不同历史版本是相关观测，只用于开发诊断。

主要判据是034能否发现Pine报告被错误弱化，并正确说明自己的访问边界；同时检查004真实车辆约束是否被保留，以及是否产生错误反驳。另记录身份/来源视角错误、引文是否与可见文本一致、任务后果判断是否成立、实际token及格式失败。人工逐条核对，不以issue数量、是否用了引文或addressed作为成功分数。

本阶段固定AFTER不让TRY重写、也不运行CHOOSE，识别的是复核辨别能力，不能称为修复效果。若B有稳定的正确发现且不明显增加错误批评，再用匹配的选择阶段比较这些反馈能否保留更好的实际版本。034两个选项都对，评估必须包含理由中的证据保留；仅看选项准确率会漏掉主要差异。只有这一步成立，才考虑接入完整流程并另测是否提高最终任务质量。
