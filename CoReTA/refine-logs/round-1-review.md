# CoReTA v0.3 第一轮独立设计审查

日期：2026-10-18。以下为第一轮完整审查原文；由同一审查代理在第二轮复审开始前保存。

<details>
<summary>第一轮完整审查原文</summary>

CALIBRATION: none  
OVERALL SCORE: **8.00 / 10**  
Verdict: **REVISE**

设计保持了原始锚点，已经具体到可以开始实现轻量协议骨架。当前需要修订的是几处跨文件契约，不需要先获得效果数据、证明模型判断正确、增加训练或扩大实验。独立的实施就绪判断为：**可开始编码；完成下述三项修订后，再冻结可执行设计。** 尚无端点、模型 revision 和执行环境属于真实运行前的依赖，不等同于研究方案不可实现。

本次仅阅读设计文件，未修改文件、运行实验或独立复核外部来源。评审依据包含父代理刚保存的数据集标识、显式重建上下文和程序构造冗余贡献三项修订。

| 维度 | 权重 | 分数 | 判断 |
|---|---:|---:|---|
| Problem Fidelity | 15% | 9.5 | 保持提高团队能力、实际利用贡献和先完成设计的目标；效率正确后置 |
| Method Specificity | 25% | 7.5 | 调用路径、载荷和失败路径具体；版本引用、变体规则及干预对象仍有执行歧义 |
| Contribution Quality | 25% | 7.5 | 主贡献集中于需求、贡献、应用与后续动作的关联；机制增量有待验证，当前没有贡献膨胀 |
| Frontier Leverage | 15% | 8.5 | 冻结 LLM 的独立解题、审查、修复和动作选择使用自然，不需要强加训练组件 |
| Feasibility | 10% | 8.0 | 三实例、同步调度、有限工作轮可实施；数据适配和资源清单需要在 E0 完成 |
| Validation Focus | 5% | 8.0 | 三块实验分别覆盖效用、组织机制和内容依赖；统计单位与主要解释边界合理 |
| Venue Readiness | 5% | 7.0 | 已形成可检验机制假设；论文定位与经验贡献仍待实际结果和更精确的近邻比较 |

加权结果为 `1.425 + 1.875 + 1.875 + 1.275 + 0.800 + 0.400 + 0.350 = 8.000`。

GAP：没有提供人工确认的优劣方案作为校准锚点，因此以上分数是未校准的同模型家族暂定判断。8.00 分不表示已经证明新颖性或有效性；同样，未达到论文 READY 门槛也不意味着不能实施。

**需要优先修复的三处问题**

1. **IMPORTANT：版本、引用与实际输入包还没有形成唯一的执行契约。**

   定位：[提案 §4.1—4.2、§5](C:/Users/QVQ/Documents/ChatGPT/agent-research/CoReTA/refine-logs/round-0-initial-proposal.md:64)，[LEAD_UPDATE 模板](C:/Users/QVQ/Documents/ChatGPT/agent-research/CoReTA/design/v0.3/PROMPTS.md:44)，[LeadUpdate Schema](C:/Users/QVQ/Documents/ChatGPT/agent-research/CoReTA/design/v0.3/coreta.schema.json:412)。

   `LeadUpdate` 同时输出新 `Candidate` 和 `next`，但尚未明确：`next.request.target_step_ids` 指向输入时的旧候选，还是此次提交后的新候选；`Application.before_refs`、`changed_step_ids` 和事件 `base_version` 分别绑定哪一版。模板提供 `CURRENT={{candidate_json}}`，却没有显式的版本和可引用事件目录。三份初稿也各有 `s1…s8`，如果传裸 Candidate，引用容易混淆。

   此外，Finalizer 仅以 `condition_evidence_package` 表示输入，尚未冻结各条件究竟包含初稿、最后候选、哪些请求包和应用记录。实现者可能在两个合理选择间产生不同系统行为。

   **最小修复：**补一张提交与引用表，不必扩建状态系统。建议明定：先在版本 `v` 上生成输出；原子提交新候选为 `v+1`；`before_refs` 指向 `v`，`changed_step_ids` 和 `next.target_step_ids` 指向 `v+1`；随后生成的 request 绑定 `v+1`。给模板输入增加由程序生成的 `current_version`、候选事件 id 和可引用事件目录，并规定初稿步骤引用方式。另用一张小表冻结各条件 Finalizer 的包成员、顺序及裁剪规则。

2. **IMPORTANT：No-application-record 与基于 unresolved 的程序限制尚不相容。**

   定位：[提案 §5 的程序校验](C:/Users/QVQ/Documents/ChatGPT/agent-research/CoReTA/refine-logs/round-0-initial-proposal.md:101)，[No-application-record 提示规格](C:/Users/QVQ/Documents/ChatGPT/agent-research/CoReTA/design/v0.3/PROMPTS.md:104)，[B2](C:/Users/QVQ/Documents/ChatGPT/agent-research/CoReTA/refine-logs/EXPERIMENT_PLAN.md:85)。

   主协议规定“上一请求被标记 unresolved”后禁止原样重复，但没有指明该标记来自 `Review.verdict` 还是 `Application.application_outcome`。两者含义不同，而且 `cannot_help` 路径没有 Review。若依据 Application，删除 Application 后程序便失去该信号；若变体悄悄取消限制，比较就同时改变了动作权限。

   **最小修复：**最简选择是所有条件统一取消这项依赖模型自报结果的硬限制，保留两工作轮上限和重复请求日志，在完整协议中继续保留利用应用反馈调整动作的提示。也可以定义一个仅依赖两条件共有字段的重复规则，但必须写出唯一判定方式。无需引入新的收益判断器。

3. **IMPORTANT：B3 必须替换完整 Contribution，防止正文之外保留原贡献信息。**

   定位：[B3 的冗余构造与分支规则](C:/Users/QVQ/Documents/ChatGPT/agent-research/CoReTA/refine-logs/EXPERIMENT_PLAN.md:94)，[Contribution Schema](C:/Users/QVQ/Documents/ChatGPT/agent-research/CoReTA/design/v0.3/coreta.schema.json:219)。

   当前程序抽取规则具体定义了冗余文本，但 Contribution 还含有 `basis_refs` 和 `check_suggestion`。如果实现只替换 `body`，原贡献的新公式、关键反例或修复方法仍可能通过 `check_suggestion` 进入检查者。即使各分支只读自身事件，也无法消除这种对象内部残留。

   **最小修复：**直接规定替代对象：保留请求关联和来源身份；`body` 使用冻结抽取算法；`basis_refs` 仅引用被抽取的原候选材料；`check_suggestion` 使用固定通用检查语句，不复制原贡献；`status=provided`。分支事件及父引用不得指向原贡献正文、检查或应用结果。此修复不增加调用，也不改变 B3 的诊断性质。

**已核对且不应据此扩大方案的部分**

- **调度与资源算式一致。**完整路径为 `3+1+1+2×3+1=12` 次正常调用；两次格式修复后最多 14 次生成请求，每请求最多三次 HTTP 尝试对应 42 次。五条件调用和为 32，`664×3×32=63,744`；共享初稿银行后每实例减少八次，为 `1,992×24=47,808`。B3 在首个帮助贡献之后最多还有六次后续调用，1,800 的上界成立。见[提案 §7](C:/Users/QVQ/Documents/ChatGPT/agent-research/CoReTA/refine-logs/round-0-initial-proposal.md:121)与[实验规模](C:/Users/QVQ/Documents/ChatGPT/agent-research/CoReTA/refine-logs/EXPERIMENT_PLAN.md:138)。

- **成员分工没有明显封死互补空间。**A1/A2 可以补全、反驳、修复或提出完整替代解，检查者也可提出修正。固定 A0 维护状态是合理的第一版控制变量。同模型成员只支持研究独立执行产生的贡献差异，不能自动扩展为异构专长利用；文件已经承认这一边界。

- **gold/test 隔离的原则充分。**PublicTask 白名单、独立评分进程、禁止隐藏历史追加和分支自身事件视图已经构成可执行方向。需要落实的是上述具体输入契约，不需要另建大型权限系统。

- **来源台账区分了借鉴与自设计。**MetaGPT/AutoGen 的接口组织、Blackboard 的请求思想、Debate/MoA 的候选交流与汇总没有被整体包装为 CoReTA 首创。主机制仍应表述为可检验的组织协议，而非字段清单创新。实现前按台账锁定实际采用的 commit、包和数据版本即可；本审查不将尚未重新查新作为实施阻塞。见[来源台账](C:/Users/QVQ/Documents/ChatGPT/agent-research/CoReTA/refine-logs/SOURCE_LEDGER.md:20)。

**进入 E0 前补齐的几项小规格**

- **MBPP 接口适配：**[实验计划 §2.3](C:/Users/QVQ/Documents/ChatGPT/agent-research/CoReTA/refine-logs/EXPERIMENT_PLAN.md:44)仍把实际字段与接口确认留待实现。需要预定“公开题面缺少函数名或签名”时如何处理：使用基准公开的接口资料，或按固定规则替换为接口完整的开发题。不能把接口未知造成的失败算作协作能力失败，也不能临时读取参考实现生成接口。这是来源/适配核查点，不要求新增数据集研究。

- **Generic-help 的“保留时机”应明确含义：**[提示词第 102 行](C:/Users/QVQ/Documents/ChatGPT/agent-research/CoReTA/design/v0.3/PROMPTS.md:102)建议改为保留动作策略、初审和调用上限，后续动作由该变体自己的状态决定。如果指逐步强制重放完整 CoReTA 的时机和收件人，则是另一种干预，不能混写。

- **B3 缺失分支的分母：**[第 92—98 行](C:/Users/QVQ/Documents/ChatGPT/agent-research/CoReTA/refine-logs/EXPERIMENT_PLAN.md:92)应区分 `no_eligible_help` 与 `intervention_unavailable`。前者可以按预定政策差值记零；后者没有观察到替代分支结果，不能也当零。建议报告指定总体的资格/可构造比例，以及可构造配对样本上的差值；若报告整体意向结果，明确缺失处理或界限。无需为了补齐数量另挑成功案例。

- **离线核对的盲法：**[第 114—116 行](C:/Users/QVQ/Documents/ChatGPT/agent-research/CoReTA/refine-logs/EXPERIMENT_PLAN.md:114)应把“可看测试结果”限定到贡献与应用判断提交后的解盲阶段，避免与“先看不到最终成功标签”冲突。题目级配对 bootstrap、三个重复先按题平均及双主比较校正方向合理，不需要增加重复种子冒充更多独立任务。

Simplification Opportunities：删除依赖 unresolved 的程序硬限制；将版本、引用和上下文包统一到一个确定性构造器。其他主要组件已有明确职责，暂不建议为减少组件数删除贡献检查或实际应用记录。

Modernization Opportunities：**NONE。**当前冻结 LLM 与结构化调用足以检验假设，暂无理由增加训练路由、复杂记忆或额外裁判模型。

Drift Warning：**NONE。**问题锚点保持。上述修订均针对执行契约和实验解释，不把同成本优势、先证明正确性或大型系统建设设为本轮门槛。

</details>
